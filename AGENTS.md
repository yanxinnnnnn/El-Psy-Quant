# AGENTS.md

This file defines the shared context for AI agents working on El-Psy-Quant.

## Project Identity

El-Psy-Quant is an AI-native quantitative research and trading platform.

The project is built like a startup product, not a one-off learning script.

## Mission

Build a production-ready platform that can ingest market data, research strategies, run backtests, generate reviewable artifacts, operate paper-trading workflows, and eventually support tightly controlled live trading.

## Operating Model

- The human founder makes final decisions.
- ChatGPT acts as CTO for milestone planning, sprint scope, architecture boundaries, and PR review.
- Codex acts as the implementation developer for coding sprints.
- Documentation-only planning and closeout sprints may be handled directly by the CTO.
- AI-generated code must be reviewable, tested, and simple.
- Do not optimize for cleverness. Optimize for correctness and maintainability.

## Engineering Principles

- Use Python for the backend and domain platform.
- Prefer modern Python packaging and tooling.
- Prefer `uv` for dependency management unless the founder decides otherwise.
- Use a `src/` layout.
- Use `pytest` for testing.
- Use `ruff` for formatting and linting.
- Use type hints for public functions.
- Keep modules small and composable.
- Avoid premature abstraction.
- Avoid hidden network calls in tests.
- Keep financial calculations explicit and well documented.
- Keep broker-specific behavior behind adapters rather than leaking it into strategy, evaluation, governance, persistence, or UI domain models.

## Quant Principles

- Never claim a strategy is profitable without evidence.
- Avoid look-ahead bias.
- Avoid survivorship bias where possible.
- Always distinguish research code, backtesting code, paper execution code, and live execution code.
- Prefer reproducible experiments.
- Risk metrics matter as much as return metrics.
- Human approval records are governance evidence, not proof that runtime execution occurred.

## Definition of Done

A task is done only when:

- The code runs locally when runtime behavior changes.
- Tests are included where appropriate.
- README or docs are updated when behavior changes.
- Assumptions and limitations are documented.
- The implementation is simple enough for a human reviewer to understand.
- The complete quality gate passes.
- The PR is marked Ready for review, not left as Draft.

## Long-Term Platform Direction

Build an AI-native quant research operating system that turns trading ideas into reproducible, auditable, risk-aware decisions before any real capital is deployed.

The long-term phase roadmap is maintained in:

```text
docs/strategy/future-platform-roadmap.md
```

## Completed Foundations

Milestones 18–26 are complete:

```text
M18 — Paper Trading Workflow Integration Foundation
M19 — Configured Paper Workflow Wiring Foundation
M20 — Research-to-Paper Promotion Foundation
M21 — Paper Run Comparison and Review Foundation
M22 — Decision Governance Foundation
M23 — Report Artifact Foundation
M24 — Strategy Review Workflow Foundation
M25 — Paper Trading Productization Planning
M26 — Paper Trading Application Service Foundation
```

Milestone 24 delivered explicit, immutable, human-controlled strategy lifecycle governance without runtime lifecycle execution.

Milestone 25 defined how productization wraps completed domain capabilities without replacing or weakening their boundaries.

Milestone 26 then established a thin local FastAPI application and versioned API boundary over selected existing capabilities. It delivered deterministic strategy reads, bounded artifact inspection, synchronous in-memory paper execution, and stateless lifecycle proposal/review commands while preserving domain and artifact authority.

## Current Focus

The current milestone is:

```text
Milestone 27 — Persistence and Paper Job Control Foundation
```

Milestone 26 is complete. Its final production endpoint surface includes:

```text
GET  /api/v1/health
GET  /api/v1/strategies
GET  /api/v1/strategies/{strategy_name}
GET  /api/v1/research-runs
GET  /api/v1/research-runs/{experiment_slug}/{run_id}
GET  /api/v1/evidence-manifests
GET  /api/v1/evidence-manifests/{manifest_type}/{artifact_key}
POST /api/v1/paper-runs
POST /api/v1/lifecycle-transition-proposals
POST /api/v1/lifecycle-transition-records
```

