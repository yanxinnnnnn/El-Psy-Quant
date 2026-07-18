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
        "/api/v1/lifecycle-transition-proposals",
        "lifecycle.propose",
    ),
    ApiOperation(
        "POST",
        "/api/v1/lifecycle-transition-records",
        "lifecycle.review",
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
    "log_paper_job_command_completed",
    "log_paper_job_execution_terminal",
    "resolve_api_operation",
]
