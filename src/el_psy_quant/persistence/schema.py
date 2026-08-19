"""Read-only contract for the one supported product database schema."""

from __future__ import annotations

import sqlite3
from pathlib import Path

CURRENT_PRODUCT_SCHEMA_REVISION = "0011_paper_execution"
APPROVED_PRODUCT_SCHEMA_REVISIONS = (
    "0001_product_baseline",
    "0002_artifact_index",
    "0003_paper_jobs",
    "0004_paper_job_recovery_audit",
    "0005_paper_job_result_references",
    "0006_portfolio_reviews",
    "0007_paper_account_ledger",
    "0008_market_time_foundation",
    "0009_market_time_runtime",
    "0010_strategy_order_risk",
    CURRENT_PRODUCT_SCHEMA_REVISION,
)

REQUIRED_PRODUCT_TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "artifact_index_entries": (
        "record_schema_version",
        "artifact_type",
        "artifact_key",
        "root_type",
        "relative_path",
        "source_id",
    ),
    "paper_jobs": (
        "record_schema_version",
        "job_id",
        "run_id",
        "status",
        "request_schema_version",
        "request_payload",
        "submitted_timestamp",
        "updated_timestamp",
    ),
    "paper_job_submission_keys": (
        "record_schema_version",
        "idempotency_key",
        "job_id",
        "request_schema_version",
        "request_digest",
        "created_timestamp",
    ),
    "paper_job_attempts": (
        "record_schema_version",
        "attempt_id",
        "job_id",
        "attempt_number",
        "status",
        "started_timestamp",
        "completed_timestamp",
        "error_code",
    ),
    "paper_job_result_references": (
        "record_schema_version",
        "job_id",
        "root_type",
        "artifact_schema_version",
        "result_summary_schema_version",
        "artifact_relative_path",
        "result_summary_relative_path",
        "created_timestamp",
    ),
    "portfolio_reviews": (
        "record_schema_version",
        "review_id",
        "status",
        "source_schema_version",
        "source_id",
        "source_digest",
        "source_relative_path",
        "baseline_scenario_id",
        "baseline_scenario_digest",
        "proposed_scenario_id",
        "proposed_scenario_digest",
        "proposed_component_id",
        "analysis_schema_version",
        "analysis_digest",
        "analysis_relative_path",
        "create_idempotency_key",
        "create_command_digest",
        "created_by",
        "created_timestamp",
        "decision_schema_version",
        "decision_id",
        "decision_digest",
        "decision_relative_path",
        "decision_idempotency_key",
        "decision_command_digest",
        "outcome",
        "reviewed_by",
        "reviewed_timestamp",
        "version",
        "updated_timestamp",
    ),
    "paper_accounts": (
        "record_schema_version",
        "account_id",
        "display_name",
        "base_currency",
        "lifecycle_status",
        "head_version",
        "head_event_id",
        "head_chain_digest",
        "projection_status",
        "created_by",
        "created_timestamp",
        "updated_timestamp",
        "closed_timestamp",
    ),
    "paper_account_events": (
        "record_schema_version",
        "event_schema_version",
        "event_id",
        "account_id",
        "sequence_number",
        "account_version",
        "event_type",
        "command_idempotency_key",
        "command_digest",
        "expected_account_version",
        "actor",
        "reason",
        "effective_timestamp",
        "recorded_timestamp",
        "details_payload",
        "previous_chain_digest",
        "event_digest",
        "chain_digest",
    ),
    "paper_cash_ledger_entries": (
        "record_schema_version",
        "entry_schema_version",
        "cash_entry_id",
        "account_id",
        "event_id",
        "entry_index",
        "movement_type",
        "currency",
        "signed_amount",
        "entry_digest",
    ),
    "paper_position_ledger_entries": (
        "record_schema_version",
        "entry_schema_version",
        "position_entry_id",
        "account_id",
        "event_id",
        "entry_index",
        "symbol",
        "signed_quantity_delta",
        "signed_cost_basis_delta",
        "adjustment_category",
        "entry_digest",
    ),
    "paper_account_creation_keys": (
        "record_schema_version",
        "creation_idempotency_key",
        "creation_request_digest",
        "account_id",
        "creation_event_id",
        "created_timestamp",
    ),
    "paper_account_projections": (
        "record_schema_version",
        "projection_schema_version",
        "account_id",
        "lifecycle_status",
        "cash_balance",
        "available_cash",
        "approved_portfolio_reviews_payload",
        "source_account_version",
        "source_event_id",
        "source_chain_digest",
        "projection_digest",
        "updated_timestamp",
    ),
    "paper_account_position_projections": (
        "record_schema_version",
        "position_projection_schema_version",
        "account_id",
        "symbol",
        "quantity",
        "aggregate_cost_basis",
        "average_unit_cost",
        "average_unit_cost_is_rounded",
    ),
    "paper_account_snapshots": (
        "record_schema_version",
        "snapshot_schema_version",
        "snapshot_id",
        "account_id",
        "account_version",
        "head_event_id",
        "head_chain_digest",
        "operation_idempotency_key",
        "operation_command_digest",
        "created_by",
        "recorded_timestamp",
        "reason",
        "projection_payload",
        "projection_digest",
        "snapshot_digest",
    ),
    "paper_account_reconciliations": (
        "record_schema_version",
        "reconciliation_schema_version",
        "reconciliation_id",
        "account_id",
        "operation_idempotency_key",
        "operation_command_digest",
        "created_by",
        "recorded_timestamp",
        "reason",
        "outcome",
        "mismatch_codes_payload",
        "authoritative_account_version",
        "authoritative_event_id",
        "authoritative_chain_digest",
        "authoritative_projection_digest",
        "candidate_account_version",
        "candidate_event_id",
        "candidate_chain_digest",
        "candidate_projection_digest",
        "reconciliation_digest",
    ),
    "trading_calendars": (
        "record_schema_version",
        "calendar_id",
        "market",
        "timezone",
        "calendar_version",
        "created_at",
    ),
    "trading_sessions": (
        "record_schema_version",
        "session_id",
        "calendar_id",
        "trading_date",
        "open_time",
        "close_time",
        "session_type",
    ),
    "market_data_events": (
        "record_schema_version",
        "event_schema_version",
        "event_id",
        "instrument_id",
        "event_time",
        "event_json",
    ),
    "market_data_replays": (
        "record_schema_version",
        "replay_state_schema_version",
        "replay_id",
        "event_stream_digest",
        "event_count",
        "start_time",
        "position",
        "last_event_id",
        "current_event_time",
        "status",
    ),
    "market_data_replay_events": (
        "record_schema_version",
        "replay_id",
        "event_position",
        "event_id",
    ),
    "strategy_signals": (
        "record_schema_version",
        "signal_schema_version",
        "signal_id",
        "signal_digest",
        "payload_json",
        "strategy_name",
        "strategy_version",
        "adapter_version",
        "parameters_digest",
        "calendar_id",
        "calendar_version",
        "trading_session_id",
        "replay_id",
        "event_stream_digest",
        "cursor_position",
        "signal_event_id",
        "instrument_id",
        "target_semantics",
        "target_position_quantity",
        "created_at",
    ),
    "order_intents": (
        "record_schema_version",
        "intent_schema_version",
        "intent_id",
        "intent_digest",
        "payload_json",
        "signal_id",
        "signal_digest",
        "account_id",
        "account_head_version",
        "account_head_event_id",
        "account_head_chain_digest",
        "calendar_id",
        "trading_session_id",
        "replay_id",
        "event_stream_digest",
        "cursor_position",
        "current_event_id",
        "instrument_id",
        "side",
        "requested_quantity",
        "target_position_quantity",
        "current_position_quantity",
        "intent_policy_version",
        "created_at",
    ),
    "pre_trade_risk_decisions": (
        "record_schema_version",
        "decision_schema_version",
        "decision_id",
        "decision_digest",
        "payload_json",
        "snapshot_id",
        "snapshot_digest",
        "intent_id",
        "intent_digest",
        "account_id",
        "account_head_version",
        "account_head_event_id",
        "account_head_chain_digest",
        "calendar_id",
        "trading_session_id",
        "replay_id",
        "event_stream_digest",
        "cursor_position",
        "current_event_id",
        "instrument_id",
        "risk_policy_id",
        "risk_policy_configuration_digest",
        "outcome",
        "reason_codes_json",
        "created_at",
    ),
    "strategy_order_command_receipts": (
        "record_schema_version",
        "namespace",
        "command_idempotency_key",
        "command_digest",
        "command_actor",
        "result_kind",
        "result_id",
        "result_digest",
        "result_payload_json",
        "created_at",
    ),
    "paper_execution_orders": (
        "record_schema_version",
        "order_schema_version",
        "execution_order_id",
        "execution_order_digest",
        "payload_json",
        "intent_id",
        "intent_digest",
        "risk_decision_id",
        "risk_decision_digest",
        "risk_snapshot_id",
        "risk_snapshot_digest",
        "account_id",
        "account_handoff_version",
        "account_handoff_event_id",
        "account_handoff_chain_digest",
        "calendar_id",
        "calendar_version",
        "trading_session_id",
        "replay_id",
        "event_stream_digest",
        "handoff_cursor_position",
        "handoff_event_id",
        "instrument_id",
        "side",
        "requested_quantity",
        "policy_id",
        "policy_configuration_digest",
        "policy_reference_digest",
        "origin_command_digest",
        "created_at",
    ),
    "paper_execution_attempts": (
        "record_schema_version",
        "attempt_schema_version",
        "attempt_id",
        "attempt_digest",
        "execution_order_id",
        "execution_version_before",
        "execution_version_after",
        "attempt_result",
        "consumed_event_id",
        "consumed_event_position",
        "pre_cursor_position",
        "pre_cursor_last_event_id",
        "post_cursor_position",
        "post_cursor_last_event_id",
        "payload_json",
        "created_at",
    ),
    "paper_execution_fills": (
        "record_schema_version",
        "fill_schema_version",
        "fill_id",
        "fill_digest",
        "execution_order_id",
        "attempt_id",
        "consumed_event_id",
        "consumed_event_position",
        "payload_json",
        "created_at",
    ),
    "paper_execution_settlement_links": (
        "record_schema_version",
        "settlement_link_schema_version",
        "settlement_link_id",
        "settlement_link_digest",
        "settlement_link_evidence_digest",
        "execution_order_id",
        "attempt_id",
        "fill_id",
        "account_id",
        "account_event_id",
        "cash_entry_id",
        "position_entry_id",
        "payload_json",
        "recorded_at",
    ),
    "paper_execution_command_receipts": (
        "record_schema_version",
        "namespace",
        "command_idempotency_key",
        "command_digest",
        "command_actor",
        "result_kind",
        "execution_order_id",
        "execution_order_digest",
        "attempt_id",
        "attempt_digest",
        "fill_id",
        "fill_digest",
        "settlement_link_id",
        "settlement_link_evidence_digest",
        "account_event_id",
        "created_at",
    ),
}

