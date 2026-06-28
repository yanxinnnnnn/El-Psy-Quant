# El-Psy-Quant

An AI-native quantitative research and trading platform built in public.

## Mission

Build a production-ready quantitative research platform from zero to production, using AI as an engineering teammate while keeping human judgment in control.

This project is intentionally built sprint by sprint. The goal is not to find a magic profitable strategy on day one. The goal is to build a reliable platform that can repeatedly test, evaluate, and improve trading ideas.

## Current Milestone

**Milestone 3 — Data Reproducibility & Research Workflow** is complete.

The project can now run a deterministic single-asset moving-average crossover research pipeline, evaluate the result with basic metrics, persist daily prices to a local CSV cache, connect Yahoo Finance downloads to that cache, and run research directly from local CSV files.

See the milestone summaries:

```text
docs/milestones/milestone-001-research-pipeline-foundation.md
docs/milestones/milestone-002-performance-and-local-data.md
docs/milestones/milestone-003-data-reproducibility-and-research-workflow.md
```

## Current Capabilities

- Market data provider abstraction.
- Yahoo Finance daily price provider.
- Local CSV daily price loader.
- Local CSV data cache:
  - deterministic cache file paths
  - cache writing
  - cache reading
- Explicit Yahoo-to-CSV cache workflow.
- CSV-to-pipeline convenience workflow.
- Basic indicators:
  - simple moving average
  - exponential moving average
  - daily return
- Moving-average crossover signal events.
- Long-only position state conversion.
- Daily strategy return calculation using previous-day positions.
- Equity curve calculation using compounded returns.
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

```python
from el_psy_quant.data import download_daily_prices_to_cache, read_daily_prices_cache

path = download_daily_prices_to_cache("AAPL", "data/cache", period="5y")
prices = read_daily_prices_cache("data/cache", "AAPL")
```

## Run the Research Pipeline from CSV

```python
from el_psy_quant.backtesting import moving_average_crossover_from_csv

result, summary = moving_average_crossover_from_csv(
    "data/cache/AAPL.csv",
    fast_window=20,
    slow_window=50,
    initial_capital=1_000.0,
)
```

## Module Overview

```text
el_psy_quant/
  data/          # Market data providers, CSV loading, cache helpers, and data workflows
  indicators/    # Pure indicator calculations
  signals/       # Signal event generation
  portfolio/     # Positions, returns, and equity curves
  backtesting/   # Research pipelines and local-file workflows
  performance/   # Metrics and backtest summaries
```

## Documentation

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

## Next Milestone

**Milestone 4 — Research Experimentation Foundation**

Planned direction:

1. Improve live download failure handling so provider errors and empty downloads are easier to understand.
2. Add a deterministic moving-average parameter sweep using local CSV input.
3. Add a small experiment result summary table.
4. Refresh milestone documentation again after the experimentation layer is stable.

The guiding principle for the next milestone: do not confuse parameter search with alpha discovery. Make experiments repeatable, comparable, and easy to inspect.

## Disclaimer

This project is for education, research, and software engineering practice. Nothing in this repository is financial advice.
