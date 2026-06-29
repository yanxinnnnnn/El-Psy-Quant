# Milestone 6 — Risk & Benchmark Foundation

## Milestone Summary

Milestone 6 made El-Psy-Quant's evaluation layer more disciplined.

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

The project can now calculate CAGR, annualized volatility, Sharpe-style ratio, and compare strategy results against a local CSV buy-and-hold benchmark over shared dates.

This milestone is still not an advanced performance attribution system. It is an evaluation discipline layer. The goal was to stop reading total return in isolation.

## Product Thinking

The project followed this progression:

```text
Annualized metrics
  -> Sharpe-style evaluation
  -> Benchmark comparison
```

The key idea was to make performance numbers harder to misread.

A strategy result is incomplete if it only says:

```text
The strategy made money.
```

A more useful evaluation asks:

```text
How fast did it compound?
How volatile was it?
How much excess return did it earn per unit of volatility?
Did it beat a simple buy-and-hold benchmark over the same dates?
```

Milestone 6 deliberately kept the evaluation layer simple and explicit.

## Sprint History

### Sprint 25 — Annualized Metrics Foundation

Goal: add CAGR and annualized volatility with explicit period assumptions.

Delivered:

- `cagr(equity, periods_per_year)`
- `annualized_volatility(returns, periods_per_year)`
- Backtest summary support for optional annualized metrics.
- Explicit `periods_per_year` argument instead of hidden frequency assumptions.
- CAGR based on elapsed periods using `len(equity) - 1`.
- Annualized volatility using sample standard deviation.

Why it mattered:

- Total return across different time spans is easy to misread.
- CAGR makes growth rate comparable across backtest lengths.
- Annualized volatility adds basic risk context.
- Frequency assumptions stay visible instead of being buried inside the implementation.

What we deliberately avoided:

- Sharpe ratio.
- Benchmark comparison.
- Rolling metrics.
- Charts.
- Dashboards.
- Statistical significance tests.

### Sprint 26 — Sharpe-Style Evaluation

Goal: add a simple risk-adjusted return metric.

Delivered:

- `sharpe_ratio(returns, periods_per_year, annual_risk_free_rate=0.0)`
- Explicit conversion from annual risk-free rate to periodic risk-free rate:

```text
(1 + annual_risk_free_rate) ** (1 / periods_per_year) - 1
```

- Annualized arithmetic excess return divided by annualized volatility.
- Zero-volatility validation.
- Backtest summary support for optional Sharpe-style metric.
- Preference for `net_strategy_return` when available, with `strategy_return` fallback.

Why it mattered:

- Return alone does not show whether the volatility was worth it.
- Sharpe-style evaluation connects excess return to risk.
- Explicit risk-free-rate and frequency assumptions reduce hidden magic.

What we deliberately avoided:

- Sortino ratio.
- Calmar ratio.
- Information ratio.
- Rolling Sharpe.
- Benchmark comparison.
- Factor analytics.

### Sprint 27 — Benchmark Comparison

Goal: compare strategy results against a simple local buy-and-hold benchmark.

Delivered:

- `compare_to_buy_and_hold_benchmark(...)`
- Local benchmark CSV input.
- Benchmark `Close` prices loaded with the existing CSV loader.
- Strict alignment by shared index values.
- No row-number alignment.
- No forward-fill or back-fill.
- Benchmark buy-and-hold returns from aligned close prices.
- Flat strategy, benchmark, and excess metric output.
- Optional annualized and Sharpe-style metrics when `periods_per_year` is provided.

Why it mattered:

- A strategy that makes money can still underperform a simple benchmark.
- Benchmark comparison gives the strategy result context.
- Date alignment rules reduce accidental comparison errors.

What we deliberately avoided:

- Alpha and beta.
- Information ratio.
- Tracking error.
- Factor models.
- Rolling benchmark comparison.
- Multi-benchmark support.
- Benchmark downloads.
- Multi-asset research.

## Current Architecture After Milestone 6

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
    costs.py            # Transaction cost drag from position turnover
    equity.py           # Equity curves
    positions.py        # Long-only position states
    returns.py          # Strategy returns
    slippage.py         # Slippage drag from position turnover
    trades.py           # Long-only trade record extraction
  backtesting/
    benchmarks.py       # Local buy-and-hold benchmark comparison
    experiments.py      # Parameter sweep and descriptive experiment overview helpers
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
- Run deterministic local examples without network access.

## What This Milestone Deliberately Avoided

The project intentionally did not build:

- Alpha or beta.
- Information ratio.
- Tracking error.
- Factor models.
- Rolling metrics.
- Rolling Sharpe.
- Rolling benchmark comparison.
- Monthly or yearly breakdowns.
- Drawdown duration.
- VaR or CVaR.
- Statistical significance tests.
- Charts.
- Dashboards.
- CLI commands.
- File exports.
- Multi-benchmark support.
- Multi-asset portfolio research.
- Benchmark download workflows.

This was deliberate. Milestone 6 focused on basic evaluation discipline, not advanced attribution or portfolio analytics.

## Research Discipline Reinforced

Milestone 6 reinforced one important rule:

```text
A strategy result without risk context and benchmark comparison is incomplete.
```

Total return is not enough. A high-return strategy may be too volatile, may fail after costs, or may simply underperform a passive benchmark.

This milestone made evaluation more honest without pretending the project now has full institutional-grade performance analytics.

## Engineering Principles Reinforced

Milestone 6 reinforced several habits:

1. Keep annualization assumptions explicit.
2. Do not hide `252` as a universal truth.
3. Prefer net returns when costs and slippage are available.
4. Treat Sharpe-style metrics as context, not proof.
5. Align benchmark comparisons by shared dates only.
6. Do not forward-fill or back-fill benchmark data silently.
7. Keep benchmark logic simple before adding attribution layers.
8. Avoid overclaiming outperformance.

## Next Milestone Plan — Multi-Asset Research Foundation

Milestone 7 should move the project from single-symbol research toward multi-symbol research.

Suggested sprint plan:

### Sprint 29 — Multi-Symbol Local Input

Support loading multiple local CSV/cache paths into a simple symbol-to-prices structure.

Keep it local-only. Do not add portfolio optimization.

### Sprint 30 — Multi-Symbol Strategy Execution

Run the existing moving-average crossover workflow across multiple symbols.

Keep per-symbol outputs inspectable.

### Sprint 31 — Cross-Symbol Summary

Aggregate multi-symbol results into a compact summary table.

Avoid capital allocation optimization.

### Sprint 32 — Milestone 7 Documentation Refresh

Summarize the multi-asset research layer and update README and roadmap again.

## Milestone 7 Guiding Principle

Single-symbol research is useful, but real research eventually needs breadth.

The next goal is to run the same disciplined workflow across multiple symbols while keeping results reproducible and inspectable.
