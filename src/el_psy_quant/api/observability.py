"""Bounded sanitized local product events using standard-library logging only."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal, TypeAlias

from starlette.routing import compile_path

PRODUCT_LOGGER_NAME = "el_psy_quant.product_events"
UVICORN_ERROR_LOGGER_NAME = "uvicorn.error"


def _configured_product_logger() -> logging.Logger:
    """Route bounded INFO events through Uvicorn's existing console handler."""
    logger = logging.getLogger(PRODUCT_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.parent = logging.getLogger(UVICORN_ERROR_LOGGER_NAME)
    logger.propagate = True
    return logger


PRODUCT_LOGGER = _configured_product_logger()
UNMATCHED_OPERATION = "unmatched"
UNMATCHED_ROUTE_TEMPLATE = "unmatched"
MAX_DURATION_MS = 2_147_483_647

PaperJobCommand: TypeAlias = Literal["submit", "run", "cancel", "retry", "recover"]
SubmissionOutcome: TypeAlias = Literal["created", "replayed"]
RecoveryOutcome: TypeAlias = Literal["requeued", "succeeded", "failed"]
PaperExecutionEvent: TypeAlias = Literal[
    "paper_execution_order_created",
    "paper_execution_step_no_fill",
    "paper_execution_fill_created",
    "paper_execution_order_filled",
    "paper_execution_order_rejected",
    "paper_execution_order_partially_filled_rejected",
    "paper_execution_idempotent_replay",
    "paper_execution_stale_authority_refused",
    "paper_execution_corruption_refused",
    "paper_execution_reconciliation_checked",
]
PaperRuntimeEvent: TypeAlias = Literal[
    "paper_runtime_created",
    "paper_runtime_start_requested",
    "paper_runtime_stop_requested",
    "paper_runtime_resume_requested",
    "paper_runtime_recover_requested",
    "paper_runtime_idempotent_replay",
    "paper_runtime_lifecycle_refused",
    "paper_runtime_corruption_refused",
    "paper_runtime_health_checked",
    "paper_runtime_reconciliation_checked",
]


@dataclass(frozen=True)
class ApiOperation:
    """One bounded method/template to internal operation mapping."""

    method: str
    route_template: str
    operation: str


API_OPERATIONS: tuple[ApiOperation, ...] = (
    ApiOperation("GET", "/api/v1/health", "health.read"),
    ApiOperation("GET", "/api/v1/demo-workspace", "demo_workspace.read"),
    ApiOperation("GET", "/api/v1/strategies", "strategy.list"),
    ApiOperation("GET", "/api/v1/strategies/{strategy_name}", "strategy.detail"),
    ApiOperation("GET", "/api/v1/research-runs", "research_run.list"),
    ApiOperation(
        "GET",
        "/api/v1/research-runs/{experiment_slug}/{run_id}",
        "research_run.detail",
    ),
    ApiOperation("GET", "/api/v1/evidence-manifests", "evidence_manifest.list"),
    ApiOperation(
        "GET",
        "/api/v1/evidence-manifests/{manifest_type}/{artifact_key}",
        "evidence_manifest.detail",
    ),
    ApiOperation("POST", "/api/v1/paper-runs", "paper_run.execute"),
    ApiOperation("POST", "/api/v1/paper-jobs", "paper_job.submit"),
    ApiOperation("GET", "/api/v1/paper-jobs", "paper_job.list"),
    ApiOperation("GET", "/api/v1/paper-jobs/{job_id}", "paper_job.detail"),
    ApiOperation(
        "GET",
        "/api/v1/paper-jobs/{job_id}/attempts",
        "paper_job.attempts",
    ),
    ApiOperation("POST", "/api/v1/paper-jobs/{job_id}/run", "paper_job.run"),
    ApiOperation("POST", "/api/v1/paper-jobs/{job_id}/cancel", "paper_job.cancel"),
    ApiOperation("POST", "/api/v1/paper-jobs/{job_id}/retry", "paper_job.retry"),
    ApiOperation("POST", "/api/v1/paper-jobs/{job_id}/recover", "paper_job.recover"),
    ApiOperation("GET", "/api/v1/paper-jobs/{job_id}/result", "paper_job.result"),
    ApiOperation(
        "POST",
        "/api/v1/portfolio-reviews",
        "portfolio_review.create",
    ),
    ApiOperation(
        "GET",
        "/api/v1/portfolio-reviews",
        "portfolio_review.list",
    ),
    ApiOperation(
        "GET",
        "/api/v1/portfolio-reviews/{review_id}",
        "portfolio_review.detail",
    ),
    ApiOperation(
        "POST",
        "/api/v1/portfolio-reviews/{review_id}/decision",
        "portfolio_review.decision",
    ),
    ApiOperation("POST", "/api/v1/paper-accounts", "paper_account.create"),
    ApiOperation("GET", "/api/v1/paper-accounts", "paper_account.list"),
    ApiOperation(
        "GET",
        "/api/v1/paper-accounts/{account_id}",
        "paper_account.detail",
    ),
    ApiOperation(
        "GET",
        "/api/v1/paper-accounts/{account_id}/ledger",
        "paper_account.ledger",
    ),
    ApiOperation(
        "POST",
        "/api/v1/paper-accounts/{account_id}/cash-movements",
        "paper_account.cash_movement",
    ),
    ApiOperation(
        "POST",
        "/api/v1/paper-accounts/{account_id}/position-adjustments",
        "paper_account.position_adjustment",
    ),
    ApiOperation(
        "POST",
        "/api/v1/paper-accounts/{account_id}/evidence-links",
        "paper_account.evidence_link",
    ),
    ApiOperation(
        "POST",
        "/api/v1/paper-accounts/{account_id}/lifecycle",
        "paper_account.lifecycle",
    ),
    ApiOperation(
        "POST",
        "/api/v1/paper-accounts/{account_id}/snapshots",
        "paper_account.snapshot",
    ),
    ApiOperation(
        "POST",
        "/api/v1/paper-accounts/{account_id}/reconciliations",
        "paper_account.reconciliation",
    ),
    ApiOperation(
        "POST",
        "/api/v1/lifecycle-transition-proposals",
        "lifecycle.propose",
    ),
    ApiOperation(
        "POST",
        "/api/v1/lifecycle-transition-records",
        "lifecycle.review",
    ),
    ApiOperation(
        "POST",
        "/api/v1/strategy-signals/evaluate",
        "strategy_signal.evaluate",
    ),
    ApiOperation(
        "GET", "/api/v1/strategy-signals", "strategy_signal.list"
    ),
    ApiOperation(
        "GET",
        "/api/v1/strategy-signals/{signal_id}",
        "strategy_signal.detail",
    ),
    ApiOperation("POST", "/api/v1/order-intents", "order_intent.create"),
    ApiOperation("GET", "/api/v1/order-intents", "order_intent.list"),
    ApiOperation(
        "GET",
        "/api/v1/order-intents/{intent_id}",
        "order_intent.detail",
    ),
    ApiOperation(
        "POST",
        "/api/v1/pre-trade-risk-decisions",
        "pre_trade_risk_decision.create",
    ),
    ApiOperation(
        "GET",
        "/api/v1/pre-trade-risk-decisions",
        "pre_trade_risk_decision.list",
    ),
    ApiOperation(
        "GET",
        "/api/v1/pre-trade-risk-decisions/{decision_id}",
        "pre_trade_risk_decision.detail",
    ),
    ApiOperation(
        "POST", "/api/v1/paper-execution/orders", "paper_execution.order_create"
    ),
    ApiOperation(
        "GET", "/api/v1/paper-execution/orders", "paper_execution.order_list"
    ),
    ApiOperation(
        "GET",
        "/api/v1/paper-execution/orders/{execution_order_id}",
        "paper_execution.order_detail",
    ),
    ApiOperation(
        "POST",
        "/api/v1/paper-execution/orders/{execution_order_id}/steps",
        "paper_execution.order_step",
    ),
    ApiOperation(
        "GET",
        "/api/v1/paper-execution/orders/{execution_order_id}/attempts",
        "paper_execution.attempt_list",
    ),
    ApiOperation(
        "GET",
        "/api/v1/paper-execution/attempts/{attempt_id}",
        "paper_execution.attempt_detail",
    ),
    ApiOperation(
        "GET", "/api/v1/paper-execution/fills", "paper_execution.fill_list"
    ),
    ApiOperation(
        "GET",
        "/api/v1/paper-execution/fills/{fill_id}",
        "paper_execution.fill_detail",
    ),
    ApiOperation(
        "GET",
        "/api/v1/paper-execution/orders/{execution_order_id}/reconciliation",
        "paper_execution.reconciliation",
    ),
    ApiOperation("POST", "/api/v1/paper-runtimes", "paper_runtime.create"),
    ApiOperation("GET", "/api/v1/paper-runtimes", "paper_runtime.list"),
    ApiOperation(
        "GET", "/api/v1/paper-runtimes/{runtime_id}", "paper_runtime.detail"
    ),
    ApiOperation(
        "POST",
        "/api/v1/paper-runtimes/{runtime_id}/start",
        "paper_runtime.start",
    ),
    ApiOperation(
        "POST",
        "/api/v1/paper-runtimes/{runtime_id}/stop",
        "paper_runtime.stop",
    ),
    ApiOperation(
        "POST",
        "/api/v1/paper-runtimes/{runtime_id}/resume",
        "paper_runtime.resume",
    ),
    ApiOperation(
        "POST",
        "/api/v1/paper-runtimes/{runtime_id}/recover",
        "paper_runtime.recover",
    ),
    ApiOperation(
        "GET",
        "/api/v1/paper-runtimes/{runtime_id}/health",
        "paper_runtime.health",
    ),
    ApiOperation(
        "GET",
        "/api/v1/paper-runtimes/{runtime_id}/reconciliation",
        "paper_runtime.reconciliation",
    ),
    ApiOperation(
        "GET",
        "/api/v1/paper-runtimes/{runtime_id}/audit",
        "paper_runtime.audit",
    ),
    ApiOperation(
        "GET",
        "/api/v1/paper-runtimes/{runtime_id}/work",
        "paper_runtime.work",
    ),
    ApiOperation(
        "GET",
        "/api/v1/paper-runtimes/{runtime_id}/checkpoints",
        "paper_runtime.checkpoints",
    ),
)

def build_operation_indexes(
    operations: tuple[ApiOperation, ...],
) -> tuple[dict[tuple[str, str], str], dict[str, set[str]]]:
    """Build bounded indexes and reject duplicate keys or operation names."""
    by_method_and_template = {
        (item.method, item.route_template): item.operation for item in operations
    }
    if len(by_method_and_template) != len(operations):
        raise ValueError("API method and route-template mappings must be unique")
    if len({item.operation for item in operations}) != len(operations):
        raise ValueError("API operation names must be unique")
    by_template: dict[str, set[str]] = {}
    for item in operations:
        by_template.setdefault(item.route_template, set()).add(item.operation)
    return by_method_and_template, by_template


(
    _OPERATION_BY_METHOD_AND_TEMPLATE,
    _OPERATIONS_BY_TEMPLATE,
) = build_operation_indexes(API_OPERATIONS)
_APPROVED_ROUTE_PATTERNS = tuple(
    (template, compile_path(template)[0])
    for template in _OPERATIONS_BY_TEMPLATE
)


def approved_route_template_for_path(path: object) -> str | None:
    """Match a concrete scope path but return only a static approved template."""
    if not isinstance(path, str):
        return None
    for template, pattern in _APPROVED_ROUTE_PATTERNS:
        if pattern.fullmatch(path) is not None:
            return template
    return None


def resolve_api_operation(
    *,
    method: str,
    matched_route_template: object,
) -> tuple[str, str]:
    """Return only approved bounded operation and route-template values."""
    if (
        not isinstance(matched_route_template, str)
        or matched_route_template not in _OPERATIONS_BY_TEMPLATE
    ):
        return UNMATCHED_OPERATION, UNMATCHED_ROUTE_TEMPLATE
    operation = _OPERATION_BY_METHOD_AND_TEMPLATE.get(
        (method, matched_route_template)
    )
    if operation is None:
        candidates = _OPERATIONS_BY_TEMPLATE[matched_route_template]
        operation = next(iter(candidates)) if len(candidates) == 1 else None
    return (
        (operation, matched_route_template)
        if operation is not None
        else (UNMATCHED_OPERATION, matched_route_template)
    )


def request_log_level(status_code: int) -> int:
    if status_code >= 500:
        return logging.ERROR
    if status_code >= 400:
        return logging.WARNING
    return logging.INFO


def bounded_duration_ms(start: float, end: float) -> int:
    """Normalize monotonic timing to one bounded non-negative integer."""
    return min(MAX_DURATION_MS, max(0, int((end - start) * 1000)))


def log_api_request_completed(
    *,
    request_id: str,
    method: str,
    operation: str,
    route_template: str,
    status_code: int,
    duration_ms: int,
    error_code: str | None,
) -> None:
    PRODUCT_LOGGER.log(
        request_log_level(status_code),
        (
            "api_request_completed request_id=%s method=%s operation=%s "
            "route_template=%s status_code=%s duration_ms=%s error_code=%s"
        ),
        request_id,
        method,
        operation,
        route_template,
        status_code,
        duration_ms,
        error_code,
        extra={
            "event": "api_request_completed",
            "request_id": request_id,
            "method": method,
            "operation": operation,
            "route_template": route_template,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "error_code": error_code,
        },
    )


def log_paper_job_command_completed(
    *,
    request_id: str,
    command: PaperJobCommand,
    job_id: str,
    durable_status: str,
    attempt_id: str | None = None,
    attempt_number: int | None = None,
    submission_outcome: SubmissionOutcome | None = None,
    recovery_outcome: RecoveryOutcome | None = None,
) -> None:
    PRODUCT_LOGGER.info(
        (
            "paper_job_command_completed request_id=%s command=%s job_id=%s "
            "durable_status=%s attempt_id=%s attempt_number=%s "
            "submission_outcome=%s recovery_outcome=%s"
        ),
        request_id,
        command,
        job_id,
        durable_status,
        attempt_id,
        attempt_number,
        submission_outcome,
        recovery_outcome,
        extra={
            "event": "paper_job_command_completed",
            "request_id": request_id,
            "command": command,
            "job_id": job_id,
            "durable_status": durable_status,
            "attempt_id": attempt_id,
            "attempt_number": attempt_number,
            "submission_outcome": submission_outcome,
            "recovery_outcome": recovery_outcome,
        },
    )


def log_paper_job_execution_terminal(
    *,
    event: Literal[
        "paper_job_execution_completed",
        "paper_job_execution_failed",
        "paper_job_execution_uncertain",
    ],
    request_id: str,
    job_id: str,
    attempt_id: str,
    attempt_number: int,
    durable_status: str | None,
    error_code: str | None,
) -> None:
    level = (
        logging.INFO
        if event == "paper_job_execution_completed"
        else logging.WARNING
        if event == "paper_job_execution_failed"
        else logging.ERROR
    )
    PRODUCT_LOGGER.log(
        level,
        (
            "%s request_id=%s job_id=%s attempt_id=%s attempt_number=%s "
            "durable_status=%s error_code=%s"
        ),
        event,
        request_id,
        job_id,
        attempt_id,
        attempt_number,
        durable_status,
        error_code,
        extra={
            "event": event,
            "request_id": request_id,
            "job_id": job_id,
            "attempt_id": attempt_id,
            "attempt_number": attempt_number,
            "durable_status": durable_status,
            "error_code": error_code,
        },
    )


def log_portfolio_review_command_completed(
    *,
    event: Literal[
        "portfolio_review_create_completed",
        "portfolio_review_decision_completed",
    ],
    request_id: str,
    command: Literal["create", "decision"],
    review_id: str,
    decision_id: str | None,
    durable_status: str,
    command_outcome: Literal["created", "replayed"],
    human_decision_outcome: str | None,
) -> None:
    """Log only bounded durable portfolio-review command identity."""
    PRODUCT_LOGGER.info(
        (
            "%s request_id=%s command=%s review_id=%s decision_id=%s "
            "durable_status=%s command_outcome=%s human_decision_outcome=%s"
        ),
        event,
        request_id,
        command,
        review_id,
        decision_id,
        durable_status,
        command_outcome,
        human_decision_outcome,
        extra={
            "event": event,
            "request_id": request_id,
            "command": command,
            "review_id": review_id,
            "decision_id": decision_id,
            "durable_status": durable_status,
            "command_outcome": command_outcome,
            "human_decision_outcome": human_decision_outcome,
        },
    )


def log_paper_account_command_completed(
    *,
    operation: Literal[
        "create",
        "cash_movement",
        "position_adjustment",
        "evidence_link",
        "freeze",
        "reactivate",
        "close",
    ],
    request_id: str,
    http_status: int,
    account_id: str,
    event_id: str,
    account_version: int,
    event_type: str,
    replayed: bool,
    projection_status: str,
) -> None:
    """Log only bounded accepted Paper Account command identity."""
    PRODUCT_LOGGER.info(
        (
            "paper_account_command_completed operation=%s request_id=%s "
            "http_status=%s account_id=%s event_id=%s account_version=%s "
            "event_type=%s replayed=%s projection_status=%s"
        ),
        operation,
        request_id,
        http_status,
        account_id,
        event_id,
        account_version,
        event_type,
        replayed,
        projection_status,
        extra={
            "event": "paper_account_command_completed",
            "operation": operation,
            "request_id": request_id,
            "http_status": http_status,
            "account_id": account_id,
            "event_id": event_id,
            "account_version": account_version,
            "event_type": event_type,
            "replayed": replayed,
            "projection_status": projection_status,
        },
    )


def log_paper_account_snapshot_completed(
    *,
    request_id: str,
    http_status: int,
    account_id: str,
    account_version: int,
    snapshot_id: str,
    replayed: bool,
) -> None:
    """Log bounded immutable snapshot operation identity."""
    PRODUCT_LOGGER.info(
        (
            "paper_account_snapshot_completed request_id=%s http_status=%s "
            "account_id=%s account_version=%s snapshot_id=%s replayed=%s"
        ),
        request_id,
        http_status,
        account_id,
        account_version,
        snapshot_id,
        replayed,
        extra={
            "event": "paper_account_snapshot_completed",
            "operation": "snapshot",
            "request_id": request_id,
            "http_status": http_status,
            "account_id": account_id,
            "account_version": account_version,
            "snapshot_id": snapshot_id,
            "replayed": replayed,
        },
    )


def log_paper_account_reconciliation_completed(
    *,
    request_id: str,
    http_status: int,
    account_id: str,
    account_version: int,
    reconciliation_id: str,
    outcome: str,
    replayed: bool,
    projection_status: str,
) -> None:
    """Log bounded immutable reconciliation operation identity."""
    PRODUCT_LOGGER.info(
        (
            "paper_account_reconciliation_completed request_id=%s "
            "http_status=%s account_id=%s account_version=%s "
            "reconciliation_id=%s outcome=%s replayed=%s "
            "projection_status=%s"
        ),
        request_id,
        http_status,
        account_id,
        account_version,
        reconciliation_id,
        outcome,
        replayed,
        projection_status,
        extra={
            "event": "paper_account_reconciliation_completed",
            "operation": "reconciliation",
            "request_id": request_id,
            "http_status": http_status,
            "account_id": account_id,
            "account_version": account_version,
            "reconciliation_id": reconciliation_id,
            "outcome": outcome,
            "replayed": replayed,
            "projection_status": projection_status,
        },
    )


def log_strategy_signal_evaluation_completed(
    *,
    request_id: str,
    http_status: int,
    replayed: bool,
    signal_id: str,
    signal_digest: str,
    replay_id: str,
    instrument_id: str,
) -> None:
    """Log only bounded Signal result identity and immediate anchors."""
    PRODUCT_LOGGER.info(
        (
            "strategy_signal_evaluation_completed request_id=%s "
            "http_status=%s replayed=%s result_kind=strategy_signal "
            "signal_id=%s signal_digest=%s replay_id=%s instrument_id=%s"
        ),
        request_id,
        http_status,
        replayed,
        signal_id,
        signal_digest,
        replay_id,
        instrument_id,
        extra={
            "event": "strategy_signal_evaluation_completed",
            "request_id": request_id,
            "http_status": http_status,
            "replayed": replayed,
            "result_kind": "strategy_signal",
            "signal_id": signal_id,
            "signal_digest": signal_digest,
            "replay_id": replay_id,
            "instrument_id": instrument_id,
        },
    )


def log_order_intent_derivation_completed(
    *,
    request_id: str,
    http_status: int,
    replayed: bool,
    result_kind: Literal["order_intent", "order_intent_no_action"],
    result_id: str,
    result_digest: str,
    signal_id: str,
    account_id: str,
    replay_id: str,
    instrument_id: str,
    side: Literal["buy", "sell"] | None,
    no_action_reason: Literal["target_already_satisfied"] | None,
) -> None:
    """Log bounded Intent/no-action identity without financial values."""
    PRODUCT_LOGGER.info(
        (
            "order_intent_derivation_completed request_id=%s http_status=%s "
            "replayed=%s result_kind=%s result_id=%s result_digest=%s "
            "signal_id=%s account_id=%s replay_id=%s instrument_id=%s "
            "side=%s no_action_reason=%s"
        ),
        request_id,
        http_status,
        replayed,
        result_kind,
        result_id,
        result_digest,
        signal_id,
        account_id,
        replay_id,
        instrument_id,
        side,
        no_action_reason,
        extra={
            "event": "order_intent_derivation_completed",
            "request_id": request_id,
            "http_status": http_status,
            "replayed": replayed,
            "result_kind": result_kind,
            "result_id": result_id,
            "result_digest": result_digest,
            "signal_id": signal_id,
            "account_id": account_id,
            "replay_id": replay_id,
            "instrument_id": instrument_id,
            "side": side,
            "no_action_reason": no_action_reason,
        },
    )


def log_pre_trade_risk_evaluation_completed(
    *,
    request_id: str,
    http_status: int,
    replayed: bool,
    decision_id: str,
    decision_digest: str,
    intent_id: str,
    account_id: str,
    replay_id: str,
    instrument_id: str,
    outcome: Literal["allow", "reject"],
    reason_codes: tuple[str, ...],
) -> None:
    """Log bounded Decision identity, outcome, and closed ordered reasons."""
    PRODUCT_LOGGER.info(
        (
            "pre_trade_risk_evaluation_completed request_id=%s "
            "http_status=%s replayed=%s "
            "result_kind=pre_trade_risk_decision decision_id=%s "
            "decision_digest=%s intent_id=%s account_id=%s replay_id=%s "
            "instrument_id=%s outcome=%s reason_codes=%s"
        ),
        request_id,
        http_status,
        replayed,
        decision_id,
        decision_digest,
        intent_id,
        account_id,
        replay_id,
        instrument_id,
        outcome,
        ",".join(reason_codes),
        extra={
            "event": "pre_trade_risk_evaluation_completed",
            "request_id": request_id,
            "http_status": http_status,
            "replayed": replayed,
            "result_kind": "pre_trade_risk_decision",
            "decision_id": decision_id,
            "decision_digest": decision_digest,
            "intent_id": intent_id,
            "account_id": account_id,
            "replay_id": replay_id,
            "instrument_id": instrument_id,
            "outcome": outcome,
            "reason_codes": reason_codes,
        },
    )


def log_paper_execution_event(
    *,
    event: PaperExecutionEvent,
    request_id: str,
    operation: str,
    http_status: int,
    execution_order_id: str | None = None,
    execution_order_digest: str | None = None,
    attempt_id: str | None = None,
    attempt_digest: str | None = None,
    fill_id: str | None = None,
    fill_digest: str | None = None,
    account_id: str | None = None,
    replay_id: str | None = None,
    instrument_id: str | None = None,
    execution_version: int | None = None,
    attempt_result: str | None = None,
    terminal_reason: str | None = None,
    no_fill_reason: str | None = None,
    replayed: bool | None = None,
) -> None:
    """Emit bounded M34 correlation metadata without financial/request payloads."""
    level = (
        logging.WARNING
        if event
        in {
            "paper_execution_stale_authority_refused",
            "paper_execution_corruption_refused",
        }
        else logging.INFO
    )
    values = {
        "event": event,
        "request_id": request_id,
        "operation": operation,
        "http_status": http_status,
        "execution_order_id": execution_order_id,
        "execution_order_digest": execution_order_digest,
        "attempt_id": attempt_id,
        "attempt_digest": attempt_digest,
        "fill_id": fill_id,
        "fill_digest": fill_digest,
        "account_id": account_id,
        "replay_id": replay_id,
        "instrument_id": instrument_id,
        "execution_version": execution_version,
        "attempt_result": attempt_result,
        "terminal_reason": terminal_reason,
        "no_fill_reason": no_fill_reason,
        "replayed": replayed,
    }
    PRODUCT_LOGGER.log(
        level,
        (
            "%s request_id=%s operation=%s http_status=%s "
            "execution_order_id=%s attempt_id=%s fill_id=%s "
            "execution_version=%s attempt_result=%s terminal_reason=%s "
            "no_fill_reason=%s replayed=%s"
        ),
        event,
        request_id,
        operation,
        http_status,
        execution_order_id,
        attempt_id,
        fill_id,
        execution_version,
        attempt_result,
        terminal_reason,
        no_fill_reason,
        replayed,
        extra=values,
    )


def log_paper_runtime_event(
    *,
    event: PaperRuntimeEvent,
    request_id: str,
    operation: str,
    http_status: int,
    runtime_id: str | None = None,
    desired_state: str | None = None,
    observed_state: str | None = None,
    row_version: int | None = None,
    fencing_token: int | None = None,
    outcome: str | None = None,
    replayed: bool | None = None,
) -> None:
    """Emit bounded M35 operational identity without command or payload data."""

    level = (
        logging.WARNING
        if event in {"paper_runtime_lifecycle_refused", "paper_runtime_corruption_refused"}
        else logging.INFO
    )
    values = {
        "event": event,
        "request_id": request_id,
        "operation": operation,
        "http_status": http_status,
        "runtime_id": runtime_id,
        "desired_state": desired_state,
        "observed_state": observed_state,
        "row_version": row_version,
        "fencing_token": fencing_token,
        "outcome": outcome,
        "replayed": replayed,
    }
    PRODUCT_LOGGER.log(
        level,
        (
            "%s request_id=%s operation=%s http_status=%s runtime_id=%s "
            "desired_state=%s observed_state=%s row_version=%s "
            "fencing_token=%s outcome=%s replayed=%s"
        ),
        event,
        request_id,
        operation,
        http_status,
        runtime_id,
        desired_state,
        observed_state,
        row_version,
        fencing_token,
        outcome,
        replayed,
        extra=values,
    )


__all__ = [
    "API_OPERATIONS",
    "MAX_DURATION_MS",
    "PRODUCT_LOGGER_NAME",
    "UVICORN_ERROR_LOGGER_NAME",
    "UNMATCHED_OPERATION",
    "UNMATCHED_ROUTE_TEMPLATE",
    "approved_route_template_for_path",
    "bounded_duration_ms",
    "build_operation_indexes",
    "log_api_request_completed",
    "log_paper_account_command_completed",
    "log_paper_account_reconciliation_completed",
    "log_paper_account_snapshot_completed",
    "log_order_intent_derivation_completed",
    "log_paper_job_command_completed",
    "log_paper_job_execution_terminal",
    "log_paper_execution_event",
    "log_paper_runtime_event",
    "log_portfolio_review_command_completed",
    "log_pre_trade_risk_evaluation_completed",
    "log_strategy_signal_evaluation_completed",
    "resolve_api_operation",
]
