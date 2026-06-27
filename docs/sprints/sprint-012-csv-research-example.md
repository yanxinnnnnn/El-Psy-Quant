# Sprint 12 — CSV Research Example

## Objective

Add the first local CSV-based research example.

Sprint 11 added a deterministic CSV loader. Sprint 12 should connect that loader to the existing research pipeline and summary layer, so users can see the complete local-file workflow without relying on live market data.

## Product Goal

As the founder, I want a runnable example that starts from a local CSV file and produces a pipeline result plus summary, so the project demonstrates a reproducible research workflow using file-based input.

The target flow is:

```text
local CSV file
  -> load_daily_prices_csv
  -> close prices
  -> moving_average_crossover_pipeline
  -> backtest_summary
  -> printed output
```

## Technical Direction

Add a CSV example script and a small deterministic sample CSV file:

```text
examples/
├── csv_research_example.py
└── data/
    └── sample_daily_prices.csv

tests/
└── test_csv_research_example.py
```

The sample data should be small enough to keep in git and deterministic enough for tests.

## Implementation Scope

### Must Have

Add:

```text
examples/csv_research_example.py
examples/data/sample_daily_prices.csv
```

The script should:

- Load `examples/data/sample_daily_prices.csv` using `load_daily_prices_csv`.
- Extract `prices["Close"]`.
- Run `moving_average_crossover_pipeline`.
- Run `backtest_summary`.
- Print the final few rows of the result DataFrame.
- Print the summary dictionary in a readable way.
- Have a `main()` function.
- Use `if __name__ == "__main__": main()`.
- Resolve the sample CSV path relative to the script file, not the current working directory.
- Avoid network calls.
- Avoid file output.
- Avoid charts.

The sample CSV should:

- Include required columns:
  - `Date`
  - `Open`
  - `High`
  - `Low`
  - `Close`
  - `Volume`
- Have dates sorted ascending.
- Include enough rows to generate moving averages and at least one signal if practical.
- Contain no missing `Date` or `Close` values.
- Be small and readable.

### README Update

Add a short section explaining how to run the CSV example:

```bash
uv run python examples/csv_research_example.py
```

Keep the existing in-memory minimal example section.

### Tests

Add tests covering:

- The CSV example module can be imported.
- `main()` runs without raising.
- The example prints output containing at least:
  - `summary`
  - `total_return`
  - `max_drawdown`
- The example does not call Yahoo Finance or any live data provider.
- The sample CSV can be loaded by `load_daily_prices_csv`.
- The sample CSV has a usable `Close` column.

Use pytest `capsys` and `monkeypatch` where useful.

## Out of Scope

- No CLI argument parsing.
- No custom CSV path argument.
- No live Yahoo Finance download.
- No data cache.
- No automatic CSV writing.
- No large sample dataset.
- No notebooks.
- No charts.
- No dashboards.
- No new indicators.
- No new strategies.
- No new metrics.
- No backtesting engine changes.
- No transaction costs or slippage.
- No broker integration.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python examples/csv_research_example.py` works.
- README includes the CSV example run command.
- The example is deterministic and network-free.
- The implementation stays small and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 12 scope.
3. Do not introduce CLI parsing, custom path arguments, live downloads, caching, notebooks, charts, dashboards, new indicators, new strategies, new metrics, backtesting engine changes, transaction costs, slippage, cloud features, or broker integration.
4. Keep the CSV file small and readable.
5. Resolve the sample CSV path relative to the example script.
6. Do not use live market data in tests.
7. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether the example clearly demonstrates local CSV research flow.
- Whether the CSV sample is small and deterministic.
- Whether the example is robust to current working directory changes.
- Whether Codex avoided turning this into a CLI or data framework.