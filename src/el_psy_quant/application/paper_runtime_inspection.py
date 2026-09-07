"""Read-only application seam for M35 runtime transport inspection."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Generic, Iterator, Literal, TypeVar

from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from el_psy_quant.application.paper_runtime import (
    PaperRuntimeRunnerService,
    validate_pending_paper_runtime_work_authority,
)
from el_psy_quant.paper_runtime import (
    PaperRuntime,
    PaperRuntimeCheckpoint,
    PaperRuntimeEvent,
    PaperRuntimeWork,
)
from el_psy_quant.paper_runtime._canonical import bounded_string, utc_datetime
from el_psy_quant.persistence.paper_execution_records import (
    PaperExecutionReconciliationRequiredError,
)
from el_psy_quant.persistence.paper_execution_repository import (
    SqlAlchemyPaperExecutionRepository,
)
from el_psy_quant.persistence.paper_runtime_records import (
    PaperRuntimeNotFoundError,
    PaperRuntimePersistenceCorruptionError,
    PaperRuntimeStorageBusyError,
    PaperRuntimeStorageFailureError,
)
from el_psy_quant.persistence.paper_runtime_repository import (
    SqlAlchemyPaperRuntimeRepository,
)

PaperRuntimeLeaseStatus = Literal["unowned", "active", "expired"]
PaperRuntimeReconciliationStatus = Literal[
    "coherent_nonterminal",
    "coherent_terminal",
    "coherent_stopped",
    "blocked",
    "continuation_stale",
]
PaperRuntimeContinuationStatus = Literal["current", "stale", "not_applicable"]
PaperRuntimeInspectionClock = Callable[[], datetime]
T = TypeVar("T")


@dataclass(frozen=True)
class PaperRuntimePage(Generic[T]):
    items: tuple[T, ...]
    has_more: bool


@dataclass(frozen=True)
class PaperRuntimeHealth:
    runtime: PaperRuntime
    lease_status: PaperRuntimeLeaseStatus
    claimed: bool
    terminal: bool
    blocked: bool
    checked_at: datetime


@dataclass(frozen=True)
class PaperRuntimeReconciliation:
    runtime: PaperRuntime
    status: PaperRuntimeReconciliationStatus
    historical_coherent: bool
    continuation_status: PaperRuntimeContinuationStatus
    execution_version: int
    execution_terminal: bool
    work_count: int
    checkpoint_count: int
    event_count: int
    pending_work_id: str | None


@dataclass(frozen=True)
class PaperRuntimeAuditEntry:
    event: PaperRuntimeEvent
    work_id: str | None
    checkpoint_id: str | None


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


def _busy(exc: OperationalError) -> bool:
    return isinstance(exc.orig, sqlite3.OperationalError) and any(
        marker in str(exc.orig).lower() for marker in ("locked", "busy")
    )


class PaperRuntimeInspectionService:
    """Inspect durable runtime evidence without claims, writes, recovery, or Step."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        clock: PaperRuntimeInspectionClock = _default_clock,
    ) -> None:
        if not isinstance(session_factory, sessionmaker):
            raise TypeError("session_factory must be a SQLAlchemy sessionmaker")
        if not callable(clock):
            raise TypeError("clock must be callable")
        self._session_factory = session_factory
        self._clock = clock

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
        runtime = repository.get_runtime(
            runtime_id=bounded_string(runtime_id, "runtime_id", 96)
        )
        if runtime is None:
            raise PaperRuntimeNotFoundError()
        return runtime

    def get_runtime(self, *, runtime_id: str) -> PaperRuntime:
        with self._read() as session:
            return self._runtime(
                SqlAlchemyPaperRuntimeRepository(session=session),
                runtime_id=runtime_id,
            )

    def list_runtimes(
        self,
        *,
        limit: int,
        cursor_created_at: datetime | None = None,
        cursor_runtime_id: str | None = None,
        account_id: str | None = None,
        replay_id: str | None = None,
        trading_session_id: str | None = None,
        desired_state: str | None = None,
        observed_state: str | None = None,
    ) -> PaperRuntimePage[PaperRuntime]:
        with self._read() as session:
            items, has_more = SqlAlchemyPaperRuntimeRepository(
                session=session
            ).list_runtimes_page(
                limit=limit,
                cursor_created_at=cursor_created_at,
                cursor_runtime_id=cursor_runtime_id,
                account_id=account_id,
                replay_id=replay_id,
                trading_session_id=trading_session_id,
                desired_state=desired_state,
                observed_state=observed_state,
            )
            return PaperRuntimePage(items=items, has_more=has_more)

    def get_health(self, *, runtime_id: str) -> PaperRuntimeHealth:
        checked_at = utc_datetime(self._clock(), "runtime health clock")
        runtime = self.get_runtime(runtime_id=runtime_id)
        if runtime.owner_id is None:
            lease_status: PaperRuntimeLeaseStatus = "unowned"
        elif runtime.lease_expires_at is None:
            raise PaperRuntimePersistenceCorruptionError()
        elif runtime.lease_expires_at <= checked_at:
            lease_status = "expired"
        else:
            lease_status = "active"
        return PaperRuntimeHealth(
            runtime=runtime,
            lease_status=lease_status,
            claimed=runtime.owner_id is not None,
            terminal=runtime.observed_state == "completed",
            blocked=runtime.observed_state == "blocked",
            checked_at=checked_at,
        )

    def reconcile_runtime(self, *, runtime_id: str) -> PaperRuntimeReconciliation:
        """Validate complete historical evidence and classify live freshness."""

        with self._read() as session:
            runtime_repository = SqlAlchemyPaperRuntimeRepository(session=session)
            runtime = self._runtime(runtime_repository, runtime_id=runtime_id)
            execution_repository = SqlAlchemyPaperExecutionRepository(session=session)
            history = execution_repository.load_historical_history(
                execution_order_id=runtime.execution_order_id
            )
            order = history.order
            market = order.market_handoff_reference
            if (
                order.execution_order_digest != runtime.execution_order_digest
                or order.account_id != runtime.account_id
                or market.replay_id != runtime.replay_id
                or market.trading_session_id != runtime.trading_session_id
            ):
                raise PaperRuntimePersistenceCorruptionError()
            works = runtime_repository.list_all_work(runtime_id=runtime.runtime_id)
            checkpoints = runtime_repository.list_all_checkpoints(
                runtime_id=runtime.runtime_id
            )
            events = runtime_repository.list_all_events(runtime_id=runtime.runtime_id)
            pending = PaperRuntimeRunnerService._audit_work_observations(
                runtime_repository,
                runtime=runtime,
                canonical_execution_version=history.state.execution_version,
                canonical_attempts=history.attempts,
                allow_missing_observation=True,
                require_complete_runtime_work=True,
            )
            if pending is not None:
                validate_pending_paper_runtime_work_authority(
                    runtime_repository=runtime_repository,
                    execution_repository=execution_repository,
                    runtime=runtime,
                    work=pending,
                    history=history,
                )
            completed_events = tuple(
                item for item in events if item.event_type == "runtime_completed"
            )
            blocked_events = tuple(
                item for item in events if item.event_type == "runtime_blocked"
            )
            if (
                len(completed_events) > 1
                or len(blocked_events) > 1
                or (runtime.observed_state == "completed")
                != (len(completed_events) == 1)
                or (runtime.observed_state == "blocked") != (len(blocked_events) == 1)
                or (
                    runtime.observed_state == "completed" and not history.state.terminal
                )
            ):
                raise PaperRuntimePersistenceCorruptionError()

            if history.state.terminal or runtime.observed_state in (
                "completed",
                "blocked",
            ):
                continuation: PaperRuntimeContinuationStatus = "not_applicable"
            else:
                try:
                    execution_repository.validate_current_working_authority(
                        history=history
                    )
                    continuation = "current"
                except PaperExecutionReconciliationRequiredError:
                    continuation = "stale"

            if runtime.observed_state == "blocked":
                status: PaperRuntimeReconciliationStatus = "blocked"
            elif continuation == "stale":
                status = "continuation_stale"
            elif runtime.observed_state == "completed" or history.state.terminal:
                status = "coherent_terminal"
            elif (
                runtime.desired_state == "stopped"
                or runtime.observed_state == "stopped"
            ):
                status = "coherent_stopped"
            else:
                status = "coherent_nonterminal"
            return PaperRuntimeReconciliation(
                runtime=runtime,
                status=status,
                historical_coherent=True,
                continuation_status=continuation,
                execution_version=history.state.execution_version,
                execution_terminal=history.state.terminal,
                work_count=len(works),
                checkpoint_count=len(checkpoints),
                event_count=len(events),
                pending_work_id=None if pending is None else pending.work_id,
            )

    def list_work(
        self,
        *,
        runtime_id: str,
        limit: int,
        cursor_work_id: str | None = None,
        cursor_expected_execution_version: int | None = None,
    ) -> PaperRuntimePage[PaperRuntimeWork]:
        with self._read() as session:
            items, has_more = SqlAlchemyPaperRuntimeRepository(
                session=session
            ).list_work_page(
                runtime_id=runtime_id,
                limit=limit,
                cursor_work_id=cursor_work_id,
                cursor_expected_execution_version=cursor_expected_execution_version,
            )
            return PaperRuntimePage(items=items, has_more=has_more)

    def list_checkpoints(
        self,
        *,
        runtime_id: str,
        limit: int,
        cursor_checkpoint_id: str | None = None,
        cursor_observed_execution_version: int | None = None,
    ) -> PaperRuntimePage[PaperRuntimeCheckpoint]:
        with self._read() as session:
            items, has_more = SqlAlchemyPaperRuntimeRepository(
                session=session
            ).list_checkpoints_page(
                runtime_id=runtime_id,
                limit=limit,
                cursor_checkpoint_id=cursor_checkpoint_id,
                cursor_observed_execution_version=cursor_observed_execution_version,
            )
            return PaperRuntimePage(items=items, has_more=has_more)

    def list_audit(
        self,
        *,
        runtime_id: str,
        limit: int,
        cursor_event_id: str | None = None,
        cursor_event_sequence: int | None = None,
    ) -> PaperRuntimePage[PaperRuntimeAuditEntry]:
        with self._read() as session:
            events, has_more = SqlAlchemyPaperRuntimeRepository(
                session=session
            ).list_events_page(
                runtime_id=runtime_id,
                limit=limit,
                cursor_event_id=cursor_event_id,
                cursor_event_sequence=cursor_event_sequence,
            )
            entries = []
            for event in events:
                payload = event.to_dict()["payload"]
                if type(payload) is not dict:
                    raise PaperRuntimePersistenceCorruptionError()
                work = payload.get("work")
                checkpoint = payload.get("checkpoint")
                if work is not None and type(work) is not dict:
                    raise PaperRuntimePersistenceCorruptionError()
                if checkpoint is not None and type(checkpoint) is not dict:
                    raise PaperRuntimePersistenceCorruptionError()
                entries.append(
                    PaperRuntimeAuditEntry(
                        event=event,
                        work_id=None if work is None else work.get("work_id"),
                        checkpoint_id=(
                            None
                            if checkpoint is None
                            else checkpoint.get("checkpoint_id")
                        ),
                    )
                )
            return PaperRuntimePage(items=tuple(entries), has_more=has_more)


__all__ = [
    "PaperRuntimeAuditEntry",
    "PaperRuntimeContinuationStatus",
    "PaperRuntimeHealth",
    "PaperRuntimeInspectionService",
    "PaperRuntimeLeaseStatus",
    "PaperRuntimePage",
    "PaperRuntimeReconciliation",
    "PaperRuntimeReconciliationStatus",
]
