# El-Psy-Quant

An AI-native quantitative research and trading platform built in public.

## Mission

Build a production-ready quantitative research platform from zero to production, using AI as an engineering teammate while keeping human judgment in control.

The project is intentionally built sprint by sprint. The goal is not to find a magic profitable strategy on day one. The goal is to build a reliable platform that can repeatedly research, test, evaluate, review, operate, and improve trading ideas.

## Current Milestone Status

Milestones 1–25 are complete.

The latest completed milestone is **Milestone 25 — Paper Trading Productization Planning**.

Milestone 25 defined the staged founder product architecture:

```text
Browser
  -> React/Next.js founder workspace
  -> FastAPI application API
  -> thin application services / use cases
  -> existing El-Psy-Quant domain modules and artifact readers
  -> SQLite product repositories and simple local job runner
```

Key ownership decisions:

- existing domain modules remain authoritative for quantitative and governance rules
- API handlers and UI code must not duplicate domain logic
- existing local artifact files remain authoritative
- SQLite stores product indexes, references, jobs, operational status, and other product metadata rather than silently duplicating full artifact payloads
- lifecycle current state is a derived read model from immutable snapshots and approved human records, not an independently authoritative mutable field
- paper job status is separate mutable operational state
- the browser uses the API and never directly accesses SQLite, artifact directories, Python modules, QMT, MiniQMT, or a broker

## Current Direction

The current milestone is:

```text
Milestone 26 — Paper Trading Application Service Foundation
```

Sprints 138 through 143 are complete. The next sprint is:

```text
Sprint 144 — Milestone 26 Closeout
```

The approved productization sequence is:

```text
M25 — Paper Trading Productization Planning                 S137      Complete
M26 — Paper Trading Application Service Foundation          S138-S144 In progress
M27 — Persistence and Paper Job Control Foundation          S145-S151 Planned
M28 — Founder Paper Trading Web Workspace                   S152-S159 Planned
M29 — Product Feedback and Hardening                        S160-S165 Planned
M30 — Portfolio-Level Decision Review Foundation                       Deferred, not canceled
```

M28 must deliver the first usable local Web MVP.

M29 must use real founder workflows to harden usability, reliability, recovery, audit visibility, migrations, tests, and local deployment. After M29, the target is a local Paper Trading Web MVP reliable enough for daily Founder use.

## Founder Product Target

The first product is local-first, Founder-only, single-user or minimally authenticated, and Paper Trading only.

Approved founder journeys:

- strategy list and strategy detail
- research and backtest inspection
- governance evidence and report-artifact inspection
- starting a paper run
- paper-run status
- equity, positions, orders, and fills
- paper-run comparison
- lifecycle transition proposals
- human review records
- lifecycle timeline

Recommended implementation direction:

```text
FastAPI
explicit request/response schemas
SQLite + SQLAlchemy
simple local background jobs
React/Next.js
Docker Compose / local-first
single-user or minimal authentication
```

Explicitly deferred through the founder productization phase unless a separate roadmap decision changes the scope:

- microservices
- Kubernetes
- Kafka
- Redis clusters
- distributed queues
- multi-tenancy
- complex RBAC
- cloud SaaS hosting
- broad real-time trading dashboards
- broker integration
- automatic lifecycle transitions
- automatic strategy approval or capital allocation
- real-money trading

## Future QMT Boundary

QMT is a future execution adapter only.

```text
Browser
  -> Web/API
  -> broker-neutral execution command
  -> Windows QMT agent
  -> MiniQMT
  -> broker
```

Future broker-neutral execution concepts remain:

```text
OrderIntent
ExecutionOrder
ExecutionFill
AccountSnapshot
PositionSnapshot
BrokerOrderReference
```

QMT-specific behavior must not leak into strategy, evaluation, governance, persistence, or UI domain models. The browser must never connect directly to QMT, and no live QMT behavior should be added before dedicated execution-risk and live-readiness governance exists.

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
  - portfolio risk metrics
  - worst drawdown inspection
  - per-symbol contribution returns and summaries
  - standalone attribution artifacts
- Backtest execution realism foundation:
  - explicit execution assumptions
  - order-intent boundaries
  - deterministic assumed fills
  - execution-adjusted trade summaries
  - in-memory execution realism artifacts
- Paper trading foundation:
  - deterministic local paper account state
  - explicit paper order records and ledgers
  - paper fill application
  - equity snapshots from caller-supplied prices
  - deterministic session summaries
