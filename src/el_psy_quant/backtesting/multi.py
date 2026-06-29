"""Deterministic multi-symbol strategy execution."""

from collections.abc import Mapping

import pandas as pd

from el_psy_quant.backtesting.pipelines import moving_average_crossover_pipeline
from el_psy_quant.performance import backtest_summary


def moving_average_crossover_multi_symbol(
    prices_by_symbol: Mapping[str, pd.DataFrame],
    fast_window: int,
    slow_window: int,
    initial_capital: float = 1.0,
    transaction_cost_rate: float = 0.0,
    slippage_rate: float = 0.0,
) -> dict[str, pd.DataFrame]:
    """Run the moving-average crossover pipeline independently per symbol."""
    if not prices_by_symbol:
        raise ValueError("prices_by_symbol must not be empty")

    normalized_symbols: list[str] = []
    seen: set[str] = set()
    for symbol in prices_by_symbol:
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("symbol must not be empty")
        if normalized in seen:
            raise ValueError(f"duplicate symbol: {normalized}")
        seen.add(normalized)
        normalized_symbols.append(normalized)

    results: dict[str, pd.DataFrame] = {}
    for normalized, prices in zip(
        normalized_symbols, prices_by_symbol.values(), strict=True
    ):
        if "Close" not in prices.columns:
            raise ValueError(f"prices for {normalized} must contain a Close column")

        results[normalized] = moving_average_crossover_pipeline(
            prices["Close"],
            fast_window=fast_window,
            slow_window=slow_window,
            initial_capital=initial_capital,
            transaction_cost_rate=transaction_cost_rate,
            slippage_rate=slippage_rate,
        )

    return results


def summarize_multi_symbol_results(
    results_by_symbol: Mapping[str, pd.DataFrame],
    periods_per_year: int | float | None = None,
    annual_risk_free_rate: float = 0.0,
) -> pd.DataFrame:
    """Summarize independent per-symbol pipeline results in input order."""
    if not results_by_symbol:
        raise ValueError("results_by_symbol must not be empty")

    normalized_symbols: list[str] = []
    seen: set[str] = set()
    for symbol in results_by_symbol:
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("symbol must not be empty")
        if normalized in seen:
            raise ValueError(f"duplicate symbol: {normalized}")
        seen.add(normalized)
        normalized_symbols.append(normalized)

    rows = [
        {
            "symbol": symbol,
            **backtest_summary(
                result,
                periods_per_year=periods_per_year,
                annual_risk_free_rate=annual_risk_free_rate,
            ),
        }
        for symbol, result in zip(
            normalized_symbols, results_by_symbol.values(), strict=True
        )
    ]
    return pd.DataFrame(rows)
