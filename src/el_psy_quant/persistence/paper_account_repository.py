"""Caller-transaction-owned repository for durable Paper Accounts."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, cast

from sqlalchemy import and_, delete, or_, select, update
from sqlalchemy.orm import Session

from el_psy_quant.paper_account import (
    PAPER_ACCOUNT_GENESIS_CHAIN_DIGEST,
    PaperAccountLedgerEventBundle,
    PaperAccountProjection,
    PaperAccountReconciliation,
    PaperAccountSnapshot,
)
from el_psy_quant.persistence.paper_account_mapping import (
    account_record_from_row,
    account_row_from_record,
    cash_rows,
    event_row,
    position_rows,
    projection_from_rows,
    projection_rows,
    reconciliation_from_row,
    reconstruct_history_page_items,
    reconciliation_row,
    reconstruct_history,
    snapshot_from_row,
    snapshot_row,
)
from el_psy_quant.persistence.paper_account_model import (
    PaperAccountCreationKeyRow,
    PaperAccountEventRow,
    PaperAccountPositionProjectionRow,
    PaperAccountProjectionRow,
    PaperAccountReconciliationRow,
    PaperAccountRow,
    PaperAccountSnapshotRow,
    PaperCashLedgerEntryRow,
    PaperPositionLedgerEntryRow,
)
from el_psy_quant.persistence.paper_accounts import (
    PaperAccountCreationKeyRecord,
    PaperAccountLedgerPage,
    PaperAccountListPage,
    PaperAccountPersistenceCorruptionError,
    PaperAccountProjectionStatus,
    PaperAccountRecord,
    _exact_string,
    _exact_utc,
)


class PaperAccountRepository(Protocol):
    """Transaction-scoped persistence boundary with no implicit commits."""

    def get_account(self, *, account_id: str) -> PaperAccountRecord | None: ...

    def list_accounts(
        self, *, lifecycle_status: str | None = None
    ) -> tuple[PaperAccountRecord, ...]: ...

    def list_account_page(
        self,
        *,
        lifecycle_status: str | None,
        limit: int,
        cursor_created_timestamp: datetime | None,
        cursor_account_id: str | None,
    ) -> PaperAccountListPage: ...

    def get_history(
        self, *, account: PaperAccountRecord
    ) -> tuple[PaperAccountLedgerEventBundle, ...]: ...

    def get_history_page(
        self,
        *,
        account: PaperAccountRecord,
        after_sequence_number: int,
        limit: int,
    ) -> PaperAccountLedgerPage: ...

    def get_creation_key(
        self, *, creation_idempotency_key: str
    ) -> PaperAccountCreationKeyRecord | None: ...

    def get_projection(
        self, *, account: PaperAccountRecord
    ) -> PaperAccountProjection | None: ...

    def add_created_account(
        self,
        *,
        account: PaperAccountRecord,
        creation_key: PaperAccountCreationKeyRecord,
        bundle: PaperAccountLedgerEventBundle,
        projection: PaperAccountProjection,
        updated_timestamp: datetime,
    ) -> None: ...

    def append_mutation(
        self,
        *,
        prior_account: PaperAccountRecord,
        next_account: PaperAccountRecord,
        bundle: PaperAccountLedgerEventBundle,
        projection: PaperAccountProjection,
        updated_timestamp: datetime,
    ) -> bool: ...


class SqlAlchemyPaperAccountRepository:
    """Strict SQLAlchemy implementation that never commits caller work."""

    def __init__(self, *, session: Session) -> None:
        if not isinstance(session, Session):
            raise TypeError("session must be a SQLAlchemy Session")
        self._session = session

    def get_account(self, *, account_id: str) -> PaperAccountRecord | None:
        row = self._session.get(
            PaperAccountRow,
            _exact_string(account_id, "account_id", 512),
        )
        return None if row is None else account_record_from_row(row)

    def list_accounts(
        self, *, lifecycle_status: str | None = None
    ) -> tuple[PaperAccountRecord, ...]:
        statement = select(PaperAccountRow)
        if lifecycle_status is not None:
            if lifecycle_status not in ("active", "frozen", "closed"):
                raise ValueError("unsupported lifecycle status")
            statement = statement.where(
                PaperAccountRow.lifecycle_status == lifecycle_status
            )
        statement = statement.order_by(
            PaperAccountRow.created_timestamp.desc(),
            PaperAccountRow.account_id.asc(),
        )
        return tuple(
            account_record_from_row(row)
            for row in self._session.scalars(statement).all()
        )

    def list_account_page(
        self,
        *,
        lifecycle_status: str | None,
        limit: int,
        cursor_created_timestamp: datetime | None,
        cursor_account_id: str | None,
    ) -> PaperAccountListPage:
        if type(limit) is not int or not 1 <= limit <= 200:
            raise ValueError("account page limit must be an integer from 1 to 200")
        if (cursor_created_timestamp is None) is not (
            cursor_account_id is None
        ):
            raise ValueError("account page cursor anchors must be paired")
        statement = select(PaperAccountRow)
        if lifecycle_status is not None:
            if lifecycle_status not in ("active", "frozen", "closed"):
                raise ValueError("unsupported lifecycle status")
            statement = statement.where(
                PaperAccountRow.lifecycle_status == lifecycle_status
            )
        if cursor_created_timestamp is not None:
            cursor_timestamp = _exact_utc(
                cursor_created_timestamp,
                "cursor_created_timestamp",
            )
            cursor_id = _exact_string(
                cursor_account_id,
                "cursor_account_id",
                512,
            )
            statement = statement.where(
                or_(
                    PaperAccountRow.created_timestamp < cursor_timestamp,
                    and_(
                        PaperAccountRow.created_timestamp == cursor_timestamp,
                        PaperAccountRow.account_id > cursor_id,
                    ),
                )
            )
        rows = tuple(
            self._session.scalars(
                statement.order_by(
                    PaperAccountRow.created_timestamp.desc(),
                    PaperAccountRow.account_id.asc(),
                ).limit(limit + 1)
            ).all()
        )
        return PaperAccountListPage(
            items=tuple(account_record_from_row(row) for row in rows[:limit]),
            has_more=len(rows) > limit,
        )

    def get_history(
        self, *, account: PaperAccountRecord
    ) -> tuple[PaperAccountLedgerEventBundle, ...]:
        if type(account) is not PaperAccountRecord:
            raise ValueError("account must be PaperAccountRecord")
        event_rows = tuple(
            self._session.scalars(
                select(PaperAccountEventRow)
                .where(PaperAccountEventRow.account_id == account.account_id)
                .order_by(PaperAccountEventRow.sequence_number.asc())
            ).all()
        )
        cash = tuple(
            self._session.scalars(
                select(PaperCashLedgerEntryRow)
                .where(
                    PaperCashLedgerEntryRow.account_id == account.account_id
                )
                .order_by(
                    PaperCashLedgerEntryRow.event_id.asc(),
                    PaperCashLedgerEntryRow.entry_index.asc(),
                )
            ).all()
        )
        positions = tuple(
            self._session.scalars(
                select(PaperPositionLedgerEntryRow)
                .where(
                    PaperPositionLedgerEntryRow.account_id
                    == account.account_id
                )
                .order_by(
                    PaperPositionLedgerEntryRow.event_id.asc(),
                    PaperPositionLedgerEntryRow.entry_index.asc(),
                )
            ).all()
        )
        return reconstruct_history(
            account=account,
            event_rows=event_rows,
            cash_rows=cash,
            position_rows=positions,
        )

    def get_history_page(
        self,
        *,
        account: PaperAccountRecord,
        after_sequence_number: int,
        limit: int,
    ) -> PaperAccountLedgerPage:
        if type(account) is not PaperAccountRecord:
            raise ValueError("account must be PaperAccountRecord")
        if type(after_sequence_number) is not int or after_sequence_number < 0:
            raise ValueError("after_sequence_number must be a non-negative integer")
        if type(limit) is not int or not 1 <= limit <= 200:
            raise ValueError("ledger page limit must be an integer from 1 to 200")
        if after_sequence_number >= account.head_version:
            return PaperAccountLedgerPage(items=(), has_more=False)

        rows = tuple(
            self._session.scalars(
                select(PaperAccountEventRow)
                .where(
                    PaperAccountEventRow.account_id == account.account_id,
                    PaperAccountEventRow.sequence_number
                    > after_sequence_number,
                )
                .order_by(PaperAccountEventRow.sequence_number.asc())
                .limit(limit + 1)
            ).all()
        )
        if not rows:
            raise PaperAccountPersistenceCorruptionError()
        selected = rows[:limit]
        event_ids = tuple(row.event_id for row in selected)
        cash = tuple(
            self._session.scalars(
                select(PaperCashLedgerEntryRow)
                .where(
                    PaperCashLedgerEntryRow.account_id == account.account_id,
                    PaperCashLedgerEntryRow.event_id.in_(event_ids),
                )
                .order_by(
                    PaperCashLedgerEntryRow.event_id.asc(),
                    PaperCashLedgerEntryRow.entry_index.asc(),
                )
            ).all()
        )
        positions = tuple(
            self._session.scalars(
                select(PaperPositionLedgerEntryRow)
                .where(
                    PaperPositionLedgerEntryRow.account_id == account.account_id,
                    PaperPositionLedgerEntryRow.event_id.in_(event_ids),
                )
                .order_by(
                    PaperPositionLedgerEntryRow.event_id.asc(),
                    PaperPositionLedgerEntryRow.entry_index.asc(),
                )
            ).all()
        )
        execution_event_ids = {
            row.event_id
            for row in selected
            if row.event_type == "execution_fill_posted"
        }
        validated_execution_bundles: tuple[PaperAccountLedgerEventBundle, ...] = ()
        if execution_event_ids:
            fully_reconstructed = self.get_history(account=account)
            validated_execution_bundles = tuple(
                bundle
                for bundle in fully_reconstructed
                if bundle.event.event_id in execution_event_ids
            )
            if len(validated_execution_bundles) != len(execution_event_ids):
                raise PaperAccountPersistenceCorruptionError()
        previous_chain_digest = PAPER_ACCOUNT_GENESIS_CHAIN_DIGEST
        if after_sequence_number > 0:
            previous_chain_digest = cast(
                str | None,
                self._session.scalar(
                    select(PaperAccountEventRow.chain_digest).where(
                        PaperAccountEventRow.account_id == account.account_id,
                        PaperAccountEventRow.sequence_number
                        == after_sequence_number,
                    )
                ),
            )
            if previous_chain_digest is None:
                raise PaperAccountPersistenceCorruptionError()
        items = reconstruct_history_page_items(
            account=account,
            event_rows=selected,
            cash_rows=cash,
            position_rows=positions,
            expected_first_sequence=after_sequence_number + 1,
            previous_chain_digest=previous_chain_digest,
            validated_execution_bundles=validated_execution_bundles,
        )
        last = items[-1].event
        if last.sequence_number == account.head_version and (
            last.event_id != account.head_event_id
            or last.chain_digest != account.head_chain_digest
        ):
            raise PaperAccountPersistenceCorruptionError()
        return PaperAccountLedgerPage(
            items=items,
            has_more=len(rows) > limit,
        )

    def get_event_by_command_key(
        self,
        *,
        account_id: str,
        command_idempotency_key: str,
    ) -> PaperAccountEventRow | None:
        return self._session.scalar(
            select(PaperAccountEventRow).where(
                PaperAccountEventRow.account_id
                == _exact_string(account_id, "account_id", 512),
                PaperAccountEventRow.command_idempotency_key
                == _exact_string(
                    command_idempotency_key,
                    "command_idempotency_key",
                    128,
                ),
            )
        )

    def get_creation_key(
        self, *, creation_idempotency_key: str
    ) -> PaperAccountCreationKeyRecord | None:
        row = self._session.get(
            PaperAccountCreationKeyRow,
            _exact_string(
                creation_idempotency_key,
                "creation_idempotency_key",
                128,
            ),
        )
        if row is None:
            return None
        try:
            return PaperAccountCreationKeyRecord(
                record_schema_version=cast(object, row.record_schema_version),  # type: ignore[arg-type]
                creation_idempotency_key=row.creation_idempotency_key,
                creation_request_digest=row.creation_request_digest,
                account_id=row.account_id,
                creation_event_id=row.creation_event_id,
                created_timestamp=_exact_utc(
                    row.created_timestamp, "created_timestamp"
                ),
            )
        except (AttributeError, TypeError, ValueError) as exc:
            raise PaperAccountPersistenceCorruptionError() from exc

    def get_projection(
        self, *, account: PaperAccountRecord
    ) -> PaperAccountProjection | None:
        row = self._session.get(PaperAccountProjectionRow, account.account_id)
        if row is None:
            return None
        children = tuple(
            self._session.scalars(
                select(PaperAccountPositionProjectionRow)
                .where(
                    PaperAccountPositionProjectionRow.account_id
                    == account.account_id
                )
                .order_by(PaperAccountPositionProjectionRow.symbol.asc())
            ).all()
        )
        return projection_from_rows(
            account=account,
            row=row,
            position_rows=children,
        )

    def add_created_account(
        self,
        *,
        account: PaperAccountRecord,
        creation_key: PaperAccountCreationKeyRecord,
        bundle: PaperAccountLedgerEventBundle,
        projection: PaperAccountProjection,
        updated_timestamp: datetime,
    ) -> None:
        if (
            account.head_version != 1
            or bundle.event.event_type != "account_created"
            or bundle.resulting_state.head_version != 1
            or creation_key.account_id != account.account_id
            or creation_key.creation_event_id != bundle.event.event_id
            or projection.source_account_version != 1
        ):
            raise ValueError("created account records are inconsistent")
        parent, children = projection_rows(
            projection,
            updated_timestamp=updated_timestamp,
        )
        self._session.add(account_row_from_record(account))
        self._session.add(event_row(bundle))
        self._session.add_all(cash_rows(bundle))
        self._session.add_all(position_rows(bundle))
        self._session.add(
            PaperAccountCreationKeyRow(
                record_schema_version=creation_key.record_schema_version,
                creation_idempotency_key=(
                    creation_key.creation_idempotency_key
                ),
                creation_request_digest=creation_key.creation_request_digest,
                account_id=creation_key.account_id,
                creation_event_id=creation_key.creation_event_id,
                created_timestamp=creation_key.created_timestamp,
            )
        )
        self._session.add(parent)
        self._session.add_all(children)
        self._session.flush()

    def append_mutation(
        self,
        *,
        prior_account: PaperAccountRecord,
        next_account: PaperAccountRecord,
        bundle: PaperAccountLedgerEventBundle,
        projection: PaperAccountProjection,
        updated_timestamp: datetime,
    ) -> bool:
        if (
            prior_account.account_id != next_account.account_id
            or next_account.head_version != prior_account.head_version + 1
            or bundle.event.sequence_number != next_account.head_version
            or bundle.event.previous_chain_digest
            != prior_account.head_chain_digest
            or projection.source_account_version != next_account.head_version
        ):
            raise ValueError("mutation records are inconsistent")
        self._session.add(event_row(bundle))
        self._session.add_all(cash_rows(bundle))
        self._session.add_all(position_rows(bundle))
        result = self._session.execute(
            update(PaperAccountRow)
            .where(
                PaperAccountRow.account_id == prior_account.account_id,
                PaperAccountRow.head_version == prior_account.head_version,
                PaperAccountRow.head_event_id
                == prior_account.head_event_id,
                PaperAccountRow.head_chain_digest
                == prior_account.head_chain_digest,
            )
            .values(
                lifecycle_status=next_account.lifecycle_status,
                head_version=next_account.head_version,
                head_event_id=next_account.head_event_id,
                head_chain_digest=next_account.head_chain_digest,
                projection_status="current",
                updated_timestamp=next_account.updated_timestamp,
                closed_timestamp=next_account.closed_timestamp,
            )
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            return False
        self.replace_projection(
            projection=projection,
            updated_timestamp=updated_timestamp,
        )
        self._session.flush()
        return True

    def replace_projection(
        self,
        *,
        projection: PaperAccountProjection,
        updated_timestamp: datetime,
    ) -> None:
        parent, children = projection_rows(
            projection,
            updated_timestamp=updated_timestamp,
        )
        self._session.execute(
            delete(PaperAccountPositionProjectionRow).where(
                PaperAccountPositionProjectionRow.account_id
                == projection.account_id
            )
        )
        existing = self._session.get(
            PaperAccountProjectionRow,
            projection.account_id,
        )
        if existing is None:
            self._session.add(parent)
        else:
            for column in (
                "record_schema_version",
                "projection_schema_version",
                "lifecycle_status",
                "cash_balance",
                "available_cash",
                "approved_portfolio_reviews_payload",
                "source_account_version",
                "source_event_id",
                "source_chain_digest",
                "projection_digest",
                "updated_timestamp",
            ):
                setattr(existing, column, getattr(parent, column))
        self._session.add_all(children)
        self._session.flush()

    def update_projection_status(
        self,
        *,
        account: PaperAccountRecord,
        projection_status: PaperAccountProjectionStatus,
        updated_timestamp: datetime,
    ) -> bool:
        result = self._session.execute(
            update(PaperAccountRow)
            .where(
                PaperAccountRow.account_id == account.account_id,
                PaperAccountRow.head_version == account.head_version,
                PaperAccountRow.head_event_id == account.head_event_id,
                PaperAccountRow.head_chain_digest
                == account.head_chain_digest,
            )
            .values(
                projection_status=projection_status,
                updated_timestamp=_exact_utc(
                    updated_timestamp, "updated_timestamp"
                ),
            )
            .execution_options(synchronize_session=False)
        )
        self._session.flush()
        return result.rowcount == 1

    def add_snapshot(self, *, snapshot: PaperAccountSnapshot) -> None:
        self._session.add(snapshot_row(snapshot))
        self._session.flush()

    def get_snapshot(
        self, *, snapshot_id: str
    ) -> PaperAccountSnapshot | None:
        row = self._session.get(
            PaperAccountSnapshotRow,
            _exact_string(snapshot_id, "snapshot_id", 512),
        )
        return None if row is None else snapshot_from_row(row)

    def get_snapshot_by_operation_key(
        self, *, account_id: str, operation_idempotency_key: str
    ) -> PaperAccountSnapshot | None:
        row = self._session.scalar(
            select(PaperAccountSnapshotRow).where(
                PaperAccountSnapshotRow.account_id
                == _exact_string(account_id, "account_id", 512),
                PaperAccountSnapshotRow.operation_idempotency_key
                == _exact_string(
                    operation_idempotency_key,
                    "operation_idempotency_key",
                    128,
                ),
            )
        )
        return None if row is None else snapshot_from_row(row)

    def add_reconciliation(
        self, *, reconciliation: PaperAccountReconciliation
    ) -> None:
        self._session.add(reconciliation_row(reconciliation))
        self._session.flush()

    def get_reconciliation(
        self, *, reconciliation_id: str
    ) -> PaperAccountReconciliation | None:
        row = self._session.get(
            PaperAccountReconciliationRow,
            _exact_string(
                reconciliation_id,
                "reconciliation_id",
                512,
            ),
        )
        return None if row is None else reconciliation_from_row(row)

    def get_reconciliation_by_operation_key(
        self, *, account_id: str, operation_idempotency_key: str
    ) -> PaperAccountReconciliation | None:
        row = self._session.scalar(
            select(PaperAccountReconciliationRow).where(
                PaperAccountReconciliationRow.account_id
                == _exact_string(account_id, "account_id", 512),
                PaperAccountReconciliationRow.operation_idempotency_key
                == _exact_string(
                    operation_idempotency_key,
                    "operation_idempotency_key",
                    128,
                ),
            )
        )
        return None if row is None else reconciliation_from_row(row)


__all__ = [
    "PaperAccountRepository",
    "SqlAlchemyPaperAccountRepository",
]
