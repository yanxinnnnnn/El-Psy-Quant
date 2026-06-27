"""Local CSV market data loading."""

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = ("Date", "Open", "High", "Low", "Close", "Volume")


def load_daily_prices_csv(path: str | Path) -> pd.DataFrame:
    """Load and validate daily prices from a local CSV file."""
    prices = pd.read_csv(path)

    missing = [column for column in REQUIRED_COLUMNS if column not in prices.columns]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")

    try:
        dates = pd.to_datetime(prices["Date"], errors="raise")
    except (TypeError, ValueError) as exc:
        raise ValueError("Date contains invalid values") from exc

    prices = prices.drop(columns="Date")
    prices.index = pd.DatetimeIndex(dates, name="Date")

    if prices.index.has_duplicates:
        raise ValueError("Date contains duplicate values")
    if prices["Close"].isna().any():
        raise ValueError("Close must not contain NaN values")

    return prices.sort_index()

