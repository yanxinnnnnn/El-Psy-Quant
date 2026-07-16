# El-Psy-Quant

An AI-native quantitative research and trading platform built in public.

## Mission

Build a production-ready quantitative research platform from zero to production, using AI as an engineering teammate while keeping human judgment in control.

The project is intentionally built sprint by sprint. The goal is not to find a magic profitable strategy on day one. The goal is to build a reliable platform that can repeatedly research, test, evaluate, review, operate, and improve trading ideas.

## Current Milestone Status

Milestones 1–28 are complete.

**Milestone 29 — Product Feedback and Hardening** is in progress. The next sprint is:

```text
Sprint 161 — Founder Feedback and Product Experience Architecture
```

Milestone 28 closed after the Founder locally verified the isolated Demo Workspace and the complete product journey:

```text
Strategy
  -> Research Evidence
  -> Governance Evidence
  -> Paper Run
  -> Portfolio Result
  -> Comparison
  -> Lifecycle Review
  -> Human Decision Evidence
```

The formal closeout record is:

```text
docs/closeouts/milestone-028-founder-paper-trading-web-workspace-closeout.md
```

## Current Direction

The platform has enough quantitative and governance depth for the current phase. Milestone 29 now uses real Founder feedback to improve the product before portfolio-level and execution-risk work resumes.

The main product feedback is:

1. The Web workspace is stable and professional, but its visual language still resembles an academic research portal or enterprise internal dashboard.
2. The product needs a complete multilingual foundation, with English as the default language and Simplified Chinese (`zh-CN`) as the first additional language.
3. Workflow guidance should evolve from passive navigation toward a Founder Dashboard and explicit next-action support.
4. Daily local use still requires reliability, recovery, error-surface, audit, migration, test, and deployment hardening.

The approved sequence is:

```text
M25 — Paper Trading Productization Planning                 S137      Complete
M26 — Paper Trading Application Service Foundation          S138-S144 Complete
M27 — Persistence and Paper Job Control Foundation          S145-S151 Complete
M28 — Founder Paper Trading Web Workspace                   S152-S160 Complete
M29 — Product Feedback and Hardening                        S161-S168 In Progress
M30 — Portfolio-Level Decision Review Foundation                       Deferred, not canceled
```

Milestone 29 sprint plan:

```text
S161 Founder Feedback and Product Experience Architecture
S162 Multilingual Foundation and Simplified Chinese Workspace
S163 Modern Visual System Foundation
S164 Founder Dashboard and Workflow Information Architecture Refresh
S165 Reliability, Idempotency, and Job Recovery Hardening
S166 Error Surface, Observability, and Audit Hardening
S167 Migration, Test, and Local Deployment Hardening
S168 Milestone 29 Closeout and M30 Handoff
```

Internationalization precedes the broad visual refresh so both English and Chinese layouts shape the design system rather than being bolted on afterward.

## Founder Product Target

The first product is:

- local-first;
- Founder-only;
- single-user or minimally authenticated;
- Paper Trading only;
- review-oriented rather than latency-oriented; and
- a modular monolith.

It supports:

- strategy list and detail inspection;
- research and backtest evidence inspection;
- governance and report-manifest inspection;
- durable paper-job submission and manual control;
- paper-job status, attempts, retry, recovery, and cancellation;
- authoritative portfolio-result inspection;
- explicit paper-result comparison;
- lifecycle transition proposals;
- explicit human review records;
- an in-session lifecycle timeline; and
- a deterministic isolated Demo Workspace for first-run evaluation.

It is not:

- a live trading system;
- a broker integration project;
- a SaaS product;
- a multi-tenant platform;
- a professional real-time trading terminal;
- an automatic strategy approval engine; or
- an automatic capital-allocation system.

## Approved Product Architecture

```text
Browser
  -> React/Next.js Founder workspace
  -> fixed same-origin /api/backend gateway
  -> versioned FastAPI application API
  -> thin application services / use cases
  -> existing El-Psy-Quant domain modules and artifact readers
  -> SQLite product repositories and simple local job runner
```

Recommended implementation direction:

```text
FastAPI
explicit request and response schemas
SQLite + SQLAlchemy
repository boundaries
simple local jobs
React/Next.js
Docker Compose / local-first
single-user or minimal authentication
```

## Authority Boundaries

### Domain authority

Existing research, backtesting, paper, promotion, comparison, decision, report, and lifecycle modules remain authoritative for quantitative and governance behavior.

The application and Web layers must not duplicate:

- financial calculations;
- paper execution semantics;
- result validation;
- comparison meaning;
- governance validation;
- lifecycle transition validation; or
- human-control rules.

### Artifact authority

Existing local artifact files remain authoritative for completed research, paper, comparison, governance, and report outputs.

SQLite stores compact product metadata such as:

- artifact indexes and references;
- paper-job requests and operational status;
- attempts and bounded error codes;
- idempotency data; and
- result references.

