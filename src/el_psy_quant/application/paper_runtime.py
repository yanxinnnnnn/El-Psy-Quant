"""M35 runtime lifecycle, ownership, fencing, and control replay services."""

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
    create_paper_runtime,
    create_paper_runtime_command_receipt,
    create_paper_runtime_event,
    digest_paper_runtime_control_command,
    reconstruct_paper_runtime_event_result,
    validate_paper_runtime,
)
from el_psy_quant.paper_runtime._canonical import (
    bounded_string,
    digest,
    non_negative_int,
    utc_datetime,
)
from el_psy_quant.persistence.paper_execution_repository import (
    SqlAlchemyPaperExecutionRepository,
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


class PaperRuntimeAlreadyExistsError(Exception):
    """An M35 runtime already exists for the exact M34 execution Order."""


class PaperRuntimeBindingMismatchError(Exception):
    """The supplied immutable runtime or execution binding does not match."""


class PaperRuntimeLifecycleConflictError(Exception):
    """The current runtime state does not permit the requested lifecycle control."""


class PaperRuntimeTerminalContinuationError(Exception):
    """Terminal M34 or M35 authority cannot continue automatically."""


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


@dataclass(frozen=True)
class PaperRuntimeLifecycleResult:
    runtime: PaperRuntime
    event: PaperRuntimeEvent
    receipt: PaperRuntimeCommandReceipt
    replayed: bool


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


class PaperRuntimeLifecycleService:
    """Own atomic durable Create/Start/Stop/Resume/Recover control intent."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        clock: PaperRuntimeClock = _default_clock,
    ) -> None:
        if not isinstance(session_factory, sessionmaker):
            raise TypeError("session_factory must be a SQLAlchemy sessionmaker")
        if not callable(clock):
            raise TypeError("clock must be callable")
        self._session_factory = session_factory
        self._clock = clock

    def _now(self) -> datetime:
        return utc_datetime(self._clock(), "runtime lifecycle clock")

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

    @staticmethod
    def _result_from_replay(
        replay: PaperRuntimeControlReplay,
    ) -> PaperRuntimeLifecycleResult:
        return PaperRuntimeLifecycleResult(
            runtime=replay.runtime,
            event=replay.event,
            receipt=replay.receipt,
            replayed=True,
        )

    @staticmethod
    def _append_control_evidence(
        repository: SqlAlchemyPaperRuntimeRepository,
        *,
        namespace: str,
        event_type: str,
        runtime: PaperRuntime,
        command_idempotency_key: str,
        command_digest: str,
        command_actor: str,
        recorded_at: datetime,
    ) -> PaperRuntimeLifecycleResult:
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
        stored_event = repository.append_event(event=event)
        receipt = create_paper_runtime_command_receipt(
            namespace=namespace,
            command_idempotency_key=command_idempotency_key,
            command_digest=command_digest,
            command_actor=command_actor,
            runtime=runtime,
            result_event=stored_event,
            created_at=recorded_at,
        )
        stored_receipt = repository.append_receipt(receipt=receipt)
        return PaperRuntimeLifecycleResult(
            runtime=runtime,
            event=stored_event,
            receipt=stored_receipt,
            replayed=False,
        )

    @staticmethod
    def _existing_command_digest(
        *,
        namespace: str,
        runtime_id: str,
        runtime_binding_digest: str,
        expected_runtime_version: int,
        requested_action: str,
        command_actor: str,
    ) -> str:
        runtime_identifier = bounded_string(runtime_id, "runtime_id", 96)
        binding_digest = digest(runtime_binding_digest, "runtime_binding_digest")
        version = non_negative_int(
            expected_runtime_version, "expected_runtime_version"
        )
        return digest_paper_runtime_control_command(
            namespace=namespace,
            command_actor=command_actor,
            command_target_identity={
                "runtime_id": runtime_identifier,
                "runtime_binding_digest": binding_digest,
            },
            material_payload={
                "expected_runtime_version": version,
                "requested_action": requested_action,
            },
        )

    @staticmethod
    def _load_exact_runtime(
        repository: SqlAlchemyPaperRuntimeRepository,
        *,
        runtime_id: str,
        runtime_binding_digest: str,
        expected_runtime_version: int,
    ) -> PaperRuntime:
        runtime = repository.get_runtime(runtime_id=runtime_id)
        if runtime is None:
            raise PaperRuntimeNotFoundError()
        if runtime.runtime_binding_digest != runtime_binding_digest:
            raise PaperRuntimeBindingMismatchError()
        if runtime.row_version != expected_runtime_version:
            raise PaperRuntimeConcurrencyConflictError()
        return runtime

    @staticmethod
    def _require_live_nonterminal(
        execution: SqlAlchemyPaperExecutionRepository,
        *,
        runtime: PaperRuntime,
    ) -> None:
        history = execution.load_history(
            execution_order_id=runtime.execution_order_id
        )
        if (
            history.order.execution_order_digest != runtime.execution_order_digest
            or history.state.terminal
        ):
            raise PaperRuntimeTerminalContinuationError()

    def create_runtime(
        self,
        *,
        execution_order_id: str,
        execution_order_digest: str,
        logical_actor: str,
        runtime_policy_id: str,
        runtime_policy_version: int,
        command_idempotency_key: str,
        command_actor: str,
    ) -> PaperRuntimeLifecycleResult:
        order_id = bounded_string(execution_order_id, "execution_order_id", 96)
        order_digest = digest(execution_order_digest, "execution_order_digest")
        actor = bounded_string(logical_actor, "logical_actor", 256)
        policy_id = bounded_string(runtime_policy_id, "runtime_policy_id", 128)
        policy_version = non_negative_int(
            runtime_policy_version, "runtime_policy_version"
        )
        command_digest = digest_paper_runtime_control_command(
            namespace="create_paper_runtime",
            command_actor=command_actor,
            command_target_identity={
                "execution_order_id": order_id,
                "execution_order_digest": order_digest,
            },
            material_payload={
                "logical_actor": actor,
                "runtime_policy_id": policy_id,
                "runtime_policy_version": policy_version,
            },
        )
        with self._write() as session:
            now = self._now()
            repository = SqlAlchemyPaperRuntimeRepository(session=session)
            replay = resolve_paper_runtime_control_replay(
                repository,
                namespace="create_paper_runtime",
                command_idempotency_key=command_idempotency_key,
                command_digest=command_digest,
            )
            if replay is not None:
                return self._result_from_replay(replay)

            execution = SqlAlchemyPaperExecutionRepository(session=session)
            historical = execution.load_historical_history(
                execution_order_id=order_id
            )
            if historical.order.execution_order_digest != order_digest:
                raise PaperRuntimeBindingMismatchError()
            if historical.state.terminal:
                raise PaperRuntimeTerminalContinuationError()
            execution.load_history(execution_order_id=order_id)
            if repository.get_runtime_for_order(execution_order_id=order_id) is not None:
                raise PaperRuntimeAlreadyExistsError()

            runtime = create_paper_runtime(
                execution_order=historical.order,
                logical_actor=actor,
                runtime_policy_id=policy_id,
                runtime_policy_version=policy_version,
                created_at=now,
            )
            stored = repository.append_runtime(runtime=runtime)
            return self._append_control_evidence(
                repository,
                namespace="create_paper_runtime",
                event_type="runtime_created",
                runtime=stored,
                command_idempotency_key=command_idempotency_key,
                command_digest=command_digest,
                command_actor=command_actor,
                recorded_at=now,
            )

    def _mutate_existing(
        self,
        *,
        namespace: str,
        event_type: str,
        requested_action: str,
        runtime_id: str,
        runtime_binding_digest: str,
        expected_runtime_version: int,
        command_idempotency_key: str,
        command_actor: str,
    ) -> PaperRuntimeLifecycleResult:
        command_digest = self._existing_command_digest(
            namespace=namespace,
            runtime_id=runtime_id,
            runtime_binding_digest=runtime_binding_digest,
            expected_runtime_version=expected_runtime_version,
            requested_action=requested_action,
            command_actor=command_actor,
        )
        with self._write() as session:
            now = self._now()
            repository = SqlAlchemyPaperRuntimeRepository(session=session)
            replay = resolve_paper_runtime_control_replay(
                repository,
                namespace=namespace,
                command_idempotency_key=command_idempotency_key,
                command_digest=command_digest,
            )
            if replay is not None:
                return self._result_from_replay(replay)

            current = self._load_exact_runtime(
                repository,
                runtime_id=runtime_id,
                runtime_binding_digest=runtime_binding_digest,
                expected_runtime_version=expected_runtime_version,
            )
            execution = SqlAlchemyPaperExecutionRepository(session=session)
            if current.observed_state in ("completed", "blocked"):
                raise PaperRuntimeTerminalContinuationError()
            if namespace == "start_paper_runtime":
                if not (
                    current.desired_state == "stopped"
                    and current.observed_state == "ready"
                ):
                    raise PaperRuntimeLifecycleConflictError()
                self._require_live_nonterminal(execution, runtime=current)
                replacement = _replace_runtime(
                    current,
                    desired_state="running",
                    row_version=current.row_version + 1,
                    updated_at=now,
                )
            elif namespace == "stop_paper_runtime":
                if current.desired_state != "running":
                    raise PaperRuntimeLifecycleConflictError()
                historical = execution.load_historical_history(
                    execution_order_id=current.execution_order_id
                )
                if (
                    historical.order.execution_order_digest
                    != current.execution_order_digest
                ):
                    raise PaperRuntimePersistenceCorruptionError()
                replacement = _replace_runtime(
                    current,
                    desired_state="stopped",
                    row_version=current.row_version + 1,
                    updated_at=now,
                )
            elif namespace == "resume_paper_runtime":
                if not (
                    current.desired_state == "stopped"
                    and current.observed_state == "stopped"
                ):
                    raise PaperRuntimeLifecycleConflictError()
                self._require_live_nonterminal(execution, runtime=current)
                replacement = _replace_runtime(
                    current,
                    desired_state="running",
                    row_version=current.row_version + 1,
                    updated_at=now,
                )
            elif namespace == "recover_paper_runtime":
                if not (
                    current.desired_state == "running"
                    and current.observed_state in ("ready", "running")
                ):
                    raise PaperRuntimeLifecycleConflictError()
                if current.owner_id is not None and current.lease_expires_at > now:
                    raise PaperRuntimeOwnershipBusyError()
                self._require_live_nonterminal(execution, runtime=current)
                replacement = _replace_runtime(
                    current,
                    row_version=current.row_version + 1,
                    updated_at=now,
                )
            else:
                raise ValueError("unsupported lifecycle command namespace")

            stored = repository.compare_and_swap_runtime(
                expected_runtime=current, replacement_runtime=replacement
            )
            return self._append_control_evidence(
                repository,
                namespace=namespace,
                event_type=event_type,
                runtime=stored,
                command_idempotency_key=command_idempotency_key,
                command_digest=command_digest,
                command_actor=command_actor,
                recorded_at=now,
            )

    def start_runtime(
        self,
        *,
        runtime_id: str,
        runtime_binding_digest: str,
        expected_runtime_version: int,
        command_idempotency_key: str,
        command_actor: str,
    ) -> PaperRuntimeLifecycleResult:
        return self._mutate_existing(
            namespace="start_paper_runtime",
            event_type="start_requested",
            requested_action="start",
            runtime_id=runtime_id,
            runtime_binding_digest=runtime_binding_digest,
            expected_runtime_version=expected_runtime_version,
            command_idempotency_key=command_idempotency_key,
            command_actor=command_actor,
        )

    def stop_runtime(
        self,
        *,
        runtime_id: str,
        runtime_binding_digest: str,
        expected_runtime_version: int,
        command_idempotency_key: str,
        command_actor: str,
    ) -> PaperRuntimeLifecycleResult:
        return self._mutate_existing(
            namespace="stop_paper_runtime",
            event_type="stop_requested",
            requested_action="stop",
            runtime_id=runtime_id,
            runtime_binding_digest=runtime_binding_digest,
            expected_runtime_version=expected_runtime_version,
            command_idempotency_key=command_idempotency_key,
            command_actor=command_actor,
        )

    def resume_runtime(
        self,
        *,
        runtime_id: str,
        runtime_binding_digest: str,
        expected_runtime_version: int,
        command_idempotency_key: str,
        command_actor: str,
    ) -> PaperRuntimeLifecycleResult:
        return self._mutate_existing(
            namespace="resume_paper_runtime",
            event_type="resume_requested",
            requested_action="resume",
            runtime_id=runtime_id,
            runtime_binding_digest=runtime_binding_digest,
            expected_runtime_version=expected_runtime_version,
            command_idempotency_key=command_idempotency_key,
            command_actor=command_actor,
        )

    def recover_runtime(
        self,
        *,
        runtime_id: str,
        runtime_binding_digest: str,
        expected_runtime_version: int,
        command_idempotency_key: str,
        command_actor: str,
    ) -> PaperRuntimeLifecycleResult:
        return self._mutate_existing(
            namespace="recover_paper_runtime",
            event_type="recover_requested",
            requested_action="recover",
            runtime_id=runtime_id,
            runtime_binding_digest=runtime_binding_digest,
            expected_runtime_version=expected_runtime_version,
            command_idempotency_key=command_idempotency_key,
            command_actor=command_actor,
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
    "PaperRuntimeAlreadyExistsError",
    "PaperRuntimeBindingMismatchError",
    "PaperRuntimeClaimMismatchError",
    "PaperRuntimeClock",
    "PaperRuntimeControlIdempotencyConflictError",
    "PaperRuntimeControlReplay",
    "PaperRuntimeLeaseExpiredError",
    "PaperRuntimeLifecycleConflictError",
    "PaperRuntimeLifecycleResult",
    "PaperRuntimeLifecycleService",
    "PaperRuntimeOwnershipBusyError",
    "PaperRuntimeOwnershipResult",
    "PaperRuntimeOwnershipService",
    "PaperRuntimeTerminalContinuationError",
    "resolve_paper_runtime_control_replay",
]
