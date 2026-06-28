# Sprint 18 — Moving-Average Parameter Sweep

## Objective

Add a deterministic local parameter sweep for the moving-average crossover strategy.

Sprint 15 added a convenience function for running one moving-average crossover research flow from a local CSV. Sprint 18 should allow running many `(fast_window, slow_window)` combinations against the same local CSV input and comparing their summary metrics.

This sprint starts the experimentation layer, but it must stay disciplined: parameter search is not alpha discovery.

## Product Goal

As the founder, I want to run a small grid of moving-average parameters against one local CSV file and get a tabular summary, so I can compare experiment outcomes without manually running each parameter pair.

The target flow is:

```text
local CSV
  -> close prices
  -> many moving-average window pairs
  -> pipeline per pair
  -> summary per pair
  -> experiment summary DataFrame
```

## Technical Direction

Add a small experiment helper under the backtesting package:

```text
src/
└── el_psy_quant/
    └── backtesting/
        ├── __init__.py
        ├── pipelines.py
        ├── workflows.py
        └── experiments.py

tests/
└── test_backtesting_experiments.py
```

Keep this as a function, not a class.

## Implementation Scope

### Must Have

Implement:

```python
def moving_average_crossover_parameter_sweep(
    path: str | Path,
    fast_windows: Iterable[int],
    slow_windows: Iterable[int],
    initial_capital: float = 1.0,
) -> pd.DataFrame:
    ...
```

The function should:

- Accept a local CSV path as `str` or `pathlib.Path`.
- Load prices using `load_daily_prices_csv(path)`.
- Use `prices["Close"]` as the close-price series.
- Iterate over every combination of `fast_windows` and `slow_windows`.
- Run only valid combinations where `fast_window < slow_window`.
- Skip invalid combinations where `fast_window >= slow_window`.
- For each valid pair:
  - run `moving_average_crossover_pipeline`
  - run `backtest_summary`
  - add one row to the output DataFrame
- Return a `pd.DataFrame` with one row per valid parameter pair.

Required output columns:

```text
fast_window
slow_window
initial_equity
final_equity
total_return
max_drawdown
periods
```

The output should be sorted by:

```text
fast_window ascending, then slow_window ascending
```

### Empty Input / Empty Result Handling

The function should raise `ValueError` if:

- `fast_windows` is empty.
- `slow_windows` is empty.
- No valid `(fast_window, slow_window)` combinations exist.

Use clear messages, for example:

```text
fast_windows must not be empty
slow_windows must not be empty
no valid moving-average window combinations
```

### Export

Export the function from:

```python
el_psy_quant.backtesting
```

## Example Usage

```python
from el_psy_quant.backtesting import moving_average_crossover_parameter_sweep

summary = moving_average_crossover_parameter_sweep(
    "data/cache/AAPL.csv",
    fast_windows=[5, 10, 20],
    slow_windows=[20, 50, 100],
    initial_capital=1_000.0,
)

print(summary)
```

## Tests

Add tests covering:

- The function returns a DataFrame with the required columns.
- It creates one row per valid `(fast_window, slow_window)` pair.
- It skips invalid pairs where `fast_window >= slow_window`.
- The output is sorted by `fast_window`, then `slow_window`.
- It accepts a `Path` object.
- Custom `initial_capital` is reflected in the output rows.
- Empty `fast_windows` raises `ValueError`.
- Empty `slow_windows` raises `ValueError`.
- All-invalid combinations raise `ValueError`.
- Invalid CSV input propagates a `ValueError` from the CSV loader.
- The function is exported from `el_psy_quant.backtesting`.

Use pytest `tmp_path` to create small deterministic CSV files.

## README Update

Add a short example showing:

```python
from el_psy_quant.backtesting import moving_average_crossover_parameter_sweep

summary = moving_average_crossover_parameter_sweep(
    "data/cache/AAPL.csv",
    fast_windows=[5, 10, 20],
    slow_windows=[20, 50, 100],
    initial_capital=1_000.0,
)
```

Keep it short. Do not turn the README into an experiment tutorial.

## Out of Scope

- No charts.
- No heatmaps.
- No dashboards.
- No CLI command.
- No file export.
- No automatic ranking recommendation.
- No "best strategy" claim.
- No statistical significance testing.
- No walk-forward validation.
- No train/test split.
- No benchmark comparison.
- No transaction costs or slippage.
- No multi-symbol support.
- No generic experiment framework.
- No parallel execution.
- No live download.
- No cache refresh.
- No broker integration.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.backtesting import moving_average_crossover_parameter_sweep"` works.
- README includes a short parameter-sweep usage example.
- The implementation stays deterministic, local-only, and network-free.
- The implementation stays small and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 18 scope.
3. Do not introduce charts, heatmaps, dashboards, CLI commands, file exports, automatic ranking recommendations, best-strategy claims, statistical significance tests, walk-forward validation, train/test split, benchmark comparison, transaction costs, slippage, multi-symbol support, generic experiment frameworks, parallel execution, live downloads, cache refresh, cloud features, or broker integration.
4. Reuse `load_daily_prices_csv`, `moving_average_crossover_pipeline`, and `backtest_summary`.
5. Use temporary CSV files in tests. Do not call Yahoo Finance or any live network service.
6. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether the sweep is deterministic and local-only.
- Whether invalid parameter pairs are skipped intentionally.
- Whether the output table is simple and easy to inspect.
- Whether Codex avoided making any profitability or "best parameter" claims.