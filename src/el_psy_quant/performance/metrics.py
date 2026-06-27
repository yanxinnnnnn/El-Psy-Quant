"""Basic performance metrics."""

import pandas as pd


def _validate_equity(equity: pd.Series) -> None:
    if equity.empty:
        raise ValueError("equity must not be empty")
    if equity.isna().any():
        raise ValueError("equity must not contain NaN values")


def total_return(equity: pd.Series) -> float:
    """Return the percentage change from the first to final equity value."""
    _validate_equity(equity)
    if equity.iloc[0] <= 0:
        raise ValueError("starting equity must be positive")

    return float(equity.iloc[-1] / equity.iloc[0] - 1.0)


def max_drawdown(equity: pd.Series) -> float:
    """Return the worst percentage decline from a running equity peak."""
    _validate_equity(equity)
    if (equity <= 0).any():
        raise ValueError("equity values must be positive")

    running_peak = equity.cummax()
    drawdown = equity / running_peak - 1.0
    return float(drawdown.min())

