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
    M33 --> M34["M34<br/>First True Paper Trading ✅"]
    M34 --> M35["M35<br/>Durable Runtime & Recovery ✅ after S227 merge"]
    M35 --> M36["M36<br/>Multi-day Operations — Next"]
    M36 --> FUTURE["Future<br/>Execution Readiness & Broker Adapter"]
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
| M30 — Portfolio-Level Decision Review Foundation | S169-178 | Complete | Portfolio-aware human decision governance | Portfolio impact and one human decision are reproducibly reviewable without automatic allocation. |
| M31 — Stateful Paper Account and Ledger Foundation | S179-188 | Complete | Durable account truth | One auditable ledger owns cash, positions, adjustments, and account-derived state across sessions. |
| M32 — Market Data Replay, Trading Calendar, and Session Clock | S189-196 | Complete | Deterministic market-time inputs | Calendar/session/event/replay authority is durable and inspectable. |
| M33 — Strategy-to-Order and Pre-Trade Risk Pipeline | S197-206 | Complete | Account-aware strategy-to-risk authority | Exact strategy and market evidence becomes deterministic Signal, account-bound Intent, and pre-trade Risk authority without execution. |
| M34 — Paper Execution Simulator and First True Paper Trading | S207-216 | Complete | Market/strategy-driven Paper Trading | Simulated execution/fill authority is created from M31/M32/M33 evidence and atomically settles to the account. |
| M35 — Durable Paper Runtime and Recovery | S217-227 | Complete after S227 merge | Restart-safe execution orchestration | Durable runtime/work identity, claims, fencing, recovery, controls, API/CLI/Web, Demo v7, and Founder acceptance are complete. |
| M36 — Multi-day Paper Operations and Acceptance | S228+ TBD | Next / Planning | Continuous multi-session Paper Trading | One account operates safely across sessions and trading days with explicit rollover, recovery, reconciliation, and Founder acceptance. |

## Completed Milestone 31

M31 established durable Paper Account identity/lifecycle, immutable ledger
events/postings, deterministic replay, projection verification, snapshots and
reconciliation, append-only persistence, idempotency/concurrency, versioned API,
bilingual Web, and isolated Demo/recovery evidence.

Final authority:

```text
M31 ledger events/postings = financial authority
M31 ledger replay = account-state authority
projection/snapshot/reconciliation = derived evidence/cache
```

Canonical records:

```text
docs/architecture/stateful-paper-account-and-ledger.md
docs/milestones/milestone-031-stateful-paper-account-and-ledger-foundation.md
docs/closeouts/milestone-031-stateful-paper-account-and-ledger-foundation-closeout.md
```

## Completed Milestone 32

M32 established Trading Calendar/Session definitions, canonical versioned market
events, deterministic replay/cursor/lifecycle, durable persistence, restart
recovery, read-only market-time APIs, bilingual replay inspection, and isolated
Demo evidence.

Final authority:

```text
TradingCalendar / TradingSession = calendar/session authority
MarketDataEvent = canonical market-state event authority
MarketDataReplayEngine = deterministic progression authority
```

Canonical records:

```text
docs/milestones/milestone-032-market-data-replay-trading-calendar-and-session-clock.md
docs/closeouts/milestone-032-market-data-replay-trading-calendar-and-session-clock-closeout.md
```

## Completed Milestone 33

M33 delivered:

```text
M31 Paper Account authority
  + M32 market-time/replay authority
  -> StrategySignal recommendation evidence
  -> account-bound OrderIntent or deterministic no-action
  -> PreTradeRiskDecision allow/reject evidence
  -> future M34 execution candidate only
```

Signal/Intent/Risk records remain immutable strategy-to-risk authority. An
`allow` Decision is not perpetual execution authorization.

Canonical records:

```text
docs/architecture/strategy-to-order-and-pre-trade-risk.md
docs/milestones/milestone-033-strategy-to-order-and-pre-trade-risk-pipeline.md
docs/closeouts/milestone-033-strategy-to-order-and-pre-trade-risk-pipeline-closeout.md
```

## Completed Milestone 34

M34 is the first genuine execution/fill/account-mutation milestone.

Delivered authority:

```text
PaperExecutionOrder
  -> exact one-event Step
    -> PaperExecutionAttempt
      -> optional PaperExecutionFill
        -> one atomic M31 execution_fill_posted settlement
    -> exact M32 progression when an event is consumed
  -> strict historical reconstruction / live freshness / reconciliation
```

M34 introduced migration `0011_paper_execution`, exactly nine versioned Paper
Execution operations, bilingual `/paper-execution`, Demo v6, and adversarial
restart/concurrency/corruption/isolation hardening.

M34 is execution authority and remains manually stepped without M35.

Canonical records:

```text
docs/architecture/paper-execution-simulator.md
docs/milestones/milestone-034-paper-execution-simulator-and-first-true-paper-trading.md
docs/closeouts/milestone-034-paper-execution-simulator-and-first-true-paper-trading-closeout.md
```

## Milestone 35 — Durable Paper Runtime and Recovery

Issue #429 froze M35 architecture. S217–S226 are Complete; S227 is the current
documentation-only closeout and M36 handoff.

