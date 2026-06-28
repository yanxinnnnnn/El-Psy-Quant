# El-Psy-Quant

An AI-native quantitative research and trading platform built in public.

## Mission

Build a production-ready quantitative research platform from zero to production, using AI as an engineering teammate while keeping human judgment in control.

This project is intentionally built sprint by sprint. The goal is not to find a magic profitable strategy on day one. The goal is to build a reliable platform that can repeatedly test, evaluate, and improve trading ideas.

## Current Milestone

**Milestone 5 — Strategy Realism Foundation** is complete.

The project can now run a deterministic single-asset moving-average crossover research pipeline, evaluate the result with basic metrics, persist daily prices to a local CSV cache, connect Yahoo Finance downloads to that cache with clearer failure handling, run research directly from local CSV files, sweep moving-average parameters, summarize parameter-sweep results, apply transaction costs and slippage when positions change, and extract basic trade records from position changes.

See the milestone summaries:

```text
docs/milestones/milestone-001-research-pipeline-foundation.md
docs/milestones/milestone-002-performance-and-local-data.md
docs/milestones/milestone-003-data-reproducibility-and-research-workflow.md
docs/milestones/milestone-004-research-experimentation-foundation.md
docs/milestones/milestone-005-strategy-realism-foundation.md
```

## Current Capabilities

- Market data provider abstraction.
- Yahoo Finance daily price provider.
- Local CSV daily price loader.
- Local CSV data cache:
  - deterministic cache file paths
  - cache writing
  - cache reading
- Explicit Yahoo-to-CSV cache workflow with clearer failure handling.
- CSV-to-pipeline convenience workflow.
- Deterministic moving-average parameter sweep from local CSV input.
- Descriptive parameter-sweep overview summary.
- Basic indicators:
  - simple moving average
  - exponential moving average
  - daily return
- Moving-average crossover signal events.
- Long-only position state conversion.
- Daily gross strategy return calculation using previous-day positions.
- Transaction cost drag when positions change.
- Slippage drag when positions change.
- Net strategy return calculation after transaction costs and slippage.
- Equity curve calculation using compounded net returns.
- Basic trade record extraction from long-only position changes.
- Minimal moving-average crossover research pipeline.
- Basic performance metrics:
  - total return
  - max drawdown
- Compact backtest summary.
- Deterministic in-memory research example.
- Deterministic local CSV research example.

## Quick Start

