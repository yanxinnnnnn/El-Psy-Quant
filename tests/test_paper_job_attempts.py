"""Tests for Sprint 149 execution-attempt and sanitized error audit."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command as alembic_command
from alembic.config import Config

import el_psy_quant.application.paper_jobs as service
from el_psy_quant.application import (
    PaperAccountStateCommandInput,
    PaperJobExecutionError,
    PaperJobStateConflictError,
    PaperRunCommand,
    list_paper_job_attempts,
    run_paper_job_once,
    submit_paper_job,
)
from el_psy_quant.persistence import (
    PaperJobAttemptRecord,
    SqlAlchemyPaperJobAttemptRepository,
    create_product_database_engine,
    create_product_session_factory,
    create_running_paper_job_attempt,
    resolve_product_database_config,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JOB_ID = "00000000-0000-4000-8000-000000000001"
ATTEMPT_ID = "00000000-0000-4000-8000-000000000101"
NOW = datetime(2026, 7, 14, 10, 0, tzinfo=timezone.utc)


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


def _command(run_id: str = "attempt-run") -> PaperRunCommand:
    account = PaperAccountStateCommandInput(
        timestamp="2026-07-14T09:00:00Z",
        starting_cash=1_000,
        current_cash=1_000,
        positions={},
    )
    return PaperRunCommand(
        run_id=run_id,
        created_timestamp="2026-07-14T09:30:00Z",
        starting_account_state=account,
        ending_account_state=replace(account, timestamp="2026-07-14T09:15:00Z"),
        orders=(),
        fills=(),
    )


def _submit(session_factory, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(service, "_new_job_id", lambda: JOB_ID)
    return submit_paper_job(session_factory=session_factory, command=_command())


def test_attempt_contract_enforces_state_and_error_invariants() -> None:
    running = create_running_paper_job_attempt(
        attempt_id=ATTEMPT_ID,
        job_id=JOB_ID,
        attempt_number=1,
        started_timestamp=NOW,
    )
    assert running.status == "running"
    assert running.completed_timestamp is None
    assert running.error_code is None

    invalid = (
        {"attempt_number": 0},
        {"completed_timestamp": NOW},
        {"error_code": "filesystem_io_failed"},
        {"status": "succeeded"},
        {
            "status": "failed",
            "completed_timestamp": NOW,
            "error_code": None,
        },
        {
            "status": "failed",
            "completed_timestamp": NOW - timedelta(seconds=1),
            "error_code": "filesystem_io_failed",
        },
        {
            "status": "failed",
            "completed_timestamp": NOW,
            "error_code": "private_exception",
        },
    )
    for changes in invalid:
        with pytest.raises(ValueError):
            replace(running, **changes)


def test_repository_start_list_complete_and_rollback_are_caller_owned(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)
    attempt = create_running_paper_job_attempt(
        attempt_id=ATTEMPT_ID,
        job_id=job.job_id,
        attempt_number=1,
        started_timestamp=NOW,
    )
    with session_factory() as session:
        repository = SqlAlchemyPaperJobAttemptRepository(session=session)
        repository.start_attempt(attempt=attempt)
        session.rollback()
    assert list_paper_job_attempts(
        session_factory=session_factory,
        job_id=job.job_id,
    ) == ()

    with session_factory.begin() as session:
        repository = SqlAlchemyPaperJobAttemptRepository(session=session)
        repository.start_attempt(attempt=attempt)
        assert repository.next_attempt_number(job_id=job.job_id) == 2
    with session_factory.begin() as session:
        completed = SqlAlchemyPaperJobAttemptRepository(
            session=session
        ).complete_attempt(
            attempt_id=attempt.attempt_id,
            status="failed",
            completed_timestamp=NOW + timedelta(seconds=1),
            error_code="workflow_validation_failed",
        )
    assert completed is not None
    assert completed.status == "failed"
    assert list_paper_job_attempts(
        session_factory=session_factory,
        job_id=job.job_id,
    ) == (completed,)


def test_successful_runner_claim_and_completion_share_attempt_audit(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)
    monkeypatch.setattr(service, "_new_attempt_id", lambda: ATTEMPT_ID)
    claim_time = job.updated_timestamp + timedelta(seconds=1)
    completion_time = claim_time + timedelta(seconds=1)
    times = iter((claim_time, completion_time))
    monkeypatch.setattr(service, "_utc_now", lambda: next(times))
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    result = run_paper_job_once(
        session_factory=session_factory,
        job_id=job.job_id,
        run_dir=run_dir,
    )

    assert result.job.status == "succeeded"
    assert result.attempt.status == "succeeded"
    assert result.attempt.attempt_id == ATTEMPT_ID
    assert result.attempt.started_timestamp == claim_time
    assert result.attempt.completed_timestamp == completion_time
    assert result.job.updated_timestamp == completion_time
    assert list_paper_job_attempts(
        session_factory=session_factory,
        job_id=job.job_id,
    ) == (result.attempt,)


def test_claim_rolls_back_job_when_attempt_start_fails(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)
    original = service.SqlAlchemyPaperJobAttemptRepository.start_attempt

    def fail_after_flush(self, *, attempt):
        original(self, attempt=attempt)
        raise RuntimeError("attempt start failed")

    monkeypatch.setattr(
        service.SqlAlchemyPaperJobAttemptRepository,
        "start_attempt",
        fail_after_flush,
    )

    with pytest.raises(RuntimeError, match="attempt start failed"):
        run_paper_job_once(
            session_factory=session_factory,
            job_id=job.job_id,
            run_dir=tmp_path,
        )

    from el_psy_quant.application import get_paper_job  # noqa: PLC0415

    assert get_paper_job(
        session_factory=session_factory,
        job_id=job.job_id,
    ).status == "queued"
    assert list_paper_job_attempts(
        session_factory=session_factory,
        job_id=job.job_id,
    ) == ()


def test_terminal_job_transition_rolls_back_when_attempt_completion_fails(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    original = service.SqlAlchemyPaperJobAttemptRepository.complete_attempt

    def fail_after_update(self, **kwargs):
        original(self, **kwargs)
        raise RuntimeError("attempt completion failed")

    monkeypatch.setattr(
        service.SqlAlchemyPaperJobAttemptRepository,
        "complete_attempt",
        fail_after_update,
    )

    with pytest.raises(RuntimeError, match="attempt completion failed"):
        run_paper_job_once(
            session_factory=session_factory,
            job_id=job.job_id,
            run_dir=run_dir,
        )

    from el_psy_quant.application import get_paper_job  # noqa: PLC0415

    assert get_paper_job(
        session_factory=session_factory,
        job_id=job.job_id,
    ).status == "running"
    assert list_paper_job_attempts(
        session_factory=session_factory,
        job_id=job.job_id,
    )[0].status == "running"


@pytest.mark.parametrize(
    ("failure", "error_code"),
    (
        (ValueError("private validation"), "workflow_validation_failed"),
        (FileExistsError("private output"), "output_conflict"),
        (OSError("private filesystem"), "filesystem_io_failed"),
    ),
)
def test_expected_failures_persist_only_sanitized_error_codes(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: Exception,
    error_code: str,
) -> None:
    job = _submit(session_factory, monkeypatch)
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    def fail(**_kwargs):
        raise failure

    monkeypatch.setattr(service, "run_paper_workflow_request", fail)

    with pytest.raises(PaperJobExecutionError) as raised:
        run_paper_job_once(
            session_factory=session_factory,
            job_id=job.job_id,
            run_dir=run_dir,
        )

    assert raised.value.__cause__ is failure
    attempt = list_paper_job_attempts(
        session_factory=session_factory,
        job_id=job.job_id,
    )[0]
    assert attempt.status == "failed"
    assert attempt.error_code == error_code
    assert all(
        private not in repr(attempt)
        for private in (str(failure), type(failure).__name__)
    )


def test_programming_failure_leaves_job_and_attempt_running(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    def fail(**_kwargs):
        raise RuntimeError("programming")

    monkeypatch.setattr(service, "run_paper_workflow_request", fail)
    with pytest.raises(RuntimeError):
        run_paper_job_once(
            session_factory=session_factory,
            job_id=job.job_id,
            run_dir=run_dir,
        )

    attempt = list_paper_job_attempts(
        session_factory=session_factory,
        job_id=job.job_id,
    )[0]
    assert attempt.status == "running"
    assert attempt.completed_timestamp is None


def test_concurrent_claim_loser_creates_no_second_attempt(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)
    run_dirs = (tmp_path / "one", tmp_path / "two")
    for run_dir in run_dirs:
        run_dir.mkdir()

    def run(run_dir: Path):
        try:
            return run_paper_job_once(
                session_factory=session_factory,
                job_id=job.job_id,
                run_dir=run_dir,
            )
        except PaperJobStateConflictError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(run, run_dirs))

    assert sum(not isinstance(result, Exception) for result in results) == 1
    assert sum(isinstance(result, PaperJobStateConflictError) for result in results) == 1
    assert len(
        list_paper_job_attempts(
            session_factory=session_factory,
            job_id=job.job_id,
        )
    ) == 1


def test_attempt_repository_exposes_no_generic_mutation_surface(
    session_factory,
) -> None:
    with session_factory() as session:
        repository = SqlAlchemyPaperJobAttemptRepository(session=session)
        assert all(
            not hasattr(repository, name)
            for name in ("update", "delete", "scan", "claim_next", "patch")
        )
        assert isinstance(repository.list_for_job(job_id=JOB_ID), tuple)


def test_attempt_record_contains_only_approved_fields() -> None:
    assert set(PaperJobAttemptRecord.__dataclass_fields__) == {
        "record_schema_version",
        "attempt_id",
        "job_id",
        "attempt_number",
        "status",
        "started_timestamp",
        "completed_timestamp",
        "error_code",
    }
