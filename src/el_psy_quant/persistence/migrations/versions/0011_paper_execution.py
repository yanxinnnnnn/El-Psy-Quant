"""Add durable M34 paper-execution authority.

Revision ID: 0011_paper_execution
Revises: 0010_strategy_order_risk
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_paper_execution"
down_revision: str | None = "0010_strategy_order_risk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _append_only(table: str, prefix: str) -> None:
    op.execute(
        f"CREATE TRIGGER trg_{prefix}_no_update BEFORE UPDATE ON {table} "
        "BEGIN SELECT RAISE(ABORT, 'append-only authority'); END"
    )
    op.execute(
        f"CREATE TRIGGER trg_{prefix}_no_delete BEFORE DELETE ON {table} "
        "BEGIN SELECT RAISE(ABORT, 'append-only authority'); END"
    )


def _digest(column: str) -> str:
    return f"length({column}) = 64 AND {column} NOT GLOB '*[^0-9a-f]*'"


def _expand_m31_execution_vocabulary() -> None:
    """Permit only the S210 domain-owned execution posting vocabulary."""
    context = op.get_context()
    connection = op.get_bind()
    with context.autocommit_block():
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        try:
            with op.batch_alter_table(
                "paper_account_events", recreate="always"
            ) as batch:
                batch.drop_constraint(
                    "ck_paper_account_events_event_type", type_="check"
                )
                batch.create_check_constraint(
                    "ck_paper_account_events_event_type",
                    "event_type IN ('account_created', 'cash_movement_posted', "
                    "'position_adjustment_posted', 'portfolio_review_evidence_linked', "
                    "'account_frozen', 'account_reactivated', 'account_closed', "
                    "'execution_fill_posted')",
                )
            with op.batch_alter_table(
                "paper_cash_ledger_entries", recreate="always"
            ) as batch:
                batch.drop_constraint(
                    "ck_paper_cash_entries_movement_type", type_="check"
                )
                batch.create_check_constraint(
                    "ck_paper_cash_entries_movement_type",
                    "movement_type IN ('initial_cash', 'deposit', 'withdrawal', "
                    "'manual_adjustment', 'fee', 'commission', 'tax', "
                    "'execution_settlement')",
                )
            with op.batch_alter_table(
                "paper_position_ledger_entries", recreate="always"
            ) as batch:
                batch.drop_constraint(
                    "ck_paper_position_entries_adjustment_category", type_="check"
                )
                batch.create_check_constraint(
                    "ck_paper_position_entries_adjustment_category",
                    "adjustment_category IN ('opening_balance', 'manual_correction', "
                    "'corporate_action', 'other', 'execution_fill')",
                )
            for table, prefix in (
                ("paper_account_events", "paper_account_events"),
                ("paper_cash_ledger_entries", "paper_cash_ledger_entries"),
                ("paper_position_ledger_entries", "paper_position_ledger_entries"),
            ):
                op.execute(
                    f"CREATE TRIGGER IF NOT EXISTS trg_{prefix}_no_update "
                    f"BEFORE UPDATE ON {table} "
                    "BEGIN SELECT RAISE(ABORT, 'append-only authority'); END"
                )
                op.execute(
                    f"CREATE TRIGGER IF NOT EXISTS trg_{prefix}_no_delete "
                    f"BEFORE DELETE ON {table} "
                    "BEGIN SELECT RAISE(ABORT, 'append-only authority'); END"
                )
        finally:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            if connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() != 1:
                raise RuntimeError("failed to restore SQLite foreign-key enforcement")
        if connection.exec_driver_sql("PRAGMA foreign_key_check").first() is not None:
            raise RuntimeError("M31 vocabulary migration broke foreign-key authority")


def upgrade() -> None:
    if not op.get_context().as_sql:
        _expand_m31_execution_vocabulary()
    op.create_table(
        "paper_execution_orders",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("order_schema_version", sa.Integer(), nullable=False),
        sa.Column("execution_order_id", sa.String(96), nullable=False),
        sa.Column("execution_order_digest", sa.String(64), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("intent_id", sa.String(80), nullable=False),
        sa.Column("intent_digest", sa.String(64), nullable=False),
        sa.Column("risk_decision_id", sa.String(96), nullable=False),
        sa.Column("risk_decision_digest", sa.String(64), nullable=False),
        sa.Column("risk_snapshot_id", sa.String(96), nullable=False),
        sa.Column("risk_snapshot_digest", sa.String(64), nullable=False),
        sa.Column("account_id", sa.String(512), nullable=False),
        sa.Column("account_handoff_version", sa.Integer(), nullable=False),
        sa.Column("account_handoff_event_id", sa.String(512), nullable=False),
        sa.Column("account_handoff_chain_digest", sa.String(64), nullable=False),
        sa.Column("calendar_id", sa.String(512), nullable=False),
        sa.Column("calendar_version", sa.Integer(), nullable=False),
        sa.Column("trading_session_id", sa.String(512), nullable=False),
        sa.Column("replay_id", sa.String(512), nullable=False),
        sa.Column("event_stream_digest", sa.String(64), nullable=False),
        sa.Column("handoff_cursor_position", sa.Integer(), nullable=False),
        sa.Column("handoff_event_id", sa.String(512), nullable=False),
        sa.Column("instrument_id", sa.String(512), nullable=False),
        sa.Column("side", sa.String(8), nullable=False),
        sa.Column("requested_quantity", sa.String(128), nullable=False),
        sa.Column("policy_id", sa.String(128), nullable=False),
        sa.Column("policy_configuration_digest", sa.String(64), nullable=False),
        sa.Column("policy_reference_digest", sa.String(64), nullable=False),
        sa.Column("origin_command_digest", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("execution_order_id", name="pk_paper_execution_orders"),
        sa.UniqueConstraint(
            "execution_order_digest", name="uq_paper_execution_orders_digest"
        ),
        sa.ForeignKeyConstraint(
            ("intent_id",),
            ("order_intents.intent_id",),
            name="fk_paper_execution_orders_intent",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("risk_decision_id",),
            ("pre_trade_risk_decisions.decision_id",),
            name="fk_paper_execution_orders_decision",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("account_id",),
            ("paper_accounts.account_id",),
            name="fk_paper_execution_orders_account",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("account_handoff_event_id",),
            ("paper_account_events.event_id",),
            name="fk_paper_execution_orders_account_event",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("calendar_id",),
            ("trading_calendars.calendar_id",),
            name="fk_paper_execution_orders_calendar",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("trading_session_id",),
            ("trading_sessions.session_id",),
            name="fk_paper_execution_orders_session",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("replay_id",),
            ("market_data_replays.replay_id",),
            name="fk_paper_execution_orders_replay",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("handoff_event_id",),
            ("market_data_events.event_id",),
            name="fk_paper_execution_orders_market_event",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "record_schema_version = 1 AND order_schema_version = 1",
            name="ck_paper_execution_orders_versions",
        ),
        sa.CheckConstraint(
            _digest("execution_order_digest"), name="ck_paper_execution_orders_digest"
        ),
        sa.CheckConstraint(
            "side IN ('buy', 'sell')", name="ck_paper_execution_orders_side"
        ),
    )
    op.create_index(
        "ix_paper_execution_orders_created_id",
        "paper_execution_orders",
        ("created_at", "execution_order_id"),
    )
    op.create_index(
        "ix_paper_execution_orders_working_tuple",
        "paper_execution_orders",
        ("account_id", "replay_id", "trading_session_id", "execution_order_id"),
    )
    op.create_index(
        "ix_paper_execution_orders_intent_policy",
        "paper_execution_orders",
        ("intent_id", "policy_reference_digest"),
    )

    op.create_table(
        "paper_execution_attempts",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("attempt_schema_version", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.String(96), nullable=False),
        sa.Column("attempt_digest", sa.String(64), nullable=False),
        sa.Column("execution_order_id", sa.String(96), nullable=False),
        sa.Column("execution_version_before", sa.Integer(), nullable=False),
        sa.Column("execution_version_after", sa.Integer(), nullable=False),
        sa.Column("attempt_result", sa.String(32), nullable=False),
        sa.Column("consumed_event_id", sa.String(512), nullable=True),
        sa.Column("consumed_event_position", sa.Integer(), nullable=True),
        sa.Column("pre_cursor_position", sa.Integer(), nullable=False),
        sa.Column("pre_cursor_last_event_id", sa.String(512), nullable=True),
        sa.Column("post_cursor_position", sa.Integer(), nullable=False),
        sa.Column("post_cursor_last_event_id", sa.String(512), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("attempt_id", name="pk_paper_execution_attempts"),
        sa.UniqueConstraint(
            "attempt_digest", name="uq_paper_execution_attempts_digest"
        ),
        sa.UniqueConstraint(
            "execution_order_id",
            "execution_version_before",
            name="uq_paper_execution_attempts_version_before",
        ),
        sa.UniqueConstraint(
            "execution_order_id",
            "execution_version_after",
            name="uq_paper_execution_attempts_version_after",
        ),
        sa.ForeignKeyConstraint(
            ("execution_order_id",),
            ("paper_execution_orders.execution_order_id",),
            name="fk_paper_execution_attempts_order",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("consumed_event_id",),
            ("market_data_events.event_id",),
            name="fk_paper_execution_attempts_event",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "record_schema_version = 1 AND attempt_schema_version = 1",
            name="ck_paper_execution_attempts_versions",
        ),
        sa.CheckConstraint(
            "execution_version_before >= 0 AND execution_version_after = execution_version_before + 1",
            name="ck_paper_execution_attempts_sequence",
        ),
        sa.CheckConstraint(
            "attempt_result IN ('no_fill', 'fill', 'risk_rejected', 'boundary_rejected')",
            name="ck_paper_execution_attempts_result",
        ),
    )
    op.create_index(
        "ix_paper_execution_attempts_order_version",
        "paper_execution_attempts",
        ("execution_order_id", "execution_version_before"),
    )
    op.create_index(
        "ix_paper_execution_attempts_event",
        "paper_execution_attempts",
        ("execution_order_id", "consumed_event_position"),
    )

    op.create_table(
        "paper_execution_fills",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("fill_schema_version", sa.Integer(), nullable=False),
        sa.Column("fill_id", sa.String(96), nullable=False),
        sa.Column("fill_digest", sa.String(64), nullable=False),
        sa.Column("execution_order_id", sa.String(96), nullable=False),
        sa.Column("attempt_id", sa.String(96), nullable=False),
        sa.Column("consumed_event_id", sa.String(512), nullable=False),
        sa.Column("consumed_event_position", sa.Integer(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("fill_id", name="pk_paper_execution_fills"),
        sa.UniqueConstraint("fill_digest", name="uq_paper_execution_fills_digest"),
        sa.UniqueConstraint("attempt_id", name="uq_paper_execution_fills_attempt"),
        sa.UniqueConstraint(
            "execution_order_id",
            "consumed_event_position",
            name="uq_paper_execution_fills_order_event_position",
        ),
        sa.ForeignKeyConstraint(
            ("execution_order_id",),
            ("paper_execution_orders.execution_order_id",),
            name="fk_paper_execution_fills_order",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("attempt_id",),
            ("paper_execution_attempts.attempt_id",),
            name="fk_paper_execution_fills_attempt",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("consumed_event_id",),
            ("market_data_events.event_id",),
            name="fk_paper_execution_fills_event",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "record_schema_version = 1 AND fill_schema_version = 1",
            name="ck_paper_execution_fills_versions",
        ),
    )
    op.create_index(
        "ix_paper_execution_fills_order_created",
        "paper_execution_fills",
        ("execution_order_id", "created_at", "fill_id"),
    )
    op.create_index(
        "ix_paper_execution_fills_event",
        "paper_execution_fills",
        ("execution_order_id", "consumed_event_id"),
    )

    op.create_table(
        "paper_execution_settlement_links",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("settlement_link_schema_version", sa.Integer(), nullable=False),
        sa.Column("settlement_link_id", sa.String(96), nullable=False),
        sa.Column("settlement_link_digest", sa.String(64), nullable=False),
        sa.Column("settlement_link_evidence_digest", sa.String(64), nullable=False),
        sa.Column("execution_order_id", sa.String(96), nullable=False),
        sa.Column("attempt_id", sa.String(96), nullable=False),
        sa.Column("fill_id", sa.String(96), nullable=False),
        sa.Column("account_id", sa.String(512), nullable=False),
        sa.Column("account_event_id", sa.String(512), nullable=False),
        sa.Column("cash_entry_id", sa.String(512), nullable=False),
        sa.Column("position_entry_id", sa.String(512), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint(
            "settlement_link_id", name="pk_paper_execution_settlement_links"
        ),
        sa.UniqueConstraint(
            "settlement_link_digest", name="uq_paper_execution_settlement_links_digest"
        ),
        sa.UniqueConstraint(
            "settlement_link_evidence_digest",
            name="uq_paper_execution_settlement_links_evidence",
        ),
        sa.UniqueConstraint("fill_id", name="uq_paper_execution_settlement_links_fill"),
        sa.UniqueConstraint(
            "account_event_id", name="uq_paper_execution_settlement_links_event"
        ),
        sa.ForeignKeyConstraint(
            ("execution_order_id",),
            ("paper_execution_orders.execution_order_id",),
            name="fk_paper_execution_settlement_links_order",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("attempt_id",),
            ("paper_execution_attempts.attempt_id",),
            name="fk_paper_execution_settlement_links_attempt",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("fill_id",),
            ("paper_execution_fills.fill_id",),
            name="fk_paper_execution_settlement_links_fill",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("account_event_id",),
            ("paper_account_events.event_id",),
            name="fk_paper_execution_settlement_links_account_event",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("cash_entry_id",),
            ("paper_cash_ledger_entries.cash_entry_id",),
            name="fk_paper_execution_settlement_links_cash",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("position_entry_id",),
            ("paper_position_ledger_entries.position_entry_id",),
            name="fk_paper_execution_settlement_links_position",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "record_schema_version = 1 AND settlement_link_schema_version = 1",
            name="ck_paper_execution_settlement_links_versions",
        ),
    )
    op.create_index(
        "ix_paper_execution_settlement_links_order",
        "paper_execution_settlement_links",
        ("execution_order_id", "attempt_id"),
    )

    op.create_table(
        "paper_execution_command_receipts",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("namespace", sa.String(64), nullable=False),
        sa.Column("command_idempotency_key", sa.String(128), nullable=False),
        sa.Column("command_digest", sa.String(64), nullable=False),
        sa.Column("command_actor", sa.String(256), nullable=False),
        sa.Column("result_kind", sa.String(64), nullable=False),
        sa.Column("execution_order_id", sa.String(96), nullable=False),
        sa.Column("execution_order_digest", sa.String(64), nullable=False),
        sa.Column("attempt_id", sa.String(96), nullable=True),
        sa.Column("attempt_digest", sa.String(64), nullable=True),
        sa.Column("fill_id", sa.String(96), nullable=True),
        sa.Column("fill_digest", sa.String(64), nullable=True),
        sa.Column("settlement_link_id", sa.String(96), nullable=True),
        sa.Column("settlement_link_evidence_digest", sa.String(64), nullable=True),
        sa.Column("account_event_id", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint(
            "namespace",
            "command_idempotency_key",
            name="pk_paper_execution_command_receipts",
        ),
        sa.UniqueConstraint(
            "namespace",
            "command_digest",
            name="uq_paper_execution_command_receipts_digest",
        ),
        sa.ForeignKeyConstraint(
            ("execution_order_id",),
            ("paper_execution_orders.execution_order_id",),
            name="fk_paper_execution_receipts_order",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("attempt_id",),
            ("paper_execution_attempts.attempt_id",),
            name="fk_paper_execution_receipts_attempt",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("fill_id",),
            ("paper_execution_fills.fill_id",),
            name="fk_paper_execution_receipts_fill",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("settlement_link_id",),
            ("paper_execution_settlement_links.settlement_link_id",),
            name="fk_paper_execution_receipts_link",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("account_event_id",),
            ("paper_account_events.event_id",),
            name="fk_paper_execution_receipts_event",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "record_schema_version = 1", name="ck_paper_execution_receipts_version"
        ),
        sa.CheckConstraint(
            "namespace IN ('create_paper_execution_order', 'step_paper_execution_order')",
            name="ck_paper_execution_receipts_namespace",
        ),
        sa.CheckConstraint(
            "result_kind IN ('paper_execution_order', 'paper_execution_step')",
            name="ck_paper_execution_receipts_result_kind",
        ),
        sa.CheckConstraint(
            "(result_kind = 'paper_execution_order' AND attempt_id IS NULL AND fill_id IS NULL AND settlement_link_id IS NULL AND account_event_id IS NULL) OR (result_kind = 'paper_execution_step' AND attempt_id IS NOT NULL AND ((fill_id IS NULL AND settlement_link_id IS NULL AND account_event_id IS NULL) OR (fill_id IS NOT NULL AND settlement_link_id IS NOT NULL AND account_event_id IS NOT NULL)))",
            name="ck_paper_execution_receipts_result_refs",
        ),
    )
    op.create_index(
        "ix_paper_execution_receipts_result",
        "paper_execution_command_receipts",
        ("result_kind", "execution_order_id", "attempt_id"),
    )

    for table, prefix in (
        ("paper_execution_orders", "paper_execution_orders"),
        ("paper_execution_attempts", "paper_execution_attempts"),
        ("paper_execution_fills", "paper_execution_fills"),
        ("paper_execution_settlement_links", "paper_execution_settlement_links"),
        ("paper_execution_command_receipts", "paper_execution_command_receipts"),
    ):
        _append_only(table, prefix)


def downgrade() -> None:
    op.drop_table("paper_execution_command_receipts")
    op.drop_table("paper_execution_settlement_links")
    op.drop_table("paper_execution_fills")
    op.drop_table("paper_execution_attempts")
    op.drop_table("paper_execution_orders")