REQUIRED_PRODUCT_INDEXES: dict[str, tuple[str, ...]] = {
    "paper_accounts": (
        "ix_paper_accounts_created_timestamp",
        "ix_paper_accounts_lifecycle_status",
    ),
    "paper_account_events": (
        "ix_paper_account_events_account_recorded",
    ),
    "paper_cash_ledger_entries": (
        "ix_paper_cash_entries_account_event",
    ),
    "paper_position_ledger_entries": (
        "ix_paper_position_entries_account_event",
    ),
    "paper_account_snapshots": (
        "ix_paper_account_snapshots_account_version",
    ),
    "paper_account_reconciliations": (
        "ix_paper_account_reconciliations_account_recorded",
    ),
    "trading_sessions": (
        "ix_trading_sessions_calendar_date_open",
    ),
    "market_data_events": (
        "ix_market_data_events_time_id",
    ),
    "market_data_replays": (
        "ix_market_data_replays_status_id",
    ),
    "market_data_replay_events": (
        "ix_market_data_replay_events_event_id",
    ),
    "strategy_signals": (
        "ix_strategy_signals_created_id",
        "ix_strategy_signals_instrument_created_id",
        "ix_strategy_signals_market_anchor",
        "ix_strategy_signals_strategy_created_id",
        "ix_strategy_signals_strategy_instrument",
    ),
    "order_intents": (
        "ix_order_intents_account_created_id",
        "ix_order_intents_created_id",
        "ix_order_intents_instrument_created_id",
        "ix_order_intents_market_anchor",
        "ix_order_intents_side_created_id",
        "ix_order_intents_signal_created_id",
        "ix_order_intents_signal_account",
    ),
    "pre_trade_risk_decisions": (
        "ix_pre_trade_risk_decisions_account_created_id",
        "ix_pre_trade_risk_decisions_account_market",
        "ix_pre_trade_risk_decisions_created_id",
        "ix_pre_trade_risk_decisions_intent_created_id",
        "ix_pre_trade_risk_decisions_intent_outcome",
        "ix_pre_trade_risk_decisions_outcome_created_id",
    ),
    "strategy_order_command_receipts": (
        "ix_strategy_order_command_receipts_result",
    ),
    "paper_execution_orders": (
        "ix_paper_execution_orders_created_id",
        "ix_paper_execution_orders_intent_policy",
        "ix_paper_execution_orders_working_tuple",
    ),
    "paper_execution_attempts": (
        "ix_paper_execution_attempts_event",
        "ix_paper_execution_attempts_order_version",
    ),
    "paper_execution_fills": (
        "ix_paper_execution_fills_event",
        "ix_paper_execution_fills_order_created",
    ),
    "paper_execution_settlement_links": (
        "ix_paper_execution_settlement_links_order",
    ),
    "paper_execution_command_receipts": (
        "ix_paper_execution_receipts_result",
    ),
}

