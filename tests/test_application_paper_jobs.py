"""Tests for explicit durable paper-job submission and reads."""

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from alembic import command as alembic_command
from alembic.config import Config
from sqlalchemy import select

import el_psy_quant.application.paper_jobs as service
import el_psy_quant.application.paper_runs as paper_run_service
import el_psy_quant.persistence.paper_job_repository as repository_module
import el_psy_quant.persistence.paper_jobs as paper_jobs_module
from el_psy_quant.application import (
    PaperAccountStateCommandInput,
    PaperFillCommandInput,
    PaperJobConflictError,
    PaperJobNotFoundError,
    PaperOrderCommandInput,
    PaperRunCommand,
    PaperRunInvalidError,
    get_paper_job,
    get_paper_job_by_run_id,
    list_paper_jobs,
    submit_paper_job,
)
from el_psy_quant.persistence import (
    SqlAlchemyPaperJobRepository,
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV
from el_psy_quant.persistence.paper_job_model import PaperJobRow

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JOB_ID = "12345678-1234-4abc-8def-1234567890ab"
NOW = datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc)


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


def _account(timestamp: str, cash: float, positions: dict[str, float]):
    return PaperAccountStateCommandInput(
        timestamp=timestamp,
        starting_cash=10_000,
        current_cash=cash,
        positions=positions,
    )


def _command(run_id: object = " durable-run ") -> PaperRunCommand:
    return PaperRunCommand(
        run_id=run_id,
        created_timestamp="2026-07-13T11:59:00Z",
        starting_account_state=_account("2026-07-13T11:00:00Z", 10_000, {"aapl": 1}),
        ending_account_state=_account("2026-07-13T11:30:00Z", 9_000, {"aapl": 2}),
        orders=(
            PaperOrderCommandInput(
                order_id=" order-1 ",
                timestamp="2026-07-13T11:10:00Z",
                symbol="aapl",
                side="BUY",
                quantity=1,
                status="FILLED",
            ),
        ),
        fills=(
            PaperFillCommandInput(
                timestamp="2026-07-13T11:11:00Z",
                symbol="aapl",
                side="BUY",
                quantity=1,
                price=1_000,
                order_id=" order-1 ",
            ),
        ),
    )


def _deterministic_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(service, "_new_job_id", lambda: JOB_ID)
    monkeypatch.setattr(service, "_utc_now", lambda: NOW)


