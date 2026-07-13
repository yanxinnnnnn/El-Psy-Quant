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

Milestones 18–25 are complete:

```text
M18 — Paper Trading Workflow Integration Foundation
M19 — Configured Paper Workflow Wiring Foundation
M20 — Research-to-Paper Promotion Foundation
M21 — Paper Run Comparison and Review Foundation
M22 — Decision Governance Foundation
M23 — Report Artifact Foundation
M24 — Strategy Review Workflow Foundation
M25 — Paper Trading Productization Planning
```

Milestone 24 delivered explicit, immutable, human-controlled strategy lifecycle governance without runtime lifecycle execution.

Milestone 25 then defined how productization wraps those completed domain capabilities without replacing or weakening their boundaries.

## Current Focus

The current milestone is:

```text
Milestone 26 — Paper Trading Application Service Foundation
```

Sprint 138 added the local FastAPI application factory, `/api/v1` boundary, process-health endpoint, server-owned request IDs, and stable sanitized error envelopes. It adds no application services, persistence, background jobs, Web UI, broker, QMT, live, or real-money behavior.

Sprint 139 added a deterministic built-in strategy catalog read service and the versioned strategy list/detail endpoints. Catalog order follows `supported_strategy_names()`, and parameter metadata is descriptive only; existing configuration and domain validation remain authoritative. It adds no execution, experiment discovery, artifact inspection, ranking, lifecycle state, persistence, paper commands, UI, broker, QMT, live, or real-money behavior.

Sprint 140 added bounded read-only inspection for configured research-run manifests and saved metrics under `EL_PSY_QUANT_RESEARCH_ARTIFACT_ROOT`. List reads manifests only; detail reads one manifest plus its safely contained metrics reference. No arbitrary HTTP path, recomputation, comparison, governance, paper, lifecycle, persistence, background work, UI, broker, QMT, live, or real-money behavior was added.

Sprint 141 added bounded read-only inspection for saved strategy-decision, report-artifact, and strategy-review workflow manifests under `EL_PSY_QUANT_EVIDENCE_ARTIFACT_ROOT`. Existing domain factories remain authoritative, artifact keys are safe file selectors rather than manifest IDs, and compact references are never resolved. No chain inference, lifecycle state derivation, approval, execution, persistence, jobs, UI, broker, QMT, live, or capital behavior was added.

Sprint 142 added a synchronous in-memory paper-run application command and `POST /api/v1/paper-runs`. Callers supply explicit starting and ending states, orders, and fills; existing paper factories and `run_paper_trading_request(...)` remain authoritative. The command does not generate orders, apply fills to derive state, accept paths, persist artifacts, create durable jobs or status, execute configured-paper workflows, or add broker, QMT, live, or capital behavior.

The next sprint is:

```text
Sprint 143 — Lifecycle Proposal and Human Review Application Commands
```

Approved productization sequence:

```text
M25 — S137      Paper Trading Productization Planning
M26 — S138-S144 Paper Trading Application Service Foundation
M27 — S145-S151 Persistence and Paper Job Control Foundation
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
- Keep M26 free of product database and background-worker requirements.
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
