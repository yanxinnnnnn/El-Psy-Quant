"""Add durable M33 strategy, intent, risk, and command-receipt evidence.

Revision ID: 0010_strategy_order_risk
Revises: 0009_market_time_runtime
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_strategy_order_risk"
down_revision: str | Sequence[str] | None = "0009_market_time_runtime"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _digest(column: str) -> str:
    return f"length({column}) = 64 AND {column} NOT GLOB '*[^0-9a-f]*'"


def _append_only(table: str, prefix: str) -> None:
    op.execute(
        sa.text(
            f"CREATE TRIGGER trg_{prefix}_no_update BEFORE UPDATE ON {table} "
            "BEGIN SELECT RAISE(ABORT, 'M33 authority is append-only'); END"
        )
    )
    op.execute(
        sa.text(
            f"CREATE TRIGGER trg_{prefix}_no_delete BEFORE DELETE ON {table} "
            "BEGIN SELECT RAISE(ABORT, 'M33 authority cannot be deleted'); END"
        )
    )


def upgrade() -> None:
    """Create only Sprint 202 immutable storage and lookup structures."""
    op.create_table(
        "strategy_signals",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("signal_schema_version", sa.Integer(), nullable=False),
        sa.Column("signal_id", sa.String(length=80), nullable=False),
        sa.Column("signal_digest", sa.String(length=64), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("strategy_name", sa.String(length=128), nullable=False),
        sa.Column("strategy_version", sa.String(length=64), nullable=False),
        sa.Column("adapter_version", sa.String(length=64), nullable=False),
        sa.Column("parameters_digest", sa.String(length=64), nullable=False),
        sa.Column("calendar_id", sa.String(length=512), nullable=False),
        sa.Column("calendar_version", sa.Integer(), nullable=False),
        sa.Column("trading_session_id", sa.String(length=512), nullable=False),
        sa.Column("replay_id", sa.String(length=512), nullable=False),
        sa.Column("event_stream_digest", sa.String(length=64), nullable=False),
        sa.Column("cursor_position", sa.Integer(), nullable=False),
        sa.Column("signal_event_id", sa.String(length=512), nullable=False),
        sa.Column("instrument_id", sa.String(length=512), nullable=False),
        sa.Column("target_semantics", sa.String(length=64), nullable=False),
        sa.Column(
            "target_position_quantity", sa.String(length=128), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("signal_id", name="pk_strategy_signals"),
        sa.UniqueConstraint(
            "signal_digest", name="uq_strategy_signals_digest"
        ),
        sa.ForeignKeyConstraint(
            ("calendar_id",),
            ("trading_calendars.calendar_id",),
            name="fk_strategy_signals_calendar",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("trading_session_id",),
            ("trading_sessions.session_id",),
            name="fk_strategy_signals_session",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("replay_id",),
            ("market_data_replays.replay_id",),
            name="fk_strategy_signals_replay",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("signal_event_id",),
            ("market_data_events.event_id",),
            name="fk_strategy_signals_event",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "record_schema_version = 1 AND signal_schema_version = 1",
            name="ck_strategy_signals_versions",
        ),
        sa.CheckConstraint(
            _digest("signal_digest"), name="ck_strategy_signals_digest"
        ),
        sa.CheckConstraint(
            _digest("parameters_digest"),
            name="ck_strategy_signals_parameters_digest",
        ),
        sa.CheckConstraint(
            _digest("event_stream_digest"),
            name="ck_strategy_signals_stream_digest",
        ),
        sa.CheckConstraint(
            "cursor_position >= 1", name="ck_strategy_signals_cursor"
        ),
    )
    op.create_index(
        "ix_strategy_signals_created_id",
        "strategy_signals",
        ("created_at", "signal_id"),
    )
    op.create_index(
        "ix_strategy_signals_strategy_instrument",
        "strategy_signals",
        (
            "strategy_name",
            "strategy_version",
            "adapter_version",
            "instrument_id",
            "signal_id",
        ),
    )
    op.create_index(
        "ix_strategy_signals_market_anchor",
        "strategy_signals",
        (
            "calendar_id",
            "trading_session_id",
            "replay_id",
            "cursor_position",
            "signal_id",
        ),
    )

    op.create_table(
        "order_intents",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("intent_schema_version", sa.Integer(), nullable=False),
        sa.Column("intent_id", sa.String(length=80), nullable=False),
        sa.Column("intent_digest", sa.String(length=64), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("signal_id", sa.String(length=80), nullable=False),
        sa.Column("signal_digest", sa.String(length=64), nullable=False),
        sa.Column("account_id", sa.String(length=512), nullable=False),
        sa.Column("account_head_version", sa.Integer(), nullable=False),
        sa.Column(
            "account_head_event_id", sa.String(length=512), nullable=False
        ),
        sa.Column(
            "account_head_chain_digest", sa.String(length=64), nullable=False
        ),
        sa.Column("calendar_id", sa.String(length=512), nullable=False),
        sa.Column("trading_session_id", sa.String(length=512), nullable=False),
        sa.Column("replay_id", sa.String(length=512), nullable=False),
        sa.Column("event_stream_digest", sa.String(length=64), nullable=False),
        sa.Column("cursor_position", sa.Integer(), nullable=False),
        sa.Column("current_event_id", sa.String(length=512), nullable=False),
        sa.Column("instrument_id", sa.String(length=512), nullable=False),
        sa.Column("side", sa.String(length=8), nullable=False),
        sa.Column("requested_quantity", sa.String(length=128), nullable=False),
        sa.Column(
            "target_position_quantity", sa.String(length=128), nullable=False
        ),
        sa.Column(
            "current_position_quantity", sa.String(length=128), nullable=False
        ),
        sa.Column(
            "intent_policy_version", sa.String(length=128), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("intent_id", name="pk_order_intents"),
        sa.UniqueConstraint("intent_digest", name="uq_order_intents_digest"),
        sa.ForeignKeyConstraint(
            ("signal_id",),
            ("strategy_signals.signal_id",),
            name="fk_order_intents_signal",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("account_id",),
            ("paper_accounts.account_id",),
            name="fk_order_intents_account",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("account_head_event_id",),
            ("paper_account_events.event_id",),
            name="fk_order_intents_account_event",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("replay_id",),
            ("market_data_replays.replay_id",),
            name="fk_order_intents_replay",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("current_event_id",),
            ("market_data_events.event_id",),
            name="fk_order_intents_market_event",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "record_schema_version = 1 AND intent_schema_version = 1",
            name="ck_order_intents_versions",
        ),
        sa.CheckConstraint(
            _digest("intent_digest"), name="ck_order_intents_digest"
        ),
        sa.CheckConstraint(
            _digest("signal_digest"), name="ck_order_intents_signal_digest"
        ),
        sa.CheckConstraint(
            _digest("account_head_chain_digest"),
            name="ck_order_intents_account_digest",
        ),
        sa.CheckConstraint(
            _digest("event_stream_digest"),
            name="ck_order_intents_stream_digest",
        ),
        sa.CheckConstraint("side IN ('buy', 'sell')", name="ck_order_intents_side"),
    )
    op.create_index(
        "ix_order_intents_created_id",
        "order_intents",
        ("created_at", "intent_id"),
    )
    op.create_index(
        "ix_order_intents_signal_account",
        "order_intents",
        ("signal_id", "account_id", "intent_id"),
    )
    op.create_index(
        "ix_order_intents_market_anchor",
        "order_intents",
        ("replay_id", "cursor_position", "instrument_id", "intent_id"),
    )

    op.create_table(
        "pre_trade_risk_decisions",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("decision_schema_version", sa.Integer(), nullable=False),
        sa.Column("decision_id", sa.String(length=96), nullable=False),
        sa.Column("decision_digest", sa.String(length=64), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("snapshot_id", sa.String(length=96), nullable=False),
        sa.Column("snapshot_digest", sa.String(length=64), nullable=False),
        sa.Column("intent_id", sa.String(length=80), nullable=False),
        sa.Column("intent_digest", sa.String(length=64), nullable=False),
        sa.Column("account_id", sa.String(length=512), nullable=False),
        sa.Column("account_head_version", sa.Integer(), nullable=False),
        sa.Column(
            "account_head_event_id", sa.String(length=512), nullable=False
        ),
        sa.Column(
            "account_head_chain_digest", sa.String(length=64), nullable=False
        ),
        sa.Column("calendar_id", sa.String(length=512), nullable=False),
        sa.Column("trading_session_id", sa.String(length=512), nullable=False),
        sa.Column("replay_id", sa.String(length=512), nullable=False),
        sa.Column("event_stream_digest", sa.String(length=64), nullable=False),
        sa.Column("cursor_position", sa.Integer(), nullable=False),
        sa.Column("current_event_id", sa.String(length=512), nullable=False),
        sa.Column("instrument_id", sa.String(length=512), nullable=False),
        sa.Column("risk_policy_id", sa.String(length=128), nullable=False),
        sa.Column(
            "risk_policy_configuration_digest",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column("outcome", sa.String(length=8), nullable=False),
        sa.Column("reason_codes_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint(
            "decision_id", name="pk_pre_trade_risk_decisions"
        ),
        sa.UniqueConstraint(
            "decision_digest", name="uq_pre_trade_risk_decisions_digest"
        ),
        sa.UniqueConstraint(
            "snapshot_id", name="uq_pre_trade_risk_decisions_snapshot_id"
        ),
        sa.UniqueConstraint(
            "snapshot_digest",
            name="uq_pre_trade_risk_decisions_snapshot_digest",
        ),
        sa.ForeignKeyConstraint(
            ("intent_id",),
            ("order_intents.intent_id",),
            name="fk_pre_trade_risk_decisions_intent",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("account_id",),
            ("paper_accounts.account_id",),
            name="fk_pre_trade_risk_decisions_account",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("replay_id",),
            ("market_data_replays.replay_id",),
            name="fk_pre_trade_risk_decisions_replay",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "record_schema_version = 1 AND decision_schema_version = 1",
            name="ck_pre_trade_risk_decisions_versions",
        ),
        sa.CheckConstraint(
            _digest("decision_digest"),
            name="ck_pre_trade_risk_decisions_digest",
        ),
        sa.CheckConstraint(
            _digest("snapshot_digest"),
            name="ck_pre_trade_risk_decisions_snapshot_digest",
        ),
        sa.CheckConstraint(
            _digest("intent_digest"),
            name="ck_pre_trade_risk_decisions_intent_digest",
        ),
        sa.CheckConstraint(
            _digest("risk_policy_configuration_digest"),
            name="ck_pre_trade_risk_decisions_policy_digest",
        ),
        sa.CheckConstraint(
            "outcome IN ('allow', 'reject')",
            name="ck_pre_trade_risk_decisions_outcome",
        ),
    )
    op.create_index(
        "ix_pre_trade_risk_decisions_created_id",
        "pre_trade_risk_decisions",
        ("created_at", "decision_id"),
    )
    op.create_index(
        "ix_pre_trade_risk_decisions_intent_outcome",
        "pre_trade_risk_decisions",
        ("intent_id", "outcome", "decision_id"),
    )
    op.create_index(
        "ix_pre_trade_risk_decisions_account_market",
        "pre_trade_risk_decisions",
        ("account_id", "replay_id", "cursor_position", "decision_id"),
    )

    op.create_table(
        "strategy_order_command_receipts",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("namespace", sa.String(length=64), nullable=False),
        sa.Column(
            "command_idempotency_key", sa.String(length=128), nullable=False
        ),
        sa.Column("command_digest", sa.String(length=64), nullable=False),
        sa.Column("command_actor", sa.String(length=256), nullable=False),
        sa.Column("result_kind", sa.String(length=64), nullable=False),
        sa.Column("result_id", sa.String(length=96), nullable=False),
        sa.Column("result_digest", sa.String(length=64), nullable=False),
        sa.Column("result_payload_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint(
            "namespace",
            "command_idempotency_key",
            name="pk_strategy_order_command_receipts",
        ),
        sa.UniqueConstraint(
            "namespace",
            "command_digest",
            name="uq_strategy_order_command_receipts_digest",
        ),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_strategy_order_command_receipts_version",
        ),
        sa.CheckConstraint(
            "namespace IN ('evaluate_strategy_signal', "
            "'derive_order_intent', 'evaluate_pre_trade_risk')",
            name="ck_strategy_order_command_receipts_namespace",
        ),
        sa.CheckConstraint(
            "result_kind IN ('strategy_signal', 'order_intent', "
            "'order_intent_no_action', 'pre_trade_risk_decision')",
            name="ck_strategy_order_command_receipts_result_kind",
        ),
        sa.CheckConstraint(
            _digest("command_digest"),
            name="ck_strategy_order_command_receipts_command_digest",
        ),
        sa.CheckConstraint(
            _digest("result_digest"),
            name="ck_strategy_order_command_receipts_result_digest",
        ),
        sa.CheckConstraint(
            "(result_kind = 'order_intent_no_action' "
            "AND result_payload_json IS NOT NULL) OR "
            "(result_kind != 'order_intent_no_action' "
            "AND result_payload_json IS NULL)",
            name="ck_strategy_order_command_receipts_payload",
        ),
    )
    op.create_index(
        "ix_strategy_order_command_receipts_result",
        "strategy_order_command_receipts",
        ("result_kind", "result_id"),
    )

    for table, prefix in (
        ("strategy_signals", "strategy_signals"),
        ("order_intents", "order_intents"),
        ("pre_trade_risk_decisions", "pre_trade_risk_decisions"),
        ("strategy_order_command_receipts", "strategy_order_command_receipts"),
    ):
        _append_only(table, prefix)


def downgrade() -> None:
    """Remove only Sprint 202 durable M33 objects."""
    op.drop_table("strategy_order_command_receipts")
    op.drop_table("pre_trade_risk_decisions")
    op.drop_table("order_intents")
    op.drop_table("strategy_signals")
