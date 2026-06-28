"""Composable research pipelines."""

import pandas as pd

from el_psy_quant.indicators import daily_return, simple_moving_average
from el_psy_quant.portfolio import (
    equity_curve,
    long_only_position,
    slippage_cost,
    strategy_return,
    transaction_cost,
)
from el_psy_quant.signals import crossover_signal


def moving_average_crossover_pipeline(
    close: pd.Series,
    fast_window: int,
    slow_window: int,
    initial_capital: float = 1.0,
    transaction_cost_rate: float = 0.0,
    slippage_rate: float = 0.0,
) -> pd.DataFrame:
    """Compose the single-asset moving-average crossover research pipeline."""
    if fast_window >= slow_window:
        raise ValueError("fast_window must be less than slow_window")
    if close.isna().any():
        raise ValueError("close must not contain NaN values")

    fast_sma = simple_moving_average(close, fast_window)
    slow_sma = simple_moving_average(close, slow_window)
    signal = crossover_signal(fast_sma, slow_sma)
    position = long_only_position(signal)
    asset_return = daily_return(close)
    returns = strategy_return(position, asset_return)
    costs = transaction_cost(position, transaction_cost_rate)
    slippage = slippage_cost(position, slippage_rate)
    net_returns = returns - costs - slippage
    equity = equity_curve(net_returns, initial_capital)

    return pd.DataFrame(
        {
            "close": close,
            "fast_sma": fast_sma,
            "slow_sma": slow_sma,
            "signal": signal,
            "position": position,
            "asset_return": asset_return,
            "strategy_return": returns,
            "transaction_cost": costs,
            "slippage": slippage,
            "net_strategy_return": net_returns,
            "equity": equity,
        },
        index=close.index,
    )

