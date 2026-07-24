# Paper Trading Runtime Roadmap — M30 to M36

## Purpose

This document defines the Founder-approved route from the completed M29 product
to genuine market-driven and continuous Paper Trading.

It is an architectural sequence, not a fixed date or sprint commitment. Every
milestone requires its own planning Issue, architecture review, implementation
Issues, Founder acceptance, and manual merge.

## Current Status

```text
M30 — Complete
M31 — In Progress (S179–S183 Complete; S184 durable persistence foundation)
M32–M36 — Planned
```

M31 uses the approved S179–S188 sequence. M32–M36 remain unassigned until each
milestone is planned.

## Starting Product After M30

El-Psy-Quant already provides:

- reproducible research and backtesting;
- explicit execution assumptions and Paper Trading records;
- file-authoritative Paper artifacts and result summaries;
- durable manually controlled Paper Jobs and attempts;
- comparison, promotion, decision, report, lifecycle, and portfolio-review
  evidence;
- one local bilingual Founder workspace and versioned API;
- compact SQLite product state and authoritative artifact roots;
- fail-closed Standard/Demo startup and read-only verification;
- isolated persistent Standard and disposable Demo storage;
- exact migration head `0006_portfolio_reviews`; and
- documented local backup, upgrade, reset, recovery, and smoke workflows.

M30 additionally provides:

```text
explicit immutable portfolio review source
  -> explicit static baseline/proposed scenarios
  -> concentration and review exposure
  -> historical interaction and proposed impact
  -> immutable analysis evidence
  -> explicit approve / reject / defer decision
```

M30 decisions are governance evidence. Scenario weights are review assumptions.
Neither creates or funds an account or becomes ledger truth.

## Approved Sequence

```text
M30 Portfolio-Level Decision Review Foundation — Complete
  -> M31 Stateful Paper Account and Ledger Foundation — In Progress
  -> M32 Market Data Replay, Trading Calendar, and Session Clock
  -> M33 Strategy-to-Order and Pre-Trade Risk Pipeline
  -> M34 Paper Execution Simulator and First True Paper Trading
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
- complete bilingual Founder workflow;
- isolated Demo v2 and exact replay; and
- successful Standard/Demo runtime acceptance.

### Boundary

M30 does not create account, cash, position, order, fill, fee, market-session,
execution, or runtime truth.

## M31 — Stateful Paper Account and Ledger Foundation

### Status

**In Progress — S179–S183 Complete; S184 implementation-complete/pending Founder review.**

### User-visible outcome

The Founder can create and inspect a durable local Paper Account whose cash,
positions, controlled adjustments, and account history are derived from one
auditable ledger and remain consistent across restarts.

### Approved durable/domain capability

Issue #355 defines the approved equivalent of:

```text
PaperAccount
LedgerEntry
CashMovement
PositionMovement
AccountSnapshot
AccountReference
```

Exact names are implementation decisions. Competing mutable balance authorities
are not allowed.

### Approved decisions

The approved architecture defines:

- account ID and lifecycle;
- creation and initial-cash semantics;
- controlled deposit, withdrawal, correction, and fee/adjustment semantics;
- immutable ledger entry identity and ordering;
- cash and position movement representation;
- order/fill persistence boundaries without execution;
- sign conventions and numeric precision;
- account versioning and optimistic concurrency;
- command idempotency and replay;
- snapshot generation and validation;
- reconciliation and derived-balance authority;
- artifact versus SQLite ownership;
- migration and existing-volume upgrade behavior;
- versioned API and bilingual Founder Web boundaries;
- deterministic isolated Demo data;
- errors, observability, backup, recovery, and Founder acceptance; and
- exact linkage to approved M30 evidence.

Sprint 180 established the separate pure `el_psy_quant.paper_account` contracts:
canonical exact Decimal values, identity/reference values, closed lifecycle
validation, deterministic commands, and a trusted bounded approved-M30
provenance reference. Sprint 181 added immutable account events and cash
postings, exact cash-only state, contiguous versions, and fail-closed
digest-chain replay. Sprint 182 added immutable position postings, exact
long-only quantity and aggregate cost basis, display-only average unit cost,
and complete mixed-ledger replay through the same chain. Sprint 183 adds
deterministic complete projections rebuilt from that history, strict candidate
verification without silent repair, and immutable snapshot/reconciliation
evidence. Sprint 184 makes ledger authority, projection caches, and derived
snapshot/reconciliation evidence durable with strict reconstruction,
idempotency, append-only triggers, and one-winner transactions. S185–S187 retain
API, Web, Demo, and acceptance; migration head is
`0007_paper_account_ledger`.

### M30 relationship

An approved M30 review may be attached as evidence through the bounded Sprint
180 reference and Sprint 181 evidence-link event.

That reference:

- does not create or fund an account;
- does not convert scenario weights into holdings;
- does not authorize orders or execution;
- does not become a ledger entry; and
- does not replace explicit account or transaction authority.

### M31 exit direction

M31 completes only when one durable account can be reconstructed and reconciled
from approved immutable ledger truth across restarts, with complete audit and
Founder acceptance.

### Explicit M31 non-goals

M31 does not introduce:

- market data or session clocks;
- strategy evaluation for runtime order generation;
- target exposure or order creation;
- pre-trade order risk;
- simulated execution;
- workers, scheduling, or multi-day runtime;
- broker, QMT, MiniQMT, private-edge, live, or real-money behavior; or
- automatic strategy approval or capital allocation.

## M32 — Market Data Replay, Trading Calendar, and Session Clock

### User-visible outcome

The Founder can select and inspect one validated historical market session with
explicit calendar, timezone, symbol coverage, data freshness, and replay identity.

### Core capability

- market dataset identity and provenance;
- supported symbol/bar contracts;
- trading calendar and timezone rules;
- session open/close and holiday handling;
- deterministic replay cursor/clock;
- missing, stale, duplicate, and out-of-order data rules; and
- reproducible session evidence.

### Dependencies

- durable M31 account identity;
- explicit market-data source authority; and
- no hidden dependence on wall-clock time.

### Exit criteria

The same approved historical session replays deterministically with complete data
and calendar evidence.

### Non-goals

No strategy-to-order generation, execution, broker feed, live streaming, or
continuous scheduling.

## M33 — Strategy-to-Order and Pre-Trade Risk Pipeline

### User-visible outcome

The Founder can select an approved strategy, M31 account, and M32 session and
inspect idempotent strategy output, target exposure/order intent, and explicit
pre-trade risk results.

### Core capability

- exact strategy/version/config binding;
- deterministic signal evaluation;
- account-aware target exposure;
- order-intent identity and idempotency;
- quantity, price, and cash/position checks;
- symbol/session eligibility;
- explicit accept/reject risk evidence; and
- no account mutation before execution.

### Dependencies

- M31 account and ledger truth;
- M32 market/session truth; and
- approved strategy evidence.

### Exit criteria

The same account, strategy, and session produce reproducible risk-checked order
intent without Founder-authored orders.

### Non-goals

No fills, execution simulation, account posting, worker, broker, or live behavior.

## M34 — Paper Execution Simulator and First True Paper Trading

### Product gate

M34 is the first genuine market/strategy-driven Paper Trading milestone.

### User-visible outcome

The Founder selects an approved strategy, account, symbols, and historical market
session. The platform itself:

```text
reads validated market data
  -> evaluates the strategy
  -> derives target exposure and order intent
  -> applies pre-trade risk
  -> simulates order lifecycle and fills
  -> posts durable account/ledger effects
  -> exposes complete audit evidence
