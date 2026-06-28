# Milestone 4 — Research Experimentation Foundation

## Milestone Summary

Milestone 4 made El-Psy-Quant more useful as a research tool.

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
Can we persist daily price data locally and run research from cached CSV files?
```

Milestone 4 answered:

```text
Can we run repeated local experiments and summarize their results without pretending parameter search is alpha discovery?
```

The project can now handle live download failures more clearly, run deterministic moving-average parameter sweeps from local CSV input, and summarize parameter sweep results with a descriptive overview table.

This milestone is still not about proving a profitable strategy. It is about making experiments repeatable, comparable, and easier to inspect.

## Product Thinking

The project followed this progression:

```text
Clearer download failures
  -> Deterministic parameter sweep
  -> Descriptive experiment overview
```

The key idea was to make research iteration easier without turning the project into a parameter-mining machine.

A parameter sweep is useful because it helps compare assumptions. It is dangerous when treated as proof that the best historical row is a reliable future strategy.

Milestone 4 deliberately kept the experiment layer descriptive rather than prescriptive.

## Sprint History

### Sprint 17 — Download Failure Handling

Goal: make live download failures easier to understand.

Delivered:

- Clear workflow-level error handling in `download_daily_prices_to_cache`.
- Empty provider results are rejected before cache writing.
- Provider exceptions are wrapped with ticker-specific context.
- Original provider exceptions are preserved as the cause.
- Failed or empty downloads are not written to the local cache.
- README notes that live providers can fail or be rate-limited.

Why it mattered:

- Users calling the live download workflow now see download-level errors instead of low-level cache writer errors.
- Bad or empty live data still cannot pollute the local cache.
- The live data boundary is clearer.

What we deliberately avoided:

- Retry logic.
- Exponential backoff.
- Rate-limit handling frameworks.
- yfinance-specific exception imports.
- Automatic cache fallback.
- Provider redesign.

### Sprint 18 — Moving-Average Parameter Sweep

Goal: run repeated moving-average crossover experiments from local CSV input.

Delivered:

- `moving_average_crossover_parameter_sweep(path, fast_windows, slow_windows, initial_capital=1.0)`
- One output row per valid `(fast_window, slow_window)` pair.
- Invalid pairs where `fast_window >= slow_window` are skipped.
- Empty parameter inputs are rejected.
- All-invalid grids are rejected.
- Output is sorted by `fast_window`, then `slow_window`.
- The function reuses:
  - `load_daily_prices_csv`
  - `moving_average_crossover_pipeline`
  - `backtest_summary`

Why it mattered:

- Experiments can now compare multiple parameter choices without manual repetition.
- The workflow stays deterministic and local-only.
- The output remains a plain DataFrame, which keeps it inspectable.

What we deliberately avoided:

- Best-parameter recommendation.
- Ranking score.
- Charts and heatmaps.
- Dashboards.
- CLI commands.
- File export.
- Parallel execution.
- Live downloads.

### Sprint 19 — Experiment Result Overview

Goal: summarize a parameter sweep result without ranking or recommending parameter pairs.

Delivered:

- `summarize_parameter_sweep_results(results)`
- One-row descriptive overview DataFrame.
- Stable overview columns for:
  - run count
  - window ranges
  - equity ranges
  - return ranges
  - drawdown ranges
  - period ranges
- Empty input validation.
- Missing required column validation.
- Tests confirming the function does not mutate input results.

Why it mattered:

- Users can quickly inspect experiment scale and metric distribution.
- The helper describes what happened without claiming which parameter pair should be used.
- It supports research discipline instead of optimization theater.

What we deliberately avoided:

- Best-parameter output.
- Automatic ranking.
- Score columns.
- Strategy recommendations.
- Charts.
- Generic experiment framework.

## Current Architecture After Milestone 4

```text
el_psy_quant/
  data/
    cache.py            # Local CSV cache read/write helpers
    csv.py              # Local CSV daily price loader
    providers.py        # Market data provider abstraction and Yahoo Finance provider
    workflows.py        # Explicit Yahoo-to-cache workflow with clearer failure handling
  indicators/
    trend.py            # SMA, EMA, daily returns
  signals/
    crossover.py        # Crossover event signals
  portfolio/
    positions.py        # Long-only position states
    returns.py          # Strategy returns
    equity.py           # Equity curves
  backtesting/
    experiments.py      # Parameter sweep and descriptive experiment overview helpers
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
- Fail live download workflows with clearer user-facing errors.
- Run a moving-average crossover research pipeline directly from a CSV file.
- Run deterministic moving-average parameter sweeps from local CSV input.
- Produce a descriptive one-row overview of parameter sweep results.
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

- Best-parameter recommendations.
- Automatic ranking.
- Score columns.
- Charts.
- Heatmaps.
- Dashboards.
- CLI commands.
- File exports.
- Statistical significance testing.
- Walk-forward validation.
- Train/test split.
- Benchmark comparison.
- Transaction costs or slippage.
- Multi-symbol support.
- Generic experiment framework.
- Parallel execution.
- Broker integration.

This was deliberate. Milestone 4 focused on repeatable local experimentation, not on strategy claims.

## Research Discipline Reinforced

Milestone 4 reinforced one important rule:

```text
Parameter search is not alpha discovery.
```

A parameter sweep can reveal how sensitive a strategy is to different assumptions. It cannot prove that the highest historical return row is a robust future edge.

That distinction matters. Without it, a research platform becomes a backtest overfitting machine with extra steps.

## Engineering Principles Reinforced

Milestone 4 reinforced several habits:

1. Keep live provider failures clear and contained.
2. Keep local experiments deterministic and network-free.
3. Compare experiment results, but do not blindly rank them.
4. Prefer plain DataFrames over heavy framework abstractions.
5. Make result tables stable and easy to inspect.
6. Do not overclaim profitability or strategy quality.
7. Build research discipline before adding realism layers.

## Next Milestone Plan — Strategy Realism Foundation

Milestone 5 should make backtests less toy-like by introducing basic realism.

Suggested sprint plan:

### Sprint 21 — Transaction Cost Foundation

Add a simple transaction cost model applied when positions change.

Keep it generic and explicit. Do not build broker-specific fee schedules yet.

### Sprint 22 — Slippage Foundation

Add a simple slippage model for position changes.

Keep it small. Do not simulate order books.

### Sprint 23 — Trade Record Foundation

Extract basic trade records from position changes.

This helps users inspect what the strategy actually did, not just the final equity curve.

### Sprint 24 — Milestone 5 Documentation Refresh

Summarize the strategy realism layer and update README and roadmap again.

## Milestone 5 Guiding Principle

A backtest without costs, slippage, and trade visibility is still a toy.

The next goal is to make the toy less fake without pretending it is production-grade trading infrastructure.
