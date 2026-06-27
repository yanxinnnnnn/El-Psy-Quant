# Sprint 9 — Backtest Summary Layer

## Objective

Add the first small backtest summary layer.

Sprint 8 added basic performance metrics. Sprint 9 should package the most important results from a pipeline output DataFrame into a simple, explicit summary dictionary, without introducing report objects, charts, annualization, or a full analytics framework.

## Product Goal

As the founder, I want a compact summary function so that a pipeline result can be quickly inspected without manually calling each metric function every time.

## Technical Direction

Extend the performance module:

```text
src/
└── el_psy_quant/
    └── performance/
        ├── __init__.py
        ├── metrics.py
        └── summary.py

tests/
└── test_performance_summary.py
```

Keep the summary function pure and deterministic.

## Implementation Scope

### Must Have

Implement:

```python
def backtest_summary(result: pd.DataFrame) -> dict[str, float]:
    ...
```

The function should:

- Accept the DataFrame returned by `moving_average_crossover_pipeline`.
- Require an `equity` column; raise `ValueError` if missing.
- Require a `strategy_return` column; raise `ValueError` if missing.
- Reject empty input with `ValueError`.
- Reject NaN values in required columns with `ValueError`.
- Return a plain dictionary with exactly these keys:
  - `initial_equity`
  - `final_equity`
  - `total_return`
  - `max_drawdown`
  - `periods`
- Use existing metric functions:
  - `total_return`
  - `max_drawdown`
- Keep values as plain floats except `periods`, which may be returned as `float` for consistency or `int` if type clarity is preferred.

### Example

Given a pipeline result with:

```text
equity: [1000.0, 1100.0, 1045.0]
strategy_return: [0.0, 0.10, -0.05]
```

Expected summary:

```python
{
    "initial_equity": 1000.0,
    "final_equity": 1045.0,
    "total_return": 0.045,
    "max_drawdown": -0.05,
    "periods": 3,
}
```

## Important Design Rule

This sprint is a summary layer, not a reporting framework.

Do not introduce:

- dataclasses
- report objects
- text reports
- charts
- tables
- file exports
- dashboards

A simple dictionary is enough for now.

## Tests

Add tests covering:

- Normal summary output.
- Summary uses existing metric functions correctly.
- Missing `equity` column raises `ValueError`.
- Missing `strategy_return` column raises `ValueError`.
- Empty DataFrame raises `ValueError`.
- NaN in `equity` raises `ValueError`.
- NaN in `strategy_return` raises `ValueError`.
- Output has exactly the expected keys.
- `periods` equals the number of rows.

## Out of Scope

- No CAGR / annualized return.
- No Sharpe ratio.
- No volatility metrics.
- No benchmark comparison.
- No report class or dataclass.
- No markdown/HTML/text report generation.
- No charts.
- No file export.
- No backtesting engine changes.
- No transaction costs or slippage.
- No trade records.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.performance import backtest_summary"` works.
- README is updated with a small summary usage example.
- The implementation stays small, pure, and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 9 scope.
3. Do not introduce CAGR, Sharpe ratio, annualization, report objects, dataclasses, charts, text reports, file exports, benchmark comparison, backtesting engine changes, transaction costs, slippage, trade records, dashboard, cloud features, or broker integration.
4. Keep the function pure and easy to test.
5. Do not use live market data in tests.
6. Reuse existing metric functions instead of duplicating metric formulas.
7. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether summary values are calculated from the pipeline output, not raw prices.
- Whether existing metrics are reused.
- Whether the output dictionary stays intentionally small.
- Whether Codex avoided premature report abstractions.