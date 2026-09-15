# El-Psy-Quant

An AI-native quantitative research and trading platform built in public.

## Mission

Build a production-ready quantitative research platform from zero to production,
using AI as an engineering teammate while keeping human judgment in control.

The goal is not to claim a magic profitable strategy. The goal is to build a
reproducible, auditable, risk-aware platform that can research, test, review,
operate, and improve trading ideas before real capital is deployed.

## Current Status

Milestones 1–34 are **Complete**. Milestone 35 — Durable Paper Runtime and
Recovery — is in its documentation-only Sprint 227 closeout and becomes
**Complete after the S227 PR is merged**.

Current closeout state:

```text
M35 — Durable Paper Runtime and Recovery
S217 — Complete
S218 — Complete
S219 — Complete
S220 — Complete
S221 — Complete
S222 — Complete
S223 — Complete
S224 — Complete
S225 — Complete
S226 — Complete
S227 — Milestone 35 Closeout and M36 Handoff
```

Issue #429 is the authoritative M35 architecture source. Issue #448 is the
authoritative S227 closeout specification.

After S227 merge, the exact next milestone is:

```text
M36 — Multi-day Paper Operations and Acceptance
```

The expected next Sprint is the CTO-owned architecture/planning gate:

```text
Sprint 228 — Plan Milestone 36: Multi-day Paper Operations and Acceptance
```

Current migration head:

```text
0012_durable_paper_runtime
```

Current Demo source/descriptor/dataset:

```text
v7
```

Canonical recent closeouts:

```text
docs/closeouts/milestone-033-strategy-to-order-and-pre-trade-risk-pipeline-closeout.md
docs/closeouts/milestone-034-paper-execution-simulator-and-first-true-paper-trading-closeout.md
docs/closeouts/milestone-035-durable-paper-runtime-and-recovery-closeout.md
```

## Product Delivered Through M35

The current product provides:

- a local Founder-only Next.js workspace;
- a versioned FastAPI API through a fixed same-origin gateway;
- paired minimal Founder authentication;
- complete English and Simplified Chinese product support;
- a modern responsive AI Quant Decision Workspace visual system;
- a bounded Founder Dashboard for workflow navigation and operational attention;
- authoritative strategy, research, governance, report, Paper Job, result,
  comparison, portfolio-review, lifecycle-review, Paper Account, market-time,
  strategy-to-risk, Paper Execution, and durable Paper Runtime inspection;
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

## Paper Trading Authority Chain

### M31 — Stateful Paper Account and Ledger Foundation

M31 established independent Paper Account identity/lifecycle, immutable cash and
position ledger events/postings, exact Decimal money/quantity, deterministic
ledger replay, projection verification, snapshots/reconciliation, append-only
SQLite persistence, command idempotency/concurrency, versioned API, bilingual Web,
and isolated Demo/recovery evidence.

Final M31 authority:

```text
ledger events/postings = financial authority
ledger replay = account-state authority
projection/snapshot/reconciliation = derived evidence/cache
API/Web/Demo = presentation and verification only
```

### M32 — Market Data Replay, Trading Calendar, and Session Clock

M32 established immutable Trading Calendar and Trading Session authority,
canonical versioned `MarketDataEvent` values, deterministic replay ordering and
cursor/lifecycle state, durable event/replay persistence, restart recovery,
read-only market-time APIs, bilingual replay inspection, and isolated Demo
verification.

Final M32 authority:

```text
TradingCalendar / TradingSession = calendar and session authority
MarketDataEvent = canonical market-state event authority
MarketDataReplayEngine = deterministic progression authority
persistence = store and restore existing authorities only
Web / Demo = presentation and verification only
```

### M33 — Strategy-to-Order and Pre-Trade Risk Pipeline

M33 established the immutable strategy-to-risk chain:

```text
exact versioned strategy runtime + exact M32 replay prefix
  -> StrategySignal recommendation evidence
  -> exact M31 account head
  -> account-bound OrderIntent or deterministic no-action
  -> exact risk/account/market snapshot
  -> immutable allow/reject PreTradeRiskDecision
  -> M34 execution candidate only
```

M33 Signal/Intent/Risk records remain strategy-to-risk authority only. An
`allow` Decision is historical evidence over one exact snapshot, not perpetual
execution authorization.

### M34 — Paper Execution Simulator and First True Paper Trading

M34 established a separate immutable execution boundary:

```text
M31 account authority
  + M32 market/replay authority
  + exact M33 Intent + matching allow Decision
    -> immutable PaperExecutionOrder
      -> explicit synchronous one-event Step
        -> immutable PaperExecutionAttempt
          -> optional immutable PaperExecutionFill
            -> exactly one atomic M31 execution settlement
        -> exact M32 progression when an event is consumed
      -> strict historical reconstruction / live freshness / reconciliation
```

M34 delivers deterministic future-event execution, exact execution price,
slippage, costs, execution-time risk revalidation, Fill-to-M31 settlement,
append-only persistence under `0011_paper_execution`, exactly nine Paper
Execution API operations, bilingual `/paper-execution`, Demo v6, and adversarial
restart/concurrency/corruption/isolation evidence.

M34 remains execution authority. It does not own durable runtime orchestration.

### M35 — Durable Paper Runtime and Recovery

M35 adds durable operational orchestration around the exact existing M34
one-event Step. It does not create a second execution path.

The final chain is:

```text
M31 + M32 + M33
  -> M34 PaperExecutionOrder
    -> M35 PaperRuntime
      -> claim / lease / heartbeat / fencing
      -> durable PaperRuntimeWork
      -> S222 recovery / S221 runner
        -> exact existing M34 one-event Step
      -> M35 checkpoint/audit observation of committed canonical truth
```

M35 delivers:

