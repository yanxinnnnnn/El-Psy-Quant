# Future Platform Roadmap — Founder-Level CTO Plan

## Purpose

El-Psy-Quant is an AI-native quantitative research operating system that turns
trading ideas into reproducible, auditable, risk-aware evidence and explicit
human decisions before real capital is deployed.

The platform must not become a loose collection of strategy scripts, an
autonomous trading bot, or a premature distributed system.

## Long-Term Product Chain

```text
trusted research evidence
  -> realistic backtest and Paper Trading evidence
  -> explicit comparison and governance
  -> usable bilingual Founder decision workspace
  -> portfolio-level decision review
  -> durable Paper Account and ledger truth
  -> deterministic market-session inputs
  -> strategy-to-order and pre-trade risk
  -> simulated execution and first true Paper Trading
  -> durable session runtime
  -> continuous multi-day Paper operations
  -> separately approved live-execution readiness
```

## Current Position

Milestones 1–30 are Complete after Sprint 178 merges.

Completed recent chain:

```text
M25 Paper Trading Productization Planning
M26 Paper Trading Application Service Foundation
M27 Persistence and Paper Job Control Foundation
M28 Founder Paper Trading Web Workspace
M29 Product Feedback and Hardening
M30 Portfolio-Level Decision Review Foundation
```

The next milestone is:

```text
M31 — Stateful Paper Account and Ledger Foundation
```

M31 is In Progress through the approved S179–S188 sequence. Sprints 179–185 are
Complete after PR #367 merged. Sprint 186 is implementation-complete and
pending Founder review; it presents durable account authority through the
bilingual generated-contract-only Founder Web.

## Completed M29 Productization and Hardening

M29 produced:

- complete English and Simplified Chinese support;
- a modern responsive Founder decision workspace;
- a decision-oriented Dashboard;
- explicit Paper Job replay, execution control, retry, recovery, and audit;
- complete stable bilingual error meaning and bounded local observability;
- exact migrations and fail-closed local startup;
- locked Python and Web build/runtime inputs;
- Standard/Demo isolation and read-only verification; and
- documented cold backup, upgrade, Demo reset, and return-to-Standard operation.

Records:

```text
docs/milestones/milestone-029-product-feedback-and-hardening.md
docs/closeouts/milestone-029-product-feedback-and-hardening-closeout.md
```

## Completed M30 Portfolio Decision Review

M30 produced:

- an explicit immutable source with ordered components, evidence, symbols,
  aligned returns, audit context, and digest;
- strict explicit baseline/proposed static scenarios;
- domain-calculated concentration, exposure, overlap, correlation, behavior,
  contribution, drawdown, and proposed impact;
- immutable source, analysis, and human-decision artifacts;
- compact SQLite workflow/idempotency state;
- migration head `0006_portfolio_reviews`;
- exactly four portfolio-review API routes;
- complete bilingual Founder list/create/detail/decision workflows;
- explicit research/evidence composition without manufactured return authority;
- isolated Demo Workspace v2 review, exact replay, decision persistence, and
  Standard isolation;
- installed-wheel Alembic authority for the runtime-only backend; and
- successful Founder Standard/Demo and bilingual browser acceptance.

M30 scenario weights remain review assumptions. M30 approval remains governance
evidence. Neither is account, cash, position, order, fill, fee, or ledger truth.

Records:

```text
docs/architecture/portfolio-level-decision-review.md
docs/milestones/milestone-030-portfolio-level-decision-review-foundation.md
docs/closeouts/milestone-030-portfolio-level-decision-review-foundation-closeout.md
```

## Approved M31–M36 Sequence

M31 has the approved S179–S188 sequence. M32–M36 remain an architectural
sequence without sprint ranges; each must receive its own planning Issue,
architecture review, implementation Issues, Founder acceptance, and manual
merge.

```text
M31 Stateful Paper Account and Ledger Foundation
  -> M32 Market Data Replay, Trading Calendar, and Session Clock
  -> M33 Strategy-to-Order and Pre-Trade Risk Pipeline
  -> M34 Paper Execution Simulator and First True Paper Trading
  -> M35 Durable Paper Runtime and Recovery
  -> M36 Multi-day Paper Operations and Acceptance
```

## M31 — Stateful Paper Account and Ledger Foundation

### User-visible outcome

The Founder can create and inspect a durable local Paper Account whose cash,
positions, controlled adjustments, and account history derive from one auditable
ledger and remain consistent across restarts.

### Approved architecture

Issue #355 defines:

- account identity and lifecycle;
- initial cash and controlled funding/adjustment semantics;
- immutable cash and position ledger entries;
- order and fill persistence boundaries without execution;
- fee and adjustment semantics;
- optimistic concurrency, account versioning, and idempotency;
- snapshots, reconciliation, and derived-balance authority;
- artifact versus SQLite ownership;
- API and bilingual Founder Web boundaries;
- Demo data and Standard isolation;
- migration and upgrade behavior;
- Founder acceptance; and
- how an approved M30 review reference is attached without becoming ledger truth.

