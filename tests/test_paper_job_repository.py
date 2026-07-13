"""Integration tests for the caller-owned paper-job repository."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier

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
    prepare_paper_run_request_for_persistence,
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


def _prepare(job: PaperJobRecord):
    return prepare_paper_run_request_for_persistence(job.request)


def test_add_get_get_by_run_and_list_round_trip_typed_records(database) -> None:
    _, _, factory = database
    first = _job(FIRST_ID, "run-1", NOW)
    second = _job(SECOND_ID, "run-2", NOW + timedelta(seconds=1))
    first_prepared = _prepare(first)
    second_prepared = _prepare(second)
    with factory.begin() as session:
        repository = SqlAlchemyPaperJobRepository(session=session)
        assert repository.add(job=second, prepared_request=second_prepared) is second
        assert repository.add(job=first, prepared_request=first_prepared) is first

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
    prepared_request = _prepare(job)

    with factory.begin() as session:
        repository = SqlAlchemyPaperJobRepository(session=session)
        with pytest.raises(ValueError, match="only queued paper jobs may be added"):
            repository.add(job=job, prepared_request=prepared_request)

    with factory() as session:
        assert SqlAlchemyPaperJobRepository(session=session).list() == ()


def test_add_rejects_malformed_and_noncanonical_raw_payloads(database) -> None:
    _, _, factory = database
    job = _job(FIRST_ID, "run-1")
    canonical_payload = serialize_paper_run_request(job.request)

    for raw_payload in ("{", f" {canonical_payload}"):
        with factory.begin() as session:
            repository = SqlAlchemyPaperJobRepository(session=session)
            with pytest.raises(
                ValueError,
                match="prepared request must come from the strict codec factory",
            ):
                repository.add(
                    job=job,
                    prepared_request=raw_payload,  # type: ignore[arg-type]
                )

    with factory() as session:
        assert SqlAlchemyPaperJobRepository(session=session).list() == ()


def test_add_rejects_prepared_payload_for_a_different_request(database) -> None:
    _, _, factory = database
    job = _job(FIRST_ID, "run-1")
    different_request = replace(
        job.request,
        created_timestamp="2026-07-13T11:46:00Z",
    )
    mismatched_prepared = prepare_paper_run_request_for_persistence(
        different_request
    )

    with factory.begin() as session:
        repository = SqlAlchemyPaperJobRepository(session=session)
        with pytest.raises(
            ValueError,
            match="prepared request must belong to the paper job request",
        ):
            repository.add(job=job, prepared_request=mismatched_prepared)

    with factory() as session:
        assert SqlAlchemyPaperJobRepository(session=session).list() == ()


def test_canonical_request_survives_new_engine_and_session(database) -> None:
    database_path, engine, factory = database
    job = _job(FIRST_ID, "durable-run")
    expected_payload = serialize_paper_run_request(job.request)
    prepared_request = _prepare(job)
    with factory.begin() as session:
        SqlAlchemyPaperJobRepository(session=session).add(
            job=job,
            prepared_request=prepared_request,
        )
        stored_payload = session.scalar(
            select(PaperJobRow.request_payload).where(PaperJobRow.job_id == FIRST_ID)
        )
        assert stored_payload == expected_payload

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
    prepared_request = _prepare(job)
    with factory() as session:
        SqlAlchemyPaperJobRepository(session=session).add(
            job=job,
            prepared_request=prepared_request,
        )
        session.rollback()

    with factory() as session:
        assert SqlAlchemyPaperJobRepository(session=session).list() == ()


def test_duplicate_job_and_run_id_surface_integrity_without_hidden_commit(
    database,
) -> None:
    _, _, factory = database
    first = _job(FIRST_ID, "unique-run")
    first_prepared = _prepare(first)
    with factory.begin() as session:
        SqlAlchemyPaperJobRepository(session=session).add(
            job=first,
            prepared_request=first_prepared,
        )

    duplicate_job = _job(FIRST_ID, "other-run")
    duplicate_job_prepared = _prepare(duplicate_job)
    with factory() as session:
        repository = SqlAlchemyPaperJobRepository(session=session)
        with pytest.raises(IntegrityError):
            repository.add(
                job=duplicate_job,
                prepared_request=duplicate_job_prepared,
            )
        session.rollback()
    duplicate_run = _job(SECOND_ID, "unique-run")
    duplicate_run_prepared = _prepare(duplicate_run)
    with factory() as session:
        repository = SqlAlchemyPaperJobRepository(session=session)
        with pytest.raises(IntegrityError):
            repository.add(
                job=duplicate_run,
                prepared_request=duplicate_run_prepared,
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
    prepared_request = _prepare(job)
    with factory.begin() as session:
        SqlAlchemyPaperJobRepository(session=session).add(
            job=job,
            prepared_request=prepared_request,
        )
    with factory() as session:
        restored = SqlAlchemyPaperJobRepository(session=session).get(job_id=FIRST_ID)

    assert restored is not None
    assert restored.run_id == "no-side-effect"


def test_approved_conditional_transitions_round_trip_typed_records(database) -> None:
    _, _, factory = database
    success = _job(FIRST_ID, "success")
    failed = _job(SECOND_ID, "failed")
    canceled = _job("00000000-0000-4000-8000-000000000003", "canceled")
    with factory.begin() as session:
        repository = SqlAlchemyPaperJobRepository(session=session)
        for job in (success, failed, canceled):
            repository.add(job=job, prepared_request=_prepare(job))

    running_time = NOW + timedelta(seconds=1)
    terminal_time = NOW + timedelta(seconds=2)
    with factory.begin() as session:
        repository = SqlAlchemyPaperJobRepository(session=session)
        running_success = repository.transition_status(
            job_id=success.job_id,
            expected_status="queued",
            target_status="running",
            updated_timestamp=running_time,
        )
        running_failed = repository.transition_status(
            job_id=failed.job_id,
            expected_status="queued",
            target_status="running",
            updated_timestamp=running_time,
        )
        canceled_job = repository.transition_status(
            job_id=canceled.job_id,
            expected_status="queued",
            target_status="canceled",
            updated_timestamp=terminal_time,
        )
    with factory.begin() as session:
        repository = SqlAlchemyPaperJobRepository(session=session)
        succeeded_job = repository.transition_status(
            job_id=success.job_id,
            expected_status="running",
            target_status="succeeded",
            updated_timestamp=terminal_time,
        )
        failed_job = repository.transition_status(
            job_id=failed.job_id,
            expected_status="running",
            target_status="failed",
            updated_timestamp=terminal_time,
        )

    assert running_success is not None and running_success.status == "running"
    assert running_failed is not None and running_failed.status == "running"
    assert canceled_job is not None and canceled_job.status == "canceled"
    assert succeeded_job is not None and succeeded_job.status == "succeeded"
    assert failed_job is not None and failed_job.status == "failed"
    with factory() as session:
        repository = SqlAlchemyPaperJobRepository(session=session)
        assert repository.get(job_id=success.job_id) == succeeded_job
        assert repository.get(job_id=failed.job_id) == failed_job
        assert repository.get(job_id=canceled.job_id) == canceled_job
        assert repository.list(status="succeeded") == (succeeded_job,)
        assert repository.list(status="failed") == (failed_job,)
        assert repository.list(status="canceled") == (canceled_job,)


def test_transition_expected_status_mismatch_is_no_update(database) -> None:
    _, _, factory = database
    job = _job(FIRST_ID, "mismatch")
    with factory.begin() as session:
        SqlAlchemyPaperJobRepository(session=session).add(
            job=job,
            prepared_request=_prepare(job),
        )

    with factory.begin() as session:
        result = SqlAlchemyPaperJobRepository(session=session).transition_status(
            job_id=job.job_id,
            expected_status="running",
            target_status="succeeded",
            updated_timestamp=NOW + timedelta(seconds=1),
        )

    assert result is None
    with factory() as session:
        assert SqlAlchemyPaperJobRepository(session=session).get(job_id=job.job_id) == job


def test_repository_rejects_reversed_transition_timestamp(database) -> None:
    _, _, factory = database
    job = _job(FIRST_ID, "reversed-time")
    with factory.begin() as session:
        SqlAlchemyPaperJobRepository(session=session).add(
            job=job,
            prepared_request=_prepare(job),
        )

    with factory.begin() as session:
        with pytest.raises(ValueError, match="updated_timestamp"):
            SqlAlchemyPaperJobRepository(session=session).transition_status(
                job_id=job.job_id,
                expected_status="queued",
                target_status="running",
                updated_timestamp=NOW - timedelta(microseconds=1),
            )

    with factory() as session:
        assert SqlAlchemyPaperJobRepository(session=session).get(job_id=job.job_id) == job


def test_transition_flush_is_caller_owned_and_rollback_wins(database) -> None:
    _, _, factory = database
    job = _job(FIRST_ID, "rollback-transition")
    with factory.begin() as session:
        SqlAlchemyPaperJobRepository(session=session).add(
            job=job,
            prepared_request=_prepare(job),
        )

    with factory() as session:
        transitioned = SqlAlchemyPaperJobRepository(
            session=session
        ).transition_status(
            job_id=job.job_id,
            expected_status="queued",
            target_status="running",
            updated_timestamp=NOW + timedelta(seconds=1),
        )
        assert transitioned is not None and transitioned.status == "running"
        session.rollback()

    with factory() as session:
        assert SqlAlchemyPaperJobRepository(session=session).get(job_id=job.job_id) == job


@pytest.mark.parametrize(
    ("expected", "target"),
    (
        ("queued", "succeeded"),
        ("running", "canceled"),
        ("succeeded", "running"),
        ("failed", "running"),
        ("canceled", "queued"),
    ),
)
def test_repository_rejects_unapproved_transition_surface(
    database,
    expected: str,
    target: str,
) -> None:
    _, _, factory = database

    with factory.begin() as session:
        with pytest.raises(ValueError, match="transition is not allowed"):
            SqlAlchemyPaperJobRepository(session=session).transition_status(
                job_id=FIRST_ID,
                expected_status=expected,  # type: ignore[arg-type]
                target_status=target,  # type: ignore[arg-type]
                updated_timestamp=NOW,
            )


def test_concurrent_claim_cancel_operations_have_exactly_one_winner(database) -> None:
    _, _, factory = database
    job = _job(FIRST_ID, "claim-cancel-race")
    with factory.begin() as session:
        SqlAlchemyPaperJobRepository(session=session).add(
            job=job,
            prepared_request=_prepare(job),
        )
    barrier = Barrier(2)

    def attempt(target):
        barrier.wait()
        with factory.begin() as session:
            return SqlAlchemyPaperJobRepository(session=session).transition_status(
                job_id=job.job_id,
                expected_status="queued",
                target_status=target,
                updated_timestamp=NOW + timedelta(seconds=1),
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(
            executor.map(attempt, ("running", "canceled"))  # type: ignore[arg-type]
        )

    winners = tuple(result for result in results if result is not None)
    assert len(winners) == 1
    assert winners[0].status in {"running", "canceled"}


def test_two_independent_sessions_cannot_both_claim_one_job(database) -> None:
    _, _, factory = database
    job = _job(FIRST_ID, "single-claim")
    with factory.begin() as session:
        SqlAlchemyPaperJobRepository(session=session).add(
            job=job,
            prepared_request=_prepare(job),
        )

    barrier = Barrier(2)

    def claim(seconds: int):
        barrier.wait()
        with factory.begin() as session:
            return SqlAlchemyPaperJobRepository(session=session).transition_status(
                job_id=job.job_id,
                expected_status="queued",
                target_status="running",
                updated_timestamp=NOW + timedelta(seconds=seconds),
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(claim, (1, 2)))

    assert sum(result is not None for result in results) == 1


def test_repository_exposes_no_generic_mutation_or_queue_scan(database) -> None:
    _, _, factory = database
    with factory() as session:
        repository = SqlAlchemyPaperJobRepository(session=session)
        assert all(
            not hasattr(repository, name)
            for name in ("update", "delete", "claim_next", "scan", "set_status")
        )
