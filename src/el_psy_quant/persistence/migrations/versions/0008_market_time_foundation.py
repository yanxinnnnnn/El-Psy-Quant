"""Add durable trading calendars and sessions.

Revision ID: 0008_market_time_foundation
Revises: 0007_paper_account_ledger
Create Date: 2026-07-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_market_time_foundation"
down_revision: str | Sequence[str] | None = "0007_paper_account_ledger"
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
    """Create only the immutable market-time authority tables."""
    op.create_table(
        "trading_calendars",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("calendar_id", sa.String(length=512), nullable=False),
        sa.Column("market", sa.String(length=64), nullable=False),
        sa.Column("timezone", sa.String(length=128), nullable=False),
        sa.Column("calendar_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_trading_calendars_record_schema_version",
        ),
        sa.CheckConstraint(
            "length(calendar_id) BETWEEN 1 AND 512 "
            "AND calendar_id = trim(calendar_id)",
            name="ck_trading_calendars_identity",
        ),
        sa.CheckConstraint(
            "length(market) BETWEEN 1 AND 64 AND market = trim(market) "
            "AND market = upper(market) "
            "AND market NOT GLOB '*[^A-Z0-9._:-]*' "
            "AND substr(market, 1, 1) GLOB '[A-Z0-9]'",
            name="ck_trading_calendars_market",
        ),
        sa.CheckConstraint(
            "length(timezone) BETWEEN 1 AND 128 AND timezone = trim(timezone)",
            name="ck_trading_calendars_timezone",
        ),
        sa.CheckConstraint(
            "calendar_version >= 1",
            name="ck_trading_calendars_version",
        ),
        sa.PrimaryKeyConstraint(
            "calendar_id",
            name="pk_trading_calendars",
        ),
        sa.UniqueConstraint(
            "market",
            "calendar_version",
            name="uq_trading_calendars_market_version",
        ),
    )
    op.create_table(
        "trading_sessions",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=512), nullable=False),
        sa.Column("calendar_id", sa.String(length=512), nullable=False),
        sa.Column("trading_date", sa.Date(), nullable=False),
        sa.Column("open_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("close_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("session_type", sa.String(length=64), nullable=False),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_trading_sessions_record_schema_version",
        ),
        sa.CheckConstraint(
            "length(session_id) BETWEEN 1 AND 512 "
            "AND session_id = trim(session_id)",
            name="ck_trading_sessions_identity",
        ),
        sa.CheckConstraint(
            "length(calendar_id) BETWEEN 1 AND 512 "
            "AND calendar_id = trim(calendar_id)",
            name="ck_trading_sessions_calendar_identity",
        ),
        sa.CheckConstraint(
            "open_time < close_time",
            name="ck_trading_sessions_boundaries",
        ),
        sa.CheckConstraint(
            "length(session_type) BETWEEN 1 AND 64 "
            "AND session_type = trim(session_type) "
            "AND session_type = lower(session_type) "
            "AND session_type NOT GLOB '*[^a-z0-9_]*' "
            "AND substr(session_type, 1, 1) GLOB '[a-z]'",
            name="ck_trading_sessions_type",
        ),
        sa.ForeignKeyConstraint(
            ("calendar_id",),
            ("trading_calendars.calendar_id",),
            name="fk_trading_sessions_calendar_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "session_id",
            name="pk_trading_sessions",
        ),
        sa.UniqueConstraint(
            "calendar_id",
            "trading_date",
            "open_time",
            "close_time",
            "session_type",
            name="uq_trading_sessions_definition",
        ),
    )
    op.create_index(
        "ix_trading_sessions_calendar_date_open",
        "trading_sessions",
        ("calendar_id", "trading_date", "open_time", "session_id"),
        unique=False,
    )
    _append_only_triggers(
        table_name="trading_calendars",
        trigger_prefix="trading_calendars",
    )
    _append_only_triggers(
        table_name="trading_sessions",
        trigger_prefix="trading_sessions",
    )


def downgrade() -> None:
    """Remove only the Sprint 190 market-time authority."""
    op.drop_table("trading_sessions")
    op.drop_table("trading_calendars")
