# El-Psy-Quant

An AI-native quantitative research and trading platform built in public.

## Mission

Build a production-ready quantitative research platform from zero to production, using AI as an engineering teammate while keeping human judgment in control.

This project is intentionally built sprint by sprint. The goal is not to find a magic profitable strategy on day one. The goal is to build a reliable platform that can repeatedly test, evaluate, and improve trading ideas.

## Current Milestone

**Milestone 20 — Research-to-Paper Promotion Foundation** is complete.

Milestone 20 completed the promotion governance chain:

```text
promotion source reference contract -> paper promotion candidate contract -> promotion evidence summary -> explicit promotion record -> promotion manifest and candidate references
```

**Milestone 21 — Paper Run Comparison and Review Foundation** is in progress.

Milestone 21 will define the first comparison and review layer after promotion governance:

```text
paper run reference contract -> paper run comparison input contract -> paper run comparison summary -> paper run review decision record -> review manifest and comparison references
```

The broader platform direction is to build an AI-native quant research operating system that turns trading ideas into reproducible, auditable, risk-aware decisions before any real capital is deployed.

The next focus is:

```text
Sprint 116 — Milestone 21 Documentation Refresh / Closeout
```

Sprint 116 should close Milestone 21 with documentation refresh only, preserving the paper run comparison and review guardrails.

See the milestone summaries in:

```text
docs/milestones/
```

The latest milestone docs are:

```text
docs/milestones/milestone-019-configured-paper-workflow-wiring-foundation.md
docs/milestones/milestone-020-research-to-paper-promotion-foundation.md
docs/milestones/milestone-021-paper-run-comparison-review-foundation.md
```

The long-term platform roadmap is:

