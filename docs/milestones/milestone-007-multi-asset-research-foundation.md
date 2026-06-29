# Milestone 7 — Multi-Asset Research Foundation

## Milestone Summary

Milestone 7 moved El-Psy-Quant from single-symbol research toward multi-symbol research.

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

Milestone 5 answered:

```text
Can we make the backtest account for basic frictions and expose the strategy's position-change behavior?
```

Milestone 6 answered:

```text
Can we evaluate strategy results with explicit annualized metrics, risk-adjusted return, and benchmark context?
```

Milestone 7 answered:

```text
Can we run the same local research workflow across multiple symbols and inspect the results side by side?
```

The project can now load multiple local CSV/cache files, run the existing moving-average crossover pipeline independently across symbols, and summarize the per-symbol results into a compact comparison table.

This milestone is still not portfolio construction. It is a multi-symbol research breadth layer. The goal was to stop being trapped in one-symbol experiments while avoiding premature allocation logic.

## Product Thinking

The project followed this progression:

```text
Multi-symbol local input
  -> Independent multi-symbol strategy execution
  -> Cross-symbol summary
```

The key idea was to expand breadth without pretending to have a portfolio engine.

A single-symbol workflow is useful, but it can be misleading if every research habit is built around one ticker. Serious research eventually needs the ability to ask:

```text
Does the same workflow behave similarly across multiple symbols?
Which symbols look strong or weak under the same assumptions?
Are results broadly repeatable or isolated to one asset?
```

Milestone 7 deliberately kept the workflow simple:

```text
symbol -> local prices
symbol -> independent pipeline result
symbol -> summary row
```

There is no capital allocation, no portfolio equity curve, and no rebalancing yet.

## Sprint History

### Sprint 29 — Multi-Symbol Local Input

Goal: add deterministic local multi-symbol price loading helpers.

Delivered:

- `load_daily_prices_csvs(paths_by_symbol)`
- `read_daily_prices_caches(cache_dir, symbols)`
- Symbol normalization using:

```text
symbol.strip().upper()
```

- Strict duplicate normalized symbol detection.
- Empty input validation.
- Reuse of existing single-file CSV and cache readers.
- Local-only, deterministic tests.

Why it mattered:

- Future multi-symbol workflows need a stable `symbol -> prices` input shape.
- Local reproducibility stays ahead of live convenience.
- Symbol normalization prevents subtle duplicate-key bugs.

What we deliberately avoided:

- Live downloads.
- Yahoo provider changes.
- Cache writing changes.
- Strategy execution.
- Portfolio logic.
- CLI commands.

### Sprint 30 — Multi-Symbol Strategy Execution

Goal: run the existing moving-average crossover pipeline independently across multiple symbols.

Delivered:

- `moving_average_crossover_multi_symbol(...)`
- Input shape:

```text
symbol -> prices DataFrame
```

- Output shape:

```text
symbol -> pipeline result DataFrame
```

- Reuse of the existing single-symbol `moving_average_crossover_pipeline`.
- Pass-through support for:
  - `fast_window`
  - `slow_window`
  - `initial_capital`
  - `transaction_cost_rate`
  - `slippage_rate`
- Symbol normalization and duplicate detection consistent with Sprint 29.

Why it mattered:

- The same strategy workflow can now run across many symbols without manual user-code loops.
- Each symbol stays inspectable.
- The implementation avoids premature portfolio construction.

What we deliberately avoided:

- Date alignment across symbols.
- Capital allocation.
- Rebalancing.
- Portfolio equity curves.
- Equal-weight portfolios.
- Symbol ranking.

### Sprint 31 — Cross-Symbol Summary

Goal: summarize independent per-symbol pipeline results into one comparison table.

Delivered:

- `summarize_multi_symbol_results(...)`
- One summary row per symbol.
- Reuse of `backtest_summary`.
- Optional annualized and Sharpe-style metrics via:
  - `periods_per_year`
  - `annual_risk_free_rate`
- Deterministic row order based on input order.
- Symbol normalization and duplicate detection consistent with prior sprints.

Why it mattered:

- Multi-symbol results need a compact inspection layer.
- Users can compare final equity, total return, drawdown, CAGR, volatility, and Sharpe-style metrics across symbols.
- The summary remains comparison output, not trading decision automation.

What we deliberately avoided:

- Portfolio optimization.
- Top-N selection.
- Symbol ranking for trading decisions.
- Multi-symbol trade aggregation.
- Date alignment across symbols.
- File export.
- Dashboards.

## Current Architecture After Milestone 7

