# Sprint 31 — Cross-Symbol Summary

## Objective

Add deterministic cross-symbol summary helpers for multi-symbol strategy results.

Sprint 29 added local multi-symbol price loading. Sprint 30 added independent multi-symbol moving-average crossover execution. Sprint 31 should summarize those per-symbol pipeline results into a compact table.

This sprint should not allocate capital, build a portfolio equity curve, rebalance positions, rank symbols by a trading decision rule, or optimize portfolios.

## Product Goal

As the founder, I want to turn multi-symbol strategy results into one summary table, so I can inspect and compare per-symbol performance without manually looping in user code.

The target behavior is:

```text
symbol -> pipeline result
  -> symbol-level backtest summary per result
  -> DataFrame with one row per symbol
```

Each symbol remains independent. The summary is comparison output, not a portfolio.

## Technical Direction

Extend the existing backtesting multi-symbol area:

```text
src/
└── el_psy_quant/
    └── backtesting/
        ├── __init__.py
        ├── benchmarks.py
        ├── experiments.py
        ├── multi.py
        ├── pipelines.py
        ├── trades.py
        └── workflows.py

tests/
└── test_backtesting_multi.py
```

Reuse existing functions where possible:

- `backtest_summary`
- `moving_average_crossover_multi_symbol`

Keep this deterministic and local-only.

## Implementation Scope

### 1. Add Cross-Symbol Summary Helper

Implement:

```python
def summarize_multi_symbol_results(
    results_by_symbol: Mapping[str, pd.DataFrame],
    periods_per_year: int | float | None = None,
    annual_risk_free_rate: float = 0.0,
) -> pd.DataFrame:
    ...
```

The function should:

- Accept a mapping from symbol to pipeline result DataFrame.
- Reject an empty mapping with `ValueError`.
- Normalize symbols by stripping whitespace and uppercasing.
- Reject empty symbols after stripping.
- Reject duplicate normalized symbols with `ValueError`.
- Summarize each result with `backtest_summary`.
- Pass through optional `periods_per_year` and `annual_risk_free_rate`.
- Return a `pd.DataFrame` with one row per symbol.
- Preserve deterministic row order based on input iteration order after normalization.
- Let `backtest_summary` validation errors propagate where reasonable.

Required base output columns:

```text
symbol
initial_equity
final_equity
total_return
max_drawdown
periods
```

When `periods_per_year` is provided, also include:

```text
cagr
annualized_volatility
sharpe_ratio
```

Do not sort by performance. Preserve input order.

### 2. Export Helper

Export the function from:

```python
el_psy_quant.backtesting
```

Required import:

```python
from el_psy_quant.backtesting import summarize_multi_symbol_results
```

should work.

## Validation Details

Symbol normalization should match Sprint 29 and Sprint 30 style:

```python
normalized = symbol.strip().upper()
```

Duplicate examples that should raise:

```python
{"AAPL": result, " aapl ": other_result}
```

Do not align dates across symbols in this sprint.
Do not truncate, forward-fill, back-fill, union, or intersect dates across symbols.
Each result should be summarized independently.

## Example Usage

```python
from el_psy_quant.backtesting import (
    moving_average_crossover_multi_symbol,
    summarize_multi_symbol_results,
)
from el_psy_quant.data import read_daily_prices_caches

prices_by_symbol = read_daily_prices_caches("data/cache", ["AAPL", "MSFT"])
results_by_symbol = moving_average_crossover_multi_symbol(
    prices_by_symbol,
    fast_window=20,
    slow_window=50,
    initial_capital=1_000.0,
)
summary = summarize_multi_symbol_results(
    results_by_symbol,
    periods_per_year=252,
    annual_risk_free_rate=0.02,
)
```

## Tests

Add tests covering:

- Summarizes multiple pipeline results into one DataFrame.
- Normalizes symbols by stripping whitespace and uppercasing.
- Preserves deterministic row order.
- Base output includes:
  - `symbol`
  - `initial_equity`
  - `final_equity`
  - `total_return`
  - `max_drawdown`
  - `periods`
- Annualized output includes:
  - `cagr`
  - `annualized_volatility`
  - `sharpe_ratio`
  when `periods_per_year` is provided.
- Annualized output is not included when `periods_per_year` is omitted.
- Rejects empty mapping.
- Rejects empty symbol.
- Rejects duplicate normalized symbols.
- Propagates invalid result errors from `backtest_summary`.
- Function is exported from `el_psy_quant.backtesting`.

Use deterministic in-memory DataFrames. No live network calls.

## README Update

Add a short example showing:

```python
from el_psy_quant.backtesting import summarize_multi_symbol_results

summary = summarize_multi_symbol_results(
    results_by_symbol,
    periods_per_year=252,
    annual_risk_free_rate=0.02,
)
```

Briefly state:

- Cross-symbol summary compares independent per-symbol results.
- It does not build a portfolio or allocate capital.
- It does not align dates across symbols.

Keep it short.

## Out of Scope

- No portfolio optimization.
- No capital allocation.
- No rebalancing logic.
- No portfolio equity curve.
- No equal-weight portfolio.
- No benchmark comparison changes.
- No symbol ranking for trading decisions.
- No top-N selection.
- No multi-symbol trade record aggregation.
- No date alignment across symbols.
- No live downloads.
- No Yahoo provider changes.
- No cache writing changes.
- No CLI.
- No charts.
- No dashboards.
- No file export.
- No database.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.backtesting import summarize_multi_symbol_results"` works.
- README documents the cross-symbol summary helper briefly.
- The implementation stays deterministic, local-only, and network-free.
- The implementation stays small and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 31 scope.
3. Do not introduce portfolio optimization, capital allocation, rebalancing logic, portfolio equity curves, equal-weight portfolios, benchmark comparison changes, symbol ranking for trading decisions, top-N selection, multi-symbol trade record aggregation, date alignment across symbols, live downloads, Yahoo provider changes, cache writing changes, CLI commands, charts, dashboards, file exports, databases, cloud features, or broker integration.
4. Keep symbol normalization explicit and consistent with Sprint 29 and Sprint 30.
5. Reuse `backtest_summary`.
6. Keep tests deterministic and network-free.
7. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether each symbol is summarized independently.
- Whether row order is deterministic.
- Whether output columns are easy to inspect.
- Whether Codex avoided jumping ahead to portfolio construction or allocation.
