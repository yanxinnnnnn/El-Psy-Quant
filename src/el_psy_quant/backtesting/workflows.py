"""Convenience workflows for local backtesting research."""

from pathlib import Path

import pandas as pd

from el_psy_quant.backtesting.pipelines import moving_average_crossover_pipeline
from el_psy_quant.data import load_daily_prices_csv
from el_psy_quant.performance import backtest_summary


def moving_average_crossover_from_csv(
    path: str | Path,
    fast_window: int,
    slow_window: int,
    initial_capital: float = 1.0,
    transaction_cost_rate: float = 0.0,
    slippage_rate: float = 0.0,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Run the moving-average crossover research flow from a local CSV."""
    prices = load_daily_prices_csv(path)
    result = moving_average_crossover_pipeline(
        prices["Close"],
        fast_window,
        slow_window,
        initial_capital,
        transaction_cost_rate,
        slippage_rate,
    )
    return result, backtest_summary(result)
