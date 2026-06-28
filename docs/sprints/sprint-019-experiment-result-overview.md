# Sprint 19 — Experiment Result Overview

## Objective

Add a small overview helper for parameter-sweep experiment results.

Sprint 18 added `moving_average_crossover_parameter_sweep`, which returns one row per valid `(fast_window, slow_window)` pair. Sprint 19 should add a higher-level overview of that table so users can quickly inspect experiment scale and metric distribution without claiming that any parameter pair is the best strategy.

This sprint is about experiment inspection, not strategy recommendation.

## Product Goal

As the founder, I want a compact one-row overview table for a parameter sweep result, so I can quickly understand how many runs were evaluated and what the metric ranges look like.

The target flow is:

```text
parameter sweep result DataFrame
  -> summarize_parameter_sweep_results
  -> one-row overview DataFrame
```

## Technical Direction

Extend the existing backtesting experiment module:

```text
src/
└── el_psy_quant/
    └── backtesting/
        ├── __init__.py
        ├── experiments.py
        ├── pipelines.py
        └── workflows.py

tests/
└── test_backtesting_experiments.py
```

Keep this as a function, not a class.

Do not add a generic experiment framework.

## Implementation Scope

### Must Have

Implement:

```python
def summarize_parameter_sweep_results(results: pd.DataFrame) -> pd.DataFrame:
    ...
```

The function should:

- Accept a parameter sweep result DataFrame.
- Require the columns produced by `moving_average_crossover_parameter_sweep`:
  - `fast_window`
  - `slow_window`
  - `initial_equity`
  - `final_equity`
  - `total_return`
  - `max_drawdown`
  - `periods`
- Reject an empty DataFrame with `ValueError`.
- Reject missing required columns with `ValueError`.
- Return a one-row `pd.DataFrame`.

Required output columns:

```text
runs
fast_window_min
fast_window_max
slow_window_min
slow_window_max
initial_equity_min
initial_equity_max
final_equity_min
final_equity_mean
final_equity_max
total_return_min
total_return_mean
total_return_max
max_drawdown_min
max_drawdown_mean
max_drawdown_max
periods_min
periods_max
```

The output should not include:

- best parameter pair
- recommended parameter pair
- ranking label
- score
- strategy recommendation

### Export

Export the function from:

```python
el_psy_quant.backtesting
```

## Example Usage

```python
from el_psy_quant.backtesting import (
    moving_average_crossover_parameter_sweep,
    summarize_parameter_sweep_results,
)

results = moving_average_crossover_parameter_sweep(
    "data/cache/AAPL.csv",
    fast_windows=[5, 10, 20],
    slow_windows=[20, 50, 100],
    initial_capital=1_000.0,
)

overview = summarize_parameter_sweep_results(results)
print(overview)
```

## Tests

Add tests covering:

- The function returns a one-row DataFrame.
- The returned overview has the required columns in stable order.
- `runs` equals the number of experiment rows.
- Window min/max values are computed correctly.
- `initial_equity`, `final_equity`, `total_return`, `max_drawdown`, and `periods` overview values are computed correctly.
- Empty input raises `ValueError`.
- Missing required columns raise `ValueError`.
- The function accepts the DataFrame returned by `moving_average_crossover_parameter_sweep`.
- The function does not mutate the input DataFrame.
- The function is exported from `el_psy_quant.backtesting`.

Use deterministic in-memory DataFrames for most tests. Use a temporary CSV only where helpful for integration with the existing parameter sweep function.

## README Update

Add a short example showing:

```python
from el_psy_quant.backtesting import summarize_parameter_sweep_results

overview = summarize_parameter_sweep_results(summary)
```

Keep it short. Do not turn the README into an experiment tutorial.

## Out of Scope

- No best-parameter recommendation.
- No automatic ranking.
- No score column.
- No charts.
- No heatmaps.
- No dashboards.
- No CLI command.
- No file export.
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
- `uv run python -c "from el_psy_quant.backtesting import summarize_parameter_sweep_results"` works.
- README includes a short parameter-sweep overview usage example.
- The implementation stays deterministic, local-only, and network-free.
- The implementation stays small and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 19 scope.
3. Do not introduce best-parameter recommendations, automatic ranking, score columns, charts, heatmaps, dashboards, CLI commands, file exports, statistical significance tests, walk-forward validation, train/test split, benchmark comparison, transaction costs, slippage, multi-symbol support, generic experiment frameworks, parallel execution, live downloads, cache refresh, cloud features, or broker integration.
4. Reuse the result structure produced by `moving_average_crossover_parameter_sweep`.
5. Keep tests deterministic and network-free.
6. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether the overview is descriptive rather than prescriptive.
- Whether it avoids naming a best parameter pair.
- Whether the output is stable and easy to inspect.
- Whether Codex avoided expanding this into a generic experiment framework.