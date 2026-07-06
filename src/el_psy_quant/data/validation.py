"""Reusable structural validation for loaded daily price data."""

from collections.abc import Mapping

import pandas as pd

from el_psy_quant.data.universe import build_symbol_universe

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


def validate_daily_prices_by_symbol(
    prices_by_symbol: Mapping[str, pd.DataFrame],
) -> tuple[str, ...]:
    """Validate an ordered map of configured local price inputs."""
    symbols = build_symbol_universe(prices_by_symbol)
    for symbol, prices in zip(
        symbols,
        prices_by_symbol.values(),
        strict=True,
    ):
        try:
            validate_daily_prices(prices)
        except ValueError as error:
            raise ValueError(f"{symbol} price data invalid: {error}") from error
    return symbols
