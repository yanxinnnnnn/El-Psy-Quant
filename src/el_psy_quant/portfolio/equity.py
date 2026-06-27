"""Equity curve calculation."""

import pandas as pd


def equity_curve(
    strategy_return: pd.Series, initial_capital: float = 1.0
) -> pd.Series:
    """Compound periodic strategy returns from ``initial_capital``."""
    if strategy_return.isna().any():
        raise ValueError("strategy_return must not contain NaN values")
    if initial_capital <= 0:
        raise ValueError("initial_capital must be positive")

    return (1.0 + strategy_return.astype(float)).cumprod() * initial_capital