```text
docs/strategy/future-platform-roadmap.md
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
- Backtest execution realism foundation:
  - explicit execution assumptions
  - order-intent boundaries
  - deterministic assumed fills
  - execution-adjusted trade summaries
  - in-memory execution realism artifacts for local backtests
- Paper trading foundation:
  - deterministic local paper account state
  - optional equity snapshots from explicitly supplied prices only
  - deterministic local paper order records and ledgers
  - explicit paper fill application to local account state
  - deterministic local paper trading session summaries
  - standalone in-memory paper trading artifacts
- Paper trading persistence and audit foundation:
  - explicit local paper artifact file contract
  - local paper artifact writer for explicit destination paths
  - local paper artifact reader with top-level file-contract validation
  - compact paper session audit summaries from validated artifact payloads
- Paper trading workflow integration foundation:
  - immutable local paper run request contract
  - local in-memory paper run execution boundary
  - explicit local paper run artifact persistence
  - immutable local paper run result summaries
- Configured paper workflow wiring foundation:
  - optional local YAML `paper_run` config contract for explicit paper-run inputs
  - side-effect-free conversion from validated paper-run config to `PaperRunRequest`
  - side-effect-free configured paper output paths for paper artifacts and result summaries
  - local configured paper workflow runner that writes only configured paper artifact and result-summary JSON files
  - configured-run metadata and manifest references to paper artifact and result-summary files
- Research-to-paper promotion foundation:
  - typed promotion source references for existing local or logical evidence
  - explicit paper promotion candidates for manual review
  - descriptive promotion evidence summaries with source facts, assumptions, warnings, and missing-evidence fields
  - explicit human-controlled promotion records with validated statuses and rationale
  - local promotion manifests and compact candidate references for manual inspection
- Paper run comparison and review foundation:
  - typed paper run references for existing paper artifacts or paper result summaries
  - explicit paper run comparison inputs with purpose and review context
  - deterministic caller-supplied comparison summaries with facts, assumptions, warnings, and missing-evidence fields
  - human-controlled review decision records with explicit status and rationale
  - local review manifests and compact comparison/review references for manual inspection
- Basic and annualized performance metrics.
- Buy-and-hold benchmark comparison.
- GitHub Actions CI and local quality gate in `scripts/check.py`.

## Planned Next Platform Layer

Milestone 21 plans a conservative paper run comparison and review foundation.

It should add comparison governance, not trading automation:

- paper run references for existing paper artifacts or paper result summaries
- explicit paper run comparison inputs
- descriptive comparison summaries with source facts, assumptions, warnings, and missing-evidence fields
- human-controlled paper run review decision records
- local review manifests and comparison references

It must not add automatic paper run discovery, artifact loading/parsing/scoring beyond explicit contracts, dashboards, broad report generation, database behavior, broker behavior, live execution, automatic capital deployment decisions, live-readiness claims, or real-money readiness claims.

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

## Backtest Execution Realism Foundation

Milestone 15 made execution assumptions explicit and reviewable.

The completed chain is:

```text
execution assumptions -> order intent boundary -> deterministic fill model -> execution-adjusted trade summary -> execution realism artifact
```

This milestone remains local and deterministic. It does not introduce external execution connectivity, paper trading, or operational runtime behavior.

## Paper Trading Foundation

Milestone 16 made local paper-trading state explicit and reviewable.

The completed chain is:

```text
paper account state -> paper order ledger -> paper fill application -> paper trading session summary -> paper trading artifact
```

The paper-trading foundation is local, deterministic, and inspectable. It does not currently support external execution connectivity, configured-run integration, artifact persistence, or report generation.

## Paper Trading Persistence & Audit Foundation

Milestone 17 made paper-trading artifacts durable and audit-friendly.

The completed chain is:

```text
paper artifact file contract -> local paper artifact writer -> local paper artifact reader and validation -> paper session audit summary
```

This milestone remains local and deterministic. It does not add configured-run expansion, databases, dashboards, broad report generation, deep object reconstruction, or schema migration behavior.

## Paper Trading Workflow Integration Foundation

Milestone 18 made the paper-trading state, artifact, persistence, and audit boundaries into an explicit local paper run workflow foundation.

The completed chain is:

```text
paper run request contract -> paper run execution boundary -> paper run artifact persistence -> paper run result summary
```

This milestone remains local, deterministic, and explicit-input driven. It does not add broader configured workflow or operational integrations.

## Configured Paper Workflow Wiring Foundation

Milestone 19 connected the completed paper run workflow to local configuration and configured-run output discipline.

The completed chain is:

```text
paper workflow config contract -> configured paper request builder -> configured paper output layout -> configured paper workflow runner -> configured paper manifest and result references
```

Milestone 19 added an optional local YAML `paper_run` section that validates explicit account states, orders, and fills while keeping research-only configs backward compatible. It can convert that validated config into `PaperRunRequest`, reserve configured paper output paths, run the local paper workflow while writing only the configured paper artifact and result-summary JSON files, and record references to those files in configured-run metadata and manifest outputs.

This milestone remains local and deterministic. It does not add broker integration, live execution, order routing, market data streaming, automatic research-to-paper promotion, dashboards, databases, or broad reporting.

## Research-to-Paper Promotion Foundation

Milestone 20 defined explicit promotion governance before paper comparison, decision records, reports, broker readiness, or live-readiness claims.

The completed chain is:

```text
promotion source reference contract -> paper promotion candidate contract -> promotion evidence summary -> explicit promotion record -> promotion manifest and candidate references
```

A promotion candidate is not an approval. A promotion record is not a live-readiness claim. The milestone keeps paper workflow execution separate from research-to-paper promotion records.

Sprint 104 added typed promotion source references only. Source references identify existing evidence without loading artifacts, scoring strategies, creating candidates, or executing paper workflows.

Sprint 105 added explicit paper promotion candidates. Candidates group one or more source references with a title and optional manual-review context, but they do not approve strategies, construct paper run requests, create paper orders or fills, or execute paper workflows.

Sprint 106 added descriptive promotion evidence summaries. Evidence summaries attach explicit source facts, assumptions, warnings, and missing-evidence notes to a candidate without loading artifacts, extracting metrics, scoring evidence, or creating pass/fail approval logic.

Sprint 107 added explicit promotion records. Promotion records tie evidence summaries to human-controlled status, rationale, reviewer context, and timestamps without inferring approval, claiming live readiness, or claiming real-money readiness.

Sprint 108 added local promotion manifests and compact candidate references. These contracts group existing promotion records and references for manual inspection without filesystem I/O, artifact loading, scoring, reporting, approval automation, or paper workflow execution.

Sprint 109 closed Milestone 20 with a documentation refresh and preserved the research-to-paper promotion guardrails.

## Paper Run Comparison and Review Foundation

Milestone 21 is defining the first comparison and review layer on top of completed paper workflow and promotion-governance foundations.

The planned chain is:

```text
paper run reference contract -> paper run comparison input contract -> paper run comparison summary -> paper run review decision record -> review manifest and comparison references
```

A paper run reference is not artifact loading. A comparison summary is not a scoring engine. A review decision record is not a capital deployment decision or live-readiness claim.

Sprint 111 added typed paper run references only. Paper run references identify existing paper artifacts or paper result summaries without loading artifacts, discovering runs automatically, comparing metrics, generating reports, executing paper workflows, or claiming live or real-money readiness.

Sprint 112 added explicit paper run comparison inputs. Comparison inputs group paper run references with purpose and review context without discovering runs automatically, loading artifacts, comparing metrics, scoring runs, generating summaries, or executing paper workflows.

Sprint 113 added deterministic caller-supplied comparison summaries. These summaries record comparison facts, assumptions, warnings, missing-evidence notes, reviewer context, and timestamps without discovering runs automatically, loading artifacts, calculating or comparing metrics, scoring, ranking, choosing winners, making review decisions, generating reports, or executing workflows.

Sprint 114 added human-controlled paper run review decision records. These records tie a supported explicit status and reviewer rationale to a comparison summary without automatic approval, automatic promotion, capital allocation, order routing, paper order or fill construction, broker behavior, workflow execution, dashboards, reports, or readiness claims.

Sprint 115 added local review manifests and compact comparison/review references. These contracts group existing comparison summaries and review decisions for manual inspection without file writing, file reading, filesystem scanning, persistence, database behavior, reports, dashboards, workflow execution, broker behavior, approval automation, capital allocation, order routing, or readiness claims.

Sprint 110 planned the M21 scope, sprint sequence, and guardrails.

## Local Experiment Configuration

Experiments can be described by a small local YAML file and run with the existing CLI.

```bash
el-psy-quant run experiment.yaml --output-root outputs --run-id 20260630T141500Z
```

The configured workflow currently supports the existing moving-average crossover strategy, validates optional explicit paper-run inputs, converts them into `PaperRunRequest`, reserves configured paper output paths, can run the local configured paper workflow, and can record paper output references in metadata and manifest files. It does not integrate portfolio construction.

The next step is to close Milestone 21 with documentation refresh, not to automate paper run discovery, strategy approval, paper execution, or live readiness.

## Module Overview

```text
el_psy_quant/
  cli.py         # Thin argparse entrypoint for local configured experiments
  comparison.py  # Compare existing metrics from saved local experiment runs
  configured_paper.py # Configured local paper workflow runner
  configured_paper_references.py # Configured paper metadata and manifest references
  config.py      # Load and validate local YAML experiment settings, including optional explicit paper-run inputs
  promotion/     # Research-to-paper promotion references and governance contracts
  paper_review/  # Paper run comparison and review reference contracts
  outputs.py     # Create deterministic local experiment directories and reserved paths
  strategies/    # Strategy contract, adapters, validation, and exact-name resolution
  data/          # Price validation, symbol universes, providers, and local input helpers
  execution/     # Execution assumptions, order intents, assumed fills, summaries, and artifacts
  paper/         # Local paper account state, order ledger, fill application, session summary, artifact, persistence/audit, run request, run execution, run persistence, and run result boundaries
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
docs/strategy/future-platform-roadmap.md
AGENTS.md
```

## Engineering Principles

- Build in small, reviewable milestones.
- Keep everything local and deterministic until the architecture is ready for more operational complexity.
- Treat documentation as part of the product, not an afterthought.
- Prefer simple, explicit Python over clever abstractions.
- Do not claim trading performance without evidence.
