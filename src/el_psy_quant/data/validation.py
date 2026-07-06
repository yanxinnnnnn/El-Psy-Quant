"""Reusable structural validation for loaded daily price data."""

import pandas as pd

REQUIRED_PRICE_COLUMNS = ("Open", "High", "Low", "Close", "Volume")


def validate_daily_prices(prices: pd.DataFrame) -> None:
    """Validate daily price structure without changing the input."""
    if not isinstance(prices, pd.DataFrame):
        raise ValueError("prices must be a pandas DataFrame")
    if prices.empty:
        raise ValueError("prices must not be empty")

    missing = [
        column for column in REQUIRED_PRICE_COLUMNS if column not in prices.columns
    ]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValueError("prices must have a DatetimeIndex")
    if prices.index.isna().any():
        raise ValueError("prices index must not contain missing dates")
    if prices.index.has_duplicates:
        raise ValueError("prices index must not contain duplicate dates")
    if prices["Close"].isna().any():
        raise ValueError("Close must not contain NaN values")
    if not pd.api.types.is_numeric_dtype(prices["Close"]):
        raise ValueError("Close must contain numeric values")