Milestone 26 added no product database, repository layer, durable job, worker, scheduler, queue, idempotency registry, Web UI, broker, QMT, live, or capital behavior.

Sprint 145 added the explicit `EL_PSY_QUANT_PRODUCT_DATABASE_PATH` contract,
lazy SQLite SQLAlchemy engine construction, caller-owned session factories, and
an intentionally empty Alembic baseline. It added no artifact index, product
repository, business table, durable job, worker, or API database dependency.

Sprint 146 added one compact `artifact_index_entries` table, an immutable index
entry contract, a caller-transaction-owned repository, and explicit atomic
refresh plus database-only read services for the supported research and
evidence manifest layouts. Existing list readers remain discovery-authoritative
and artifact files remain payload-authoritative. It added no automatic refresh,
API change, paper-job record or status, worker, lifecycle mutation, or Sprint
147 behavior.

Sprint 147 added a shared validation-only `PaperRunCommand` to
`PaperRunRequest` boundary, strict canonical request codec, immutable durable
paper-job record, constrained `paper_jobs` table, caller-owned repository, and
explicit submit/get/list services. Submission creates only one queued row;
duplicate run IDs conflict. The existing synchronous API remains unchanged and
database-free. It added no runner, status transition, retry, recovery,
idempotency design, error/result persistence, API route, or Sprint 148 behavior.

Sprint 148 added a shared request-driven paper workflow, the four explicit
operational transitions, conditional caller-owned repository updates, one
explicit selected-job runner, and queued-only manual cancellation. The runner
claims and commits before executing outside database transactions, then records
success or expected failure in a separate transaction. Durable output writes
use atomic exclusive creation after preflight so concurrent jobs cannot clobber
authoritative files. Existing artifact files remain completed-output authority.
It added no migration, recovery, retry,
idempotency, persisted error detail, result reference, API route, or worker.

The next sprint is:

```text
Sprint 149 — Job Recovery, Idempotency, and Error Audit Foundation
```

Sprint 149 may add only the recovery, idempotency, and error-audit behavior
defined by its authoritative issue. It must not weaken the Sprint 148
single-job, file-authority, transaction, or lifecycle-separation boundaries.

Approved productization sequence:

```text
M25 — S137      Paper Trading Productization Planning
M26 — S138-S144 Paper Trading Application Service Foundation — Complete
M27 — S145-S151 Persistence and Paper Job Control Foundation — In Progress
M28 — S152-S159 Founder Paper Trading Web Workspace
M29 — S160-S165 Product Feedback and Hardening
M30 —           Portfolio-Level Decision Review Foundation
```

M28 must deliver the first usable local Web MVP.

M29 must use real founder feedback and reliability evidence to harden the MVP for daily local use.

Portfolio-level review is deferred to M30, not canceled.

## Founder Product Target

The first usable product is:

- local-first
- Founder-only
- single-user or minimally authenticated
- Paper Trading only
- review-oriented rather than latency-oriented
- a modular monolith

It must support:

- strategy list and detail
- research and backtest inspection
- governance evidence and report-artifact inspection
- paper-run launch and status
- equity, positions, orders, and fills
- paper-run comparison
- lifecycle transition proposals
- human review records
- lifecycle timeline

It is not a live trading system, broker project, SaaS product, multi-tenant platform, or professional real-time trading terminal.

## Approved Product Architecture

```text
Browser
  -> React/Next.js founder workspace
  -> FastAPI application API
  -> thin application services / use cases
  -> existing El-Psy-Quant domain modules and artifact readers
  -> SQLite product repositories and simple local job runner
```

Recommended implementation direction:

- FastAPI
- explicit request and response schemas
- SQLite with SQLAlchemy
- repository boundaries
- simple local background jobs
- React/Next.js
- Docker Compose and local-first deployment
- single-user or minimal authentication

Do not introduce premature microservices, Kubernetes, Kafka, Redis clusters, distributed queues, multi-tenancy, complex RBAC, cloud SaaS behavior, broad real-time dashboards, or broker integration.

