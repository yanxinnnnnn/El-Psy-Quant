# El-Psy-Quant Roadmap

## Purpose

This rolling roadmap turns the sprint-by-sprint project plan into a milestone
sequence.

Guiding principle:

```text
Build reproducible research, evidence, and control boundaries before adding
operational complexity or real capital.
```

## Timeline Overview

```mermaid
flowchart LR
    M1["M1-M8<br/>Research Workflow Foundations ✅"] --> M9["M9-M15<br/>Quality, Portfolio & Execution Realism ✅"]
    M9 --> M16["M16-M19<br/>Paper Trading Evidence Foundations ✅"]
    M16 --> M20["M20-M24<br/>Governance & Review Workflow ✅"]
    M20 --> M25["M25-M29<br/>Founder Productization & Hardening ✅"]
    M25 --> M30["M30<br/>Portfolio Decision Review ✅"]
    M30 --> M31["M31<br/>Stateful Account & Ledger ✅"]
    M31 --> M32["M32<br/>Market Time & Replay ✅"]
    M32 --> M33["M33<br/>Strategy-to-Order & Risk — In Progress"]
    M33 --> M34["M34<br/>First True Paper Trading"]
    M34 --> M35["M35-M36<br/>Durable Multi-day Operations"]
    M35 --> FUTURE["Future<br/>Execution Readiness & Broker Adapter"]
```

## Milestone Table

| Milestone | Sprint Range | Status | Theme | Exit Criteria |
|---|---:|---|---|---|
| M1 — Research Pipeline Foundation | S1-7 | Complete | First reproducible strategy pipeline | Prices produce signals, positions, returns, and equity. |
| M2 — Performance & Local Data Foundation | S8-12 | Complete | Metrics and deterministic local data | Local research can be evaluated consistently. |
| M3 — Data Reproducibility & Research Workflow | S13-16 | Complete | Cache and reusable data workflows | Inputs can be persisted and reused. |
| M4 — Research Experimentation Foundation | S17-20 | Complete | Repeatable experiments | Parameter runs are reviewable without false alpha claims. |
| M5 — Strategy Realism Foundation | S21-24 | Complete | Costs, slippage, and trade visibility | Backtests include explicit basic frictions. |
| M6 — Risk & Benchmark Foundation | S25-28 | Complete | Evaluation discipline | Results include benchmark and risk context. |
| M7 — Multi-Asset Research Foundation | S29-32 | Complete | Multi-symbol research | Independent symbol workflows can be summarized together. |
| M8 — Research Operations Foundation | S33-36 | Complete | Repeatable local operations | Experiments can be configured and stored consistently. |
| M9 — Project Quality Foundation | S37-41 | Complete | Automated quality gates | Pull requests are checked consistently. |
| M10 — Experiment Artifact & Comparison Foundation | S42-46 | Complete | Stable run artifacts | Existing runs can be inspected and compared. |
| M11 — Strategy Interface Foundation | S47-52 | Complete | Stable strategy boundaries | Strategies plug into configured workflows through an interface. |
| M12 — Data Integrity & Universe Foundation | S53-57 | Complete | Input and universe validation | Invalid symbol and price inputs are rejected. |
| M13 — Portfolio Construction Foundation | S58-63 | Complete | Portfolio alignment and allocation | Static portfolio assumptions are explicit. |
| M14 — Portfolio Risk & Attribution Foundation | S64-69 | Complete | Portfolio explanation | Risk, drawdown, contribution, and attribution are available. |
| M15 — Backtest Execution Realism Foundation | S70-76 | Complete | Explicit execution assumptions | Order intents, fills, and realism summaries are reviewable. |
| M16 — Paper Trading Foundation | S77-83 | Complete | Local paper state and records | Accounts, orders, fills, sessions, and artifacts are explicit. |
| M17 — Paper Trading Persistence & Audit Foundation | S84-89 | Complete | Durable paper outputs | Paper artifacts can be saved, loaded, validated, and summarized. |
| M18 — Paper Trading Workflow Integration Foundation | S90-95 | Complete | Explicit Paper Run boundary | A paper request can produce and persist a local result. |
| M19 — Configured Paper Workflow Wiring Foundation | S96-102 | Complete | Config-driven paper runs | Configured runs can produce and reference paper outputs. |
| M20 — Research-to-Paper Promotion Foundation | S103-109 | Complete | Human-controlled promotion governance | Evidence, candidates, records, and manifests are explicit. |
| M21 — Paper Run Comparison and Review Foundation | S110-116 | Complete | Multi-run review governance | Paper runs can be referenced, compared, and reviewed. |
| M22 — Decision Governance Foundation | S117-123 | Complete | Strategy-level human decisions | Decision evidence and human records are explicit. |
| M23 — Report Artifact Foundation | S124-129 | Complete | Deterministic review packaging | Report sources, summaries, references, and manifests are explicit. |
| M24 — Strategy Review Workflow Foundation | S130-136 | Complete | Human-controlled lifecycle governance | Proposals and reviews remain non-executing evidence. |
| M25 — Paper Trading Productization Planning | S137 | Complete | Founder product architecture | M26-M29 staged productization is explicit. |
| M26 — Paper Trading Application Service Foundation | S138-144 | Complete | Thin local API boundary | Existing capabilities are exposed through versioned schemas. |
| M27 — Persistence and Paper Job Control Foundation | S145-151 | Complete | Durable controllable local jobs | Product metadata and jobs are inspectable, idempotent, and recoverable. |
| M28 — Founder Paper Trading Web Workspace | S152-160 | Complete | First usable local Founder Web MVP | The complete paper-decision journey is usable through Web/API. |
| M29 — Product Feedback and Hardening | S161-168 | Complete | Bilingual daily-use product reliability | The modernized product is dependable for routine Founder use. |
| M30 — Portfolio-Level Decision Review Foundation | S169-178 | Complete | Portfolio-aware human decision governance | Concentration, exposure, interaction, historical impact, and one human decision are reproducibly reviewable without automatic allocation. |
| M31 — Stateful Paper Account and Ledger Foundation | S179-188 | Complete | Durable account truth | One auditable ledger owns cash, positions, adjustments, and account-derived state across sessions. |
| M32 — Market Data Replay, Trading Calendar, and Session Clock | S189-196 | Complete | Deterministic market-time inputs | Validated calendars, sessions, canonical market events, replay state, persistence, recovery, API, Web, and Demo evidence are complete. |
| M33 — Strategy-to-Order and Pre-Trade Risk Pipeline | S197-206 | In Progress | Account-aware order intent | Exact strategy and market evidence become deterministic Signal, account-bound intent, and pre-trade risk authority without execution. |
| M34 — Paper Execution Simulator and First True Paper Trading | TBD | Planned | Market/strategy-driven Paper Trading | The platform generates and fills orders from market data and strategy output, then updates the durable account. |
| M35 — Durable Paper Runtime and Recovery | TBD | Planned | Reliable session execution | Durable claims, checkpoints, controls, duplicate prevention, and interruption recovery exist. |
| M36 — Multi-day Paper Operations and Acceptance | TBD | Planned | Continuous multi-session Paper Trading | One account runs safely across sessions and trading days with reconciliation and Founder acceptance. |

