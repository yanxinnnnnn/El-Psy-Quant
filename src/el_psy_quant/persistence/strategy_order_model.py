"""Internal SQLAlchemy models for durable M33 strategy-to-risk authority."""

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


class StrategySignalRow(ProductPersistenceBase):
    """One immutable canonical Strategy Signal."""

    __tablename__ = "strategy_signals"
    __table_args__ = (
        PrimaryKeyConstraint("signal_id", name="pk_strategy_signals"),
        UniqueConstraint("signal_digest", name="uq_strategy_signals_digest"),
        ForeignKeyConstraint(
            ("calendar_id",),
            ("trading_calendars.calendar_id",),
            name="fk_strategy_signals_calendar",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("trading_session_id",),
            ("trading_sessions.session_id",),
            name="fk_strategy_signals_session",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("replay_id",),
            ("market_data_replays.replay_id",),
            name="fk_strategy_signals_replay",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("signal_event_id",),
            ("market_data_events.event_id",),
            name="fk_strategy_signals_event",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "record_schema_version = 1 AND signal_schema_version = 1",
            name="ck_strategy_signals_versions",
        ),
        CheckConstraint(
            _DIGEST_CHECK.format("signal_digest"),
            name="ck_strategy_signals_digest",
        ),
        CheckConstraint(
            _DIGEST_CHECK.format("parameters_digest"),
            name="ck_strategy_signals_parameters_digest",
        ),
        CheckConstraint(
            _DIGEST_CHECK.format("event_stream_digest"),
            name="ck_strategy_signals_stream_digest",
        ),
        CheckConstraint(
            "cursor_position >= 1",
            name="ck_strategy_signals_cursor",
        ),
        Index(
            "ix_strategy_signals_created_id",
            "created_at",
            "signal_id",
        ),
        Index(
            "ix_strategy_signals_strategy_instrument",
            "strategy_name",
            "strategy_version",
            "adapter_version",
            "instrument_id",
            "signal_id",
        ),
        Index(
            "ix_strategy_signals_market_anchor",
            "calendar_id",
            "trading_session_id",
            "replay_id",
            "cursor_position",
            "signal_id",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    signal_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    signal_id: Mapped[str] = mapped_column(String(80), nullable=False)
    signal_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text(), nullable=False)
    strategy_name: Mapped[str] = mapped_column(String(128), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    adapter_version: Mapped[str] = mapped_column(String(64), nullable=False)
    parameters_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    calendar_id: Mapped[str] = mapped_column(String(512), nullable=False)
    calendar_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    trading_session_id: Mapped[str] = mapped_column(String(512), nullable=False)
    replay_id: Mapped[str] = mapped_column(String(512), nullable=False)
    event_stream_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    cursor_position: Mapped[int] = mapped_column(Integer(), nullable=False)
    signal_event_id: Mapped[str] = mapped_column(String(512), nullable=False)
    instrument_id: Mapped[str] = mapped_column(String(512), nullable=False)
    target_semantics: Mapped[str] = mapped_column(String(64), nullable=False)
    target_position_quantity: Mapped[str] = mapped_column(
        String(128), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class OrderIntentRow(ProductPersistenceBase):
    """One immutable account-bound M33 Order Intent."""

    __tablename__ = "order_intents"
    __table_args__ = (
        PrimaryKeyConstraint("intent_id", name="pk_order_intents"),
        UniqueConstraint("intent_digest", name="uq_order_intents_digest"),
        ForeignKeyConstraint(
            ("signal_id",),
            ("strategy_signals.signal_id",),
            name="fk_order_intents_signal",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("account_id",),
            ("paper_accounts.account_id",),
            name="fk_order_intents_account",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("account_head_event_id",),
            ("paper_account_events.event_id",),
            name="fk_order_intents_account_event",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("replay_id",),
            ("market_data_replays.replay_id",),
            name="fk_order_intents_replay",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("current_event_id",),
            ("market_data_events.event_id",),
            name="fk_order_intents_market_event",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "record_schema_version = 1 AND intent_schema_version = 1",
            name="ck_order_intents_versions",
        ),
        CheckConstraint(
            _DIGEST_CHECK.format("intent_digest"),
            name="ck_order_intents_digest",
        ),
        CheckConstraint(
            _DIGEST_CHECK.format("signal_digest"),
            name="ck_order_intents_signal_digest",
        ),
        CheckConstraint(
            _DIGEST_CHECK.format("account_head_chain_digest"),
            name="ck_order_intents_account_digest",
        ),
        CheckConstraint(
            _DIGEST_CHECK.format("event_stream_digest"),
            name="ck_order_intents_stream_digest",
        ),
        CheckConstraint(
            "side IN ('buy', 'sell')",
            name="ck_order_intents_side",
        ),
        Index(
            "ix_order_intents_created_id",
            "created_at",
            "intent_id",
        ),
        Index(
            "ix_order_intents_signal_account",
            "signal_id",
            "account_id",
            "intent_id",
        ),
        Index(
            "ix_order_intents_market_anchor",
            "replay_id",
            "cursor_position",
            "instrument_id",
            "intent_id",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    intent_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    intent_id: Mapped[str] = mapped_column(String(80), nullable=False)
    intent_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text(), nullable=False)
    signal_id: Mapped[str] = mapped_column(String(80), nullable=False)
    signal_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    account_id: Mapped[str] = mapped_column(String(512), nullable=False)
    account_head_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    account_head_event_id: Mapped[str] = mapped_column(String(512), nullable=False)
    account_head_chain_digest: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    calendar_id: Mapped[str] = mapped_column(String(512), nullable=False)
    trading_session_id: Mapped[str] = mapped_column(String(512), nullable=False)
    replay_id: Mapped[str] = mapped_column(String(512), nullable=False)
    event_stream_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    cursor_position: Mapped[int] = mapped_column(Integer(), nullable=False)
    current_event_id: Mapped[str] = mapped_column(String(512), nullable=False)
    instrument_id: Mapped[str] = mapped_column(String(512), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    requested_quantity: Mapped[str] = mapped_column(String(128), nullable=False)
    target_position_quantity: Mapped[str] = mapped_column(
        String(128), nullable=False
    )
    current_position_quantity: Mapped[str] = mapped_column(
        String(128), nullable=False
    )
    intent_policy_version: Mapped[str] = mapped_column(
        String(128), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class PreTradeRiskDecisionRow(ProductPersistenceBase):
    """One immutable decision containing its complete immutable snapshot."""

    __tablename__ = "pre_trade_risk_decisions"
    __table_args__ = (
        PrimaryKeyConstraint(
            "decision_id", name="pk_pre_trade_risk_decisions"
        ),
        UniqueConstraint(
            "decision_digest", name="uq_pre_trade_risk_decisions_digest"
        ),
        UniqueConstraint(
            "snapshot_id", name="uq_pre_trade_risk_decisions_snapshot_id"
        ),
        UniqueConstraint(
            "snapshot_digest",
            name="uq_pre_trade_risk_decisions_snapshot_digest",
        ),
        ForeignKeyConstraint(
            ("intent_id",),
            ("order_intents.intent_id",),
            name="fk_pre_trade_risk_decisions_intent",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("account_id",),
            ("paper_accounts.account_id",),
            name="fk_pre_trade_risk_decisions_account",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("replay_id",),
            ("market_data_replays.replay_id",),
            name="fk_pre_trade_risk_decisions_replay",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "record_schema_version = 1 AND decision_schema_version = 1",
            name="ck_pre_trade_risk_decisions_versions",
        ),
        CheckConstraint(
            _DIGEST_CHECK.format("decision_digest"),
            name="ck_pre_trade_risk_decisions_digest",
        ),
        CheckConstraint(
            _DIGEST_CHECK.format("snapshot_digest"),
            name="ck_pre_trade_risk_decisions_snapshot_digest",
        ),
        CheckConstraint(
            _DIGEST_CHECK.format("intent_digest"),
            name="ck_pre_trade_risk_decisions_intent_digest",
        ),
        CheckConstraint(
            _DIGEST_CHECK.format("risk_policy_configuration_digest"),
            name="ck_pre_trade_risk_decisions_policy_digest",
        ),
        CheckConstraint(
            "outcome IN ('allow', 'reject')",
            name="ck_pre_trade_risk_decisions_outcome",
        ),
        Index(
            "ix_pre_trade_risk_decisions_created_id",
            "created_at",
            "decision_id",
        ),
        Index(
            "ix_pre_trade_risk_decisions_intent_outcome",
            "intent_id",
            "outcome",
            "decision_id",
        ),
        Index(
            "ix_pre_trade_risk_decisions_account_market",
            "account_id",
            "replay_id",
            "cursor_position",
            "decision_id",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    decision_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    decision_id: Mapped[str] = mapped_column(String(96), nullable=False)
    decision_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text(), nullable=False)
    snapshot_id: Mapped[str] = mapped_column(String(96), nullable=False)
    snapshot_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    intent_id: Mapped[str] = mapped_column(String(80), nullable=False)
    intent_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    account_id: Mapped[str] = mapped_column(String(512), nullable=False)
    account_head_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    account_head_event_id: Mapped[str] = mapped_column(String(512), nullable=False)
    account_head_chain_digest: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    calendar_id: Mapped[str] = mapped_column(String(512), nullable=False)
    trading_session_id: Mapped[str] = mapped_column(String(512), nullable=False)
    replay_id: Mapped[str] = mapped_column(String(512), nullable=False)
    event_stream_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    cursor_position: Mapped[int] = mapped_column(Integer(), nullable=False)
    current_event_id: Mapped[str] = mapped_column(String(512), nullable=False)
    instrument_id: Mapped[str] = mapped_column(String(512), nullable=False)
    risk_policy_id: Mapped[str] = mapped_column(String(128), nullable=False)
    risk_policy_configuration_digest: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    outcome: Mapped[str] = mapped_column(String(8), nullable=False)
    reason_codes_json: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class StrategyOrderCommandReceiptRow(ProductPersistenceBase):
    """Append-only scoped command-to-result mapping; not domain authority."""

    __tablename__ = "strategy_order_command_receipts"
    __table_args__ = (
        PrimaryKeyConstraint(
            "namespace",
            "command_idempotency_key",
            name="pk_strategy_order_command_receipts",
        ),
        UniqueConstraint(
            "namespace",
            "command_digest",
            name="uq_strategy_order_command_receipts_digest",
        ),
        CheckConstraint(
            "record_schema_version = 1",
            name="ck_strategy_order_command_receipts_version",
        ),
        CheckConstraint(
            "namespace IN ('evaluate_strategy_signal', "
            "'derive_order_intent', 'evaluate_pre_trade_risk')",
            name="ck_strategy_order_command_receipts_namespace",
        ),
        CheckConstraint(
            "result_kind IN ('strategy_signal', 'order_intent', "
            "'order_intent_no_action', 'pre_trade_risk_decision')",
            name="ck_strategy_order_command_receipts_result_kind",
        ),
        CheckConstraint(
            _DIGEST_CHECK.format("command_digest"),
            name="ck_strategy_order_command_receipts_command_digest",
        ),
        CheckConstraint(
            _DIGEST_CHECK.format("result_digest"),
            name="ck_strategy_order_command_receipts_result_digest",
        ),
        CheckConstraint(
            "(result_kind = 'order_intent_no_action' "
            "AND result_payload_json IS NOT NULL) OR "
            "(result_kind != 'order_intent_no_action' "
            "AND result_payload_json IS NULL)",
            name="ck_strategy_order_command_receipts_payload",
        ),
        Index(
            "ix_strategy_order_command_receipts_result",
            "result_kind",
            "result_id",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    namespace: Mapped[str] = mapped_column(String(64), nullable=False)
    command_idempotency_key: Mapped[str] = mapped_column(
        String(128), nullable=False
    )
    command_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    command_actor: Mapped[str] = mapped_column(String(256), nullable=False)
    result_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    result_id: Mapped[str] = mapped_column(String(96), nullable=False)
    result_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    result_payload_json: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


__all__ = [
    "OrderIntentRow",
    "PreTradeRiskDecisionRow",
    "StrategyOrderCommandReceiptRow",
    "StrategySignalRow",
]
