"""Trend and return indicators."""

import pandas as pd


def simple_moving_average(series: pd.Series, window: int) -> pd.Series:
    """Return the rolling arithmetic mean over ``window`` observations."""
    if window <= 0:
        raise ValueError("window must be positive")

    return series.rolling(window=window).mean()


def exponential_moving_average(series: pd.Series, span: int) -> pd.Series:
    """Return the exponentially weighted mean using ``span``."""
    if span <= 0:
        raise ValueError("span must be positive")

    return series.ewm(span=span, adjust=False).mean()


def daily_return(series: pd.Series) -> pd.Series:
    """Return the percentage change from the previous observation."""
    return series.pct_change(fill_method=None)

