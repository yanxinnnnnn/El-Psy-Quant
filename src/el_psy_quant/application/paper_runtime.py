"""M35 runtime lifecycle, ownership, fencing, and control replay services."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterator, Literal

from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from el_psy_quant.application.paper_execution import PaperExecutionApplicationService
from el_psy_quant.paper_execution import create_step_paper_execution_order_command
from el_psy_quant.paper_runtime import (
    PAPER_RUNTIME_COMMAND_NAMESPACES,
    PaperRuntime,
    PaperRuntimeCheckpoint,
    PaperRuntimeCommandReceipt,
    PaperRuntimeEvent,
    PaperRuntimeWork,
    create_paper_runtime,
    create_paper_execution_order_reference_from_runtime,
    create_paper_runtime_checkpoint,
    create_paper_runtime_command_receipt,
    create_paper_runtime_event,
    create_paper_runtime_work,
    digest_paper_runtime_control_command,
    reconstruct_paper_runtime_event_result,
    validate_paper_runtime,
)
from el_psy_quant.persistence.paper_execution_records import (
    COMMAND_NAMESPACE_STEP_ORDER,
    PaperExecutionCorruptAuthorityError,
    PaperExecutionIdempotencyConflictError,
    PaperExecutionReconciliationRequiredError,
    PaperExecutionStaleAuthorityError,
    PaperExecutionStepCommit,
    PaperExecutionStoredResult,
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


class PaperRuntimeRunnerStateError(Exception):
    """The durable runtime lifecycle state is not runnable."""


class PaperRuntimeObservationRequiredError(Exception):
    """A committed M34 Step is missing its M35 operational observation."""


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


PaperRuntimeIterationOutcome = Literal["running", "stopped", "completed"]
PaperRuntimeLoopOutcome = Literal[
    "stopped", "completed", "iteration_budget_exhausted"
]


@dataclass(frozen=True)
class PaperRuntimeIterationResult:
    outcome: PaperRuntimeIterationOutcome
    runtime: PaperRuntime
    work: PaperRuntimeWork | None
    checkpoint: PaperRuntimeCheckpoint | None
    step_replayed: bool | None


@dataclass(frozen=True)
class PaperRuntimeLoopResult:
    outcome: PaperRuntimeLoopOutcome
    runtime: PaperRuntime
    iterations: int
    last_iteration: PaperRuntimeIterationResult | None


PaperRuntimeRecoveryOutcome = Literal["runnable", "stopped", "completed", "blocked"]


@dataclass(frozen=True)
class PaperRuntimeRecoveryResult:
    outcome: PaperRuntimeRecoveryOutcome
    runtime: PaperRuntime
    work: PaperRuntimeWork | None
    checkpoint: PaperRuntimeCheckpoint | None
    step_replayed: bool | None


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


@dataclass(frozen=True)
class _PreparedRuntimeIteration:
    outcome: Literal["step", "stopped", "completed"]
    runtime: PaperRuntime
    work: PaperRuntimeWork | None


class PaperRuntimeRunnerService:
    """Run one already-claimed M35 runtime through exact durable M34 Steps."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        execution_service: PaperExecutionApplicationService,
        ownership_service: PaperRuntimeOwnershipService,
        clock: PaperRuntimeClock = _default_clock,
    ) -> None:
        if not isinstance(session_factory, sessionmaker):
            raise TypeError("session_factory must be a SQLAlchemy sessionmaker")
        if not isinstance(execution_service, PaperExecutionApplicationService):
            raise TypeError("execution_service must be PaperExecutionApplicationService")
        if not isinstance(ownership_service, PaperRuntimeOwnershipService):
            raise TypeError("ownership_service must be PaperRuntimeOwnershipService")
        if (
            execution_service._session_factory is not session_factory
            or ownership_service._session_factory is not session_factory
        ):
            raise ValueError("runner services must share one session factory")
        if not callable(clock):
            raise TypeError("clock must be callable")
        self._session_factory = session_factory
        self._execution_service = execution_service
        self._ownership_service = ownership_service
        self._clock = clock

    def _now(self) -> datetime:
        return utc_datetime(self._clock(), "runtime runner clock")

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
    def _runtime(
        repository: SqlAlchemyPaperRuntimeRepository, *, runtime_id: str
    ) -> PaperRuntime:
        runtime = repository.get_runtime(runtime_id=runtime_id)
        if runtime is None:
            raise PaperRuntimeNotFoundError()
        return runtime

    @staticmethod
    def _assert_claim(
        runtime: PaperRuntime,
        *,
        owner_id: str,
        fencing_token: int,
        now: datetime,
    ) -> None:
        PaperRuntimeOwnershipService._assert_exact_claim(
            runtime,
            owner_id=owner_id,
            fencing_token=fencing_token,
            now=now,
        )

    @staticmethod
    def _work_reference(work: PaperRuntimeWork) -> dict[str, object]:
        return {
            "work_id": work.work_id,
            "work_digest": work.work_digest,
            "expected_execution_version": work.expected_execution_version,
        }

    @staticmethod
    def _checkpoint_reference(
        checkpoint: PaperRuntimeCheckpoint,
    ) -> dict[str, object]:
        return {
            "checkpoint_id": checkpoint.checkpoint_id,
            "checkpoint_digest": checkpoint.checkpoint_digest,
            "observed_execution_version": checkpoint.observed_execution_version,
        }

    @classmethod
    def _work_event_payload(
        cls,
        *,
        runtime: PaperRuntime,
        work: PaperRuntimeWork,
        checkpoint: PaperRuntimeCheckpoint | None = None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "resulting_runtime": runtime.to_dict(),
            "work": cls._work_reference(work),
        }
        if checkpoint is not None:
            payload["checkpoint"] = cls._checkpoint_reference(checkpoint)
        return payload

    @staticmethod
    def _append_runtime_event(
        repository: SqlAlchemyPaperRuntimeRepository,
        *,
        runtime: PaperRuntime,
        event_type: str,
        payload: dict[str, object],
        recorded_at: datetime,
    ) -> PaperRuntimeEvent:
        return repository.append_event(
            event=create_paper_runtime_event(
                runtime=runtime,
                event_sequence=repository.next_event_sequence(
                    runtime_id=runtime.runtime_id
                ),
                event_type=event_type,
                resulting_runtime_version=runtime.row_version,
                payload=payload,
                recorded_at=recorded_at,
            )
        )

    @classmethod
    def _require_exact_work_event(
        cls,
        repository: SqlAlchemyPaperRuntimeRepository,
        *,
        runtime: PaperRuntime,
        work: PaperRuntimeWork,
        event_type: Literal["work_created", "work_observed"],
        checkpoint: PaperRuntimeCheckpoint | None = None,
    ) -> PaperRuntimeEvent:
        events = repository.find_work_events(
            runtime_id=runtime.runtime_id,
            work_id=work.work_id,
            event_type=event_type,
        )
        if len(events) != 1:
            raise PaperRuntimePersistenceCorruptionError()
        payload = events[0].to_dict()["payload"]
        if type(payload) is not dict:
            raise PaperRuntimePersistenceCorruptionError()
        if payload.get("work") != cls._work_reference(work):
            raise PaperRuntimePersistenceCorruptionError()
        if event_type == "work_observed":
            if checkpoint is None or payload.get("checkpoint") != cls._checkpoint_reference(
                checkpoint
            ):
                raise PaperRuntimePersistenceCorruptionError()
        elif "checkpoint" in payload:
            raise PaperRuntimePersistenceCorruptionError()
        return events[0]

    @classmethod
    def _audit_work_observations(
        cls,
        repository: SqlAlchemyPaperRuntimeRepository,
        *,
        runtime: PaperRuntime,
        canonical_execution_version: int,
        canonical_attempts: tuple = (),
        allow_missing_observation: bool = False,
        require_complete_runtime_work: bool = False,
    ) -> PaperRuntimeWork | None:
        events = repository.list_all_events(runtime_id=runtime.runtime_id)
        works = repository.list_all_work(runtime_id=runtime.runtime_id)
        checkpoints = repository.list_all_checkpoints(runtime_id=runtime.runtime_id)
        created_events = tuple(
            event for event in events if event.event_type == "work_created"
        )
        observed_events_all = tuple(
            event for event in events if event.event_type == "work_observed"
        )
        if len(created_events) != len(works) or len(observed_events_all) != len(
            checkpoints
        ):
            raise PaperRuntimePersistenceCorruptionError()

        if canonical_attempts:
            if len(canonical_attempts) != canonical_execution_version:
                raise PaperRuntimePersistenceCorruptionError()
            runtime_start_version = sum(
                attempt.created_at < runtime.created_at for attempt in canonical_attempts
            )
            if any(
                attempt.created_at < runtime.created_at
                for attempt in canonical_attempts[runtime_start_version:]
            ):
                raise PaperRuntimePersistenceCorruptionError()
        else:
            runtime_start_version = 0

        checkpoint_work_ids = {checkpoint.work_id for checkpoint in checkpoints}
        current: PaperRuntimeWork | None = None
        observed_versions: set[int] = set()
        for work in works:
            cls._require_exact_work_event(
                repository,
                runtime=runtime,
                work=work,
                event_type="work_created",
            )
            checkpoint = repository.get_checkpoint_for_work(work_id=work.work_id)
            observed_events = repository.find_work_events(
                runtime_id=runtime.runtime_id,
                work_id=work.work_id,
                event_type="work_observed",
            )
            if checkpoint is None:
                if observed_events:
                    raise PaperRuntimePersistenceCorruptionError()
            else:
                if checkpoint.work_id not in checkpoint_work_ids:
                    raise PaperRuntimePersistenceCorruptionError()
                cls._require_exact_work_event(
                    repository,
                    runtime=runtime,
                    work=work,
                    event_type="work_observed",
                    checkpoint=checkpoint,
                )
                observed_versions.add(work.expected_execution_version)
            if work.expected_execution_version < runtime_start_version:
                raise PaperRuntimePersistenceCorruptionError()
            if work.expected_execution_version < canonical_execution_version:
                if checkpoint is None and not allow_missing_observation:
                    raise PaperRuntimeObservationRequiredError()
                if checkpoint is None:
                    if (
                        current is not None
                        or work.expected_execution_version
                        != canonical_execution_version - 1
                    ):
                        raise PaperRuntimePersistenceCorruptionError()
                    current = work
            elif work.expected_execution_version == canonical_execution_version:
                if checkpoint is not None or current is not None:
                    raise PaperRuntimePersistenceCorruptionError()
                current = work
            else:
                raise PaperRuntimePersistenceCorruptionError()

        required_versions = set(range(runtime_start_version, canonical_execution_version))
        represented_versions = {
            work.expected_execution_version
            for work in works
            if work.expected_execution_version < canonical_execution_version
        }
        if require_complete_runtime_work and represented_versions != required_versions:
            raise PaperRuntimePersistenceCorruptionError()
        if require_complete_runtime_work and observed_versions != required_versions - (
            set() if current is None else {current.expected_execution_version}
        ):
            raise PaperRuntimePersistenceCorruptionError()
        return current

    @staticmethod
    def _completed_events(
        repository: SqlAlchemyPaperRuntimeRepository, *, runtime_id: str
    ) -> tuple[PaperRuntimeEvent, ...]:
        return tuple(
            event
            for event in repository.list_all_events(runtime_id=runtime_id)
            if event.event_type == "runtime_completed"
        )

    @classmethod
    def _transition_completed(
        cls,
        repository: SqlAlchemyPaperRuntimeRepository,
        *,
        runtime: PaperRuntime,
        now: datetime,
    ) -> PaperRuntime:
        if runtime.observed_state == "completed":
            if len(cls._completed_events(repository, runtime_id=runtime.runtime_id)) != 1:
                raise PaperRuntimePersistenceCorruptionError()
            return runtime
        if cls._completed_events(repository, runtime_id=runtime.runtime_id):
            raise PaperRuntimePersistenceCorruptionError()
        completed = _replace_runtime(
            runtime,
            observed_state="completed",
            row_version=runtime.row_version + 1,
            updated_at=now,
        )
        stored = repository.compare_and_swap_runtime(
            expected_runtime=runtime, replacement_runtime=completed
        )
        cls._append_runtime_event(
            repository,
            runtime=stored,
            event_type="runtime_completed",
            payload={"resulting_runtime": stored.to_dict()},
            recorded_at=now,
        )
        return stored

    @staticmethod
    def _transition_observed(
        repository: SqlAlchemyPaperRuntimeRepository,
        *,
        runtime: PaperRuntime,
        observed_state: Literal["running", "stopped"],
        now: datetime,
    ) -> PaperRuntime:
        if runtime.observed_state == observed_state:
            return runtime
        replacement = _replace_runtime(
            runtime,
            observed_state=observed_state,
            row_version=runtime.row_version + 1,
            updated_at=now,
        )
        return repository.compare_and_swap_runtime(
            expected_runtime=runtime, replacement_runtime=replacement
        )

    def _phase_a_prepare(
        self, *, runtime_id: str, owner_id: str, fencing_token: int
    ) -> _PreparedRuntimeIteration:
        with self._write() as session:
            now = self._now()
            repository = SqlAlchemyPaperRuntimeRepository(session=session)
            runtime = self._runtime(repository, runtime_id=runtime_id)
            self._assert_claim(
                runtime,
                owner_id=owner_id,
                fencing_token=fencing_token,
                now=now,
            )
            if runtime.observed_state in ("blocked", "completed"):
                raise PaperRuntimeRunnerStateError()

            execution = SqlAlchemyPaperExecutionRepository(session=session)
            history = execution.load_historical_history(
                execution_order_id=runtime.execution_order_id
            )
            if history.order.execution_order_digest != runtime.execution_order_digest:
                raise PaperRuntimePersistenceCorruptionError()
            version = history.state.execution_version
            current_work = self._audit_work_observations(
                repository,
                runtime=runtime,
                canonical_execution_version=version,
                canonical_attempts=history.attempts,
            )

            if runtime.desired_state == "stopped":
                stopped = self._transition_observed(
                    repository,
                    runtime=runtime,
                    observed_state="stopped",
                    now=now,
                )
                return _PreparedRuntimeIteration("stopped", stopped, None)

            if history.state.terminal:
                if current_work is not None:
                    raise PaperRuntimePersistenceCorruptionError()
                completed = self._transition_completed(
                    repository, runtime=runtime, now=now
                )
                return _PreparedRuntimeIteration("completed", completed, None)

            execution.validate_current_working_authority(history=history)
            work = current_work
            if work is None:
                work = create_paper_runtime_work(
                    runtime=runtime,
                    expected_execution_version=version,
                    created_at=now,
                )
                repository.append_work(work=work)
                running = self._transition_observed(
                    repository,
                    runtime=runtime,
                    observed_state="running",
                    now=now,
                )
                self._append_runtime_event(
                    repository,
                    runtime=running,
                    event_type="work_created",
                    payload=self._work_event_payload(runtime=running, work=work),
                    recorded_at=now,
                )
                runtime = running
            else:
                runtime = self._transition_observed(
                    repository,
                    runtime=runtime,
                    observed_state="running",
                    now=now,
                )
            return _PreparedRuntimeIteration("step", runtime, work)

    def _settle_stopped_before_step(
        self, *, runtime_id: str, owner_id: str, fencing_token: int
    ) -> PaperRuntime:
        with self._write() as session:
            now = self._now()
            repository = SqlAlchemyPaperRuntimeRepository(session=session)
            runtime = self._runtime(repository, runtime_id=runtime_id)
            self._assert_claim(
                runtime,
                owner_id=owner_id,
                fencing_token=fencing_token,
                now=now,
            )
            if runtime.desired_state != "stopped":
                raise PaperRuntimeConcurrencyConflictError()
            return self._transition_observed(
                repository,
                runtime=runtime,
                observed_state="stopped",
                now=now,
            )

    def _confirm_step_entry(
        self,
        *,
        runtime_id: str,
        owner_id: str,
        fencing_token: int,
        work: PaperRuntimeWork,
    ) -> PaperRuntime:
        runtime = self._ownership_service.assert_active_runtime_claim(
            runtime_id=runtime_id,
            owner_id=owner_id,
            fencing_token=fencing_token,
        )
        self._require_step_entry_runtime(runtime=runtime, work=work)
        return runtime

    @staticmethod
    def _require_step_entry_runtime(
        *, runtime: PaperRuntime, work: PaperRuntimeWork
    ) -> None:
        if runtime.observed_state in ("blocked", "completed"):
            raise PaperRuntimeRunnerStateError()
        if (
            runtime.runtime_id != work.runtime_id
            or runtime.execution_order_id != work.execution_order_id
            or runtime.execution_order_digest != work.execution_order_digest
            or runtime.logical_actor != work.m34_step_actor
        ):
            raise PaperRuntimePersistenceCorruptionError()

    @staticmethod
    def _verify_step_result(
        stored: PaperExecutionStoredResult[PaperExecutionStepCommit],
        *,
        attempt,
        fill,
        settlement_link,
    ) -> None:
        if type(stored) is not PaperExecutionStoredResult:
            raise PaperRuntimePersistenceCorruptionError()
        commit = stored.result
        if type(commit) is not PaperExecutionStepCommit:
            raise PaperRuntimePersistenceCorruptionError()
        if (
            commit.step_result.attempt != attempt
            or commit.step_result.fill != fill
            or commit.settlement_link != settlement_link
            or commit.account_event_id
            != (None if settlement_link is None else settlement_link.account_event_id)
        ):
            raise PaperRuntimePersistenceCorruptionError()

    def _phase_c_observe(
        self,
        *,
        runtime_id: str,
        owner_id: str,
        fencing_token: int,
        work: PaperRuntimeWork,
        step: PaperExecutionStoredResult[PaperExecutionStepCommit],
    ) -> PaperRuntimeIterationResult:
        with self._write() as session:
            now = self._now()
            repository = SqlAlchemyPaperRuntimeRepository(session=session)
            runtime = self._runtime(repository, runtime_id=runtime_id)
            self._assert_claim(
                runtime,
                owner_id=owner_id,
                fencing_token=fencing_token,
                now=now,
            )
            if runtime.observed_state == "blocked":
                raise PaperRuntimeRunnerStateError()
            stored_work = repository.get_work(work_id=work.work_id)
            if stored_work != work:
                raise PaperRuntimePersistenceCorruptionError()
            self._require_exact_work_event(
                repository,
                runtime=runtime,
                work=work,
                event_type="work_created",
            )

            execution = SqlAlchemyPaperExecutionRepository(session=session)
            history = execution.load_historical_history(
                execution_order_id=runtime.execution_order_id
            )
            if history.order.execution_order_digest != runtime.execution_order_digest:
                raise PaperRuntimePersistenceCorruptionError()
            if runtime.observed_state == "completed" and not history.state.terminal:
                raise PaperRuntimePersistenceCorruptionError()
            attempt, fill, link = repository.load_checkpoint_authority(
                runtime=runtime, work=work
            )
            if (
                history.state.execution_version
                < work.expected_execution_version + 1
                or attempt not in history.attempts
            ):
                raise PaperRuntimePersistenceCorruptionError()
            self._verify_step_result(
                step,
                attempt=attempt,
                fill=fill,
                settlement_link=link,
            )

            checkpoint = repository.get_checkpoint_for_work(work_id=work.work_id)
            if checkpoint is None:
                checkpoint = create_paper_runtime_checkpoint(
                    runtime=runtime,
                    work=work,
                    attempt=attempt,
                    fill=fill,
                    settlement_link=link,
                    observed_at=now,
                )
                checkpoint = repository.append_checkpoint(checkpoint=checkpoint)
                self._append_runtime_event(
                    repository,
                    runtime=runtime,
                    event_type="work_observed",
                    payload=self._work_event_payload(
                        runtime=runtime, work=work, checkpoint=checkpoint
                    ),
                    recorded_at=now,
                )
            else:
                self._require_exact_work_event(
                    repository,
                    runtime=runtime,
                    work=work,
                    event_type="work_observed",
                    checkpoint=checkpoint,
                )

            if history.state.terminal:
                runtime = self._transition_completed(
                    repository, runtime=runtime, now=now
                )
                outcome: PaperRuntimeIterationOutcome = "completed"
            elif runtime.desired_state == "stopped":
                runtime = self._transition_observed(
                    repository,
                    runtime=runtime,
                    observed_state="stopped",
                    now=now,
                )
                outcome = "stopped"
            else:
                runtime = self._transition_observed(
                    repository,
                    runtime=runtime,
                    observed_state="running",
                    now=now,
                )
                outcome = "running"
            result = PaperRuntimeIterationResult(
                outcome=outcome,
                runtime=runtime,
                work=work,
                checkpoint=checkpoint,
                step_replayed=step.replayed,
            )
        return result

    def _release(
        self, *, runtime_id: str, owner_id: str, fencing_token: int
    ) -> PaperRuntime:
        return self._ownership_service.release_runtime_claim(
            runtime_id=runtime_id,
            owner_id=owner_id,
            fencing_token=fencing_token,
        ).runtime

    def run_one_claimed_iteration(
        self, *, runtime_id: str, owner_id: str, fencing_token: int
    ) -> PaperRuntimeIterationResult:
        """Run one serial Phase A / M34 Phase B / Phase C iteration."""

        runtime_identifier = bounded_string(runtime_id, "runtime_id", 96)
        owner = bounded_string(owner_id, "owner_id", 256)
        fence = non_negative_int(fencing_token, "fencing_token")
        prepared = self._phase_a_prepare(
            runtime_id=runtime_identifier,
            owner_id=owner,
            fencing_token=fence,
        )
        if prepared.outcome in ("stopped", "completed"):
            released = self._release(
                runtime_id=runtime_identifier,
                owner_id=owner,
                fencing_token=fence,
            )
            return PaperRuntimeIterationResult(
                outcome=prepared.outcome,
                runtime=released,
                work=None,
                checkpoint=None,
                step_replayed=None,
            )

        work = prepared.work
        if work is None:
            raise PaperRuntimePersistenceCorruptionError()
        fresh = self._confirm_step_entry(
            runtime_id=runtime_identifier,
            owner_id=owner,
            fencing_token=fence,
            work=work,
        )
        if fresh.desired_state == "stopped":
            self._settle_stopped_before_step(
                runtime_id=runtime_identifier,
                owner_id=owner,
                fencing_token=fence,
            )
            released = self._release(
                runtime_id=runtime_identifier,
                owner_id=owner,
                fencing_token=fence,
            )
            return PaperRuntimeIterationResult(
                outcome="stopped",
                runtime=released,
                work=work,
                checkpoint=None,
                step_replayed=None,
            )

        command = create_step_paper_execution_order_command(
            execution_order_reference=create_paper_execution_order_reference_from_runtime(
                fresh
            ),
            expected_execution_version=work.expected_execution_version,
            command_idempotency_key=work.m34_step_idempotency_key,
            actor=work.m34_step_actor,
        )
        step = self._execution_service.step_order(command)
        result = self._phase_c_observe(
            runtime_id=runtime_identifier,
            owner_id=owner,
            fencing_token=fence,
            work=work,
            step=step,
        )
        if result.outcome in ("stopped", "completed"):
            return PaperRuntimeIterationResult(
                outcome=result.outcome,
                runtime=self._release(
                    runtime_id=runtime_identifier,
                    owner_id=owner,
                    fencing_token=fence,
                ),
                work=result.work,
                checkpoint=result.checkpoint,
                step_replayed=result.step_replayed,
            )
        fresh = self._ownership_service.assert_active_runtime_claim(
            runtime_id=runtime_identifier,
            owner_id=owner,
            fencing_token=fence,
        )
        if fresh.desired_state == "stopped":
            self._settle_stopped_before_step(
                runtime_id=runtime_identifier,
                owner_id=owner,
                fencing_token=fence,
            )
            return PaperRuntimeIterationResult(
                outcome="stopped",
                runtime=self._release(
                    runtime_id=runtime_identifier,
                    owner_id=owner,
                    fencing_token=fence,
                ),
                work=result.work,
                checkpoint=result.checkpoint,
                step_replayed=result.step_replayed,
            )
        renewed = self._ownership_service.renew_runtime_claim(
            runtime_id=runtime_identifier,
            owner_id=owner,
            fencing_token=fence,
        )
        return PaperRuntimeIterationResult(
            outcome="running",
            runtime=renewed,
            work=result.work,
            checkpoint=result.checkpoint,
            step_replayed=result.step_replayed,
        )

    def run_claimed_runtime(
        self,
        *,
        runtime_id: str,
        owner_id: str,
        fencing_token: int,
        iteration_budget: int | None = None,
    ) -> PaperRuntimeLoopResult:
        """Serially run fresh durable iterations until lifecycle or caller control stops."""

        if iteration_budget is not None and (
            type(iteration_budget) is not int or iteration_budget <= 0
        ):
            raise ValueError("iteration_budget must be strictly positive")
        iterations = 0
        last: PaperRuntimeIterationResult | None = None
        while iteration_budget is None or iterations < iteration_budget:
            last = self.run_one_claimed_iteration(
                runtime_id=runtime_id,
                owner_id=owner_id,
                fencing_token=fencing_token,
            )
            iterations += 1
            if last.outcome in ("stopped", "completed"):
                return PaperRuntimeLoopResult(
                    outcome=last.outcome,
                    runtime=last.runtime,
                    iterations=iterations,
                    last_iteration=last,
                )
        if last is None:
            raise PaperRuntimePersistenceCorruptionError()
        return PaperRuntimeLoopResult(
            outcome="iteration_budget_exhausted",
            runtime=last.runtime,
            iterations=iterations,
            last_iteration=last,
        )