REQUIRED_PRODUCT_TRIGGERS = (
    "trg_paper_accounts_immutable_identity",
    "trg_paper_accounts_no_delete",
    "trg_paper_account_events_no_update",
    "trg_paper_account_events_no_delete",
    "trg_paper_cash_ledger_entries_no_update",
    "trg_paper_cash_ledger_entries_no_delete",
    "trg_paper_position_ledger_entries_no_update",
    "trg_paper_position_ledger_entries_no_delete",
    "trg_paper_account_creation_keys_no_update",
    "trg_paper_account_creation_keys_no_delete",
    "trg_paper_account_snapshots_no_update",
    "trg_paper_account_snapshots_no_delete",
    "trg_paper_account_reconciliations_no_update",
    "trg_paper_account_reconciliations_no_delete",
    "trg_trading_calendars_no_update",
    "trg_trading_calendars_no_delete",
    "trg_trading_sessions_no_update",
    "trg_trading_sessions_no_delete",
    "trg_market_data_events_no_update",
    "trg_market_data_events_no_delete",
    "trg_market_data_replay_events_no_update",
    "trg_market_data_replay_events_no_delete",
    "trg_market_data_replays_immutable_stream",
    "trg_market_data_replays_no_delete",
    "trg_strategy_signals_no_update",
    "trg_strategy_signals_no_delete",
    "trg_order_intents_no_update",
    "trg_order_intents_no_delete",
    "trg_pre_trade_risk_decisions_no_update",
    "trg_pre_trade_risk_decisions_no_delete",
    "trg_strategy_order_command_receipts_no_update",
    "trg_strategy_order_command_receipts_no_delete",
    "trg_paper_execution_orders_no_update",
    "trg_paper_execution_orders_no_delete",
    "trg_paper_execution_attempts_no_update",
    "trg_paper_execution_attempts_no_delete",
    "trg_paper_execution_fills_no_update",
    "trg_paper_execution_fills_no_delete",
    "trg_paper_execution_settlement_links_no_update",
    "trg_paper_execution_settlement_links_no_delete",
    "trg_paper_execution_command_receipts_no_update",
    "trg_paper_execution_command_receipts_no_delete",
)


