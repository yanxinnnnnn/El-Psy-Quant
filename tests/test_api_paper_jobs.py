"""HTTP tests for the Sprint 150 durable paper-job boundary."""

from pathlib import Path
from threading import Event
from uuid import UUID

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from el_psy_quant.api.app import create_app
from el_psy_quant.api.middleware import REQUEST_ID_HEADER
from el_psy_quant.api.paper_job_schemas import (
    PaperJobResponse,
    PaperJobResultResponse,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV

PROJECT_ROOT = Path(__file__).resolve().parents[1]


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


def _assert_error(response, status: int, code: str) -> None:
    assert response.status_code == status
    payload = response.json()
    assert payload["error"]["code"] == code
    request_id = response.headers[REQUEST_ID_HEADER]
    assert str(UUID(request_id)) == request_id == payload["request_id"]


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
        created_job = PaperJobResponse.model_validate(created.json())
        replay_job = PaperJobResponse.model_validate(replay.json())
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
        assert run.json()["job_id"] == created_job.job_id

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
        first = client.post("/api/v1/paper-jobs", json=_payload()).json()
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
        ).json()
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
        submitted = client.post("/api/v1/paper-jobs", json=_payload()).json()
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
    assert "PaperJobResultResponse" in schemas
    assert "PaperRunCommandRequest" in schemas
    assert not any("Row" in name or "Session" == name for name in schemas)
