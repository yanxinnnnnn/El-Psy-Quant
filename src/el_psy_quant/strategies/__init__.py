"""Strategy contracts for research pipelines."""

from el_psy_quant.strategies.base import Strategy, validate_strategy_result
from el_psy_quant.strategies.moving_average import MovingAverageCrossoverStrategy

__all__ = [
    "MovingAverageCrossoverStrategy",
    "Strategy",
    "validate_strategy_result",
]
