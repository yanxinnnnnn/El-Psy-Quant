"""Strategy contracts for research pipelines."""

from el_psy_quant.strategies.base import Strategy, validate_strategy_result
from el_psy_quant.strategies.moving_average import MovingAverageCrossoverStrategy
from el_psy_quant.strategies.resolver import (
    resolve_strategy,
    supported_strategy_names,
)

__all__ = [
    "MovingAverageCrossoverStrategy",
    "Strategy",
    "resolve_strategy",
    "supported_strategy_names",
    "validate_strategy_result",
]
