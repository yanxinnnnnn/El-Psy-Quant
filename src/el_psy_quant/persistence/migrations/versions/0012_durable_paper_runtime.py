"""Durable M35 Paper Runtime contracts and persistence foundation.

Revision ID: 0012_durable_paper_runtime
Revises: 0011_paper_execution
"""

from alembic import op
import sqlalchemy as sa

revision: str = "0012_durable_paper_runtime"
down_revision: str | None = "0011_paper_execution"
branch_labels: str | None = None
depends_on: str | None = None


def _digest(column: str) -> str:
    return f"length({column}) = 64 AND {column} NOT GLOB '*[^0-9a-f]*'"


def _append_only(table: str, prefix: str) -> None:
    op.execute(
        f"CREATE TRIGGER trg_{prefix}_no_update BEFORE UPDATE ON {table} BEGIN SELECT RAISE(ABORT, '{table} is append-only'); END"
    )
    op.execute(
        f"CREATE TRIGGER trg_{prefix}_no_delete BEFORE DELETE ON {table} BEGIN SELECT RAISE(ABORT, '{table} is append-only'); END"
    )


def upgrade() -> None:
    op.create_table(
        "paper_runtimes",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("runtime_schema_version", sa.Integer(), nullable=False),
        sa.Column("runtime_id", sa.String(96), nullable=False),
        sa.Column("runtime_binding_digest", sa.String(64), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("execution_order_id", sa.String(96), nullable=False),
        sa.Column("execution_order_digest", sa.String(64), nullable=False),
        sa.Column("account_id", sa.String(512), nullable=False),
        sa.Column("replay_id", sa.String(512), nullable=False),
        sa.Column("trading_session_id", sa.String(512), nullable=False),
        sa.Column("logical_actor", sa.String(256), nullable=False),
        sa.Column("runtime_policy_id", sa.String(128), nullable=False),
        sa.Column("runtime_policy_version", sa.Integer(), nullable=False),
        sa.Column("desired_state", sa.String(16), nullable=False),
        sa.Column("observed_state", sa.String(16), nullable=False),
        sa.Column("owner_id", sa.String(256), nullable=True),
        sa.Column("fencing_token", sa.Integer(), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("row_version", sa.Integer(), nullable=False),
        sa.Column("block_reason_code", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("runtime_id", name="pk_paper_runtimes"),
        sa.UniqueConstraint("runtime_binding_digest", name="uq_paper_runtimes_binding"),
        sa.UniqueConstraint("execution_order_id", name="uq_paper_runtimes_order"),
        sa.ForeignKeyConstraint(
            ("execution_order_id",),
            ("paper_execution_orders.execution_order_id",),
            name="fk_paper_runtimes_order",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("account_id",),
            ("paper_accounts.account_id",),
            name="fk_paper_runtimes_account",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("replay_id",),
            ("market_data_replays.replay_id",),
            name="fk_paper_runtimes_replay",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("trading_session_id",),
            ("trading_sessions.session_id",),
            name="fk_paper_runtimes_session",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "record_schema_version = 1 AND runtime_schema_version = 1",
            name="ck_paper_runtimes_versions",
        ),
        sa.CheckConstraint(
            _digest("runtime_binding_digest"), name="ck_paper_runtimes_binding_digest"
        ),
        sa.CheckConstraint(
            _digest("execution_order_digest"), name="ck_paper_runtimes_order_digest"
        ),
        sa.CheckConstraint(
            "runtime_policy_version >= 0 AND fencing_token >= 0 AND row_version >= 0",
            name="ck_paper_runtimes_nonnegative",
        ),
        sa.CheckConstraint(
            "desired_state IN ('running','stopped')", name="ck_paper_runtimes_desired"
        ),
        sa.CheckConstraint(
            "observed_state IN ('ready','running','stopped','completed','blocked')",
            name="ck_paper_runtimes_observed",
        ),
        sa.CheckConstraint(
            "(owner_id IS NULL AND claimed_at IS NULL AND heartbeat_at IS NULL AND lease_expires_at IS NULL) OR (owner_id IS NOT NULL AND claimed_at IS NOT NULL AND heartbeat_at IS NOT NULL AND lease_expires_at IS NOT NULL)",
            name="ck_paper_runtimes_owner_group",
        ),
        sa.CheckConstraint(
            "(observed_state = 'blocked' AND block_reason_code IS NOT NULL AND length(block_reason_code) > 0) OR (observed_state <> 'blocked' AND block_reason_code IS NULL)",
            name="ck_paper_runtimes_block_reason",
        ),
    )
    op.create_index(
        "ix_paper_runtimes_binding",
        "paper_runtimes",
        ["account_id", "replay_id", "trading_session_id"],
    )
    op.create_index(
        "ix_paper_runtimes_state",
        "paper_runtimes",
        ["desired_state", "observed_state", "updated_at"],
    )
    op.execute(
        "CREATE TRIGGER trg_paper_runtimes_no_delete BEFORE DELETE ON paper_runtimes BEGIN SELECT RAISE(ABORT, 'paper_runtimes cannot be deleted'); END"
    )
    immutable = (
        "record_schema_version",
        "runtime_schema_version",
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
    condition = " OR ".join(f"NEW.{column} IS NOT OLD.{column}" for column in immutable)
    op.execute(
        f"CREATE TRIGGER trg_paper_runtimes_immutable_binding BEFORE UPDATE ON paper_runtimes WHEN {condition} BEGIN SELECT RAISE(ABORT, 'paper_runtimes immutable binding cannot change'); END"
    )

    op.create_table(
        "paper_runtime_work",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("work_schema_version", sa.Integer(), nullable=False),
        sa.Column("work_id", sa.String(96), nullable=False),
        sa.Column("work_digest", sa.String(64), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("runtime_id", sa.String(96), nullable=False),
        sa.Column("execution_order_id", sa.String(96), nullable=False),
        sa.Column("execution_order_digest", sa.String(64), nullable=False),
        sa.Column("expected_execution_version", sa.Integer(), nullable=False),
        sa.Column("m34_step_idempotency_key", sa.String(128), nullable=False),
        sa.Column("m34_step_actor", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("work_id", name="pk_paper_runtime_work"),
        sa.UniqueConstraint("work_digest", name="uq_paper_runtime_work_digest"),
        sa.UniqueConstraint(
            "m34_step_idempotency_key", name="uq_paper_runtime_work_step_key"
        ),
        sa.UniqueConstraint(
            "runtime_id",
            "expected_execution_version",
            name="uq_paper_runtime_work_version",
        ),
        sa.ForeignKeyConstraint(
            ("runtime_id",),
            ("paper_runtimes.runtime_id",),
            name="fk_paper_runtime_work_runtime",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("execution_order_id",),
            ("paper_execution_orders.execution_order_id",),
            name="fk_paper_runtime_work_order",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "record_schema_version = 1 AND work_schema_version = 1",
            name="ck_paper_runtime_work_versions",
        ),
        sa.CheckConstraint(_digest("work_digest"), name="ck_paper_runtime_work_digest"),
        sa.CheckConstraint(
            _digest("execution_order_digest"), name="ck_paper_runtime_work_order_digest"
        ),
        sa.CheckConstraint(
            "expected_execution_version >= 0",
            name="ck_paper_runtime_work_execution_version",
        ),
    )
    op.create_index(
        "ix_paper_runtime_work_runtime",
        "paper_runtime_work",
        ["runtime_id", "expected_execution_version"],
    )

    op.create_table(
        "paper_runtime_checkpoints",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("checkpoint_schema_version", sa.Integer(), nullable=False),
        sa.Column("checkpoint_id", sa.String(96), nullable=False),
        sa.Column("checkpoint_digest", sa.String(64), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("runtime_id", sa.String(96), nullable=False),
        sa.Column("work_id", sa.String(96), nullable=False),
        sa.Column("execution_order_id", sa.String(96), nullable=False),
        sa.Column("execution_order_digest", sa.String(64), nullable=False),
        sa.Column("observed_execution_version", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.String(96), nullable=False),
        sa.Column("attempt_digest", sa.String(64), nullable=False),
        sa.Column("fill_id", sa.String(96), nullable=True),
        sa.Column("fill_digest", sa.String(64), nullable=True),
        sa.Column("settlement_link_id", sa.String(96), nullable=True),
        sa.Column("settlement_link_evidence_digest", sa.String(64), nullable=True),
        sa.Column("account_event_id", sa.String(512), nullable=True),
        sa.Column("replay_id", sa.String(512), nullable=False),
        sa.Column("event_stream_digest", sa.String(64), nullable=False),
        sa.Column("post_cursor_position", sa.Integer(), nullable=False),
        sa.Column("post_cursor_last_event_id", sa.String(512), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("checkpoint_id", name="pk_paper_runtime_checkpoints"),
        sa.UniqueConstraint(
            "checkpoint_digest", name="uq_paper_runtime_checkpoints_digest"
        ),
        sa.UniqueConstraint("work_id", name="uq_paper_runtime_checkpoints_work"),
        sa.UniqueConstraint(
            "runtime_id",
            "observed_execution_version",
            name="uq_paper_runtime_checkpoints_version",
        ),
        sa.ForeignKeyConstraint(
            ("runtime_id",),
            ("paper_runtimes.runtime_id",),
            name="fk_paper_runtime_checkpoints_runtime",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("work_id",),
            ("paper_runtime_work.work_id",),
            name="fk_paper_runtime_checkpoints_work",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("execution_order_id",),
            ("paper_execution_orders.execution_order_id",),
            name="fk_paper_runtime_checkpoints_order",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("attempt_id",),
            ("paper_execution_attempts.attempt_id",),
            name="fk_paper_runtime_checkpoints_attempt",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("fill_id",),
            ("paper_execution_fills.fill_id",),
            name="fk_paper_runtime_checkpoints_fill",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("settlement_link_id",),
            ("paper_execution_settlement_links.settlement_link_id",),
            name="fk_paper_runtime_checkpoints_link",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("account_event_id",),
            ("paper_account_events.event_id",),
            name="fk_paper_runtime_checkpoints_account_event",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("replay_id",),
            ("market_data_replays.replay_id",),
            name="fk_paper_runtime_checkpoints_replay",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "record_schema_version = 1 AND checkpoint_schema_version = 1",
            name="ck_paper_runtime_checkpoints_versions",
        ),
        sa.CheckConstraint(
            _digest("checkpoint_digest"), name="ck_paper_runtime_checkpoints_digest"
        ),
        sa.CheckConstraint(
            _digest("execution_order_digest"),
            name="ck_paper_runtime_checkpoints_order_digest",
        ),
        sa.CheckConstraint(
            _digest("attempt_digest"),
            name="ck_paper_runtime_checkpoints_attempt_digest",
        ),
        sa.CheckConstraint(
            _digest("event_stream_digest"),
            name="ck_paper_runtime_checkpoints_stream_digest",
        ),
        sa.CheckConstraint(
            "observed_execution_version >= 1 AND post_cursor_position >= 0",
            name="ck_paper_runtime_checkpoints_nonnegative",
        ),
        sa.CheckConstraint(
            "(fill_id IS NULL AND fill_digest IS NULL AND settlement_link_id IS NULL AND settlement_link_evidence_digest IS NULL AND account_event_id IS NULL) OR (fill_id IS NOT NULL AND fill_digest IS NOT NULL AND settlement_link_id IS NOT NULL AND settlement_link_evidence_digest IS NOT NULL AND account_event_id IS NOT NULL)",
            name="ck_paper_runtime_checkpoints_optional_group",
        ),
        sa.CheckConstraint(
            "fill_digest IS NULL OR (" + _digest("fill_digest") + ")",
            name="ck_paper_runtime_checkpoints_fill_digest",
        ),
        sa.CheckConstraint(
            "settlement_link_evidence_digest IS NULL OR ("
            + _digest("settlement_link_evidence_digest")
            + ")",
            name="ck_paper_runtime_checkpoints_link_digest",
        ),
    )
    op.create_index(
        "ix_paper_runtime_checkpoints_runtime",
        "paper_runtime_checkpoints",
        ["runtime_id", "observed_execution_version"],
    )

    op.create_table(
        "paper_runtime_events",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("event_schema_version", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(96), nullable=False),
        sa.Column("event_digest", sa.String(64), nullable=False),
        sa.Column("runtime_id", sa.String(96), nullable=False),
        sa.Column("event_sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("resulting_runtime_version", sa.Integer(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id", name="pk_paper_runtime_events"),
        sa.UniqueConstraint("event_digest", name="uq_paper_runtime_events_digest"),
        sa.UniqueConstraint(
            "runtime_id", "event_sequence", name="uq_paper_runtime_events_sequence"
        ),
        sa.ForeignKeyConstraint(
            ("runtime_id",),
            ("paper_runtimes.runtime_id",),
            name="fk_paper_runtime_events_runtime",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "record_schema_version = 1 AND event_schema_version = 1",
            name="ck_paper_runtime_events_versions",
        ),
        sa.CheckConstraint(
            _digest("event_digest"), name="ck_paper_runtime_events_digest"
        ),
        sa.CheckConstraint(
            "event_sequence >= 0 AND resulting_runtime_version >= 0",
            name="ck_paper_runtime_events_nonnegative",
        ),
        sa.CheckConstraint(
            "event_type IN ('runtime_created','start_requested','stop_requested','resume_requested','recover_requested','claim_acquired','claim_released','claim_taken_over','work_created','work_observed','runtime_completed','runtime_blocked')",
            name="ck_paper_runtime_events_type",
        ),
    )
    op.create_index(
        "ix_paper_runtime_events_runtime",
        "paper_runtime_events",
        ["runtime_id", "event_sequence"],
    )

    op.create_table(
        "paper_runtime_command_receipts",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("receipt_schema_version", sa.Integer(), nullable=False),
        sa.Column("namespace", sa.String(64), nullable=False),
        sa.Column("command_idempotency_key", sa.String(128), nullable=False),
        sa.Column("command_digest", sa.String(64), nullable=False),
        sa.Column("command_actor", sa.String(256), nullable=False),
        sa.Column("runtime_id", sa.String(96), nullable=False),
        sa.Column("result_event_id", sa.String(96), nullable=False),
        sa.Column("result_event_digest", sa.String(64), nullable=False),
        sa.Column("resulting_runtime_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint(
            "namespace",
            "command_idempotency_key",
            name="pk_paper_runtime_command_receipts",
        ),
        sa.UniqueConstraint(
            "namespace",
            "command_digest",
            name="uq_paper_runtime_command_receipts_digest",
        ),
        sa.ForeignKeyConstraint(
            ("runtime_id",),
            ("paper_runtimes.runtime_id",),
            name="fk_paper_runtime_receipts_runtime",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("result_event_id",),
            ("paper_runtime_events.event_id",),
            name="fk_paper_runtime_receipts_event",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "record_schema_version = 1 AND receipt_schema_version = 1",
            name="ck_paper_runtime_receipts_versions",
        ),
        sa.CheckConstraint(
            "namespace IN ('create_paper_runtime','start_paper_runtime','stop_paper_runtime','resume_paper_runtime','recover_paper_runtime')",
            name="ck_paper_runtime_receipts_namespace",
        ),
        sa.CheckConstraint(
            _digest("command_digest"), name="ck_paper_runtime_receipts_command_digest"
        ),
        sa.CheckConstraint(
            _digest("result_event_digest"),
            name="ck_paper_runtime_receipts_event_digest",
        ),
        sa.CheckConstraint(
            "resulting_runtime_version >= 0",
            name="ck_paper_runtime_receipts_version_nonnegative",
        ),
    )
    op.create_index(
        "ix_paper_runtime_receipts_result",
        "paper_runtime_command_receipts",
        ["runtime_id", "result_event_id"],
    )

    _append_only("paper_runtime_work", "paper_runtime_work")
    _append_only("paper_runtime_checkpoints", "paper_runtime_checkpoints")
    _append_only("paper_runtime_events", "paper_runtime_events")
    _append_only("paper_runtime_command_receipts", "paper_runtime_receipts")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_paper_runtime_receipts_no_delete")
    op.execute("DROP TRIGGER IF EXISTS trg_paper_runtime_receipts_no_update")
    op.drop_table("paper_runtime_command_receipts")
    op.execute("DROP TRIGGER IF EXISTS trg_paper_runtime_events_no_delete")
    op.execute("DROP TRIGGER IF EXISTS trg_paper_runtime_events_no_update")
    op.drop_table("paper_runtime_events")
    op.execute("DROP TRIGGER IF EXISTS trg_paper_runtime_checkpoints_no_delete")
    op.execute("DROP TRIGGER IF EXISTS trg_paper_runtime_checkpoints_no_update")
    op.drop_table("paper_runtime_checkpoints")
    op.execute("DROP TRIGGER IF EXISTS trg_paper_runtime_work_no_delete")
    op.execute("DROP TRIGGER IF EXISTS trg_paper_runtime_work_no_update")
    op.drop_table("paper_runtime_work")
    op.execute("DROP TRIGGER IF EXISTS trg_paper_runtimes_immutable_binding")
    op.execute("DROP TRIGGER IF EXISTS trg_paper_runtimes_no_delete")
    op.drop_table("paper_runtimes")
