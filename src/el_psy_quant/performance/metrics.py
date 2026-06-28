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


def cagr(equity: pd.Series, periods_per_year: int | float) -> float:
    """Return compound annual growth using an explicit period frequency."""
    _validate_equity(equity)
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    if len(equity) < 2:
        raise ValueError("equity must contain at least two points")
    if (equity <= 0).any():
        raise ValueError("equity values must be positive")

    years = (len(equity) - 1) / periods_per_year
    return float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1)


def annualized_volatility(
    returns: pd.Series, periods_per_year: int | float
) -> float:
    """Return sample volatility annualized by an explicit period frequency."""
    if returns.empty:
        raise ValueError("returns must not be empty")
    if returns.isna().any():
        raise ValueError("returns must not contain NaN values")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    if len(returns) < 2:
        raise ValueError("returns must contain at least two observations")

    return float(returns.std(ddof=1) * periods_per_year**0.5)

