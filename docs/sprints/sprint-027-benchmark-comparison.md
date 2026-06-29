# Sprint 27 — Benchmark Comparison

## Objective

Add a simple benchmark comparison workflow using local CSV input.

Sprint 25 added annualized return and volatility. Sprint 26 added Sharpe-style evaluation. Sprint 27 should compare a strategy result against a basic buy-and-hold benchmark so strategy performance is evaluated with context.

This sprint should not add alpha/beta, information ratio, factor models, rolling benchmark analysis, charts, dashboards, or multi-asset research.

## Product Goal

As the founder, I want to compare a strategy pipeline result against a benchmark CSV file, so I can see whether the strategy did better or worse than a simple buy-and-hold baseline over the same dates.

The target behavior is:

```text
strategy pipeline result + benchmark CSV
  -> aligned strategy and benchmark periods
  -> strategy summary
  -> benchmark buy-and-hold summary
  -> comparison deltas
```

Benchmark assumptions must stay explicit and simple.

## Technical Direction

Add a small benchmark helper under the backtesting package:

```text
src/
└── el_psy_quant/
    └── backtesting/
        ├── __init__.py
        ├── benchmarks.py
        ├── experiments.py
        ├── pipelines.py
        ├── trades.py
        └── workflows.py

tests/
└── test_backtesting_benchmarks.py
```

Reuse existing functions where possible:

- `load_daily_prices_csv`
- `equity_curve`
- `backtest_summary`

Keep this deterministic and local-only.

## Implementation Scope

### 1. Add Benchmark Comparison Helper

Implement:

```python
def compare_to_buy_and_hold_benchmark(
    result: pd.DataFrame,
    benchmark_path: str | Path,
    initial_capital: float = 1.0,
    periods_per_year: int | float | None = None,
    annual_risk_free_rate: float = 0.0,
) -> dict[str, float]:
    ...
```

The function should:

- Accept a strategy pipeline result DataFrame.
- Accept a local benchmark CSV path as `str` or `Path`.
- Load benchmark prices using `load_daily_prices_csv(benchmark_path)`.
- Use benchmark `Close` prices.
- Align the strategy result and benchmark prices by shared index values.
- Require at least two aligned rows.
- Use the strategy result's `equity` and return column over the aligned dates.
- Prefer `net_strategy_return` when present.
- Fall back to `strategy_return` when `net_strategy_return` is not present.
- Build benchmark buy-and-hold returns from aligned benchmark close prices:

```python
benchmark_return = benchmark_close.pct_change().fillna(0.0)
benchmark_equity = equity_curve(benchmark_return, initial_capital)
```

- Summarize both strategy and benchmark using `backtest_summary`.
- When `periods_per_year` is provided, include annualized metrics and Sharpe for both strategy and benchmark.
- Return a flat dictionary.

### 2. Required Output Keys

Base output keys should include:

```text
strategy_initial_equity
strategy_final_equity
strategy_total_return
strategy_max_drawdown
strategy_periods
benchmark_initial_equity
benchmark_final_equity
benchmark_total_return
benchmark_max_drawdown
benchmark_periods
excess_total_return
excess_final_equity
```

Where:

```text
excess_total_return = strategy_total_return - benchmark_total_return
excess_final_equity = strategy_final_equity - benchmark_final_equity
```

When `periods_per_year` is provided, also include:

```text
strategy_cagr
strategy_annualized_volatility
strategy_sharpe_ratio
benchmark_cagr
benchmark_annualized_volatility
benchmark_sharpe_ratio
excess_cagr
excess_sharpe_ratio
```

Where:

```text
excess_cagr = strategy_cagr - benchmark_cagr
excess_sharpe_ratio = strategy_sharpe_ratio - benchmark_sharpe_ratio
```

### 3. Validation

The function should raise `ValueError` if:

- `result` is empty.
- `result` is missing `equity`.
- `result` is missing both `net_strategy_return` and `strategy_return`.
- There are fewer than two aligned benchmark/strategy rows.
- The benchmark CSV is invalid according to existing CSV loader validation.
- `initial_capital <= 0`.

Do not silently forward-fill or back-fill benchmark data.
Do not compare non-overlapping dates.
Do not align by row number.

### 4. Export

Export the function from:

```python
el_psy_quant.backtesting
```

## Example Usage

```python
from el_psy_quant.backtesting import compare_to_buy_and_hold_benchmark

comparison = compare_to_buy_and_hold_benchmark(
    result,
    "data/cache/SPY.csv",
    initial_capital=1_000.0,
    periods_per_year=252,
    annual_risk_free_rate=0.02,
)

print(comparison)
```

## Tests

Add tests covering:

- The function returns strategy, benchmark, and excess base metrics.
- It aligns strategy and benchmark by shared index values, not by row number.
- It requires at least two aligned rows.
- It uses `net_strategy_return` when present.
- It falls back to `strategy_return` when `net_strategy_return` is absent.
- It calculates benchmark buy-and-hold equity from benchmark close returns.
- It includes annualized metrics when `periods_per_year` is provided.
- It does not include annualized metrics when `periods_per_year` is omitted.
- It rejects missing strategy `equity`.
- It rejects missing strategy return columns.
- It rejects empty strategy result.
- It rejects non-positive `initial_capital`.
- It propagates benchmark CSV validation errors.
- Function is exported from `el_psy_quant.backtesting`.

Use deterministic temporary CSV files. No live network calls.

## README Update

Add a short example showing:

```python
from el_psy_quant.backtesting import compare_to_buy_and_hold_benchmark

comparison = compare_to_buy_and_hold_benchmark(
    result,
    "data/cache/SPY.csv",
    initial_capital=1_000.0,
    periods_per_year=252,
    annual_risk_free_rate=0.02,
)
```

Briefly state:

- Benchmark comparison uses a local CSV file.
- Benchmark performance is simple buy-and-hold over aligned dates.
- Outperformance claims should be made carefully.

Keep it short. Do not turn README into an attribution report.

## Out of Scope

- No alpha or beta.
- No information ratio.
- No tracking error.
- No factor models.
- No rolling benchmark comparison.
- No monthly/yearly benchmark breakdown.
- No benchmark charts.
- No dashboard.
- No CLI.
- No file export.
- No multi-benchmark support.
- No multi-asset portfolio research.
- No benchmark download workflow.
- No live download changes.
- No pipeline changes.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.backtesting import compare_to_buy_and_hold_benchmark"` works.
- README documents the benchmark comparison helper briefly.
- The implementation stays deterministic, local-only, and network-free.
- The implementation stays small and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 27 scope.
3. Do not introduce alpha, beta, information ratio, tracking error, factor models, rolling benchmark comparison, monthly/yearly benchmark breakdown, charts, dashboards, CLI commands, file exports, multi-benchmark support, multi-asset portfolio research, benchmark downloads, live download changes, cloud features, or broker integration.
4. Align strategy and benchmark by shared index values only.
5. Do not forward-fill, back-fill, or align by row number.
6. Reuse existing local CSV, equity, and summary helpers.
7. Keep tests deterministic and network-free.
8. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether benchmark comparison is aligned by date.
- Whether benchmark logic is clearly buy-and-hold.
- Whether result keys are easy to inspect.
- Whether Codex avoided turning this into attribution, factor, or multi-asset analytics.
