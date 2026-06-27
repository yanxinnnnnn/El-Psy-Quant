# Milestone 2 — Performance & Local Data Foundation

## Milestone Summary

Milestone 2 turned El-Psy-Quant from a minimal research pipeline into a more inspectable and reproducible research workflow.

Milestone 1 answered:

```text
Can we turn close prices into an equity curve?
```

Milestone 2 answered:

```text
Can we evaluate that equity curve and reproduce the workflow from local data?
```

The project can now calculate basic performance metrics, summarize a backtest result, load local CSV price data, and run research examples both from in-memory data and from a bundled CSV file.

This milestone is still not about proving a profitable strategy. It is about making evaluation and data input honest, deterministic, and easy to inspect.

## Product Thinking

The project followed this progression:

```text
Equity Curve
  -> Basic Metrics
  -> Backtest Summary
  -> Local Example
  -> Local CSV Loader
  -> CSV Research Example
```

The key idea was to improve research usability without jumping into a large reporting system, CLI app, data platform, or live-data cache.

Each sprint added one practical capability while preserving the project rules:

- Keep functions small and pure where possible.
- Keep tests deterministic and network-free.
- Avoid premature frameworks.
- Prefer explicit validation over silent assumptions.
- Make examples readable for a beginner.

## Sprint History

### Sprint 8 — Basic Performance Metrics

Goal: add the first performance metric calculation layer.

Delivered:

- `total_return(equity)`
- `max_drawdown(equity)`
- Tests for normal returns, flat returns, negative returns, empty data, NaNs, non-positive equity values, and running-peak drawdown logic.

Why it mattered:

- The platform stopped relying only on final equity values.
- `total_return` answers how much the strategy made or lost over the whole period.
- `max_drawdown` answers how bad the worst peak-to-trough decline was.
- This made strategy evaluation more honest.

What we deliberately avoided:

- CAGR.
- Sharpe ratio.
- Annualization assumptions.
- Volatility metrics.
- Report objects.
- Charts.

### Sprint 9 — Backtest Summary Layer

Goal: package the most important results from a pipeline output into a compact summary.

Delivered:

- `backtest_summary(result)`
- Summary keys:
  - `initial_equity`
  - `final_equity`
  - `total_return`
  - `max_drawdown`
  - `periods`
- Tests for required columns, empty input, NaNs, exact output keys, row count, and metric function reuse.

Why it mattered:

- Users no longer need to manually call every metric function after running a pipeline.
- The summary layer created a simple inspection surface without creating a full reporting framework.

What we deliberately avoided:

- Dataclasses.
- Report objects.
- Markdown or HTML reports.
- Charts.
- Benchmark comparisons.
- Annualized metrics.

### Sprint 10 — Minimal Local Research Example

Goal: add a runnable deterministic example using in-memory sample prices.

Delivered:

- `examples/minimal_research_example.py`
- Example flow:

```text
sample close prices
  -> moving_average_crossover_pipeline
  -> backtest_summary
  -> printed result tail and summary
```

- Tests for importability, `main()` execution, expected output labels, and provider isolation.

Why it mattered:

- The repository became easier for a new contributor to understand.
- A user can run one file and see the full current research flow.
- The example stayed network-free and deterministic.

What we deliberately avoided:

- CLI arguments.
- Live data.
- Charts.
- Notebooks.
- File exports.

### Sprint 11 — Local CSV Data Loader

Goal: add the first deterministic local data input path.

Delivered:

- `load_daily_prices_csv(path)`
- Required CSV columns:
  - `Date`
  - `Open`
  - `High`
  - `Low`
  - `Close`
  - `Volume`
- Date parsing into a named `DatetimeIndex`.
- Ascending date sorting.
- Validation for missing columns, invalid dates, blank dates, duplicate dates, and missing `Close` values.
- Tests using temporary CSV files.

Why it mattered:

- The project can now run research from reproducible local files instead of only hardcoded data or live providers.
- The loader creates a clean path toward future data caching and real local datasets.
- CSV validation prevents bad input data from silently polluting backtests.

What we deliberately avoided:

- A provider class.
- Live downloads.
- Caching.
- Databases.
- Parquet.
- Time zone logic.
- Adjusted-price logic.
- Split/dividend handling.
- Trading calendars.

