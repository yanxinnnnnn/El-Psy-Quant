# Milestone 3 — Data Reproducibility & Research Workflow

## Milestone Summary

Milestone 3 made El-Psy-Quant's data workflow more reproducible and practical.

Milestone 1 answered:

```text
Can we turn close prices into an equity curve?
```

Milestone 2 answered:

```text
Can we evaluate that equity curve and reproduce the workflow from local data?
```

Milestone 3 answered:

```text
Can we persist daily price data locally, connect live downloads to that local cache, and run research directly from cached CSV files?
```

The project can now write daily price data to a deterministic local CSV cache, read that cache back through the same validated CSV loader, download Yahoo Finance data into the cache through an explicit workflow, and run the moving-average crossover research flow directly from a local CSV file.

This milestone is still not about proving a profitable strategy. It is about making the research workflow reproducible, inspectable, and less dependent on live network behavior.

## Product Thinking

The project followed this progression:

```text
Local CSV Loader
  -> Local Cache Read/Write
  -> Yahoo-to-CSV Cache Workflow
  -> CSV-to-Pipeline Convenience Function
```

The key idea was to separate two different concerns:

```text
Live data providers fetch data.
Local CSV/cache files support reproducible research.
```

This separation matters because live providers can fail, change, rate-limit, or return empty results. Research should not depend on a live external service every time a strategy is evaluated.

## Sprint History

### Sprint 13 — Data Cache Foundation

Goal: add a deterministic local CSV cache layer.

Delivered:

- `cache_path(cache_dir, symbol)`
- `write_daily_prices_cache(prices, cache_dir, symbol)`
- `read_daily_prices_cache(cache_dir, symbol)`
- Safe deterministic symbol-to-file normalization.
- Cache writing with validation for:
  - empty data
  - missing required columns
  - non-`DatetimeIndex` input
  - missing dates
  - duplicate dates
  - missing `Close` values
- Cache reading through the existing `load_daily_prices_csv` function.

Why it mattered:

- Cached files are written in the same format the CSV loader already understands.
- The project avoided two competing CSV formats.
- Invalid data is rejected before being persisted.

What we deliberately avoided:

- Databases.
- Parquet.
- Compression.
- Cache expiration.
- Metadata sidecars.
- Automatic refresh.
- Provider classes.
- CLI commands.

### Sprint 14 — Yahoo-to-CSV Cache Workflow

Goal: connect live downloads to the local cache through an explicit workflow.

Delivered:

- `download_daily_prices_to_cache(ticker, cache_dir, period="5y", provider=None)`
- Provider injection for deterministic tests.
- Default usage of `YahooFinanceProvider()` when no provider is supplied.
- Input validation for empty ticker and empty period.
- Cache writing through `write_daily_prices_cache`.
- README documentation that this workflow performs a live download when called.

Why it mattered:

- The project now has a bridge from live market data to reproducible local research.
- Tests stay network-free by using fake providers and monkeypatching.
- Live downloads remain explicit rather than hidden behind local research helpers.

What we deliberately avoided:

- Automatic refresh.
- Cache freshness checks.
- Retry logic.
- Rate-limit handling.
- Start/end date support.
- Multi-symbol batch download.
- Pipeline changes.

### Sprint 15 — CSV Pipeline Convenience Function

Goal: add a small helper that runs the existing research pipeline directly from a local CSV file.

Delivered:

- `moving_average_crossover_from_csv(path, fast_window, slow_window, initial_capital=1.0)`
- A thin composition of:
  - `load_daily_prices_csv`
  - `moving_average_crossover_pipeline`
  - `backtest_summary`
- Return value:

```python
(result, summary)
```

Where:

- `result` is the full pipeline DataFrame.
- `summary` is the compact backtest summary dictionary.

Why it mattered:

- Users can run the most common local research flow with one small function.
- The full intermediate result remains inspectable.
- The helper stays local and network-free.

What we deliberately avoided:

- CLI commands.
- Reports.
- Dataclasses.
- Charts.
- Notebooks.
- Live downloads.
- Cache refresh.
- Automatic Yahoo fallback.
- Strategy classes.
- Generic backtesting engine abstractions.

## Current Architecture After Milestone 3

```text
el_psy_quant/
  data/
    cache.py            # Local CSV cache read/write helpers
    csv.py              # Local CSV daily price loader
    providers.py        # Market data provider abstraction and Yahoo Finance provider
    workflows.py        # Explicit Yahoo-to-cache workflow
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
    workflows.py        # CSV-to-pipeline convenience workflow
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
- Validate local CSV data at the boundary.
- Write daily prices to a deterministic local CSV cache.
- Read cached daily prices through the same CSV loader.
- Download Yahoo Finance data into the local cache through an explicit workflow.
- Run a moving-average crossover research pipeline directly from a CSV file.
- Calculate basic indicators from price series.
- Generate moving-average crossover event signals.
- Convert signal events into long-only position states.
- Calculate daily strategy returns using previous-day positions.
- Compound strategy returns into an equity curve.
- Calculate total return and max drawdown from an equity curve.
- Produce a compact backtest summary dictionary.
- Run deterministic local examples without network access.

## What This Milestone Deliberately Avoided

The project intentionally did not build:

- A full data platform.
- A CLI application.
- A dashboard.
- A report system.
- A generic backtesting engine.
- Strategy classes.
- Multi-asset portfolio support.
- Automatic cache refresh.
- Cache expiration.
- Metadata sidecar files.
- Retry/rate-limit logic.
- Start/end date download APIs.
- Transaction costs or slippage.
- Benchmark comparisons.
- Broker integration.

This was deliberate. Milestone 3 focused on reproducible data workflow, not on platform bloat.

## Lesson From Yahoo Finance Rate Limits

During local testing, Yahoo Finance returned a rate-limit error and `yfinance` produced an empty DataFrame.

This confirmed the project direction:

```text
Live providers are useful inputs, but they are not reliable research storage.
```

The cache writer correctly rejected the empty DataFrame instead of writing a broken CSV file. That is the right failure mode.

A future sprint may improve the live-download error message so provider failures are easier to understand, but the underlying design is sound: bad or empty data should not enter the local cache.

## Engineering Principles Reinforced

Milestone 3 reinforced several habits:

1. Keep live downloads explicit.
2. Treat local cached data as the reproducible research input.
3. Reuse existing validation instead of duplicating rules.
4. Do not write invalid data to disk.
5. Keep convenience functions thin and inspectable.
6. Keep tests deterministic and network-free.
7. Build boring data infrastructure before chasing strategy complexity.

## Next Milestone Plan — Research Experimentation Foundation

Milestone 4 should make local strategy experimentation easier and more honest while still avoiding overfitting theater.

Suggested sprint plan:

### Sprint 17 — Download Failure Handling

Improve error handling around live provider downloads so empty downloads and provider failures produce clearer messages.

This is especially useful after seeing Yahoo Finance rate limits in local testing.

### Sprint 18 — Moving-Average Parameter Sweep

Add a deterministic local parameter sweep for moving-average crossover windows using CSV input.

The goal is comparison and learning, not claiming the best parameters are profitable.

### Sprint 19 — Experiment Result Summary

Add a small tabular summary for multiple parameter runs.

Keep it as a DataFrame, not a dashboard or report framework.

### Sprint 20 — Milestone 4 Documentation Refresh

Summarize the experimentation layer and update README again.

## Milestone 4 Guiding Principle

Do not confuse parameter search with alpha discovery.

The next goal is to make experiments repeatable, comparable, and easy to inspect.