SQLite must not silently copy complete artifact payloads and become a competing source of truth.

### Lifecycle authority

Do not create an independently authoritative mutable strategy lifecycle `current_state` field.

A transition proposal is non-executing. A human review record is governance evidence. Neither silently mutates lifecycle state or proves runtime execution.

### Paper-job authority

Paper-job status is mutable operational state and remains separate from strategy lifecycle governance.

The durable states are:

```text
queued
running
succeeded
failed
canceled
```

### Browser boundary

The browser must use the Web/API boundary. It must never directly access:

- SQLite;
- local artifact directories;
- Python domain modules;
- Demo source files;
- QMT;
- MiniQMT; or
- a broker.

### Demo isolation

Standard startup remains unseeded. Demo data uses a separate Compose project and volume, is deterministic and disposable, and is always visibly identified as example evidence rather than real user data.

## Current Capabilities

### Research and evaluation

- Local market-data loading, caching, and validation.
- Symbol-universe normalization and duplicate protection.
- Configured local research workflows through YAML and a thin CLI.
- Stable run artifacts including manifests, metadata, summaries, and metrics.
- Saved-run comparison from existing local artifacts.
- Strategy interface, moving-average adapter, and exact-name resolver.
- Returns, costs, slippage, equity, trades, benchmarks, and risk-adjusted metrics.
- Independent multi-symbol workflows and portfolio summaries.
- Portfolio risk, drawdown, contribution, and attribution foundations.
- Explicit execution assumptions, order intents, assumed fills, and execution-adjusted summaries.

### Paper trading and persistence

- Deterministic paper account, position, order, fill, and session records.
- Explicit paper artifact writers, readers, validation, and audit summaries.
- Configured paper-run requests and output layouts.
- SQLite and Alembic product persistence.
- Compact rebuildable artifact index.
- Durable paper-job requests and operational state.
- Replay-safe keyed submission.
- Attempt audit with approved bounded error codes.
- Manual run, cancellation, retry, and interrupted-job recovery.
- Compact result references and strict authoritative result reads.

### Governance and decision evidence

- Research-to-paper promotion candidates, summaries, records, and manifests.
- Paper-run comparison and human review governance.
- Strategy decision evidence, summaries, records, and manifests.
- Report sources, sections, summaries, references, and manifests.
- Immutable lifecycle snapshots, non-executing proposals, human review records, and workflow manifests.

### Application and API

- Deterministic FastAPI application construction.
- Versioned `/api/v1` routes.
- Server-owned request IDs and stable sanitized errors.
- Strategy catalog reads.
- Bounded research and evidence-manifest inspection.
- Synchronous paper-run and lifecycle command boundaries.
- Durable paper-job API for submission, status, attempts, control, and result reads.
- Read-only Demo Workspace descriptor API when Demo mode is explicitly enabled.

### Founder Web workspace

- Strict TypeScript Next.js App Router application under `web/`.
- Responsive and accessible workspace shell.
- Same-origin API gateway and generated TypeScript contracts.
- Strategy, research, governance, paper-job, portfolio-result, comparison, and lifecycle views.
- Explicit loading, empty, invalid, unavailable, not-found, and retry states.
- Minimal paired Founder HTTP Basic authentication.
- Reproducible standard Docker Compose startup.
- Isolated Demo Workspace startup and reset.
- Guided first-run workflow.
- Product-facing user guide and local operations runbook.

## Quick Start

### Prerequisites

- Docker Desktop with Docker Compose v2
- free loopback ports `3000` and `8000`

Copy the local configuration template:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and replace the Founder password placeholder with a unique local-only password. Do not reuse a system, email, cloud, or broker password.

### Standard workspace

Build and start the clean persistent workspace:

```powershell
docker compose up --build --detach
docker compose ps
```

Open:

```text
http://127.0.0.1:3000
```

Enter the Founder username and password from `.env` in the browser HTTP Basic prompt.

Run authenticated smoke verification:

```powershell
docker compose exec web node /app/verify-mvp.mjs
```

Stop while preserving the standard `mvp-data` volume:

```powershell
docker compose down
```

Do not run `docker compose down --volumes` unless the standard local database and authoritative artifacts may be permanently deleted.

### Isolated Demo Workspace

The standard and Demo instances publish the same loopback ports and cannot run simultaneously.

Stop the standard workspace, then start Demo mode:

```powershell
docker compose down
docker compose -f compose.yaml -f compose.demo.yaml up --build --detach
docker compose -f compose.yaml -f compose.demo.yaml ps
```

The Demo uses the distinct `el-psy-quant-demo_demo-data` volume. It validates and installs the versioned `examples/demo_workspace/` source before FastAPI serves requests.

Run the guided smoke path:

```powershell
docker compose -f compose.yaml -f compose.demo.yaml exec web node /app/verify-mvp.mjs
```

Stop while preserving Demo storage:

