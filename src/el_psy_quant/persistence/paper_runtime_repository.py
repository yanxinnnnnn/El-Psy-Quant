"""Caller-transaction-owned strict repository primitives for M35 evidence."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.orm import Session

from el_psy_quant.paper_execution import (
    ExecutionSettlementLink,
    PaperExecutionAttempt,
    PaperExecutionFill,
    create_step_paper_execution_order_command,
)
from el_psy_quant.paper_runtime import (
    PaperRuntime,
    PaperRuntimeCheckpoint,
    PaperRuntimeCommandReceipt,
    PaperRuntimeEvent,
    PaperRuntimeWork,
    create_paper_runtime,
    create_paper_runtime_checkpoint,
    validate_paper_runtime,
    validate_paper_runtime_command_receipt,
    validate_paper_runtime_event,
    validate_paper_runtime_work,
)
from el_psy_quant.paper_runtime._canonical import (
    bounded_string,
    digest,
    load_canonical_json,
)
from el_psy_quant.persistence.paper_execution_records import (
    PaperExecutionCorruptAuthorityError,
)
from el_psy_quant.persistence.paper_execution_repository import (
    SqlAlchemyPaperExecutionRepository,
)
from el_psy_quant.persistence.paper_runtime_mapping import (
    checkpoint_from_row,
    checkpoint_row,
    event_from_row,
    event_row,
    receipt_from_row,
    receipt_row,
    runtime_from_row,
    runtime_row,
    work_from_row,
    work_row,
)
from el_psy_quant.persistence.paper_runtime_model import (
    PaperRuntimeCheckpointRow,
    PaperRuntimeCommandReceiptRow,
    PaperRuntimeEventRow,
    PaperRuntimeRow,
    PaperRuntimeWorkRow,
)
from el_psy_quant.persistence.paper_runtime_records import (
    PAPER_RUNTIME_LIST_LIMIT_MAXIMUM,
    PaperRuntimeConcurrencyConflictError,
    PaperRuntimeNotFoundError,
    PaperRuntimePersistenceCorruptionError,
)


_RUNTIME_IMMUTABLE_FIELDS = (
    "schema_version",
    "runtime_id",
    "runtime_binding_digest",
    "execution_order_id",
    "execution_order_digest",
    "account_id",
    "replay_id",
    "trading_session_id",
    "logical_actor",
    "runtime_policy_id",
    "runtime_policy_version",
    "created_at",
)

_RUNTIME_MUTABLE_COLUMNS = (
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


class PaperRuntimeRepository(Protocol):
    def get_runtime(self, *, runtime_id: str) -> PaperRuntime | None: ...
    def append_runtime(self, *, runtime: PaperRuntime) -> PaperRuntime: ...
    def compare_and_swap_runtime(
        self, *, expected_runtime: PaperRuntime, replacement_runtime: PaperRuntime
    ) -> PaperRuntime: ...
    def get_work(self, *, work_id: str) -> PaperRuntimeWork | None: ...
    def append_work(self, *, work: PaperRuntimeWork) -> PaperRuntimeWork: ...
    def list_all_work(self, *, runtime_id: str) -> tuple[PaperRuntimeWork, ...]: ...
    def get_checkpoint(
        self, *, checkpoint_id: str
    ) -> PaperRuntimeCheckpoint | None: ...
    def append_checkpoint(
        self, *, checkpoint: PaperRuntimeCheckpoint
    ) -> PaperRuntimeCheckpoint: ...
    def load_checkpoint_authority(
        self, *, runtime: PaperRuntime, work: PaperRuntimeWork
    ) -> tuple[
        PaperExecutionAttempt, PaperExecutionFill | None, ExecutionSettlementLink | None
    ]: ...
    def list_all_checkpoints(
        self, *, runtime_id: str
    ) -> tuple[PaperRuntimeCheckpoint, ...]: ...
    def get_event(self, *, event_id: str) -> PaperRuntimeEvent | None: ...
    def append_event(self, *, event: PaperRuntimeEvent) -> PaperRuntimeEvent: ...
    def list_all_events(self, *, runtime_id: str) -> tuple[PaperRuntimeEvent, ...]: ...
    def find_work_events(
        self, *, runtime_id: str, work_id: str, event_type: str
    ) -> tuple[PaperRuntimeEvent, ...]: ...
    def next_event_sequence(self, *, runtime_id: str) -> int: ...
    def get_receipt_by_digest(
        self, *, namespace: str, command_digest: str
    ) -> PaperRuntimeCommandReceipt | None: ...


class SqlAlchemyPaperRuntimeRepository:
    """Strict M35 storage that reconstructs authority and never commits."""

    def __init__(self, *, session: Session) -> None:
        if not isinstance(session, Session):
            raise TypeError("session must be a SQLAlchemy Session")
        self._session = session
        self._execution = SqlAlchemyPaperExecutionRepository(session=session)

    @staticmethod
    def _limit(value: int) -> int:
        if type(value) is not int or not 1 <= value <= PAPER_RUNTIME_LIST_LIMIT_MAXIMUM:
            raise ValueError("limit is invalid")
        return value

    def _validate_runtime_authority(self, runtime: PaperRuntime) -> PaperRuntime:
        try:
            history = self._execution.load_historical_history(
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
            expected = create_paper_runtime(
                execution_order=order,
                logical_actor=runtime.logical_actor,
                runtime_policy_id=runtime.runtime_policy_id,
                runtime_policy_version=runtime.runtime_policy_version,
                created_at=runtime.created_at,
            )
            if (
                expected.runtime_id != runtime.runtime_id
                or expected.runtime_binding_digest != runtime.runtime_binding_digest
            ):
                raise PaperRuntimePersistenceCorruptionError()
            return runtime
        except (PaperExecutionCorruptAuthorityError, ValueError) as exc:
            raise PaperRuntimePersistenceCorruptionError() from exc

    def get_runtime(self, *, runtime_id: str) -> PaperRuntime | None:
        row = self._session.get(
            PaperRuntimeRow, bounded_string(runtime_id, "runtime_id", 96)
        )
        if row is None:
            return None
        return self._validate_runtime_authority(runtime_from_row(row))

    def get_runtime_for_order(self, *, execution_order_id: str) -> PaperRuntime | None:
        row = self._session.scalar(
            select(PaperRuntimeRow).where(
                PaperRuntimeRow.execution_order_id
                == bounded_string(execution_order_id, "execution_order_id", 96)
            )
        )
        return (
            None
            if row is None
            else self._validate_runtime_authority(runtime_from_row(row))
        )

    def list_runtimes(self, *, limit: int = 200) -> tuple[PaperRuntime, ...]:
        rows = self._session.scalars(
            select(PaperRuntimeRow)
            .order_by(PaperRuntimeRow.created_at, PaperRuntimeRow.runtime_id)
            .limit(self._limit(limit))
        ).all()
        return tuple(
            self._validate_runtime_authority(runtime_from_row(row)) for row in rows
        )

    def list_runtimes_page(
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
    ) -> tuple[tuple[PaperRuntime, ...], bool]:
        """Return one bounded deterministic runtime page without mutating state."""

        page_limit = self._limit(limit)
        if (cursor_created_at is None) is not (cursor_runtime_id is None):
            raise ValueError("runtime cursor anchor is incomplete")
        statement = select(PaperRuntimeRow)
        for column, value, name in (
            (PaperRuntimeRow.account_id, account_id, "account_id"),
            (PaperRuntimeRow.replay_id, replay_id, "replay_id"),
            (
                PaperRuntimeRow.trading_session_id,
                trading_session_id,
                "trading_session_id",
            ),
        ):
            if value is not None:
                statement = statement.where(column == bounded_string(value, name, 512))
        if desired_state is not None:
            if desired_state not in ("running", "stopped"):
                raise ValueError("desired state filter is invalid")
            statement = statement.where(PaperRuntimeRow.desired_state == desired_state)
        if observed_state is not None:
            if observed_state not in (
                "ready",
                "running",
                "stopped",
                "completed",
                "blocked",
            ):
                raise ValueError("observed state filter is invalid")
            statement = statement.where(
                PaperRuntimeRow.observed_state == observed_state
            )
        if cursor_created_at is not None:
            if (
                type(cursor_created_at) is not datetime
                or cursor_created_at.tzinfo is None
                or cursor_created_at.utcoffset() is None
                or cursor_created_at.utcoffset().total_seconds() != 0
            ):
                raise ValueError("runtime cursor timestamp is invalid")
            identity = bounded_string(cursor_runtime_id, "cursor_runtime_id", 96)
            anchor = self._session.scalar(
                statement.where(
                    PaperRuntimeRow.runtime_id == identity,
                    PaperRuntimeRow.created_at == cursor_created_at,
                )
            )
            if anchor is None:
                raise ValueError("runtime cursor anchor is not canonical")
            statement = statement.where(
                or_(
                    PaperRuntimeRow.created_at < cursor_created_at,
                    and_(
                        PaperRuntimeRow.created_at == cursor_created_at,
                        PaperRuntimeRow.runtime_id > identity,
                    ),
                )
            )
        rows = tuple(
            self._session.scalars(
                statement.order_by(
                    PaperRuntimeRow.created_at.desc(),
                    PaperRuntimeRow.runtime_id.asc(),
                ).limit(page_limit + 1)
            ).all()
        )
        return (
            tuple(
                self._validate_runtime_authority(runtime_from_row(row))
                for row in rows[:page_limit]
            ),
            len(rows) > page_limit,
        )

    def append_runtime(self, *, runtime: PaperRuntime) -> PaperRuntime:
        self._validate_runtime_authority(runtime)
        current = self.get_runtime(runtime_id=runtime.runtime_id)
        by_order = self.get_runtime_for_order(
            execution_order_id=runtime.execution_order_id
        )
        existing = current or by_order
        if existing is not None:
            if existing != runtime or existing.to_dict() != runtime.to_dict():
                raise PaperRuntimePersistenceCorruptionError()
            return existing
        self._session.add(runtime_row(runtime))
        self._session.flush()
        return runtime

    def compare_and_swap_runtime(
        self,
        *,
        expected_runtime: PaperRuntime,
        replacement_runtime: PaperRuntime,
    ) -> PaperRuntime:
        """Replace one exact snapshot with its exact next version, without commit."""

        expected = validate_paper_runtime(expected_runtime)
        replacement = validate_paper_runtime(replacement_runtime)
        if any(
            getattr(expected, field) != getattr(replacement, field)
            for field in _RUNTIME_IMMUTABLE_FIELDS
        ):
            raise ValueError("runtime immutable binding cannot change")
        expected = self._validate_runtime_authority(expected)
        replacement = self._validate_runtime_authority(replacement)
        if replacement.row_version != expected.row_version + 1:
            raise ValueError("replacement runtime version is not the exact successor")
        if replacement.fencing_token < expected.fencing_token:
            raise ValueError("replacement runtime fencing token regresses")
        if replacement.updated_at < expected.updated_at:
            raise ValueError("replacement runtime timestamp regresses")

        expected_row = runtime_row(expected)
        replacement_row = runtime_row(replacement)
        exact_predicates = tuple(
            getattr(PaperRuntimeRow, column.name) == getattr(expected_row, column.name)
            for column in PaperRuntimeRow.__table__.columns
        )
        values = {
            name: getattr(replacement_row, name) for name in _RUNTIME_MUTABLE_COLUMNS
        }
        values["payload_json"] = replacement_row.payload_json
        result = self._session.execute(
            update(PaperRuntimeRow)
            .where(and_(*exact_predicates))
            .values(**values)
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            raise PaperRuntimeConcurrencyConflictError()
        self._session.flush()
        self._session.expire_all()
        stored = self.get_runtime(runtime_id=replacement.runtime_id)
        if (
            stored is None
            or stored != replacement
            or stored.to_dict() != replacement.to_dict()
        ):
            raise PaperRuntimePersistenceCorruptionError()
        return stored

    def get_work(self, *, work_id: str) -> PaperRuntimeWork | None:
        row = self._session.get(
            PaperRuntimeWorkRow, bounded_string(work_id, "work_id", 96)
        )
        if row is None:
            return None
        runtime = self.get_runtime(runtime_id=row.runtime_id)
        if runtime is None:
            raise PaperRuntimePersistenceCorruptionError()
        work = work_from_row(row, runtime=runtime)
        command = create_step_paper_execution_order_command(
            execution_order_reference=_order_reference(runtime),
            expected_execution_version=work.expected_execution_version,
            command_idempotency_key=work.m34_step_idempotency_key,
            actor=work.m34_step_actor,
        )
        if command.command_idempotency_key != work.m34_step_idempotency_key:
            raise PaperRuntimePersistenceCorruptionError()
        return work

    def get_work_for_version(
        self, *, runtime_id: str, expected_execution_version: int
    ) -> PaperRuntimeWork | None:
        if (
            type(expected_execution_version) is not int
            or expected_execution_version < 0
        ):
            raise ValueError("expected_execution_version is invalid")
        row = self._session.scalar(
            select(PaperRuntimeWorkRow).where(
                PaperRuntimeWorkRow.runtime_id
                == bounded_string(runtime_id, "runtime_id", 96),
                PaperRuntimeWorkRow.expected_execution_version
                == expected_execution_version,
            )
        )
        return None if row is None else self.get_work(work_id=row.work_id)

    def list_work(
        self, *, runtime_id: str, limit: int = 200
    ) -> tuple[PaperRuntimeWork, ...]:
        rows = self._session.scalars(
            select(PaperRuntimeWorkRow)
            .where(
                PaperRuntimeWorkRow.runtime_id
                == bounded_string(runtime_id, "runtime_id", 96)
            )
            .order_by(PaperRuntimeWorkRow.expected_execution_version)
            .limit(self._limit(limit))
        ).all()
        return tuple(
            item
            for row in rows
            if (item := self.get_work(work_id=row.work_id)) is not None
        )

    def list_work_page(
        self,
        *,
        runtime_id: str,
        limit: int,
        cursor_work_id: str | None = None,
        cursor_expected_execution_version: int | None = None,
    ) -> tuple[tuple[PaperRuntimeWork, ...], bool]:
        page_limit = self._limit(limit)
        runtime = self.get_runtime(runtime_id=runtime_id)
        if runtime is None:
            raise PaperRuntimeNotFoundError()
        if (cursor_work_id is None) is not (cursor_expected_execution_version is None):
            raise ValueError("Work cursor anchor is incomplete")
        statement = select(PaperRuntimeWorkRow).where(
            PaperRuntimeWorkRow.runtime_id == runtime.runtime_id
        )
        if cursor_expected_execution_version is not None:
            if (
                type(cursor_expected_execution_version) is not int
                or cursor_expected_execution_version < 0
            ):
                raise ValueError("Work cursor version is invalid")
            identity = bounded_string(cursor_work_id, "cursor_work_id", 96)
            anchor = self._session.scalar(
                statement.where(
                    PaperRuntimeWorkRow.work_id == identity,
                    PaperRuntimeWorkRow.expected_execution_version
                    == cursor_expected_execution_version,
                )
            )
            if anchor is None:
                raise ValueError("Work cursor anchor is not canonical")
            statement = statement.where(
                PaperRuntimeWorkRow.expected_execution_version
                > cursor_expected_execution_version
            )
        rows = tuple(
            self._session.scalars(
                statement.order_by(
                    PaperRuntimeWorkRow.expected_execution_version
                ).limit(page_limit + 1)
            ).all()
        )
        items = tuple(
            item
            for row in rows[:page_limit]
            if (item := self.get_work(work_id=row.work_id)) is not None
        )
        if len(items) != min(len(rows), page_limit):
            raise PaperRuntimePersistenceCorruptionError()
        return items, len(rows) > page_limit

    def list_all_work(self, *, runtime_id: str) -> tuple[PaperRuntimeWork, ...]:
        """Read every Work exactly for runner recovery gates, without truncation."""

        rows = self._session.scalars(
            select(PaperRuntimeWorkRow)
            .where(
                PaperRuntimeWorkRow.runtime_id
                == bounded_string(runtime_id, "runtime_id", 96)
            )
            .order_by(PaperRuntimeWorkRow.expected_execution_version)
        ).all()
        work = tuple(
            item
            for row in rows
            if (item := self.get_work(work_id=row.work_id)) is not None
        )
        versions = tuple(item.expected_execution_version for item in work)
        if len(work) != len(rows) or len(set(versions)) != len(versions):
            raise PaperRuntimePersistenceCorruptionError()
        return work

    def append_work(self, *, work: PaperRuntimeWork) -> PaperRuntimeWork:
        runtime = self.get_runtime(runtime_id=work.runtime_id)
        if runtime is None:
            raise PaperRuntimePersistenceCorruptionError()
        validate_paper_runtime_work(work, runtime=runtime)
        current = self.get_work(work_id=work.work_id)
        by_version = self.get_work_for_version(
            runtime_id=work.runtime_id,
            expected_execution_version=work.expected_execution_version,
        )
        existing = current or by_version
        if existing is not None:
            if existing != work or existing.to_dict() != work.to_dict():
                raise PaperRuntimePersistenceCorruptionError()
            return existing
        self._session.add(work_row(work))
        self._session.flush()
        return work

    def _reconstruct_checkpoint(
        self, row: PaperRuntimeCheckpointRow
    ) -> PaperRuntimeCheckpoint:
        runtime = self.get_runtime(runtime_id=row.runtime_id)
        work = self.get_work(work_id=row.work_id)
        if runtime is None or work is None:
            raise PaperRuntimePersistenceCorruptionError()
        checkpoint = checkpoint_from_row(row, runtime=runtime, work=work)
        try:
            attempt, fill, link = self._canonical_checkpoint_authority(
                runtime=runtime, work=work
            )
            expected = create_paper_runtime_checkpoint(
                runtime=runtime,
                work=work,
                attempt=attempt,
                fill=fill,
                settlement_link=link,
                observed_at=checkpoint.observed_at,
            )
            if expected != checkpoint or expected.to_dict() != checkpoint.to_dict():
                raise PaperRuntimePersistenceCorruptionError()
            return checkpoint
        except (PaperExecutionCorruptAuthorityError, ValueError) as exc:
            raise PaperRuntimePersistenceCorruptionError() from exc

    def _canonical_checkpoint_authority(
        self, *, runtime: PaperRuntime, work: PaperRuntimeWork
    ) -> tuple[
        PaperExecutionAttempt,
        PaperExecutionFill | None,
        ExecutionSettlementLink | None,
    ]:
        try:
            history = self._execution.load_historical_history(
                execution_order_id=runtime.execution_order_id
            )
            attempts = tuple(
                attempt
                for attempt in history.attempts
                if attempt.execution_version_before == work.expected_execution_version
            )
            if len(attempts) != 1:
                raise PaperRuntimePersistenceCorruptionError()
            attempt = attempts[0]
            if attempt.execution_version_after != work.expected_execution_version + 1:
                raise PaperRuntimePersistenceCorruptionError()
            fills = tuple(
                fill
                for fill in history.fills
                if fill.attempt_reference.attempt_id == attempt.attempt_id
                and fill.attempt_reference.attempt_digest == attempt.attempt_digest
            )
            if len(fills) > 1:
                raise PaperRuntimePersistenceCorruptionError()
            fill = None if not fills else fills[0]
            links = tuple(
                link
                for link in history.settlement_links
                if link.execution_attempt_reference.attempt_id == attempt.attempt_id
                and link.execution_attempt_reference.attempt_digest
                == attempt.attempt_digest
            )
            if (fill is None and links) or (fill is not None and len(links) != 1):
                raise PaperRuntimePersistenceCorruptionError()
            link = None if not links else links[0]
            if fill is not None and (
                link is None
                or link.execution_fill_reference.fill_id != fill.fill_id
                or link.execution_fill_reference.fill_digest != fill.fill_digest
            ):
                raise PaperRuntimePersistenceCorruptionError()
            return attempt, fill, link
        except PaperExecutionCorruptAuthorityError as exc:
            raise PaperRuntimePersistenceCorruptionError() from exc

    def load_checkpoint_authority(
        self, *, runtime: PaperRuntime, work: PaperRuntimeWork
    ) -> tuple[
        PaperExecutionAttempt,
        PaperExecutionFill | None,
        ExecutionSettlementLink | None,
    ]:
        """Expose the exact canonical authority used by checkpoint reconstruction."""

        return self._canonical_checkpoint_authority(runtime=runtime, work=work)

    def get_checkpoint(self, *, checkpoint_id: str) -> PaperRuntimeCheckpoint | None:
        row = self._session.get(
            PaperRuntimeCheckpointRow,
            bounded_string(checkpoint_id, "checkpoint_id", 96),
        )
        return None if row is None else self._reconstruct_checkpoint(row)

    def get_checkpoint_for_work(self, *, work_id: str) -> PaperRuntimeCheckpoint | None:
        row = self._session.scalar(
            select(PaperRuntimeCheckpointRow).where(
                PaperRuntimeCheckpointRow.work_id
                == bounded_string(work_id, "work_id", 96)
            )
        )
        return None if row is None else self._reconstruct_checkpoint(row)

    def list_checkpoints(
        self, *, runtime_id: str, limit: int = 200
    ) -> tuple[PaperRuntimeCheckpoint, ...]:
        rows = self._session.scalars(
            select(PaperRuntimeCheckpointRow)
            .where(
                PaperRuntimeCheckpointRow.runtime_id
                == bounded_string(runtime_id, "runtime_id", 96)
            )
            .order_by(PaperRuntimeCheckpointRow.observed_execution_version)
            .limit(self._limit(limit))
        ).all()
        return tuple(self._reconstruct_checkpoint(row) for row in rows)

    def list_checkpoints_page(
        self,
        *,
        runtime_id: str,
        limit: int,
        cursor_checkpoint_id: str | None = None,
        cursor_observed_execution_version: int | None = None,
    ) -> tuple[tuple[PaperRuntimeCheckpoint, ...], bool]:
        page_limit = self._limit(limit)
        runtime = self.get_runtime(runtime_id=runtime_id)
        if runtime is None:
            raise PaperRuntimeNotFoundError()
        if (cursor_checkpoint_id is None) is not (
            cursor_observed_execution_version is None
        ):
            raise ValueError("checkpoint cursor anchor is incomplete")
        statement = select(PaperRuntimeCheckpointRow).where(
            PaperRuntimeCheckpointRow.runtime_id == runtime.runtime_id
        )
        if cursor_observed_execution_version is not None:
            if (
                type(cursor_observed_execution_version) is not int
                or cursor_observed_execution_version < 0
            ):
                raise ValueError("checkpoint cursor version is invalid")
            identity = bounded_string(cursor_checkpoint_id, "cursor_checkpoint_id", 96)
            anchor = self._session.scalar(
                statement.where(
                    PaperRuntimeCheckpointRow.checkpoint_id == identity,
                    PaperRuntimeCheckpointRow.observed_execution_version
                    == cursor_observed_execution_version,
                )
            )
            if anchor is None:
                raise ValueError("checkpoint cursor anchor is not canonical")
            statement = statement.where(
                PaperRuntimeCheckpointRow.observed_execution_version
                > cursor_observed_execution_version
            )
        rows = tuple(
            self._session.scalars(
                statement.order_by(
                    PaperRuntimeCheckpointRow.observed_execution_version
                ).limit(page_limit + 1)
            ).all()
        )
        return (
            tuple(self._reconstruct_checkpoint(row) for row in rows[:page_limit]),
            len(rows) > page_limit,
        )

    def list_all_checkpoints(
        self, *, runtime_id: str
    ) -> tuple[PaperRuntimeCheckpoint, ...]:
        """Read every checkpoint exactly for operational reconciliation."""

        rows = self._session.scalars(
            select(PaperRuntimeCheckpointRow)
            .where(
                PaperRuntimeCheckpointRow.runtime_id
                == bounded_string(runtime_id, "runtime_id", 96)
            )
            .order_by(PaperRuntimeCheckpointRow.observed_execution_version)
        ).all()
        checkpoints = tuple(self._reconstruct_checkpoint(row) for row in rows)
        work_ids = tuple(item.work_id for item in checkpoints)
        versions = tuple(item.observed_execution_version for item in checkpoints)
        if len(set(work_ids)) != len(work_ids) or len(set(versions)) != len(versions):
            raise PaperRuntimePersistenceCorruptionError()
        return checkpoints

    def append_checkpoint(
        self, *, checkpoint: PaperRuntimeCheckpoint
    ) -> PaperRuntimeCheckpoint:
        runtime = self.get_runtime(runtime_id=checkpoint.runtime_id)
        work = self.get_work(work_id=checkpoint.work_id)
        if runtime is None or work is None:
            raise PaperRuntimePersistenceCorruptionError()
        current = self.get_checkpoint(checkpoint_id=checkpoint.checkpoint_id)
        by_work = self.get_checkpoint_for_work(work_id=checkpoint.work_id)
        existing = current or by_work
        if existing is not None:
            if existing != checkpoint:
                raise PaperRuntimePersistenceCorruptionError()
            return existing
        # Validate against canonical M34/M31/M32 before the observation is inserted.
        transient = checkpoint_row(checkpoint)
        validated = self._reconstruct_transient_checkpoint(
            transient, runtime=runtime, work=work
        )
        self._session.add(checkpoint_row(validated))
        self._session.flush()
        return validated

    def _reconstruct_transient_checkpoint(
        self,
        row: PaperRuntimeCheckpointRow,
        *,
        runtime: PaperRuntime,
        work: PaperRuntimeWork,
    ) -> PaperRuntimeCheckpoint:
        checkpoint = checkpoint_from_row(row, runtime=runtime, work=work)
        attempt, fill, link = self._canonical_checkpoint_authority(
            runtime=runtime, work=work
        )
        try:
            expected = create_paper_runtime_checkpoint(
                runtime=runtime,
                work=work,
                attempt=attempt,
                fill=fill,
                settlement_link=link,
                observed_at=checkpoint.observed_at,
            )
        except ValueError as exc:
            raise PaperRuntimePersistenceCorruptionError() from exc
        if expected != checkpoint:
            raise PaperRuntimePersistenceCorruptionError()
        return checkpoint

    def get_event(self, *, event_id: str) -> PaperRuntimeEvent | None:
        row = self._session.get(
            PaperRuntimeEventRow, bounded_string(event_id, "event_id", 96)
        )
        if row is None:
            return None
        runtime = self.get_runtime(runtime_id=row.runtime_id)
        if runtime is None:
            raise PaperRuntimePersistenceCorruptionError()
        return event_from_row(row, runtime=runtime)

    def list_events(
        self, *, runtime_id: str, limit: int = 200
    ) -> tuple[PaperRuntimeEvent, ...]:
        rows = self._session.scalars(
            select(PaperRuntimeEventRow)
            .where(
                PaperRuntimeEventRow.runtime_id
                == bounded_string(runtime_id, "runtime_id", 96)
            )
            .order_by(PaperRuntimeEventRow.event_sequence)
            .limit(self._limit(limit))
        ).all()
        events = tuple(
            item
            for row in rows
            if (item := self.get_event(event_id=row.event_id)) is not None
        )
        if tuple(event.event_sequence for event in events) != tuple(range(len(events))):
            raise PaperRuntimePersistenceCorruptionError()
        return events

    def list_events_page(
        self,
        *,
        runtime_id: str,
        limit: int,
        cursor_event_id: str | None = None,
        cursor_event_sequence: int | None = None,
    ) -> tuple[tuple[PaperRuntimeEvent, ...], bool]:
        page_limit = self._limit(limit)
        runtime = self.get_runtime(runtime_id=runtime_id)
        if runtime is None:
            raise PaperRuntimeNotFoundError()
        if (cursor_event_id is None) is not (cursor_event_sequence is None):
            raise ValueError("event cursor anchor is incomplete")
        statement = select(PaperRuntimeEventRow).where(
            PaperRuntimeEventRow.runtime_id == runtime.runtime_id
        )
        if cursor_event_sequence is not None:
            if type(cursor_event_sequence) is not int or cursor_event_sequence < 0:
                raise ValueError("event cursor sequence is invalid")
            identity = bounded_string(cursor_event_id, "cursor_event_id", 96)
            anchor = self._session.scalar(
                statement.where(
                    PaperRuntimeEventRow.event_id == identity,
                    PaperRuntimeEventRow.event_sequence == cursor_event_sequence,
                )
            )
            if anchor is None:
                raise ValueError("event cursor anchor is not canonical")
            statement = statement.where(
                PaperRuntimeEventRow.event_sequence > cursor_event_sequence
            )
        rows = tuple(
            self._session.scalars(
                statement.order_by(PaperRuntimeEventRow.event_sequence).limit(
                    page_limit + 1
                )
            ).all()
        )
        events = tuple(
            event_from_row(row, runtime=runtime) for row in rows[:page_limit]
        )
        if events and cursor_event_sequence is None and events[0].event_sequence != 0:
            raise PaperRuntimePersistenceCorruptionError()
        if any(
            right.event_sequence != left.event_sequence + 1
            for left, right in zip(events, events[1:])
        ):
            raise PaperRuntimePersistenceCorruptionError()
        return events, len(rows) > page_limit

    def find_work_events(
        self, *, runtime_id: str, work_id: str, event_type: str
    ) -> tuple[PaperRuntimeEvent, ...]:
        """Find exact Work evidence without relying on bounded event listings."""

        if event_type not in ("work_created", "work_observed"):
            raise ValueError("event_type is not Work evidence")
        runtime = self.get_runtime(runtime_id=runtime_id)
        if runtime is None:
            raise PaperRuntimePersistenceCorruptionError()
        identity = bounded_string(work_id, "work_id", 96)
        rows = self._session.scalars(
            select(PaperRuntimeEventRow)
            .where(
                PaperRuntimeEventRow.runtime_id == runtime.runtime_id,
                PaperRuntimeEventRow.event_type == event_type,
            )
            .order_by(PaperRuntimeEventRow.event_sequence)
        ).all()
        matches: list[PaperRuntimeEvent] = []
        for row in rows:
            event = event_from_row(row, runtime=runtime)
            payload = load_canonical_json(event.payload_json)
            if type(payload) is not dict or type(payload.get("work")) is not dict:
                raise PaperRuntimePersistenceCorruptionError()
            if payload["work"].get("work_id") == identity:
                matches.append(event)
        if len(matches) > 1:
            raise PaperRuntimePersistenceCorruptionError()
        return tuple(matches)

    def list_all_events(self, *, runtime_id: str) -> tuple[PaperRuntimeEvent, ...]:
        """Read the complete immutable event stream for exact runner checks."""

        runtime = self.get_runtime(runtime_id=runtime_id)
        if runtime is None:
            raise PaperRuntimePersistenceCorruptionError()
        rows = self._session.scalars(
            select(PaperRuntimeEventRow)
            .where(PaperRuntimeEventRow.runtime_id == runtime.runtime_id)
            .order_by(PaperRuntimeEventRow.event_sequence)
        ).all()
        events = tuple(event_from_row(row, runtime=runtime) for row in rows)
        if tuple(event.event_sequence for event in events) != tuple(range(len(events))):
            raise PaperRuntimePersistenceCorruptionError()
        return events

    def append_event(self, *, event: PaperRuntimeEvent) -> PaperRuntimeEvent:
        runtime = self.get_runtime(runtime_id=event.runtime_id)
        if runtime is None:
            raise PaperRuntimePersistenceCorruptionError()
        validate_paper_runtime_event(event, runtime=runtime)
        current = self.get_event(event_id=event.event_id)
        if current is not None:
            if current != event:
                raise PaperRuntimePersistenceCorruptionError()
            return current
        count, minimum, maximum = self._event_sequence_authority(
            runtime_id=runtime.runtime_id
        )
        if event.event_sequence != count:
            raise PaperRuntimePersistenceCorruptionError()
        self._session.add(event_row(event))
        self._session.flush()
        return event

    def _event_sequence_authority(
        self, *, runtime_id: str
    ) -> tuple[int, int | None, int | None]:
        count, minimum, maximum = self._session.execute(
            select(
                func.count(PaperRuntimeEventRow.event_id),
                func.min(PaperRuntimeEventRow.event_sequence),
                func.max(PaperRuntimeEventRow.event_sequence),
            ).where(
                PaperRuntimeEventRow.runtime_id
                == bounded_string(runtime_id, "runtime_id", 96)
            )
        ).one()
        if (count == 0 and (minimum is not None or maximum is not None)) or (
            count > 0 and (minimum != 0 or maximum != count - 1)
        ):
            raise PaperRuntimePersistenceCorruptionError()
        return count, minimum, maximum

    def next_event_sequence(self, *, runtime_id: str) -> int:
        runtime = self.get_runtime(runtime_id=runtime_id)
        if runtime is None:
            raise PaperRuntimePersistenceCorruptionError()
        count, _minimum, _maximum = self._event_sequence_authority(
            runtime_id=runtime.runtime_id
        )
        return count

    def get_receipt(
        self, *, namespace: str, command_idempotency_key: str
    ) -> PaperRuntimeCommandReceipt | None:
        row = self._session.get(
            PaperRuntimeCommandReceiptRow,
            (
                bounded_string(namespace, "namespace", 64),
                bounded_string(command_idempotency_key, "command_idempotency_key", 128),
            ),
        )
        if row is None:
            return None
        runtime = self.get_runtime(runtime_id=row.runtime_id)
        event = self.get_event(event_id=row.result_event_id)
        if runtime is None or event is None:
            raise PaperRuntimePersistenceCorruptionError()
        return receipt_from_row(row, runtime=runtime, result_event=event)

    def get_receipt_by_digest(
        self, *, namespace: str, command_digest: str
    ) -> PaperRuntimeCommandReceipt | None:
        row = self._session.scalar(
            select(PaperRuntimeCommandReceiptRow).where(
                PaperRuntimeCommandReceiptRow.namespace
                == bounded_string(namespace, "namespace", 64),
                PaperRuntimeCommandReceiptRow.command_digest
                == digest(command_digest, "command_digest"),
            )
        )
        if row is None:
            return None
        return self.get_receipt(
            namespace=row.namespace,
            command_idempotency_key=row.command_idempotency_key,
        )

    def list_receipts(
        self, *, runtime_id: str, limit: int = 200
    ) -> tuple[PaperRuntimeCommandReceipt, ...]:
        rows = self._session.scalars(
            select(PaperRuntimeCommandReceiptRow)
            .where(
                PaperRuntimeCommandReceiptRow.runtime_id
                == bounded_string(runtime_id, "runtime_id", 96)
            )
            .order_by(
                PaperRuntimeCommandReceiptRow.created_at,
                PaperRuntimeCommandReceiptRow.namespace,
            )
            .limit(self._limit(limit))
        ).all()
        return tuple(
            item
            for row in rows
            if (
                item := self.get_receipt(
                    namespace=row.namespace,
                    command_idempotency_key=row.command_idempotency_key,
                )
            )
            is not None
        )

    def append_receipt(
        self, *, receipt: PaperRuntimeCommandReceipt
    ) -> PaperRuntimeCommandReceipt:
        runtime = self.get_runtime(runtime_id=receipt.runtime_id)
        event = self.get_event(event_id=receipt.result_event_id)
        if runtime is None or event is None:
            raise PaperRuntimePersistenceCorruptionError()
        validate_paper_runtime_command_receipt(
            receipt, runtime=runtime, result_event=event
        )
        current = self.get_receipt(
            namespace=receipt.namespace,
            command_idempotency_key=receipt.command_idempotency_key,
        )
        if current is not None:
            if current != receipt:
                raise PaperRuntimePersistenceCorruptionError()
            return current
        self._session.add(receipt_row(receipt))
        self._session.flush()
        return receipt


def _order_reference(runtime: PaperRuntime):
    from el_psy_quant.paper_execution.orders import PaperExecutionOrderReference

    result = object.__new__(PaperExecutionOrderReference)
    object.__setattr__(result, "schema_version", 1)
    object.__setattr__(result, "execution_order_id", runtime.execution_order_id)
    object.__setattr__(result, "execution_order_digest", runtime.execution_order_digest)
    return result


__all__ = ["PaperRuntimeRepository", "SqlAlchemyPaperRuntimeRepository"]
