# Sprint 2 — Indicators Foundation

## Objective

Add the first pure quantitative indicator functions.

This sprint turns El-Psy-Quant from a project that can fetch market data into a project that can begin transforming market data into research features.

## Product Goal

As the founder, I want a small, well-tested indicator layer so that future strategies can reuse reliable calculations instead of duplicating pandas logic.

## Technical Direction

Create a new indicators module:

```text
src/
└── el_psy_quant/
    └── indicators/
        ├── __init__.py
        └── trend.py

tests/
└── test_indicators_trend.py
```

Keep indicators as pure functions.

They should accept `pd.Series` and return `pd.Series`.

## Implementation Scope

### Must Have

Implement:

1. `simple_moving_average(series: pd.Series, window: int) -> pd.Series`
2. `exponential_moving_average(series: pd.Series, span: int) -> pd.Series`
3. `daily_return(series: pd.Series) -> pd.Series`

### Behavior Requirements

#### `simple_moving_average`

- Use pandas rolling mean.
- Preserve the input index.
- Use the default pandas behavior for early rows where there is insufficient data.
- Validate that `window > 0`.

#### `exponential_moving_average`

- Use pandas exponential weighted mean.
- Preserve the input index.
- Validate that `span > 0`.
- Prefer `adjust=False` unless there is a documented reason not to.

#### `daily_return`

- Use percentage change.
- Preserve the input index.
- Do not fill the first NaN value.

### Tests

Add tests covering:

- Normal SMA calculation.
- SMA preserves index.
- SMA rejects non-positive windows.
- Normal EMA calculation with deterministic expected values.
- EMA preserves index.
- EMA rejects non-positive spans.
- Daily return calculation.
- Daily return preserves the first NaN.

### Out of Scope

- No trading signals.
- No strategy classes.
- No backtesting.
- No charting.
- No network calls.
- No dependency on Yahoo Finance.
- No TA-Lib or third-party indicator package.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.indicators import simple_moving_average"` works.
- README is updated with a small indicator usage example.
- The implementation stays small and pure.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 2 scope.
3. Do not introduce strategy, backtesting, broker integration, dashboard, or cloud features.
4. Keep functions pure and easy to test.
5. Do not use live market data in tests.
6. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether indicator functions are easy to understand.
- Whether invalid parameter validation is simple and explicit.
- Whether tests verify actual numeric behavior, not only that functions run.
- Whether Codex avoided unnecessary classes or abstractions.