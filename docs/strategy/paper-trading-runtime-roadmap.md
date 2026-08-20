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
M34 — In Progress through approved S207–S216; S215 current
M35–M36 — Planned future milestones
```

M31 used S179–S188, M32 used S189–S196, and M33 used S197–S206. Issue #389
remains the authoritative M33 architecture source for the completed boundary.
M34 uses S207–S216 under authoritative architecture Issue #408. S207–S214 are
Complete and S215 is current under Issue #423. M35–M36 retain intentionally
unassigned sprint ranges until each milestone is planned.

The current migration head is exactly:

```text
0011_paper_execution
```

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
  -> M34 Paper Execution Simulator and First True Paper Trading — In Progress
  -> M35 Durable Paper Runtime and Recovery
  -> M36 Multi-day Paper Operations and Acceptance
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

**In Progress through S207–S216. S207–S214 are Complete; Sprint 215 is current.**

M34 is the first genuine market/strategy-driven Paper Trading milestone.

### Entry gate from M33

M34 may consume only an M33 OrderIntent with a matching `allow`
PreTradeRiskDecision and exact verified M31/M32 anchors. Execution handoff must
revalidate account and market freshness; an earlier M33 allow result is not
automatically fresh execution authorization.

### Approved architecture and current implementation

Issue #408 defines M34 authority for:

- execution command identity;
- execution order lifecycle;
- fill timing and execution-price authority;
- rejection and partial-fill semantics;
- slippage, fees, commission, and tax treatment;
- atomic fill-to-M31-ledger postings;
- order/fill/account reconciliation;
- execution idempotency and duplicate prevention;
- execution-time account/market freshness;
- persistence and migration;
- API, Web, Demo, recovery, and acceptance boundaries.

M34 must own execution/fill/ledger effects atomically and must not mutate M33
Signal, Intent, or Decision records.

Sprint 208 completed the pure `paper_execution` Order, policy, exact M31/M32/M33
handoff, create/step command identity, compact reference, and derived lifecycle
contracts.

Sprint 209 adds pure/in-memory one-event execution: exact M32 `next_event()`
progression, immutable Attempt and unsettled Fill authority, deterministic
price/slippage/cost evidence, execution-time risk revalidation, and strict
history-derived lifecycle progression. Boundary attempts leave M32 untouched;
valid in-session outcomes consume exactly one event.

S209 posts no M31 settlement/account mutation and adds no durable replay
checkpoint, persistence, migration, API, Web, Demo, or worker. An S209 Fill is
not proof of M31 settlement.

Sprint 210 adds pure Fill-to-M31 settlement: exactly one combined execution
event, one cash posting, one position posting, exact buy/sell average-cost
effects, and deterministic one-to-one settlement-link reconciliation. M31
replay remains account authority.

Sprint 211 adds durable Order/Attempt/Fill/SettlementLink/receipt persistence,
strict reconstruction, atomic create/step transactions, and M31/M32 CAS
integration.

Sprint 212 adds exactly nine thin authenticated Paper Execution operations,
strict schemas and bounded pagination, stable errors and audit correlation,
canonical OpenAPI, and generated TypeScript contracts. The migration head
remains `0011_paper_execution`. Sprint 213 adds the single bilingual
generated-contract-only Founder workspace for explicit manual control and
immutable evidence inspection. S214 upgrades the isolated Demo source and
descriptor to v6 with four independent execution contexts: one fresh manual
handoff, one completed no-fill/partial/full flow, one execution-time risk
rejection, and one session-boundary exhaustion rejection. Prebuilt M34
authority is created only through the merged application paths. S215–S216
remain bounded to adversarial hardening and closeout respectively. Sprint 215
is current under Issue #423; S216 remains planned.

### User-visible outcome

After M34 is implemented and accepted, one manually started historical session
should be able to follow:

```text
validated M31/M32/M33 authority
  -> simulated execution order
  -> deterministic execution/fill policy
  -> simulated fills or explicit rejection
  -> atomic durable M31 ledger effects
  -> complete reconciliation and audit evidence
```

The Founder no longer pre-supplies orders and fills as the transaction script.

### Non-goals

M34 still does not imply a continuous scheduler, multi-day operation, broker
adapter, live execution, or real-money behavior.

## M35 — Durable Paper Runtime and Recovery

### Status

**Planned future milestone.**

### User-visible outcome

The Founder can start, inspect, stop, resume, recover, and reconcile one Paper
session without relying on a fragile post-response callback.

### Core capability

- durable work claims and leases or equivalent ownership;
- explicit checkpoints and progress;
- start/stop/resume/recover controls;
- heartbeat or stale-work detection where approved;
- duplicate prevention and command idempotency;
- interruption recovery;
- terminal reconciliation; and
- bounded operational observability.

### Dependency

Complete M34 transaction and execution authority.

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

The current implementation action is:

```text
implement Sprint 215 M34 adversarial hardening under Issue #423
```

Do not pre-implement S216 closeout or M35 runtime semantics during S215.
M35–M36 remain future milestones until their predecessors are complete and
explicitly planned.
