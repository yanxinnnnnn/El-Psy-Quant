"""Standalone portfolio summaries and machine-readable artifacts."""

import json
from collections.abc import Iterable, Mapping
from numbers import Real
from pathlib import Path

import pandas as pd

from el_psy_quant.data.universe import build_symbol_universe
from el_psy_quant.performance import backtest_summary
from el_psy_quant.portfolio.equity import equity_curve
from el_psy_quant.portfolio.weights import validate_static_weights


def _validate_portfolio_return(
    portfolio_return: pd.Series,
    initial_capital: float,
) -> None:
    if not isinstance(portfolio_return, pd.Series):
        raise ValueError("portfolio_return must be a pandas Series")
    if portfolio_return.empty:
        raise ValueError("portfolio_return must not be empty")
    if not isinstance(portfolio_return.index, pd.DatetimeIndex):
        raise ValueError("portfolio_return must have a DatetimeIndex")
    if not pd.api.types.is_numeric_dtype(portfolio_return):
        raise ValueError("portfolio_return must contain numeric values")
    if portfolio_return.isna().any():
        raise ValueError("portfolio_return must not contain missing values")
    if (
        isinstance(initial_capital, bool)
        or not isinstance(initial_capital, Real)
        or initial_capital <= 0
    ):
        raise ValueError("initial_capital must be positive")


def summarize_portfolio_return(
    portfolio_return: pd.Series,
    initial_capital: float = 1.0,
    periods_per_year: int | float | None = None,
    annual_risk_free_rate: float = 0.0,
) -> dict[str, float]:
    """Summarize a standalone portfolio return series with existing metrics."""
    _validate_portfolio_return(portfolio_return, initial_capital)
    result = pd.DataFrame(
        {
            "strategy_return": portfolio_return,
            "equity": equity_curve(portfolio_return, float(initial_capital)),
        },
        index=portfolio_return.index,
    )
    summary = backtest_summary(
        result,
        periods_per_year=periods_per_year,
        annual_risk_free_rate=annual_risk_free_rate,
    )
    return {name: float(value) for name, value in summary.items()}


def build_portfolio_summary_artifact(
    portfolio_return: pd.Series,
    *,
    construction_method: str,
    symbols: Iterable[str],
    weights: Mapping[str, float] | None = None,
    initial_capital: float = 1.0,
    periods_per_year: int | float | None = None,
    annual_risk_free_rate: float = 0.0,
) -> dict[str, object]:
    """Build a versioned, JSON-compatible standalone portfolio artifact."""
    normalized_symbols = build_symbol_universe(symbols)
    serialized_weights: dict[str, float] | None = None
    if weights is not None:
        validated_weights = validate_static_weights(normalized_symbols, weights)
        serialized_weights = {
            symbol: float(value) for symbol, value in validated_weights.items()
        }

    metrics = summarize_portfolio_return(
        portfolio_return,
        initial_capital=initial_capital,
        periods_per_year=periods_per_year,
        annual_risk_free_rate=annual_risk_free_rate,
    )
    return {
        "schema_version": 1,
        "construction": {
            "method": construction_method,
            "symbols": list(normalized_symbols),
            "weights": serialized_weights,
        },
        "evaluation": {
            "initial_capital": float(initial_capital),
            "periods_per_year": (
                None if periods_per_year is None else float(periods_per_year)
            ),
            "annual_risk_free_rate": float(annual_risk_free_rate),
        },
        "metrics": metrics,
    }


def write_portfolio_summary_artifact(
    artifact: Mapping[str, object],
    path: str | Path,
) -> Path:
    """Write a standalone portfolio summary artifact as deterministic JSON."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path
