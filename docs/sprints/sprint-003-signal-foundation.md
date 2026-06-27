# Sprint 3 — Signal Foundation

## Objective

Add the first signal-generation layer.

Sprint 1 gave us market data. Sprint 2 gave us indicators. Sprint 3 should turn indicator relationships into explicit trading signals, without introducing portfolio accounting or backtesting.

## Product Goal

As the founder, I want reusable signal functions so that future strategies and backtests can consume consistent buy/sell/hold outputs instead of duplicating crossover logic.

## Technical Direction

Create a new signals module:

```text
src/
└── el_psy_quant/
    └── signals/
        ├── __init__.py
        └── crossover.py

tests/
└── test_signals_crossover.py
```

Keep signals as pure functions.

They should accept `pd.Series` inputs and return a `pd.Series` aligned to the input index.

## Signal Convention

Use integer signal values:

- `1` = buy / bullish event
- `-1` = sell / bearish event
- `0` = no signal

This convention represents **events**, not current position.

For example, if the short moving average stays above the long moving average for five days, that should not emit five buy signals. It should emit a buy signal only on the crossover day.

## Implementation Scope

### Must Have

Implement:

```python
def crossover_signal(fast: pd.Series, slow: pd.Series) -> pd.Series:
    ...
```

The function should:

- Return `1` when `fast` crosses from less than or equal to `slow` to greater than `slow`.
- Return `-1` when `fast` crosses from greater than or equal to `slow` to less than `slow`.
- Return `0` otherwise.
- Preserve the input index.
- Raise `ValueError` if the two series indexes are not equal.
- Handle `NaN` values conservatively: do not emit crossover signals when the current or previous comparison depends on `NaN`.

### Nice to Have

- Add a helper alias such as `moving_average_crossover_signal` only if it does not add complexity.
- Document a small README example using `simple_moving_average` and `crossover_signal`.

### Out of Scope

- No portfolio positions.
- No cash or trade accounting.
- No backtesting engine.
- No broker integration.
- No charting.
- No live market data tests.
- No strategy classes yet.

## Example Behavior

Given:

```text
fast: [1, 2, 3, 2, 1]
slow: [2, 2, 2, 2, 2]
```

Expected signal:

```text
[0, 0, 1, 0, -1]
```

Why:

- At index 2, fast crosses from equal/below slow to above slow.
- At index 4, fast crosses from equal/above slow to below slow.

## Tests

Add tests covering:

- Bullish crossover emits `1`.
- Bearish crossover emits `-1`.
- No repeated signal while fast remains above slow.
- No signal when indexes differ; raise `ValueError`.
- Input index is preserved.
- NaN values do not produce false signals.
- Returned dtype is integer-like if practical.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.signals import crossover_signal"` works.
- README is updated with a small signal usage example.
- The implementation stays small and pure.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 3 scope.
3. Do not introduce portfolio, backtesting, broker integration, dashboard, charting, cloud features, or strategy classes.
4. Keep functions pure and easy to test.
5. Do not use live market data in tests.
6. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether `crossover_signal` emits event signals, not position states.
- Whether NaN behavior is conservative.
- Whether tests catch repeated-signal mistakes.
- Whether Codex avoided unnecessary abstractions.