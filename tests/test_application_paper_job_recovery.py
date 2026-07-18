"""Tests for explicit interrupted-job recovery and manual retry."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command as alembic_command
from alembic.config import Config

import el_psy_quant.application.paper_jobs as service
from el_psy_quant.application import (
    PaperAccountStateCommandInput,
    PaperJobExecutionError,
    PaperJobOutputConflictError,
    PaperJobNotFoundError,
    PaperJobRecoveryError,
    PaperJobStateConflictError,
    PaperRunCommand,
    get_paper_job,
    list_paper_job_attempts,
    recover_interrupted_paper_job,
    retry_failed_paper_job,
    run_paper_job_once,
    submit_paper_job,
)
from el_psy_quant.configured_paper import run_paper_workflow_request
from el_psy_quant.outputs import create_configured_paper_run_output_paths
from el_psy_quant.persistence import (
    SqlAlchemyPaperJobAttemptRepository,
    SqlAlchemyPaperJobRepository,
    create_running_paper_job_attempt,
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JOB_ID = "00000000-0000-4000-8000-000000000001"
NOW = datetime(2026, 7, 14, 11, 0, tzinfo=timezone.utc)


@pytest.fixture
def session_factory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    database_path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    alembic_command.upgrade(Config(str(PROJECT_ROOT / "alembic.ini")), "head")
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=database_path)
    )
    factory = create_product_session_factory(engine=engine)
    try:
        yield factory
    finally:
        engine.dispose()


def _command(run_id: str = "recovery-run") -> PaperRunCommand:
    starting = PaperAccountStateCommandInput(
        timestamp="2026-07-14T10:00:00Z",
        starting_cash=1_000,
        current_cash=1_000,
        positions={},
    )
    ending = PaperAccountStateCommandInput(
        timestamp="2026-07-14T10:30:00Z",
        starting_cash=1_000,
        current_cash=1_000,
        positions={},
    )
    return PaperRunCommand(
        run_id=run_id,
        created_timestamp="2026-07-14T10:45:00Z",
        starting_account_state=starting,
        ending_account_state=ending,
        orders=(),
        fills=(),
    )


def _submit(session_factory, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(service, "_new_job_id", lambda: JOB_ID)
    monkeypatch.setattr(service, "_utc_now", lambda: NOW)
    return submit_paper_job(session_factory=session_factory, command=_command())


def _running(session_factory, monkeypatch: pytest.MonkeyPatch, *, legacy=False):
    job = _submit(session_factory, monkeypatch)
    if legacy:
        with session_factory.begin() as session:
            running = SqlAlchemyPaperJobRepository(session=session).transition_status(
                job_id=job.job_id,
                expected_status="queued",
                target_status="running",
                updated_timestamp=NOW,
            )
        assert running is not None
        return running
    running, _ = service._claim_job_and_attempt(
        session_factory=session_factory,
        job_id=job.job_id,
    )
    return running


def test_recovery_validates_stale_threshold_and_running_state(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    running = _running(session_factory, monkeypatch)

    with pytest.raises(ValueError, match="stale_before"):
        recover_interrupted_paper_job(
            session_factory=session_factory,
            job_id=running.job_id,
            run_dir=tmp_path,
            stale_before=datetime(2026, 7, 14, 11, 0),
        )
    with pytest.raises(PaperJobStateConflictError):
        recover_interrupted_paper_job(
            session_factory=session_factory,
            job_id=running.job_id,
            run_dir=tmp_path,
            stale_before=NOW - timedelta(microseconds=1),
        )


def test_no_outputs_requeues_and_interrupts_attempt_without_file_changes(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    running = _running(session_factory, monkeypatch)
    before = tuple(tmp_path.rglob("*"))

    result = recover_interrupted_paper_job(
        session_factory=session_factory,
        job_id=running.job_id,
        run_dir=tmp_path,
        stale_before=NOW,
    )

    assert result.outcome == "requeued"
    assert result.job.status == "queued"
    assert result.attempt.status == "interrupted"
    assert result.attempt.error_code == "interrupted_without_output"
    assert tuple(tmp_path.rglob("*")) == before


def test_two_valid_consistent_outputs_recover_to_succeeded_without_rewrite(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    running = _running(session_factory, monkeypatch)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    workflow = run_paper_workflow_request(
        request=running.request,
        run_dir=run_dir,
        output_write_mode="exclusive",
    )
    artifact_before = workflow.paper_run_artifact_path.read_bytes()
    summary_before = workflow.paper_run_result_summary_path.read_bytes()

    result = recover_interrupted_paper_job(
        session_factory=session_factory,
        job_id=running.job_id,
        run_dir=run_dir,
        stale_before=NOW,
    )

    assert result.outcome == "succeeded"
    assert result.job.status == "succeeded"
    assert result.attempt.status == "succeeded"
    assert result.attempt.error_code is None
    assert workflow.paper_run_artifact_path.read_bytes() == artifact_before
    assert workflow.paper_run_result_summary_path.read_bytes() == summary_before


@pytest.mark.parametrize("existing", ("artifact", "summary"))
def test_one_output_fails_with_partial_code_and_preserves_file(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    existing: str,
) -> None:
    running = _running(session_factory, monkeypatch)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    paths = create_configured_paper_run_output_paths(run_dir=run_dir)
    path = (
        paths.paper_run_artifact_path
        if existing == "artifact"
        else paths.paper_run_result_summary_path
    )
    path.parent.mkdir()
    content = b"partial-authoritative-output"
    path.write_bytes(content)

    result = recover_interrupted_paper_job(
        session_factory=session_factory,
        job_id=running.job_id,
        run_dir=run_dir,
        stale_before=NOW,
    )

    assert result.outcome == "failed"
    assert result.job.status == "failed"
    assert result.attempt.error_code == "partial_output_detected"
    assert path.read_bytes() == content


def test_invalid_or_inconsistent_outputs_fail_and_preserve_both(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    running = _running(session_factory, monkeypatch)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    paths = create_configured_paper_run_output_paths(run_dir=run_dir)
    paths.paper_run_artifact_path.parent.mkdir()
    artifact = b"{invalid"
    summary = b"{}"
    paths.paper_run_artifact_path.write_bytes(artifact)
    paths.paper_run_result_summary_path.write_bytes(summary)

    result = recover_interrupted_paper_job(
        session_factory=session_factory,
        job_id=running.job_id,
        run_dir=run_dir,
        stale_before=NOW,
    )

    assert result.outcome == "failed"
    assert result.attempt.error_code == "invalid_output_detected"
    assert paths.paper_run_artifact_path.read_bytes() == artifact
    assert paths.paper_run_result_summary_path.read_bytes() == summary


def test_read_oserror_leaves_job_and_attempt_running(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    running = _running(session_factory, monkeypatch)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    paths = create_configured_paper_run_output_paths(run_dir=run_dir)
    paths.paper_run_artifact_path.parent.mkdir()
    paths.paper_run_artifact_path.write_text("{}", encoding="utf-8")
    paths.paper_run_result_summary_path.write_text("{}", encoding="utf-8")
    failure = PermissionError("private path")

    def forbidden(_path):
        raise failure

    monkeypatch.setattr(service, "read_paper_trading_artifact_file", forbidden)

    with pytest.raises(PaperJobRecoveryError) as raised:
        recover_interrupted_paper_job(
            session_factory=session_factory,
            job_id=running.job_id,
            run_dir=run_dir,
            stale_before=NOW,
        )

    assert raised.value.__cause__ is failure
    assert get_paper_job(
        session_factory=session_factory,
        job_id=running.job_id,
    ).status == "running"
    assert list_paper_job_attempts(
        session_factory=session_factory,
        job_id=running.job_id,
    )[0].status == "running"


def test_recovery_filesystem_inspection_has_no_open_database_session(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    running = _running(session_factory, monkeypatch)
    active = 0
    original_inspect = service._inspect_recovery_outputs

    class TrackingFactory:
        @contextmanager
        def __call__(self):
            nonlocal active
            with session_factory() as session:
                active += 1
                try:
                    yield session
                finally:
                    active -= 1

        def begin(self):
            return session_factory.begin()

    def inspect(**kwargs):
        assert active == 0
        return original_inspect(**kwargs)

    monkeypatch.setattr(service, "_inspect_recovery_outputs", inspect)

    recover_interrupted_paper_job(
        session_factory=TrackingFactory(),  # type: ignore[arg-type]
        job_id=running.job_id,
        run_dir=tmp_path,
        stale_before=NOW,
    )


def test_concurrent_recoveries_have_one_optimistic_winner(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    running = _running(session_factory, monkeypatch)

    def recover():
        try:
            return recover_interrupted_paper_job(
                session_factory=session_factory,
                job_id=running.job_id,
                run_dir=tmp_path,
                stale_before=NOW,
            )
        except PaperJobStateConflictError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(lambda _: recover(), range(2)))

    assert sum(not isinstance(result, Exception) for result in results) == 1
    assert sum(isinstance(result, PaperJobStateConflictError) for result in results) == 1
    attempts = list_paper_job_attempts(
        session_factory=session_factory,
        job_id=running.job_id,
    )
    assert len(attempts) == 1
    assert attempts[0].status == "interrupted"


def test_legacy_running_job_without_attempt_gets_one_synthetic_attempt(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    running = _running(session_factory, monkeypatch, legacy=True)
    assert list_paper_job_attempts(
        session_factory=session_factory,
        job_id=running.job_id,
    ) == ()

    result = recover_interrupted_paper_job(
        session_factory=session_factory,
        job_id=running.job_id,
        run_dir=tmp_path,
        stale_before=NOW,
    )

    assert result.attempt.attempt_number == 1
    assert result.attempt.started_timestamp == running.updated_timestamp
    assert result.attempt.status == "interrupted"


def test_recovery_rejects_existing_terminal_attempt_without_synthetic_result(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    running = _running(session_factory, monkeypatch)
    with session_factory.begin() as session:
        attempts = SqlAlchemyPaperJobAttemptRepository(session=session)
        active = attempts.get_running_for_job(job_id=running.job_id)
        assert active is not None
        completed = attempts.complete_attempt(
            attempt_id=active.attempt_id,
            status="interrupted",
            completed_timestamp=NOW,
            error_code="interrupted_without_output",
        )
        assert completed is not None
    before = list_paper_job_attempts(
        session_factory=session_factory,
        job_id=running.job_id,
    )
    monkeypatch.setattr(
        service,
        "_new_attempt_id",
        lambda: (_ for _ in ()).throw(AssertionError("synthetic attempt created")),
    )

    with pytest.raises(PaperJobStateConflictError):
        recover_interrupted_paper_job(
            session_factory=session_factory,
            job_id=running.job_id,
            run_dir=tmp_path,
            stale_before=NOW,
        )

    assert get_paper_job(
        session_factory=session_factory,
        job_id=running.job_id,
    ).status == "running"
    assert list_paper_job_attempts(
        session_factory=session_factory,
        job_id=running.job_id,
    ) == before
    assert len(before) == 1
    assert before[0].status == "interrupted"


def test_recovery_rejects_multiple_running_attempts_without_modifying_them(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    running = _running(session_factory, monkeypatch)
    with session_factory.begin() as session:
        attempts = SqlAlchemyPaperJobAttemptRepository(session=session)
        attempts.start_attempt(
            attempt=create_running_paper_job_attempt(
                attempt_id="00000000-0000-4000-8000-000000000099",
                job_id=running.job_id,
                attempt_number=2,
                started_timestamp=NOW,
            )
        )
    before = list_paper_job_attempts(
        session_factory=session_factory,
        job_id=running.job_id,
    )

    with pytest.raises(PaperJobStateConflictError):
        recover_interrupted_paper_job(
            session_factory=session_factory,
            job_id=running.job_id,
            run_dir=tmp_path,
            stale_before=NOW,
        )

    assert get_paper_job(
        session_factory=session_factory,
        job_id=running.job_id,
    ).status == "running"
    assert list_paper_job_attempts(
        session_factory=session_factory,
        job_id=running.job_id,
    ) == before
    assert len(before) == 2
    assert all(attempt.status == "running" for attempt in before)


def _failed_job(session_factory, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    job = _submit(session_factory, monkeypatch)
    run_dir = tmp_path / "failed-run"
    run_dir.mkdir()

    def fail(**_kwargs):
        raise ValueError("expected")

    monkeypatch.setattr(service, "run_paper_workflow_request", fail)
    with pytest.raises(PaperJobExecutionError):
        run_paper_job_once(
            session_factory=session_factory,
            job_id=job.job_id,
            run_dir=run_dir,
        )
    return job


def test_retry_requeues_failed_without_execution_or_attempt_then_next_run_is_two(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _failed_job(session_factory, tmp_path, monkeypatch)
    retry_dir = tmp_path / "retry"
    retry_dir.mkdir()
    original_attempts = list_paper_job_attempts(
        session_factory=session_factory,
        job_id=job.job_id,
    )
    monkeypatch.setattr(
        service,
        "run_paper_workflow_request",
        run_paper_workflow_request,
    )

    queued = retry_failed_paper_job(
        session_factory=session_factory,
        job_id=job.job_id,
        run_dir=retry_dir,
    )

    assert queued.status == "queued"
    assert list_paper_job_attempts(
        session_factory=session_factory,
        job_id=job.job_id,
    ) == original_attempts
    result = run_paper_job_once(
        session_factory=session_factory,
        job_id=job.job_id,
        run_dir=retry_dir,
    )
    assert result.attempt.attempt_number == 2


def test_retry_output_conflict_leaves_job_failed(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _failed_job(session_factory, tmp_path, monkeypatch)
    retry_dir = tmp_path / "retry"
    retry_dir.mkdir()
    paths = create_configured_paper_run_output_paths(run_dir=retry_dir)
    paths.paper_run_artifact_path.parent.mkdir()
    paths.paper_run_artifact_path.write_text("preserve", encoding="utf-8")

    with pytest.raises(PaperJobOutputConflictError):
        retry_failed_paper_job(
            session_factory=session_factory,
            job_id=job.job_id,
            run_dir=retry_dir,
        )

    assert get_paper_job(
        session_factory=session_factory,
        job_id=job.job_id,
    ).status == "failed"
    assert paths.paper_run_artifact_path.read_text(encoding="utf-8") == "preserve"


def test_concurrent_retry_has_one_queued_winner(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _failed_job(session_factory, tmp_path, monkeypatch)
    retry_dir = tmp_path / "retry"
    retry_dir.mkdir()

    def retry():
        try:
            return retry_failed_paper_job(
                session_factory=session_factory,
                job_id=job.job_id,
                run_dir=retry_dir,
            )
        except PaperJobStateConflictError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = tuple(executor.map(lambda _index: retry(), range(2)))

    assert sum(
        not isinstance(outcome, Exception) for outcome in outcomes
    ) == 1
    assert sum(
        isinstance(outcome, PaperJobStateConflictError) for outcome in outcomes
    ) == 1
    assert get_paper_job(
        session_factory=session_factory,
        job_id=job.job_id,
    ).status == "queued"
    assert len(
        list_paper_job_attempts(
            session_factory=session_factory,
            job_id=job.job_id,
        )
    ) == 1


def test_retry_non_failed_status_conflicts(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)

    with pytest.raises(PaperJobStateConflictError):
        retry_failed_paper_job(
            session_factory=session_factory,
            job_id=job.job_id,
            run_dir=tmp_path,
        )


def test_recovery_and_retry_missing_job_are_explicit_not_found(
    session_factory,
    tmp_path: Path,
) -> None:
    with pytest.raises(PaperJobNotFoundError):
        recover_interrupted_paper_job(
            session_factory=session_factory,
            job_id=JOB_ID,
            run_dir=tmp_path,
            stale_before=NOW,
        )
    with pytest.raises(PaperJobNotFoundError):
        retry_failed_paper_job(
            session_factory=session_factory,
            job_id=JOB_ID,
            run_dir=tmp_path,
        )