class ProductSchemaVerificationError(Exception):
    """Raised when a product database cannot satisfy the read-only contract."""


def _read_only_connection(database_path: Path) -> sqlite3.Connection:
    try:
        resolved = database_path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ProductSchemaVerificationError(
            "product database is unavailable"
        ) from exc
    if database_path.is_symlink() or not resolved.is_file():
        raise ProductSchemaVerificationError(
            "product database must be an existing real file"
        )
    try:
        return sqlite3.connect(
            f"{resolved.as_uri()}?mode=ro",
            uri=True,
            timeout=1.0,
        )
    except sqlite3.Error as exc:
        raise ProductSchemaVerificationError(
            "product database is not readable"
        ) from exc


def _read_product_schema_revision(connection: sqlite3.Connection) -> str:
    try:
        revisions = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchall()
    except sqlite3.Error as exc:
        raise ProductSchemaVerificationError(
            "product database revision is unavailable"
        ) from exc
    if len(revisions) != 1:
        raise ProductSchemaVerificationError(
            "product database must contain exactly one revision"
        )
    revision = revisions[0][0]
    if (
        not isinstance(revision, str)
        or revision not in APPROVED_PRODUCT_SCHEMA_REVISIONS
    ):
        raise ProductSchemaVerificationError(
            "product database revision is not recognized"
        )
    return revision


