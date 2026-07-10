# El-Psy-Quant

An AI-native quantitative research and trading platform built in public.

## Mission

Build a production-ready quantitative research platform from zero to production, using AI as an engineering teammate while keeping human judgment in control.

The project is intentionally built sprint by sprint. The goal is not to find a magic profitable strategy on day one. The goal is to build a reliable platform that can repeatedly test, evaluate, review, and improve trading ideas.

## Current Milestone Status

**Milestone 20 — Research-to-Paper Promotion Foundation** is complete.

```text
promotion source reference contract
  -> paper promotion candidate contract
  -> promotion evidence summary
  -> explicit promotion record
  -> promotion manifest and candidate references
```

**Milestone 21 — Paper Run Comparison and Review Foundation** is complete.

```text
paper run reference contract
  -> paper run comparison input contract
  -> paper run comparison summary
  -> paper run review decision record
  -> review manifest and comparison references
```

**Milestone 22 — Decision Governance Foundation** is complete.

```text
decision evidence reference contract
  -> strategy decision input contract
  -> strategy decision summary
  -> explicit strategy decision record
  -> decision manifest and references
```

**Milestone 23 — Report Artifact Foundation** is complete.

```text
report source reference contract
  -> report section contract
  -> report artifact summary
  -> report artifact reference and manifest contracts
  -> report artifact closeout
```

Milestone 23 added deterministic review-package contracts above completed governance records. The report-artifact layer remains explicit caller-supplied/local structure only. It does not generate reports, render dashboards, discover evidence, load artifacts, calculate metrics, score or rank strategies, recommend decisions, execute workflows, integrate brokers, persist report manifests, or claim live readiness.

**Milestone 24 — Strategy Review Workflow Foundation** is in progress.

```text
strategy review evidence reference contract
  -> strategy lifecycle state snapshot contract
  -> lifecycle transition proposal contract
  -> human-controlled lifecycle transition record
  -> strategy review workflow manifest and references
  -> strategy review workflow closeout
```

Milestone 24 is contract-only. Its approved lifecycle vocabulary is limited to `research_review`, `paper_review`, `watchlist`, `on_hold`, and `rejected`. There is no implicit initial state, no automatic mapping from decision statuses, no automatic transition application, and no `live_candidate` or live-readiness state.

Sprint 131 added explicit typed pointers to completed M20–M23 governance artifacts. These evidence references do not discover, load, parse, validate, score, rank, or evaluate artifacts; declare lifecycle states; propose, approve, reject, or execute transitions; or imply paper eligibility, broker readiness, live readiness, or capital deployment.

The next focus is:

```text
Sprint 132 — Strategy Lifecycle State Snapshot Foundation
```

See:

```text
docs/roadmap.md
docs/milestones/milestone-023-report-artifact-foundation.md
docs/milestones/milestone-024-strategy-review-workflow-foundation.md
docs/sprints/sprint-130-milestone-24-planning.md
docs/strategy/future-platform-roadmap.md
```

## Current Capabilities

- Local market-data loading, caching, and validation.
- Symbol-universe normalization and duplicate protection.
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
  - optional local YAML `paper_run` config contract
  - side-effect-free conversion to `PaperRunRequest`
  - configured paper output paths
  - local configured paper workflow runner
  - configured-run metadata and manifest references to paper outputs
- Research-to-paper promotion foundation:
  - typed promotion source references
  - explicit paper promotion candidates
  - descriptive promotion evidence summaries
  - explicit human-controlled promotion records
  - local promotion manifests and candidate references
- Paper run comparison and review foundation:
  - typed paper run references
  - explicit comparison inputs
  - caller-supplied comparison summaries
  - human-controlled review decision records
  - local review manifests and comparison/review references
- Decision governance foundation:
  - typed decision evidence references
  - explicit strategy decision inputs
  - caller-supplied strategy decision summaries
  - human-controlled strategy decision records
  - local strategy decision manifests and summary/record references
- Report artifact foundation:
  - typed report source references for completed governance records and manifests
  - caller-supplied report sections with explicit source references
  - caller-supplied report artifact summaries that group explicit sections
  - compact report artifact references to stable report summary IDs
  - local report artifact manifests containing explicit summary references