## Product Ownership Boundaries

### Domain Authority

Existing research, backtesting, paper, promotion, comparison, decision, report, and strategy-review modules remain authoritative for quantitative and governance behavior.

The application and UI layers must not duplicate:

- financial calculations
- paper execution semantics
- comparison logic
- governance validation
- lifecycle transition validation
- human-control rules

FastAPI route handlers must remain thin and must not become a second domain layer.

### Artifact Authority

Existing local artifact files remain authoritative for completed research, paper, comparison, governance, and report outputs.

SQLite may store product indexes, explicit artifact references, paper job records, operational status, idempotency data, and minimal local authentication data.

SQLite must not silently copy complete artifact payloads and become a competing source of truth.

Artifact access must remain under configured local roots. Reject path traversal and arbitrary filesystem access.

### Lifecycle Authority

Do not create an independently authoritative mutable strategy lifecycle `current_state` field.

A product current-state view may be derived from explicit immutable snapshots and approved human transition records.

A transition proposal remains non-executing. A human review record remains governance evidence. Neither may silently mutate lifecycle state.

### Paper Job Authority

Paper job status is mutable operational state and must remain separate from strategy lifecycle governance.

M27 may define durable local states equivalent to:

```text
queued
running
succeeded
failed
canceled
```

Exact transitions, retries, recovery, idempotency, and cancellation semantics belong in the relevant implementation issues.

### Browser Boundary

The browser must use the Web/API boundary.

The UI must not directly access:

- SQLite
- local artifact directories
- Python domain modules
- QMT
- MiniQMT
- any broker

## API, Security, and Deployment Baselines

- Use a versioned local API, initially under `/api/v1`.
- Use explicit API schemas instead of leaking internal Python objects.
- Provide stable error responses and request or job IDs where applicable.
- M26 completed without product database or background-worker requirements.
- Move long-running paper execution behind durable local job control in M27.
- Bind to loopback by default.
- Require authentication for non-loopback exposure.
- Avoid broad CORS and keep same-origin defaults.
- Never log credentials or authentication material.
- Support one local machine through M29.
- Use Docker Compose only when it materially simplifies the M28 Web MVP.

## Future QMT Boundary

QMT is a future execution adapter only.

Preferred boundary:

```text
Browser
  -> Web/API
  -> broker-neutral execution command
  -> Windows QMT agent
  -> MiniQMT
  -> broker
```

Future broker-neutral execution concepts may include:

```text
OrderIntent
ExecutionOrder
ExecutionFill
AccountSnapshot
PositionSnapshot
BrokerOrderReference
```

Potential venues may include `internal_paper`, optional future `qmt_paper`, and future `qmt_live`.

Never connect the browser directly to QMT. Do not add live QMT behavior before dedicated execution-risk and live-readiness governance exists.

## Implementation Sprint Issue Requirements

Future Codex implementation sprint issues must include the Windows proxy prelude:

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7892"
$env:HTTPS_PROXY="http://127.0.0.1:7892"
$env:ALL_PROXY="http://127.0.0.1:7892"

git config http.proxy http://127.0.0.1:7892
git config https.proxy http://127.0.0.1:7892
```

They must also state:

- Do not use `--global`.
- Do not commit proxy config.
- Do not modify project files for proxy setup.
- Recommend a Codex model and reasoning effort for the specific sprint.
- Use GPT-5.6 Terra with Medium reasoning for normal implementation sprints unless complexity justifies another choice.
- Use GPT-5.6 Sol with High or stronger reasoning for architecture-heavy, ambiguous, high-risk, or difficult cross-module work.
- Use GPT-5.6 Luna with Light or Medium reasoning for mechanical or documentation-only corrections.
- Treat the GitHub issue body as the authoritative specification; keep the separate Codex execution prompt short.
- Run `uv run python scripts/check.py` before opening the PR.
- The PR body must start with a clean manually typed `Closes #<issue-number>` line.
- After opening the PR, mark it Ready for review. Do not leave it as Draft.
- Do not merge the PR unless the founder explicitly requests it.
