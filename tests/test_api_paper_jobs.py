"""HTTP tests for the Sprint 150 durable paper-job boundary."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier, Event
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.orm import Session, sessionmaker

from el_psy_quant.api.app import create_app
from el_psy_quant.api.middleware import REQUEST_ID_HEADER
from el_psy_quant.api.paper_job_schemas import (
    PaperJobRecoveryResponse,
    PaperJobResponse,
    PaperJobResultResponse,
    PaperJobSubmissionResponse,
)
from el_psy_quant.api.paper_run_schemas import PaperRunCommandRequest
from el_psy_quant.api.routes.paper_runs import paper_run_command_from_request
import el_psy_quant.api.routes.paper_jobs as paper_job_routes
from el_psy_quant.application import submit_paper_job
from el_psy_quant.persistence import (
    PaperJobAttemptRecord,
    PaperJobRecord,
    SqlAlchemyPaperJobAttemptRepository,
    SqlAlchemyPaperJobRepository,
    SqlAlchemyPaperJobResultReferenceRepository,
    create_paper_job_result_reference,
    create_product_database_engine,
    create_product_session_factory,
    create_running_paper_job_attempt,
    resolve_product_database_config,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RECOVERY_AUDIT_REVISION = "0004_paper_job_recovery_audit"


def _payload(run_id: str = "paper-run-001") -> dict[str, object]:
    return {
        "run_id": run_id,
        "created_timestamp": "2026-07-14T12:00:00Z",
        "starting_account_state": {
            "timestamp": "2026-07-14T12:00:00Z",
            "starting_cash": 10_000,
            "current_cash": 10_000,
            "positions": {"AAPL": 1},
        },
        "ending_account_state": {
            "timestamp": "2026-07-14T12:05:00Z",
            "starting_cash": 10_000,
            "current_cash": 9_900,
            "positions": {"AAPL": 2},
        },
        "orders": [],
        "fills": [],
    }


@pytest.fixture
def configured_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    database_path = tmp_path / "product.sqlite3"
    paper_root = tmp_path / "paper-root"
    paper_root.mkdir()
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    command.upgrade(Config(str(PROJECT_ROOT / "alembic.ini")), "head")
    return create_app(
        product_database_path=database_path,
        paper_artifact_root=paper_root,
    )


@pytest.fixture
def revision_0004_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    database_path = tmp_path / "product.sqlite3"
    paper_root = tmp_path / "paper-root"
    paper_root.mkdir()
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    command.upgrade(
        Config(str(PROJECT_ROOT / "alembic.ini")),
        RECOVERY_AUDIT_REVISION,
    )
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=database_path)
    )
    session_factory = create_product_session_factory(engine=engine)
    try:
        yield (
            create_app(
                product_database_path=database_path,
                paper_artifact_root=paper_root,
            ),
            engine,
            session_factory,
            paper_root,
        )
    finally:
        engine.dispose()


def _assert_error(response, status: int, code: str) -> None:
    assert response.status_code == status, response.text
    payload = response.json()
    assert payload["error"]["code"] == code
    request_id = response.headers[REQUEST_ID_HEADER]
    assert str(UUID(request_id)) == request_id == payload["request_id"]


def _submit_direct(
    session_factory: sessionmaker[Session],
    *,
    run_id: str,
) -> PaperJobRecord:
    request = PaperRunCommandRequest.model_validate(_payload(run_id))
    return submit_paper_job(
        session_factory=session_factory,
        command=paper_run_command_from_request(request),
    )


def _transition_direct(
    session_factory: sessionmaker[Session],
    *,
    job: PaperJobRecord,
    target_status: str,
) -> tuple[PaperJobRecord, tuple[PaperJobAttemptRecord, ...]]:
    running_timestamp = job.updated_timestamp
    with session_factory.begin() as session:
        jobs = SqlAlchemyPaperJobRepository(session=session)
        running = jobs.transition_status(
            job_id=job.job_id,
            expected_status="queued",
            target_status="running",
            updated_timestamp=running_timestamp,
        )
        assert running is not None
        attempts = SqlAlchemyPaperJobAttemptRepository(session=session)
        attempt = attempts.start_attempt(
            attempt=create_running_paper_job_attempt(
                attempt_id=str(uuid4()),
                job_id=job.job_id,
                attempt_number=1,
                started_timestamp=running_timestamp,
            )
        )
        if target_status == "failed":
            failed_timestamp = running_timestamp
            failed = jobs.transition_status(
                job_id=job.job_id,
                expected_status="running",
                target_status="failed",
                updated_timestamp=failed_timestamp,
            )
            assert failed is not None
            completed = attempts.complete_attempt(
                attempt_id=attempt.attempt_id,
                status="failed",
                completed_timestamp=failed_timestamp,
                error_code="workflow_validation_failed",
            )
            assert completed is not None
            return failed, (completed,)
        assert target_status == "running"
        return running, (attempt,)


def _durable_state(
    session_factory: sessionmaker[Session],
    *,
    job_id: str,
) -> tuple[PaperJobRecord, tuple[PaperJobAttemptRecord, ...]]:
    with session_factory() as session:
        job = SqlAlchemyPaperJobRepository(session=session).get(job_id=job_id)
        assert job is not None
        attempts = SqlAlchemyPaperJobAttemptRepository(
            session=session
        ).list_for_job(job_id=job_id)
    return job, attempts


def _add_direct_reference(
    session_factory: sessionmaker[Session],
    *,
    job_id: str,
):
    reference = create_paper_job_result_reference(
        job_id=job_id,
        created_timestamp=datetime(2026, 7, 17, 10, 0, tzinfo=timezone.utc),
    )
    with session_factory.begin() as session:
        SqlAlchemyPaperJobResultReferenceRepository(session=session).add(
            reference=reference
        )
    return reference


def _assert_0004_schema_unchanged(engine) -> None:
    with engine.connect() as connection:
        assert (
            MigrationContext.configure(connection).get_current_revision()
            == RECOVERY_AUDIT_REVISION
        )
    assert "paper_job_result_references" not in inspect(engine).get_table_names()


def test_submission_replay_list_detail_run_attempts_and_result(configured_app) -> None:
    with TestClient(configured_app) as client:
        created = client.post(
            "/api/v1/paper-jobs",
            json=_payload(),
            headers={"Idempotency-Key": "caller-key-1"},
        )
        replay = client.post(
            "/api/v1/paper-jobs",
            json=_payload(),
            headers={"Idempotency-Key": "caller-key-1"},
        )

        assert created.status_code == replay.status_code == 200
        created_submission = PaperJobSubmissionResponse.model_validate(created.json())
        replay_submission = PaperJobSubmissionResponse.model_validate(replay.json())
        assert created_submission.submission_outcome == "created"
        assert replay_submission.submission_outcome == "replayed"
        created_job = created_submission.job
        replay_job = replay_submission.job
        assert replay_job == created_job
        assert created_job.status == "queued"
        assert created_job.attempt_count == 0
        assert created_job.result_available is False
        assert created_job.result_url is None

        listed = client.get("/api/v1/paper-jobs", params={"status": "queued"})
        detail = client.get(f"/api/v1/paper-jobs/{created_job.job_id}")
        assert listed.status_code == detail.status_code == 200
        assert listed.json() == [detail.json()]

        run = client.post(f"/api/v1/paper-jobs/{created_job.job_id}/run")
        assert run.status_code == 202
        accepted_job = PaperJobResponse.model_validate(run.json())
        assert accepted_job.job_id == created_job.job_id
        assert accepted_job.status == "running"
        assert accepted_job.attempt_count == 1
        assert accepted_job.latest_attempt is not None
        assert accepted_job.latest_attempt.status == "running"

        completed = client.get(f"/api/v1/paper-jobs/{created_job.job_id}")
        attempts = client.get(
            f"/api/v1/paper-jobs/{created_job.job_id}/attempts"
        )
        result = client.get(f"/api/v1/paper-jobs/{created_job.job_id}/result")

        completed_job = PaperJobResponse.model_validate(completed.json())
        assert completed_job.status == "succeeded"
        assert completed_job.attempt_count == 1
        assert completed_job.latest_attempt is not None
        assert completed_job.latest_attempt.status == "succeeded"
        assert completed_job.result_available is True
        assert completed_job.result_url == (
            f"/api/v1/paper-jobs/{created_job.job_id}/result"
        )
        assert attempts.status_code == 200
        assert set(attempts.json()[0]) == {
            "attempt_id",
            "attempt_number",
            "status",
            "started_timestamp",
            "completed_timestamp",
            "error_code",
        }
        result_model = PaperJobResultResponse.model_validate(result.json())
        assert result_model.job_id == created_job.job_id
        assert result_model.run_id == "paper-run-001"
        assert result_model.artifact.session_summary.order_count == 0
        assert "path" not in result.text.lower()
        assert "paper-root" not in result.text


def test_concurrent_run_requests_have_one_claimed_202_winner(
    configured_app,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    barrier = Barrier(2)
    original_claim = paper_job_routes.claim_product_paper_job

    def synchronized_claim(**kwargs):
        barrier.wait(timeout=5)
        return original_claim(**kwargs)

    monkeypatch.setattr(
        paper_job_routes,
        "claim_product_paper_job",
        synchronized_claim,
    )
    monkeypatch.setattr(
        paper_job_routes,
        "execute_claimed_product_paper_job",
        lambda **_kwargs: None,
    )
    with TestClient(configured_app) as client:
        submitted = client.post(
            "/api/v1/paper-jobs",
            json=_payload("concurrent-run"),
        ).json()["job"]

        with ThreadPoolExecutor(max_workers=2) as executor:
            responses = tuple(
                executor.map(
                    lambda _index: client.post(
                        f"/api/v1/paper-jobs/{submitted['job_id']}/run"
                    ),
                    range(2),
                )
            )

    assert sorted(response.status_code for response in responses) == [202, 409]
    winner = next(response for response in responses if response.status_code == 202)
    accepted = PaperJobResponse.model_validate(winner.json())
    assert accepted.status == "running"
    assert accepted.attempt_count == 1
    assert accepted.latest_attempt is not None
    assert accepted.latest_attempt.status == "running"
    loser = next(response for response in responses if response.status_code == 409)
    assert loser.json()["error"]["code"] == "paper_job_state_conflict"


def test_recovery_response_reports_explicit_outcome(
    configured_app,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        paper_job_routes,
        "execute_claimed_product_paper_job",
        lambda **_kwargs: None,
    )
    with TestClient(configured_app) as client:
        submitted = client.post(
            "/api/v1/paper-jobs",
            json=_payload("recovery-outcome"),
        ).json()["job"]
        accepted = client.post(
            f"/api/v1/paper-jobs/{submitted['job_id']}/run"
        ).json()
        stale_before = (
            PaperJobResponse.model_validate(accepted).updated_timestamp
            + timedelta(seconds=1)
        ).isoformat()
        recovered = client.post(
            f"/api/v1/paper-jobs/{submitted['job_id']}/recover",
            json={"stale_before": stale_before},
        )

    assert recovered.status_code == 200
    response = PaperJobRecoveryResponse.model_validate(recovered.json())
    assert response.recovery_outcome == "requeued"
    assert response.job.status == "queued"
    assert response.job.latest_attempt is not None
    assert response.job.latest_attempt.status == "interrupted"


def test_existing_reference_retry_and_recover_return_stable_output_conflict(
    configured_app,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        paper_job_routes,
        "execute_claimed_product_paper_job",
        lambda **_kwargs: None,
    )
    session_factory = configured_app.state.product_session_factory
    paper_root = configured_app.state.paper_artifact_root
    assert session_factory is not None
    assert paper_root is not None
    with TestClient(configured_app) as client:
        recovery_job = client.post(
            "/api/v1/paper-jobs",
            json=_payload("reference-recovery-conflict"),
        ).json()["job"]
        accepted = client.post(
            f"/api/v1/paper-jobs/{recovery_job['job_id']}/run"
        ).json()
        recovery_reference = _add_direct_reference(
            session_factory,
            job_id=recovery_job["job_id"],
        )
        recovery_before = _durable_state(
            session_factory,
            job_id=recovery_job["job_id"],
        )
        recovered = client.post(
            f"/api/v1/paper-jobs/{recovery_job['job_id']}/recover",
            json={"stale_before": accepted["updated_timestamp"]},
        )

        retry_job = _submit_direct(
            session_factory,
            run_id="reference-retry-conflict",
        )
        failed, _ = _transition_direct(
            session_factory,
            job=retry_job,
            target_status="failed",
        )
        (Path(paper_root) / "jobs" / failed.job_id / "paper").mkdir(parents=True)
        retry_reference = _add_direct_reference(
            session_factory,
            job_id=failed.job_id,
        )
        retry_before = _durable_state(
            session_factory,
            job_id=failed.job_id,
        )
        retried = client.post(f"/api/v1/paper-jobs/{failed.job_id}/retry")

    _assert_error(recovered, 409, "paper_job_output_conflict")
    _assert_error(retried, 409, "paper_job_output_conflict")
    assert _durable_state(
        session_factory,
        job_id=recovery_job["job_id"],
    ) == recovery_before
    assert _durable_state(
        session_factory,
        job_id=failed.job_id,
    ) == retry_before
    with session_factory() as session:
        references = SqlAlchemyPaperJobResultReferenceRepository(session=session)
        assert references.get_by_job_id(
            job_id=recovery_job["job_id"]
        ) == recovery_reference
        assert references.get_by_job_id(job_id=failed.job_id) == retry_reference


def test_run_and_cancel_race_has_one_transition_winner(
    configured_app,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    barrier = Barrier(2)
    original_claim = paper_job_routes.claim_product_paper_job
    original_cancel = paper_job_routes.cancel_paper_job

    def synchronized_claim(**kwargs):
        barrier.wait(timeout=5)
        return original_claim(**kwargs)

    def synchronized_cancel(**kwargs):
        barrier.wait(timeout=5)
        return original_cancel(**kwargs)

    monkeypatch.setattr(
        paper_job_routes,
        "claim_product_paper_job",
        synchronized_claim,
    )
    monkeypatch.setattr(
        paper_job_routes,
        "cancel_paper_job",
        synchronized_cancel,
    )
    monkeypatch.setattr(
        paper_job_routes,
        "execute_claimed_product_paper_job",
        lambda **_kwargs: None,
    )
    with TestClient(configured_app) as client:
        submitted = client.post(
            "/api/v1/paper-jobs",
            json=_payload("run-cancel-race"),
        ).json()["job"]
        paths = (
            f"/api/v1/paper-jobs/{submitted['job_id']}/run",
            f"/api/v1/paper-jobs/{submitted['job_id']}/cancel",
        )
        with ThreadPoolExecutor(max_workers=2) as executor:
            responses = tuple(executor.map(client.post, paths))
        settled = client.get(
            f"/api/v1/paper-jobs/{submitted['job_id']}"
        ).json()

    assert sum(response.status_code == 409 for response in responses) == 1
    assert sum(response.status_code in {200, 202} for response in responses) == 1
    if settled["status"] == "running":
        assert settled["attempt_count"] == 1
    else:
        assert settled["status"] == "canceled"
        assert settled["attempt_count"] == 0


def test_submission_conflicts_and_validation_are_sanitized(configured_app) -> None:
    with TestClient(configured_app) as client:
        assert client.post(
            "/api/v1/paper-jobs",
            json=_payload(),
            headers={"Idempotency-Key": "same-key"},
        ).status_code == 200
        changed = _payload("changed-run")
        mismatch = client.post(
            "/api/v1/paper-jobs",
            json=changed,
            headers={"Idempotency-Key": "same-key"},
        )
        duplicate_run = client.post("/api/v1/paper-jobs", json=_payload())
        invalid_key = client.post(
            "/api/v1/paper-jobs",
            json=_payload("another-run"),
            headers={"Idempotency-Key": "invalid key"},
        )

    _assert_error(mismatch, 409, "paper_job_idempotency_conflict")
    _assert_error(duplicate_run, 409, "paper_job_conflict")
    _assert_error(invalid_key, 422, "paper_job_invalid")
    assert "same-key" not in mismatch.text
    assert "invalid key" not in invalid_key.text


def test_manual_controls_and_no_path_inputs(configured_app) -> None:
    with TestClient(configured_app) as client:
        first = client.post("/api/v1/paper-jobs", json=_payload()).json()["job"]
        canceled = client.post(f"/api/v1/paper-jobs/{first['job_id']}/cancel")
        assert canceled.status_code == 200
        assert canceled.json()["status"] == "canceled"
        _assert_error(
            client.post(f"/api/v1/paper-jobs/{first['job_id']}/cancel"),
            409,
            "paper_job_state_conflict",
        )

        second = client.post(
            "/api/v1/paper-jobs", json=_payload("paper-run-002")
        ).json()["job"]
        _assert_error(
            client.post(f"/api/v1/paper-jobs/{second['job_id']}/retry"),
            409,
            "paper_job_state_conflict",
        )
        recovery = client.post(
            f"/api/v1/paper-jobs/{second['job_id']}/recover",
            json={
                "stale_before": "2026-07-14T13:00:00Z",
                "run_dir": "C:\\private",
            },
        )
        _assert_error(recovery, 422, "request_validation_error")
        submission_with_path = _payload("paper-run-003")
        submission_with_path["run_dir"] = "C:\\private"
        _assert_error(
            client.post("/api/v1/paper-jobs", json=submission_with_path),
            422,
            "request_validation_error",
        )


def test_list_is_bounded_and_status_filter_is_exact(configured_app) -> None:
    with TestClient(configured_app) as client:
        client.post("/api/v1/paper-jobs", json=_payload())
        assert len(client.get("/api/v1/paper-jobs", params={"limit": 1}).json()) == 1
        for value in (0, 201):
            _assert_error(
                client.get("/api/v1/paper-jobs", params={"limit": value}),
                422,
                "request_validation_error",
            )
        _assert_error(
            client.get("/api/v1/paper-jobs", params={"status": "QUEUED"}),
            422,
            "request_validation_error",
        )


def test_durable_configuration_failures_are_503_and_missing_db_is_not_created(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(PRODUCT_DATABASE_PATH_ENV, raising=False)
    missing = tmp_path / "missing.sqlite3"

    absent_config = TestClient(create_app()).get("/api/v1/paper-jobs")
    missing_file = TestClient(
        create_app(product_database_path=missing)
    ).get("/api/v1/paper-jobs")
    missing_root = tmp_path / "paper-root"
    missing_root.mkdir()
    database_path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    command.upgrade(Config(str(PROJECT_ROOT / "alembic.ini")), "head")
    no_root_app = create_app(product_database_path=database_path)
    with TestClient(no_root_app) as client:
        submitted = client.post("/api/v1/paper-jobs", json=_payload()).json()["job"]
        no_root = client.post(f"/api/v1/paper-jobs/{submitted['job_id']}/run")

    _assert_error(absent_config, 503, "product_database_unavailable")
    _assert_error(missing_file, 503, "product_database_unavailable")
    _assert_error(no_root, 503, "paper_artifact_root_unavailable")
    assert not missing.exists()


def test_unmigrated_database_is_sanitized_and_existing_sync_route_is_independent(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "unmigrated.sqlite3"
    database_path.touch()
    app = create_app(product_database_path=database_path)

    durable = TestClient(app).get("/api/v1/paper-jobs")
    synchronous = TestClient(create_app()).post("/api/v1/paper-runs", json=_payload())

    _assert_error(durable, 503, "product_database_unavailable")
    assert synchronous.status_code == 200


def test_revision_0004_submission_is_rejected_before_any_durable_write(
    revision_0004_environment,
) -> None:
    app, engine, _session_factory, _paper_root = revision_0004_environment

    with TestClient(app) as client:
        durable = client.post(
            "/api/v1/paper-jobs",
            json=_payload(),
            headers={"Idempotency-Key": "preflight-key"},
        )
        synchronous = client.post(
            "/api/v1/paper-runs",
            json=_payload("synchronous-run"),
        )

    _assert_error(durable, 503, "product_database_unavailable")
    assert synchronous.status_code == 200
    with engine.connect() as connection:
        assert connection.exec_driver_sql("SELECT COUNT(*) FROM paper_jobs").scalar() == 0
        assert (
            connection.exec_driver_sql(
                "SELECT COUNT(*) FROM paper_job_submission_keys"
            ).scalar()
            == 0
        )
    _assert_0004_schema_unchanged(engine)


def test_revision_0004_cancel_is_rejected_before_queued_job_changes(
    revision_0004_environment,
) -> None:
    app, engine, session_factory, _paper_root = revision_0004_environment
    queued = _submit_direct(session_factory, run_id="queued-cancel-run")
    before = _durable_state(session_factory, job_id=queued.job_id)

    with TestClient(app) as client:
        response = client.post(f"/api/v1/paper-jobs/{queued.job_id}/cancel")

    _assert_error(response, 503, "product_database_unavailable")
    assert _durable_state(session_factory, job_id=queued.job_id) == before
    assert before[0].status == "queued"
    _assert_0004_schema_unchanged(engine)


def test_revision_0004_retry_is_rejected_before_failed_job_changes(
    revision_0004_environment,
) -> None:
    app, engine, session_factory, paper_root = revision_0004_environment
    queued = _submit_direct(session_factory, run_id="failed-retry-run")
    failed, _attempts = _transition_direct(
        session_factory,
        job=queued,
        target_status="failed",
    )
    (paper_root / "jobs" / failed.job_id / "paper").mkdir(parents=True)
    before = _durable_state(session_factory, job_id=failed.job_id)

    with TestClient(app) as client:
        response = client.post(f"/api/v1/paper-jobs/{failed.job_id}/retry")

    _assert_error(response, 503, "product_database_unavailable")
    assert _durable_state(session_factory, job_id=failed.job_id) == before
    assert before[0].status == "failed"
    assert before[1][0].status == "failed"
    _assert_0004_schema_unchanged(engine)


def test_revision_0004_recovery_is_rejected_before_running_state_changes(
    revision_0004_environment,
) -> None:
    app, engine, session_factory, paper_root = revision_0004_environment
    queued = _submit_direct(session_factory, run_id="running-recovery-run")
    running, _attempts = _transition_direct(
        session_factory,
        job=queued,
        target_status="running",
    )
    (paper_root / "jobs" / running.job_id / "paper").mkdir(parents=True)
    before = _durable_state(session_factory, job_id=running.job_id)
    stale_before = (running.updated_timestamp + timedelta(seconds=1)).isoformat()

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/paper-jobs/{running.job_id}/recover",
            json={"stale_before": stale_before},
        )

    _assert_error(response, 503, "product_database_unavailable")
    assert _durable_state(session_factory, job_id=running.job_id) == before
    assert before[0].status == "running"
    assert before[1][0].status == "running"
    _assert_0004_schema_unchanged(engine)


def test_application_owned_engine_is_disposed_on_shutdown(
    configured_app,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    disposed = Event()
    engine = configured_app.state.product_database_engine
    monkeypatch.setattr(engine, "dispose", disposed.set)

    with TestClient(configured_app) as client:
        assert client.get("/api/v1/health").status_code == 200
        assert not disposed.is_set()

    assert disposed.is_set()


def test_openapi_has_only_explicit_durable_job_schemas_and_methods() -> None:
    document = create_app().openapi()
    paths = document["paths"]

    assert set(path for path in paths if path.startswith("/api/v1/paper-jobs")) == {
        "/api/v1/paper-jobs",
        "/api/v1/paper-jobs/{job_id}",
        "/api/v1/paper-jobs/{job_id}/attempts",
        "/api/v1/paper-jobs/{job_id}/run",
        "/api/v1/paper-jobs/{job_id}/cancel",
        "/api/v1/paper-jobs/{job_id}/retry",
        "/api/v1/paper-jobs/{job_id}/recover",
        "/api/v1/paper-jobs/{job_id}/result",
    }
    assert set(paths["/api/v1/paper-jobs"]) == {"get", "post"}
    assert set(paths["/api/v1/paper-jobs/{job_id}"]) == {"get"}
    schemas = document["components"]["schemas"]
    assert "PaperJobResponse" in schemas
    assert "PaperJobSubmissionResponse" in schemas
    assert "PaperJobRecoveryResponse" in schemas
    assert "PaperJobResultResponse" in schemas
    assert "PaperRunCommandRequest" in schemas
    assert not any("Row" in name or "Session" == name for name in schemas)
