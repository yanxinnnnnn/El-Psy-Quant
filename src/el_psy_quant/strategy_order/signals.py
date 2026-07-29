"""Immutable Strategy Signal evidence and compact signal references."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import cast

from el_psy_quant.paper_account import PaperQuantity
from el_psy_quant.strategy_order._canonical import (
    canonical_digest,
    normalize_utc_datetime,
    reject_public_construction,
    validate_digest,
)
from el_psy_quant.strategy_order.market_references import (
    StrategySignalMarketReference,
    _clone_strategy_signal_market_reference,
    validate_strategy_signal_market_reference,
)
from el_psy_quant.strategy_order.runtime import (
    TARGET_POSITION_QUANTITY,
    StrategyRuntimeReference,
    _clone_strategy_runtime_reference,
    validate_strategy_runtime_reference,
)
from el_psy_quant.strategy_order.signal_commands import (
    EvaluateStrategySignalCommand,
    validate_evaluate_strategy_signal_command,
)

STRATEGY_SIGNAL_SCHEMA_VERSION = 1
STRATEGY_SIGNAL_REFERENCE_SCHEMA_VERSION = 1


def _exact_quantity(value: object) -> PaperQuantity:
    if type(value) is not PaperQuantity:
        raise ValueError("target_position_quantity must be PaperQuantity")
    try:
        rebuilt = PaperQuantity.parse(value.canonical)
    except (AttributeError, ValueError) as exc:
        raise ValueError(
            "target_position_quantity must be a valid PaperQuantity"
        ) from exc
    if rebuilt != value:
        raise ValueError(
            "target_position_quantity must be a valid PaperQuantity"
        )
    return rebuilt


def _signal_payload_without_identity(
    *,
    schema_version: int,
    strategy_runtime_reference: StrategyRuntimeReference,
    market_reference: StrategySignalMarketReference,
    target_semantics: str,
    target_position_quantity: PaperQuantity,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "strategy_runtime_reference": strategy_runtime_reference.to_dict(),
        "market_reference": market_reference.to_dict(),
        "target_semantics": target_semantics,
        "target_position_quantity": (
            target_position_quantity.to_json_value()
        ),
    }


@dataclass(frozen=True, init=False)
class StrategySignal:
    """Immutable deterministic evidence of one advisory recommendation."""

    schema_version: int
    signal_id: str
    signal_digest: str
    strategy_runtime_reference: StrategyRuntimeReference
    market_reference: StrategySignalMarketReference
    target_semantics: str
    target_position_quantity: PaperQuantity
    created_at: datetime

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return the complete deterministic JSON-compatible signal."""
        return {
            "schema_version": self.schema_version,
            "signal_id": self.signal_id,
            "signal_digest": self.signal_digest,
            "strategy_runtime_reference": (
                self.strategy_runtime_reference.to_dict()
            ),
            "market_reference": self.market_reference.to_dict(),
            "target_semantics": self.target_semantics,
            "target_position_quantity": (
                self.target_position_quantity.to_json_value()
            ),
            "created_at": self.created_at.isoformat(),
        }


def _create_strategy_signal_from_evaluation(
    *,
    command: EvaluateStrategySignalCommand,
    target_position_quantity: PaperQuantity,
    created_at: datetime,
) -> StrategySignal:
    """Trusted internal S199 boundary from evaluated target to Signal."""
    validate_evaluate_strategy_signal_command(command)
    target = _exact_quantity(target_position_quantity)
    configured_value = command.strategy_runtime_reference.parameters[
        "target_position_quantity"
    ]
    configured = PaperQuantity.parse(cast(str, configured_value))
    if target.decimal_value < 0:
        raise ValueError("target_position_quantity must be non-negative")
    if target not in (PaperQuantity.parse("0"), configured):
        raise ValueError(
            "target_position_quantity must be zero or the configured quantity"
        )
    normalized_created_at = normalize_utc_datetime(
        created_at,
        field_name="created_at",
    )
    runtime_snapshot = _clone_strategy_runtime_reference(
        command.strategy_runtime_reference
    )
    market_snapshot = _clone_strategy_signal_market_reference(
        command.market_reference
    )
    payload = _signal_payload_without_identity(
        schema_version=STRATEGY_SIGNAL_SCHEMA_VERSION,
        strategy_runtime_reference=runtime_snapshot,
        market_reference=market_snapshot,
        target_semantics=TARGET_POSITION_QUANTITY,
        target_position_quantity=target,
    )
    digest = canonical_digest(payload)
    result = object.__new__(StrategySignal)
    object.__setattr__(
        result,
        "schema_version",
        STRATEGY_SIGNAL_SCHEMA_VERSION,
    )
    object.__setattr__(result, "signal_id", f"sig_{digest}")
    object.__setattr__(result, "signal_digest", digest)
    object.__setattr__(
        result,
        "strategy_runtime_reference",
        runtime_snapshot,
    )
    object.__setattr__(result, "market_reference", market_snapshot)
    object.__setattr__(
        result,
        "target_semantics",
        TARGET_POSITION_QUANTITY,
    )
    object.__setattr__(result, "target_position_quantity", target)
    object.__setattr__(result, "created_at", normalized_created_at)
    return result


