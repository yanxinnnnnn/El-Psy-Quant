# El-Psy-Quant

An AI-native quantitative research and trading platform built in public.

## Mission

Build a production-ready quantitative research platform from zero to production,
using AI as an engineering teammate while keeping human judgment in control.

The goal is not to claim a magic profitable strategy. The goal is to build a
reproducible, auditable, risk-aware platform that can research, test, review,
operate, and improve trading ideas before real capital is deployed.

## Current Status

Milestones 1–29 are **Complete**.

Milestone 30 is **In Progress**:

```text
M30 — Portfolio-Level Decision Review Foundation
```

The approved M30 sequence is:

```text
S169 Milestone 30 Architecture and Planning
S170 Portfolio Review Input and Scenario Contract Foundation
S171 Concentration and Exposure Analysis Foundation
S172 Strategy Interaction and Proposed Portfolio Impact Foundation
S173 Portfolio Review Artifact and Human Decision Foundation
S174 Durable Portfolio Review Persistence and Application/API Foundation
S175 Founder Portfolio Decision Review Web Workspace
S176 Portfolio Review Workflow Integration, Demo, and Acceptance Hardening
S177 Milestone 30 Closeout and M31 Handoff
```

Sprints 169–175 are complete. Sprint 176 implementation is complete; Founder
Standard/Demo runtime acceptance remains. Sprint 177 is next only after Sprint
176 is merged and that acceptance is complete.

## Product Delivered Through M29

The current product provides:

- a local Founder-only Next.js workspace;
- a versioned FastAPI API through a fixed same-origin gateway;
- paired minimal Founder authentication;
- complete English and Simplified Chinese product support;
- a modern responsive AI Quant Decision Workspace visual system;
- a bounded Founder Dashboard for operational attention and workflow navigation;
- authoritative strategy, research, governance, report, Paper Job, result,
  comparison, and lifecycle-review inspection;
- explicit Paper Job submit, replay, Run, Cancel, Retry, Recover, attempt, and
  result workflows;
- stable localized error meaning with raw codes, request IDs, and technical audit
  details;
- sanitized local request and Paper Job correlation events;
- SQLite/Alembic persistence through one exact migration chain;
- fail-closed Standard and Demo startup with read-only workspace verification;
- locked Python build/runtime inputs and `npm ci` for the Web image;
- isolated persistent Standard and disposable Demo storage;
- non-mutating bilingual runtime smoke verification; and
- cold-backup, upgrade, Demo-only reset, and return-to-Standard guidance.

The complete current user journey remains:

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

M30 is planned to extend that product with:

```text
validated portfolio review source
  -> explicit baseline and proposed scenarios
  -> concentration and review exposure
  -> strategy interaction and symbol overlap
  -> historical portfolio impact
  -> explicit human portfolio decision evidence
```

Sprint 170 supplies immutable in-memory portfolio-review source and static
scenario contracts. Sprint 171 adds pure domain-calculated concentration,
ordered component weight-change exposure, declared-symbol evidence, and active
coverage results. Sprint 172 adds source-ordered declared-symbol overlap,
pairwise and candidate-to-baseline historical correlation, baseline/proposed
historical portfolio behavior, ordered contribution, and exact
proposed-minus-baseline impact. These are immutable in-memory domain results;
Sprint 173 adds immutable historical-scenario analysis and governance-only
decision payloads, canonical SHA-256 digests, UTC audit normalization, and typed
source/analysis/decision references. Source return observations remain separate.
Sprint 174 adds hashed fixed-layout write-once source/analysis/decision files,
strict reopen and S171/S172 recalculation, one compact SQLite review record,
create/decision idempotency, one-winner settlement, four versioned API routes,
and explicit OpenAPI/generated TypeScript contracts. Migration head is
`0006_portfolio_reviews`. S174 adds no Founder Web, Demo data, lifecycle,
account, order, execution, M31, private-edge, broker, or live capability.

Sprint 175 adds three bilingual Founder routes for exact backend-ordered review
listing, manual structured source/scenario construction, complete authoritative
evidence inspection, and one explicit governance-only decision. The Web client
uses the checked-in generated contracts with complete nested runtime
validation, preserves drafts and previously loaded evidence across failures,
and never normalizes weights or recalculates financial evidence. S175 adds no
backend, generated contract, Demo, lifecycle, Paper Job, account, order,
execution, M31, private-edge, broker, or live capability.

Sprint 176 integrates the unchanged builder with explicit public research and
evidence selection. Imports are limited to exact metadata and compatible
references; aligned component returns, weights, scenarios, audit input, and the
proposed component remain Founder authority. Demo dataset/descriptor v2 adds one
isolated deterministic awaiting review and an explicit replace-confirmed prefill.
It never auto-submits or decides. Standard remains unseeded, all portfolio
analysis stays server-owned, and Founder Docker/browser acceptance remains.

## What the Current Product Is Not Yet

The current Paper workflow is auditable and operationally controlled, but it is
not yet a continuous market-driven Paper Trading runtime.

It does not yet provide:

- a persistent Paper Account cash/position ledger across sessions;
- market-data replay tied to a trading calendar and session clock;
- automatic strategy-signal-to-order conversion;
- pre-trade risk checks for automatically generated orders;
- a runtime order lifecycle and execution simulator;
- a durable worker/checkpoint/recovery loop; or
- continuous multi-day Paper Trading.