- Basic and annualized performance metrics.
- Buy-and-hold benchmark comparison.
- GitHub Actions CI and local quality gate in `scripts/check.py`.

## Planned Next Platform Layer

Milestone 24 is **Strategy Review Workflow Foundation**.

Sprint 131 added the first contract in this layer: explicit evidence references to completed M20–M23 governance artifacts. The next sprint should define caller-supplied lifecycle state snapshots without adding mutable state, persistence, or a state-machine service.

- typed references to completed M20–M23 governance records
- immutable caller-supplied lifecycle state snapshots
- a fixed state vocabulary: `research_review`, `paper_review`, `watchlist`, `on_hold`, and `rejected`
- a documented permitted-transition matrix
- caller-supplied transition proposals that do not change state
- explicit human-controlled transition records
- local manifests and references for lifecycle governance artifacts

The milestone remains contract-only. It must not add runtime state mutation, mutable state storage, a state-machine service, a generic workflow engine, automatic decision-to-state mapping, evidence discovery or loading, configured workflow changes, broker/live behavior, capital deployment, databases, hosted orchestration, or readiness claims.

`live_candidate` and similar states are explicitly excluded. Live-readiness semantics belong to a later dedicated milestone after risk and operational controls exist.

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

## Recent Milestone Closeouts

### Milestone 20 — Research-to-Paper Promotion Foundation

A promotion candidate is not an approval. A promotion record is not a live-readiness claim. Paper workflow execution remains separate from promotion governance.

### Milestone 21 — Paper Run Comparison and Review Foundation

A paper-run reference is not artifact loading. A comparison summary is not a scoring engine. A review decision record is not a capital-deployment decision or live-readiness claim.

### Milestone 22 — Decision Governance Foundation

A decision evidence reference is not artifact loading. A decision summary is not a recommendation engine. A decision record is not automatic approval, capital deployment, broker approval, or live readiness.

### Milestone 23 — Report Artifact Foundation

A report source reference is only a pointer. A report section is not a rendering pipeline. A report artifact summary is descriptive and caller-supplied. A report manifest is a local reference contract, not persistence, report generation, dashboard behavior, or workflow execution.

Sprint 129 closed Milestone 23 through documentation only and preserved all report-artifact guardrails.

### Milestone 24 — Planning Decision

A lifecycle state snapshot is an explicit declaration, not stored mutable state. A transition proposal is not an action. A transition record is a human-controlled governance artifact, not a transition executor. No lifecycle artifact implies broker readiness, live readiness, or capital deployment.

## Local Experiment Configuration

Experiments can be described by a local YAML file and run with the existing CLI.

```bash
el-psy-quant run experiment.yaml --output-root outputs --run-id 20260630T141500Z
```

The configured workflow supports the existing moving-average crossover strategy, validates optional explicit paper-run inputs, converts them into `PaperRunRequest`, reserves configured paper output paths, runs the local configured paper workflow, and records paper output references in metadata and manifest files. It does not integrate portfolio construction into that configured paper workflow.

## Module Overview

```text
el_psy_quant/
  cli.py         # Thin argparse entrypoint for local configured experiments
  comparison.py  # Compare existing metrics from saved local experiment runs
  configured_paper.py # Configured local paper workflow runner
  configured_paper_references.py # Configured paper metadata and manifest references
  config.py      # Load and validate local YAML experiment settings
  decision_governance/ # Strategy-level decision evidence and governance contracts
  report_artifacts/ # Report source, section, summary, reference, and manifest contracts
  promotion/     # Research-to-paper promotion references and governance contracts
  paper_review/  # Paper run comparison and review reference contracts
  outputs.py     # Create deterministic local experiment directories and reserved paths
  strategies/    # Strategy contract, adapters, validation, and exact-name resolution
  data/          # Price validation, symbol universes, providers, and local input helpers
  execution/     # Execution assumptions, order intents, fills, summaries, and artifacts
  paper/         # Local paper state, records, persistence, audit, and run boundaries
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