M33 uses the approved S197–S206 sequence from Issue #389. M34–M36 retain
intentionally unassigned sprint ranges and each receives its own CTO-owned
architecture-and-planning Issue before implementation.

## Completed Milestone 30

M30 delivered explicit portfolio-level decision review evidence and one explicit
human decision without automatic allocation or execution.

Authoritative records:

```text
docs/architecture/portfolio-level-decision-review.md
docs/milestones/milestone-030-portfolio-level-decision-review-foundation.md
docs/closeouts/milestone-030-portfolio-level-decision-review-foundation-closeout.md
```

## Completed Milestone 31

M31 delivered:

```text
Paper Account identity and lifecycle
  -> immutable cash and position ledgers
  -> aggregate cost basis and deterministic replay
  -> projection rebuild, snapshot, and reconciliation evidence
  -> SQLite persistence, append-only protection, idempotency, and concurrency
  -> versioned API and bilingual Founder Web
  -> isolated Demo v3 upgrade, restart, and recovery evidence
```

Final authority:

- ledger events/postings remain financial authority;
- ledger replay remains account-state authority;
- projection, snapshot, and reconciliation remain derived evidence/cache; and
- API, Web, and Demo remain presentation and verification only.

M30 review evidence may be linked, but it cannot create, fund, or mutate an
account.

Canonical records:

```text
docs/architecture/stateful-paper-account-and-ledger.md
docs/milestones/milestone-031-stateful-paper-account-and-ledger-foundation.md
docs/sprints/sprint-179-milestone-31-architecture-and-planning.md
```

## Completed Milestone 32

M32 delivered:

```text
Trading Calendar and Trading Session authority
  -> canonical versioned MarketDataEvent contract
  -> deterministic replay engine, cursor, lifecycle, and stream binding
  -> durable event/replay persistence and restart-safe recovery
  -> read-only market-time inspection APIs
  -> bilingual Founder Replay Workspace
  -> isolated Demo v4 replay and recovery evidence
```

Completed sprint chain:

| Sprint | Deliverable | Status |
|---:|---|---|
| S189 | Milestone 32 Architecture and Planning | Complete |
| S190 | Trading Calendar Foundation | Complete |
| S191 | Market Data Canonical Contract | Complete |
| S192 | Deterministic Market Data Replay Engine Foundation | Complete |
| S193 | Market Time Persistence and API Layer | Complete |
| S194 | Founder Replay Workspace | Complete |
| S195 | Demo and Recovery Hardening | Complete |
| S196 | Milestone 32 Closeout and M33 Handoff | Complete after merge |

Final authority:

- `TradingCalendar` and `TradingSession` own calendar/session definitions;
- `MarketDataEvent` owns canonical market-state event representation;
- `MarketDataReplayEngine` owns deterministic consumption, cursor, and lifecycle;
- persistence stores and restores those authorities but does not replace them;
- Web and Demo remain presentation and verification only; and
- M31 financial/account authority remains unchanged.

