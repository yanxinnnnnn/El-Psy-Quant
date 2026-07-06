"""Deterministic resolution of known strategy names."""

from el_psy_quant.strategies.base import Strategy
from el_psy_quant.strategies.moving_average import MovingAverageCrossoverStrategy

_SUPPORTED_STRATEGY_NAMES = ("moving_average_crossover",)


def supported_strategy_names() -> tuple[str, ...]:
    """Return supported strategy names in deterministic order."""
    return _SUPPORTED_STRATEGY_NAMES


def resolve_strategy(name: str) -> Strategy:
    """Return a fresh strategy for an exact supported name."""
    if name == "moving_average_crossover":
        return MovingAverageCrossoverStrategy()

    supported = ", ".join(_SUPPORTED_STRATEGY_NAMES)
    raise ValueError(f"unknown strategy {name!r}; supported strategies: {supported}")
