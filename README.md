# El-Psy-Quant

An AI-native quantitative research and trading platform built in public.

## Mission

Build a production-ready quantitative research platform from zero to production, using AI as an engineering teammate while keeping human judgment in control.

This project is intentionally built sprint by sprint. The goal is not to find a magic profitable strategy on day one. The goal is to build a reliable platform that can repeatedly test, evaluate, and improve trading ideas.

## Current Milestone

**Milestone 8 — Research Operations Foundation** is complete.

The project can now run deterministic single-symbol and multi-symbol moving-average crossover research workflows, evaluate results with basic and annualized metrics, persist daily prices to a local CSV cache, connect Yahoo Finance downloads to that cache with clearer failure handling, run research directly from local CSV files, sweep moving-average parameters, summarize parameter-sweep results, apply transaction costs and slippage when positions change, extract basic trade records from position changes, calculate Sharpe-style risk-adjusted metrics, compare strategy results against a local CSV buy-and-hold benchmark over shared dates, load multiple local symbols, run the existing strategy independently across symbols, summarize cross-symbol results into a compact comparison table, describe local experiments with YAML, create deterministic local output folders, and run one local configured experiment from a thin CLI wrapper.

See the milestone summaries:

```text
docs/milestones/milestone-001-research-pipeline-foundation.md
docs/milestones/milestone-002-performance-and-local-data.md
docs/milestones/milestone-003-data-reproducibility-and-research-workflow.md
docs/milestones/milestone-004-research-experimentation-foundation.md
docs/milestones/milestone-005-strategy-realism-foundation.md
docs/milestones/milestone-006-risk-and-benchmark-foundation.md
docs/milestones/milestone-007-multi-asset-research-foundation.md
docs/milestones/milestone-008-research-operations-foundation.md
```

## Current Capabilities

- Market data provider abstraction.
- Yahoo Finance daily price provider.
- Local CSV daily price loader.
- Local CSV data cache:
  - deterministic cache file paths
  - cache writing
  - cache reading
- Multi-symbol local input:
  - load multiple local CSV files by symbol
  - read multiple cached price files by symbol
  - normalize and validate symbols consistently
- Local YAML experiment config loading and validation for configured local research workflows.
- Deterministic local experiment output directories and reserved artifact paths.
- Minimal `argparse` CLI for the current local configured crossover workflow,
  writing only copied config, basic metadata, and a cross-symbol summary.
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
- Independent multi-symbol moving-average crossover execution.
- Cross-symbol summary table for independent per-symbol results.
- Basic performance metrics:
  - total return
  - max drawdown
- Annualized performance metrics:
  - CAGR
  - annualized volatility
- Sharpe-style risk-adjusted evaluation with explicit frequency and risk-free-rate assumptions.
- Local CSV buy-and-hold benchmark comparison over shared dates.
- Compact backtest summary with optional annualized and risk-adjusted metrics.
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

Annualized summary metrics are optional and require explicit assumptions:

```python
summary = backtest_summary(
    result,
    periods_per_year=252,
    annual_risk_free_rate=0.02,
)
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

Annualized metrics require an explicit frequency. For daily trading data, 252
periods per year is common, but it is not universal.

```python
from el_psy_quant.performance import annualized_volatility, cagr

annual_return = cagr(result["equity"], periods_per_year=252)
annual_vol = annualized_volatility(
    result["net_strategy_return"], periods_per_year=252
)
```

Sharpe compares excess return with volatility. Its frequency and risk-free-rate
assumptions must be explicit; a higher value is not proof of strategy quality.

```python
from el_psy_quant.performance import sharpe_ratio

sharpe = sharpe_ratio(
    result["net_strategy_return"],
    periods_per_year=252,
    annual_risk_free_rate=0.02,
)
```

Benchmark comparison uses a local CSV and simple buy-and-hold performance over
shared dates. Outperformance claims should be made carefully.

```python
from el_psy_quant.backtesting import compare_to_buy_and_hold_benchmark

comparison = compare_to_buy_and_hold_benchmark(
    result,
    "data/cache/SPY.csv",
    initial_capital=1_000.0,
    periods_per_year=252,
    annual_risk_free_rate=0.02,
)
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