def validate_strategy_signal(value: object) -> StrategySignal:
    """Recompute and verify one complete immutable Strategy Signal."""
    if type(value) is not StrategySignal:
        raise ValueError("signal must be a StrategySignal")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != STRATEGY_SIGNAL_SCHEMA_VERSION
        ):
            raise ValueError("unsupported strategy signal schema_version")
        validate_strategy_runtime_reference(
            value.strategy_runtime_reference
        )
        validate_strategy_signal_market_reference(value.market_reference)
        if value.target_semantics != TARGET_POSITION_QUANTITY:
            raise ValueError("unsupported target semantics")
        target = _exact_quantity(value.target_position_quantity)
        configured_value = value.strategy_runtime_reference.parameters[
            "target_position_quantity"
        ]
        configured = PaperQuantity.parse(cast(str, configured_value))
        if target not in (PaperQuantity.parse("0"), configured):
            raise ValueError("invalid target quantity")
        normalized_created_at = normalize_utc_datetime(
            value.created_at,
            field_name="created_at",
        )
        if normalized_created_at != value.created_at:
            raise ValueError("created_at must be normalized to UTC")
        payload = _signal_payload_without_identity(
            schema_version=value.schema_version,
            strategy_runtime_reference=value.strategy_runtime_reference,
            market_reference=value.market_reference,
            target_semantics=value.target_semantics,
            target_position_quantity=target,
        )
        digest = canonical_digest(payload)
        validate_digest(value.signal_digest, field_name="signal_digest")
        if value.signal_digest != digest or value.signal_id != f"sig_{digest}":
            raise ValueError("signal identity does not match content")
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError("strategy signal is invalid") from exc
    return value


@dataclass(frozen=True, init=False)
class StrategySignalReference:
    """Compact immutable pointer to a complete validated Strategy Signal."""

    schema_version: int
    signal_id: str
    signal_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return only the minimum deterministic signal anchor."""
        return {
            "schema_version": self.schema_version,
            "signal_id": self.signal_id,
            "signal_digest": self.signal_digest,
        }


def create_strategy_signal_reference(
    signal: StrategySignal,
) -> StrategySignalReference:
    """Create a compact reference from one complete valid signal."""
    validate_strategy_signal(signal)
    result = object.__new__(StrategySignalReference)
    object.__setattr__(
        result,
        "schema_version",
        STRATEGY_SIGNAL_REFERENCE_SCHEMA_VERSION,
    )
    object.__setattr__(result, "signal_id", signal.signal_id)
    object.__setattr__(result, "signal_digest", signal.signal_digest)
    return result


def validate_strategy_signal_reference(
    value: object,
) -> StrategySignalReference:
    """Validate the self-consistency of one compact signal reference."""
    if type(value) is not StrategySignalReference:
        raise ValueError("signal_reference must be a StrategySignalReference")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != STRATEGY_SIGNAL_REFERENCE_SCHEMA_VERSION
        ):
            raise ValueError("unsupported signal-reference schema_version")
        digest = validate_digest(
            value.signal_digest,
            field_name="signal_digest",
        )
        if value.signal_id != f"sig_{digest}":
            raise ValueError("signal_id must match signal_digest")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("strategy signal reference is invalid") from exc
    return value
