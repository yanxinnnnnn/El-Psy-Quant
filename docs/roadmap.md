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
    M32 --> M33["M33<br/>Strategy-to-Order & Risk ✅"]
    M33 --> M34["M34<br/>First True Paper Trading — In Progress"]
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
| M33 — Strategy-to-Order and Pre-Trade Risk Pipeline | S197-206 | Complete | Account-aware strategy-to-risk authority | Exact strategy and market evidence become deterministic Signal, account-bound Intent, and pre-trade Risk authority without execution. |
| M34 — Paper Execution Simulator and First True Paper Trading | S207-216 | In Progress | Market/strategy-driven Paper Trading | The platform creates its own simulated execution/fill authority and atomically posts fill effects to the durable account. |
| M35 — Durable Paper Runtime and Recovery | TBD | Planned | Reliable session execution | Durable claims, checkpoints, controls, duplicate prevention, and interruption recovery exist. |
| M36 — Multi-day Paper Operations and Acceptance | TBD | Planned | Continuous multi-session Paper Trading | One account runs safely across sessions and trading days with reconciliation and Founder acceptance. |

M33 used the approved S197–S206 sequence from Issue #389. M34 uses the approved
S207–S216 sequence from authoritative architecture Issue #408. S207 is Complete
and S208 is current under authoritative implementation Issue #409. M35–M36
retain intentionally unassigned sprint ranges.

## Completed Milestone 30

M30 delivered explicit portfolio-level decision review evidence and one explicit
human decision without automatic allocation or execution.

Canonical records:

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

Canonical records:

```text
docs/architecture/stateful-paper-account-and-ledger.md
docs/milestones/milestone-031-stateful-paper-account-and-ledger-foundation.md
docs/closeouts/milestone-031-stateful-paper-account-and-ledger-foundation-closeout.md
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
| S196 | Milestone 32 Closeout and M33 Handoff | Complete |

Final authority:

- `TradingCalendar` and `TradingSession` own calendar/session definitions;
- `MarketDataEvent` owns canonical market-state event representation;
- `MarketDataReplayEngine` owns deterministic consumption, cursor, and lifecycle;
- persistence stores and restores those authorities but does not replace them;
- Web and Demo remain presentation and verification only; and
- M31 financial/account authority remains unchanged.

## Completed Milestone 33

M33 delivered the deterministic strategy-to-risk chain:

```text
M31 Paper Account authority
  + M32 market-time/replay authority
  -> StrategySignal recommendation evidence
  -> account-bound M33 OrderIntent or deterministic no-action
  -> PreTradeRiskDecision allow/reject evidence
  -> future M34 execution candidate only
```

Completed sprint chain:

| Sprint | Deliverable | Status |
|---:|---|---|
| S197 | Milestone 33 Architecture and Planning | Complete |
| S198 | Strategy Runtime Reference and Signal Contract Foundation | Complete |
| S199 | Deterministic Strategy Signal Evaluation Foundation | Complete |
| S200 | Account-Bound Order Intent and Idempotency Foundation | Complete |
| S201 | Pre-Trade Risk Decision and Evidence Foundation | Complete |
| S202 | Durable M33 Persistence, Migration, Concurrency, and Application Service | Complete |
| S203 | Versioned Strategy-to-Risk API, Errors, Audit, and Generated Contracts | Complete |
| S204 | Bilingual Founder Strategy-to-Risk Workspace | Complete |
| S205 | Demo v5, Integration, Upgrade, Restart, Recovery, and Acceptance Hardening | Complete |
| S206 | Milestone 33 Closeout and M34 Handoff | Complete after merge |

Final M33 authority:

- StrategySignal is immutable advisory recommendation evidence from one exact
  versioned runtime and M32 replay prefix;
- M33 OrderIntent is immutable account-bound risk-pending delta authority and
  is not an accepted or executed order;
- PreTradeRiskDecision is immutable allow/reject evidence over one exact
  account/market/policy snapshot and is not automatically fresh execution
  authorization;
- persistence stores/restores authority but does not redefine it;
- API, OpenAPI, generated TypeScript, Web, Demo, logs, and descriptor metadata
  remain transport/presentation/verification surfaces; and
- M31/M32 authority remains frozen and unmodified.

Migration evolution through current M34:

```text
0007_paper_account_ledger
  -> 0008_market_time_foundation
  -> 0009_market_time_runtime
  -> 0010_strategy_order_risk
  -> 0011_paper_execution