```text
el_psy_quant/
  data/
    cache.py            # Local CSV cache read/write helpers
    csv.py              # Local CSV daily price loader
    multi.py            # Local multi-symbol CSV/cache loading helpers
    providers.py        # Market data provider abstraction and Yahoo Finance provider
    workflows.py        # Explicit Yahoo-to-cache workflow with clearer failure handling
  indicators/
    trend.py            # SMA, EMA, daily returns
  signals/
    crossover.py        # Crossover event signals
  portfolio/
    costs.py            # Transaction cost drag from position turnover
    equity.py           # Equity curves
    positions.py        # Long-only position states
    returns.py          # Strategy returns
    slippage.py         # Slippage drag from position turnover
    trades.py           # Long-only trade record extraction
  backtesting/
    benchmarks.py       # Local buy-and-hold benchmark comparison
    experiments.py      # Parameter sweep and descriptive experiment overview helpers
    multi.py            # Multi-symbol strategy execution and summary helpers
    pipelines.py        # Minimal MA crossover research pipeline with costs/slippage
    trades.py           # Trade record helper for pipeline results
    workflows.py        # CSV-to-pipeline convenience workflow
  performance/
    metrics.py          # Total return, drawdown, annualized metrics, Sharpe-style ratio
    summary.py          # Compact backtest summary with optional annualized/risk metrics

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
- Load multiple local CSV files into a symbol-to-prices mapping.
- Read multiple cached local price files into a symbol-to-prices mapping.
- Download Yahoo Finance data into the local cache through an explicit workflow.
- Fail live download workflows with clearer user-facing errors.
- Run a moving-average crossover research pipeline directly from a CSV file.
- Run deterministic moving-average parameter sweeps from local CSV input.
- Produce a descriptive one-row overview of parameter sweep results.
- Calculate basic indicators from price series.
- Generate moving-average crossover event signals.
- Convert signal events into long-only position states.
- Calculate gross daily strategy returns using previous-day positions.
- Calculate transaction cost drag when positions change.
- Calculate slippage drag when positions change.
- Calculate net strategy returns after transaction costs and slippage.
- Compound net strategy returns into an equity curve.
- Extract basic BUY/SELL records from long-only position changes.
- Attach cost, slippage, net return, and equity context to trade records when available.
- Calculate total return and max drawdown from an equity curve.
- Calculate CAGR from an equity curve with explicit period assumptions.
- Calculate annualized volatility from return series with explicit period assumptions.
- Calculate a Sharpe-style ratio with explicit risk-free-rate and frequency assumptions.
- Produce compact backtest summaries with optional annualized and risk-adjusted metrics.
- Compare a strategy result against a local CSV buy-and-hold benchmark over shared dates.
- Run the moving-average crossover pipeline independently across multiple symbols.
- Summarize independent multi-symbol pipeline results into one comparison table.
- Run deterministic local examples without network access.

## What This Milestone Deliberately Avoided

The project intentionally did not build:

- Portfolio optimization.
- Capital allocation.
- Rebalancing logic.
- Portfolio equity curves.
- Equal-weight portfolios.
- Symbol ranking for trading decisions.
- Top-N selection.
- Multi-symbol trade record aggregation.
- Date alignment across symbols.
- Cross-symbol benchmark aggregation.
- Multi-asset risk models.
- Correlation or covariance analysis.
- Live multi-symbol downloads.
- Dashboards.
- File exports.
- Databases.

This was deliberate. Milestone 7 focused on multi-symbol research breadth, not portfolio management.

## Research Discipline Reinforced

Milestone 7 reinforced one important rule:

```text
Multi-symbol research is not automatically portfolio research.
```

Running a strategy across multiple symbols is useful. Summarizing the results is useful. But none of that means the project has made claims about capital allocation, diversification, portfolio risk, or production trading.

That distinction matters. Without it, a simple batch runner can accidentally get marketed as an investment engine. That would be nonsense with a nice README.

## Engineering Principles Reinforced

Milestone 7 reinforced several habits:

1. Keep local reproducibility ahead of live convenience.
2. Normalize symbols consistently.
3. Reject duplicate normalized symbols early.
4. Reuse stable single-symbol functions instead of duplicating logic.
5. Keep per-symbol results inspectable.
6. Preserve deterministic order for user-facing tables.
7. Treat cross-symbol summaries as comparison output, not trading instructions.
8. Avoid portfolio complexity until the research layer is stable.

## Next Milestone Plan — Research Operations Foundation

Milestone 8 should make repeated local research workflows easier to run and inspect.

Suggested sprint plan:

### Sprint 33 — Experiment Config Foundation

Add a simple YAML or TOML config format for local experiments.

Keep it small. Do not build a config framework.

### Sprint 34 — Local Experiment Output Layout

Add a deterministic local output folder structure for experiment results.

No database yet.

### Sprint 35 — Minimal CLI Wrapper

Add a small CLI command that wraps existing experiment functions.

The CLI should call stable functions, not become the architecture.

### Sprint 36 — Milestone 8 Documentation Refresh

Summarize the research operations layer and update README and roadmap again.

## Milestone 8 Guiding Principle

A research platform becomes more useful when experiments can be configured, repeated, and inspected consistently.

The next goal is to make local research workflows more operational without turning the project into a heavy framework.
