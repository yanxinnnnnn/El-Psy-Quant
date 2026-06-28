"""Simple transaction cost calculations."""

import pandas as pd


def transaction_cost(position: pd.Series, cost_rate: float) -> pd.Series:
    """Return the cost drag caused by long-only position turnover."""
    if cost_rate < 0:
        raise ValueError("cost_rate must not be negative")
    if position.isna().any():
        raise ValueError("position must not contain NaN values")
    if not position.isin([0, 1]).all():
        raise ValueError("position values must be 0 or 1")

    turnover = position.astype(float).diff().abs()
    if not turnover.empty:
        turnover.iloc[0] = abs(float(position.iloc[0]))
    return turnover * cost_rate