@dataclass(frozen=True)
class _PreparedRuntimeRecovery:
    outcome: Literal["step", "runnable", "stopped", "completed", "blocked"]
    runtime: PaperRuntime
    work: PaperRuntimeWork | None


class PaperRuntimeRecoveryService:
    """Recover one M35 runtime without creating another execution path."""

    _CORRUPT_REASON = "operational_authority_corrupt"
    _STALE_REASON = "stale_live_continuation"

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        execution_service: PaperExecutionApplicationService,
        ownership_service: PaperRuntimeOwnershipService,
        clock: PaperRuntimeClock = _default_clock,
    ) -> None:
        if not isinstance(session_factory, sessionmaker):
            raise TypeError("session_factory must be a SQLAlchemy sessionmaker")
        if not isinstance(execution_service, PaperExecutionApplicationService):
            raise TypeError("execution_service must be PaperExecutionApplicationService")
        if not isinstance(ownership_service, PaperRuntimeOwnershipService):
            raise TypeError("ownership_service must be PaperRuntimeOwnershipService")
        if (
            execution_service._session_factory is not session_factory
            or ownership_service._session_factory is not session_factory
        ):
            raise ValueError("recovery services must share one session factory")
        if not callable(clock):
            raise TypeError("clock must be callable")
        self._session_factory = session_factory
        self._execution_service = execution_service
        self._ownership_service = ownership_service
        self._clock = clock
        self._runner_service = PaperRuntimeRunnerService(
            session_factory=session_factory,
            execution_service=execution_service,
            ownership_service=ownership_service,
            clock=clock,
        )

    def _now(self) -> datetime:
        return utc_datetime(self._clock(), "runtime recovery clock")

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
    def _require_runtime_order_binding(runtime: PaperRuntime, history) -> None:
        order = history.order
        market = order.market_handoff_reference
        if (
            order.execution_order_id != runtime.execution_order_id
            or order.execution_order_digest != runtime.execution_order_digest
            or order.account_id != runtime.account_id
            or market.replay_id != runtime.replay_id
            or market.trading_session_id != runtime.trading_session_id
        ):
            raise PaperRuntimePersistenceCorruptionError()

    @staticmethod
    def _work_command(runtime: PaperRuntime, work: PaperRuntimeWork):
        if (
            work.runtime_id != runtime.runtime_id
            or work.execution_order_id != runtime.execution_order_id
            or work.execution_order_digest != runtime.execution_order_digest
            or work.m34_step_actor != runtime.logical_actor
        ):
            raise PaperRuntimePersistenceCorruptionError()
        return create_step_paper_execution_order_command(
            execution_order_reference=create_paper_execution_order_reference_from_runtime(
                runtime
            ),
            expected_execution_version=work.expected_execution_version,
            command_idempotency_key=work.m34_step_idempotency_key,
            actor=work.m34_step_actor,
        )

    def _validate_pending_step_authority(
        self,
        *,
        runtime_repository: SqlAlchemyPaperRuntimeRepository,
        execution_repository: SqlAlchemyPaperExecutionRepository,
        runtime: PaperRuntime,
        work: PaperRuntimeWork,
        history,
    ) -> None:
        command = self._work_command(runtime, work)
        attempts = tuple(
            attempt
            for attempt in history.attempts
            if attempt.execution_version_before == work.expected_execution_version
        )
        if len(attempts) > 1:
            raise PaperRuntimePersistenceCorruptionError()
        if history.state.execution_version == work.expected_execution_version:
            if attempts:
                raise PaperRuntimePersistenceCorruptionError()
        elif history.state.execution_version == work.expected_execution_version + 1:
            if len(attempts) != 1:
                raise PaperRuntimePersistenceCorruptionError()
        else:
            raise PaperRuntimePersistenceCorruptionError()

        receipt = execution_repository.get_receipt(
            namespace=COMMAND_NAMESPACE_STEP_ORDER,
            command_idempotency_key=work.m34_step_idempotency_key,
        )
        if receipt is None:
            return
        if receipt.command_digest != command.command_digest or not attempts:
            raise PaperRuntimePersistenceCorruptionError()
        resolved = execution_repository.resolve_receipt(receipt=receipt)
        if type(resolved) is not PaperExecutionStepCommit:
            raise PaperRuntimePersistenceCorruptionError()
        attempt, fill, link = runtime_repository.load_checkpoint_authority(
            runtime=runtime, work=work
        )
        self._runner_service._verify_step_result(
            PaperExecutionStoredResult(result=resolved, replayed=True),
            attempt=attempt,
            fill=fill,
            settlement_link=link,
        )

    def _confirm_recovery_step_entry(
        self,
        *,
        runtime_id: str,
        owner_id: str,
        fencing_token: int,
        work: PaperRuntimeWork,
    ) -> tuple[PaperRuntime, bool]:
        """Freshly fence R2 and report whether its exact Attempt is canonical."""

        with self._read() as session:
            now = self._now()
            runtime_repository = SqlAlchemyPaperRuntimeRepository(session=session)
            runtime = self._runner_service._runtime(
                runtime_repository, runtime_id=runtime_id
            )
            self._runner_service._assert_claim(
                runtime,
                owner_id=owner_id,
                fencing_token=fencing_token,
                now=now,
            )
            self._runner_service._require_step_entry_runtime(runtime=runtime, work=work)
            stored_work = runtime_repository.get_work(work_id=work.work_id)
            if stored_work != work:
                raise PaperRuntimePersistenceCorruptionError()
            self._runner_service._require_exact_work_event(
                runtime_repository,
                runtime=runtime,
                work=work,
                event_type="work_created",
            )

            execution_repository = SqlAlchemyPaperExecutionRepository(session=session)
            history = execution_repository.load_historical_history(
                execution_order_id=runtime.execution_order_id
            )
            self._require_runtime_order_binding(runtime, history)
            self._validate_pending_step_authority(
                runtime_repository=runtime_repository,
                execution_repository=execution_repository,
                runtime=runtime,
                work=work,
                history=history,
            )
            return (
                runtime,
                history.state.execution_version == work.expected_execution_version + 1,
            )

    def _phase_r1_reconcile(
        self, *, runtime_id: str, owner_id: str, fencing_token: int
    ) -> _PreparedRuntimeRecovery:
        with self._write() as session:
            now = self._now()
            repository = SqlAlchemyPaperRuntimeRepository(session=session)
            runtime = self._runner_service._runtime(repository, runtime_id=runtime_id)
            self._runner_service._assert_claim(
                runtime,
                owner_id=owner_id,
                fencing_token=fencing_token,
                now=now,
            )
            if runtime.observed_state == "blocked":
                blocked_events = tuple(
                    event
                    for event in repository.list_all_events(runtime_id=runtime.runtime_id)
                    if event.event_type == "runtime_blocked"
                )
                if len(blocked_events) != 1:
                    raise PaperRuntimePersistenceCorruptionError()
                return _PreparedRuntimeRecovery("blocked", runtime, None)

            execution = SqlAlchemyPaperExecutionRepository(session=session)
            history = execution.load_historical_history(
                execution_order_id=runtime.execution_order_id
            )
            self._require_runtime_order_binding(runtime, history)
            completed_events = self._runner_service._completed_events(
                repository, runtime_id=runtime.runtime_id
            )
            blocked_events = tuple(
                event
                for event in repository.list_all_events(runtime_id=runtime.runtime_id)
                if event.event_type == "runtime_blocked"
            )
            if blocked_events or (
                runtime.observed_state == "completed"
                and (not history.state.terminal or len(completed_events) != 1)
            ) or (
                runtime.observed_state != "completed" and completed_events
            ):
                raise PaperRuntimePersistenceCorruptionError()
            work = self._runner_service._audit_work_observations(
                repository,
                runtime=runtime,
                canonical_execution_version=history.state.execution_version,
                canonical_attempts=history.attempts,
                allow_missing_observation=True,
                require_complete_runtime_work=True,
            )
            if runtime.observed_state == "completed" and work is not None:
                raise PaperRuntimePersistenceCorruptionError()
            if work is not None:
                self._validate_pending_step_authority(
                    runtime_repository=repository,
                    execution_repository=execution,
                    runtime=runtime,
                    work=work,
                    history=history,
                )
                if (
                    runtime.desired_state == "stopped"
                    and history.state.execution_version
                    == work.expected_execution_version
                ):
                    stopped = self._runner_service._transition_observed(
                        repository,
                        runtime=runtime,
                        observed_state="stopped",
                        now=now,
                    )
                    return _PreparedRuntimeRecovery("stopped", stopped, work)
                return _PreparedRuntimeRecovery("step", runtime, work)

            if history.state.terminal:
                completed = self._runner_service._transition_completed(
                    repository, runtime=runtime, now=now
                )
                return _PreparedRuntimeRecovery("completed", completed, None)
            if runtime.desired_state == "stopped":
                stopped = self._runner_service._transition_observed(
                    repository,
                    runtime=runtime,
                    observed_state="stopped",
                    now=now,
                )
                return _PreparedRuntimeRecovery("stopped", stopped, None)

            execution.validate_current_working_authority(history=history)
            running = self._runner_service._transition_observed(
                repository,
                runtime=runtime,
                observed_state="running",
                now=now,
            )
            return _PreparedRuntimeRecovery("runnable", running, None)

    def _transition_blocked(
        self,
        *,
        runtime_id: str,
        owner_id: str,
        fencing_token: int,
        reason_code: str,
    ) -> PaperRuntime:
        reason = bounded_string(reason_code, "block_reason_code", 128)
        with self._write() as session:
            now = self._now()
            repository = SqlAlchemyPaperRuntimeRepository(session=session)
            runtime = self._runner_service._runtime(repository, runtime_id=runtime_id)
            self._runner_service._assert_claim(
                runtime,
                owner_id=owner_id,
                fencing_token=fencing_token,
                now=now,
            )
            blocked_events = tuple(
                event
                for event in repository.list_all_events(runtime_id=runtime.runtime_id)
                if event.event_type == "runtime_blocked"
            )
            if runtime.observed_state == "blocked":
                if len(blocked_events) != 1 or runtime.block_reason_code != reason:
                    raise PaperRuntimePersistenceCorruptionError()
                return runtime
            if blocked_events:
                raise PaperRuntimePersistenceCorruptionError()
            blocked = _replace_runtime(
                runtime,
                observed_state="blocked",
                row_version=runtime.row_version + 1,
                block_reason_code=reason,
                updated_at=now,
            )
            stored = repository.compare_and_swap_runtime(
                expected_runtime=runtime, replacement_runtime=blocked
            )
            self._runner_service._append_runtime_event(
                repository,
                runtime=stored,
                event_type="runtime_blocked",
                payload={"resulting_runtime": stored.to_dict()},
                recorded_at=now,
            )
            return stored

    def _release_result(
        self,
        *,
        outcome: Literal["stopped", "completed", "blocked"],
        runtime_id: str,
        owner_id: str,
        fencing_token: int,
        work: PaperRuntimeWork | None,
        checkpoint: PaperRuntimeCheckpoint | None = None,
        step_replayed: bool | None = None,
    ) -> PaperRuntimeRecoveryResult:
        released = self._ownership_service.release_runtime_claim(
            runtime_id=runtime_id,
            owner_id=owner_id,
            fencing_token=fencing_token,
        ).runtime
        return PaperRuntimeRecoveryResult(
            outcome=outcome,
            runtime=released,
            work=work,
            checkpoint=checkpoint,
            step_replayed=step_replayed,
        )

    def _block_and_release(
        self,
        *,
        runtime_id: str,
        owner_id: str,
        fencing_token: int,
        reason_code: str,
    ) -> PaperRuntimeRecoveryResult:
        blocked = self._transition_blocked(
            runtime_id=runtime_id,
            owner_id=owner_id,
            fencing_token=fencing_token,
            reason_code=reason_code,
        )
        return self._release_result(
            outcome="blocked",
            runtime_id=blocked.runtime_id,
            owner_id=owner_id,
            fencing_token=fencing_token,
            work=None,
        )

    def reconcile_claimed_runtime(
        self, *, runtime_id: str, owner_id: str, fencing_token: int
    ) -> PaperRuntimeRecoveryResult:
        """Reconcile one exact active claim through R1/R2/R3 transactions."""

        runtime_identifier = bounded_string(runtime_id, "runtime_id", 96)
        owner = bounded_string(owner_id, "owner_id", 256)
        fence = non_negative_int(fencing_token, "fencing_token")
        try:
            prepared = self._phase_r1_reconcile(
                runtime_id=runtime_identifier,
                owner_id=owner,
                fencing_token=fence,
            )
        except PaperExecutionReconciliationRequiredError:
            return self._block_and_release(
                runtime_id=runtime_identifier,
                owner_id=owner,
                fencing_token=fence,
                reason_code=self._STALE_REASON,
            )
        except (
            PaperExecutionCorruptAuthorityError,
            PaperExecutionIdempotencyConflictError,
            PaperRuntimePersistenceCorruptionError,
            ValueError,
        ):
            return self._block_and_release(
                runtime_id=runtime_identifier,
                owner_id=owner,
                fencing_token=fence,
                reason_code=self._CORRUPT_REASON,
            )

        if prepared.outcome == "runnable":
            return PaperRuntimeRecoveryResult(
                outcome="runnable",
                runtime=prepared.runtime,
                work=None,
                checkpoint=None,
                step_replayed=None,
            )
        if prepared.outcome in ("stopped", "completed", "blocked"):
            return self._release_result(
                outcome=prepared.outcome,
                runtime_id=runtime_identifier,
                owner_id=owner,
                fencing_token=fence,
                work=prepared.work,
            )

        work = prepared.work
        if work is None:
            return self._block_and_release(
                runtime_id=runtime_identifier,
                owner_id=owner,
                fencing_token=fence,
                reason_code=self._CORRUPT_REASON,
            )
        try:
            fresh, canonical_attempt_exists = self._confirm_recovery_step_entry(
                runtime_id=runtime_identifier,
                owner_id=owner,
                fencing_token=fence,
                work=work,
            )
            if fresh.desired_state == "stopped" and not canonical_attempt_exists:
                stopped = self._runner_service._settle_stopped_before_step(
                    runtime_id=runtime_identifier,
                    owner_id=owner,
                    fencing_token=fence,
                )
                return self._release_result(
                    outcome="stopped",
                    runtime_id=stopped.runtime_id,
                    owner_id=owner,
                    fencing_token=fence,
                    work=work,
                )
            command = self._work_command(fresh, work)
            step = self._execution_service.step_order(command)
            observed = self._runner_service._phase_c_observe(
                runtime_id=runtime_identifier,
                owner_id=owner,
                fencing_token=fence,
                work=work,
                step=step,
            )
        except (PaperExecutionReconciliationRequiredError, PaperExecutionStaleAuthorityError):
            return self._block_and_release(
                runtime_id=runtime_identifier,
                owner_id=owner,
                fencing_token=fence,
                reason_code=self._STALE_REASON,
            )
        except (
            PaperExecutionCorruptAuthorityError,
            PaperExecutionIdempotencyConflictError,
            PaperRuntimePersistenceCorruptionError,
            ValueError,
        ):
            return self._block_and_release(
                runtime_id=runtime_identifier,
                owner_id=owner,
                fencing_token=fence,
                reason_code=self._CORRUPT_REASON,
            )

        if observed.outcome in ("stopped", "completed"):
            return self._release_result(
                outcome=observed.outcome,
                runtime_id=runtime_identifier,
                owner_id=owner,
                fencing_token=fence,
                work=observed.work,
                checkpoint=observed.checkpoint,
                step_replayed=observed.step_replayed,
            )

        follow_up = self.reconcile_claimed_runtime(
            runtime_id=runtime_identifier,
            owner_id=owner,
            fencing_token=fence,
        )
        return PaperRuntimeRecoveryResult(
            outcome=follow_up.outcome,
            runtime=follow_up.runtime,
            work=observed.work,
            checkpoint=observed.checkpoint,
            step_replayed=observed.step_replayed,
        )

    def recover_runtime(
        self, *, runtime_id: str, recovery_owner_id: str
    ) -> PaperRuntimeRecoveryResult:
        """Acquire/take over ownership, then use the one reconciliation algorithm."""

        claimed = self._ownership_service.claim_runtime(
            runtime_id=bounded_string(runtime_id, "runtime_id", 96),
            owner_id=bounded_string(recovery_owner_id, "recovery_owner_id", 256),
        ).runtime
        if claimed.owner_id is None:
            raise PaperRuntimePersistenceCorruptionError()
        return self.reconcile_claimed_runtime(
            runtime_id=claimed.runtime_id,
            owner_id=claimed.owner_id,
            fencing_token=claimed.fencing_token,
        )


__all__ = [
    "PaperRuntimeAlreadyExistsError",
    "PaperRuntimeBindingMismatchError",
    "PaperRuntimeClaimMismatchError",
    "PaperRuntimeClock",
    "PaperRuntimeControlIdempotencyConflictError",
    "PaperRuntimeControlReplay",
    "PaperRuntimeLeaseExpiredError",
    "PaperRuntimeIterationOutcome",
    "PaperRuntimeIterationResult",
    "PaperRuntimeLifecycleConflictError",
    "PaperRuntimeLifecycleResult",
    "PaperRuntimeLifecycleService",
    "PaperRuntimeOwnershipBusyError",
    "PaperRuntimeOwnershipResult",
    "PaperRuntimeOwnershipService",
    "PaperRuntimeLoopOutcome",
    "PaperRuntimeLoopResult",
    "PaperRuntimeObservationRequiredError",
    "PaperRuntimeRecoveryOutcome",
    "PaperRuntimeRecoveryResult",
    "PaperRuntimeRecoveryService",
    "PaperRuntimeRunnerService",
    "PaperRuntimeRunnerStateError",
    "PaperRuntimeTerminalContinuationError",
    "resolve_paper_runtime_control_replay",
]
