"""Compact backtest summaries."""

import pandas as pd

from el_psy_quant.performance.metrics import max_drawdown, total_return


def backtest_summary(result: pd.DataFrame) -> dict[str, float]:
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
    return {
        "initial_equity": float(equity.iloc[0]),
        "final_equity": float(equity.iloc[-1]),
        "total_return": total_return(equity),
        "max_drawdown": max_drawdown(equity),
        "periods": float(len(result)),
    }

