# El-Psy-Quant

An AI-native quantitative research and trading platform built in public.

## Mission

Build a production-ready quantitative research platform from zero to production,
using AI as an engineering teammate while keeping human judgment in control.

The goal is not to claim a magic profitable strategy. The goal is to build a
reproducible, auditable, risk-aware platform that can research, test, review,
operate, and improve trading ideas before real capital is deployed.

## Current Status

Milestones 1–33 are **Complete**. Milestone 34 is **In Progress** through the
approved S207–S216 sequence.

The current milestone and Sprint are:

```text
M34 — Paper Execution Simulator and First True Paper Trading
S207 — Complete
S208 — Complete
S209 — Complete
S210 — Complete
S211 — Complete
S212 — Versioned Paper Execution API, Errors, Audit, and Generated Contracts
```

Issue #408 is the authoritative M34 architecture source. Issue #417 is the
authoritative S212 implementation specification. M35–M36 remain future
milestones.

Current migration head:

```text
0011_paper_execution
```

The canonical M33 closeout is:

```text
docs/closeouts/milestone-033-strategy-to-order-and-pre-trade-risk-pipeline-closeout.md
```

## Product Delivered Through M33

The current product provides:

- a local Founder-only Next.js workspace;
- a versioned FastAPI API through a fixed same-origin gateway;
- paired minimal Founder authentication;
- complete English and Simplified Chinese product support;
- a modern responsive AI Quant Decision Workspace visual system;
- a bounded Founder Dashboard for workflow navigation and operational attention;
- authoritative strategy, research, governance, report, Paper Job, result,
  comparison, portfolio-review, lifecycle-review, Paper Account, market-time,
  and strategy-to-risk inspection;
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
- cold-backup, upgrade, Demo-only reset, restart, recovery, and
  return-to-Standard guidance.

### M30 — Portfolio-Level Decision Review Foundation

M30 established explicit portfolio review evidence and one explicit human
decision. Its approval remains governance evidence only. It does not allocate
capital, create or fund an account, generate an order, or authorize execution.

### M31 — Stateful Paper Account and Ledger Foundation

M31 established:

- independent Paper Account identity and lifecycle state;
- immutable cash and position ledgers;
- aggregate cost basis and deterministic replay;
- projection rebuild, snapshot, and reconciliation evidence;
- durable SQLite persistence, append-only protection, idempotency, and
  optimistic/one-winner concurrency;
- versioned API and bilingual Founder Web workflows; and
- isolated Demo upgrade, restart, recovery, and acceptance evidence.

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
- isolated Demo market-time replay and recovery evidence.

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

M33 established one deterministic strategy-to-risk chain over frozen M31/M32
authority:

```text
exact versioned strategy runtime + exact M32 replay prefix
  -> immutable StrategySignal recommendation evidence
  -> exact M31 account head
  -> immutable account-bound OrderIntent or deterministic no-action
  -> exact risk/account/market snapshot
  -> immutable allow/reject PreTradeRiskDecision
  -> future M34 execution candidate only
```

Delivered M33 capability includes:

- one closed `moving_average_crossover / v1 / v1` runtime adapter and exact
  `target_position_quantity` semantics;
- deterministic Signal evaluation from exact M32 market/session/replay/event
  anchors;
- exact target-versus-current buy/sell/no-action conversion using M31
  `PaperQuantity` authority;
- immutable account-bound M33 OrderIntent identity and command idempotency;
- explicit `long_only_cash_risk_v1` plus `latest_trade_price_v1` evidence;
- exact notional and four ordered risk rules;
- immutable allow/reject input snapshots and Decision identity;
- durable append-only Signal, Intent, Decision, and scoped command-receipt
  persistence under migration `0010_strategy_order_risk`;
- strict reconstruction, bounded keyset reads, one-winner transactions,
  restart-safe replay, stale-authority refusal, and corruption/no-repair;
- exactly nine authenticated versioned M33 API operations with stable errors,
  request IDs, bounded audit correlation, canonical OpenAPI, and generated
  TypeScript;
- one bilingual generated-contract-only `/strategy-to-risk` Founder workspace
  with no browser-side authority calculation; and
- deterministic isolated Demo v5 integration across install/reinstall,
  idempotent replay, restart, concurrency, populated upgrade, corruption/
  recovery, and Standard/Demo isolation.

The final reviewed S205 implementation baseline was Python `3061 passed` and Web
`449 passed / 47 files`, with Ruff/import/CLI/messages/contracts/lint/typecheck/
production build passing and migration head `0010_strategy_order_risk`.

Final M33 authority remains:

- StrategySignal is advisory recommendation evidence, not an order;
- M33 OrderIntent is a risk-pending request, not an accepted/routed/executed
  order, reservation, fill, or ledger mutation;
- PreTradeRiskDecision is immutable allow/reject evidence over one exact
  snapshot; `allow` is not automatically fresh execution authorization;
- M31 ledger/account and M32 market/replay truth remain upstream authority; and
- persistence, API, generated contracts, Web, Demo, logging, and descriptor
  metadata remain storage/transport/presentation/verification surfaces only.

M33 closes without execution order, fill, execution pricing, fee calculation,
reservation, fill-caused account mutation, replay progression, runtime worker,
broker, live, or real-money behavior.