- Paper persistence and audit foundation:
  - explicit paper artifact file contracts
  - local writers and readers
  - top-level file validation
  - compact audit summaries
- Paper workflow integration foundation:
  - immutable paper run requests
  - local in-memory execution boundary
  - explicit artifact persistence
  - immutable result summaries
- Configured paper workflow wiring:
  - optional local YAML `paper_run` configuration
  - conversion to `PaperRunRequest`
  - configured paper output paths
  - local configured paper runner
  - metadata and manifest references to paper outputs
- Research-to-paper promotion governance:
  - typed promotion evidence references
  - explicit promotion candidates
  - evidence summaries
  - human-controlled promotion records
  - promotion manifests and candidate references
- Paper run comparison and review governance:
  - typed run references
  - explicit comparison inputs and summaries
  - human review decision records
  - review manifests and references
- Decision governance:
  - typed decision evidence references
  - explicit decision inputs and summaries
  - human-controlled decision records
  - decision manifests and references
- Report artifact foundation:
  - report source references
  - caller-supplied sections and summaries
  - compact report references
  - local report manifests
- Strategy lifecycle governance:
  - typed M20–M23 evidence references
  - immutable state snapshots
  - deterministic transition proposals
  - human-controlled transition records
  - compact workflow references and manifests
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

Run the local application API on loopback only:

```bash
uv run uvicorn el_psy_quant.api.app:app --host 127.0.0.1 --port 8000
```

`create_app()` provides independent FastAPI instances, and all Sprint 138 routes use the `/api/v1` boundary. `GET /api/v1/health` returns process health only. It is not a database, worker, broker, QMT, external-service, live-trading, or readiness check. Every response receives a server-owned UUID in `X-Request-ID`; handled errors use the stable `error` plus `request_id` envelope without exposing internal exception details.

The built-in strategy catalog is available through:

```text
GET /api/v1/strategies
GET /api/v1/strategies/{strategy_name}
```

Catalog identity and order follow `supported_strategy_names()` exactly. It currently describes only `moving_average_crossover`. Parameter metadata is descriptive; existing configuration and domain validation remain authoritative. These endpoints do not discover experiments, inspect artifacts, execute strategies, expose performance or lifecycle state, rank strategies, run paper workflows, persist data, or imply broker/QMT/live readiness.

Configured research-run inspection uses one server-side local root:

```powershell
$env:EL_PSY_QUANT_RESEARCH_ARTIFACT_ROOT="C:\path\to\experiment-outputs"
uv run uvicorn el_psy_quant.api.app:app --host 127.0.0.1 --port 8000
```

The read-only endpoints are:

```text
GET /api/v1/research-runs
GET /api/v1/research-runs/{experiment_slug}/{run_id}
```

The list reads fixed `manifest.json` files only. Detail reads the selected fixed manifest and its safely contained `artifacts.metrics` JSON reference. All identifiers and artifact references remain under the configured root; HTTP requests cannot select a root or arbitrary path. The service does not read config, metadata, summary CSV, logs, or raw results, and it does not recompute, compare, aggregate, or rank metrics. Governance, paper, lifecycle, persistence, jobs, UI, broker, QMT, live, and real-money behavior remain excluded.

Configured evidence-manifest inspection uses an independent server-side root:

```powershell
$env:EL_PSY_QUANT_EVIDENCE_ARTIFACT_ROOT="C:\path\to\evidence-artifacts"
uv run uvicorn el_psy_quant.api.app:app --host 127.0.0.1 --port 8000
```

The fixed layout is:

```text
<evidence-root>/
  strategy-decisions/<artifact-key>.json
  report-artifacts/<artifact-key>.json
  strategy-review/<artifact-key>.json
```

The read-only endpoints are:

```text
GET /api/v1/evidence-manifests
GET /api/v1/evidence-manifests/{manifest_type}/{artifact_key}
```

Only saved top-level `StrategyDecisionManifest`, `ReportArtifactManifest`, and `StrategyReviewWorkflowManifest` payloads are inspected. Existing domain reference and manifest factories remain authoritative for validation. Safe artifact keys select configured files and remain separate from domain manifest IDs. Compact references are returned as pointers only; they are not loaded or resolved. The service adds no chain-completeness or current-state inference, approval, execution, persistence, jobs, UI, broker, QMT, live, or capital behavior.

The synchronous paper-run command is available through:

```text
POST /api/v1/paper-runs
```