## Multi-Symbol Research

Multi-symbol loading, execution, and summaries are local-only. Each symbol runs
independently on its own dates. This does not align dates, allocate capital,
rebalance positions, or build a portfolio.

```python
from el_psy_quant.data import load_daily_prices_csvs, read_daily_prices_caches

prices_by_symbol = load_daily_prices_csvs(
    {
        "AAPL": "data/cache/AAPL.csv",
        "MSFT": "data/cache/MSFT.csv",
    }
)
cached_prices_by_symbol = read_daily_prices_caches(
    "data/cache",
    ["AAPL", "MSFT"],
)
```

```python
from el_psy_quant.backtesting import moving_average_crossover_multi_symbol
from el_psy_quant.data import read_daily_prices_caches

prices_by_symbol = read_daily_prices_caches("data/cache", ["AAPL", "MSFT"])
results_by_symbol = moving_average_crossover_multi_symbol(
    prices_by_symbol,
    fast_window=20,
    slow_window=50,
    initial_capital=1_000.0,
)
```

Cross-symbol summaries compare independent per-symbol results. They do not
align dates, allocate capital, or build a portfolio.

```python
from el_psy_quant.backtesting import summarize_multi_symbol_results

summary = summarize_multi_symbol_results(
    results_by_symbol,
    periods_per_year=252,
    annual_risk_free_rate=0.02,
)
```

## Local Experiment Configuration

Experiments can be described by a small local YAML file:

```yaml
experiment:
  name: ma-crossover-local
  strategy: moving_average_crossover
data:
  source: csv
  paths:
    AAPL: data/cache/AAPL.csv
    MSFT: data/cache/MSFT.csv
parameters:
  fast_window: 20
  slow_window: 50
  initial_capital: 1000.0
evaluation:
  periods_per_year: 252
  annual_risk_free_rate: 0.02
```

```python
from el_psy_quant.config import load_experiment_config

config = load_experiment_config("experiment.yaml")
```

The config loader validates local experiment settings. The current configured
workflow supports the existing moving-average crossover strategy only.

## Local Experiment Output Layout

Create deterministic local directories for future experiment artifacts:

```python
from el_psy_quant.outputs import create_experiment_output_layout

layout = create_experiment_output_layout(
    "outputs",
    "ma-crossover-local",
    run_id="20260630T141500Z",
)
```

The layout helper creates the experiment, run, results, and logs directories.
It does not itself run experiments, write result files, or add a database.

## Run a Local Configured Experiment

```bash
el-psy-quant run experiment.yaml --output-root outputs --run-id 20260630T141500Z
```

The command runs the current moving-average crossover workflow from local CSV
or cache data and writes only:

```text
config.yaml
metadata.json
results/summary.csv
logs/
```

It does not download live data or add dashboards, reports, databases, portfolio
construction, or interactive prompts.

## Module Overview

```text
el_psy_quant/
  cli.py         # Thin argparse entrypoint for local configured experiments
  config.py      # Load and validate local YAML experiment settings; no execution or CLI
  outputs.py     # Create deterministic local experiment directories and reserved paths
  data/          # Market data providers, CSV loading, cache helpers, data workflows, and multi-symbol input
  indicators/    # Pure indicator calculations
  signals/       # Signal event generation
  portfolio/     # Positions, returns, equity, costs, slippage, and trade records
  backtesting/   # Research pipelines, local-file workflows, experiments, trade helpers, benchmarks, and multi-symbol research helpers
  performance/   # Metrics, annualized evaluation, Sharpe-style ratio, and backtest summaries
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
- Keep annualization and risk-free-rate assumptions explicit.
- Compare against benchmarks before making strategy-quality claims.
- Treat multi-symbol research as breadth, not portfolio construction.
- Keep operational wrappers thin; CLI should wrap stable functions, not become the architecture.

## Next Step

**Sprint 38 — GitHub Actions CI Foundation**

Milestone 9 will focus on project quality before adding more research surface area. The next sprint should add GitHub-hosted checks so future PRs prove that `pytest`, `ruff`, import checks, and CLI help still work.

## Disclaimer

This project is for education, research, and software engineering practice. Nothing in this repository is financial advice.
