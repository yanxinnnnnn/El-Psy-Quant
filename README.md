# El-Psy-Quant

An AI-native quantitative research and trading platform built in public.

## Mission

Build a production-ready quantitative research platform from zero to production,
using AI as an engineering teammate while keeping human judgment in control.

The goal is not to claim a magic profitable strategy. The goal is to build a
reproducible, auditable, risk-aware platform that can research, test, review,
operate, and improve trading ideas before real capital is deployed.

## Current Status

Milestones 1–30 are **Complete** after Sprint 178 merges.

The next milestone is:

```text
M31 — Stateful Paper Account and Ledger Foundation
```

M31 is **In Progress** through the Founder-approved S179–S188 sequence. Sprints
179–185 are Complete after PR #367 merged. Sprint 186 is
implementation-complete and pending Founder review. It exposes durable Paper
Account list, create, detail, ledger, mutation, snapshot, and reconciliation
workflows through the bilingual generated-contract-only Founder Web.

Current migration head:

```text
0007_paper_account_ledger
```

## Product Delivered Through M30

The current product provides:

- a local Founder-only Next.js workspace;
- a versioned FastAPI API through a fixed same-origin gateway;
- paired minimal Founder authentication;
- complete English and Simplified Chinese product support;
- a modern responsive AI Quant Decision Workspace visual system;
- a bounded Founder Dashboard for workflow navigation and operational attention;
- authoritative strategy, research, governance, report, Paper Job, result,
  comparison, portfolio-review, and lifecycle-review inspection;
- explicit Paper Job submit, replay, Run, Cancel, Retry, Recover, attempt, and
  result workflows;
- stable localized error meaning with raw codes, request IDs, and technical audit
  details;
- sanitized local request and command correlation events;
- SQLite/Alembic persistence through one exact migration chain;
- fail-closed Standard and Demo startup with read-only verification;
- locked Python build/runtime inputs and `npm ci` for the Web image;
- isolated persistent Standard and disposable Demo storage;
- non-mutating bilingual runtime smoke verification; and
- cold-backup, upgrade, Demo-only reset, and return-to-Standard guidance.

M30 adds a complete portfolio-level decision-review workflow:

```text
explicit immutable review source
  -> explicit baseline and proposed scenarios
  -> concentration and review exposure
  -> symbol overlap and historical return interaction
  -> baseline/proposed historical behavior and impact
  -> immutable analysis evidence
  -> explicit approve / reject / defer decision
  -> bilingual Founder inspection and audit
```

M30 includes:

- 2–12 ordered review components;
- typed evidence references and per-component research origin;
- exact ordered aligned historical returns;
- strict non-negative static weights with no automatic normalization;
- domain-calculated concentration, exposure, overlap, correlation, behavior,
  contribution, drawdown, and proposed impact;
- immutable source, analysis, and human-decision artifacts;
- compact SQLite metadata and idempotency state;
- exactly four versioned portfolio-review API routes;
- three bilingual Founder portfolio-review routes;
- explicit research-run and compatible evidence-manifest composition;
- deterministic isolated Demo Workspace v2 review and create prefill;
- exact replay and persisted human-decision evidence;
- installed-wheel Alembic resources for the runtime-only backend; and
- successful Founder Standard/Demo, persistence, isolation, and bilingual browser
  acceptance.

Formal M30 records:

```text
docs/architecture/portfolio-level-decision-review.md
docs/milestones/milestone-030-portfolio-level-decision-review-foundation.md
docs/closeouts/milestone-030-portfolio-level-decision-review-foundation-closeout.md
```

## Current Founder Journey

```text
Strategy
  -> Research Evidence
  -> Governance Evidence
  -> Paper Run
  -> Portfolio Result
  -> Comparison
  -> Portfolio Review
  -> Paper Account
  -> Lifecycle Review
  -> Human Decision Evidence
```

Portfolio-review creation keeps aligned returns, scenario weights, audit input,
and proposed-component selection under explicit Founder control. The browser does
not calculate portfolio evidence, normalize weights, select a candidate, or
record a decision automatically.

## What the Current Product Is Not Yet

The current Paper workflow is auditable and operationally controlled, but it is
not yet a continuous market-driven Paper Trading runtime.

It does not yet provide:

- account-funded interpretation of M30 scenario weights;
- market-data replay tied to a trading calendar and session clock;
- automatic strategy-signal-to-order conversion;
- pre-trade risk checks for automatically generated orders;
- a runtime order lifecycle and execution simulator;
- a durable worker/checkpoint/recovery loop;
- continuous multi-day Paper Trading;
- broker, QMT, MiniQMT, private-edge, live, or real-money behavior; or
- automatic strategy ranking, approval, optimization, or capital allocation.

M30 approval is governance evidence only. It does not create, fund, or mutate an
account and does not authorize execution.

## Approved Route to Genuine Paper Trading

```text
M30 Portfolio-Level Decision Review Foundation — Complete
  -> M31 Stateful Paper Account and Ledger Foundation — In Progress
  -> M32 Market Data Replay, Trading Calendar, and Session Clock
  -> M33 Strategy-to-Order and Pre-Trade Risk Pipeline
  -> M34 Paper Execution Simulator and First True Paper Trading
  -> M35 Durable Paper Runtime and Recovery
  -> M36 Multi-day Paper Operations and Acceptance
```

