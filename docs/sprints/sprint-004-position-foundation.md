# Sprint 4 — Position Foundation

## Objective

Add the first position-generation layer.

Sprint 3 gave us signal events. Sprint 4 should convert those events into a daily long-only position state, without introducing portfolio accounting, returns calculation, or backtesting.

## Product Goal

As the founder, I want reusable position functions so that future return calculations can consume clear daily exposure states instead of directly interpreting raw signal events.

## Technical Direction

Create a new portfolio module:

```text
src/
└── el_psy_quant/
    └── portfolio/
        ├── __init__.py
        └── positions.py

tests/
└── test_portfolio_positions.py
```

Keep position generation as pure functions.

Functions should accept `pd.Series` inputs and return a `pd.Series` aligned to the input index.

## Position Convention

Use integer position values:

- `1` = long / holding the asset
- `0` = flat / no position

This first implementation is **long-only**. It does not support short selling.

## Implementation Scope

### Must Have

Implement:

```python
def long_only_position(signal: pd.Series) -> pd.Series:
    ...
```

The function should:

- Interpret `1` in the signal as entering or staying long.
- Interpret `-1` in the signal as exiting to flat.
- Interpret `0` in the signal as keeping the previous position.
- Start from flat position `0`.
- Preserve the input index.
- Return an integer-like `pd.Series`.
- Raise `ValueError` if signal contains values other than `-1`, `0`, or `1`.
- Handle `NaN` values conservatively: reject them with `ValueError` rather than silently treating them as hold signals.

### Example Behavior

Given:

```text
signal:   [0, 1, 0, 0, -1, 0, 1]
position: [0, 1, 1, 1,  0, 0, 1]
```

Why:

- Start flat.
- Buy signal moves position to long.
- Hold signals keep the previous state.
- Sell signal moves position to flat.

### Tests

Add tests covering:

- Basic conversion from signal events to long-only positions.
- Starting flat when the first signal is `0`.
- First signal `1` enters long.
- First signal `-1` remains flat.
- Repeated buy signals keep position at `1`.
- Repeated sell signals keep position at `0`.
- Input index is preserved.
- Returned dtype is integer-like if practical.
- Invalid signal values raise `ValueError`.
- NaN signal values raise `ValueError`.

### Out of Scope

- No strategy classes.
- No position sizing.
- No short positions.
- No leverage.
- No cash accounting.
- No transaction records.
- No transaction costs.
- No slippage.
- No return calculation.
- No backtesting engine.
- No broker integration.
- No charting.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.portfolio import long_only_position"` works.
- README is updated with a small signal-to-position usage example.
- The implementation stays small and pure.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 4 scope.
3. Do not introduce strategy classes, return calculation, backtesting, cash accounting, trade records, broker integration, dashboard, charting, or cloud features.
4. Keep functions pure and easy to test.
5. Do not use live market data in tests.
6. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether signal events are correctly converted into position states.
- Whether the implementation starts flat.
- Whether invalid values and NaNs are rejected explicitly.
- Whether Codex avoided unnecessary abstractions.