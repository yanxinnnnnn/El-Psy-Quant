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
    M30 --> M31["M31<br/>Stateful Account & Ledger — In Progress"]
    M31 --> M32["M32-M34<br/>Market-Driven Paper Trading"]
    M32 --> M35["M35-M36<br/>Durable Multi-day Operations"]
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
| M31 — Stateful Paper Account and Ledger Foundation | S179-188 | In Progress | Durable account truth | One auditable ledger owns cash, positions, adjustments, and account-derived state across sessions. |
| M32 — Market Data Replay, Trading Calendar, and Session Clock | TBD | Planned | Deterministic market-time inputs | Validated historical sessions can drive later Paper runtime behavior. |
| M33 — Strategy-to-Order and Pre-Trade Risk Pipeline | TBD | Planned | Account-aware order intent | Strategy output becomes idempotent risk-checked Paper order intent. |
| M34 — Paper Execution Simulator and First True Paper Trading | TBD | Planned | Market/strategy-driven Paper Trading | The platform generates and fills orders from market data and strategy output, then updates the durable account. |
| M35 — Durable Paper Runtime and Recovery | TBD | Planned | Reliable session execution | Durable claims, checkpoints, controls, duplicate prevention, and interruption recovery exist. |
| M36 — Multi-day Paper Operations and Acceptance | TBD | Planned | Continuous multi-session Paper Trading | One account runs safely across sessions and trading days with reconciliation and Founder acceptance. |

M31 uses the approved S179–S188 sequence. M32–M36 retain intentionally unassigned
sprint ranges and each receives its own architecture-and-planning Issue before
implementation.

## Completed Milestone 29

M29 turned the M28 working MVP into a product suitable for routine Founder use:

```text
complete English / Simplified Chinese product
  -> modern bilingual visual system
  -> decision-oriented Founder Dashboard
  -> understandable Paper Job control and recovery
  -> actionable error and audit surfaces
  -> safe migrations and local deployment
  -> formal runtime-roadmap handoff
```

Sprint range S161–S168 is Complete.

Closeout records:

```text
docs/milestones/milestone-029-product-feedback-and-hardening.md
docs/closeouts/milestone-029-product-feedback-and-hardening-closeout.md
```

## Completed Milestone 30

M30 delivered:

```text
explicit immutable review source
  -> explicit baseline and proposed static scenarios
  -> concentration and review exposure
  -> symbol overlap and historical return interaction
  -> baseline/proposed historical behavior and impact
  -> immutable source, analysis, and decision evidence
  -> bilingual Founder inspection and explicit human decision
  -> isolated Demo v2 and accepted Standard/Demo runtime
```

Completed sprint chain:

| Sprint | Deliverable | Status |
|---:|---|---|
| S169 | Milestone 30 Architecture and Planning | Complete |
| S170 | Portfolio Review Input and Scenario Contract Foundation | Complete |
| S171 | Concentration and Exposure Analysis Foundation | Complete |
| S172 | Strategy Interaction and Proposed Portfolio Impact Foundation | Complete |
| S173 | Portfolio Review Artifact and Human Decision Foundation | Complete |
| S174 | Durable Portfolio Review Persistence and Application/API Foundation | Complete |
| S175 | Founder Portfolio Decision Review Web Workspace | Complete |
| S176 | Portfolio Review Workflow Integration, Demo, and Acceptance Hardening | Complete |
| S177 | Backend Runtime Alembic Resource Packaging and Startup Recovery | Complete |
| S178 | Milestone 30 Closeout and M31 Handoff | Complete after merge |

M30 acceptance confirmed:

- preserved Standard `0005_paper_job_result_references` to
  `0006_portfolio_reviews` upgrade;
- Standard read-only verification and non-mutating smoke;
- Standard remains unseeded;
- Demo Workspace dataset/descriptor v2;
- exact create prefill and replay;
- one explicit decision persisted across Demo restart;
- return-to-Standard storage isolation; and
- English and Simplified Chinese browser acceptance.

M30 does not allocate capital, mutate an account, generate orders, simulate
fills, start a worker, connect to a broker, or implement M31–M36 behavior.

Authoritative records:

```text
docs/architecture/portfolio-level-decision-review.md
docs/milestones/milestone-030-portfolio-level-decision-review-foundation.md
docs/closeouts/milestone-030-portfolio-level-decision-review-foundation-closeout.md
```

## Current Milestone — M31

```text
M31 — Stateful Paper Account and Ledger Foundation
```

Sprint 179 architecture and planning is Complete. Sprint 180 is the first
implementation sprint and adds only pure immutable domain contracts.

M31 must establish independent account and ledger authority for:

- account identity and lifecycle;
- initial cash and controlled adjustments;
- immutable cash and position ledger entries;
- order/fill persistence boundaries without execution;
- fee semantics;
- optimistic concurrency and idempotency;
- snapshots and reconciliation;
- derived balances; and
- an explicit evidence link to approved M30 review records.

M30 scenario weights remain review assumptions. M30 approval remains governance
evidence. Neither becomes account or ledger truth.

Approved M31 sprint chain:

```text
S179 planning
  -> S180 contracts
  -> S181 cash/event authority
  -> S182 position/cost-basis authority
  -> S183 snapshot/reconciliation authority
  -> S184 persistence/application transaction authority
  -> S185 API
  -> S186 Web
  -> S187 integration and Founder acceptance
  -> S188 closeout
```

S179 is Complete. S180 establishes only exact Decimal, identity, lifecycle,
command digest, and approved-M30 provenance-reference contracts. Migration head
remains `0006_portfolio_reviews`.

## Approved Paper Trading Runtime Sequence

```text
M30 Portfolio-Level Decision Review Foundation — Complete
  -> M31 Stateful Paper Account and Ledger Foundation — In Progress
  -> M32 Market Data Replay, Trading Calendar, and Session Clock
  -> M33 Strategy-to-Order and Pre-Trade Risk Pipeline
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

Authoritative roadmap:

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

- Domain modules remain quantitative and governance authority.
- Completed files remain full artifact payload authority.
- SQLite remains compact metadata and operational state.
- Raw product truth remains unchanged by localization.
- Paper Job, lifecycle, portfolio review, and future account state remain
  separate authorities.
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