M35 adds durable operational orchestration around one exact existing M34 Order:

```text
M31 + M32 + M33
  -> M34 PaperExecutionOrder
    -> M35 PaperRuntime
      -> claim / lease / heartbeat / fencing
      -> PaperRuntimeWork
      -> S222 recovery / S221 runner
        -> exact existing M34 one-event Step
      -> M35 operational checkpoint/audit observation
```

There remains exactly one execution path. M35 does not calculate fills, settle
M31 directly, consume M32 events directly, or repair canonical M31–M34 truth.

Delivered M35 sequence:

| Sprint | Deliverable | Status |
|---:|---|---|
| S217 | M35 architecture and planning — Issue #429 | Complete |
| S218 | Durable runtime contracts, persistence, migration `0012` — #430 / PR #431 | Complete |
| S219 | Claims, leases, heartbeat, fencing, control idempotency — #432 / PR #433 | Complete |
| S220 | Runtime lifecycle services — #434 / PR #435 | Complete |
| S221 | Durable runner over exact existing M34 Step — #436 / PR #437 | Complete |
| S222 | Crash/restart/stale-lease recovery and reconciliation — #438 / PR #439 | Complete |
| S223 | Twelve runtime API operations, audit/contracts, dedicated CLI — #440 / PR #441 | Complete |
| S224 | Founder Durable Paper Runtime Web Workspace — #442 / PR #443 | Complete |
| S225 | Concurrency/idempotency/recovery/observability/isolation hardening — #444 / PR #445 | Complete |
| S226 | Demo v7 E2E and Founder Docker/browser acceptance — #446 / PR #447 | Complete |
| S227 | M35 closeout and M36 handoff — #448 | Complete after merge |

Final accepted M35 implementation baseline:

```text
S226 reviewed head: 9f57f030a7847a7176a09265a56be16faae2362e
S226 reviewed merge ref: 5741c33a49c454bed19169a9fba420c506edd3d4
S226 merge commit / S227 baseline: 6af41c166d4106c89c0189d3688773cde7d2cb77
Python: 3396 passed
Web: 501 passed / 51 files
migration head: 0012_durable_paper_runtime
Demo: v7
Founder Docker/browser acceptance: PASS
```

Canonical records:

```text
docs/milestones/milestone-035-durable-paper-runtime-and-recovery.md
docs/closeouts/milestone-035-durable-paper-runtime-and-recovery-closeout.md
```

## Migration Evolution Through M35

```text
0007_paper_account_ledger
  -> 0008_market_time_foundation
  -> 0009_market_time_runtime
  -> 0010_strategy_order_risk
  -> 0011_paper_execution
  -> 0012_durable_paper_runtime
```

Current head is exactly:

```text
0012_durable_paper_runtime
```

## Next Milestone — M36 Multi-day Paper Operations and Acceptance

M36 is the exact next milestone after S227 merge.

The expected planning gate is:

```text
Sprint 228 — Plan Milestone 36: Multi-day Paper Operations and Acceptance
```

S228 must plan before implementation:

- multi-day operating identity and composition over one-Order M35 runtimes;
- session/day rollover and closed-market/overnight semantics;
- M32 continuation across trading days;
- EOD checkpoints and cross-day restart/recovery;
- cross-day M31 freshness and reconciliation;
- whether/how later M33 decisions and M34 Orders are created;
- operator lifecycle and scheduling/process model;
- cross-day concurrency/idempotency/reconciliation;
- API/Web/Demo evolution and migration needs;
- Standard/Demo isolation;
- multi-account/shared-stream/reservation boundaries;
- whether Demo v8 is required; and
- the detailed M36 sprint sequence.

M36 must preserve the M31–M35 authority chain rather than bypassing it.

## Approved Paper Trading Runtime Sequence

```text
M30 Portfolio-Level Decision Review Foundation — Complete
  -> M31 Stateful Paper Account and Ledger Foundation — Complete
  -> M32 Market Data Replay, Trading Calendar, and Session Clock — Complete
  -> M33 Strategy-to-Order and Pre-Trade Risk Pipeline — Complete
  -> M34 Paper Execution Simulator and First True Paper Trading — Complete
  -> M35 Durable Paper Runtime and Recovery — Complete after S227 merge
  -> M36 Multi-day Paper Operations and Acceptance — exact next milestone
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

- M31 remains financial/account authority.
- M32 remains market-time/progression authority.
- M33 remains immutable strategy-to-risk authority.
- M34 remains execution/fill authority.
- M35 remains runtime orchestration authority only.
- Persistence stores/restores authority but does not redefine it.
- Standard and Demo storage remain isolated.
- Browser/API/Demo remain transport/presentation/verification surfaces according
  to their accepted boundaries.

## Explicitly Deferred

Unless a future milestone explicitly approves them:

- multi-day policy before S228 planning;
- broker, QMT, or MiniQMT integration;
- real-money execution;
- automatic strategy ranking, approval, optimization, or capital allocation;
- public SaaS, multi-tenancy, or complex RBAC;
- microservices, Kubernetes, Kafka, or Redis clusters;
- distributed job infrastructure; and
- broad real-time trading-terminal behavior.
