"""Deterministic local CSV cache helpers."""

import re
from pathlib import Path

import pandas as pd

from el_psy_quant.data.csv import load_daily_prices_csv
from el_psy_quant.data.validation import validate_daily_prices


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
    validate_daily_prices(prices)

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
