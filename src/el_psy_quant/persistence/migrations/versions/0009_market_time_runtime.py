"""Add durable market-data replay recovery state.

Revision ID: 0009_market_time_runtime
Revises: 0008_market_time_foundation
Create Date: 2026-07-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_market_time_runtime"
down_revision: str | Sequence[str] | None = "0008_market_time_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _append_only_triggers(
    *,
    table_name: str,
    trigger_prefix: str,
) -> None:
    op.execute(
        sa.text(
            f"CREATE TRIGGER trg_{trigger_prefix}_no_update "
            f"BEFORE UPDATE ON {table_name} "
            "BEGIN "
            "SELECT RAISE(ABORT, 'market-time authority is append-only'); "
            "END"
        )
    )
    op.execute(
        sa.text(
            f"CREATE TRIGGER trg_{trigger_prefix}_no_delete "
            f"BEFORE DELETE ON {table_name} "
            "BEGIN "
            "SELECT RAISE(ABORT, 'market-time authority cannot be deleted'); "
            "END"
        )
    )


def upgrade() -> None:
    """Create only canonical event and replay recovery persistence."""
    op.create_table(
        "market_data_events",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("event_schema_version", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=512), nullable=False),
        sa.Column("instrument_id", sa.String(length=512), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_json", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_market_data_events_record_schema_version",
        ),
        sa.CheckConstraint(
            "event_schema_version = 1",
            name="ck_market_data_events_event_schema_version",
        ),
        sa.CheckConstraint(
            "length(event_id) BETWEEN 1 AND 512 "
            "AND event_id = trim(event_id)",
            name="ck_market_data_events_identity",
        ),
        sa.CheckConstraint(
            "length(instrument_id) BETWEEN 1 AND 512 "
            "AND instrument_id = trim(instrument_id)",
            name="ck_market_data_events_instrument_identity",
        ),
        sa.CheckConstraint(
            "length(event_json) >= 2",
            name="ck_market_data_events_canonical_json",
        ),
        sa.PrimaryKeyConstraint(
            "event_id",
            name="pk_market_data_events",
        ),
    )
    op.create_index(
        "ix_market_data_events_time_id",
        "market_data_events",
        ("event_time", "event_id"),
        unique=False,
    )

    op.create_table(
        "market_data_replays",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("replay_state_schema_version", sa.Integer(), nullable=False),
        sa.Column("replay_id", sa.String(length=512), nullable=False),
        sa.Column("event_stream_digest", sa.String(length=64), nullable=False),
        sa.Column("event_count", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("last_event_id", sa.String(length=512), nullable=True),
        sa.Column(
            "current_event_time",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_market_data_replays_record_schema_version",
        ),
        sa.CheckConstraint(
            "replay_state_schema_version = 1",
            name="ck_market_data_replays_state_schema_version",
        ),
        sa.CheckConstraint(
            "length(replay_id) BETWEEN 1 AND 512 "
            "AND replay_id = trim(replay_id)",
            name="ck_market_data_replays_identity",
        ),
        sa.CheckConstraint(
            "length(event_stream_digest) = 64 "
            "AND event_stream_digest NOT GLOB '*[^0-9a-f]*'",
            name="ck_market_data_replays_stream_digest",
        ),
        sa.CheckConstraint(
            "event_count >= 0 AND position >= 0 AND position <= event_count",
            name="ck_market_data_replays_positions",
        ),
        sa.CheckConstraint(
            "(event_count = 0 AND start_time IS NULL) "
            "OR (event_count > 0 AND start_time IS NOT NULL)",
            name="ck_market_data_replays_start_time",
        ),
        sa.CheckConstraint(
            "(last_event_id IS NULL AND current_event_time IS NULL) "
            "OR (last_event_id IS NOT NULL AND current_event_time IS NOT NULL)",
            name="ck_market_data_replays_cursor_pair",
        ),
        sa.CheckConstraint(
            "(position = 0 AND last_event_id IS NULL) "
            "OR (position > 0 AND last_event_id IS NOT NULL)",
            name="ck_market_data_replays_consumed_event",
        ),
        sa.CheckConstraint(
            "status IN ('ready', 'running', 'paused', 'completed')",
            name="ck_market_data_replays_status",
        ),
        sa.CheckConstraint(
            "status != 'ready' OR position = 0",
            name="ck_market_data_replays_ready_position",
        ),
        sa.CheckConstraint(
            "status != 'completed' OR position = event_count",
            name="ck_market_data_replays_completed_position",
        ),
        sa.PrimaryKeyConstraint(
            "replay_id",
            name="pk_market_data_replays",
        ),
    )
    op.create_index(
        "ix_market_data_replays_status_id",
        "market_data_replays",
        ("status", "replay_id"),
        unique=False,
    )

    op.create_table(
        "market_data_replay_events",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("replay_id", sa.String(length=512), nullable=False),
        sa.Column("event_position", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=512), nullable=False),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_market_data_replay_events_record_schema_version",
        ),
        sa.CheckConstraint(
            "length(replay_id) BETWEEN 1 AND 512 "
            "AND replay_id = trim(replay_id)",
            name="ck_market_data_replay_events_replay_identity",
        ),
        sa.CheckConstraint(
            "event_position >= 0",
            name="ck_market_data_replay_events_position",
        ),
        sa.CheckConstraint(
            "length(event_id) BETWEEN 1 AND 512 "
            "AND event_id = trim(event_id)",
            name="ck_market_data_replay_events_event_identity",
        ),
        sa.ForeignKeyConstraint(
            ("replay_id",),
            ("market_data_replays.replay_id",),
            name="fk_market_data_replay_events_replay_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("event_id",),
            ("market_data_events.event_id",),
            name="fk_market_data_replay_events_event_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "replay_id",
            "event_position",
            name="pk_market_data_replay_events",
        ),
        sa.UniqueConstraint(
            "replay_id",
            "event_id",
            name="uq_market_data_replay_events_identity",
        ),
    )
    op.create_index(
        "ix_market_data_replay_events_event_id",
        "market_data_replay_events",
        ("event_id",),
        unique=False,
    )

    _append_only_triggers(
        table_name="market_data_events",
        trigger_prefix="market_data_events",
    )
    _append_only_triggers(
        table_name="market_data_replay_events",
        trigger_prefix="market_data_replay_events",
    )
    op.execute(
        sa.text(
            "CREATE TRIGGER trg_market_data_replays_immutable_stream "
            "BEFORE UPDATE ON market_data_replays "
            "WHEN NEW.record_schema_version IS NOT OLD.record_schema_version "
            "OR NEW.replay_state_schema_version "
            "IS NOT OLD.replay_state_schema_version "
            "OR NEW.replay_id IS NOT OLD.replay_id "
            "OR NEW.event_stream_digest IS NOT OLD.event_stream_digest "
            "OR NEW.event_count IS NOT OLD.event_count "
            "OR NEW.start_time IS NOT OLD.start_time "
            "BEGIN "
            "SELECT RAISE(ABORT, 'replay stream authority is immutable'); "
            "END"
        )
    )
    op.execute(
        sa.text(
            "CREATE TRIGGER trg_market_data_replays_no_delete "
            "BEFORE DELETE ON market_data_replays "
            "BEGIN "
            "SELECT RAISE(ABORT, 'market-time authority cannot be deleted'); "
            "END"
        )
    )


def downgrade() -> None:
    """Remove only the Sprint 193 replay recovery persistence."""
    op.drop_table("market_data_replay_events")
    op.drop_table("market_data_replays")
    op.drop_table("market_data_events")