```

The current migration head is exactly `0011_paper_execution`.

Canonical M33 records:

```text
docs/architecture/strategy-to-order-and-pre-trade-risk.md
docs/milestones/milestone-033-strategy-to-order-and-pre-trade-risk-pipeline.md
docs/closeouts/milestone-033-strategy-to-order-and-pre-trade-risk-pipeline-closeout.md
```

M33 closes with no execution order, fill, reservation, execution pricing/fees,
fill-caused account mutation, worker, scheduler, broker, live, or real-money
behavior.

## Current Milestone — M34 In Progress

```text
M34 — Paper Execution Simulator and First True Paper Trading
```

M34 is the first genuine execution/fill/account-mutation milestone. S207 froze
its separate execution authority boundary in Issue #408. S208 now implements
the pure execution Order, policy, handoff, command, and lifecycle contracts
under Issue #409.

M34 may consume only an M33 Intent with a matching `allow` Decision and exact
verified M31/M32 anchors. It must revalidate account and market freshness at
execution time.

S209 completed pure one-event Attempt/Fill/pricing/cost/risk authority. S210
completed pure Fill-to-M31 combined-event settlement and one-to-one link
reconciliation. S211 adds durable immutable M34 records and atomic M31/M32 CAS
transactions under Issue #415. S212 adds exactly nine versioned Paper Execution
operations, stable errors/audit, canonical OpenAPI, and generated contracts
under Issue #417. The migration head remains `0011_paper_execution`;
S213 added the generated-contract-only bilingual Founder Paper Execution
workspace. S214 is current under Issue #421 and upgrades Demo source/descriptor
to v6 with four application-built Paper Execution scenarios. S215–S216 remain
planned; migration head remains `0011_paper_execution`.
M34 must not mutate M33 Signal, Intent, or Decision records.

Approved M34 sequence:

| Sprint | Deliverable | Status |
|---:|---|---|
| S207 | Milestone 34 Architecture and Planning | Complete |
| S208 | Paper Execution Order, Policy, and Lifecycle Contract Foundation | Complete |
| S209 | Deterministic One-Event Execution, Pricing, Costs, and Fill Semantics | Complete |
| S210 | Atomic Execution Fill to M31 Ledger Domain Integration | Complete |
| S211 | Durable M34 Persistence, Migration, Transactions, Idempotency, and Reconciliation | Complete |
| S212 | Versioned Paper Execution API, Errors, Audit, and Generated Contracts | Complete |
| S213 | Bilingual Founder Paper Execution Workspace | Complete |
| S214 | Demo v6 and End-to-End First True Paper Trading Evidence | In Progress |
| S215 | M34 Restart, Concurrency, Upgrade, Recovery, Corruption, and Isolation Hardening | Planned |
| S216 | Milestone 34 Closeout and M35 Handoff | Planned |

## Approved Paper Trading Runtime Sequence

```text
M30 Portfolio-Level Decision Review Foundation — Complete
  -> M31 Stateful Paper Account and Ledger Foundation — Complete
  -> M32 Market Data Replay, Trading Calendar, and Session Clock — Complete
  -> M33 Strategy-to-Order and Pre-Trade Risk Pipeline — Complete
  -> M34 Paper Execution Simulator and First True Paper Trading — In Progress
  -> M35 Durable Paper Runtime and Recovery
  -> M36 Multi-day Paper Operations and Acceptance
```

### M34 — First genuine Paper Trading gate

At M34 completion, verified M31/M32/M33 authority drives simulated execution,
fills, and atomic durable account effects. The Founder no longer pre-supplies
orders and fills as the transaction script.

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
- M33 Signal/Intent/Risk records remain immutable strategy-to-risk authority.
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
