"""Static presentation metadata for every stable public API error code."""

from dataclasses import dataclass
from typing import Literal, TypeAlias

ErrorCategory: TypeAlias = Literal[
    "authentication",
    "not_found",
    "invalid",
    "conflict",
    "unavailable",
    "protocol",
    "internal",
]


@dataclass(frozen=True)
class StableApiError:
    """One stable public code and its non-behavioral semantic category."""

    code: str
    category: ErrorCategory


STABLE_API_ERRORS: tuple[StableApiError, ...] = (
    StableApiError("not_found", "not_found"),
    StableApiError("method_not_allowed", "protocol"),
    StableApiError("http_error", "protocol"),
    StableApiError("request_validation_error", "invalid"),
    StableApiError("internal_server_error", "internal"),
    StableApiError("founder_authentication_required", "authentication"),
    StableApiError("research_artifact_root_unavailable", "unavailable"),
    StableApiError("research_run_not_found", "not_found"),
    StableApiError("research_artifact_invalid", "invalid"),
    StableApiError("evidence_artifact_root_unavailable", "unavailable"),
    StableApiError("evidence_manifest_not_found", "not_found"),
    StableApiError("evidence_artifact_invalid", "invalid"),
    StableApiError("paper_run_invalid", "invalid"),
    StableApiError("product_database_unavailable", "unavailable"),
    StableApiError("paper_artifact_root_unavailable", "unavailable"),
    StableApiError("paper_job_not_found", "not_found"),
    StableApiError("paper_job_invalid", "invalid"),
    StableApiError("paper_job_idempotency_conflict", "conflict"),
    StableApiError("paper_job_conflict", "conflict"),
    StableApiError("paper_job_state_conflict", "conflict"),
    StableApiError("paper_job_output_conflict", "conflict"),
    StableApiError("paper_job_recovery_failed", "unavailable"),
    StableApiError("paper_job_result_unavailable", "conflict"),
    StableApiError("paper_job_result_invalid", "invalid"),
    StableApiError("portfolio_review_not_found", "not_found"),
    StableApiError("portfolio_review_invalid", "invalid"),
    StableApiError("portfolio_review_conflict", "conflict"),
    StableApiError("portfolio_review_idempotency_conflict", "conflict"),
    StableApiError("portfolio_review_settled_conflict", "conflict"),
    StableApiError("portfolio_review_artifact_conflict", "conflict"),
    StableApiError("portfolio_review_artifact_invalid", "invalid"),
    StableApiError("portfolio_review_artifact_unavailable", "unavailable"),
    StableApiError(
        "portfolio_review_artifact_root_unavailable",
        "unavailable",
    ),
    StableApiError("paper_account_not_found", "not_found"),
    StableApiError("paper_account_version_conflict", "conflict"),
    StableApiError("paper_account_idempotency_conflict", "conflict"),
    StableApiError("paper_account_frozen", "conflict"),
    StableApiError("paper_account_closed", "conflict"),
    StableApiError("paper_account_close_not_empty", "conflict"),
    StableApiError(
        "paper_account_insufficient_available_cash",
        "conflict",
    ),
    StableApiError("paper_account_negative_position", "conflict"),
    StableApiError("paper_account_negative_cost_basis", "conflict"),
    StableApiError(
        "paper_account_zero_quantity_nonzero_cost_basis",
        "conflict",
    ),
    StableApiError("paper_account_invalid_decimal", "invalid"),
    StableApiError("paper_account_invalid_m30_reference", "invalid"),
    StableApiError("paper_account_projection_stale", "conflict"),
    StableApiError("paper_account_reconciliation_failed", "conflict"),
    StableApiError("paper_account_snapshot_conflict", "conflict"),
    StableApiError("paper_account_storage_busy", "unavailable"),
    StableApiError("paper_account_schema_incompatible", "unavailable"),
    StableApiError("strategy_signal_not_found", "not_found"),
    StableApiError("order_intent_not_found", "not_found"),
    StableApiError(
        "pre_trade_risk_decision_not_found", "not_found"
    ),
    StableApiError("strategy_order_idempotency_conflict", "conflict"),
    StableApiError("strategy_order_stale_authority", "conflict"),
    StableApiError(
        "strategy_order_reconciliation_required", "conflict"
    ),
    StableApiError(
        "strategy_order_invalid_runtime_configuration", "invalid"
    ),
    StableApiError("strategy_order_invalid_risk_policy", "invalid"),
    StableApiError("strategy_order_invalid_decimal", "invalid"),
    StableApiError("strategy_order_invalid_cursor", "invalid"),
    StableApiError("strategy_order_schema_incompatible", "unavailable"),
    StableApiError("strategy_order_authority_unavailable", "unavailable"),
    StableApiError("strategy_order_storage_busy", "unavailable"),
    StableApiError("strategy_order_storage_failure", "unavailable"),
    StableApiError("lifecycle_transition_proposal_invalid", "invalid"),
    StableApiError("lifecycle_transition_record_invalid", "invalid"),
    StableApiError("demo_workspace_not_configured", "not_found"),
    StableApiError("demo_workspace_unavailable", "unavailable"),
)

def build_stable_error_index(
    errors: tuple[StableApiError, ...],
) -> dict[str, StableApiError]:
    """Build one exact index and reject duplicate stable codes."""
    index = {error.code: error for error in errors}
    if len(index) != len(errors):
        raise ValueError("stable API error codes must be unique")
    return index


STABLE_API_ERROR_BY_CODE = build_stable_error_index(STABLE_API_ERRORS)

__all__ = [
    "ErrorCategory",
    "STABLE_API_ERRORS",
    "STABLE_API_ERROR_BY_CODE",
    "StableApiError",
    "build_stable_error_index",
]