M31 has the approved S179–S188 sequence. M32–M36 retain no sprint ranges and each
receives its own architecture-and-planning Issue before implementation.

### M31 — Account and ledger truth

M31 must establish an independent durable source of truth for account identity,
cash, positions, adjustments, fees, order/fill references, snapshots,
reconciliation, idempotency, and concurrency.

Sprint 180 established the separate `el_psy_quant.paper_account` contract
boundary. Sprint 181 added pure immutable creation, cash-movement,
approved-evidence-link, and lifecycle events; exact cash postings; contiguous
version and digest chains; and fail-closed cash-only replay. Sprint 182 added
normalized-symbol position commands and postings, long-only quantity and
aggregate-cost-basis invariants, display-only average cost, and one complete
mixed-ledger state and replay boundary without changing valid Sprint 181 event
digests. Sprint 183 added a canonical complete projection, verification statuses
`current` and `reconciliation_required`, closed ordered mismatch codes, and
immutable snapshot/reconciliation evidence anchored to replayed history.
Sprint 184 adds migration `0007_paper_account_ledger`, append-only durable
history, strict row/domain reconstruction, replaceable projection caches,
immutable snapshot/reconciliation rows, creation and operation idempotency,
`BEGIN IMMEDIATE` plus guarded head compare-and-swap, and internal application
services. Sprint 185 adds exactly ten versioned Paper Account operations, strict
canonical-string financial transport, bounded list and ledger pagination,
stable sanitized Paper Account errors, server-owned request IDs, bounded
success audit events, and generated OpenAPI/TypeScript contracts. Sprint 186
adds the bilingual generated-contract-only Founder Paper Account list, create,
detail, ledger, mutation, snapshot, and reconciliation workspace. Verification
never silently repairs or replaces a candidate projection. API and browser
payloads are not financial authority. No filesystem artifacts, Demo, Docker
acceptance, order/fill, market, execution, worker, broker, live, or real-money
behavior exists yet; those integration and acceptance boundaries remain S187.
The existing `el_psy_quant.paper` evidence model is unchanged.

An approved M30 review may be linked as evidence, but it is not ledger truth and
cannot itself create or fund an account.

Canonical M31 records:

```text
docs/architecture/stateful-paper-account-and-ledger.md
docs/milestones/milestone-031-stateful-paper-account-and-ledger-foundation.md
docs/sprints/sprint-179-milestone-31-architecture-and-planning.md
docs/sprints/sprint-180-paper-account-identity-lifecycle-decimal-and-evidence-reference-contract-foundation.md
docs/sprints/sprint-181-immutable-cash-ledger-and-account-event-foundation.md
docs/sprints/sprint-182-immutable-position-ledger-and-aggregate-cost-basis-foundation.md
docs/sprints/sprint-183-account-snapshot-reconciliation-and-projection-rebuild-foundation.md
docs/sprints/sprint-184-durable-paper-account-persistence-migration-concurrency-and-application-service-foundation.md
docs/sprints/sprint-185-versioned-paper-account-api-errors-and-audit-surface-foundation.md
docs/sprints/sprint-186-bilingual-founder-paper-account-web-workspace.md
```

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

Authoritative runtime roadmap:

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
  -> domain modules and artifact readers/writers
  -> compact SQLite product state and authoritative artifact roots
```

Authority rules:

- domain modules own quantitative, Paper Trading, comparison, governance,
  lifecycle, and portfolio-review calculations;
- API handlers and the Web layer do not duplicate financial calculations;
- completed artifact files remain full payload authority;
- SQLite stores compact indexes, references, idempotency records, attempts, jobs,
  reviews, and operational state rather than complete artifact payloads;
- Paper Job, lifecycle, portfolio review, and future Paper Account state remain
  separate authorities;
- lifecycle proposals remain non-executing;
- human review remains explicit governance evidence;
- raw IDs, states, versions, timestamps, codes, digests, values, and artifact
  content remain authoritative and untranslated;
- the browser never directly accesses SQLite, artifact directories, Python, QMT,
  MiniQMT, or a broker; and
- Demo data remains isolated from Standard user data.

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

The gate verifies lock/export parity, installed-wheel migration resources, Python
tests and linting, package/CLI behavior, OpenAPI/generated TypeScript freshness,
message catalogs, ESLint, strict TypeScript, Web tests, and the production Next.js
build.

## Key Records

```text
AGENTS.md
docs/roadmap.md
docs/strategy/future-platform-roadmap.md
docs/strategy/paper-trading-runtime-roadmap.md
docs/milestones/milestone-029-product-feedback-and-hardening.md
docs/closeouts/milestone-029-product-feedback-and-hardening-closeout.md
docs/architecture/portfolio-level-decision-review.md
docs/milestones/milestone-030-portfolio-level-decision-review-foundation.md
docs/closeouts/milestone-030-portfolio-level-decision-review-foundation-closeout.md
docs/sprints/sprint-178-milestone-030-closeout-and-m31-handoff.md
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