### M34 — Current S212 Versioned API Foundation

S208 introduced a separate pure `el_psy_quant.paper_execution` authority
boundary with exact execution-policy values, strict M31/M32/M33 handoff
references, create/step command identities, immutable deterministic
`PaperExecutionOrder`, a compact Order reference, and derived lifecycle state.

S209 adds pure/in-memory one-event execution with immutable Attempt and
unsettled Fill authority, exact M32 `next_event()` progression, deterministic
execution price/slippage/cost evidence, execution-time risk revalidation, and
strict full/partial/no-fill/rejection lifecycle reconstruction.

S210 maps one validated Fill to one M31 `execution_fill_posted` event containing
exactly one cash and one position posting. Buy costs are capitalized; sell cost
basis uses deterministic proportional average cost with exact full-exit cleanup.
One immutable `ExecutionSettlementLink` binds the Fill to that M31 authority.

S211 adds immutable Order/Attempt/Fill/SettlementLink/receipt persistence and
atomic SQLite create/step orchestration across M34, M31 settlement, and M32
checkpoint CAS authority.

S212 adds exactly nine Founder-authenticated Paper Execution operations, strict
public schemas, bounded keyset pagination, stable sanitized errors, request-ID
and audit correlation, canonical OpenAPI, and generated TypeScript contracts.
The migration head remains `0011_paper_execution`; S213–S216 remain planned.

## Current Founder Journey

The existing Founder product supports explicit inspection and controlled
commands across:

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
  -> StrategySignal
  -> OrderIntent or no-action
  -> PreTradeRiskDecision
  -> Lifecycle / Human Decision Evidence
```

The browser remains a presentation and command surface. It does not duplicate
financial calculations, infer market-time truth, calculate Signal/Intent/Risk
authority, silently repair state, select a strategy automatically, execute a
trade, or directly mutate SQLite.

## What the Current Product Is Not Yet

The current product now reaches deterministic risk-checked strategy intent, but
it is not yet true end-to-end simulated execution.

It does not yet provide:

- a Founder Web execution workflow or Demo v6 evidence;
- a durable worker/claim/checkpoint/recovery loop for session execution;
- continuous multi-day Paper Trading;
- broker, QMT, MiniQMT, private-edge, live, or real-money behavior; or
- automatic strategy ranking, approval, optimization, or capital allocation.

## Approved Route to Genuine Paper Trading

```text
M30 Portfolio-Level Decision Review Foundation — Complete
  -> M31 Stateful Paper Account and Ledger Foundation — Complete
  -> M32 Market Data Replay, Trading Calendar, and Session Clock — Complete
  -> M33 Strategy-to-Order and Pre-Trade Risk Pipeline — Complete
  -> M34 Paper Execution Simulator and First True Paper Trading — In Progress (S207–S216)
  -> M35 Durable Paper Runtime and Recovery
  -> M36 Multi-day Paper Operations and Acceptance
```

M34 may consume only an M33 Intent with a matching `allow`
PreTradeRiskDecision and exact verified account/market anchors. At execution
handoff it must revalidate freshness; M33 risk allowance is not automatically
fresh execution authorization.

S207 froze the M34 architecture in Issue #408. S208 completed the pure Order,
policy, handoff, command, and lifecycle foundation. S209 completed the pure
one-event Attempt/Fill/pricing/cost/risk layer. S210 completed pure Fill-to-M31
settlement and link reconciliation. S211 adds durable atomic authority under
Issue #415. S212 adds the versioned API/error/audit/generated-contract boundary
under Issue #417. S213–S216 remain planned.

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
- M33 Signal/Intent/Risk records own immutable strategy-to-risk evidence;
- persistence stores and restores authority but does not replace it;
- API, Web, and Demo payloads remain presentation and verification surfaces;
- raw IDs, states, versions, timestamps, codes, digests, values, and artifact
  content remain authoritative and untranslated;
- the browser never directly accesses SQLite, artifact directories, Python,
  QMT, MiniQMT, or a broker; and
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
message catalogs, ESLint, strict TypeScript, Web tests, and the production
Next.js build.

## Key Records

```text
AGENTS.md
docs/roadmap.md
docs/strategy/paper-trading-runtime-roadmap.md
docs/architecture/portfolio-level-decision-review.md
docs/architecture/stateful-paper-account-and-ledger.md
docs/architecture/strategy-to-order-and-pre-trade-risk.md
docs/milestones/milestone-030-portfolio-level-decision-review-foundation.md
docs/closeouts/milestone-030-portfolio-level-decision-review-foundation-closeout.md
docs/milestones/milestone-031-stateful-paper-account-and-ledger-foundation.md
docs/closeouts/milestone-031-stateful-paper-account-and-ledger-foundation-closeout.md
docs/milestones/milestone-032-market-data-replay-trading-calendar-and-session-clock.md
docs/closeouts/milestone-032-market-data-replay-trading-calendar-and-session-clock-closeout.md
docs/milestones/milestone-033-strategy-to-order-and-pre-trade-risk-pipeline.md
docs/closeouts/milestone-033-strategy-to-order-and-pre-trade-risk-pipeline-closeout.md
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
