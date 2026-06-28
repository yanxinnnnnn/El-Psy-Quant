"""Deterministic local CSV cache helpers."""

import re
from pathlib import Path

import pandas as pd

from el_psy_quant.data.csv import load_daily_prices_csv

REQUIRED_PRICE_COLUMNS = ("Open", "High", "Low", "Close", "Volume")


def cache_path(cache_dir: str | Path, symbol: str) -> Path:
    """Return the deterministic CSV cache path for ``symbol``."""
    normalized = symbol.strip().upper()
    if not normalized:
        raise ValueError("symbol must not be empty")
    normalized = re.sub(r"[/\\:\s]", "_", normalized)
    return Path(cache_dir) / f"{normalized}.csv"


def write_daily_prices_cache(
    prices: pd.DataFrame,
    cache_dir: str | Path,
    symbol: str,
) -> Path:
    """Validate and write daily prices to a local CSV cache."""
    if prices.empty:
        raise ValueError("prices must not be empty")

    missing = [
        column for column in REQUIRED_PRICE_COLUMNS if column not in prices.columns
    ]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValueError("prices must have a DatetimeIndex")
    if prices.index.has_duplicates:
        raise ValueError("prices index must not contain duplicate dates")
    if prices["Close"].isna().any():
        raise ValueError("Close must not contain NaN values")

    path = cache_path(cache_dir, symbol)
    path.parent.mkdir(parents=True, exist_ok=True)
    prices.sort_index().to_csv(path, index=True, index_label="Date")
    return path


def read_daily_prices_cache(cache_dir: str | Path, symbol: str) -> pd.DataFrame:
    """Read daily prices from a local CSV cache."""
    path = cache_path(cache_dir, symbol)
    if not path.exists():
        raise FileNotFoundError(path)
    return load_daily_prices_csv(path)

