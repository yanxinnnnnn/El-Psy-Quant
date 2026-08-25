# Paper Trading Runtime Roadmap — M30 to M36

## Purpose

This document defines the Founder-approved route from the completed M29 product
to genuine market-driven and continuous Paper Trading.

It is an architectural sequence, not a fixed date commitment. Every milestone
requires its own planning Issue, architecture review, implementation Issues,
Founder acceptance, and manual merge.

## Current Status

```text
M30 — Complete
M31 — Complete
M32 — Complete
M33 — Complete through S197–S206
M34 — Complete after S216 closeout merge through S207–S216
M35 — exact next milestone; architecture/planning starts with S217 after S216 merge
M36 — Planned future milestone
```

M31 used S179–S188, M32 used S189–S196, M33 used S197–S206, and M34 uses the
approved S207–S216 sequence under architecture Issue #408. S207–S215 are
Complete and S216 is the current documentation-only closeout under Issue #425.
After S216 merge, Sprint 217 is the CTO-owned architecture/planning gate for
M35. No M35 implementation Sprint is pre-approved before that plan.

The current migration head is exactly:

```text
0011_paper_execution
```

Current Demo source/descriptor/dataset remains v6.

## Starting Product After M30

El-Psy-Quant already provided:

- reproducible research and backtesting;
- explicit execution assumptions and Paper Trading records;
- file-authoritative Paper artifacts and result summaries;
- durable manually controlled Paper Jobs and attempts;
- comparison, promotion, decision, report, lifecycle, and portfolio-review
  evidence;
- one local bilingual Founder workspace and versioned API;
- compact SQLite product state and authoritative artifact roots;
- fail-closed Standard/Demo startup and read-only verification;
- isolated persistent Standard and disposable Demo storage; and
- documented local backup, upgrade, reset, recovery, and smoke workflows.

M30 additionally delivered explicit immutable portfolio-review evidence and an
explicit approve/reject/defer human decision. M30 decisions remain governance
evidence only and do not create or fund an account.

## Approved Sequence

```text
M30 Portfolio-Level Decision Review Foundation — Complete
  -> M31 Stateful Paper Account and Ledger Foundation — Complete
  -> M32 Market Data Replay, Trading Calendar, and Session Clock — Complete
  -> M33 Strategy-to-Order and Pre-Trade Risk Pipeline — Complete
  -> M34 Paper Execution Simulator and First True Paper Trading — Complete after S216 merge
  -> M35 Durable Paper Runtime and Recovery — exact next milestone
  -> M36 Multi-day Paper Operations and Acceptance — future
```

## M30 — Portfolio-Level Decision Review Foundation

### Status

**Complete.**

### User-visible outcome

Before considering a strategy for future automated Paper Trading, the Founder can
review an explicit proposal in portfolio context and record one immutable human
decision.

### Delivered authority

- explicit ordered review source and evidence;
- exact aligned historical returns;
- strict explicit static scenarios;
- concentration, exposure, overlap, interaction, behavior, contribution,
  drawdown, and impact evidence;
- immutable source, analysis, and decision artifacts;
- compact durable metadata and idempotency;
- four versioned API routes;
- complete bilingual Founder workflow; and
- isolated deterministic Demo evidence.

### Boundary

M30 does not create account, cash, position, order, fill, fee, market-session,
execution, or runtime truth.

## M31 — Stateful Paper Account and Ledger Foundation

### Status

**Complete.**

### User-visible outcome

The Founder can create and inspect a durable local Paper Account whose cash,
positions, controlled adjustments, and account history are derived from one
auditable ledger and remain consistent across restarts.

### Delivered authority

M31 established:

```text
Paper Account identity/lifecycle
  -> immutable cash and position events/postings
  -> deterministic ledger replay
  -> verified projection cache
  -> immutable snapshot/reconciliation evidence
```

The completed M31 boundary includes exact Decimal contracts, lifecycle and
command idempotency, append-only persistence, one-winner transactions, exact
ledger replay, projection rebuild/verification, snapshots/reconciliations,
versioned API, bilingual Founder Web, isolated Demo, upgrade/restart/recovery,
and Founder acceptance guidance.

### M30 relationship

An approved M30 review may be linked as bounded governance evidence. It does not
create cash, holdings, orders, or execution authority and does not become a
ledger event.

### Boundary

M31 does not introduce market-time authority, strategy-to-order generation,
pre-trade risk, simulated execution, runtime workers, broker behavior, or live
trading.

## M32 — Market Data Replay, Trading Calendar, and Session Clock

### Status

**Complete.**

### User-visible outcome

The Founder can select and inspect one validated historical market session with
explicit calendar, timezone, symbol coverage, canonical events, replay identity,
and cursor state.

