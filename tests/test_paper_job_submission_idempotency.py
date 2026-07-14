"""Tests for Sprint 149 durable submission idempotency."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier

import pytest
from alembic import command as alembic_command
from alembic.config import Config
from sqlalchemy import func, select

import el_psy_quant.application.paper_jobs as service
from el_psy_quant.application import (
    PaperAccountStateCommandInput,
    PaperJobConflictError,
    PaperJobIdempotencyConflictError,
    PaperJobNotFoundError,
    PaperRunCommand,
    get_paper_job_by_idempotency_key,
    list_paper_job_attempts,
    list_paper_jobs,
    submit_paper_job,
)
from el_psy_quant.persistence import (
    SqlAlchemyPaperJobRepository,
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
    validate_paper_job_idempotency_key,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV
from el_psy_quant.persistence.paper_job_model import PaperJobRow
from el_psy_quant.persistence.paper_job_submission_key_model import (
    PaperJobSubmissionKeyRow,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 7, 14, 9, 0, tzinfo=timezone.utc)


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


def _account(timestamp: str):
    return PaperAccountStateCommandInput(
        timestamp=timestamp,
        starting_cash=1_000,
        current_cash=1_000,
        positions={},
    )


def _command(run_id: str = "run-1", created: str = "2026-07-14T08:00:00Z"):
    return PaperRunCommand(
        run_id=run_id,
        created_timestamp=created,
        starting_account_state=_account("2026-07-14T07:00:00Z"),
        ending_account_state=_account("2026-07-14T07:30:00Z"),
        orders=(),
        fills=(),
    )


@pytest.mark.parametrize(
    "value",
    (
        "",
        " leading",
        "trailing ",
        "bad/key",
        "bad key",
        "x" * 129,
        1,
        True,
    ),
)
def test_idempotency_key_validation_is_exact(value: object) -> None:
    with pytest.raises(ValueError, match="idempotency_key"):
        validate_paper_job_idempotency_key(value)

    assert validate_paper_job_idempotency_key("Client:paper_1.test-key") == (
        "Client:paper_1.test-key"
    )


def test_no_key_preserves_duplicate_run_conflict(
    session_factory,
) -> None:
    first = submit_paper_job(session_factory=session_factory, command=_command())

    with pytest.raises(PaperJobConflictError):
        submit_paper_job(session_factory=session_factory, command=_command())

    assert list_paper_jobs(session_factory=session_factory) == (first,)


def test_first_keyed_submission_creates_one_job_and_compact_mapping(
    session_factory,
) -> None:
    job = submit_paper_job(
        session_factory=session_factory,
        command=_command(),
        idempotency_key="client:run-1",
    )

    assert get_paper_job_by_idempotency_key(
        session_factory=session_factory,
        idempotency_key="client:run-1",
    ) == job
    with session_factory() as session:
        mapping = session.scalar(select(PaperJobSubmissionKeyRow))
        assert mapping is not None
        assert len(mapping.request_digest) == 64
        assert mapping.request_digest == mapping.request_digest.lower()
        assert not hasattr(mapping, "request_payload")
        assert session.scalar(select(func.count()).select_from(PaperJobRow)) == 1
        assert (
            session.scalar(select(func.count()).select_from(PaperJobSubmissionKeyRow))
            == 1
        )


def test_key_mapping_failure_rolls_back_job_and_mapping_atomically(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = service.SqlAlchemyPaperJobSubmissionKeyRepository.add

    def fail_after_flush(self, *, record):
        original(self, record=record)
        raise RuntimeError("mapping write failed")

    monkeypatch.setattr(
        service.SqlAlchemyPaperJobSubmissionKeyRepository,
        "add",
        fail_after_flush,
    )

    with pytest.raises(RuntimeError, match="mapping write failed"):
        submit_paper_job(
            session_factory=session_factory,
            command=_command(),
            idempotency_key="client:atomic",
        )

    assert list_paper_jobs(session_factory=session_factory) == ()
    with session_factory() as session:
        assert (
            session.scalar(select(func.count()).select_from(PaperJobSubmissionKeyRow))
            == 0
        )


@pytest.mark.parametrize(
    "status",
    ("queued", "running", "succeeded", "failed", "canceled"),
)
def test_exact_replay_returns_original_job_in_every_status_without_new_facts(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
    status: str,
) -> None:
    first = submit_paper_job(
        session_factory=session_factory,
        command=_command(),
        idempotency_key="client:replay",
    )
    transition_time = first.updated_timestamp + timedelta(seconds=1)
    if status != "queued":
        with session_factory.begin() as session:
            repository = SqlAlchemyPaperJobRepository(session=session)
            if status == "canceled":
                expected = repository.transition_status(
                    job_id=first.job_id,
                    expected_status="queued",
                    target_status="canceled",
                    updated_timestamp=transition_time,
                )
            else:
                running = repository.transition_status(
                    job_id=first.job_id,
                    expected_status="queued",
                    target_status="running",
                    updated_timestamp=transition_time,
                )
                if status == "running":
                    expected = running
                else:
                    expected = repository.transition_status(
                        job_id=first.job_id,
                        expected_status="running",
                        target_status=status,  # type: ignore[arg-type]
                        updated_timestamp=transition_time + timedelta(seconds=1),
                    )
        assert expected is not None
    else:
        expected = first
    monkeypatch.setattr(
        service,
        "_new_job_id",
        lambda: (_ for _ in ()).throw(AssertionError("replay generated job identity")),
    )
    monkeypatch.setattr(
        service,
        "_utc_now",
        lambda: (_ for _ in ()).throw(AssertionError("replay generated timestamp")),
    )

    replay = submit_paper_job(
        session_factory=session_factory,
        command=_command(),
        idempotency_key="client:replay",
    )

    assert replay == expected
    assert list_paper_jobs(session_factory=session_factory) == (expected,)
    assert list_paper_job_attempts(
        session_factory=session_factory,
        job_id=first.job_id,
    ) == ()


def test_same_key_changed_request_conflicts(session_factory) -> None:
    submit_paper_job(
        session_factory=session_factory,
        command=_command(),
        idempotency_key="client:stable",
    )

    with pytest.raises(PaperJobIdempotencyConflictError):
        submit_paper_job(
            session_factory=session_factory,
            command=_command(run_id="other-run"),
            idempotency_key="client:stable",
        )


def test_missing_key_and_attempt_job_reads_are_explicit_not_found(
    session_factory,
) -> None:
    with pytest.raises(PaperJobNotFoundError):
        get_paper_job_by_idempotency_key(
            session_factory=session_factory,
            idempotency_key="client:missing",
        )
    with pytest.raises(PaperJobNotFoundError):
        list_paper_job_attempts(
            session_factory=session_factory,
            job_id="00000000-0000-4000-8000-000000000099",
        )


def test_different_key_duplicate_run_remains_job_conflict(session_factory) -> None:
    submit_paper_job(
        session_factory=session_factory,
        command=_command(),
        idempotency_key="client:first",
    )

    with pytest.raises(PaperJobConflictError):
        submit_paper_job(
            session_factory=session_factory,
            command=_command(),
            idempotency_key="client:second",
        )


def test_digest_is_computed_before_submission_transaction(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transaction_started = False
    original = service.digest_prepared_paper_run_request

    def tracked(prepared):
        assert not transaction_started
        return original(prepared)

    class TrackingFactory:
        @contextmanager
        def begin(self):
            nonlocal transaction_started
            transaction_started = True
            with session_factory.begin() as session:
                yield session

    monkeypatch.setattr(service, "digest_prepared_paper_run_request", tracked)

    submit_paper_job(
        session_factory=TrackingFactory(),  # type: ignore[arg-type]
        command=_command(),
        idempotency_key="client:digest",
    )


def test_concurrent_same_key_same_request_converges_on_one_job(
    session_factory,
) -> None:
    barrier = Barrier(2)

    def submit():
        barrier.wait()
        return submit_paper_job(
            session_factory=session_factory,
            command=_command(),
            idempotency_key="client:race",
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(lambda _: submit(), range(2)))

    assert results[0] == results[1]
    assert list_paper_jobs(session_factory=session_factory) == (results[0],)


def test_concurrent_same_key_different_requests_has_winner_and_conflict(
    session_factory,
) -> None:
    barrier = Barrier(2)

    def submit(command):
        barrier.wait()
        try:
            return submit_paper_job(
                session_factory=session_factory,
                command=command,
                idempotency_key="client:mismatch-race",
            )
        except PaperJobIdempotencyConflictError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(
            executor.map(
                submit,
                (_command("run-a"), _command("run-b")),
            )
        )

    assert sum(not isinstance(result, Exception) for result in results) == 1
    assert sum(isinstance(result, PaperJobIdempotencyConflictError) for result in results) == 1
    assert len(list_paper_jobs(session_factory=session_factory)) == 1
