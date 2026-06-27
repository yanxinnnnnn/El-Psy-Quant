# Sprint 6 — Equity Curve Foundation

## Objective

Add the first equity curve calculation layer.

Sprint 5 gave us daily strategy returns. Sprint 6 should convert those daily returns into a cumulative equity curve, without introducing performance metrics, reports, charting, or a full backtesting engine.

## Product Goal

As the founder, I want a small, explicit equity-curve function so future backtests can show how strategy capital evolves over time.

## Technical Direction

Extend the existing portfolio module:

```text
src/
└── el_psy_quant/
    └── portfolio/
        ├── __init__.py
        ├── positions.py
        ├── returns.py
        └── equity.py

tests/
└── test_portfolio_equity.py
```

Keep equity curve calculation as a pure function.

The function should accept a `pd.Series` and return a `pd.Series` aligned to the input index.

## Core Concept

An equity curve tracks how capital grows over time from periodic returns.

Formula:

```text
equity[t] = initial_capital * product(1 + strategy_return[0:t])
```

For example:

```text
strategy_return: [0.0, 0.10, -0.05]
initial_capital: 1000

equity: [1000.0, 1100.0, 1045.0]
```

Why:

- Day 1: 1000 * (1 + 0.0) = 1000
- Day 2: 1000 * (1 + 0.10) = 1100
- Day 3: 1100 * (1 - 0.05) = 1045

## Implementation Scope

### Must Have

Implement:

```python
def equity_curve(strategy_return: pd.Series, initial_capital: float = 1.0) -> pd.Series:
    ...
```

The function should:

- Reject NaN values in `strategy_return` with `ValueError`.
- Reject non-positive `initial_capital` with `ValueError`.
- Use compounding: `(1 + strategy_return).cumprod() * initial_capital`.
- Preserve the input index.
- Return a float-like `pd.Series`.
- Work for empty input by returning an empty float-like series with the same index.

### Tests

Add tests covering:

- Basic equity curve compounding.
- Custom initial capital.
- Flat returns keep equity unchanged.
- Negative returns reduce equity correctly.
- Input index is preserved.
- Returned dtype is float-like if practical.
- NaN strategy return values raise `ValueError`.
- Zero initial capital raises `ValueError`.
- Negative initial capital raises `ValueError`.
- Empty input returns an empty series with the same index.

### Out of Scope

- No CAGR.
- No Sharpe ratio.
- No max drawdown.
- No volatility metrics.
- No performance report.
- No plotting/charting.
- No trade records.
- No transaction costs.
- No slippage.
- No cash accounting.
- No backtesting engine.
- No broker integration.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.portfolio import equity_curve"` works.
- README is updated with a small strategy-return-to-equity usage example.
- The implementation stays small and pure.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 6 scope.
3. Do not introduce performance metrics, reports, charts, backtesting engine, trade records, cash accounting, transaction costs, slippage, broker integration, dashboard, or cloud features.
4. Keep functions pure and easy to test.
5. Do not use live market data in tests.
6. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether the function uses compounding rather than simple cumulative sum.
- Whether invalid capital and NaNs are rejected explicitly.
- Whether the index is preserved.
- Whether Codex avoided premature reporting/backtesting abstractions.