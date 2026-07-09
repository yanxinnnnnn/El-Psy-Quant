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

**Milestone 21 — Paper Run Comparison and Review Foundation** is complete.

Milestone 21 completed the first comparison and review layer after promotion governance:

```text
paper run reference contract -> paper run comparison input contract -> paper run comparison summary -> paper run review decision record -> review manifest and comparison references
```

**Milestone 22 — Decision Governance Foundation** is complete.

Milestone 22 completed the conservative strategy-level decision governance layer above promotion records and paper-review records:

```text
decision evidence reference contract -> strategy decision input contract -> strategy decision summary -> explicit strategy decision record -> decision manifest and references
```

**Milestone 23 — Report Artifact Foundation** is in progress.

Milestone 23 should define deterministic report artifacts above completed governance records:

```text
report source reference contract -> report section contract -> report artifact summary -> report manifest and references -> report artifact closeout
```

The broader platform direction is to build an AI-native quant research operating system that turns trading ideas into reproducible, auditable, risk-aware decisions before any real capital is deployed.

The next focus is:

```text
Sprint 127 — Report Artifact Summary Foundation
```

Sprint 127 should add a deterministic caller-supplied report artifact summary without automatic metric calculation, recommendation, ranking, dashboards, reports, workflow execution, broker behavior, or readiness claims.

See the milestone summaries in:

```text
docs/milestones/
```

The latest milestone docs are:

```text
docs/milestones/milestone-020-research-to-paper-promotion-foundation.md
docs/milestones/milestone-021-paper-run-comparison-review-foundation.md
docs/milestones/milestone-022-decision-governance-foundation.md
docs/milestones/milestone-023-report-artifact-foundation.md
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
- Decision governance foundation:
  - typed decision evidence references for existing promotion and paper-review evidence
  - explicit strategy decision inputs that group evidence references with purpose and review context
  - caller-supplied strategy decision summaries with facts, assumptions, warnings, and missing-evidence notes
  - human-controlled strategy decision records with explicit status and rationale
  - local strategy decision manifests and compact summary/record references
- Report artifact foundation:
  - typed report source references for completed governance records and manifests
  - caller-supplied report sections with explicit source references
- Basic and annualized performance metrics.
- Buy-and-hold benchmark comparison.
- GitHub Actions CI and local quality gate in `scripts/check.py`.

## Planned Next Platform Layer

Milestone 23 is in progress after the completed decision-governance layer.

The next implementation sprint should add a deterministic caller-supplied report artifact summary on top of explicit report sections.

Milestone 23 must not add automatic approval, automatic promotion, automatic decision making, automatic evidence discovery, broker integration, order routing, live execution, capital allocation, dashboards, broad report generation, report rendering pipelines, database behavior, hosted service behavior, SaaS behavior, or real-money readiness claims.

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

## Milestone Closeouts

### Paper Trading Workflow Integration Foundation

Milestone 18 closed this conservative chain:

```text
paper run request contract -> paper run execution boundary -> paper run artifact persistence -> paper run result summary
```

### Configured Paper Workflow Wiring Foundation

Milestone 19 connected the completed paper run workflow to local configuration and configured-run output discipline:

```text
paper workflow config contract -> configured paper request builder -> configured paper output layout -> configured paper workflow runner -> configured paper manifest and result references
```

Milestone 19 remains local and deterministic. It does not add broker integration, live execution, order routing, market data streaming, automatic research-to-paper promotion, dashboards, databases, or broad reporting.

### Research-to-Paper Promotion Foundation

Milestone 20 defined explicit promotion governance before paper comparison, decision records, reports, broker readiness, or live-readiness claims:

```text
promotion source reference contract -> paper promotion candidate contract -> promotion evidence summary -> explicit promotion record -> promotion manifest and candidate references
```

A promotion candidate is not an approval. A promotion record is not a live-readiness claim. The milestone keeps paper workflow execution separate from research-to-paper promotion records.

### Paper Run Comparison and Review Foundation

Milestone 21 defined the first comparison and review layer on top of completed paper workflow and promotion-governance foundations:

```text
paper run reference contract -> paper run comparison input contract -> paper run comparison summary -> paper run review decision record -> review manifest and comparison references
```

A paper run reference is not artifact loading. A comparison summary is not a scoring engine. A review decision record is not a capital deployment decision or live-readiness claim. A review manifest is a local in-memory reference contract, not file persistence, database behavior, or a workflow runner.

Sprint 116 closed Milestone 21 with a documentation refresh and preserved the paper run comparison and review guardrails.

### Decision Governance Foundation

Milestone 22 defined the strategy-level decision governance layer above promotion and paper-review evidence:

```text
decision evidence reference contract -> strategy decision input contract -> strategy decision summary -> explicit strategy decision record -> decision manifest and references
```

A decision evidence reference is not artifact loading. A strategy decision input is not automatic evidence discovery. A strategy decision summary is not a recommendation engine. A strategy decision record is not automatic approval, capital deployment, broker approval, live readiness, or real-money readiness. A decision manifest is a local reference contract, not persistence, database behavior, report generation, or workflow execution.

Sprint 117 planned Milestone 22 and preserved the decision-governance guardrails.

Sprint 118 added typed decision evidence references only.

Sprint 119 added explicit strategy decision inputs.

Sprint 120 added caller-supplied strategy decision summaries.

Sprint 121 added explicit human-controlled strategy decision records.

Sprint 122 added local strategy decision manifests and compact summary/record references.

Sprint 123 closed Milestone 22 with a documentation refresh and preserved the decision-governance guardrails.

### Planned Report Artifact Foundation

Milestone 23 should define deterministic report artifacts above completed governance records:

```text
report source reference contract -> report section contract -> report artifact summary -> report manifest and references -> report artifact closeout
```

A report source reference should be only a pointer to completed governance records. A report section should not be a rendering pipeline. A report artifact summary should be descriptive and caller-supplied, not a recommendation engine. A report manifest should be a local reference contract, not persistence, database behavior, dashboard behavior, broad report generation, or workflow execution.

Sprint 124 planned Milestone 23 and preserved the report-artifact guardrails.

Sprint 125 added typed report source references for completed governance records and manifests. Report source references are pointers only: they do not discover evidence, load artifacts, generate reports, render dashboards, score or rank records, execute workflows, add broker behavior, or claim readiness.

Sprint 126 added caller-supplied report sections with explicit source references. Report sections are structure only: they do not render reports, generate markdown/PDF output, discover evidence, load artifacts, score or rank records, execute workflows, add broker behavior, or claim readiness.

## Local Experiment Configuration

Experiments can be described by a small local YAML file and run with the existing CLI.

```bash
el-psy-quant run experiment.yaml --output-root outputs --run-id 20260630T141500Z
```

The configured workflow currently supports the existing moving-average crossover strategy, validates optional explicit paper-run inputs, converts them into `PaperRunRequest`, reserves configured paper output paths, can run the local configured paper workflow, and can record paper output references in metadata and manifest files. It does not integrate portfolio construction.

The next step is Sprint 127, not to automate evidence discovery, strategy approval, paper execution, report generation, broker behavior, or live readiness.

## Module Overview

```text
el_psy_quant/
  cli.py         # Thin argparse entrypoint for local configured experiments
  comparison.py  # Compare existing metrics from saved local experiment runs
  configured_paper.py # Configured local paper workflow runner
  configured_paper_references.py # Configured paper metadata and manifest references
  config.py      # Load and validate local YAML experiment settings, including optional explicit paper-run inputs
  decision_governance/ # Strategy-level decision evidence and governance contracts
  report_artifacts/ # Report artifact source-reference and section contracts
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