- one durable `PaperRuntime` immutably bound to one exact existing M34 Order;
- desired/observed states with control-only Start, Resume, and HTTP/Web Recover
  request semantics plus cooperative Stop;
- database-backed one-winner claims, leases, heartbeat, and monotonic fencing;
- one stable logical Work identity per execution version, preserving the exact
  M34 Step key/actor/version across retry, restart, and takeover;
- a strict three-phase transaction model: M35 pre-Step, exact existing M34 Step,
  then M35 post-Step observation;
- explicit crash/restart/stale-lease recovery across windows A–F;
- operational catch-up without canonical M31–M34 repair;
- persistence under migration `0012_durable_paper_runtime`;
- exactly twelve authenticated runtime HTTP operations;
- dedicated `run-paper-runtime` process/CLI surface;
- bilingual `/paper-runtimes` Founder control/inspection workspace;
- adversarial concurrency/idempotency/recovery/observability/isolation
  hardening; and
- deterministic Demo v7 E2E plus Founder Docker/browser/runtime acceptance.

M35 checkpoints and runtime events are operational evidence only. Canonical
progression remains:

```text
M34 history -> execution progression
M32 replay/checkpoint -> market progression
M31 ledger -> financial progression
```

The final accepted S226 baseline is:

```text
Python: 3396 passed
Web: 501 passed / 51 files
migration head: 0012_durable_paper_runtime
Demo: v7
```

## Current Founder Journey

The Founder product supports explicit inspection and controlled commands across:

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
  -> Paper Execution Order / immutable execution evidence
  -> Durable Paper Runtime control / recovery / audit inspection
  -> Lifecycle / Human Decision Evidence
```

The browser remains presentation + bounded command/inspection only. It does not
calculate ledger truth, market-time truth, Signal/Intent/Risk, execution price,
Fill/settlement truth, lease/fencing truth, or runtime recovery authority.

## What the Current Product Is Not Yet

The current product now has restart-safe single-runtime Paper execution around
one exact existing M34 Order.

It does not yet provide:

- multi-day session/day rollover;
- overnight/closed-market operating policy;
- automatic generation of later M33 Decisions or M34 Orders;
- higher-level multi-order/multi-account operating orchestration;
- reservation/capital locking for unfilled quantity;
- distributed queue/cluster scheduling;
- broker, QMT, MiniQMT, private-edge, live, or real-money behavior; or
- automatic strategy ranking, approval, optimization, or capital allocation.

## Approved Route to Genuine Paper Trading

```text
M30 Portfolio-Level Decision Review Foundation — Complete
  -> M31 Stateful Paper Account and Ledger Foundation — Complete
  -> M32 Market Data Replay, Trading Calendar, and Session Clock — Complete
  -> M33 Strategy-to-Order and Pre-Trade Risk Pipeline — Complete
  -> M34 Paper Execution Simulator and First True Paper Trading — Complete
  -> M35 Durable Paper Runtime and Recovery — Complete after S227 merge
  -> M36 Multi-day Paper Operations and Acceptance — exact next milestone
```

M36 is not implemented by S227. Sprint 228 must plan its architecture first,
including multi-day identity, session/day rollover, M32 continuation, EOD
checkpoints, cross-day restart/recovery and M31 freshness, new M33/M34 creation
boundaries, higher-level composition of M35 runtimes, scheduling, concurrency,
idempotency, reconciliation, API/Web/Demo evolution, migration needs, and
acceptance.

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
- M31 ledger events/postings own financial truth and replay owns account state;
- M32 calendar/session/event/replay own market-time truth and progression;
- M33 Signal/Intent/Risk records own immutable strategy-to-risk evidence;
- M34 Order/Attempt/Fill records own immutable execution evidence while M31
  settlement remains financial authority;
- M35 runtime/work/claim/checkpoint/event state owns operational orchestration
  only;
- persistence stores/restores authority but does not replace it;
- API, Web, and Demo remain transport/presentation/verification surfaces;
- raw IDs, states, versions, timestamps, codes, digests, values, and artifact
  content remain authoritative and untranslated;
- the browser never directly accesses SQLite, artifact directories, Python,
  QMT, MiniQMT, or a broker; and
- Standard and Demo storage remain isolated.

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
docs/architecture/stateful-paper-account-and-ledger.md
docs/architecture/strategy-to-order-and-pre-trade-risk.md
docs/architecture/paper-execution-simulator.md
docs/milestones/milestone-031-stateful-paper-account-and-ledger-foundation.md
docs/closeouts/milestone-031-stateful-paper-account-and-ledger-foundation-closeout.md
docs/milestones/milestone-032-market-data-replay-trading-calendar-and-session-clock.md
docs/closeouts/milestone-032-market-data-replay-trading-calendar-and-session-clock-closeout.md
docs/milestones/milestone-033-strategy-to-order-and-pre-trade-risk-pipeline.md
docs/closeouts/milestone-033-strategy-to-order-and-pre-trade-risk-pipeline-closeout.md
docs/milestones/milestone-034-paper-execution-simulator-and-first-true-paper-trading.md
docs/closeouts/milestone-034-paper-execution-simulator-and-first-true-paper-trading-closeout.md
docs/milestones/milestone-035-durable-paper-runtime-and-recovery.md
docs/closeouts/milestone-035-durable-paper-runtime-and-recovery-closeout.md
```

## Explicitly Deferred

Unless a future milestone explicitly approves them:

- M36 multi-day operating policy before S228 planning;
- broker, QMT, or MiniQMT integration;
- real-money execution;
- automatic strategy ranking, approval, optimization, or capital allocation;
- public SaaS, multi-tenancy, or complex RBAC;
- microservices, Kubernetes, Kafka, or Redis clusters;
- distributed job infrastructure; and
- broad real-time trading-terminal behavior.
