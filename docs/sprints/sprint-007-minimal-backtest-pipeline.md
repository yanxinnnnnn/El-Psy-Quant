# Sprint 7 — Minimal Backtest Pipeline

## Objective

Add the first end-to-end minimal backtest pipeline.

Sprints 1–6 created isolated building blocks. Sprint 7 should connect those blocks into one reusable pipeline for a simple moving-average crossover strategy, without introducing a general-purpose backtesting engine, performance report, charting, or broker integration.

## Product Goal

As the founder, I want a single small function that takes close prices and returns the key research outputs for a moving-average crossover strategy, so we can verify the full platform flow from prices to equity curve.

## Technical Direction

Create a new backtesting module:

```text
src/
└── el_psy_quant/
    └── backtesting/
        ├── __init__.py
        └── pipelines.py

tests/
└── test_backtesting_pipelines.py
```

This module should compose existing functions rather than reimplementing their logic.

## Core Pipeline

The minimal moving-average crossover pipeline should be:

```text
close prices
  -> simple moving averages
  -> crossover signals
  -> long-only positions
  -> daily asset returns
  -> strategy returns
  -> equity curve
```

## Implementation Scope

### Must Have

Implement:

```python
def moving_average_crossover_pipeline(
    close: pd.Series,
    fast_window: int,
    slow_window: int,
    initial_capital: float = 1.0,
) -> pd.DataFrame:
    ...
```

The function should:

- Accept a close-price `pd.Series`.
- Validate that `fast_window > 0` and `slow_window > 0` through the existing indicator functions where possible.
- Raise `ValueError` if `fast_window >= slow_window`.
- Reject NaN close prices with `ValueError`.
- Preserve the input index.
- Return a `pd.DataFrame` with these columns:
  - `close`
  - `fast_sma`
  - `slow_sma`
  - `signal`
  - `position`
  - `asset_return`
  - `strategy_return`
  - `equity`
- Use existing functions:
  - `simple_moving_average`
  - `crossover_signal`
  - `long_only_position`
  - `daily_return`
  - `strategy_return`
  - `equity_curve`
- Keep the pipeline deterministic and network-free.

### Important Timing Rule

This pipeline must preserve the conservative timing already established:

```text
strategy_return[t] = position[t-1] * asset_return[t]
```

Do not use same-day position for same-day return.

### Example Behavior

Given simple close prices and windows:

```text
close = [1, 2, 3, 2, 1, 2, 3]
fast_window = 2
slow_window = 3
```

The function should return a DataFrame containing all intermediate outputs. Exact values should be tested using small deterministic input.

## Tests

Add tests covering:

- The returned DataFrame has the expected columns in the expected order.
- The output index matches the close-price index.
- The pipeline composes existing behavior correctly on a deterministic small input.
- `fast_window >= slow_window` raises `ValueError`.
- NaN close prices raise `ValueError`.
- Custom initial capital is reflected in the equity column.
- The first strategy return is `0.0`.
- No network calls or data provider usage occurs.

## Out of Scope

- No generic backtesting engine class.
- No strategy classes.
- No performance metrics.
- No CAGR.
- No Sharpe ratio.
- No max drawdown.
- No performance report.
- No charting.
- No broker integration.
- No trade records.
- No transaction costs.
- No slippage.
- No cash accounting.
- No multi-asset portfolio.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.backtesting import moving_average_crossover_pipeline"` works.
- README is updated with a small end-to-end usage example.
- The implementation composes existing modules instead of duplicating logic.
- The implementation stays small and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 7 scope.
3. Do not introduce a generic backtesting engine, strategy classes, performance metrics, reports, charts, trade records, cash accounting, transaction costs, slippage, broker integration, dashboard, cloud features, or multi-asset support.
4. Keep the pipeline pure, deterministic, and network-free.
5. Do not use live market data in tests.
6. Compose existing functions instead of reimplementing their internals.
7. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether the pipeline is truly a composition layer.
- Whether output columns are clear and useful for research.
- Whether the timing rule still avoids look-ahead bias.
- Whether Codex avoided building a full framework too early.