The request supplies explicit starting and ending account states, orders, and fills. Existing paper domain factories and `run_paper_trading_request(...)` remain authoritative; the command does not generate orders, apply fills to derive state, or reconcile the caller's ending state. The normalized artifact is returned in memory without accepting a file path or writing an artifact or result summary. Repeated caller-supplied `run_id` values are independent because no durable job, status, idempotency, retry, cancellation, recovery, repository, or database exists in Sprint 142. The endpoint adds no configured-paper execution, broker, QMT, market-data stream, live execution, lifecycle transition, automatic approval, or capital allocation.

The synchronous lifecycle governance commands are available through:

```text
POST /api/v1/lifecycle-transition-proposals
POST /api/v1/lifecycle-transition-records
```

Both endpoints are stateless and in memory. The proposal command reconstructs the caller-supplied source snapshot and unresolved evidence pointers through existing strategy-review factories. The review command carries and reconstructs the complete proposal because no proposal repository or lookup exists. An approved record requires a separate caller-supplied resulting snapshot matching the proposal strategy and target state; rejected and deferred records prohibit one.

Approval is governance evidence only. Neither command applies a transition, mutates a snapshot, makes a snapshot globally current, resolves evidence, triggers paper or strategy execution, or persists an artifact, proposal, record, timeline, or status. Repeated caller-supplied IDs remain independent because no registry, database, durable job, broker, QMT, live, or capital behavior exists in Sprint 143.

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

## Local Experiment Configuration

Experiments can be described by a local YAML file and run with the existing CLI.

```bash
el-psy-quant run experiment.yaml --output-root outputs --run-id 20260630T141500Z
```

The configured workflow validates explicit research and optional paper-run inputs, executes the existing local workflows, persists deterministic outputs, and records references in metadata and manifest files. It does not integrate with a broker or imply live readiness.

## Recent Milestone Closeouts

### Milestone 20 — Research-to-Paper Promotion Foundation

A promotion candidate is not approval. A promotion record is not a live-readiness claim. Paper execution remains separate from promotion governance.

### Milestone 21 — Paper Run Comparison and Review Foundation

A paper-run reference is not artifact loading. A comparison summary is not a scoring engine. A review decision is not a capital-deployment decision.

### Milestone 22 — Decision Governance Foundation

A decision evidence reference is not artifact loading. A decision summary is not a recommendation engine. A decision record is not automatic approval.

### Milestone 23 — Report Artifact Foundation

A report source reference is only a pointer. A report artifact is not a rendering pipeline, dashboard, report engine, or workflow executor.

### Milestone 24 — Strategy Review Workflow Foundation

A lifecycle state snapshot is an explicit declaration, not stored mutable state. A transition proposal is not an action. A transition record is human governance evidence, not a runtime executor. A workflow manifest is a local index, not a resolved chain.

### Milestone 25 — Paper Trading Productization Planning

Productization wraps existing domain capabilities rather than rewriting them. Product persistence must not become a competing source of artifact truth, and operational paper-job state must remain separate from human-controlled strategy lifecycle governance.

## Module Overview

```text
el_psy_quant/
  cli.py         # Thin argparse entrypoint for local configured experiments
  api/           # Local FastAPI factory, versioned routes, request IDs, and errors
  comparison.py  # Compare existing metrics from saved local experiment runs
  configured_paper.py # Configured local paper workflow runner
  configured_paper_references.py # Configured paper metadata and manifest references
  config.py      # Load and validate local YAML experiment settings
  decision_governance/ # Strategy-level decision evidence and governance contracts
  report_artifacts/ # Report source, section, summary, reference, and manifest contracts
  promotion/     # Research-to-paper promotion references and governance contracts
  paper_review/  # Paper run comparison and review contracts
  strategy_review/ # Lifecycle evidence, snapshots, proposals, records, references, and manifests
  outputs.py     # Deterministic local experiment directories and reserved paths
  strategies/    # Strategy contracts, adapters, validation, and resolution
  data/          # Price validation, symbol universes, providers, and local input helpers
  execution/     # Execution assumptions, order intents, fills, summaries, and artifacts
  paper/         # Local paper state, records, persistence, audit, and run boundaries
  indicators/    # Pure indicator calculations
  signals/       # Signal event generation
  portfolio/     # Alignment, weights, aggregation, risk, and attribution
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
- Keep behavior local and deterministic until operational complexity is justified.
- Treat documentation as part of the product.
- Prefer simple, explicit Python over clever abstractions.
- Preserve human control over promotion, decisions, lifecycle changes, and future capital deployment.
- Do not claim trading performance without evidence.
