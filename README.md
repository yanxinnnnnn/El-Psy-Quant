# El-Psy-Quant

An AI-native quantitative research and trading platform built in public.

## Mission

Build a production-ready quantitative research platform from zero to production,
using AI as an engineering teammate while keeping human judgment in control.

The goal is not to claim a magic profitable strategy. The goal is to build a
reproducible, auditable, risk-aware platform that can research, test, review,
operate, and improve trading ideas before real capital is deployed.

## Current Status

Milestones 1–32 are **Complete**. Milestone 33 is **In Progress** through the
approved S197–S206 sequence.

```text
M33 — Strategy-to-Order and Pre-Trade Risk Pipeline
```

Issue #389 is the authoritative M33 architecture source. Sprints 197–203 are
Complete. Sprint 204 is the current implementation sprint and adds one
bilingual `/strategy-to-risk` Founder workspace over the generated S203
contracts. The Web explicitly orchestrates and inspects Signal → Intent or
no-action → Risk evidence without calculating authority or mutating Paper
Account, replay, or execution state.

Current migration head:

```text
0010_strategy_order_risk
```

## Product Delivered Through M32

The current product provides:

- a local Founder-only Next.js workspace;
- a versioned FastAPI API through a fixed same-origin gateway;
- paired minimal Founder authentication;
- complete English and Simplified Chinese product support;
- a modern responsive AI Quant Decision Workspace visual system;
- a bounded Founder Dashboard for workflow navigation and operational attention;
- authoritative strategy, research, governance, report, Paper Job, result,
  comparison, portfolio-review, lifecycle-review, Paper Account, and market-time
  inspection;
- explicit Paper Job submit, replay, Run, Cancel, Retry, Recover, attempt, and
  result workflows;
- stable localized error meaning with raw codes, request IDs, and technical audit
  details;
- sanitized local request and command correlation events;
- SQLite/Alembic persistence through one exact additive migration chain;
- fail-closed Standard and Demo startup with read-only verification;
- locked Python build/runtime inputs and `npm ci` for the Web image;
- isolated persistent Standard and disposable Demo storage;
- non-mutating bilingual runtime smoke verification; and
- cold-backup, upgrade, Demo-only reset, restart, and return-to-Standard guidance.

### M30 — Portfolio-level decision review

M30 established explicit portfolio review evidence and one explicit human
decision. Its approval remains governance evidence only. It does not allocate
capital, create or fund an account, generate an order, or authorize execution.

### M31 — Stateful Paper Account and Ledger Foundation

M31 established:

- independent Paper Account identity and lifecycle state;
- immutable cash and position ledgers;
- aggregate cost basis and deterministic replay;
- projection rebuild, snapshot, and reconciliation evidence;
- durable SQLite persistence, append-only protection, idempotency, and optimistic
  concurrency;
- versioned API and bilingual Founder Web workflows; and
- isolated Demo v3 upgrade, restart, recovery, and acceptance evidence.

Final M31 authority remains:

```text
ledger events/postings = financial authority
ledger replay = account-state authority
projection/snapshot/reconciliation = derived evidence/cache
API/Web/Demo = presentation and verification only
```

### M32 — Market Data Replay, Trading Calendar, and Session Clock

M32 established:

- immutable Trading Calendar and Trading Session authority;
- the canonical versioned `MarketDataEvent` contract;
- deterministic replay ordering, lifecycle, cursor, and stream binding;
- durable market-event and replay persistence with restart-safe recovery;
- read-only market-time inspection APIs;
- a bilingual Founder Replay Workspace; and
- isolated Demo v4 market-time replay and recovery evidence.

Final M32 authority remains:

```text
TradingCalendar / TradingSession = calendar and session authority
MarketDataEvent = market-state event authority
MarketDataReplayEngine = deterministic progression authority
persistence = store and restore existing authorities only
Web / Demo = presentation and verification only
```

M32 does not create, mutate, or authorize Paper Account financial state.

### M33 — Strategy-to-Order and Pre-Trade Risk Pipeline

Sprint 198 established the immutable contracts:

- one closed v1 `moving_average_crossover` runtime reference;
- one trusted exact M32 calendar/session/replay/current-event reference;
- one pure signal-evaluation command and deterministic command digest;
- immutable Strategy Signals restricted to zero or the configured positive
  `target_position_quantity`; and
- compact trusted Signal references.

Sprint 199 adds one exact closed adapter resolver and the
`moving_average_crossover / v1 / v1` adapter. Evaluation reconstructs and
verifies concrete calendar, session, replay, cursor, stream, current-event, and
instrument anchors; then uses only same-instrument `trade` prices from the exact
consumed prefix in M32 order. At least `slow_window + 1` valid prices are
required. The existing research `Strategy` seam remains the quantitative
implementation, and its ephemeral pandas result maps only the latest validated
long-only `0|1` position to canonical zero or the configured target quantity.

Signal identity still covers the complete runtime reference, market reference,
target semantic, and exact target quantity. Actor, command idempotency, command
digest, audit timestamp, pandas inputs, and research outputs do not affect
Signal identity.

Sprint 200 adds the narrow public M31 ledger-state validator and immutable
account-state, command, Order Intent, no-action, and compact intent-reference
contracts. The account reference copies exact M31 evidence at one ledger head;
it is not a second balance, position, account, or ledger authority. Conversion
uses only target quantity versus exact current same-instrument quantity:

