"""Versioned strategy-runtime references for M33 signal evaluation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import cast

from el_psy_quant.paper_account import PaperQuantity
from el_psy_quant.strategy_order._canonical import (
    canonical_digest,
    reject_public_construction,
)

STRATEGY_RUNTIME_REFERENCE_SCHEMA_VERSION = 1

MOVING_AVERAGE_CROSSOVER_STRATEGY_NAME = "moving_average_crossover"
MOVING_AVERAGE_CROSSOVER_STRATEGY_VERSION = "v1"
MOVING_AVERAGE_CROSSOVER_ADAPTER_VERSION = "v1"
TARGET_POSITION_QUANTITY = "target_position_quantity"

_RUNTIME_PARAMETER_FIELDS = frozenset(
    {"fast_window", "slow_window", "target_position_quantity"}
)


def _supported_exact_value(
    value: object,
    *,
    field_name: str,
    supported: str,
) -> str:
    if not isinstance(value, str) or value != supported:
        raise ValueError(f"{field_name} must be {supported}")
    return value


def _window(value: object, *, field_name: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _positive_quantity(value: object) -> PaperQuantity:
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
    if rebuilt.decimal_value <= 0:
        raise ValueError("target_position_quantity must be strictly positive")
    return rebuilt


@dataclass(frozen=True, init=False)
class StrategyRuntimeReference:
    """One immutable, explicit runtime-strategy configuration reference."""

    schema_version: int
    strategy_name: str
    strategy_version: str
    adapter_version: str
    runtime_sizing_semantics: str
    parameters_digest: str
    reference_digest: str
    _parameters_json: str = field(repr=False)

    __init__ = reject_public_construction

    @property
    def parameters(self) -> dict[str, object]:
        """Return an isolated JSON-compatible parameter snapshot."""
        return cast(dict[str, object], json.loads(self._parameters_json))

    def to_dict(self) -> dict[str, object]:
        """Return the complete deterministic JSON-compatible reference."""
        return {
            "schema_version": self.schema_version,
            "strategy_name": self.strategy_name,
            "strategy_version": self.strategy_version,
            "adapter_version": self.adapter_version,
            "runtime_sizing_semantics": self.runtime_sizing_semantics,
            "parameters": self.parameters,
            "parameters_digest": self.parameters_digest,
            "reference_digest": self.reference_digest,
        }


def _runtime_payload_without_digest(
    *,
    schema_version: int,
    strategy_name: str,
    strategy_version: str,
    adapter_version: str,
    runtime_sizing_semantics: str,
    parameters: dict[str, object],
    parameters_digest: str,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "strategy_name": strategy_name,
        "strategy_version": strategy_version,
        "adapter_version": adapter_version,
        "runtime_sizing_semantics": runtime_sizing_semantics,
        "parameters": dict(parameters),
        "parameters_digest": parameters_digest,
    }


def create_moving_average_crossover_runtime_reference(
    *,
    fast_window: int,
    slow_window: int,
    target_position_quantity: PaperQuantity,
    schema_version: int = STRATEGY_RUNTIME_REFERENCE_SCHEMA_VERSION,
    strategy_name: str = MOVING_AVERAGE_CROSSOVER_STRATEGY_NAME,
    strategy_version: str = MOVING_AVERAGE_CROSSOVER_STRATEGY_VERSION,
    adapter_version: str = MOVING_AVERAGE_CROSSOVER_ADAPTER_VERSION,
    runtime_sizing_semantics: str = TARGET_POSITION_QUANTITY,
) -> StrategyRuntimeReference:
    """Create the only runtime-reference configuration approved for S198."""
    if (
        type(schema_version) is not int
        or schema_version != STRATEGY_RUNTIME_REFERENCE_SCHEMA_VERSION
    ):
        raise ValueError(
            f"unsupported strategy runtime schema_version: {schema_version}"
        )
    normalized_name = _supported_exact_value(
        strategy_name,
        field_name="strategy_name",
        supported=MOVING_AVERAGE_CROSSOVER_STRATEGY_NAME,
    )
    normalized_strategy_version = _supported_exact_value(
        strategy_version,
        field_name="strategy_version",
        supported=MOVING_AVERAGE_CROSSOVER_STRATEGY_VERSION,
    )
    normalized_adapter_version = _supported_exact_value(
        adapter_version,
        field_name="adapter_version",
        supported=MOVING_AVERAGE_CROSSOVER_ADAPTER_VERSION,
    )
    normalized_semantics = _supported_exact_value(
        runtime_sizing_semantics,
        field_name="runtime_sizing_semantics",
        supported=TARGET_POSITION_QUANTITY,
    )
    normalized_fast = _window(fast_window, field_name="fast_window")
    normalized_slow = _window(slow_window, field_name="slow_window")
    if normalized_fast >= normalized_slow:
        raise ValueError("fast_window must be less than slow_window")
    normalized_quantity = _positive_quantity(target_position_quantity)

    parameters: dict[str, object] = {
        "fast_window": normalized_fast,
        "slow_window": normalized_slow,
        "target_position_quantity": normalized_quantity.to_json_value(),
    }
    parameters_digest = canonical_digest(parameters)
    reference_payload = _runtime_payload_without_digest(
        schema_version=schema_version,
        strategy_name=normalized_name,
        strategy_version=normalized_strategy_version,
        adapter_version=normalized_adapter_version,
        runtime_sizing_semantics=normalized_semantics,
        parameters=parameters,
        parameters_digest=parameters_digest,
    )

    result = object.__new__(StrategyRuntimeReference)
    object.__setattr__(result, "schema_version", schema_version)
    object.__setattr__(result, "strategy_name", normalized_name)
    object.__setattr__(
        result,
        "strategy_version",
        normalized_strategy_version,
    )
    object.__setattr__(result, "adapter_version", normalized_adapter_version)
    object.__setattr__(
        result,
        "runtime_sizing_semantics",
        normalized_semantics,
    )
    object.__setattr__(
        result,
        "_parameters_json",
        json.dumps(
            parameters,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ),
    )
    object.__setattr__(result, "parameters_digest", parameters_digest)
    object.__setattr__(
        result,
        "reference_digest",
        canonical_digest(reference_payload),
    )
    return result


def validate_strategy_runtime_reference(
    value: object,
) -> StrategyRuntimeReference:
    """Recompute and verify one complete runtime reference."""
    if type(value) is not StrategyRuntimeReference:
        raise ValueError(
            "strategy_runtime_reference must be a StrategyRuntimeReference"
        )
    try:
        parameters = value.parameters
        if set(parameters) != _RUNTIME_PARAMETER_FIELDS:
            raise ValueError("runtime reference parameters are invalid")
        quantity_value = parameters["target_position_quantity"]
        if not isinstance(quantity_value, str):
            raise ValueError("runtime reference quantity is invalid")
        rebuilt = create_moving_average_crossover_runtime_reference(
            fast_window=cast(int, parameters["fast_window"]),
            slow_window=cast(int, parameters["slow_window"]),
            target_position_quantity=PaperQuantity.parse(quantity_value),
            schema_version=value.schema_version,
            strategy_name=value.strategy_name,
            strategy_version=value.strategy_version,
            adapter_version=value.adapter_version,
            runtime_sizing_semantics=value.runtime_sizing_semantics,
        )
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError("strategy runtime reference is invalid") from exc
    if rebuilt != value or rebuilt.to_dict() != value.to_dict():
        raise ValueError("strategy runtime reference is invalid")
    return value


def _clone_strategy_runtime_reference(
    value: StrategyRuntimeReference,
) -> StrategyRuntimeReference:
    validate_strategy_runtime_reference(value)
    parameters = value.parameters
    quantity = cast(str, parameters["target_position_quantity"])
    return create_moving_average_crossover_runtime_reference(
        fast_window=cast(int, parameters["fast_window"]),
        slow_window=cast(int, parameters["slow_window"]),
        target_position_quantity=PaperQuantity.parse(quantity),
        schema_version=value.schema_version,
        strategy_name=value.strategy_name,
        strategy_version=value.strategy_version,
        adapter_version=value.adapter_version,
        runtime_sizing_semantics=value.runtime_sizing_semantics,
    )
