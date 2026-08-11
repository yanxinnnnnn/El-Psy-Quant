"""Central sanitized exception translation for the M33 API surface."""

from __future__ import annotations

from http import HTTPStatus
from typing import Literal, NoReturn

from el_psy_quant.api.errors import PublicApiError
from el_psy_quant.application import (
    OrderIntentNotFoundError,
    StrategyOrderCorruptAuthorityError,
    StrategyOrderIdempotencyConflictError,
    StrategyOrderNotFoundError,
    StrategyOrderReconciliationRequiredError,
    StrategyOrderStaleAuthorityError,
    StrategyOrderStorageBusyError,
    StrategyOrderStorageFailureError,
    StrategyOrderUpstreamAuthorityUnavailableError,
    StrategySignalNotFoundError,
)

StrategyOrderApiOperation = Literal[
    "signal_evaluate",
    "signal_list",
    "signal_detail",
    "intent_create",
    "intent_list",
    "intent_detail",
    "decision_create",
    "decision_list",
    "decision_detail",
]


class StrategyOrderInvalidRuntimeConfigurationError(Exception):
    """Caller runtime selection cannot form the approved reference."""


class StrategyOrderInvalidRiskPolicyError(Exception):
    """Caller policy selection cannot form the approved reference."""


class StrategyOrderInvalidDecimalError(Exception):
    """Caller financial value is not an exact supported decimal."""


class StrategyOrderInvalidCursorError(Exception):
    """Caller cursor is not one exact server-produced cursor."""


def _public(status: int, code: str, message: str) -> PublicApiError:
    return PublicApiError(status_code=status, code=code, message=message)


def _authority_unavailable() -> PublicApiError:
    return _public(
        HTTPStatus.SERVICE_UNAVAILABLE,
        "strategy_order_authority_unavailable",
        "Strategy-to-risk authority is unavailable",
    )


def _detail_not_found(operation: StrategyOrderApiOperation) -> PublicApiError:
    if operation == "signal_detail":
        return _public(
            HTTPStatus.NOT_FOUND,
            "strategy_signal_not_found",
            "Strategy Signal was not found",
        )
    if operation == "intent_detail":
        return _public(
            HTTPStatus.NOT_FOUND,
            "order_intent_not_found",
            "Order Intent was not found",
        )
    if operation == "decision_detail":
        return _public(
            HTTPStatus.NOT_FOUND,
            "pre_trade_risk_decision_not_found",
            "Pre-Trade Risk Decision was not found",
        )
    return _authority_unavailable()


def raise_strategy_order_api_error(
    exc: Exception,
    *,
    operation: StrategyOrderApiOperation,
) -> NoReturn:
    """Raise one fixed public error or preserve an unexpected exception."""
    if isinstance(exc, StrategySignalNotFoundError):
        error = _public(
            HTTPStatus.NOT_FOUND,
            "strategy_signal_not_found",
            "Strategy Signal was not found",
        )
    elif isinstance(exc, OrderIntentNotFoundError):
        error = _public(
            HTTPStatus.NOT_FOUND,
            "order_intent_not_found",
            "Order Intent was not found",
        )
    elif isinstance(exc, StrategyOrderUpstreamAuthorityUnavailableError):
        error = _authority_unavailable()
    elif isinstance(exc, StrategyOrderNotFoundError):
        error = _detail_not_found(operation)
    elif isinstance(exc, StrategyOrderIdempotencyConflictError):
        error = _public(
            HTTPStatus.CONFLICT,
            "strategy_order_idempotency_conflict",
            "Strategy-to-risk idempotency key conflicts",
        )
    elif isinstance(exc, StrategyOrderStaleAuthorityError):
        error = _public(
            HTTPStatus.CONFLICT,
            "strategy_order_stale_authority",
            "Strategy-to-risk authority is stale",
        )
    elif isinstance(exc, StrategyOrderReconciliationRequiredError):
        error = _public(
            HTTPStatus.CONFLICT,
            "strategy_order_reconciliation_required",
            "Paper Account reconciliation is required",
        )
    elif isinstance(exc, StrategyOrderInvalidRuntimeConfigurationError):
        error = _public(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "strategy_order_invalid_runtime_configuration",
            "Strategy runtime configuration is invalid",
        )
    elif isinstance(exc, StrategyOrderInvalidRiskPolicyError):
        error = _public(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "strategy_order_invalid_risk_policy",
            "Pre-trade risk policy is invalid",
        )
    elif isinstance(exc, StrategyOrderInvalidDecimalError):
        error = _public(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "strategy_order_invalid_decimal",
            "Strategy-to-risk decimal value is invalid",
        )
    elif isinstance(exc, StrategyOrderInvalidCursorError):
        error = _public(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "strategy_order_invalid_cursor",
            "Strategy-to-risk cursor is invalid",
        )
    elif isinstance(exc, StrategyOrderCorruptAuthorityError):
        error = _authority_unavailable()
    elif isinstance(exc, StrategyOrderStorageBusyError):
        error = _public(
            HTTPStatus.SERVICE_UNAVAILABLE,
            "strategy_order_storage_busy",
            "Strategy-to-risk storage is temporarily unavailable",
        )
    elif isinstance(exc, StrategyOrderStorageFailureError):
        error = _public(
            HTTPStatus.SERVICE_UNAVAILABLE,
            "strategy_order_storage_failure",
            "Strategy-to-risk storage failed",
        )
    else:
        raise exc
    raise error from exc


__all__ = [
    "StrategyOrderApiOperation",
    "StrategyOrderInvalidCursorError",
    "StrategyOrderInvalidDecimalError",
    "StrategyOrderInvalidRiskPolicyError",
    "StrategyOrderInvalidRuntimeConfigurationError",
    "raise_strategy_order_api_error",
]
