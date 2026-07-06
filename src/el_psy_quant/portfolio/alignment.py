"""Deterministic alignment of per-symbol strategy return streams."""

from collections.abc import Mapping

import pandas as pd

from el_psy_quant.data.universe import build_symbol_universe


def align_strategy_returns(
    results_by_symbol: Mapping[str, pd.DataFrame],
    return_column: str = "strategy_return",
) -> pd.DataFrame:
    """Align strategy returns on dates shared by every configured symbol."""
    if not results_by_symbol:
        raise ValueError("results_by_symbol must not be empty")

    symbols = build_symbol_universe(results_by_symbol)
    return_series: list[pd.Series] = []
    for symbol, result in zip(
        symbols,
        results_by_symbol.values(),
        strict=True,
    ):
        if not isinstance(result, pd.DataFrame):
            raise ValueError(f"{symbol} result must be a pandas DataFrame")
        if not isinstance(result.index, pd.DatetimeIndex):
            raise ValueError(f"{symbol} result must have a DatetimeIndex")
        if return_column not in result.columns:
            raise ValueError(f"{symbol} result must contain '{return_column}'")

        returns = result[return_column]
        if not pd.api.types.is_numeric_dtype(returns):
            raise ValueError(f"{symbol} {return_column} must contain numeric values")
        return_series.append(returns.rename(symbol))

    aligned = pd.concat(return_series, axis=1, join="inner")
    if aligned.empty:
        raise ValueError("strategy returns have no shared dates")
    for symbol in symbols:
        if aligned[symbol].isna().any():
            raise ValueError(
                f"{symbol} {return_column} must not contain missing values "
                "on shared dates"
            )
    return aligned
