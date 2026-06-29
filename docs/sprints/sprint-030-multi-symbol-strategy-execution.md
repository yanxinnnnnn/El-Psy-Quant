# Sprint 30 — Multi-Symbol Strategy Execution

## Objective

Add deterministic multi-symbol moving-average crossover strategy execution.

Sprint 29 added local multi-symbol price loading. Sprint 30 should run the existing single-symbol moving-average crossover pipeline independently across multiple symbols.

This sprint should not aggregate results, optimize portfolios, allocate capital, rebalance positions, rank symbols, or produce cross-symbol summaries.

## Product Goal

As the founder, I want to run the existing moving-average crossover research pipeline across multiple symbols, so I can inspect per-symbol strategy results without manually looping in user code.

The target behavior is:

```text
symbol -> prices
  -> run existing single-symbol pipeline per symbol
  -> symbol -> pipeline result
```

Each symbol is independent. There is no portfolio-level capital allocation yet.

## Technical Direction

Extend the backtesting package:

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

- `moving_average_crossover_pipeline`
- Sprint 29 multi-symbol input helpers in user-facing examples, but do not force file loading into this helper.

Keep this deterministic and local-only.

## Implementation Scope

### 1. Add Multi-Symbol Pipeline Runner

Implement:

```python
def moving_average_crossover_multi_symbol(
    prices_by_symbol: Mapping[str, pd.DataFrame],
    fast_window: int,
    slow_window: int,
    initial_capital: float = 1.0,
    transaction_cost_rate: float = 0.0,
    slippage_rate: float = 0.0,
) -> dict[str, pd.DataFrame]:
    ...
```

The function should:

- Accept a mapping from symbol to price DataFrame.
- Reject an empty mapping with `ValueError`.
- Normalize symbols by stripping whitespace and uppercasing.
- Reject empty symbols after stripping.
- Reject duplicate normalized symbols with `ValueError`.
- Require each DataFrame to contain a `Close` column.
- Use `moving_average_crossover_pipeline(prices["Close"], ...)` per symbol.
- Pass through:
  - `fast_window`
  - `slow_window`
  - `initial_capital`
  - `transaction_cost_rate`
  - `slippage_rate`
- Return a plain `dict[str, pd.DataFrame]`.
- Preserve deterministic output order based on input iteration order after normalization.
- Let pipeline validation errors propagate where reasonable.

Example:

```python
from el_psy_quant.backtesting import moving_average_crossover_multi_symbol
from el_psy_quant.data import read_daily_prices_caches

prices_by_symbol = read_daily_prices_caches("data/cache", ["AAPL", "MSFT"])
results_by_symbol = moving_average_crossover_multi_symbol(
    prices_by_symbol,
    fast_window=20,
    slow_window=50,
    initial_capital=1_000.0,
    transaction_cost_rate=0.001,
    slippage_rate=0.0005,
)
```

Expected output keys:

```text
AAPL
MSFT
```

Each value is the same kind of DataFrame returned by the existing single-symbol `moving_average_crossover_pipeline`.

### 2. Export Helper

Export the function from:

```python
el_psy_quant.backtesting
```

Required import:

```python
from el_psy_quant.backtesting import moving_average_crossover_multi_symbol
```

should work.

## Validation Details

Symbol normalization should match Sprint 29 style:

```python
normalized = symbol.strip().upper()
```

Duplicate examples that should raise:

```python
{"AAPL": aapl_prices, " aapl ": other_prices}
```

Missing `Close` examples that should raise:

```python
{"AAPL": pd.DataFrame({"Open": [1, 2]})}
```

Do not align symbols by date in this sprint. Each symbol runs independently on its own price index.

Do not truncate, forward-fill, back-fill, or union/intersect dates across symbols.

## Tests

Add tests covering:

- Runs the moving-average crossover pipeline for multiple symbols.
- Normalizes symbols by stripping whitespace and uppercasing.
- Preserves deterministic output order.
- Each result contains the expected pipeline columns.
- Passes transaction cost and slippage rates into each pipeline run.
- Rejects empty mapping.
- Rejects empty symbol.
- Rejects duplicate normalized symbols.
- Rejects missing `Close` column.
- Propagates invalid pipeline parameters, such as `fast_window >= slow_window`.
- Function is exported from `el_psy_quant.backtesting`.

Use deterministic in-memory DataFrames. No live network calls.

## README Update

Add a short example showing:

```python
from el_psy_quant.backtesting import moving_average_crossover_multi_symbol
from el_psy_quant.data import read_daily_prices_caches

prices_by_symbol = read_daily_prices_caches("data/cache", ["AAPL", "MSFT"])
results_by_symbol = moving_average_crossover_multi_symbol(
    prices_by_symbol,
    fast_window=20,
    slow_window=50,
    initial_capital=1_000.0,
)
```

Briefly state:

- Multi-symbol execution runs each symbol independently.
- It does not allocate capital or build a portfolio yet.
- It does not align dates across symbols yet.

Keep it short.

## Out of Scope

- No cross-symbol summary.
- No portfolio optimization.
- No capital allocation.
- No rebalancing logic.
- No portfolio equity curve.
- No equal-weight portfolio.
- No symbol ranking.
- No benchmark comparison changes.
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
- `uv run python -c "from el_psy_quant.backtesting import moving_average_crossover_multi_symbol"` works.
- README documents the multi-symbol strategy execution helper briefly.
- The implementation stays deterministic, local-only, and network-free.
- The implementation stays small and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 30 scope.
3. Do not introduce cross-symbol summaries, portfolio optimization, capital allocation, rebalancing logic, portfolio equity curves, equal-weight portfolios, symbol ranking, benchmark comparison changes, live downloads, Yahoo provider changes, cache writing changes, CLI commands, charts, dashboards, file exports, databases, cloud features, or broker integration.
4. Keep symbol normalization explicit and consistent with Sprint 29.
5. Reuse the existing single-symbol moving-average crossover pipeline.
6. Keep tests deterministic and network-free.
7. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether each symbol is run independently.
- Whether output shape is easy to inspect.
- Whether symbol normalization is consistent with Sprint 29.
- Whether Codex avoided jumping ahead to cross-symbol summaries or portfolio allocation.
