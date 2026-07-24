"""SQLAlchemy rows for durable Paper Account persistence.

The model module is declarative only: importing it creates no engine, session,
database file, or network resource.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from el_psy_quant.persistence.base import ProductPersistenceBase


class StrictSQLiteBoolean(TypeDecorator[bool]):
    """Persist exact 0/1 and reject corrupted non-boolean SQLite values."""

    impl = Integer
    cache_ok = True

    def process_bind_param(self, value: object, dialect: object) -> int:
        del dialect
        if type(value) is not bool:
            raise ValueError("strict SQLite boolean must be bool")
        return 1 if value else 0

    def process_result_value(self, value: object, dialect: object) -> bool:
        del dialect
        if type(value) is not int or value not in (0, 1):
            raise ValueError("persisted SQLite boolean must be 0 or 1")
        return bool(value)


class PaperAccountRow(ProductPersistenceBase):
    __tablename__ = "paper_accounts"
    __table_args__ = (
        CheckConstraint(
            "record_schema_version = 1",
            name="ck_paper_accounts_record_schema_version",
        ),
        CheckConstraint(
            "lifecycle_status IN ('active', 'frozen', 'closed')",
            name="ck_paper_accounts_lifecycle_status",
        ),
        CheckConstraint(
            "projection_status IN ('current', 'reconciliation_required')",
            name="ck_paper_accounts_projection_status",
        ),
        CheckConstraint(
            "head_version > 0",
            name="ck_paper_accounts_head_version",
        ),
        ForeignKeyConstraint(
            ["account_id", "head_event_id"],
            ["paper_account_events.account_id", "paper_account_events.event_id"],
            name="fk_paper_accounts_head_event",
            deferrable=True,
            initially="DEFERRED",
        ),
        Index(
            "ix_paper_accounts_created_timestamp",
            "created_timestamp",
            "account_id",
        ),
        Index(
            "ix_paper_accounts_lifecycle_status",
            "lifecycle_status",
            "created_timestamp",
            "account_id",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    account_id: Mapped[str] = mapped_column(String(512), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    lifecycle_status: Mapped[str] = mapped_column(String(16), nullable=False)
    head_version: Mapped[int] = mapped_column(Integer, nullable=False)
    head_event_id: Mapped[str] = mapped_column(String(512), nullable=False)
    head_chain_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    projection_status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_by: Mapped[str] = mapped_column(String(512), nullable=False)
    created_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    closed_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class PaperAccountEventRow(ProductPersistenceBase):
    __tablename__ = "paper_account_events"
    __table_args__ = (
        CheckConstraint(
            "record_schema_version = 1",
            name="ck_paper_account_events_record_schema_version",
        ),
        CheckConstraint(
            "event_schema_version = 1",
            name="ck_paper_account_events_event_schema_version",
        ),
        CheckConstraint(
            "sequence_number > 0 AND account_version = sequence_number",
            name="ck_paper_account_events_sequence_version",
        ),
        ForeignKeyConstraint(
            ["account_id"],
            ["paper_accounts.account_id"],
            name="fk_paper_account_events_account_id",
            deferrable=True,
            initially="DEFERRED",
        ),
        UniqueConstraint(
            "account_id",
            "event_id",
            name="uq_paper_account_events_account_event",
        ),
        UniqueConstraint(
            "account_id",
            "sequence_number",
            name="uq_paper_account_events_account_sequence",
        ),
        UniqueConstraint(
            "account_id",
            "command_idempotency_key",
            name="uq_paper_account_events_account_command_key",
        ),
        UniqueConstraint(
            "event_digest",
            name="uq_paper_account_events_event_digest",
        ),
        Index(
            "ix_paper_account_events_account_recorded",
            "account_id",
            "recorded_timestamp",
            "event_id",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    event_schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    event_id: Mapped[str] = mapped_column(String(512), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(512), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    account_version: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(48), nullable=False)
    command_idempotency_key: Mapped[str] = mapped_column(
        String(128), nullable=False
    )
    command_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    expected_account_version: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    actor: Mapped[str] = mapped_column(String(512), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    effective_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    recorded_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    details_payload: Mapped[str] = mapped_column(Text, nullable=False)
    previous_chain_digest: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    event_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    chain_digest: Mapped[str] = mapped_column(String(64), nullable=False)


class PaperCashLedgerEntryRow(ProductPersistenceBase):
    __tablename__ = "paper_cash_ledger_entries"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "event_id"],
            ["paper_account_events.account_id", "paper_account_events.event_id"],
            name="fk_paper_cash_entries_account_event",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "event_id",
            "entry_index",
            name="uq_paper_cash_entries_event_index",
        ),
        UniqueConstraint(
            "entry_digest",
            name="uq_paper_cash_entries_entry_digest",
        ),
        Index(
            "ix_paper_cash_entries_account_event",
            "account_id",
            "event_id",
            "entry_index",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    cash_entry_id: Mapped[str] = mapped_column(String(512), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(512), nullable=False)
    event_id: Mapped[str] = mapped_column(String(512), nullable=False)
    entry_index: Mapped[int] = mapped_column(Integer, nullable=False)
    movement_type: Mapped[str] = mapped_column(String(24), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    signed_amount: Mapped[str] = mapped_column(String(64), nullable=False)
    entry_digest: Mapped[str] = mapped_column(String(64), nullable=False)


class PaperPositionLedgerEntryRow(ProductPersistenceBase):
    __tablename__ = "paper_position_ledger_entries"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "event_id"],
            ["paper_account_events.account_id", "paper_account_events.event_id"],
            name="fk_paper_position_entries_account_event",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "event_id",
            "entry_index",
            name="uq_paper_position_entries_event_index",
        ),
        UniqueConstraint(
            "entry_digest",
            name="uq_paper_position_entries_entry_digest",
        ),
        Index(
            "ix_paper_position_entries_account_event",
            "account_id",
            "event_id",
            "entry_index",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    position_entry_id: Mapped[str] = mapped_column(
        String(512), primary_key=True
    )
    account_id: Mapped[str] = mapped_column(String(512), nullable=False)
    event_id: Mapped[str] = mapped_column(String(512), nullable=False)
    entry_index: Mapped[int] = mapped_column(Integer, nullable=False)
    symbol: Mapped[str] = mapped_column(String(128), nullable=False)
    signed_quantity_delta: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    signed_cost_basis_delta: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    adjustment_category: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    entry_digest: Mapped[str] = mapped_column(String(64), nullable=False)


class PaperAccountCreationKeyRow(ProductPersistenceBase):
    __tablename__ = "paper_account_creation_keys"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "creation_event_id"],
            ["paper_account_events.account_id", "paper_account_events.event_id"],
            name="fk_paper_account_creation_keys_account_event",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "account_id", name="uq_paper_account_creation_keys_account_id"
        ),
        UniqueConstraint(
            "creation_event_id",
            name="uq_paper_account_creation_keys_event_id",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    creation_idempotency_key: Mapped[str] = mapped_column(
        String(128), primary_key=True
    )
    creation_request_digest: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    account_id: Mapped[str] = mapped_column(String(512), nullable=False)
    creation_event_id: Mapped[str] = mapped_column(String(512), nullable=False)
    created_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class PaperAccountProjectionRow(ProductPersistenceBase):
    __tablename__ = "paper_account_projections"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id"],
            ["paper_accounts.account_id"],
            name="fk_paper_account_projections_account_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["account_id", "source_event_id"],
            ["paper_account_events.account_id", "paper_account_events.event_id"],
            name="fk_paper_account_projections_source_event",
            ondelete="RESTRICT",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    projection_schema_version: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    account_id: Mapped[str] = mapped_column(String(512), primary_key=True)
    lifecycle_status: Mapped[str] = mapped_column(String(16), nullable=False)
    cash_balance: Mapped[str] = mapped_column(String(64), nullable=False)
    available_cash: Mapped[str] = mapped_column(String(64), nullable=False)
    approved_portfolio_reviews_payload: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    source_account_version: Mapped[int] = mapped_column(Integer, nullable=False)
    source_event_id: Mapped[str] = mapped_column(String(512), nullable=False)
    source_chain_digest: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    projection_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class PaperAccountPositionProjectionRow(ProductPersistenceBase):
    __tablename__ = "paper_account_position_projections"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id"],
            ["paper_account_projections.account_id"],
            name="fk_paper_position_projections_account_id",
            ondelete="CASCADE",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    position_projection_schema_version: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    account_id: Mapped[str] = mapped_column(String(512), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(128), primary_key=True)
    quantity: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_cost_basis: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    average_unit_cost: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    average_unit_cost_is_rounded: Mapped[bool] = mapped_column(
        StrictSQLiteBoolean(), nullable=False
    )


class PaperAccountSnapshotRow(ProductPersistenceBase):
    __tablename__ = "paper_account_snapshots"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "head_event_id"],
            ["paper_account_events.account_id", "paper_account_events.event_id"],
            name="fk_paper_account_snapshots_head_event",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "account_id",
            "operation_idempotency_key",
            name="uq_paper_account_snapshots_account_operation_key",
        ),
        UniqueConstraint(
            "snapshot_digest",
            name="uq_paper_account_snapshots_snapshot_digest",
        ),
        Index(
            "ix_paper_account_snapshots_account_version",
            "account_id",
            "account_version",
            "snapshot_id",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_id: Mapped[str] = mapped_column(String(512), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(512), nullable=False)
    account_version: Mapped[int] = mapped_column(Integer, nullable=False)
    head_event_id: Mapped[str] = mapped_column(String(512), nullable=False)
    head_chain_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    operation_idempotency_key: Mapped[str] = mapped_column(
        String(128), nullable=False
    )
    operation_command_digest: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    created_by: Mapped[str] = mapped_column(String(512), nullable=False)
    recorded_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    reason: Mapped[str] = mapped_column(String(2000), nullable=False)
    projection_payload: Mapped[str] = mapped_column(Text, nullable=False)
    projection_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot_digest: Mapped[str] = mapped_column(String(64), nullable=False)


class PaperAccountReconciliationRow(ProductPersistenceBase):
    __tablename__ = "paper_account_reconciliations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "authoritative_event_id"],
            ["paper_account_events.account_id", "paper_account_events.event_id"],
            name="fk_paper_account_reconciliations_authoritative_event",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["account_id", "candidate_event_id"],
            ["paper_account_events.account_id", "paper_account_events.event_id"],
            name="fk_paper_account_reconciliations_candidate_event",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "account_id",
            "operation_idempotency_key",
            name="uq_paper_account_reconciliations_account_operation_key",
        ),
        UniqueConstraint(
            "reconciliation_digest",
            name="uq_paper_account_reconciliations_digest",
        ),
        Index(
            "ix_paper_account_reconciliations_account_recorded",
            "account_id",
            "recorded_timestamp",
            "reconciliation_id",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    reconciliation_schema_version: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    reconciliation_id: Mapped[str] = mapped_column(
        String(512), primary_key=True
    )
    account_id: Mapped[str] = mapped_column(String(512), nullable=False)
    operation_idempotency_key: Mapped[str] = mapped_column(
        String(128), nullable=False
    )
    operation_command_digest: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    created_by: Mapped[str] = mapped_column(String(512), nullable=False)
    recorded_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    reason: Mapped[str] = mapped_column(String(2000), nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    mismatch_codes_payload: Mapped[str] = mapped_column(Text, nullable=False)
    authoritative_account_version: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    authoritative_event_id: Mapped[str] = mapped_column(
        String(512), nullable=False
    )
    authoritative_chain_digest: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    authoritative_projection_digest: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    candidate_account_version: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    candidate_event_id: Mapped[str] = mapped_column(
        String(512), nullable=False
    )
    candidate_chain_digest: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    candidate_projection_digest: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    reconciliation_digest: Mapped[str] = mapped_column(
        String(64), nullable=False
    )


__all__ = [
    "PaperAccountCreationKeyRow",
    "PaperAccountEventRow",
    "PaperAccountPositionProjectionRow",
    "PaperAccountProjectionRow",
    "PaperAccountReconciliationRow",
    "PaperAccountRow",
    "PaperAccountSnapshotRow",
    "PaperCashLedgerEntryRow",
    "PaperPositionLedgerEntryRow",
    "StrictSQLiteBoolean",
]