```

The Founder no longer supplies the orders and fills as the transaction script.

### Core capability

- explicit order lifecycle;
- deterministic execution timing and price rules;
- partial-fill and rejection semantics;
- slippage, commission, and fee posting;
- atomic fill-to-ledger effects;
- reconciliation of orders, fills, cash, and positions;
- replay/idempotency protection; and
- complete result and audit artifacts.

### Dependencies

M31 account/ledger, M32 market/session, and M33 risk-checked order intent.

### Exit criteria

One manually started historical session completes end to end from strategy output
to simulated fills and reconciled durable account state.

### Non-goals

No continuous scheduler, multi-day operation, broker adapter, or live execution.

## M35 — Durable Paper Runtime and Recovery

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

### Dependencies

Complete M34 transaction and execution authority.

### Exit criteria

Interrupted session work can be classified and recovered without duplicate fills
or ledger effects.

### Non-goals

No continuous multi-day operation, broker, live execution, Kubernetes, or
distributed platform requirement.

## M36 — Multi-day Paper Operations and Acceptance

### Product gate

M36 is the continuous multi-session Paper Trading milestone.

### User-visible outcome

One account advances across multiple sessions and trading days with durable
checkpoints, reconciliation, explicit operational controls, duplicate prevention,
interruption recovery, and Founder acceptance.

### Core capability

- multi-session account continuity;
- daily/session scheduling rules;
- session boundaries and checkpoints;
- restart/recovery across days;
- cash/position/order/fill reconciliation;
- duplicate session prevention;
- controlled pause/resume and maintenance; and
- operating history and acceptance evidence.

### Dependencies

Durable M35 runtime plus approved M31–M34 authorities.

### Exit criteria

The same local account completes an accepted multi-day run with correct state,
complete evidence, and recoverable interruption behavior.

### Non-goals

No broker, QMT, MiniQMT, live, real-money, public SaaS, or distributed
infrastructure without a separate explicit roadmap decision.

## Authority Boundaries Across M31–M36

```text
M30 review evidence
  != M31 ledger truth
  != M32 market/session truth
  != M33 order-intent/risk truth
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

A later explicit decision must define:

- broker-neutral execution commands;
- isolated adapter/agent behavior;
- credential and secret handling;
- external reconciliation;
- execution-risk and kill-switch controls;
- operational ownership and rollback;
- live readiness and Founder approval; and
- real-money acceptance.

No browser-to-QMT direct connection is allowed.

## Planning Rule

Only one milestone is planned and implemented at a time.

The next action after M30 closeout is:

```text
create and review an M31 architecture-and-planning Issue
```

Do not jump directly to M31 implementation or pre-implement M32–M36 behavior.
