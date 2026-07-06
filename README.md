# El-Psy-Quant

An AI-native quantitative research and trading platform built in public.

## Mission

Build a production-ready quantitative research platform from zero to production, using AI as an engineering teammate while keeping human judgment in control.

This project is intentionally built sprint by sprint. The goal is not to find a magic profitable strategy on day one. The goal is to build a reliable platform that can repeatedly test, evaluate, and improve trading ideas.

## Current Milestone

**Milestone 13 — Portfolio Construction Foundation** is planned.

Milestone 12 closed the configured input-boundary chain:

```text
configured symbols -> local price data -> configured input validation -> strategy execution
```

Milestone 13 should now define how independent per-symbol research results become portfolio-level returns under explicit assumptions about alignment, capital, weights, and aggregation.

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
docs/milestones/milestone-009-project-quality-foundation.md
docs/milestones/milestone-010-experiment-artifact-and-comparison-foundation.md
docs/milestones/milestone-011-strategy-interface-foundation.md
docs/milestones/milestone-012-data-integrity-and-universe-foundation.md
docs/milestones/milestone-013-portfolio-construction-foundation.md
```

## Current Capabilities

- Market data provider abstraction.
- Yahoo Finance daily price provider.
- Local CSV daily price loader.
- Local CSV data cache:
  - deterministic cache file paths
  - cache writing
  - cache reading
- Local daily price validation:
  - required OHLCV columns
  - `DatetimeIndex`
  - missing and duplicate date rejection
  - numeric and non-missing `Close`
- Symbol universe discipline:
  - symbol normalization
  - blank symbol rejection
  - duplicate rejection after normalization
  - immutable configured order
- Multi-symbol local input:
  - load multiple local CSV files by symbol
  - read multiple cached price files by symbol
  - normalize and validate symbols consistently
- Local YAML experiment config loading and validation for configured local research workflows.
- Configured-run input validation before strategy execution.
- Deterministic local experiment output directories and reserved artifact paths.
- Minimal `argparse` CLI for local configured experiments.
- Stable configured-run artifacts:
  - copied `config.yaml`
  - `metadata.json`
  - `manifest.json`
  - `results/summary.csv`
  - `results/metrics.json`
  - `logs/`
- Saved-run comparison helper that combines existing metrics from local run artifacts without ranking or recomputing metrics.
- Strategy interface foundation:
  - minimal `Strategy` protocol
  - strategy result validation helper
  - `MovingAverageCrossoverStrategy` adapter
  - deterministic exact-name strategy resolver
  - configured experiment execution through the strategy boundary
- GitHub Actions CI for pull requests and pushes to `main`.
- Local quality gate in `scripts/check.py`, used by CI as the quality command source of truth.
- Repository hygiene guardrails through `.gitattributes` and a concise pull request template.
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

Run the project checks individually:

```bash
uv run pytest
uv run ruff check .
uv run python -c "import el_psy_quant"
```

Run the same complete quality gate as GitHub Actions with one local command:

```bash
uv run python scripts/check.py
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

## Data Validation

Daily price validation is intentionally structural and local. It checks that a loaded DataFrame is usable by the research system, but it does not prove that prices are correct market truth.

```python
from el_psy_quant.data import validate_daily_prices

validate_daily_prices(prices)
```

Configured price maps can be validated with symbol context:

```python
from el_psy_quant.data import validate_daily_prices_by_symbol

validate_daily_prices_by_symbol({"AAPL": prices})
```

## Symbol Universe

A local research symbol universe defines which symbols are included in a run and how they are normalized.

```python
from el_psy_quant.data import build_symbol_universe, normalize_symbol

normalize_symbol(" aapl ")
# "AAPL"

build_symbol_universe(["msft", " AAPL "])
# ("MSFT", "AAPL")
```

This is not an investable universe database, security master, or live symbol lookup service.

## Local Data Cache

```python
from el_psy_quant.data import read_daily_prices_cache, write_daily_prices_cache

path = write_daily_prices_cache(prices, "data/cache", "AAPL")
cached_prices = read_daily_prices_cache("data/cache", "AAPL")
```

## Download Yahoo Prices to the Local Cache

