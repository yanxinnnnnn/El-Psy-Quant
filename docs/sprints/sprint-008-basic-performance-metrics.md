# Sprint 8 — Basic Performance Metrics

## Objective

Add the first performance metric calculation layer.

Milestone 1 created a minimal research pipeline that can produce an equity curve. Sprint 8 begins Milestone 2 by turning equity and return series into simple, honest performance measurements.

## Product Goal

As the founder, I want a small set of pure performance metrics so that strategy results can be evaluated consistently instead of judged only by looking at the final equity number.

## Technical Direction

Create a new performance module:

```text
src/
└── el_psy_quant/
    └── performance/
        ├── __init__.py
        └── metrics.py

tests/
└── test_performance_metrics.py
```

Keep metrics as pure functions.

Metric functions should accept `pd.Series` inputs and return plain `float` values unless there is a strong reason not to.

## Implementation Scope

### Must Have

Implement:

```python
def total_return(equity: pd.Series) -> float:
    ...


def max_drawdown(equity: pd.Series) -> float:
    ...
```

### `total_return`

The function should:

- Reject empty equity series with `ValueError`.
- Reject NaN values with `ValueError`.
- Reject non-positive starting equity with `ValueError`.
- Return final equity divided by starting equity minus 1.

Formula:

```text
total_return = equity[-1] / equity[0] - 1
```

Example:

```text
equity: [1000, 1100, 1050]
total_return: 0.05
```

### `max_drawdown`

The function should:

- Reject empty equity series with `ValueError`.
- Reject NaN values with `ValueError`.
- Reject non-positive equity values with `ValueError`.
- Calculate drawdown using running peak equity.
- Return the minimum drawdown as a negative float or `0.0` if there is no drawdown.

Formula:

```text
running_peak = equity.cummax()
drawdown = equity / running_peak - 1
max_drawdown = drawdown.min()
```

Example:

```text
equity: [1000, 1200, 900, 1500]
running_peak: [1000, 1200, 1200, 1500]
drawdown: [0.0, 0.0, -0.25, 0.0]
max_drawdown: -0.25
```

## Nice to Have

- Add a small README example that calculates `total_return` and `max_drawdown` from the pipeline's `equity` column.
- Keep any helper validation private and simple.

## Out of Scope

- No CAGR / annualized return yet.
- No Sharpe ratio yet.
- No Sortino ratio.
- No volatility metrics.
- No Calmar ratio.
- No benchmark comparison.
- No performance report object.
- No charts.
- No backtesting engine changes.
- No transaction costs or slippage.
- No trade records.

## Tests

Add tests covering:

- Normal total return calculation.
- Flat equity has total return `0.0`.
- Negative total return calculation.
- Empty equity raises `ValueError` for total return.
- NaN equity raises `ValueError` for total return.
- Non-positive starting equity raises `ValueError` for total return.
- Normal max drawdown calculation.
- Monotonically increasing equity has max drawdown `0.0`.
- Empty equity raises `ValueError` for max drawdown.
- NaN equity raises `ValueError` for max drawdown.
- Non-positive equity values raise `ValueError` for max drawdown.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.performance import total_return, max_drawdown"` works.
- README is updated with a small performance metric usage example.
- The implementation stays small, pure, and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 8 scope.
3. Do not introduce CAGR, Sharpe ratio, annualization, report objects, charts, benchmark comparison, backtesting engine changes, transaction costs, slippage, trade records, dashboard, cloud features, or broker integration.
4. Keep functions pure and easy to test.
5. Do not use live market data in tests.
6. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether metrics are calculated from equity, not raw prices.
- Whether max drawdown uses running peak logic.
- Whether invalid equity data is rejected explicitly.
- Whether Codex avoided performance-report abstractions too early.