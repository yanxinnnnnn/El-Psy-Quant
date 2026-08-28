"""Sanitized exception translation for the M35 runtime API surface."""

from __future__ import annotations

from http import HTTPStatus
from typing import Literal, NoReturn

from el_psy_quant.api.errors import PublicApiError
from el_psy_quant.application.paper_runtime import (
    PaperRuntimeAlreadyExistsError,
    PaperRuntimeBindingMismatchError,
    PaperRuntimeClaimMismatchError,
    PaperRuntimeControlIdempotencyConflictError,
    PaperRuntimeLeaseExpiredError,
    PaperRuntimeLifecycleConflictError,
    PaperRuntimeOwnershipBusyError,
    PaperRuntimeRunnerStateError,
    PaperRuntimeTerminalContinuationError,
)
from el_psy_quant.persistence.paper_execution_records import (
    PaperExecutionCorruptAuthorityError,
    PaperExecutionReconciliationRequiredError,
    PaperExecutionStaleAuthorityError,
)
from el_psy_quant.persistence.paper_runtime_records import (
    PaperRuntimeConcurrencyConflictError,
    PaperRuntimeNotFoundError,
    PaperRuntimePersistenceCorruptionError,
    PaperRuntimeStorageBusyError,
    PaperRuntimeStorageFailureError,
)

PaperRuntimeApiOperation = Literal[
    "create",
    "list",
    "detail",
    "start",
    "stop",
    "resume",
    "recover",
    "health",
    "reconciliation",
    "audit",
    "work",
    "checkpoints",
]


class PaperRuntimeInvalidCursorError(Exception):
    """A transport cursor is not one exact server-produced value."""


def _public(status: int, code: str, message: str) -> PublicApiError:
    return PublicApiError(status_code=status, code=code, message=message)


def raise_paper_runtime_api_error(
    exc: Exception, *, operation: PaperRuntimeApiOperation
) -> NoReturn:
    """Raise one fixed public error without exposing internal exception material."""

    if isinstance(exc, PaperRuntimeNotFoundError):
        error = _public(
            HTTPStatus.NOT_FOUND,
            "paper_runtime_not_found",
            "Paper Runtime was not found",
        )
    elif isinstance(exc, PaperRuntimeControlIdempotencyConflictError):
        error = _public(
            HTTPStatus.CONFLICT,
            "paper_runtime_idempotency_conflict",
            "Paper Runtime idempotency key conflicts",
        )
    elif isinstance(exc, PaperRuntimeAlreadyExistsError):
        error = _public(
            HTTPStatus.CONFLICT,
            "paper_runtime_already_exists",
            "Paper Runtime already exists for this execution Order",
        )
    elif isinstance(exc, PaperRuntimeBindingMismatchError):
        error = _public(
            HTTPStatus.CONFLICT,
            "paper_runtime_binding_conflict",
            "Paper Runtime binding conflicts with durable authority",
        )
    elif isinstance(
        exc,
        (
            PaperRuntimeLifecycleConflictError,
            PaperRuntimeTerminalContinuationError,
            PaperRuntimeRunnerStateError,
        ),
    ):
        error = _public(
            HTTPStatus.CONFLICT,
            "paper_runtime_lifecycle_conflict",
            "Paper Runtime lifecycle operation conflicts with current authority",
        )
    elif isinstance(exc, PaperRuntimeConcurrencyConflictError):
        error = _public(
            HTTPStatus.CONFLICT,
            "paper_runtime_version_conflict",
            "Paper Runtime version conflicts with current authority",
        )
    elif isinstance(
        exc,
        (
            PaperRuntimeOwnershipBusyError,
            PaperRuntimeClaimMismatchError,
            PaperRuntimeLeaseExpiredError,
        ),
    ):
        error = _public(
            HTTPStatus.CONFLICT,
            "paper_runtime_ownership_conflict",
            "Paper Runtime ownership conflicts with current authority",
        )
    elif isinstance(
        exc,
        (PaperExecutionReconciliationRequiredError, PaperExecutionStaleAuthorityError),
    ):
        error = _public(
            HTTPStatus.CONFLICT,
            "paper_runtime_continuation_stale",
            "Paper Runtime live continuation is stale",
        )
    elif isinstance(exc, PaperRuntimeInvalidCursorError):
        error = _public(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "paper_runtime_invalid_cursor",
            "Paper Runtime cursor is invalid",
        )
    elif isinstance(exc, (TypeError, ValueError)):
        error = _public(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "paper_runtime_invalid_input",
            "Paper Runtime input is invalid",
        )
    elif isinstance(exc, PaperRuntimeStorageBusyError):
        error = _public(
            HTTPStatus.SERVICE_UNAVAILABLE,
            "paper_runtime_storage_busy",
            "Paper Runtime storage is temporarily unavailable",
        )
    elif isinstance(exc, PaperRuntimeStorageFailureError):
        error = _public(
            HTTPStatus.SERVICE_UNAVAILABLE,
            "paper_runtime_storage_failure",
            "Paper Runtime storage failed",
        )
    elif isinstance(
        exc,
        (PaperRuntimePersistenceCorruptionError, PaperExecutionCorruptAuthorityError),
    ):
        error = _public(
            HTTPStatus.SERVICE_UNAVAILABLE,
            "paper_runtime_authority_corrupt",
            "Paper Runtime authority is unavailable",
        )
    else:
        raise exc
    raise error from exc


__all__ = [
    "PaperRuntimeApiOperation",
    "PaperRuntimeInvalidCursorError",
    "raise_paper_runtime_api_error",
]