M30 also does not authorize automatic strategy ranking, portfolio optimization,
capital allocation, account mutation, order generation, or execution.

## Approved Route to Genuine Paper Trading

```text
M30 Portfolio-Level Decision Review Foundation
  -> M31 Stateful Paper Account and Ledger Foundation
  -> M32 Market Data Replay, Trading Calendar, and Session Clock
  -> M33 Strategy-to-Order and Pre-Trade Risk Pipeline
  -> M34 Paper Execution Simulator and First True Paper Trading
  -> M35 Durable Paper Runtime and Recovery
  -> M36 Multi-day Paper Operations and Acceptance
```

Two product gates define progress:

### M34 — First true Paper Trading

The Founder selects an approved strategy, account, symbols, and historical market
session. The platform itself reads market data, evaluates the strategy, derives
orders, applies risk checks, simulates fills, updates the durable account, and
records complete evidence. Orders and fills are no longer pre-supplied as the
transaction script.

### M36 — Continuous Paper Trading

The same account advances across multiple sessions and trading days with durable
checkpoints, reconciliation, explicit controls, duplicate prevention, and
interruption recovery.

See:

```text
docs/strategy/paper-trading-runtime-roadmap.md
```

## Approved Architecture

```text
Browser
  -> Next.js Founder Workspace
  -> fixed same-origin /api/backend gateway
  -> versioned FastAPI API
  -> thin application services / use cases
  -> existing domain modules and artifact readers
  -> isolated SQLite product state and authoritative artifact roots
```

Authority rules:

- domain modules own financial, Paper Trading, comparison, governance, lifecycle,
  and future portfolio-review calculations;
- API handlers and the Web layer do not duplicate financial calculations;
- completed artifact files remain payload authority;
- SQLite stores compact indexes, references, idempotency records, attempts, jobs,
  and operational state rather than complete artifact payloads;
- Paper Job state remains separate from lifecycle governance;
- future portfolio-review status remains separate from strategy lifecycle and
  future Paper Account truth;
- lifecycle proposals remain non-executing;
- human review remains explicit governance evidence;
- raw IDs, states, versions, timestamps, codes, and artifact content remain
  authoritative and untranslated;
- the browser never directly accesses SQLite, artifact directories, Python, QMT,
  MiniQMT, or a broker; and
- Demo data remains isolated from real user data.

## Quick Start

### Standard Founder Workspace

Prerequisites:

- Docker Desktop with Compose v2;
- a local checkout; and
- a local-only Founder password.

```powershell
Copy-Item .env.example .env
docker compose up --build --detach
docker compose ps
```

Open:

```text
http://127.0.0.1:3000
```

Run read-only verification and bilingual smoke:

```powershell
docker compose exec backend el-psy-quant verify-local-workspace --mode standard --workspace-root /data
docker compose exec web node /app/verify-mvp.mjs
```

### Isolated Demo Workspace

Stop Standard without deleting its volume, then start Demo:

```powershell
docker compose down
docker compose -f compose.yaml -f compose.demo.yaml up --build --detach
```

Verify:

```powershell
docker compose -f compose.yaml -f compose.demo.yaml exec backend el-psy-quant verify-local-workspace --mode demo --workspace-root /data/workspace
docker compose -f compose.yaml -f compose.demo.yaml exec web node /app/verify-mvp.mjs
```

Reset only Demo storage:

```powershell
docker compose -f compose.yaml -f compose.demo.yaml down --volumes
docker compose -f compose.yaml -f compose.demo.yaml up --build --detach
```

Never run a volume-removing command against the Standard project.

Operations guidance:

```text
docs/founder-mvp-local-operations.md
docs/operations/local-install-upgrade-and-recovery.md
docs/operations/error-observability-and-audit.md
```

## Development

Install exact reviewed dependencies:

```bash
uv sync --locked
npm --prefix web ci
```

Run the complete repository gate:

```bash
uv run python scripts/check.py
```

The gate verifies lock/export parity, Python tests and linting, package/CLI
behavior, OpenAPI/generated TypeScript freshness, message catalogs, ESLint,
strict TypeScript, Web tests, and the production Next.js build.

## Key Records

```text
docs/milestones/milestone-029-product-feedback-and-hardening.md
docs/closeouts/milestone-029-product-feedback-and-hardening-closeout.md
docs/product/milestone-029-product-feedback-and-hardening-plan.md
docs/architecture/portfolio-level-decision-review.md
docs/milestones/milestone-030-portfolio-level-decision-review-foundation.md
docs/sprints/sprint-169-milestone-30-architecture-and-planning.md
docs/sprints/sprint-173-portfolio-review-artifact-and-human-decision-foundation.md
docs/strategy/future-platform-roadmap.md
docs/strategy/paper-trading-runtime-roadmap.md
docs/roadmap.md
```

## Explicitly Deferred

Unless a future milestone explicitly approves them:

- broker, QMT, or MiniQMT integration;
- real-money execution;
- automatic strategy ranking, approval, optimization, or capital allocation;
- public SaaS, multi-tenancy, or complex RBAC;
- microservices, Kubernetes, Kafka, or Redis clusters;
- distributed job infrastructure; and
- broad real-time trading-terminal behavior.
