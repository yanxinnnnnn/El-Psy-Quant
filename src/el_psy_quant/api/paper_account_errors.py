"""Central sanitized Paper Account exception-to-API translation."""

from __future__ import annotations

from http import HTTPStatus
from typing import Literal, NoReturn

from el_psy_quant.api.errors import PublicApiError
from el_psy_quant.persistence.paper_accounts import (
    PaperAccountApprovedEvidenceError,
    PaperAccountClosedError,
    PaperAccountConcurrencyConflictError,
    PaperAccountFrozenError,
    PaperAccountIdempotencyConflictError,
    PaperAccountNotFoundError,
    PaperAccountOperationConflictError,
    PaperAccountPersistenceCorruptionError,
    PaperAccountProjectionReconciliationRequiredError,
    PaperAccountStorageBusyError,
    PaperAccountVersionConflictError,
)

PaperAccountApiOperation = Literal[
    "list",
    "detail",
    "ledger",
    "create",
    "cash_movement",
    "position_adjustment",
    "evidence_link",
    "lifecycle",
    "snapshot",
    "reconciliation",
]


def _public(status: int, code: str, message: str) -> PublicApiError:
    return PublicApiError(
        status_code=status,
        code=code,
        message=message,
    )


def _value_error(
    exc: ValueError,
    *,
    operation: PaperAccountApiOperation,
) -> PublicApiError:
    message = str(exc).lower()
    if any(
        phrase in message
        for phrase in (
            "canonical decimal string",
            "integer digits",
            "fractional digits",
            "signed zero",
        )
    ):
        return _public(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "paper_account_invalid_decimal",
            "Paper Account decimal value is invalid",
        )
    if "cash movement would make cash negative" in message:
        return _public(
            HTTPStatus.CONFLICT,
            "paper_account_insufficient_available_cash",
            "Paper Account has insufficient available cash",
        )
    if "position adjustment would make quantity negative" in message:
        return _public(
            HTTPStatus.CONFLICT,
            "paper_account_negative_position",
            "Paper Account position would become negative",
        )
    if "aggregate cost basis negative" in message:
        return _public(
            HTTPStatus.CONFLICT,
            "paper_account_negative_cost_basis",
            "Paper Account aggregate cost basis would become negative",
        )
    if "zero position quantity requires zero aggregate cost basis" in message:
        return _public(
            HTTPStatus.CONFLICT,
            "paper_account_zero_quantity_nonzero_cost_basis",
            "Zero position quantity requires zero aggregate cost basis",
        )
    if "closing requires" in message:
        return _public(
            HTTPStatus.CONFLICT,
            "paper_account_close_not_empty",
            "Paper Account must be empty before closing",
        )
    if operation == "snapshot":
        return _public(
            HTTPStatus.CONFLICT,
            "paper_account_snapshot_conflict",
            "Paper Account snapshot conflicts with current authority",
        )
    if operation == "reconciliation":
        return _public(
            HTTPStatus.CONFLICT,
            "paper_account_reconciliation_failed",
            "Paper Account reconciliation failed",
        )
    if "approved portfolio-review" in message:
        return _public(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "paper_account_invalid_m30_reference",
            "Approved portfolio-review reference is invalid",
        )
    if "lifecycle transition" in message:
        return _public(
            HTTPStatus.CONFLICT,
            "paper_account_version_conflict",
            "Paper Account lifecycle conflicts with current authority",
        )
    return _public(
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "request_validation_error",
        "Request Validation Error",
    )


def raise_paper_account_api_error(
    exc: Exception,
    *,
    operation: PaperAccountApiOperation,
) -> NoReturn:
    """Raise one stable sanitized error or preserve an unexpected exception."""
    if isinstance(exc, PaperAccountNotFoundError):
        error = _public(
            HTTPStatus.NOT_FOUND,
            "paper_account_not_found",
            "Paper Account was not found",
        )
    elif isinstance(
        exc,
        (
            PaperAccountVersionConflictError,
            PaperAccountConcurrencyConflictError,
        ),
    ):
        error = _public(
            HTTPStatus.CONFLICT,
            "paper_account_version_conflict",
            "Paper Account version conflicts with current authority",
        )
    elif isinstance(exc, PaperAccountIdempotencyConflictError):
        error = _public(
            HTTPStatus.CONFLICT,
            "paper_account_idempotency_conflict",
            "Paper Account idempotency key conflicts",
        )
    elif isinstance(exc, PaperAccountFrozenError):
        error = _public(
            HTTPStatus.CONFLICT,
            "paper_account_frozen",
            "Paper Account is frozen",
        )
    elif isinstance(exc, PaperAccountClosedError):
        error = _public(
            HTTPStatus.CONFLICT,
            "paper_account_closed",
            "Paper Account is closed",
        )
    elif isinstance(exc, PaperAccountApprovedEvidenceError):
        error = _public(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "paper_account_invalid_m30_reference",
            "Approved portfolio-review reference is invalid",
        )
    elif isinstance(
        exc,
        PaperAccountProjectionReconciliationRequiredError,
    ):
        error = _public(
            HTTPStatus.CONFLICT,
            "paper_account_projection_stale",
            "Paper Account projection is not current",
        )
    elif isinstance(exc, PaperAccountOperationConflictError):
        if operation == "snapshot":
            error = _public(
                HTTPStatus.CONFLICT,
                "paper_account_snapshot_conflict",
                "Paper Account snapshot operation conflicts",
            )
        else:
            error = _public(
                HTTPStatus.CONFLICT,
                "paper_account_reconciliation_failed",
                "Paper Account reconciliation operation conflicts",
            )
    elif isinstance(exc, PaperAccountStorageBusyError):
        error = _public(
            HTTPStatus.SERVICE_UNAVAILABLE,
            "paper_account_storage_busy",
            "Paper Account storage is temporarily unavailable",
        )
    elif isinstance(exc, PaperAccountPersistenceCorruptionError):
        error = _public(
            HTTPStatus.SERVICE_UNAVAILABLE,
            "paper_account_schema_incompatible",
            "Paper Account durable authority is unavailable",
        )
    elif isinstance(exc, ValueError):
        error = _value_error(exc, operation=operation)
    else:
        raise exc
    raise error from exc


__all__ = ["PaperAccountApiOperation", "raise_paper_account_api_error"]