def test_valid_submission_creates_exactly_one_queued_record_without_execution(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _deterministic_identity(monkeypatch)

    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("submission must not execute")

    monkeypatch.setattr(paper_run_service, "run_paper_trading_request", forbidden)
    job = submit_paper_job(session_factory=session_factory, command=_command())

    assert job.job_id == JOB_ID
    assert job.run_id == "durable-run"
    assert job.status == "queued"
    assert job.request.run_id == "durable-run"
    assert job.request.orders[0].order_id == "order-1"
    assert job.submitted_timestamp == job.updated_timestamp == NOW
    assert list_paper_jobs(session_factory=session_factory) == (job,)


def test_validation_and_serialization_finish_before_transaction(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _deterministic_identity(monkeypatch)
    events: list[str] = []
    transaction_started = False
    prepared_payload: str | None = None
    original_serialize = paper_jobs_module.serialize_paper_run_request

    def tracked_serialize(request):
        nonlocal prepared_payload
        if transaction_started:
            raise AssertionError("request serialization occurred after begin()")
        events.append("serialize")
        prepared_payload = original_serialize(request)
        return prepared_payload

    class TrackingFactory:
        def begin(self):
            nonlocal transaction_started
            events.append("begin")
            transaction_started = True
            return session_factory.begin()

    monkeypatch.setattr(
        paper_jobs_module,
        "serialize_paper_run_request",
        tracked_serialize,
    )
    monkeypatch.setattr(
        repository_module,
        "serialize_paper_run_request",
        tracked_serialize,
        raising=False,
    )

    submit_paper_job(session_factory=TrackingFactory(), command=_command())  # type: ignore[arg-type]

    assert events == ["serialize", "begin"]
    with session_factory() as session:
        stored_payload = session.scalar(
            select(PaperJobRow.request_payload).where(PaperJobRow.job_id == JOB_ID)
        )
    assert stored_payload == prepared_payload


def test_duplicate_run_is_explicit_conflict_not_idempotent_success(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ids = iter(
        (
            "00000000-0000-4000-8000-000000000001",
            "00000000-0000-4000-8000-000000000002",
        )
    )
    monkeypatch.setattr(service, "_new_job_id", lambda: next(ids))
    monkeypatch.setattr(service, "_utc_now", lambda: NOW)
    first = submit_paper_job(session_factory=session_factory, command=_command())

    with pytest.raises(
        PaperJobConflictError,
        match="paper job conflicts with an existing identity",
    ):
        submit_paper_job(session_factory=session_factory, command=_command())

    assert list_paper_jobs(session_factory=session_factory) == (first,)


def test_invalid_command_opens_no_transaction_and_creates_no_row(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ForbiddenFactory:
        def begin(self):
            raise AssertionError("invalid command must not open a transaction")

    with pytest.raises(PaperRunInvalidError, match="paper run request is invalid"):
        submit_paper_job(
            session_factory=ForbiddenFactory(),  # type: ignore[arg-type]
            command=replace(_command(), run_id="   "),
        )

    assert list_paper_jobs(session_factory=session_factory) == ()


def test_database_failure_rolls_back_fully(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _deterministic_identity(monkeypatch)
    original = service.SqlAlchemyPaperJobRepository.add

    def fail_after_flush(self, *, job, prepared_request):
        original(self, job=job, prepared_request=prepared_request)
        raise RuntimeError("database write failed")

    monkeypatch.setattr(service.SqlAlchemyPaperJobRepository, "add", fail_after_flush)

    with pytest.raises(RuntimeError, match="database write failed"):
        submit_paper_job(session_factory=session_factory, command=_command())
    assert list_paper_jobs(session_factory=session_factory) == ()


def test_get_list_filter_and_explicit_not_found(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _deterministic_identity(monkeypatch)
    job = submit_paper_job(session_factory=session_factory, command=_command())

    assert get_paper_job(session_factory=session_factory, job_id=JOB_ID) == job
    assert (
        get_paper_job_by_run_id(
            session_factory=session_factory,
            run_id="durable-run",
        )
        == job
    )
    assert list_paper_jobs(session_factory=session_factory, status="queued") == (job,)
    assert list_paper_jobs(session_factory=session_factory, status="running") == ()
    with pytest.raises(PaperJobNotFoundError, match="paper job not found"):
        get_paper_job(
            session_factory=session_factory,
            job_id="00000000-0000-4000-8000-000000000099",
        )
    with pytest.raises(PaperJobNotFoundError, match="paper job not found"):
        get_paper_job_by_run_id(
            session_factory=session_factory,
            run_id="missing",
        )


def test_application_surface_has_only_explicit_sprint_149_job_control() -> None:
    from el_psy_quant import application

    assert application.submit_paper_job is submit_paper_job
    assert application.get_paper_job is get_paper_job
    assert application.list_paper_jobs is list_paper_jobs
    assert callable(application.run_paper_job_once)
    assert callable(application.cancel_paper_job)
    assert callable(application.recover_interrupted_paper_job)
    assert callable(application.retry_failed_paper_job)
    assert callable(application.get_paper_job_by_idempotency_key)
    assert callable(application.list_paper_job_attempts)
    forbidden = {
        "claim_paper_job",
        "update_paper_job_status",
        "PaperJobWorker",
        "claim_next_paper_job",
        "scan_stale_paper_jobs",
        "start_paper_job_worker",
    }
    assert all(not hasattr(application, name) for name in forbidden)


def test_repository_remains_independent_from_artifact_index(session_factory) -> None:
    with session_factory() as session:
        repository = SqlAlchemyPaperJobRepository(session=session)
        assert repository.list() == ()
        assert not hasattr(repository, "artifact_index")
