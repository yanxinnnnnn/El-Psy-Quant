"""Internal SQLAlchemy rows for durable M34 execution authority."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from el_psy_quant.persistence.base import ProductPersistenceBase

_DIGEST_CHECK = "length({0}) = 64 AND {0} NOT GLOB '*[^0-9a-f]*'"


class PaperExecutionOrderRow(ProductPersistenceBase):
    __tablename__ = "paper_execution_orders"
    __table_args__ = (
        PrimaryKeyConstraint("execution_order_id", name="pk_paper_execution_orders"),
        UniqueConstraint(
            "execution_order_digest", name="uq_paper_execution_orders_digest"
        ),
        ForeignKeyConstraint(
            ("intent_id",),
            ("order_intents.intent_id",),
            name="fk_paper_execution_orders_intent",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("risk_decision_id",),
            ("pre_trade_risk_decisions.decision_id",),
            name="fk_paper_execution_orders_decision",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("account_id",),
            ("paper_accounts.account_id",),
            name="fk_paper_execution_orders_account",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("account_handoff_event_id",),
            ("paper_account_events.event_id",),
            name="fk_paper_execution_orders_account_event",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("calendar_id",),
            ("trading_calendars.calendar_id",),
            name="fk_paper_execution_orders_calendar",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("trading_session_id",),
            ("trading_sessions.session_id",),
            name="fk_paper_execution_orders_session",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("replay_id",),
            ("market_data_replays.replay_id",),
            name="fk_paper_execution_orders_replay",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("handoff_event_id",),
            ("market_data_events.event_id",),
            name="fk_paper_execution_orders_market_event",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "record_schema_version = 1 AND order_schema_version = 1",
            name="ck_paper_execution_orders_versions",
        ),
        CheckConstraint(
            _DIGEST_CHECK.format("execution_order_digest"),
            name="ck_paper_execution_orders_digest",
        ),
        CheckConstraint(
            "side IN ('buy', 'sell')", name="ck_paper_execution_orders_side"
        ),
        Index(
            "ix_paper_execution_orders_created_id", "created_at", "execution_order_id"
        ),
        Index(
            "ix_paper_execution_orders_working_tuple",
            "account_id",
            "replay_id",
            "trading_session_id",
            "execution_order_id",
        ),
        Index(
            "ix_paper_execution_orders_intent_policy",
            "intent_id",
            "policy_reference_digest",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    order_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    execution_order_id: Mapped[str] = mapped_column(String(96), nullable=False)
    execution_order_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text(), nullable=False)
    intent_id: Mapped[str] = mapped_column(String(80), nullable=False)
    intent_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_decision_id: Mapped[str] = mapped_column(String(96), nullable=False)
    risk_decision_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_snapshot_id: Mapped[str] = mapped_column(String(96), nullable=False)
    risk_snapshot_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    account_id: Mapped[str] = mapped_column(String(512), nullable=False)
    account_handoff_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    account_handoff_event_id: Mapped[str] = mapped_column(String(512), nullable=False)
    account_handoff_chain_digest: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    calendar_id: Mapped[str] = mapped_column(String(512), nullable=False)
    calendar_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    trading_session_id: Mapped[str] = mapped_column(String(512), nullable=False)
    replay_id: Mapped[str] = mapped_column(String(512), nullable=False)
    event_stream_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    handoff_cursor_position: Mapped[int] = mapped_column(Integer(), nullable=False)
    handoff_event_id: Mapped[str] = mapped_column(String(512), nullable=False)
    instrument_id: Mapped[str] = mapped_column(String(512), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    requested_quantity: Mapped[str] = mapped_column(String(128), nullable=False)
    policy_id: Mapped[str] = mapped_column(String(128), nullable=False)
    policy_configuration_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    policy_reference_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    origin_command_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class PaperExecutionAttemptRow(ProductPersistenceBase):
    __tablename__ = "paper_execution_attempts"
    __table_args__ = (
        PrimaryKeyConstraint("attempt_id", name="pk_paper_execution_attempts"),
        UniqueConstraint("attempt_digest", name="uq_paper_execution_attempts_digest"),
        UniqueConstraint(
            "execution_order_id",
            "execution_version_before",
            name="uq_paper_execution_attempts_version_before",
        ),
        UniqueConstraint(
            "execution_order_id",
            "execution_version_after",
            name="uq_paper_execution_attempts_version_after",
        ),
        ForeignKeyConstraint(
            ("execution_order_id",),
            ("paper_execution_orders.execution_order_id",),
            name="fk_paper_execution_attempts_order",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("consumed_event_id",),
            ("market_data_events.event_id",),
            name="fk_paper_execution_attempts_event",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "record_schema_version = 1 AND attempt_schema_version = 1",
            name="ck_paper_execution_attempts_versions",
        ),
        CheckConstraint(
            "execution_version_before >= 0 AND execution_version_after = execution_version_before + 1",
            name="ck_paper_execution_attempts_sequence",
        ),
        CheckConstraint(
            "attempt_result IN ('no_fill', 'fill', 'risk_rejected', 'boundary_rejected')",
            name="ck_paper_execution_attempts_result",
        ),
        Index(
            "ix_paper_execution_attempts_order_version",
            "execution_order_id",
            "execution_version_before",
        ),
        Index(
            "ix_paper_execution_attempts_event",
            "execution_order_id",
            "consumed_event_position",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    attempt_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    attempt_id: Mapped[str] = mapped_column(String(96), nullable=False)
    attempt_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    execution_order_id: Mapped[str] = mapped_column(String(96), nullable=False)
    execution_version_before: Mapped[int] = mapped_column(Integer(), nullable=False)
    execution_version_after: Mapped[int] = mapped_column(Integer(), nullable=False)
    attempt_result: Mapped[str] = mapped_column(String(32), nullable=False)
    consumed_event_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    consumed_event_position: Mapped[int | None] = mapped_column(
        Integer(), nullable=True
    )
    pre_cursor_position: Mapped[int] = mapped_column(Integer(), nullable=False)
    pre_cursor_last_event_id: Mapped[str | None] = mapped_column(
        String(512), nullable=True
    )
    post_cursor_position: Mapped[int] = mapped_column(Integer(), nullable=False)
    post_cursor_last_event_id: Mapped[str | None] = mapped_column(
        String(512), nullable=True
    )
    payload_json: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class PaperExecutionFillRow(ProductPersistenceBase):
    __tablename__ = "paper_execution_fills"
    __table_args__ = (
        PrimaryKeyConstraint("fill_id", name="pk_paper_execution_fills"),
        UniqueConstraint("fill_digest", name="uq_paper_execution_fills_digest"),
        UniqueConstraint("attempt_id", name="uq_paper_execution_fills_attempt"),
        UniqueConstraint(
            "execution_order_id",
            "consumed_event_position",
            name="uq_paper_execution_fills_order_event_position",
        ),
        ForeignKeyConstraint(
            ("execution_order_id",),
            ("paper_execution_orders.execution_order_id",),
            name="fk_paper_execution_fills_order",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("attempt_id",),
            ("paper_execution_attempts.attempt_id",),
            name="fk_paper_execution_fills_attempt",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("consumed_event_id",),
            ("market_data_events.event_id",),
            name="fk_paper_execution_fills_event",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "record_schema_version = 1 AND fill_schema_version = 1",
            name="ck_paper_execution_fills_versions",
        ),
        Index(
            "ix_paper_execution_fills_order_created",
            "execution_order_id",
            "created_at",
            "fill_id",
        ),
        Index(
            "ix_paper_execution_fills_event", "execution_order_id", "consumed_event_id"
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    fill_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    fill_id: Mapped[str] = mapped_column(String(96), nullable=False)
    fill_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    execution_order_id: Mapped[str] = mapped_column(String(96), nullable=False)
    attempt_id: Mapped[str] = mapped_column(String(96), nullable=False)
    consumed_event_id: Mapped[str] = mapped_column(String(512), nullable=False)
    consumed_event_position: Mapped[int] = mapped_column(Integer(), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class PaperExecutionSettlementLinkRow(ProductPersistenceBase):
    __tablename__ = "paper_execution_settlement_links"
    __table_args__ = (
        PrimaryKeyConstraint(
            "settlement_link_id", name="pk_paper_execution_settlement_links"
        ),
        UniqueConstraint(
            "settlement_link_digest", name="uq_paper_execution_settlement_links_digest"
        ),
        UniqueConstraint(
            "settlement_link_evidence_digest",
            name="uq_paper_execution_settlement_links_evidence",
        ),
        UniqueConstraint("fill_id", name="uq_paper_execution_settlement_links_fill"),
        UniqueConstraint(
            "account_event_id", name="uq_paper_execution_settlement_links_event"
        ),
        ForeignKeyConstraint(
            ("execution_order_id",),
            ("paper_execution_orders.execution_order_id",),
            name="fk_paper_execution_settlement_links_order",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("attempt_id",),
            ("paper_execution_attempts.attempt_id",),
            name="fk_paper_execution_settlement_links_attempt",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("fill_id",),
            ("paper_execution_fills.fill_id",),
            name="fk_paper_execution_settlement_links_fill",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("account_event_id",),
            ("paper_account_events.event_id",),
            name="fk_paper_execution_settlement_links_account_event",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("cash_entry_id",),
            ("paper_cash_ledger_entries.cash_entry_id",),
            name="fk_paper_execution_settlement_links_cash",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("position_entry_id",),
            ("paper_position_ledger_entries.position_entry_id",),
            name="fk_paper_execution_settlement_links_position",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "record_schema_version = 1 AND settlement_link_schema_version = 1",
            name="ck_paper_execution_settlement_links_versions",
        ),
        Index(
            "ix_paper_execution_settlement_links_order",
            "execution_order_id",
            "attempt_id",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    settlement_link_schema_version: Mapped[int] = mapped_column(
        Integer(), nullable=False
    )
    settlement_link_id: Mapped[str] = mapped_column(String(96), nullable=False)
    settlement_link_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    settlement_link_evidence_digest: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    execution_order_id: Mapped[str] = mapped_column(String(96), nullable=False)
    attempt_id: Mapped[str] = mapped_column(String(96), nullable=False)
    fill_id: Mapped[str] = mapped_column(String(96), nullable=False)
    account_id: Mapped[str] = mapped_column(String(512), nullable=False)
    account_event_id: Mapped[str] = mapped_column(String(512), nullable=False)
    cash_entry_id: Mapped[str] = mapped_column(String(512), nullable=False)
    position_entry_id: Mapped[str] = mapped_column(String(512), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text(), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class PaperExecutionCommandReceiptRow(ProductPersistenceBase):
    __tablename__ = "paper_execution_command_receipts"
    __table_args__ = (
        PrimaryKeyConstraint(
            "namespace",
            "command_idempotency_key",
            name="pk_paper_execution_command_receipts",
        ),
        UniqueConstraint(
            "namespace",
            "command_digest",
            name="uq_paper_execution_command_receipts_digest",
        ),
        ForeignKeyConstraint(
            ("execution_order_id",),
            ("paper_execution_orders.execution_order_id",),
            name="fk_paper_execution_receipts_order",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("attempt_id",),
            ("paper_execution_attempts.attempt_id",),
            name="fk_paper_execution_receipts_attempt",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("fill_id",),
            ("paper_execution_fills.fill_id",),
            name="fk_paper_execution_receipts_fill",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("settlement_link_id",),
            ("paper_execution_settlement_links.settlement_link_id",),
            name="fk_paper_execution_receipts_link",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("account_event_id",),
            ("paper_account_events.event_id",),
            name="fk_paper_execution_receipts_event",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "record_schema_version = 1", name="ck_paper_execution_receipts_version"
        ),
        CheckConstraint(
            "namespace IN ('create_paper_execution_order', 'step_paper_execution_order')",
            name="ck_paper_execution_receipts_namespace",
        ),
        CheckConstraint(
            "result_kind IN ('paper_execution_order', 'paper_execution_step')",
            name="ck_paper_execution_receipts_result_kind",
        ),
        CheckConstraint(
            "(result_kind = 'paper_execution_order' AND attempt_id IS NULL AND fill_id IS NULL "
            "AND settlement_link_id IS NULL AND account_event_id IS NULL) OR "
            "(result_kind = 'paper_execution_step' AND attempt_id IS NOT NULL "
            "AND ((fill_id IS NULL AND settlement_link_id IS NULL AND account_event_id IS NULL) OR "
            "(fill_id IS NOT NULL AND settlement_link_id IS NOT NULL AND account_event_id IS NOT NULL)))",
            name="ck_paper_execution_receipts_result_refs",
        ),
        Index(
            "ix_paper_execution_receipts_result",
            "result_kind",
            "execution_order_id",
            "attempt_id",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    namespace: Mapped[str] = mapped_column(String(64), nullable=False)
    command_idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    command_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    command_actor: Mapped[str] = mapped_column(String(256), nullable=False)
    result_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    execution_order_id: Mapped[str] = mapped_column(String(96), nullable=False)
    execution_order_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    attempt_id: Mapped[str | None] = mapped_column(String(96), nullable=True)
    attempt_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fill_id: Mapped[str | None] = mapped_column(String(96), nullable=True)
    fill_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    settlement_link_id: Mapped[str | None] = mapped_column(String(96), nullable=True)
    settlement_link_evidence_digest: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    account_event_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


__all__ = [
    "PaperExecutionAttemptRow",
    "PaperExecutionCommandReceiptRow",
    "PaperExecutionFillRow",
    "PaperExecutionOrderRow",
    "PaperExecutionSettlementLinkRow",
]