### Sprint 12 — CSV Research Example

Goal: add a runnable local CSV-based research example.

Delivered:

- `examples/csv_research_example.py`
- `examples/data/sample_daily_prices.csv`
- Example flow:

```text
local CSV file
  -> load_daily_prices_csv
  -> close prices
  -> moving_average_crossover_pipeline
  -> backtest_summary
  -> printed result tail and summary
```

- Tests for importability, running from another working directory, expected output, provider isolation, and sample CSV usability.

Why it mattered:

- The project now has a fully local, file-based, reproducible research demo.
- The example proves the CSV loader and research pipeline work together.
- Resolving the CSV path relative to the script makes the example robust to current-working-directory changes.

What we deliberately avoided:

- Custom CSV path arguments.
- CLI parsing.
- Live downloads.
- Caching.
- Large datasets.
- Charts.
- Notebooks.

## Current Architecture After Milestone 2

```text
el_psy_quant/
  data/
    csv.py              # Local CSV daily price loader
    providers.py        # Market data provider abstraction and Yahoo Finance provider
  indicators/
    trend.py            # SMA, EMA, daily returns
  signals/
    crossover.py        # Crossover event signals
  portfolio/
    positions.py        # Long-only position states
    returns.py          # Strategy returns
    equity.py           # Equity curves
  backtesting/
    pipelines.py        # Minimal MA crossover research pipeline
  performance/
    metrics.py          # Basic performance metrics
    summary.py          # Compact backtest summary

examples/
  minimal_research_example.py
  csv_research_example.py
  data/
    sample_daily_prices.csv
```

## Current Capabilities

The project can now:

- Fetch daily market data through `YahooFinanceProvider`.
- Load daily OHLCV price data from a local CSV file.
- Calculate basic indicators from price series.
- Generate moving-average crossover event signals.
- Convert signal events into long-only position states.
- Calculate daily strategy returns using previous-day positions.
- Compound strategy returns into an equity curve.
- Calculate total return and max drawdown from an equity curve.
- Produce a compact backtest summary dictionary.
- Run a deterministic in-memory research example.
- Run a deterministic local CSV research example.

## What This Milestone Deliberately Avoided

The project intentionally did not build:

- A full reporting framework.
- A CLI application.
- A dashboard.
- Charts.
- Notebooks.
- CAGR or Sharpe ratio.
- Annualization logic.
- Benchmark comparisons.
- Transaction costs or slippage.
- Trade records.
- Cash accounting.
- A data cache.
- A database or Parquet data layer.
- Multi-asset portfolio support.
- Broker integration.

This was deliberate. Milestone 2 focused on honest evaluation and reproducible local inputs, not on looking fancy.

## Engineering Principles Reinforced

Milestone 2 reinforced several habits:

1. Prefer reproducibility over convenience.
2. Validate local data before using it.
3. Add examples only when they clarify the workflow.
4. Keep examples deterministic and network-free.
5. Keep reporting minimal until metric assumptions are explicit.
6. Do not confuse a research library with a CLI app too early.
7. Keep the platform boring in the right places.

## Next Milestone Plan — Data Reproducibility & Research Workflow

Milestone 3 should make the local research workflow more practical while still avoiding platform bloat.

Suggested sprint plan:

### Sprint 13 — Data Cache Foundation

Add a small cache utility that can write and read daily price DataFrames to a local CSV cache directory.

This should still be deterministic and explicit. No automatic magic yet.

### Sprint 14 — Yahoo-to-CSV Workflow

Add a small workflow that fetches data through `YahooFinanceProvider` and saves it to local CSV using the cache utility.

This creates a bridge between live data and reproducible local research.

### Sprint 15 — CSV Pipeline Convenience Function

Add a small helper that loads a CSV and runs the moving-average crossover pipeline in one call.

Keep it as a convenience layer, not a backtesting engine.

### Sprint 16 — Milestone 3 Documentation Refresh

Summarize the data reproducibility layer and update the README again.

## Milestone 3 Guiding Principle

Do not chase more strategy complexity yet.

The next goal is to make data workflows reproducible, inspectable, and boring.

Boring data infrastructure is good data infrastructure.