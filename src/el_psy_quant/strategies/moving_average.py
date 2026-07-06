"""Moving-average crossover adapter for the strategy contract."""

from collections.abc import Mapping
from typing import cast

import pandas as pd

from el_psy_quant.backtesting import moving_average_crossover_pipeline
from el_psy_quant.strategies.base import validate_strategy_result


class MovingAverageCrossoverStrategy:
    """Adapt the existing moving-average pipeline to the strategy contract."""

    name = "moving_average_crossover"

    def run(
        self,
        prices: pd.DataFrame,
        parameters: Mapping[str, object],
    ) -> pd.DataFrame:
        """Run the existing pipeline and return its result unchanged."""
        if "Close" not in prices.columns:
            raise ValueError("prices must contain a 'Close' column")

        result = moving_average_crossover_pipeline(
            prices["Close"],
            fast_window=cast(int, parameters["fast_window"]),
            slow_window=cast(int, parameters["slow_window"]),
            initial_capital=cast(float, parameters.get("initial_capital", 1.0)),
            transaction_cost_rate=cast(
                float,
                parameters.get("transaction_cost_rate", 0.0),
            ),
            slippage_rate=cast(float, parameters.get("slippage_rate", 0.0)),
        )
        validate_strategy_result(result)
        return result