Sprint 180 established canonical Decimal values, immutable account identity and
lifecycle commands, deterministic command digests, and a bounded reference from
a genuine approved M30 decision. Sprint 181 added immutable cash/account events,
exact cash postings, cash-only state, and fail-closed digest-chain replay.
Sprint 182 added immutable position postings, exact long-only quantity and
aggregate cost basis, display-only average unit cost, and complete mixed-ledger
replay through the same event chain. Sprint 183 adds a canonical complete projection rebuilt only through
that replay, strict `current` or `reconciliation_required` verification with no
silent repair, and immutable snapshot/reconciliation evidence at exact account
heads. Sprint 184 persists immutable ledger authority, replaceable projections,
and immutable snapshot/reconciliation evidence at migration head
`0007_paper_account_ledger`. Sprint 185 exposes that authority through exactly
ten versioned operations while API/browser payloads and logs remain
non-authoritative. Sprint 186 adds the bilingual Founder account workspace
without browser financial calculation. Demo, integration, and acceptance remain
Sprint 187.

### Explicit M31 non-goals

M31 does not pre-authorize:

- market-data replay or a session clock;
- strategy evaluation for runtime order generation;
- pre-trade order risk;
- simulated execution;
- durable workers or scheduling;
- multi-day operations;
- brokers, QMT, MiniQMT, private-edge, live, or real-money behavior; or
- automatic strategy approval or capital allocation.

## M32 — Market Data Replay, Trading Calendar, and Session Clock

### Outcome

Validated historical market sessions, calendar identity, symbol coverage,
freshness, and deterministic replay can drive later Paper runtime behavior.

### Boundary

M32 establishes market-time truth. It does not generate orders or fills and does
not replace M31 account/ledger truth.

## M33 — Strategy-to-Order and Pre-Trade Risk Pipeline

### Outcome

Approved strategy output can be evaluated against an explicit account and market
session to produce idempotent order intent that passes explicit pre-trade risk.

### Boundary

M33 does not simulate fills or update the account as if execution occurred.

## M34 — Paper Execution Simulator and First True Paper Trading

### Product gate

M34 is the first genuine Paper Trading gate.

At completion, the Founder selects an approved strategy, explicit account,
symbols, and historical session, then the platform itself:

```text
reads validated market data
  -> evaluates the strategy
  -> derives target exposure and order intent
  -> applies pre-trade risk
  -> simulates order lifecycle and fills
  -> posts durable ledger effects
  -> exposes complete audit evidence
```

The Founder no longer supplies orders and fills as the transaction script.
Manual session start is allowed; continuous scheduling is not yet required.

## M35 — Durable Paper Runtime and Recovery

### Outcome

One Paper session advances through durable claims, checkpoints, controls,
duplicate prevention, reconciliation, and interruption recovery.

### Boundary

M35 does not yet prove safe continuous operation across multiple trading days.

## M36 — Multi-day Paper Operations and Acceptance

### Product gate

M36 is the continuous Paper Trading gate.

The same account advances across sessions and trading days with durable
checkpoints, reconciliation, explicit controls, duplicate prevention,
interruption recovery, and Founder operational acceptance.

## Preserved Authority Principles

```text
Browser
  -> Next.js Founder Workspace
  -> fixed same-origin gateway
  -> versioned FastAPI API
  -> thin application services
  -> domain and ledger authorities
  -> compact SQLite state and authoritative artifacts
```

- Domain modules own quantitative and governance calculations.
- Future ledger modules own account truth.
- Completed artifact files own full evidence payloads.
- SQLite owns only approved compact durable state.
- Raw values remain unchanged by localization.
- Standard and Demo remain isolated.
- Human approval never implies execution.
- The browser never connects directly to files, databases, Python, QMT, or a
  broker.

## Future Broker and Live Direction

Broker-specific systems remain adapters behind broker-neutral domain and
application boundaries. Completion of M36 does not automatically authorize a
broker or live deployment.

A later explicit roadmap decision must first establish:

- execution-risk governance;
- live-readiness controls;
- credential and secret handling;
- operational ownership and rollback;
- reconciliation with external broker truth;
- Founder approval; and
- clearly separated real-money acceptance.

No browser-to-QMT direct connection is allowed.

## Explicitly Deferred

Unless a future milestone explicitly approves them:

- broker, QMT, or MiniQMT integration;
- real-money execution;
- automatic strategy ranking or approval;
- automatic capital allocation;
- public SaaS, multi-tenancy, or complex RBAC;
- microservices, Kubernetes, Kafka, or Redis clusters;
- distributed job infrastructure; and
- broad real-time trading-terminal behavior.

## Authoritative Runtime Roadmap

Detailed M30–M36 sequence:

```text
docs/strategy/paper-trading-runtime-roadmap.md
```
