# El-Psy-Quant

An AI-native quantitative research and trading platform built in public.

## Mission

Build a production-ready quantitative research platform from zero to production, using AI as an engineering teammate while keeping human judgment in control.

This project is intentionally built sprint by sprint. The goal is not to find a magic profitable strategy on day one. The goal is to build a reliable platform that can repeatedly test, evaluate, and improve trading ideas.

## Current Milestone

**Milestone 15 — Backtest Execution Realism Foundation** is planned.

Milestone 14 completed the first portfolio risk and attribution layer:

```text
portfolio_return -> risk metrics
portfolio_equity -> drawdown inspection
aligned_returns + static_weights -> symbol contribution
risk + drawdown + contribution -> attribution summary artifact
```

Milestone 15 should now make backtest execution assumptions explicit before the project moves toward paper trading.

The planned Milestone 15 chain is:

```text
execution assumptions -> order intent boundary -> deterministic fill model -> execution-adjusted trade summary -> execution realism artifact
```

See the milestone summaries in:

```text
docs/milestones/
```

The latest milestone docs are:

```text
docs/milestones/milestone-014-portfolio-risk-and-attribution-foundation.md
docs/milestones/milestone-015-backtest-execution-realism-foundation.md
```

## Current Capabilities

- Local market data loading, caching, and validation.
- Symbol universe normalization and duplicate protection.
- Configured local research workflows through YAML and a thin CLI.
- Stable local run artifacts including manifest, metadata, summary, and metrics files.
- Saved-run comparison from existing local artifacts.
- Strategy interface, moving-average strategy adapter, and exact-name resolver.
- Moving-average crossover research pipeline with returns, costs, slippage, equity, and trade records.
- Independent multi-symbol research execution and cross-symbol summaries.
- Portfolio construction foundation:
  - aligned per-symbol strategy return streams
  - equal-weight portfolio returns
  - validated static portfolio weights
  - weighted portfolio returns
  - standalone portfolio summary artifacts
- Portfolio risk and attribution foundation:
  - portfolio return risk metrics
  - single worst portfolio drawdown inspection
  - static-weight per-symbol contribution returns and summaries
  - standalone portfolio attribution summary artifacts
- Execution assumptions, order-intent boundaries, and deterministic assumed fills for local backtests.
- Basic and annualized performance metrics.
- Buy-and-hold benchmark comparison.
- GitHub Actions CI and local quality gate in `scripts/check.py`.

## Quick Start

Install [uv](https://docs.astral.sh/uv/), then install the project and development dependencies:

```bash
uv sync
```

Run the complete quality gate used by GitHub Actions:

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
```

## Portfolio Construction

Portfolio construction starts after per-symbol strategy returns already exist.

```python
from el_psy_quant.portfolio import (
    align_strategy_returns,
    equal_weight_portfolio_return,
    weighted_portfolio_return,
    build_portfolio_summary_artifact,
)

aligned_returns = align_strategy_returns(results_by_symbol)
equal_weight_return = equal_weight_portfolio_return(aligned_returns)
weighted_return = weighted_portfolio_return(
    aligned_returns,
    {"AAPL": 0.6, "MSFT": 0.4},
)
artifact = build_portfolio_summary_artifact(
    weighted_return,
    construction_method="static_weight",
    symbols=aligned_returns.columns,
    weights={"AAPL": 0.6, "MSFT": 0.4},
    periods_per_year=252,
)
```

Portfolio construction is different from independent multi-symbol summaries because it must define date alignment, aggregation, weights, and recorded assumptions.

## Portfolio Risk And Attribution

Milestone 14 added the first standalone portfolio risk and attribution layer on top of the portfolio construction foundation.

The completed chain is:

```text
portfolio_return -> risk metrics
portfolio_equity -> drawdown inspection
aligned_returns + static_weights -> symbol contribution
risk + drawdown + contribution -> attribution summary artifact
```

This layer explains portfolio behavior before adding execution realism.

## Backtest Execution Realism Direction

Milestone 15 should make execution assumptions explicit and reviewable.

The planned chain is:

```text
execution assumptions -> order intent boundary -> deterministic fill model -> execution-adjusted trade summary -> execution realism artifact
```

This milestone should remain local and deterministic. It should not introduce broker integration, exchange APIs, paper trading, or live trading behavior.

## Local Experiment Configuration

Experiments can be described by a small local YAML file and run with the existing CLI.

```bash
el-psy-quant run experiment.yaml --output-root outputs --run-id 20260630T141500Z
```

The configured workflow currently supports the existing moving-average crossover strategy and does not yet integrate portfolio construction.

## Module Overview

```text
el_psy_quant/
  cli.py         # Thin argparse entrypoint for local configured experiments
  comparison.py  # Compare existing metrics from saved local experiment runs
  config.py      # Load and validate local YAML experiment settings
  outputs.py     # Create deterministic local experiment directories and reserved paths
  strategies/    # Strategy contract, adapters, validation, and exact-name resolution
  data/          # Price validation, symbol universes, providers, and local input helpers
  execution/     # Execution assumptions, order intents, and assumed fills
  indicators/    # Pure indicator calculations
  signals/       # Signal event generation
  portfolio/     # Alignment, weights, return aggregation, and standalone summaries
  backtesting/   # Research pipelines, experiments, benchmarks, and multi-symbol helpers
  performance/   # Metrics, annualized evaluation, and backtest summaries
```

## Documentation

```text
docs/roadmap.md
docs/sprints/
docs/milestones/
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
- Keep local research reproducible.
- Treat parameter search as comparison, not alpha discovery.
- Keep experiment artifacts inspectable and portable before adding platform complexity.
- Define portfolio assumptions before portfolio construction.
- Explain portfolio risk before execution realism.
- Make execution assumptions explicit before paper trading.

## Next Step

**Sprint 74 — Execution-Adjusted Trade Summary Foundation**

Sprint 74 should summarize execution-adjusted trades from explicit order intents and assumed fills without adding broker, paper-trading, or live-trading behavior.

## Disclaimer

This project is for education, research, and software engineering practice.
