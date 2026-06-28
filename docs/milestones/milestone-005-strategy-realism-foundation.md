# Milestone 5 — Strategy Realism Foundation

## Milestone Summary

Milestone 5 made El-Psy-Quant's backtests less toy-like.

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

The project can now apply transaction costs and slippage when long-only positions change, calculate equity from net returns after those drags, and extract simple trade records from position changes.

This milestone is still not production-grade execution infrastructure. It is a research realism layer. The goal was to stop pretending that trading is free and perfectly executed.

## Product Thinking

The project followed this progression:

```text
Transaction costs
  -> Slippage
  -> Trade records
```

The key idea was to introduce realism without jumping into full broker accounting.

A frictionless backtest is often misleading. A strategy that looks good before costs may collapse once every position change has a cost and slippage drag. Trade records then help inspect when those position changes actually happen.

Milestone 5 deliberately stayed simple:

```text
position change
  -> cost/slippage drag
  -> net return
  -> net equity
  -> inspectable trade rows
```

## Sprint History

### Sprint 21 — Transaction Cost Foundation

Goal: add a simple transaction cost model when positions change.

Delivered:

- `transaction_cost(position, cost_rate)`
- Validation for:
  - negative cost rate
  - NaN positions
  - invalid position values outside `0` and `1`
- Transaction cost based on long-only position turnover.
- Pipeline support for `transaction_cost_rate`.
- Pipeline output columns:
  - `transaction_cost`
  - `net_strategy_return`
- Equity calculated from `net_strategy_return`.
- CSV workflow and parameter sweep support for transaction costs.

Why it mattered:

- The strategy no longer assumes position changes are free.
- Gross return, transaction cost, net return, and equity are separated clearly.
- Parameter sweeps can now evaluate cost-adjusted results.

What we deliberately avoided:

- Broker-specific fee schedules.
- Minimum commissions.
- Tax models.
- Cash/share accounting.
- Order execution simulation.
- Full accounting engines.

### Sprint 22 — Slippage Foundation

Goal: add a simple slippage drag when positions change.

Delivered:

- `slippage_cost(position, slippage_rate)`
- Validation for:
  - negative slippage rate
  - NaN positions
  - invalid position values outside `0` and `1`
- Slippage based on long-only position turnover.
- Pipeline support for `slippage_rate`.
- Pipeline output column:
  - `slippage`
- Net return updated to:

```text
strategy_return - transaction_cost - slippage
```

- Equity calculated from return after both transaction cost and slippage.
- CSV workflow and parameter sweep support for slippage.

Why it mattered:

- The strategy no longer assumes perfect theoretical execution.
- Transaction costs and slippage are visible as separate drags.
- Results remain easy to inspect and deterministic.

What we deliberately avoided:

- Bid/ask spread models.
- Order book simulation.
- Volume-aware slippage.
- Market impact models.
- Broker behavior.
- Execution engines.

### Sprint 23 — Trade Record Foundation

Goal: expose basic strategy behavior by extracting trade records from position changes.

Delivered:

- `long_only_trade_records(position, close)`
- `moving_average_crossover_trade_records(result)`
- BUY rows for `0 -> 1` position changes.
- SELL rows for `1 -> 0` position changes.
- First-row long position treated as a BUY from initial flat state.
- Trade record columns:
  - `action`
  - `position_before`
  - `position_after`
  - `close`
- Optional pipeline context attached when available:
  - `transaction_cost`
  - `slippage`
  - `net_strategy_return`
  - `equity`

Why it mattered:

- The project can now inspect strategy behavior, not just final equity.
- Users can see where position changes happened.
- Costs, slippage, net return, and equity can be inspected at trade indexes.

What we deliberately avoided:

- Quantity or shares.
- Cash balances.
- Realized PnL per trade.
- Entry/exit pairing.
- Trade duration.
- Order IDs.
- Partial fills.
- Broker-grade ledgers.

## Current Architecture After Milestone 5

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
    experiments.py      # Parameter sweep and descriptive experiment overview helpers
    pipelines.py        # Minimal MA crossover research pipeline with costs/slippage
    trades.py           # Trade record helper for pipeline results
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
- Calculate gross daily strategy returns using previous-day positions.
- Calculate transaction cost drag when positions change.
- Calculate slippage drag when positions change.
- Calculate net strategy returns after transaction costs and slippage.
- Compound net strategy returns into an equity curve.
- Extract basic BUY/SELL records from long-only position changes.
- Attach cost, slippage, net return, and equity context to trade records when available.
- Calculate total return and max drawdown from an equity curve.
- Produce a compact backtest summary dictionary.
- Run deterministic local examples without network access.

## What This Milestone Deliberately Avoided

The project intentionally did not build:

- Broker-specific fee schedules.
- Minimum commissions.
- Tax models.
- Bid/ask spread models.
- Order execution simulation.
- Order book simulation.
- Volume-aware slippage.
- Market impact models.
- Position sizing beyond `0`/`1` long-only state.
- Short selling.
- Leverage.
- Cash/share accounting.
- Quantity or share tracking.
- Realized PnL per trade.
- Entry/exit pairing.
- Trade duration.
- Broker statements.
- Accounting ledgers.
- Tax lots.
- Multi-asset costs.
- Broker integration.

This was deliberate. Milestone 5 focused on research realism, not production execution infrastructure.

## Research Discipline Reinforced

Milestone 5 reinforced one important rule:

```text
A backtest without costs, slippage, and trade visibility is still a toy.
```

The project now has a less fake toy. It is still not a broker-grade simulator, and it should not be described as one.

That distinction matters. Basic frictions help prevent overly optimistic results, but they do not solve all execution realism problems.

## Engineering Principles Reinforced

Milestone 5 reinforced several habits:

1. Separate gross return, cost drag, slippage drag, net return, and equity.
2. Keep friction models explicit and inspectable.
3. Avoid hiding assumptions in framework magic.
4. Treat trade records as inspection data, not accounting truth.
5. Make realism incremental instead of jumping to an execution engine.
6. Keep deterministic tests around every financial assumption.
7. Do not overclaim execution quality or production readiness.

## Next Milestone Plan — Risk & Benchmark Foundation

Milestone 6 should improve evaluation discipline.

Suggested sprint plan:

### Sprint 25 — Annualized Metrics Foundation

Add CAGR and annualized volatility with explicit period assumptions.

Avoid hidden frequency assumptions.

### Sprint 26 — Sharpe-Style Evaluation

Add a simple Sharpe ratio helper with configurable risk-free rate and frequency.

Explain limitations clearly.

### Sprint 27 — Benchmark Comparison

Compare strategy results against benchmark CSV input.

Do not claim outperformance without context.

### Sprint 28 — Milestone 6 Documentation Refresh

Summarize the risk and benchmark layer and update README and roadmap again.

## Milestone 6 Guiding Principle

A strategy result without risk context and benchmark comparison is incomplete.

The next goal is to make evaluation more disciplined before adding multi-asset complexity.