Migration evolution:

```text
0007_paper_account_ledger
  -> 0008_market_time_foundation
  -> 0009_market_time_runtime
```

M32 adds no strategy, order, risk, execution, broker, live, or real-money
behavior.

Authoritative records:

```text
docs/milestones/milestone-032-market-data-replay-trading-calendar-and-session-clock.md
docs/closeouts/milestone-032-market-data-replay-trading-calendar-and-session-clock-closeout.md
docs/milestones/m32-closeout.md
```

## Current Milestone — M33 In Progress

```text
M33 — Strategy-to-Order and Pre-Trade Risk Pipeline
```

Issue #389 is the authoritative M33 architecture source. Sprints 197–200 are
Complete and Sprint 201 is the current implementation sprint. M33 owns:

- canonical strategy signals tied to explicit strategy/evidence identity;
- idempotent order intent;
- account-aware pre-trade risk decisions; and
- an auditable handoff toward the M34 execution simulator.

M33 must consume, not redefine:

- M31 account identity, lifecycle, balances, positions, version, and ledger truth;
- M32 calendar, session, event-time, canonical event, replay cursor, and replay
  lifecycle truth; and
- M30/M31 evidence links as governance references rather than execution authority.

Sprint 201 provides only pure deterministic pre-trade risk evidence over one
complete S200 Order Intent and exact current M31/M32 authority. It records one
explicit long-only cash policy, the latest same-instrument consumed trade price,
exact notional, four ordered rules, an immutable input snapshot, and an
allow/reject decision. Stale or invalid authority produces no decision. It adds
no persistence, API, Web, Demo, reservation, account mutation, replay
progression, fill, or execution behavior.

Approved M33 sprint chain:

| Sprint | Deliverable | Status |
|---:|---|---|
| S197 | Milestone 33 Architecture and Planning | Complete |
| S198 | Strategy Runtime Reference and Signal Contract Foundation | Complete |
| S199 | Deterministic Strategy Signal Evaluation Foundation | Complete |
| S200 | Account-Bound Order Intent and Idempotency Foundation | Complete |
| S201 | Pre-Trade Risk Decision and Evidence Foundation | In Progress |
| S202 | Durable M33 Persistence, Migration, Concurrency, and Application Service | Planned |
| S203 | Versioned Strategy-to-Risk API, Errors, Audit, and Generated Contracts | Planned |
| S204 | Bilingual Founder Strategy-to-Risk Workspace | Planned |
| S205 | Demo v5, Integration, Upgrade, Restart, Recovery, and Acceptance Hardening | Planned |
| S206 | Milestone 33 Closeout and M34 Handoff | Planned |

The migration head remains `0009_market_time_runtime` until the planned S202
additive migration.

## Approved Paper Trading Runtime Sequence

```text
M30 Portfolio-Level Decision Review Foundation — Complete
  -> M31 Stateful Paper Account and Ledger Foundation — Complete
  -> M32 Market Data Replay, Trading Calendar, and Session Clock — Complete
  -> M33 Strategy-to-Order and Pre-Trade Risk Pipeline — In Progress
  -> M34 Paper Execution Simulator and First True Paper Trading
  -> M35 Durable Paper Runtime and Recovery
  -> M36 Multi-day Paper Operations and Acceptance
```

### M34 — First genuine Paper Trading gate

At M34 completion, market data and strategy output drive order intent, pre-trade
risk, simulated fills, and durable account updates. The Founder no longer
pre-supplies orders and fills as the transaction script.

### M36 — Continuous Paper Trading gate

M36 proves the same account can operate across sessions and trading days with
durable checkpoints, reconciliation, controls, duplicate prevention, and
interruption recovery.

Authoritative runtime roadmap:

```text
docs/strategy/paper-trading-runtime-roadmap.md
```

## Preserved Architecture

```text
Browser
  -> Next.js Founder Workspace
  -> fixed same-origin /api/backend gateway
  -> versioned FastAPI API
  -> thin application services
  -> domain modules and artifact readers/writers
  -> compact SQLite state and authoritative artifact roots
```

- Domain modules remain quantitative and workflow authority.
- Ledger events/postings remain financial authority.
- Ledger replay remains Paper Account state authority.
- Calendar/session definitions and canonical market events remain market-time
  authority.
- Replay engine state remains deterministic progression authority.
- Persistence stores/restores authority but does not replace it.
- Raw product truth remains unchanged by localization.
- Standard and Demo storage remain isolated.
- The browser never accesses SQLite, files, Python, QMT, MiniQMT, or a broker.

## Explicitly Deferred

Unless a future milestone explicitly approves them:

- broker, QMT, or MiniQMT integration;
- real-money execution;
- automatic strategy ranking, approval, optimization, or capital allocation;
- public SaaS, multi-tenancy, or complex RBAC;
- microservices, Kubernetes, Kafka, or Redis clusters;
- distributed job infrastructure; and
- broad real-time trading-terminal behavior.
