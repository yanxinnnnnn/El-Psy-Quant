"""Typed durable M33 persistence records and sanitized failures."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Generic, Literal, TypeVar

from el_psy_quant.strategy_order import (
    OrderIntent,
    OrderIntentNoAction,
    PreTradeRiskDecision,
    StrategySignal,
)

STRATEGY_ORDER_PERSISTENCE_RECORD_SCHEMA_VERSION = 1
STRATEGY_ORDER_LIST_LIMIT_MAXIMUM = 200

COMMAND_NAMESPACE_EVALUATE_SIGNAL = "evaluate_strategy_signal"
COMMAND_NAMESPACE_DERIVE_INTENT = "derive_order_intent"
COMMAND_NAMESPACE_EVALUATE_RISK = "evaluate_pre_trade_risk"
SUPPORTED_STRATEGY_ORDER_COMMAND_NAMESPACES = (
    COMMAND_NAMESPACE_EVALUATE_SIGNAL,
    COMMAND_NAMESPACE_DERIVE_INTENT,
    COMMAND_NAMESPACE_EVALUATE_RISK,
)

RESULT_KIND_SIGNAL = "strategy_signal"
RESULT_KIND_INTENT = "order_intent"
RESULT_KIND_NO_ACTION = "order_intent_no_action"
RESULT_KIND_DECISION = "pre_trade_risk_decision"
SUPPORTED_STRATEGY_ORDER_RESULT_KINDS = (
    RESULT_KIND_SIGNAL,
    RESULT_KIND_INTENT,
    RESULT_KIND_NO_ACTION,
    RESULT_KIND_DECISION,
)

StrategyOrderCommandNamespace = Literal[
    "evaluate_strategy_signal",
    "derive_order_intent",
    "evaluate_pre_trade_risk",
]
StrategyOrderResultKind = Literal[
    "strategy_signal",
    "order_intent",
    "order_intent_no_action",
    "pre_trade_risk_decision",
]
StrategyOrderResult = (
    StrategySignal | OrderIntent | OrderIntentNoAction | PreTradeRiskDecision
)


class StrategyOrderNotFoundError(Exception):
    """Requested durable authority does not exist."""


class StrategyOrderIdempotencyConflictError(Exception):
    """A scoped idempotency key already owns another command."""


class StrategyOrderStaleAuthorityError(Exception):
    """Expected M31/M32 authority no longer matches current authority."""


class StrategyOrderReconciliationRequiredError(Exception):
    """The Paper Account projection is not verified current."""


class StrategyOrderCorruptAuthorityError(Exception):
    """Durable authority is incomplete, incompatible, or corrupt."""


class StrategyOrderStorageBusyError(Exception):
    """SQLite could not grant the bounded write transaction."""


class StrategyOrderStorageFailureError(Exception):
    """Durable storage failed without exposing implementation details."""


def _bounded_string(value: object, field: str, maximum: int) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or len(value) > maximum
    ):
        raise ValueError(f"{field} is invalid")
    return value


def _digest(value: object, field: str) -> str:
    result = _bounded_string(value, field, 64)
    if len(result) != 64 or any(c not in "0123456789abcdef" for c in result):
        raise ValueError(f"{field} is invalid")
    return result


def _utc(value: object, field: str) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise ValueError(f"{field} is invalid")
    normalized = value.astimezone(timezone.utc)
    if normalized != value:
        raise ValueError(f"{field} is invalid")
    return normalized


def _reject_constant(_value: str) -> None:
    raise ValueError("non-finite JSON is invalid")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON keys are invalid")
        result[key] = value
    return result


def canonical_json(value: object) -> str:
    """Serialize using the one merged M33 canonical JSON rule."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def load_canonical_json(payload: object) -> object:
    """Load strict canonical JSON, rejecting duplicates and alternate encodings."""
    if type(payload) is not str:
        raise StrategyOrderCorruptAuthorityError()
    try:
        value = json.loads(
            payload,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
        if canonical_json(value) != payload:
            raise ValueError("payload is not canonical")
        return value
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise StrategyOrderCorruptAuthorityError() from exc


@dataclass(frozen=True)
class StrategyOrderCommandReceipt:
    """One validated append-only command-to-result mapping."""

    namespace: StrategyOrderCommandNamespace
    command_idempotency_key: str
    command_digest: str
    command_actor: str
    result_kind: StrategyOrderResultKind
    result_id: str
    result_digest: str
    result_payload_json: str | None
    created_at: datetime
    record_schema_version: int = STRATEGY_ORDER_PERSISTENCE_RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.record_schema_version != 1:
            raise ValueError("unsupported command receipt schema")
        if self.namespace not in SUPPORTED_STRATEGY_ORDER_COMMAND_NAMESPACES:
            raise ValueError("unsupported command namespace")
        _bounded_string(self.command_idempotency_key, "command key", 128)
        _digest(self.command_digest, "command digest")
        _bounded_string(self.command_actor, "command actor", 256)
        if self.result_kind not in SUPPORTED_STRATEGY_ORDER_RESULT_KINDS:
            raise ValueError("unsupported result kind")
        _bounded_string(self.result_id, "result ID", 96)
        _digest(self.result_digest, "result digest")
        _utc(self.created_at, "created_at")
        if (self.result_payload_json is None) != (
            self.result_kind != RESULT_KIND_NO_ACTION
        ):
            raise ValueError("receipt payload does not match result kind")
        if self.result_payload_json is not None:
            load_canonical_json(self.result_payload_json)


T = TypeVar("T")


@dataclass(frozen=True)
class StrategyOrderPage(Generic[T]):
    """One bounded deterministic keyset page."""

    items: tuple[T, ...]
    has_more: bool

    def __post_init__(self) -> None:
        if type(self.items) is not tuple or type(self.has_more) is not bool:
            raise ValueError("invalid strategy-order page")


@dataclass(frozen=True)
class StrategyOrderStoredResult(Generic[T]):
    """One exact persisted result and whether the command was replayed."""

    result: T
    replayed: bool

    def __post_init__(self) -> None:
        if type(self.replayed) is not bool:
            raise ValueError("replayed must be bool")


__all__ = [
    "COMMAND_NAMESPACE_DERIVE_INTENT",
    "COMMAND_NAMESPACE_EVALUATE_RISK",
    "COMMAND_NAMESPACE_EVALUATE_SIGNAL",
    "RESULT_KIND_DECISION",
    "RESULT_KIND_INTENT",
    "RESULT_KIND_NO_ACTION",
    "RESULT_KIND_SIGNAL",
    "STRATEGY_ORDER_LIST_LIMIT_MAXIMUM",
    "STRATEGY_ORDER_PERSISTENCE_RECORD_SCHEMA_VERSION",
    "SUPPORTED_STRATEGY_ORDER_COMMAND_NAMESPACES",
    "SUPPORTED_STRATEGY_ORDER_RESULT_KINDS",
    "StrategyOrderCommandNamespace",
    "StrategyOrderCommandReceipt",
    "StrategyOrderCorruptAuthorityError",
    "StrategyOrderIdempotencyConflictError",
    "StrategyOrderNotFoundError",
    "StrategyOrderPage",
    "StrategyOrderReconciliationRequiredError",
    "StrategyOrderResult",
    "StrategyOrderResultKind",
    "StrategyOrderStaleAuthorityError",
    "StrategyOrderStorageBusyError",
    "StrategyOrderStorageFailureError",
    "StrategyOrderStoredResult",
    "canonical_json",
    "load_canonical_json",
]
