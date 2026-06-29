"""Local benchmark comparison helpers."""

from pathlib import Path

import pandas as pd

from el_psy_quant.data import load_daily_prices_csv
from el_psy_quant.performance import backtest_summary
from el_psy_quant.portfolio import equity_curve


def compare_to_buy_and_hold_benchmark(
    result: pd.DataFrame,
    benchmark_path: str | Path,
    initial_capital: float = 1.0,
    periods_per_year: int | float | None = None,
    annual_risk_free_rate: float = 0.0,
) -> dict[str, float]:
    """Compare a strategy result with an aligned local buy-and-hold benchmark."""
    if result.empty:
        raise ValueError("result must not be empty")
    if "equity" not in result:
        raise ValueError("result must contain an 'equity' column")
    if "net_strategy_return" in result:
        returns_column = "net_strategy_return"
    elif "strategy_return" in result:
        returns_column = "strategy_return"
    else:
        raise ValueError(
            "result must contain 'net_strategy_return' or 'strategy_return'"
        )
    if initial_capital <= 0:
        raise ValueError("initial_capital must be positive")

    benchmark_close = load_daily_prices_csv(benchmark_path)["Close"]
    shared_index = result.index.intersection(benchmark_close.index, sort=False)
    if len(shared_index) < 2:
        raise ValueError("strategy and benchmark must have at least two aligned rows")

    strategy_result = pd.DataFrame(
        {
            "equity": result.loc[shared_index, "equity"],
            "strategy_return": result.loc[shared_index, returns_column],
        },
        index=shared_index,
    )
    benchmark_return = benchmark_close.loc[shared_index].pct_change().fillna(0.0)
    benchmark_result = pd.DataFrame(
        {
            "equity": equity_curve(benchmark_return, initial_capital),
            "strategy_return": benchmark_return,
        },
        index=shared_index,
    )
    summary_args = {
        "periods_per_year": periods_per_year,
        "annual_risk_free_rate": annual_risk_free_rate,
    }
    strategy_summary = backtest_summary(strategy_result, **summary_args)
    benchmark_summary = backtest_summary(benchmark_result, **summary_args)

    comparison = {
        **{f"strategy_{key}": value for key, value in strategy_summary.items()},
        **{f"benchmark_{key}": value for key, value in benchmark_summary.items()},
        "excess_total_return": (
            strategy_summary["total_return"] - benchmark_summary["total_return"]
        ),
        "excess_final_equity": (
            strategy_summary["final_equity"] - benchmark_summary["final_equity"]
        ),
    }
    if periods_per_year is not None:
        comparison["excess_cagr"] = (
            strategy_summary["cagr"] - benchmark_summary["cagr"]
        )
        comparison["excess_sharpe_ratio"] = (
            strategy_summary["sharpe_ratio"]
            - benchmark_summary["sharpe_ratio"]
        )
    return comparison