def read_product_schema_revision(database_path: str | Path) -> str:
    """Read exactly one approved product revision without changing the database."""
    if not isinstance(database_path, (str, Path)):
        raise ProductSchemaVerificationError(
            "product database path must be a local file path"
        )
    connection: sqlite3.Connection | None = None
    try:
        connection = _read_only_connection(Path(database_path))
        return _read_product_schema_revision(connection)
    except ProductSchemaVerificationError:
        raise
    except (OSError, RuntimeError, sqlite3.Error, ValueError) as exc:
        raise ProductSchemaVerificationError(
            "product database revision verification failed"
        ) from exc
    finally:
        if connection is not None:
            try:
                connection.close()
            except sqlite3.Error as exc:
                raise ProductSchemaVerificationError(
                    "product database revision verification failed"
                ) from exc


def verify_product_schema(database_path: str | Path) -> str:
    """Verify the exact current revision and API-required schema without writes."""
    if not isinstance(database_path, (str, Path)):
        raise ProductSchemaVerificationError(
            "product database path must be a local file path"
        )
    connection: sqlite3.Connection | None = None
    try:
        connection = _read_only_connection(Path(database_path))
        revision = _read_product_schema_revision(connection)
        if revision != CURRENT_PRODUCT_SCHEMA_REVISION:
            raise ProductSchemaVerificationError(
                "product database revision does not match the current revision"
            )

        for table_name, expected_columns in REQUIRED_PRODUCT_TABLE_COLUMNS.items():
            try:
                columns = tuple(
                    row[1]
                    for row in connection.execute(
                        f'PRAGMA table_info("{table_name}")'
                    ).fetchall()
                )
            except sqlite3.Error as exc:
                raise ProductSchemaVerificationError(
                    "product database schema is incompatible"
                ) from exc
            if columns != expected_columns:
                raise ProductSchemaVerificationError(
                    "product database schema is incompatible"
                )
        for table_name, required_names in REQUIRED_PRODUCT_INDEXES.items():
            indexes = {
                row[1]
                for row in connection.execute(
                    f'PRAGMA index_list("{table_name}")'
                ).fetchall()
                if isinstance(row[1], str)
            }
            if not set(required_names).issubset(indexes):
                raise ProductSchemaVerificationError(
                    "product database schema is incompatible"
                )
        triggers = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'trigger'"
            ).fetchall()
            if isinstance(row[0], str)
        }
        if not set(REQUIRED_PRODUCT_TRIGGERS).issubset(triggers):
            raise ProductSchemaVerificationError(
                "product database schema is incompatible"
            )
        return CURRENT_PRODUCT_SCHEMA_REVISION
    except ProductSchemaVerificationError:
        raise
    except (OSError, RuntimeError, sqlite3.Error, ValueError) as exc:
        raise ProductSchemaVerificationError(
            "product database verification failed"
        ) from exc
    finally:
        if connection is not None:
            try:
                connection.close()
            except sqlite3.Error as exc:
                raise ProductSchemaVerificationError(
                    "product database verification failed"
                ) from exc


def product_schema_is_compatible(database_path: str | Path) -> bool:
    """Return whether one existing database satisfies the exact read-only contract."""
    try:
        verify_product_schema(database_path)
    except ProductSchemaVerificationError:
        return False
    return True


__all__ = [
    "APPROVED_PRODUCT_SCHEMA_REVISIONS",
    "CURRENT_PRODUCT_SCHEMA_REVISION",
    "ProductSchemaVerificationError",
    "REQUIRED_PRODUCT_INDEXES",
    "REQUIRED_PRODUCT_TABLE_COLUMNS",
    "REQUIRED_PRODUCT_TRIGGERS",
    "product_schema_is_compatible",
    "read_product_schema_revision",
    "verify_product_schema",
]
