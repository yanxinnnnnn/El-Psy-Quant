# Sprint 5 — Strategy Return Foundation

## Objective

Add the first strategy return calculation layer.

Sprint 4 gave us daily position states. Sprint 5 should combine those positions with asset returns to calculate daily strategy returns, without introducing cumulative returns, performance metrics, reports, or a full backtesting engine.

## Product Goal

As the founder, I want a small, explicit return-calculation function so future backtests can reuse a reliable daily strategy return series.

## Technical Direction

Extend the existing portfolio module:

```text
src/
└── el_psy_quant/
    └── portfolio/
        ├── __init__.py
        ├── positions.py
        └── returns.py

tests/
└── test_portfolio_returns.py
```

Keep return calculation as a pure function.

The function should accept `pd.Series` inputs and return a `pd.Series` aligned to the input index.

## Core Concept

Strategy return should be calculated using the **previous day's position** applied to today's asset return.

Why:

- If a buy signal happens today and creates a position today, the strategy should not earn today's return unless we explicitly model intraday execution.
- To stay conservative and avoid look-ahead assumptions, today's return should use yesterday's position.

Formula:

```text
strategy_return[t] = position[t-1] * asset_return[t]
```

The first strategy return should be `0.0` because there is no previous position.

## Implementation Scope

### Must Have

Implement:

```python
def strategy_return(position: pd.Series, asset_return: pd.Series) -> pd.Series:
    ...
```

The function should:

- Require matching indexes; raise `ValueError` if indexes differ.
- Reject NaN values in `position` with `ValueError`.
- Reject unsupported position values; for now only allow `0` and `1`.
- Treat NaN values in `asset_return` conservatively:
  - The first `asset_return` is often NaN from `pct_change`; convert the first resulting strategy return to `0.0`.
  - Other NaN asset returns should raise `ValueError`.
- Use previous-day position: `position.shift(1)`.
- Fill the first shifted position with `0`.
- Return a float-like `pd.Series`.
- Preserve the input index.

### Example Behavior

Given:

```text
position:     [0, 1, 1, 0]
asset_return: [NaN, 0.10, -0.05, 0.02]
```

Expected strategy return:

```text
[0.0, 0.0, -0.05, 0.02]
```

Why:

- Day 1 has no previous position, so strategy return is 0.
- Day 2 uses Day 1 position, which is 0, so it earns 0 despite the asset rising 10%.
- Day 3 uses Day 2 position, which is 1, so it earns -5%.
- Day 4 uses Day 3 position, which is 1, so it earns +2%.

## Tests

Add tests covering:

- Basic strategy return calculation using previous-day position.
- First strategy return is `0.0` when asset return starts with NaN.
- Position and asset return indexes must match.
- Position index is preserved in output.
- Position NaN values raise `ValueError`.
- Invalid position values raise `ValueError`.
- Asset return NaN after the first row raises `ValueError`.
- Returned dtype is float-like if practical.
- Zero position produces zero strategy returns.

## Out of Scope

- No cumulative returns.
- No CAGR.
- No Sharpe ratio.
- No max drawdown.
- No performance report.
- No trade records.
- No transaction costs.
- No slippage.
- No cash accounting.
- No backtesting engine.
- No broker integration.
- No charting.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.portfolio import strategy_return"` works.
- README is updated with a small position-to-return usage example.
- The implementation stays small and pure.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 5 scope.
3. Do not introduce cumulative returns, metrics, backtesting engine, reports, trade records, cash accounting, transaction costs, slippage, broker integration, dashboard, charting, or cloud features.
4. Keep functions pure and easy to test.
5. Do not use live market data in tests.
6. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether returns use previous-day position, not same-day position.
- Whether the first return is handled conservatively.
- Whether invalid positions and unexpected NaNs are rejected explicitly.
- Whether Codex avoided premature backtesting abstractions.