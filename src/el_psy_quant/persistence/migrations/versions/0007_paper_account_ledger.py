"""Add durable Paper Account and immutable ledger persistence.

Revision ID: 0007_paper_account_ledger
Revises: 0006_portfolio_reviews
Create Date: 2026-07-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_paper_account_ledger"
down_revision: str | Sequence[str] | None = "0006_portfolio_reviews"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DIGEST = (
    "length({column}) = 64 AND {column} NOT GLOB '*[^0-9a-f]*'"
)
_APPEND_ONLY_TABLES = (
    "paper_account_events",
    "paper_cash_ledger_entries",
    "paper_position_ledger_entries",
    "paper_account_creation_keys",
    "paper_account_snapshots",
    "paper_account_reconciliations",
)


def _digest_check(*columns: str) -> str:
    return " AND ".join(_DIGEST.format(column=column) for column in columns)


def _create_append_only_triggers(table_name: str) -> None:
    for operation in ("UPDATE", "DELETE"):
        suffix = operation.lower()
        op.execute(
            sa.text(
                f'CREATE TRIGGER "trg_{table_name}_no_{suffix}" '
                f'BEFORE {operation} ON "{table_name}" '
                "BEGIN "
                f"SELECT RAISE(ABORT, '{table_name} is append-only'); "
                "END"
            )
        )


def upgrade() -> None:
    """Create the complete Sprint 184 durable account boundary."""
    op.create_table(
        "paper_accounts",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.String(length=512), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("base_currency", sa.String(length=3), nullable=False),
        sa.Column("lifecycle_status", sa.String(length=16), nullable=False),
        sa.Column("head_version", sa.Integer(), nullable=False),
        sa.Column("head_event_id", sa.String(length=512), nullable=False),
        sa.Column("head_chain_digest", sa.String(length=64), nullable=False),
        sa.Column("projection_status", sa.String(length=32), nullable=False),
        sa.Column("created_by", sa.String(length=512), nullable=False),
        sa.Column("created_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_paper_accounts_record_schema_version",
        ),
        sa.CheckConstraint(
            "lifecycle_status IN ('active', 'frozen', 'closed')",
            name="ck_paper_accounts_lifecycle_status",
        ),
        sa.CheckConstraint(
            "projection_status IN ('current', 'reconciliation_required')",
            name="ck_paper_accounts_projection_status",
        ),
        sa.CheckConstraint(
            "head_version > 0",
            name="ck_paper_accounts_head_version",
        ),
        sa.CheckConstraint(
            "length(base_currency) = 3 "
            "AND base_currency = upper(base_currency) "
            "AND base_currency NOT GLOB '*[^A-Z]*'",
            name="ck_paper_accounts_base_currency",
        ),
        sa.CheckConstraint(
            _digest_check("head_chain_digest"),
            name="ck_paper_accounts_digest_shapes",
        ),
        sa.CheckConstraint(
            "(lifecycle_status = 'closed' AND closed_timestamp IS NOT NULL) "
            "OR (lifecycle_status != 'closed' AND closed_timestamp IS NULL)",
            name="ck_paper_accounts_closed_timestamp",
        ),
        sa.PrimaryKeyConstraint("account_id", name="pk_paper_accounts"),
        sa.ForeignKeyConstraint(
            ["account_id", "head_event_id"],
            ["paper_account_events.account_id", "paper_account_events.event_id"],
            name="fk_paper_accounts_head_event",
            deferrable=True,
            initially="DEFERRED",
        ),
    )
    op.create_index(
        "ix_paper_accounts_created_timestamp",
        "paper_accounts",
        ["created_timestamp", "account_id"],
    )
    op.create_index(
        "ix_paper_accounts_lifecycle_status",
        "paper_accounts",
        ["lifecycle_status", "created_timestamp", "account_id"],
    )

    op.create_table(
        "paper_account_events",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("event_schema_version", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=512), nullable=False),
        sa.Column("account_id", sa.String(length=512), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("account_version", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=48), nullable=False),
        sa.Column(
            "command_idempotency_key", sa.String(length=128), nullable=False
        ),
        sa.Column("command_digest", sa.String(length=64), nullable=False),
        sa.Column("expected_account_version", sa.Integer(), nullable=True),
        sa.Column("actor", sa.String(length=512), nullable=False),
        sa.Column("reason", sa.String(length=2000), nullable=True),
        sa.Column("effective_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details_payload", sa.Text(), nullable=False),
        sa.Column("previous_chain_digest", sa.String(length=64), nullable=False),
        sa.Column("event_digest", sa.String(length=64), nullable=False),
        sa.Column("chain_digest", sa.String(length=64), nullable=False),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_paper_account_events_record_schema_version",
        ),
        sa.CheckConstraint(
            "event_schema_version = 1",
            name="ck_paper_account_events_event_schema_version",
        ),
        sa.CheckConstraint(
            "sequence_number > 0 AND account_version = sequence_number",
            name="ck_paper_account_events_sequence_version",
        ),
        sa.CheckConstraint(
            "(sequence_number = 1 AND expected_account_version IS NULL) "
            "OR (sequence_number > 1 "
            "AND expected_account_version = sequence_number - 1)",
            name="ck_paper_account_events_expected_version",
        ),
        sa.CheckConstraint(
            "event_type IN ("
            "'account_created', 'cash_movement_posted', "
            "'position_adjustment_posted', "
            "'portfolio_review_evidence_linked', 'account_frozen', "
            "'account_reactivated', 'account_closed')",
            name="ck_paper_account_events_event_type",
        ),
        sa.CheckConstraint(
            _digest_check(
                "command_digest",
                "previous_chain_digest",
                "event_digest",
                "chain_digest",
            ),
            name="ck_paper_account_events_digest_shapes",
        ),
        sa.PrimaryKeyConstraint("event_id", name="pk_paper_account_events"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["paper_accounts.account_id"],
            name="fk_paper_account_events_account_id",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.UniqueConstraint(
            "account_id",
            "event_id",
            name="uq_paper_account_events_account_event",
        ),
        sa.UniqueConstraint(
            "account_id",
            "sequence_number",
            name="uq_paper_account_events_account_sequence",
        ),
        sa.UniqueConstraint(
            "account_id",
            "command_idempotency_key",
            name="uq_paper_account_events_account_command_key",
        ),
        sa.UniqueConstraint(
            "event_digest",
            name="uq_paper_account_events_event_digest",
        ),
    )
    op.create_index(
        "ix_paper_account_events_account_recorded",
        "paper_account_events",
        ["account_id", "recorded_timestamp", "event_id"],
    )

    op.create_table(
        "paper_cash_ledger_entries",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("entry_schema_version", sa.Integer(), nullable=False),
        sa.Column("cash_entry_id", sa.String(length=512), nullable=False),
        sa.Column("account_id", sa.String(length=512), nullable=False),
        sa.Column("event_id", sa.String(length=512), nullable=False),
        sa.Column("entry_index", sa.Integer(), nullable=False),
        sa.Column("movement_type", sa.String(length=24), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("signed_amount", sa.String(length=64), nullable=False),
        sa.Column("entry_digest", sa.String(length=64), nullable=False),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_paper_cash_entries_record_schema_version",
        ),
        sa.CheckConstraint(
            "entry_schema_version = 1",
            name="ck_paper_cash_entries_entry_schema_version",
        ),
        sa.CheckConstraint(
            "entry_index = 0",
            name="ck_paper_cash_entries_entry_index",
        ),
        sa.CheckConstraint(
            "movement_type IN ('initial_cash', 'deposit', 'withdrawal', "
            "'manual_adjustment', 'fee', 'commission', 'tax')",
            name="ck_paper_cash_entries_movement_type",
        ),
        sa.CheckConstraint(
            "length(currency) = 3 AND currency = upper(currency) "
            "AND currency NOT GLOB '*[^A-Z]*'",
            name="ck_paper_cash_entries_currency",
        ),
        sa.CheckConstraint(
            "length(signed_amount) > 0 "
            "AND signed_amount NOT GLOB '*[^0-9.-]*' "
            "AND signed_amount NOT LIKE '+%' "
            "AND signed_amount NOT LIKE '%e%' "
            "AND signed_amount NOT LIKE '%E%'",
            name="ck_paper_cash_entries_decimal_shape",
        ),
        sa.CheckConstraint(
            _digest_check("entry_digest"),
            name="ck_paper_cash_entries_digest_shape",
        ),
        sa.PrimaryKeyConstraint(
            "cash_entry_id", name="pk_paper_cash_ledger_entries"
        ),
        sa.ForeignKeyConstraint(
            ["account_id", "event_id"],
            ["paper_account_events.account_id", "paper_account_events.event_id"],
            name="fk_paper_cash_entries_account_event",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "event_id",
            "entry_index",
            name="uq_paper_cash_entries_event_index",
        ),
        sa.UniqueConstraint(
            "entry_digest",
            name="uq_paper_cash_entries_entry_digest",
        ),
    )
    op.create_index(
        "ix_paper_cash_entries_account_event",
        "paper_cash_ledger_entries",
        ["account_id", "event_id", "entry_index"],
    )

    op.create_table(
        "paper_position_ledger_entries",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("entry_schema_version", sa.Integer(), nullable=False),
        sa.Column("position_entry_id", sa.String(length=512), nullable=False),
        sa.Column("account_id", sa.String(length=512), nullable=False),
        sa.Column("event_id", sa.String(length=512), nullable=False),
        sa.Column("entry_index", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=128), nullable=False),
        sa.Column("signed_quantity_delta", sa.String(length=64), nullable=False),
        sa.Column("signed_cost_basis_delta", sa.String(length=64), nullable=False),
        sa.Column("adjustment_category", sa.String(length=32), nullable=False),
        sa.Column("entry_digest", sa.String(length=64), nullable=False),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_paper_position_entries_record_schema_version",
        ),
        sa.CheckConstraint(
            "entry_schema_version = 1",
            name="ck_paper_position_entries_entry_schema_version",
        ),
        sa.CheckConstraint(
            "entry_index = 0",
            name="ck_paper_position_entries_entry_index",
        ),
        sa.CheckConstraint(
            "adjustment_category IN ('opening_balance', 'manual_correction', "
            "'corporate_action', 'other')",
            name="ck_paper_position_entries_adjustment_category",
        ),
        sa.CheckConstraint(
            "length(signed_quantity_delta) > 0 "
            "AND signed_quantity_delta NOT GLOB '*[^0-9.-]*' "
            "AND signed_cost_basis_delta NOT GLOB '*[^0-9.-]*'",
            name="ck_paper_position_entries_decimal_shapes",
        ),
        sa.CheckConstraint(
            _digest_check("entry_digest"),
            name="ck_paper_position_entries_digest_shape",
        ),
        sa.PrimaryKeyConstraint(
            "position_entry_id", name="pk_paper_position_ledger_entries"
        ),
        sa.ForeignKeyConstraint(
            ["account_id", "event_id"],
            ["paper_account_events.account_id", "paper_account_events.event_id"],
            name="fk_paper_position_entries_account_event",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "event_id",
            "entry_index",
            name="uq_paper_position_entries_event_index",
        ),
        sa.UniqueConstraint(
            "entry_digest",
            name="uq_paper_position_entries_entry_digest",
        ),
    )
    op.create_index(
        "ix_paper_position_entries_account_event",
        "paper_position_ledger_entries",
        ["account_id", "event_id", "entry_index"],
    )

    op.create_table(
        "paper_account_creation_keys",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column(
            "creation_idempotency_key", sa.String(length=128), nullable=False
        ),
        sa.Column("creation_request_digest", sa.String(length=64), nullable=False),
        sa.Column("account_id", sa.String(length=512), nullable=False),
        sa.Column("creation_event_id", sa.String(length=512), nullable=False),
        sa.Column("created_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_paper_account_creation_keys_record_schema_version",
        ),
        sa.CheckConstraint(
            _digest_check("creation_request_digest"),
            name="ck_paper_account_creation_keys_digest_shape",
        ),
        sa.PrimaryKeyConstraint(
            "creation_idempotency_key",
            name="pk_paper_account_creation_keys",
        ),
        sa.ForeignKeyConstraint(
            ["account_id", "creation_event_id"],
            ["paper_account_events.account_id", "paper_account_events.event_id"],
            name="fk_paper_account_creation_keys_account_event",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "account_id", name="uq_paper_account_creation_keys_account_id"
        ),
        sa.UniqueConstraint(
            "creation_event_id",
            name="uq_paper_account_creation_keys_event_id",
        ),
    )

    op.create_table(
        "paper_account_projections",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("projection_schema_version", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.String(length=512), nullable=False),
        sa.Column("lifecycle_status", sa.String(length=16), nullable=False),
        sa.Column("cash_balance", sa.String(length=64), nullable=False),
        sa.Column("available_cash", sa.String(length=64), nullable=False),
        sa.Column(
            "approved_portfolio_reviews_payload", sa.Text(), nullable=False
        ),
        sa.Column("source_account_version", sa.Integer(), nullable=False),
        sa.Column("source_event_id", sa.String(length=512), nullable=False),
        sa.Column("source_chain_digest", sa.String(length=64), nullable=False),
        sa.Column("projection_digest", sa.String(length=64), nullable=False),
        sa.Column("updated_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_paper_account_projections_record_schema_version",
        ),
        sa.CheckConstraint(
            "projection_schema_version = 1",
            name="ck_paper_account_projections_schema_version",
        ),
        sa.CheckConstraint(
            "lifecycle_status IN ('active', 'frozen', 'closed')",
            name="ck_paper_account_projections_lifecycle_status",
        ),
        sa.CheckConstraint(
            "source_account_version > 0",
            name="ck_paper_account_projections_source_version",
        ),
        sa.CheckConstraint(
            "cash_balance = available_cash",
            name="ck_paper_account_projections_available_cash",
        ),
        sa.CheckConstraint(
            _digest_check(
                "source_chain_digest",
                "projection_digest",
            ),
            name="ck_paper_account_projections_digest_shapes",
        ),
        sa.PrimaryKeyConstraint(
            "account_id", name="pk_paper_account_projections"
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["paper_accounts.account_id"],
            name="fk_paper_account_projections_account_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["account_id", "source_event_id"],
            ["paper_account_events.account_id", "paper_account_events.event_id"],
            name="fk_paper_account_projections_source_event",
            ondelete="RESTRICT",
        ),
    )

    op.create_table(
        "paper_account_position_projections",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column(
            "position_projection_schema_version", sa.Integer(), nullable=False
        ),
        sa.Column("account_id", sa.String(length=512), nullable=False),
        sa.Column("symbol", sa.String(length=128), nullable=False),
        sa.Column("quantity", sa.String(length=64), nullable=False),
        sa.Column("aggregate_cost_basis", sa.String(length=64), nullable=False),
        sa.Column("average_unit_cost", sa.String(length=64), nullable=True),
        sa.Column(
            "average_unit_cost_is_rounded", sa.Boolean(), nullable=False
        ),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_paper_position_projections_record_schema_version",
        ),
        sa.CheckConstraint(
            "position_projection_schema_version = 1",
            name="ck_paper_position_projections_schema_version",
        ),
        sa.CheckConstraint(
            "average_unit_cost_is_rounded IN (0, 1)",
            name="ck_paper_position_projections_rounded_boolean",
        ),
        sa.CheckConstraint(
            "(average_unit_cost IS NULL "
            "AND average_unit_cost_is_rounded = 0) "
            "OR average_unit_cost IS NOT NULL",
            name="ck_paper_position_projections_average_cost",
        ),
        sa.PrimaryKeyConstraint(
            "account_id",
            "symbol",
            name="pk_paper_account_position_projections",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["paper_account_projections.account_id"],
            name="fk_paper_position_projections_account_id",
            ondelete="CASCADE",
        ),
    )

    op.create_table(
        "paper_account_snapshots",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("snapshot_schema_version", sa.Integer(), nullable=False),
        sa.Column("snapshot_id", sa.String(length=512), nullable=False),
        sa.Column("account_id", sa.String(length=512), nullable=False),
        sa.Column("account_version", sa.Integer(), nullable=False),
        sa.Column("head_event_id", sa.String(length=512), nullable=False),
        sa.Column("head_chain_digest", sa.String(length=64), nullable=False),
        sa.Column(
            "operation_idempotency_key", sa.String(length=128), nullable=False
        ),
        sa.Column("operation_command_digest", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.String(length=512), nullable=False),
        sa.Column("recorded_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(length=2000), nullable=False),
        sa.Column("projection_payload", sa.Text(), nullable=False),
        sa.Column("projection_digest", sa.String(length=64), nullable=False),
        sa.Column("snapshot_digest", sa.String(length=64), nullable=False),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_paper_account_snapshots_record_schema_version",
        ),
        sa.CheckConstraint(
            "snapshot_schema_version = 1",
            name="ck_paper_account_snapshots_schema_version",
        ),
        sa.CheckConstraint(
            "account_version > 0",
            name="ck_paper_account_snapshots_account_version",
        ),
        sa.CheckConstraint(
            _digest_check(
                "head_chain_digest",
                "operation_command_digest",
                "projection_digest",
                "snapshot_digest",
            ),
            name="ck_paper_account_snapshots_digest_shapes",
        ),
        sa.PrimaryKeyConstraint(
            "snapshot_id", name="pk_paper_account_snapshots"
        ),
        sa.ForeignKeyConstraint(
            ["account_id", "head_event_id"],
            ["paper_account_events.account_id", "paper_account_events.event_id"],
            name="fk_paper_account_snapshots_head_event",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "account_id",
            "operation_idempotency_key",
            name="uq_paper_account_snapshots_account_operation_key",
        ),
        sa.UniqueConstraint(
            "snapshot_digest",
            name="uq_paper_account_snapshots_snapshot_digest",
        ),
    )
    op.create_index(
        "ix_paper_account_snapshots_account_version",
        "paper_account_snapshots",
        ["account_id", "account_version", "snapshot_id"],
    )

    op.create_table(
        "paper_account_reconciliations",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("reconciliation_schema_version", sa.Integer(), nullable=False),
        sa.Column("reconciliation_id", sa.String(length=512), nullable=False),
        sa.Column("account_id", sa.String(length=512), nullable=False),
        sa.Column(
            "operation_idempotency_key", sa.String(length=128), nullable=False
        ),
        sa.Column("operation_command_digest", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.String(length=512), nullable=False),
        sa.Column("recorded_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(length=2000), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("mismatch_codes_payload", sa.Text(), nullable=False),
        sa.Column("authoritative_account_version", sa.Integer(), nullable=False),
        sa.Column("authoritative_event_id", sa.String(length=512), nullable=False),
        sa.Column(
            "authoritative_chain_digest", sa.String(length=64), nullable=False
        ),
        sa.Column(
            "authoritative_projection_digest", sa.String(length=64), nullable=False
        ),
        sa.Column("candidate_account_version", sa.Integer(), nullable=False),
        sa.Column("candidate_event_id", sa.String(length=512), nullable=False),
        sa.Column("candidate_chain_digest", sa.String(length=64), nullable=False),
        sa.Column("candidate_projection_digest", sa.String(length=64), nullable=False),
        sa.Column("reconciliation_digest", sa.String(length=64), nullable=False),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_paper_account_reconciliations_record_schema_version",
        ),
        sa.CheckConstraint(
            "reconciliation_schema_version = 1",
            name="ck_paper_account_reconciliations_schema_version",
        ),
        sa.CheckConstraint(
            "outcome IN ('matched', 'mismatched')",
            name="ck_paper_account_reconciliations_outcome",
        ),
        sa.CheckConstraint(
            "authoritative_account_version > 0 "
            "AND candidate_account_version > 0",
            name="ck_paper_account_reconciliations_versions",
        ),
        sa.CheckConstraint(
            _digest_check(
                "operation_command_digest",
                "authoritative_chain_digest",
                "authoritative_projection_digest",
                "candidate_chain_digest",
                "candidate_projection_digest",
                "reconciliation_digest",
            ),
            name="ck_paper_account_reconciliations_digest_shapes",
        ),
        sa.PrimaryKeyConstraint(
            "reconciliation_id",
            name="pk_paper_account_reconciliations",
        ),
        sa.ForeignKeyConstraint(
            ["account_id", "authoritative_event_id"],
            ["paper_account_events.account_id", "paper_account_events.event_id"],
            name="fk_paper_account_reconciliations_authoritative_event",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["account_id", "candidate_event_id"],
            ["paper_account_events.account_id", "paper_account_events.event_id"],
            name="fk_paper_account_reconciliations_candidate_event",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "account_id",
            "operation_idempotency_key",
            name="uq_paper_account_reconciliations_account_operation_key",
        ),
        sa.UniqueConstraint(
            "reconciliation_digest",
            name="uq_paper_account_reconciliations_digest",
        ),
    )
    op.create_index(
        "ix_paper_account_reconciliations_account_recorded",
        "paper_account_reconciliations",
        ["account_id", "recorded_timestamp", "reconciliation_id"],
    )

    for table_name in _APPEND_ONLY_TABLES:
        _create_append_only_triggers(table_name)
    op.execute(
        sa.text(
            'CREATE TRIGGER "trg_paper_accounts_no_delete" '
            'BEFORE DELETE ON "paper_accounts" '
            "BEGIN "
            "SELECT RAISE(ABORT, 'paper_accounts cannot be deleted'); "
            "END"
        )
    )
    op.execute(
        sa.text(
            'CREATE TRIGGER "trg_paper_accounts_immutable_identity" '
            "BEFORE UPDATE OF record_schema_version, account_id, display_name, "
            "base_currency, created_by, created_timestamp "
            'ON "paper_accounts" '
            "BEGIN "
            "SELECT RAISE(ABORT, 'paper account identity is immutable'); "
            "END"
        )
    )


def _drop_sprint_184_objects() -> None:
    """Remove the complete Sprint 184 object graph."""
    op.execute(sa.text('DROP TRIGGER "trg_paper_accounts_immutable_identity"'))
    op.execute(sa.text('DROP TRIGGER "trg_paper_accounts_no_delete"'))
    for table_name in reversed(_APPEND_ONLY_TABLES):
        for suffix in ("delete", "update"):
            op.execute(
                sa.text(f'DROP TRIGGER "trg_{table_name}_no_{suffix}"')
            )

    op.drop_table("paper_account_reconciliations")
    op.drop_table("paper_account_snapshots")
    op.drop_table("paper_account_position_projections")
    op.drop_table("paper_account_projections")
    op.drop_table("paper_account_creation_keys")
    op.drop_table("paper_position_ledger_entries")
    op.drop_table("paper_cash_ledger_entries")
    op.drop_table("paper_account_events")
    op.drop_index(
        "ix_paper_accounts_lifecycle_status",
        table_name="paper_accounts",
    )
    op.drop_index(
        "ix_paper_accounts_created_timestamp",
        table_name="paper_accounts",
    )
    op.drop_table("paper_accounts")


def downgrade() -> None:
    """Remove only Sprint 184 objects in dependency-safe order."""
    context = op.get_context()
    connection = op.get_bind()
    # SQLite ignores foreign_keys changes inside a transaction. Alembic's
    # autocommit boundary commits first, so the account/event cycle can be
    # dropped, and the finally block restores enforcement before returning.
    with context.autocommit_block():
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        try:
            _drop_sprint_184_objects()
        finally:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            if (
                connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one()
                != 1
            ):
                raise RuntimeError(
                    "failed to restore SQLite foreign-key enforcement"
                )
