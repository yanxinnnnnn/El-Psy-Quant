"""Deterministic product read models for built-in strategies."""

from dataclasses import MISSING, dataclass, fields
from typing import Literal

from el_psy_quant.config import MovingAverageCrossoverParameters
from el_psy_quant.strategies import supported_strategy_names

ParameterValueType = Literal["integer", "number"]


@dataclass(frozen=True)
class StrategyParameterDefinition:
    """Descriptive product metadata for one strategy parameter."""

    name: str
    value_type: ParameterValueType
    required: bool
    default: int | float | None


@dataclass(frozen=True)
class StrategySummary:
    """Immutable built-in strategy catalog summary."""

    name: str
    display_name: str
    description: str


@dataclass(frozen=True)
class StrategyDetail:
    """Immutable built-in strategy catalog detail."""

    name: str
    display_name: str
    description: str
    parameters: tuple[StrategyParameterDefinition, ...]


class StrategyNotFoundError(LookupError):
    """Raised when an exact built-in strategy name is not present."""


_MOVING_AVERAGE_DESCRIPTION = (
    "Produces research results from fast and slow moving-average crossover signals."
)

_STRATEGY_METADATA = {
    "moving_average_crossover": (
        "Moving Average Crossover",
        _MOVING_AVERAGE_DESCRIPTION,
    ),
}

_PARAMETER_VALUE_TYPES: dict[str, ParameterValueType] = {
    "fast_window": "integer",
    "slow_window": "integer",
    "initial_capital": "number",
    "transaction_cost_rate": "number",
    "slippage_rate": "number",
}


def _moving_average_parameters() -> tuple[StrategyParameterDefinition, ...]:
    definitions = []
    for field in fields(MovingAverageCrossoverParameters):
        required = field.default is MISSING
        definitions.append(
            StrategyParameterDefinition(
                name=field.name,
                value_type=_PARAMETER_VALUE_TYPES[field.name],
                required=required,
                default=None if required else field.default,
            )
        )
    return tuple(definitions)


def _build_detail(name: str) -> StrategyDetail:
    display_name, description = _STRATEGY_METADATA[name]
    return StrategyDetail(
        name=name,
        display_name=display_name,
        description=description,
        parameters=_moving_average_parameters(),
    )


def list_strategies() -> tuple[StrategySummary, ...]:
    """List built-in strategies in the authoritative domain order."""
    return tuple(
        StrategySummary(
            name=name,
            display_name=_STRATEGY_METADATA[name][0],
            description=_STRATEGY_METADATA[name][1],
        )
        for name in supported_strategy_names()
    )


def get_strategy_detail(name: str) -> StrategyDetail:
    """Return descriptive detail for an exact supported strategy name."""
    if name not in supported_strategy_names():
        raise StrategyNotFoundError("strategy not found")
    return _build_detail(name)