### Delivered authority

- Trading Calendar and Trading Session definitions;
- canonical versioned `MarketDataEvent` values;
- deterministic replay ordering, cursor, lifecycle, and stream binding;
- durable market event/replay persistence and restart recovery;
- read-only market-time APIs;
- bilingual Founder replay inspection; and
- isolated Demo/recovery verification.

### Boundary

M32 adds no strategy-to-order generation, execution, broker feed, live
streaming, financial/account mutation, or continuous scheduling.

## M33 — Strategy-to-Order and Pre-Trade Risk Pipeline

### Status

**Complete through S197–S206.** Issue #389 is the authoritative M33 architecture
source. The canonical closeout is:

```text
docs/closeouts/milestone-033-strategy-to-order-and-pre-trade-risk-pipeline-closeout.md
```

### User-visible outcome

The Founder can select one supported versioned strategy runtime, exact M31 Paper
Account authority, exact M32 calendar/session/replay/instrument anchors, and an
explicit risk policy, then inspect deterministic:

```text
StrategySignal
  -> OrderIntent or no-action
  -> allow/reject PreTradeRiskDecision
```

### Delivered authority

M33 delivered:

- exact strategy/version/config binding through one closed runtime adapter;
- deterministic Signal evaluation from an exact consumed M32 replay prefix;
- immutable advisory StrategySignal identity/digest;
- exact account-bound target-versus-current conversion to buy/sell/no-action;
- immutable M33 OrderIntent identity and durable command idempotency;
- explicit `long_only_cash_risk_v1` policy and `latest_trade_price_v1` evidence;
- exact notional and four ordered pre-trade risk rules;
- immutable allow/reject input snapshots and Decisions;
- migration `0010_strategy_order_risk` with append-only Signal/Intent/Decision
  authority and scoped command receipts;
- strict reconstruction, bounded reads, one-winner transactions, restart-safe
  replay, stale-anchor refusal, and corruption/no-repair behavior;
- exactly nine versioned M33 API operations with stable errors, request IDs,
  audit correlation, OpenAPI, and generated TypeScript;
- one bilingual generated-contract-only `/strategy-to-risk` Founder workspace;
  and
- deterministic isolated Demo v5 evidence across install, replay, restart,
  concurrency, populated upgrade, corruption/recovery, and Standard/Demo
  isolation.

The final reviewed S205 baseline was Python `3061 passed` and Web
`449 passed / 47 files`, with the complete repository quality gate green and
migration head `0010_strategy_order_risk`.

### Authority boundary

M33 Signal recommendation remains advisory. M33 Intent is risk-pending and is
not an accepted/routed/executed order. Risk `allow` is immutable evidence over
one exact snapshot, not automatically fresh execution authorization.

M33 performs no reservation, fill, execution price, fee/commission/tax
calculation, ledger posting, account mutation, replay progression, worker,
scheduler, broker, or live behavior.

## M34 — Paper Execution Simulator and First True Paper Trading

### Status

**Complete after the S216 closeout PR is merged.** Issue #408 remains the
authoritative M34 architecture source. The canonical closeout is:

```text
docs/closeouts/milestone-034-paper-execution-simulator-and-first-true-paper-trading-closeout.md
```

### User-visible outcome

One manually controlled historical Paper Trading flow can now follow:

```text
validated M31/M32/M33 authority
  -> immutable simulated PaperExecutionOrder
  -> explicit synchronous one-event Step
  -> deterministic Attempt and optional Fill
  -> atomic durable M31 ledger effects for each Fill
  -> exact M32 cursor progression
  -> historical inspection and reconciliation
```

The Founder no longer pre-supplies fill price or fill quantity as transaction
truth.

### Delivered authority

M34 delivered:

- a separate immutable `paper_execution` Order/Attempt/Fill authority model;
- exact M31/M32/M33 Create/Step freshness and handoff validation;
- the closed `working / partially_filled / filled / rejected /
  partially_filled_rejected` lifecycle derived from immutable history;
- future-event one-step execution using M32 `next_event()` semantics;
- `consumed_trade_event_price_v1` price authority;
- `fixed_bps_slippage_v1` and `per_fill_bps_costs_v1` evidence;
- execution-time `long_only_cash_risk_v1` revalidation without mutating M33;
- exact full/partial/no-fill/risk-reject/exhaustion semantics;
- one atomic M31 `execution_fill_posted` event plus execution-settlement cash
  and execution-fill position postings for every Fill;
- deterministic one-to-one `ExecutionSettlementLink` reconciliation evidence;
- migration `0011_paper_execution` with append-only authority and receipts;
- strict historical/live reconstruction, M31/M32 CAS, one-winner transactions,
  restart-safe idempotency, and read-only reconciliation;
