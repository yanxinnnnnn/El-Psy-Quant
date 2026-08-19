"""Central sanitized exception translation for the M34 API surface."""

from __future__ import annotations

from http import HTTPStatus
from typing import Literal, NoReturn

from el_psy_quant.api.errors import PublicApiError
from el_psy_quant.persistence.paper_execution_records import (
    PaperExecutionConcurrencyConflictError,
    PaperExecutionCorruptAuthorityError,
    PaperExecutionIdempotencyConflictError,
    PaperExecutionNotFoundError,
    PaperExecutionOperationConflictError,
    PaperExecutionReconciliationRequiredError,
    PaperExecutionStaleAuthorityError,
    PaperExecutionStorageBusyError,
    PaperExecutionStorageFailureError,
)

PaperExecutionApiOperation = Literal[
    "order_create",
    "order_list",
    "order_detail",
    "order_step",
    "attempt_list",
    "attempt_detail",
    "fill_list",
    "fill_detail",
    "reconciliation",
]


class PaperExecutionInvalidPolicyError(Exception):
    """Caller policy selections cannot form the approved v1 policy."""


class PaperExecutionInvalidDecimalError(Exception):
    """Caller quantity or basis-point value is not canonical."""


class PaperExecutionInvalidCursorError(Exception):
    """Caller cursor is not one exact server-produced cursor."""


def _public(status: int, code: str, message: str) -> PublicApiError:
    return PublicApiError(status_code=status, code=code, message=message)


def _authority_unavailable() -> PublicApiError:
    return _public(
        HTTPStatus.SERVICE_UNAVAILABLE,
        "paper_execution_authority_unavailable",
        "Paper Execution authority is unavailable",
    )


def _not_found(operation: PaperExecutionApiOperation) -> PublicApiError:
    if operation == "order_create":
        return _public(
            HTTPStatus.NOT_FOUND,
            "paper_execution_upstream_authority_not_found",
            "Paper Execution upstream authority was not found",
        )
    if operation == "attempt_detail":
        return _public(
            HTTPStatus.NOT_FOUND,
            "paper_execution_attempt_not_found",
            "Paper Execution Attempt was not found",
        )
    if operation == "fill_detail":
        return _public(
            HTTPStatus.NOT_FOUND,
            "paper_execution_fill_not_found",
            "Paper Execution Fill was not found",
        )
    return _public(
        HTTPStatus.NOT_FOUND,
        "paper_execution_order_not_found",
        "Paper Execution Order was not found",
    )


def raise_paper_execution_api_error(
    exc: Exception,
    *,
    operation: PaperExecutionApiOperation,
) -> NoReturn:
    """Raise one fixed public error or preserve an unexpected exception."""
    if isinstance(exc, PaperExecutionNotFoundError):
        error = _not_found(operation)
    elif isinstance(exc, PaperExecutionIdempotencyConflictError):
        error = _public(
            HTTPStatus.CONFLICT,
            "paper_execution_idempotency_conflict",
            "Paper Execution idempotency key conflicts",
        )
    elif isinstance(exc, PaperExecutionStaleAuthorityError):
        error = _public(
            HTTPStatus.CONFLICT,
            "paper_execution_stale_authority",
            "Paper Execution authority is stale",
        )
    elif isinstance(exc, PaperExecutionOperationConflictError):
        error = _public(
            HTTPStatus.CONFLICT,
            "paper_execution_operation_conflict",
            "Paper Execution operation conflicts with current authority",
        )
    elif isinstance(exc, PaperExecutionConcurrencyConflictError):
        error = _public(
            HTTPStatus.CONFLICT,
            "paper_execution_concurrency_conflict",
            "Paper Execution command lost a concurrency race",
        )
    elif isinstance(exc, PaperExecutionReconciliationRequiredError):
        error = _public(
            HTTPStatus.CONFLICT,
            "paper_execution_reconciliation_required",
            "Paper Execution reconciliation is required",
        )
    elif isinstance(exc, PaperExecutionInvalidPolicyError):
        error = _public(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "paper_execution_invalid_policy",
            "Paper Execution policy is invalid",
        )
    elif isinstance(exc, PaperExecutionInvalidDecimalError):
        error = _public(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "paper_execution_invalid_decimal",
            "Paper Execution decimal value is invalid",
        )
    elif isinstance(exc, PaperExecutionInvalidCursorError):
        error = _public(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "paper_execution_invalid_cursor",
            "Paper Execution cursor is invalid",
        )
    elif isinstance(exc, PaperExecutionCorruptAuthorityError):
        error = _authority_unavailable()
    elif isinstance(exc, PaperExecutionStorageBusyError):
        error = _public(
            HTTPStatus.SERVICE_UNAVAILABLE,
            "paper_execution_storage_busy",
            "Paper Execution storage is temporarily unavailable",
        )
    elif isinstance(exc, PaperExecutionStorageFailureError):
        error = _public(
            HTTPStatus.SERVICE_UNAVAILABLE,
            "paper_execution_storage_failure",
            "Paper Execution storage failed",
        )
    else:
        raise exc
    raise error from exc


__all__ = [
    "PaperExecutionApiOperation",
    "PaperExecutionInvalidCursorError",
    "PaperExecutionInvalidDecimalError",
    "PaperExecutionInvalidPolicyError",
    "raise_paper_execution_api_error",
]