```powershell
docker compose -f compose.yaml -f compose.demo.yaml down
```

Reset only disposable Demo storage:

```powershell
docker compose -f compose.yaml -f compose.demo.yaml down --volumes
docker compose -f compose.yaml -f compose.demo.yaml up --build --detach
```

Return to the standard workspace with:

```powershell
docker compose -f compose.yaml -f compose.demo.yaml down
docker compose up --detach
```

### Direct developer startup

Install dependencies:

```bash
uv sync
npm --prefix web ci
```

Configure the same Founder credential pair in both terminals.

Backend:

```powershell
$env:EL_PSY_QUANT_FOUNDER_USERNAME="founder"
$env:EL_PSY_QUANT_FOUNDER_PASSWORD="replace-with-a-local-password"
uv run uvicorn el_psy_quant.api.app:app --host 127.0.0.1 --port 8000
```

Web:

```powershell
$env:EL_PSY_QUANT_API_ORIGIN="http://127.0.0.1:8000"
$env:EL_PSY_QUANT_FOUNDER_USERNAME="founder"
$env:EL_PSY_QUANT_FOUNDER_PASSWORD="replace-with-a-local-password"
npm --prefix web run dev
```

Leaving both credential variables unset preserves loopback-only unauthenticated developer mode. Partial credential configuration fails closed.

## Web Routes

```text
/
/strategies
/strategies/[strategyName]
/research-runs
/research-runs/[experimentSlug]/[runId]
/evidence-manifests
/evidence-manifests/[manifestType]/[artifactKey]
/paper-jobs
/paper-jobs/new
/paper-jobs/[jobId]
/portfolio-records
/portfolio-records/[jobId]
/comparisons
/lifecycle-review
```

The browser calls only `/api/backend/api/v1/...`. It never receives a database connection or filesystem path.

## API Surface

Core reads and commands include:

```text
GET  /api/v1/health
GET  /api/v1/strategies
GET  /api/v1/strategies/{strategy_name}
GET  /api/v1/research-runs
GET  /api/v1/research-runs/{experiment_slug}/{run_id}
GET  /api/v1/evidence-manifests
GET  /api/v1/evidence-manifests/{manifest_type}/{artifact_key}
GET  /api/v1/paper-jobs
POST /api/v1/paper-jobs
GET  /api/v1/paper-jobs/{job_id}
GET  /api/v1/paper-jobs/{job_id}/attempts
POST /api/v1/paper-jobs/{job_id}/run
POST /api/v1/paper-jobs/{job_id}/cancel
POST /api/v1/paper-jobs/{job_id}/retry
POST /api/v1/paper-jobs/{job_id}/recover
GET  /api/v1/paper-jobs/{job_id}/result
POST /api/v1/paper-runs
POST /api/v1/lifecycle-transition-proposals
POST /api/v1/lifecycle-transition-records
GET  /api/v1/demo-workspace
```

`GET /api/v1/demo-workspace` is hidden with a bounded not-configured response unless Demo mode is explicitly enabled.

## Development and Quality

Run the complete quality gate:

```bash
uv run python scripts/check.py
```

The gate covers:

- Python tests;
- Ruff and package-import checks;
- CLI checks;
- OpenAPI snapshot freshness;
- generated TypeScript contract freshness;
- ESLint;
- strict TypeScript;
- frontend tests; and
- the production Next.js build.

Regenerate or verify contracts directly:

```bash
npm --prefix web run contracts:generate
npm --prefix web run contracts:check
```

## Documentation

- [Founder Workspace User Guide](docs/user-guide/README.md)
- [Founder MVP Local Operations](docs/founder-mvp-local-operations.md)
- [Project Roadmap](docs/roadmap.md)
- [Future Platform Roadmap](docs/strategy/future-platform-roadmap.md)
- [Milestone 28 Summary](docs/milestones/milestone-028-founder-paper-trading-web-workspace.md)
- [Milestone 28 Closeout](docs/closeouts/milestone-028-founder-paper-trading-web-workspace-closeout.md)

## Future Execution Boundary

QMT is a future execution adapter only.

```text
Browser
  -> Web/API
  -> broker-neutral execution command
  -> Windows QMT agent
  -> MiniQMT
  -> broker
```

QMT-specific behavior must not leak into strategy, evaluation, governance, persistence, or UI domain models. Never connect the browser directly to QMT. Do not add live behavior before dedicated portfolio review, execution-risk controls, operational readiness, and explicit human approval exist.

## Explicit Non-priorities

Do not prioritize these before the roadmap explicitly activates them:

- real-money trading;
- live broker integration;
- browser-to-broker connectivity;
- high-frequency trading;
- autonomous strategy approval;
- autonomous capital allocation;
- microservices;
- Kubernetes;
- Kafka;
- Redis clusters;
- distributed queues;
- multi-tenancy;
- complex RBAC;
- broad cloud infrastructure; or
- SaaS behavior.