```text
target > current -> buy(target - current)
target < current -> sell(current - target)
target = current -> target_already_satisfied no-action
```

Intent and no-action identity bind the complete Signal, market, account,
target/current quantity, and conversion policy. Command keys, actors, command
digests, and audit timestamps remain audit evidence and do not change result
identity. Any changed Signal or account head/version/event/chain/cash/position
anchor requires a new command and result.

M33 Signal and Order Intent authority remain separate from research DataFrames,
the M15 backtest `OrderIntent`, and legacy Paper order/fill evidence. The S200
intent is risk-pending and reserves nothing.

Sprint 201 adds the immutable `long_only_cash_risk_v1` policy reference, exact
`latest_trade_price_v1` evidence from the consumed replay prefix, exact
quantity-times-price notional, four ordered rule records, a deterministic
`risk_input_<digest>` snapshot, and an immutable `risk_decision_<digest>`
allow/reject result. The stable rule order is position sufficiency, maximum
quantity, maximum notional, then available cash. Non-applicable rules remain
present with null values and pass deterministically.

Evaluation recreates the exact intent, account, calendar, session, replay,
cursor, and current-event anchors. Changed authority fails stale and produces no
decision. Missing, invalid, unsupported, or unrepresentable latest-price or
notional input also fails closed; only valid complete rule evidence can produce
an allow or reject decision. Reference price is risk evidence only, not
execution, fill, or valuation authority.

Sprint 202 stores complete canonical Signal, Order Intent, no-action, risk
snapshot, and Decision evidence in the product SQLite database. Migration
`0010_strategy_order_risk` owns append-only triggers, unique deterministic
identity/digest constraints, strict foreign references, and scoped durable
command receipts. Reads reconstruct every nested contract, recompute identities
and provenance, and fail closed on corrupt payloads or indexed metadata.

Application services reopen and verify persisted M33 references plus exact
current M31 ledger replay/projection and M32 calendar/session/replay authority
before invoking the unchanged S198–S201 pure functions. `BEGIN IMMEDIATE`,
database constraints, and all-or-nothing receipts provide one-winner behavior;
no-action remains receipt evidence and never creates an executable intent row.

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
  -> Market Time Replay Inspection
  -> Lifecycle Review
  -> Human Decision Evidence
```

The browser remains a presentation and command surface. It does not duplicate
financial calculations, infer market-time truth, silently repair state, select a
strategy, create an order, or execute a trade.

## What the Current Product Is Not Yet

The current Paper workflow is auditable, durable, and market-time aware, but it
is not yet genuine strategy-driven Paper Trading.

It does not yet provide:

- a bilingual Founder Web workflow over durable strategy-to-risk authority;
- a runtime order lifecycle and execution simulator;
- market-driven fills and resulting ledger mutations;
- a durable worker/claim/checkpoint/recovery loop for session execution;
- continuous multi-day Paper Trading;
- broker, QMT, MiniQMT, private-edge, live, or real-money behavior; or
- automatic strategy ranking, approval, optimization, or capital allocation.

## Approved Route to Genuine Paper Trading

```text
M30 Portfolio-Level Decision Review Foundation — Complete
  -> M31 Stateful Paper Account and Ledger Foundation — Complete
  -> M32 Market Data Replay, Trading Calendar, and Session Clock — Complete
  -> M33 Strategy-to-Order and Pre-Trade Risk Pipeline — In Progress
  -> M34 Paper Execution Simulator and First True Paper Trading
  -> M35 Durable Paper Runtime and Recovery
  -> M36 Multi-day Paper Operations and Acceptance
```

M33 owns strategy signals, order intent, and pre-trade risk through S197–S206.
Sprint 202 stores and orchestrates the immutable S198–S201 authority chain.
Sprint 203 exposes that authority through exactly nine thin versioned routes
without recalculating Signal, Intent, no-action, price, notional, or risk truth.
Sprint 204 consumes those generated contracts in one bilingual guided Founder
workspace while preserving exact raw IDs, digests, codes, decimals, timestamps,
stale anchors, and idempotent replay evidence.
M33 consumes M31 account authority and M32 market-time authority, but
persistence and application services must not redefine ledger, calendar, event,
cursor, or replay truth.

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

- domain modules own quantitative and workflow calculations;
- ledger events/postings own financial truth;
- ledger replay owns Paper Account state truth;
- calendar/session definitions and canonical market events own market-time truth;
- replay engine state owns deterministic market progression;
- persistence stores and restores authority but does not replace it;
- API, Web, and Demo payloads remain presentation and verification surfaces;
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
docs/architecture/portfolio-level-decision-review.md
docs/milestones/milestone-030-portfolio-level-decision-review-foundation.md
docs/closeouts/milestone-030-portfolio-level-decision-review-foundation-closeout.md
docs/architecture/stateful-paper-account-and-ledger.md
docs/milestones/milestone-031-stateful-paper-account-and-ledger-foundation.md
docs/milestones/milestone-032-market-data-replay-trading-calendar-and-session-clock.md
docs/closeouts/milestone-032-market-data-replay-trading-calendar-and-session-clock-closeout.md
docs/milestones/m32-closeout.md
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
