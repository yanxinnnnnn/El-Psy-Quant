"""Deterministic local multi-symbol price loading."""

from collections.abc import Iterable, Mapping
from pathlib import Path

import pandas as pd

from el_psy_quant.data.cache import read_daily_prices_cache
from el_psy_quant.data.csv import load_daily_prices_csv


def _normalize_symbols(symbols: Iterable[str]) -> list[str]:
    normalized_symbols: list[str] = []
    seen: set[str] = set()
    for symbol in symbols:
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("symbol must not be empty")
        if normalized in seen:
            raise ValueError(f"duplicate symbol: {normalized}")
        seen.add(normalized)
        normalized_symbols.append(normalized)
    return normalized_symbols


def load_daily_prices_csvs(
    paths_by_symbol: Mapping[str, str | Path],
) -> dict[str, pd.DataFrame]:
    """Load local daily-price CSV files keyed by normalized symbol."""
    if not paths_by_symbol:
        raise ValueError("paths_by_symbol must not be empty")

    normalized_symbols = _normalize_symbols(paths_by_symbol)
    return {
        symbol: load_daily_prices_csv(path)
        for symbol, path in zip(
            normalized_symbols, paths_by_symbol.values(), strict=True
        )
    }


def read_daily_prices_caches(
    cache_dir: str | Path,
    symbols: Iterable[str],
) -> dict[str, pd.DataFrame]:
    """Read local daily-price caches keyed by normalized symbol."""
    normalized_symbols = _normalize_symbols(symbols)
    if not normalized_symbols:
        raise ValueError("symbols must not be empty")
    return {
        symbol: read_daily_prices_cache(cache_dir, symbol)
        for symbol in normalized_symbols
    }