Install [uv](https://docs.astral.sh/uv/), then install the project and development dependencies:

```bash
uv sync
```

Run the project checks:

```bash
uv run pytest
uv run ruff check .
uv run python -c "import el_psy_quant"
```

## Minimal Research Pipeline Example

```python
import pandas as pd

from el_psy_quant.backtesting import moving_average_crossover_pipeline

close = pd.Series(
    [1.0, 2.0, 3.0, 2.0, 1.0, 2.0, 3.0, 4.0],
    name="close",
)

result = moving_average_crossover_pipeline(
    close,
    fast_window=2,
    slow_window=3,
    initial_capital=1_000.0,
)

print(result.tail())
```

The result includes all intermediate research outputs:

```text
close
fast_sma
slow_sma
signal
position
asset_return
strategy_return
transaction_cost
slippage
net_strategy_return
equity
```

## Basic Performance Metrics

```python
from el_psy_quant.performance import max_drawdown, total_return

return_over_period = total_return(result["equity"])
worst_drawdown = max_drawdown(result["equity"])
```

## Backtest Summary

```python
from el_psy_quant.performance import backtest_summary

summary = backtest_summary(result)
```

## Run the Local Research Example

```bash
uv run python examples/minimal_research_example.py
```

## Load Local CSV Prices

```python
from el_psy_quant.data import load_daily_prices_csv

prices = load_daily_prices_csv("data/sample_prices.csv")
close = prices["Close"]
```

## Run the CSV Research Example

```bash
uv run python examples/csv_research_example.py
```

## Local Data Cache

```python
from el_psy_quant.data import read_daily_prices_cache, write_daily_prices_cache

path = write_daily_prices_cache(prices, "data/cache", "AAPL")
cached_prices = read_daily_prices_cache("data/cache", "AAPL")
```

## Download Yahoo Prices to the Local Cache

Calling this workflow performs a live download before writing the CSV cache.
Live providers can fail or be rate-limited. Failed or empty downloads are not
written to the local cache.

```python
from el_psy_quant.data import download_daily_prices_to_cache, read_daily_prices_cache

path = download_daily_prices_to_cache("AAPL", "data/cache", period="5y")
prices = read_daily_prices_cache("data/cache", "AAPL")
```

## Run the Research Pipeline from CSV

Transaction costs and slippage are charged when the position changes.
`strategy_return` is gross, `net_strategy_return` is after both drags, and
`equity` uses net returns.

```python
result = moving_average_crossover_pipeline(
    close,
    fast_window=20,
    slow_window=50,
    initial_capital=1_000.0,
    transaction_cost_rate=0.001,
    slippage_rate=0.0005,
)
```

Trade records are extracted from position changes for inspection, not
broker-grade accounting.

```python
from el_psy_quant.backtesting import moving_average_crossover_trade_records

trades = moving_average_crossover_trade_records(result)
```

```python
from el_psy_quant.backtesting import moving_average_crossover_from_csv

result, summary = moving_average_crossover_from_csv(
    "data/cache/AAPL.csv",
    fast_window=20,
    slow_window=50,
    initial_capital=1_000.0,
)
```

## Sweep Moving-Average Parameters

```python
from el_psy_quant.backtesting import moving_average_crossover_parameter_sweep

summary = moving_average_crossover_parameter_sweep(
    "data/cache/AAPL.csv",
    fast_windows=[5, 10, 20],
    slow_windows=[20, 50, 100],
    initial_capital=1_000.0,
)
```

```python
from el_psy_quant.backtesting import summarize_parameter_sweep_results

overview = summarize_parameter_sweep_results(summary)
```

## Module Overview

```text
el_psy_quant/
  data/          # Market data providers, CSV loading, cache helpers, and data workflows
  indicators/    # Pure indicator calculations
  signals/       # Signal event generation
  portfolio/     # Positions, returns, equity, costs, slippage, and trade records
  backtesting/   # Research pipelines, local-file workflows, experiments, and trade helpers
  performance/   # Metrics and backtest summaries
```

## Documentation

The project roadmap lives in:

```text
docs/roadmap.md
```

Sprint specifications live in:

```text
docs/sprints/
```

Milestone summaries live in:

```text
docs/milestones/
```

Important project context for AI agents lives in:

```text
AGENTS.md
```

## Engineering Principles

- AI writes, humans decide.
- Ship every sprint.
- Build capabilities, not random scripts.
- Keep the repository as the single source of truth.
- Prefer simple, reviewable code over clever code.
- Keep tests deterministic and network-free where possible.
- Make timing assumptions explicit to avoid look-ahead bias.
- Validate data at the boundary.
- Keep live downloads explicit and local research reproducible.
- Treat parameter search as comparison, not alpha discovery.
- Separate gross returns, frictions, net returns, and equity.
- Treat trade records as inspection data, not broker-grade accounting truth.

## Next Milestone

**Milestone 6 — Risk & Benchmark Foundation**

Planned direction:

1. Add CAGR and annualized volatility with explicit period assumptions.
2. Add Sharpe-style evaluation with configurable risk-free rate and frequency.
3. Compare strategy results against benchmark CSV input.
4. Refresh milestone documentation again after the risk and benchmark layer is stable.

The guiding principle for the next milestone: a strategy result without risk context and benchmark comparison is incomplete. Make evaluation more disciplined before adding multi-asset complexity.

## Disclaimer

This project is for education, research, and software engineering practice. Nothing in this repository is financial advice.
