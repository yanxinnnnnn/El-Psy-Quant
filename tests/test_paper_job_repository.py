"""Integration tests for the caller-owned paper-job repository."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

import el_psy_quant.paper.run_execution as paper_execution
from el_psy_quant.paper import (
    create_paper_account_state,
    create_paper_run_request,
)
from el_psy_quant.persistence import (
    PaperJobRecord,
    SqlAlchemyPaperJobRepository,
    create_product_database_engine,
    create_product_session_factory,
    create_queued_paper_job_record,
    resolve_product_database_config,
    serialize_paper_run_request,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV
from el_psy_quant.persistence.paper_job_model import PaperJobRow

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIRST_ID = "00000000-0000-4000-8000-000000000001"
SECOND_ID = "00000000-0000-4000-8000-000000000002"
NOW = datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    database_path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    command.upgrade(Config(str(PROJECT_ROOT / "alembic.ini")), "head")
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=database_path)
    )
    factory = create_product_session_factory(engine=engine)
    try:
        yield database_path, engine, factory
    finally:
        engine.dispose()


def _request(run_id: str):
    starting = create_paper_account_state(
        starting_cash=1_000,
        current_cash=1_000,
        positions={"AAPL": 1},
        timestamp="2026-07-13T11:00:00Z",
    )
    ending = create_paper_account_state(
        starting_cash=1_000,
        current_cash=900,
        positions={"AAPL": 2},
        timestamp="2026-07-13T11:30:00Z",
    )
    return create_paper_run_request(
        run_id=run_id,
        created_timestamp="2026-07-13T11:45:00Z",
        starting_account_state=starting,
        ending_account_state=ending,
        orders=(),
        fills=(),
    )


def _job(job_id: str, run_id: str, timestamp: datetime = NOW) -> PaperJobRecord:
    return create_queued_paper_job_record(
        job_id=job_id,
        request=_request(run_id),
        submitted_timestamp=timestamp,
    )


def test_add_get_get_by_run_and_list_round_trip_typed_records(database) -> None:
    _, _, factory = database
    first = _job(FIRST_ID, "run-1", NOW)
    second = _job(SECOND_ID, "run-2", NOW + timedelta(seconds=1))
    first_payload = serialize_paper_run_request(first.request)
    second_payload = serialize_paper_run_request(second.request)
    with factory.begin() as session:
        repository = SqlAlchemyPaperJobRepository(session=session)
        assert repository.add(job=second, request_payload=second_payload) is second
        assert repository.add(job=first, request_payload=first_payload) is first

    with factory() as session:
        repository = SqlAlchemyPaperJobRepository(session=session)
        assert repository.get(job_id=FIRST_ID) == first
        assert repository.get_by_run_id(run_id="run-2") == second
        assert repository.list() == (first, second)
        assert repository.list(status="queued") == (first, second)
        assert repository.list(status="running") == ()
        assert repository.get(job_id="00000000-0000-4000-8000-000000000099") is None
        assert repository.get_by_run_id(run_id="missing") is None
        with pytest.raises(ValueError, match="unsupported"):
            repository.list(status="pending")


@pytest.mark.parametrize("status", ("running", "succeeded", "failed", "canceled"))
def test_add_rejects_non_queued_statuses(database, status: str) -> None:
    _, _, factory = database
    job = replace(_job(FIRST_ID, "run-1"), status=status)
    request_payload = serialize_paper_run_request(job.request)

    with factory.begin() as session:
        repository = SqlAlchemyPaperJobRepository(session=session)
        with pytest.raises(ValueError, match="only queued paper jobs may be added"):
            repository.add(job=job, request_payload=request_payload)

    with factory() as session:
        assert SqlAlchemyPaperJobRepository(session=session).list() == ()


def test_canonical_request_survives_new_engine_and_session(database) -> None:
    database_path, engine, factory = database
    job = _job(FIRST_ID, "durable-run")
    request_payload = serialize_paper_run_request(job.request)
    with factory.begin() as session:
        SqlAlchemyPaperJobRepository(session=session).add(
            job=job,
            request_payload=request_payload,
        )
        stored_payload = session.scalar(
            select(PaperJobRow.request_payload).where(PaperJobRow.job_id == FIRST_ID)
        )
        assert stored_payload == serialize_paper_run_request(job.request)

    engine.dispose()
    reopened = create_product_database_engine(
        config=resolve_product_database_config(database_path=database_path)
    )
    reopened_factory = create_product_session_factory(engine=reopened)
    try:
        with reopened_factory() as session:
            restored = SqlAlchemyPaperJobRepository(session=session).get(
                job_id=FIRST_ID
            )
        assert restored == job
        assert restored is not None
        assert restored.request.to_dict() == job.request.to_dict()
        assert restored.submitted_timestamp.tzinfo is timezone.utc
    finally:
        reopened.dispose()


def test_repository_add_does_not_commit_and_caller_rollback_wins(database) -> None:
    _, _, factory = database
    job = _job(FIRST_ID, "rolled-back")
    request_payload = serialize_paper_run_request(job.request)
    with factory() as session:
        SqlAlchemyPaperJobRepository(session=session).add(
            job=job,
            request_payload=request_payload,
        )
        session.rollback()

    with factory() as session:
        assert SqlAlchemyPaperJobRepository(session=session).list() == ()


def test_duplicate_job_and_run_id_surface_integrity_without_hidden_commit(
    database,
) -> None:
    _, _, factory = database
    first = _job(FIRST_ID, "unique-run")
    first_payload = serialize_paper_run_request(first.request)
    with factory.begin() as session:
        SqlAlchemyPaperJobRepository(session=session).add(
            job=first,
            request_payload=first_payload,
        )

    duplicate_job = _job(FIRST_ID, "other-run")
    duplicate_job_payload = serialize_paper_run_request(duplicate_job.request)
    with factory() as session:
        repository = SqlAlchemyPaperJobRepository(session=session)
        with pytest.raises(IntegrityError):
            repository.add(
                job=duplicate_job,
                request_payload=duplicate_job_payload,
            )
        session.rollback()
    duplicate_run = _job(SECOND_ID, "unique-run")
    duplicate_run_payload = serialize_paper_run_request(duplicate_run.request)
    with factory() as session:
        repository = SqlAlchemyPaperJobRepository(session=session)
        with pytest.raises(IntegrityError):
            repository.add(
                job=duplicate_run,
                request_payload=duplicate_run_payload,
            )
        session.rollback()

    with factory() as session:
        assert SqlAlchemyPaperJobRepository(session=session).list() == (first,)


def test_repository_performs_no_execution_or_filesystem_access(
    database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, factory = database

    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("out-of-scope repository side effect")

    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(paper_execution, "run_paper_trading_request", forbidden)
    job = _job(FIRST_ID, "no-side-effect")
    request_payload = serialize_paper_run_request(job.request)
    with factory.begin() as session:
        SqlAlchemyPaperJobRepository(session=session).add(
            job=job,
            request_payload=request_payload,
        )
    with factory() as session:
        restored = SqlAlchemyPaperJobRepository(session=session).get(job_id=FIRST_ID)

    assert restored is not None
    assert restored.run_id == "no-side-effect"
