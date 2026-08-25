"""M35 runtime ownership, fencing, and generic control replay foundation."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterator, Literal

from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from el_psy_quant.paper_runtime import (
    PAPER_RUNTIME_COMMAND_NAMESPACES,
    PaperRuntime,
    PaperRuntimeCommandReceipt,
    PaperRuntimeEvent,
    create_paper_runtime_event,
    reconstruct_paper_runtime_event_result,
    validate_paper_runtime,
)
from el_psy_quant.paper_runtime._canonical import (
    bounded_string,
    digest,
    non_negative_int,
    utc_datetime,
)
from el_psy_quant.persistence.paper_runtime_records import (
    PaperRuntimeConcurrencyConflictError,
    PaperRuntimeNotFoundError,
    PaperRuntimePersistenceCorruptionError,
    PaperRuntimeStorageBusyError,
    PaperRuntimeStorageFailureError,
)
from el_psy_quant.persistence.paper_runtime_repository import (
    SqlAlchemyPaperRuntimeRepository,
)

PaperRuntimeClock = Callable[[], datetime]
ClaimEventType = Literal["claim_acquired", "claim_released", "claim_taken_over"]

_MUTABLE_RUNTIME_FIELDS = frozenset(
    (
        "desired_state",
        "observed_state",
        "owner_id",
        "fencing_token",
        "claimed_at",
        "heartbeat_at",
        "lease_expires_at",
        "row_version",
        "block_reason_code",
        "updated_at",
    )
)


class PaperRuntimeOwnershipBusyError(Exception):
    """Another transient owner holds an active runtime lease."""


class PaperRuntimeClaimMismatchError(Exception):
    """The supplied owner/fence tuple is not current durable authority."""


class PaperRuntimeLeaseExpiredError(Exception):
    """The exact supplied runtime claim has already expired."""


class PaperRuntimeControlIdempotencyConflictError(Exception):
    """A scoped control idempotency key owns different material authority."""


@dataclass(frozen=True)
class PaperRuntimeOwnershipResult:
    runtime: PaperRuntime
    event: PaperRuntimeEvent | None
    converged: bool


@dataclass(frozen=True)
class PaperRuntimeControlReplay:
    runtime: PaperRuntime
    event: PaperRuntimeEvent
    receipt: PaperRuntimeCommandReceipt


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


def _busy(exc: OperationalError) -> bool:
    return isinstance(exc.orig, sqlite3.OperationalError) and any(
        marker in str(exc.orig).lower() for marker in ("locked", "busy")
    )


def _replace_runtime(runtime: PaperRuntime, **changes: object) -> PaperRuntime:
    validate_paper_runtime(runtime)
    if not changes or not set(changes).issubset(_MUTABLE_RUNTIME_FIELDS):
        raise ValueError("runtime replacement fields are invalid")
    result = object.__new__(PaperRuntime)
    for name in PaperRuntime.__dataclass_fields__:
        object.__setattr__(result, name, changes.get(name, getattr(runtime, name)))
    return validate_paper_runtime(result)


def resolve_paper_runtime_control_replay(
    repository: SqlAlchemyPaperRuntimeRepository,
    *,
    namespace: str,
    command_idempotency_key: str,
    command_digest: str,
) -> PaperRuntimeControlReplay | None:
    """Resolve exact key replay or semantic digest convergence from events."""

    if namespace not in PAPER_RUNTIME_COMMAND_NAMESPACES:
        raise ValueError("unsupported runtime control command namespace")
    key = bounded_string(
        command_idempotency_key, "command_idempotency_key", 128
    )
    material_digest = digest(command_digest, "command_digest")
    receipt = repository.get_receipt(
        namespace=namespace, command_idempotency_key=key
    )
    if receipt is not None and receipt.command_digest != material_digest:
        raise PaperRuntimeControlIdempotencyConflictError()
    if receipt is None:
        receipt = repository.get_receipt_by_digest(
            namespace=namespace, command_digest=material_digest
        )
    if receipt is None:
        return None
    current = repository.get_runtime(runtime_id=receipt.runtime_id)
    event = repository.get_event(event_id=receipt.result_event_id)
    if current is None or event is None:
        raise PaperRuntimePersistenceCorruptionError()
    historical = reconstruct_paper_runtime_event_result(event, runtime=current)
    if (
        receipt.result_event_digest != event.event_digest
        or receipt.resulting_runtime_version != historical.row_version
        or receipt.runtime_id != historical.runtime_id
    ):
        raise PaperRuntimePersistenceCorruptionError()
    return PaperRuntimeControlReplay(
        runtime=historical,
        event=event,
        receipt=receipt,
    )


class PaperRuntimeOwnershipService:
    """Own exact SQLite transactions for runtime claims, leases, and fencing."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        lease_duration: timedelta,
        clock: PaperRuntimeClock = _default_clock,
    ) -> None:
        if not isinstance(session_factory, sessionmaker):
            raise TypeError("session_factory must be a SQLAlchemy sessionmaker")
        if type(lease_duration) is not timedelta or lease_duration <= timedelta(0):
            raise ValueError("lease_duration must be strictly positive")
        if not callable(clock):
            raise TypeError("clock must be callable")
        self._session_factory = session_factory
        self._lease_duration = lease_duration
        self._clock = clock

    def _now(self) -> datetime:
        return utc_datetime(self._clock(), "runtime ownership clock")

    @contextmanager
    def _write(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            session.connection().exec_driver_sql("BEGIN IMMEDIATE")
            session.connection().exec_driver_sql("PRAGMA defer_foreign_keys=ON")
            yield session
            session.commit()
        except OperationalError as exc:
            session.rollback()
            if _busy(exc):
                raise PaperRuntimeStorageBusyError() from exc
            raise PaperRuntimeStorageFailureError() from exc
        except IntegrityError as exc:
            session.rollback()
            raise PaperRuntimeConcurrencyConflictError() from exc
        except SQLAlchemyError as exc:
            session.rollback()
            raise PaperRuntimeStorageFailureError() from exc
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def _read(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
        except OperationalError as exc:
            if _busy(exc):
                raise PaperRuntimeStorageBusyError() from exc
            raise PaperRuntimeStorageFailureError() from exc
        except SQLAlchemyError as exc:
            raise PaperRuntimeStorageFailureError() from exc
        finally:
            session.close()

    @staticmethod
    def _runtime(
        repository: SqlAlchemyPaperRuntimeRepository, *, runtime_id: str
    ) -> PaperRuntime:
        runtime = repository.get_runtime(runtime_id=runtime_id)
        if runtime is None:
            raise PaperRuntimeNotFoundError()
        return runtime

    @staticmethod
    def _append_claim_event(
        repository: SqlAlchemyPaperRuntimeRepository,
        *,
        runtime: PaperRuntime,
        event_type: ClaimEventType,
        recorded_at: datetime,
    ) -> PaperRuntimeEvent:
        event = create_paper_runtime_event(
            runtime=runtime,
            event_sequence=repository.next_event_sequence(
                runtime_id=runtime.runtime_id
            ),
            event_type=event_type,
            resulting_runtime_version=runtime.row_version,
            payload={"resulting_runtime": runtime.to_dict()},
            recorded_at=recorded_at,
        )
        return repository.append_event(event=event)

    def claim_runtime(
        self, *, runtime_id: str, owner_id: str
    ) -> PaperRuntimeOwnershipResult:
        owner = bounded_string(owner_id, "owner_id", 256)
        with self._write() as session:
            now = self._now()
            repository = SqlAlchemyPaperRuntimeRepository(session=session)
            current = self._runtime(repository, runtime_id=runtime_id)
            if current.owner_id is not None and current.lease_expires_at > now:
                if current.owner_id == owner:
                    return PaperRuntimeOwnershipResult(
                        runtime=current, event=None, converged=True
                    )
                raise PaperRuntimeOwnershipBusyError()
            event_type: ClaimEventType = (
                "claim_acquired"
                if current.owner_id is None
                else "claim_taken_over"
            )
            replacement = _replace_runtime(
                current,
                owner_id=owner,
                fencing_token=current.fencing_token + 1,
                claimed_at=now,
                heartbeat_at=now,
                lease_expires_at=now + self._lease_duration,
                row_version=current.row_version + 1,
                updated_at=now,
            )
            stored = repository.compare_and_swap_runtime(
                expected_runtime=current, replacement_runtime=replacement
            )
            event = self._append_claim_event(
                repository,
                runtime=stored,
                event_type=event_type,
                recorded_at=now,
            )
            return PaperRuntimeOwnershipResult(
                runtime=stored, event=event, converged=False
            )

    @staticmethod
    def _assert_exact_claim(
        runtime: PaperRuntime,
        *,
        owner_id: str,
        fencing_token: int,
        now: datetime,
    ) -> None:
        if (
            runtime.owner_id is None
            or runtime.owner_id != owner_id
            or runtime.fencing_token != fencing_token
        ):
            raise PaperRuntimeClaimMismatchError()
        if runtime.lease_expires_at <= now:
            raise PaperRuntimeLeaseExpiredError()

    def renew_runtime_claim(
        self, *, runtime_id: str, owner_id: str, fencing_token: int
    ) -> PaperRuntime:
        owner = bounded_string(owner_id, "owner_id", 256)
        fence = non_negative_int(fencing_token, "fencing_token")
        with self._write() as session:
            now = self._now()
            repository = SqlAlchemyPaperRuntimeRepository(session=session)
            current = self._runtime(repository, runtime_id=runtime_id)
            self._assert_exact_claim(
                current, owner_id=owner, fencing_token=fence, now=now
            )
            replacement = _replace_runtime(
                current,
                heartbeat_at=now,
                lease_expires_at=now + self._lease_duration,
                row_version=current.row_version + 1,
                updated_at=now,
            )
            return repository.compare_and_swap_runtime(
                expected_runtime=current, replacement_runtime=replacement
            )

    def release_runtime_claim(
        self, *, runtime_id: str, owner_id: str, fencing_token: int
    ) -> PaperRuntimeOwnershipResult:
        owner = bounded_string(owner_id, "owner_id", 256)
        fence = non_negative_int(fencing_token, "fencing_token")
        with self._write() as session:
            now = self._now()
            repository = SqlAlchemyPaperRuntimeRepository(session=session)
            current = self._runtime(repository, runtime_id=runtime_id)
            self._assert_exact_claim(
                current, owner_id=owner, fencing_token=fence, now=now
            )
            replacement = _replace_runtime(
                current,
                owner_id=None,
                claimed_at=None,
                heartbeat_at=None,
                lease_expires_at=None,
                row_version=current.row_version + 1,
                updated_at=now,
            )
            stored = repository.compare_and_swap_runtime(
                expected_runtime=current, replacement_runtime=replacement
            )
            event = self._append_claim_event(
                repository,
                runtime=stored,
                event_type="claim_released",
                recorded_at=now,
            )
            return PaperRuntimeOwnershipResult(
                runtime=stored, event=event, converged=False
            )

    def assert_active_runtime_claim(
        self, *, runtime_id: str, owner_id: str, fencing_token: int
    ) -> PaperRuntime:
        owner = bounded_string(owner_id, "owner_id", 256)
        fence = non_negative_int(fencing_token, "fencing_token")
        now = self._now()
        with self._read() as session:
            repository = SqlAlchemyPaperRuntimeRepository(session=session)
            runtime = self._runtime(repository, runtime_id=runtime_id)
            self._assert_exact_claim(
                runtime, owner_id=owner, fencing_token=fence, now=now
            )
            return runtime

    def resolve_control_replay(
        self,
        *,
        namespace: str,
        command_idempotency_key: str,
        command_digest: str,
    ) -> PaperRuntimeControlReplay | None:
        with self._read() as session:
            return resolve_paper_runtime_control_replay(
                SqlAlchemyPaperRuntimeRepository(session=session),
                namespace=namespace,
                command_idempotency_key=command_idempotency_key,
                command_digest=command_digest,
            )


__all__ = [
    "PaperRuntimeClaimMismatchError",
    "PaperRuntimeClock",
    "PaperRuntimeControlIdempotencyConflictError",
    "PaperRuntimeControlReplay",
    "PaperRuntimeLeaseExpiredError",
    "PaperRuntimeOwnershipBusyError",
    "PaperRuntimeOwnershipResult",
    "PaperRuntimeOwnershipService",
    "resolve_paper_runtime_control_replay",
]
