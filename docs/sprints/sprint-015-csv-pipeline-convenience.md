# Sprint 15 — CSV Pipeline Convenience Function

## Objective

Add a small convenience function that runs the existing moving-average crossover research flow directly from a local CSV file.

Sprint 11 added CSV loading. Sprint 12 added a CSV research example. Sprint 13 added local cache helpers. Sprint 14 connected Yahoo downloads to the local cache. Sprint 15 should provide a compact programmatic entry point for the common local research path:

```text
CSV file
  -> load_daily_prices_csv
  -> moving_average_crossover_pipeline
  -> backtest_summary
```

This is a convenience layer only. It is not a backtesting engine, CLI, report system, or data platform.

## Product Goal

As the founder, I want one small helper that takes a local CSV file and moving-average parameters, then returns both the full pipeline result and the compact summary.

This makes local cached research easier to run while keeping all intermediate outputs inspectable.

## Technical Direction

Extend the backtesting package with a local-file workflow helper:

```text
src/
└── el_psy_quant/
    └── backtesting/
        ├── __init__.py
        ├── pipelines.py
        └── workflows.py

tests/
└── test_backtesting_workflows.py
```

Keep this as a function, not a class.

## Implementation Scope

### Must Have

Implement:

```python
def moving_average_crossover_from_csv(
    path: str | Path,
    fast_window: int,
    slow_window: int,
    initial_capital: float = 1.0,
) -> tuple[pd.DataFrame, dict[str, float]]:
    ...
```

The function should:

- Accept a local CSV path as `str` or `pathlib.Path`.
- Load prices using `load_daily_prices_csv(path)`.
- Use `prices["Close"]` as the close-price series.
- Run `moving_average_crossover_pipeline` with the provided windows and `initial_capital`.
- Run `backtest_summary` on the pipeline result.
- Return a tuple:

```python
(result, summary)
```

Where:

- `result` is the full pipeline `pd.DataFrame`.
- `summary` is the dictionary returned by `backtest_summary`.

The function should reuse existing validation from:

- `load_daily_prices_csv`
- `moving_average_crossover_pipeline`
- `backtest_summary`

Do not duplicate their internal validation logic unless necessary.

Export the function from `el_psy_quant.backtesting`.

## Example Usage

```python
from el_psy_quant.backtesting import moving_average_crossover_from_csv

result, summary = moving_average_crossover_from_csv(
    "data/cache/AAPL.csv",
    fast_window=20,
    slow_window=50,
    initial_capital=1_000.0,
)

print(result.tail())
print(summary)
```

## Tests

Add tests covering:

- The function loads a valid CSV and returns `(result, summary)`.
- The returned result contains expected pipeline columns.
- The returned summary contains expected summary keys.
- The function accepts a `Path` object.
- Custom `initial_capital` is reflected in the summary.
- Invalid CSV input propagates a `ValueError` from the CSV loader.
- Invalid moving-average windows propagate a `ValueError` from the pipeline.
- The function is exported from `el_psy_quant.backtesting`.

Use pytest `tmp_path` to create small deterministic CSV files.

## README Update

Add a short example showing:

```python
from el_psy_quant.backtesting import moving_average_crossover_from_csv

result, summary = moving_average_crossover_from_csv(
    "data/cache/AAPL.csv",
    fast_window=20,
    slow_window=50,
    initial_capital=1_000.0,
)
```

Keep it short. Do not turn the README into a tutorial.

## Out of Scope

- No CLI command.
- No custom report object.
- No dataclass.
- No charts.
- No notebooks.
- No file export.
- No live download.
- No cache refresh.
- No automatic fallback to Yahoo.
- No strategy classes.
- No generic backtesting engine.
- No new indicators.
- No new metrics.
- No transaction costs or slippage.
- No benchmark comparison.
- No multi-symbol support.
- No broker integration.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.backtesting import moving_average_crossover_from_csv"` works.
- README includes a short CSV-to-pipeline convenience example.
- The implementation stays small, deterministic, and network-free.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 15 scope.
3. Do not introduce CLI commands, report objects, dataclasses, charts, notebooks, file exports, live downloads, cache refresh, automatic Yahoo fallback, strategy classes, generic backtesting engines, new indicators, new metrics, transaction costs, slippage, benchmark comparison, multi-symbol support, cloud features, or broker integration.
4. Reuse `load_daily_prices_csv`, `moving_average_crossover_pipeline`, and `backtest_summary`.
5. Use temporary CSV files in tests. Do not call Yahoo Finance or any live network service.
6. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether the helper is truly a thin composition layer.
- Whether it returns both the full result and summary.
- Whether it avoids hiding live downloads or cache refresh behavior.
- Whether Codex avoided building another framework layer.