Calling this workflow performs a live download before writing the CSV cache. Live providers can fail or be rate-limited. Failed or empty downloads are not written to the local cache.

```python
from el_psy_quant.data import download_daily_prices_to_cache, read_daily_prices_cache

path = download_daily_prices_to_cache("AAPL", "data/cache", period="5y")
prices = read_daily_prices_cache("data/cache", "AAPL")
```

## Multi-Symbol Research

Multi-symbol loading, execution, and summaries are local-only. Each symbol runs independently on its own dates. This does not align dates, allocate capital, rebalance positions, or build a portfolio.

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

results_by_symbol = moving_average_crossover_multi_symbol(
    cached_prices_by_symbol,
    fast_window=20,
    slow_window=50,
    initial_capital=1_000.0,
)
```

Cross-symbol summaries compare independent per-symbol results. They do not align dates, allocate capital, or build a portfolio.

```python
from el_psy_quant.backtesting import summarize_multi_symbol_results

summary = summarize_multi_symbol_results(
    results_by_symbol,
    periods_per_year=252,
    annual_risk_free_rate=0.02,
)
```

## Portfolio Construction Direction

Milestone 13 will start by planning portfolio construction before implementing allocation behavior.

The intended chain is:

```text
aligned portfolio inputs -> equal-weight portfolio returns -> configurable weights -> portfolio summary artifact
```

Portfolio construction is different from the current independent multi-symbol summary because it must define date alignment, capital allocation, return aggregation, and weight assumptions.

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

The config loader validates local experiment settings. The current configured workflow supports the existing moving-average crossover strategy only.

## Strategy Interface

Strategies use a small structural contract:

```python
from el_psy_quant.strategies import Strategy, resolve_strategy, supported_strategy_names
```

The current supported strategy name is:

```text
moving_average_crossover
```

Configured experiments resolve that name through `resolve_strategy(...)` and execute the returned strategy through `Strategy.run(...)` for each symbol.

## Run a Local Configured Experiment

```bash
el-psy-quant run experiment.yaml --output-root outputs --run-id 20260630T141500Z
```

The command validates configured symbol and price inputs, resolves the configured strategy, runs the current moving-average crossover workflow from local CSV or cache data, and writes only:

```text
config.yaml
metadata.json
manifest.json
results/summary.csv
results/metrics.json
logs/
```

`manifest.json` records the experiment identity, data source, parameters, evaluation assumptions, and run-relative artifact paths.

`results/metrics.json` contains the metrics already present in `summary.csv` in a machine-readable form and records that source artifact with a relative path.

It does not download live data or add dashboards, reports, databases, portfolio construction, or interactive prompts.

## Compare Saved Experiment Runs

```python
from el_psy_quant.comparison import compare_experiment_runs

comparison = compare_experiment_runs(
    ["outputs/experiment/run-1", "outputs/experiment/run-2"]
)
```

The helper reads each run's manifest and metrics artifact, preserving run and symbol order without calculating new metrics or ranking performance.

## Module Overview

```text
el_psy_quant/
  cli.py         # Thin argparse entrypoint for local configured experiments
  comparison.py  # Compare existing metrics from saved local experiment runs
  config.py      # Load and validate local YAML experiment settings; no execution or CLI
  outputs.py     # Create deterministic local experiment directories and reserved paths
  strategies/    # Strategy contract, adapters, validation, and exact-name resolution
  data/          # Price validation, symbol universes, providers, and local input helpers
  indicators/    # Pure indicator calculations
  signals/       # Signal event generation
  portfolio/     # Return alignment/aggregation, positions, equity, costs, and trades
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
- Let automated quality gates verify basic claims before deeper human review.
- Keep experiment artifacts inspectable and portable before adding platform complexity.
- Define strategy interfaces before strategy proliferation.
- Define portfolio assumptions before portfolio construction.

## Next Step

**Sprint 61 — Configurable Portfolio Weights Foundation**

Sprint 61 should validate and apply user-supplied static portfolio weights
without adding optimization, rebalancing, or portfolio artifacts.

## Disclaimer

This project is for education, research, and software engineering practice. Nothing in this repository is financial advice.
