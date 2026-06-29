"""Compact backtest summaries."""

import pandas as pd

from el_psy_quant.performance.metrics import (
    annualized_volatility,
    cagr,
    max_drawdown,
    sharpe_ratio,
    total_return,
)


def backtest_summary(
    result: pd.DataFrame,
    periods_per_year: int | float | None = None,
    annual_risk_free_rate: float = 0.0,
) -> dict[str, float]:
    """Return a small performance summary from a pipeline result."""
    for column in ("equity", "strategy_return"):
        if column not in result.columns:
            raise ValueError(f"result must contain a {column!r} column")

    if result.empty:
        raise ValueError("result must not be empty")
    if result["equity"].isna().any():
        raise ValueError("equity must not contain NaN values")
    if result["strategy_return"].isna().any():
        raise ValueError("strategy_return must not contain NaN values")

    equity = result["equity"]
    summary = {
        "initial_equity": float(equity.iloc[0]),
        "final_equity": float(equity.iloc[-1]),
        "total_return": total_return(equity),
        "max_drawdown": max_drawdown(equity),
        "periods": float(len(result)),
    }
    if periods_per_year is not None:
        returns_column = (
            "net_strategy_return"
            if "net_strategy_return" in result
            else "strategy_return"
        )
        summary["cagr"] = cagr(equity, periods_per_year)
        summary["annualized_volatility"] = annualized_volatility(
            result[returns_column], periods_per_year
        )
        summary["sharpe_ratio"] = sharpe_ratio(
            result[returns_column], periods_per_year, annual_risk_free_rate
        )
    return summary