- exactly nine versioned Paper Execution operations with stable errors/audit,
  canonical OpenAPI, and generated TypeScript;
- a bilingual generated-contract-only `/paper-execution` Founder workspace;
- isolated Demo v6 fresh-manual, completed, execution-risk-rejection, and
  exhaustion scenarios through real application paths; and
- adversarial concurrency, SQLite busy, populated upgrade, rollback,
  corruption/no-repair, restart/recovery, API, and Standard/Demo isolation
  evidence.

The final reviewed S215 baseline was Python `3257 passed`, Web
`471 passed / 49 files`, and the complete repository quality gate green. Demo
remains v6 and migration head remains `0011_paper_execution`.

### Boundary

M34 is manual and synchronous. It does not own continuous runtime orchestration,
durable work claims/leases, start/stop/resume automation, a repeated Step loop,
heartbeat/stale-work detection, multi-day operations, broker behavior, or live
trading.

## M35 — Durable Paper Runtime and Recovery

### Status

**Exact next milestone after S216 merge. Architecture/planning only until S217
is accepted.**

The exact next Sprint is:

```text
Sprint 217 — Plan Milestone 35: Durable Paper Runtime and Recovery
```

### User-visible outcome

The Founder should be able to start, inspect, stop, resume, recover, and
reconcile one durable Paper session without relying on fragile in-process
continuation.

### Planning boundary

M35 must reuse the existing M34 execution primitives. In particular, durable
automation must repeatedly invoke the existing one-event M34 Step transaction
rather than inventing another execution/fill/settlement path.

S217 must explicitly decide before implementation:

- durable runtime/work identity;
- work ownership, claim, and lease semantics;
- start/stop/resume controls;
- heartbeat/stale-work detection if approved;
- loop/checkpoint semantics around the existing M34 Step primitive;
- interruption/crash recovery state machine;
- concurrency and duplicate-work behavior;
- operational reconciliation;
- bounded runtime observability;
- API/Web/Demo surfaces;
- migration needs;
- Founder acceptance; and
- the detailed M35 Sprint sequence.

M35 must not silently redefine M34 Order/Attempt/Fill identity, execution
pricing/slippage/cost/risk semantics, event-to-fill truth, M31 settlement
financial authority, M32 replay/cursor authority, M33 immutable authority,
Decimal/digest/idempotency/corruption semantics, Standard/Demo isolation, or
browser authority boundaries.

## M36 — Multi-day Paper Operations and Acceptance

### Status

**Planned future milestone.**

### Product gate

M36 is the continuous multi-session Paper Trading milestone.

### User-visible outcome

One account advances across multiple sessions and trading days with durable
checkpoints, reconciliation, explicit operational controls, duplicate
prevention, interruption recovery, and Founder acceptance.

### Core capability

- multi-session account continuity;
- daily/session scheduling rules;
- session boundaries and checkpoints;
- restart/recovery across days;
- cash/position/order/fill reconciliation;
- duplicate session prevention;
- controlled pause/resume and maintenance; and
- operating history and acceptance evidence.

### Dependency

Durable M35 runtime plus approved M31–M34 authorities.

## Authority Boundaries Across M31–M36

```text
M30 review evidence
  != M31 ledger truth
  != M32 market/session truth
  != M33 signal/intent/risk truth
  != M34 execution/fill truth
  != M35 runtime/checkpoint truth
  != M36 multi-day operating evidence
```

Each layer may reference earlier evidence, but it must not silently copy or
reinterpret another layer's authority.

The preserved product architecture remains:

```text
Browser
  -> Next.js Founder Workspace
  -> fixed same-origin gateway
  -> versioned FastAPI API
  -> thin application services
  -> domain, ledger, market, risk, execution, and runtime authorities
  -> compact SQLite state and authoritative artifacts
```

## Broker and Live Direction After M36

Broker-specific behavior remains behind a future broker-neutral adapter boundary.
M36 completion does not automatically authorize live trading.

A later explicit decision must define broker-neutral execution commands,
isolated adapter/agent behavior, credential and secret handling, external
reconciliation, execution-risk/kill-switch controls, operational ownership,
rollback, live readiness, and Founder real-money acceptance.

No browser-to-QMT direct connection is allowed.

## Planning Rule

Only one milestone is planned and implemented at a time.

The current closeout action is:

```text
complete Sprint 216 documentation-only M34 closeout under Issue #425
```

After the S216 PR is merged, create S217 and plan M35 before any runtime
implementation begins. Do not pre-implement M35 or M36 during S216.
