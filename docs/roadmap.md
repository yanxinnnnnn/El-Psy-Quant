# El-Psy-Quant Roadmap

## Purpose

This rolling roadmap turns the sprint-by-sprint project plan into a milestone
timeline.

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
    M25 --> M30["M30<br/>Portfolio Decision Review 🚧"]
    M30 --> M31["M31-M34<br/>Stateful Market-Driven Paper Trading"]
    M31 --> M35["M35-M36<br/>Durable Multi-day Paper Operations"]
    M35 --> FUTURE["Future<br/>Execution Readiness & Broker Adapter"]
```

## Milestone Table

| Milestone | Sprint Range | Status | Theme | Exit Criteria |
|---|---:|---|---|---|
| M1 — Research Pipeline Foundation | S1-7 | Complete | First reproducible strategy pipeline. | Prices produce signals, positions, returns, and equity. |
| M2 — Performance & Local Data Foundation | S8-12 | Complete | Metrics and deterministic local data. | Local research can be evaluated consistently. |
| M3 — Data Reproducibility & Research Workflow | S13-16 | Complete | Cache and reusable data workflows. | Inputs can be persisted and reused. |
| M4 — Research Experimentation Foundation | S17-20 | Complete | Repeatable experiments. | Parameter runs are reviewable without false alpha claims. |
| M5 — Strategy Realism Foundation | S21-24 | Complete | Costs, slippage, and trade visibility. | Backtests include explicit basic frictions. |
| M6 — Risk & Benchmark Foundation | S25-28 | Complete | Evaluation discipline. | Results include benchmark and risk context. |
| M7 — Multi-Asset Research Foundation | S29-32 | Complete | Multi-symbol research. | Independent symbol workflows can be summarized together. |
| M8 — Research Operations Foundation | S33-36 | Complete | Repeatable local operations. | Experiments can be configured and stored consistently. |
| M9 — Project Quality Foundation | S37-41 | Complete | Automated quality gates. | Pull requests are checked consistently. |
| M10 — Experiment Artifact & Comparison Foundation | S42-46 | Complete | Stable run artifacts. | Existing runs can be inspected and compared. |
| M11 — Strategy Interface Foundation | S47-52 | Complete | Stable strategy boundaries. | Strategies plug into configured workflows through an interface. |
| M12 — Data Integrity & Universe Foundation | S53-57 | Complete | Input and universe validation. | Invalid symbol and price inputs are rejected. |
| M13 — Portfolio Construction Foundation | S58-63 | Complete | Portfolio alignment and allocation. | Static portfolio assumptions are explicit. |
| M14 — Portfolio Risk & Attribution Foundation | S64-69 | Complete | Portfolio explanation. | Risk, drawdown, contribution, and attribution are available. |
| M15 — Backtest Execution Realism Foundation | S70-76 | Complete | Explicit execution assumptions. | Order intents, fills, and realism summaries are reviewable. |
| M16 — Paper Trading Foundation | S77-83 | Complete | Local paper state and records. | Accounts, orders, fills, sessions, and artifacts are explicit. |
| M17 — Paper Trading Persistence & Audit Foundation | S84-89 | Complete | Durable paper outputs. | Paper artifacts can be saved, loaded, validated, and summarized. |
| M18 — Paper Trading Workflow Integration Foundation | S90-95 | Complete | Explicit Paper Run boundary. | A paper request can produce and persist a local result. |
| M19 — Configured Paper Workflow Wiring Foundation | S96-102 | Complete | Config-driven paper runs. | Configured runs can produce and reference paper outputs. |
| M20 — Research-to-Paper Promotion Foundation | S103-109 | Complete | Human-controlled promotion governance. | Evidence, candidates, records, and manifests are explicit. |
| M21 — Paper Run Comparison and Review Foundation | S110-116 | Complete | Multi-run review governance. | Paper runs can be referenced, compared, and reviewed. |
| M22 — Decision Governance Foundation | S117-123 | Complete | Strategy-level human decisions. | Decision evidence and human records are explicit. |
| M23 — Report Artifact Foundation | S124-129 | Complete | Deterministic review packaging. | Report sources, summaries, references, and manifests are explicit. |
| M24 — Strategy Review Workflow Foundation | S130-136 | Complete | Human-controlled lifecycle governance. | Proposals and reviews remain non-executing evidence. |
| M25 — Paper Trading Productization Planning | S137 | Complete | Founder product architecture. | M26-M29 staged productization is explicit. |
| M26 — Paper Trading Application Service Foundation | S138-144 | Complete | Thin local API boundary. | Existing capabilities are exposed through versioned schemas. |
| M27 — Persistence and Paper Job Control Foundation | S145-151 | Complete | Durable controllable local jobs. | Product metadata and jobs are inspectable, idempotent, and recoverable. |
| M28 — Founder Paper Trading Web Workspace | S152-160 | Complete | First usable local Founder Web MVP. | The complete paper-decision journey is usable through Web/API. |
| M29 — Product Feedback and Hardening | S161-168 | Complete | Bilingual daily-use product reliability. | The modernized product is dependable for routine Founder use. |
| M30 — Portfolio-Level Decision Review Foundation | S169-177 | In Progress | Portfolio-aware human decision governance. | Concentration, review exposure, interaction, and historical portfolio impact are reproducibly reviewable without automatic allocation. |
| M31 — Stateful Paper Account and Ledger Foundation | TBD | Planned | Durable account truth. | Cash, positions, orders, fills, and snapshots persist across sessions through one auditable ledger. |
| M32 — Market Data Replay, Trading Calendar, and Session Clock | TBD | Planned | Deterministic market-time inputs. | Validated historical market sessions can drive the Paper runtime with explicit calendars and freshness rules. |
| M33 — Strategy-to-Order and Pre-Trade Risk Pipeline | TBD | Planned | Account-aware automated order intent. | Strategy output becomes idempotent risk-checked Paper orders without Founder-authored orders. |
| M34 — Paper Execution Simulator and First True Paper Trading | TBD | Planned | Market/strategy-driven Paper Trading. | The platform generates orders and fills from market data and strategy output, then updates the durable Paper Account. |
| M35 — Durable Paper Runtime and Recovery | TBD | Planned | Reliable session execution. | Durable claims, checkpoints, explicit controls, duplicate prevention, and interruption recovery exist. |
| M36 — Multi-day Paper Operations and Acceptance | TBD | Planned | Continuous multi-session Paper Trading. | One account can run safely across trading days with reconciliation and Founder operational acceptance. |

M30 now has an approved S169–S177 architecture. M31–M36 sprint ranges remain
intentionally `TBD`; each milestone receives its own planning Issue before
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
  -> formal closeout and runtime-roadmap handoff
```

Delivered sprint sequence:

| Sprint | Deliverable | Status |
|---:|---|---|
| S161 | Founder Feedback and Product Experience Architecture | Complete |
| S162 | Multilingual Foundation and Simplified Chinese Workspace | Complete |
| S163 | Modern Visual System Foundation | Complete |
| S164 | Founder Dashboard and Workflow Information Architecture Refresh | Complete |
| S165 | Reliability, Idempotency, and Job Recovery Hardening | Complete |
| S166 | Error Surface, Observability, and Audit Hardening | Complete |
| S167 | Migration, Test, and Local Deployment Hardening | Complete |
| S168 | Milestone 29 Closeout and M30–M36 Handoff | Complete |

Closeout records:

```text
docs/milestones/milestone-029-product-feedback-and-hardening.md
docs/closeouts/milestone-029-product-feedback-and-hardening-closeout.md
```

## Milestone 30 — Portfolio-Level Decision Review Foundation

M30 is now In Progress through this sequence:

| Sprint | Deliverable | Status |
|---:|---|---|
| S169 | Milestone 30 Architecture and Planning | Complete |
| S170 | Portfolio Review Input and Scenario Contract Foundation | Complete |
| S171 | Concentration and Exposure Analysis Foundation | Complete |
| S172 | Strategy Interaction and Proposed Portfolio Impact Foundation | Complete |
| S173 | Portfolio Review Artifact and Human Decision Foundation | Complete |
| S174 | Durable Portfolio Review Persistence and Application/API Foundation | Complete |
| S175 | Founder Portfolio Decision Review Web Workspace | Complete |
| S176 | Portfolio Review Workflow Integration, Demo, and Acceptance Hardening | Implementation complete; Founder Standard/Demo runtime acceptance remains |
| S177 | Milestone 30 Closeout and M31 Handoff | Planned |

The M30 product chain is:

```text
validated review source
  -> explicit baseline and proposed static scenarios
  -> concentration and review exposure
  -> strategy interaction and symbol overlap
  -> baseline/proposed historical portfolio impact
  -> immutable review evidence
  -> explicit human approve / reject / defer decision
  -> bilingual Founder inspection and audit
```

Architecture and milestone plan:

```text
docs/architecture/portfolio-level-decision-review.md
docs/milestones/milestone-030-portfolio-level-decision-review-foundation.md
```

M30 does not allocate capital, mutate an account, generate orders, simulate
fills, start a worker, connect to a broker, or implement M31–M36 behavior.

Sprint 170 supplies immutable, digestible, in-memory source/component/evidence/
aligned-return and baseline/proposed scenario contracts. Sprint 171 adds pure
in-memory concentration, ordered weight-change review exposure, declared-symbol
evidence, and active-universe coverage results. Sprint 172 adds source-ordered
declared-symbol overlap, pairwise and candidate-to-baseline correlation,
baseline/proposed historical behavior, component contribution, and exact
proposed-minus-baseline impact as immutable in-memory domain results. Both
analysis factories reject caller-authored calculations. Sprint 173 adds
immutable historical-scenario analysis and governance-only decision payloads,
canonical SHA-256 digests, UTC audit normalization, and typed
source/analysis/decision references. Source observations remain separate.
Sprint 174 adds fixed hashed write-once source/analysis/decision files, strict
reopen and domain recalculation, one compact SQLite record, create/decision
idempotency, one-winner settlement, four authenticated API routes, and explicit
OpenAPI/generated TypeScript contracts. It adds no Founder Web, Demo data,
lifecycle, account, order, execution, M31, private-edge, broker, or live
capability. Migration head is `0006_portfolio_reviews`. Sprint 176 adds explicit
research/evidence composition, isolated Demo dataset/descriptor v2, and read-only
acceptance verification. Sprint 177 is next only after merge and Founder runtime
acceptance.

## Approved Paper Trading Runtime Sequence

The authoritative future plan is:

```text
docs/strategy/paper-trading-runtime-roadmap.md
```

### M30 — Portfolio decision review

M30 adds reproducible portfolio-level context to explicit human decisions before
automatic order generation is introduced. It must not allocate capital or
authorize execution.

### M31–M33 — Build the transaction source of truth

```text
durable Paper Account and ledger
  -> validated market sessions
  -> strategy-to-order conversion
  -> pre-trade risk
```

### M34 — First genuine Paper Trading gate

At M34 completion, the Founder chooses an approved strategy, account, symbols,
and a historical session. The platform itself:

```text
reads validated market data
  -> evaluates the strategy
  -> derives target exposure and orders
  -> applies pre-trade risk
  -> simulates order lifecycle and fills
  -> updates the durable account and ledger
  -> records audit evidence
```

The Founder no longer pre-supplies orders and fills as the transaction script.
Manual session start is allowed; continuous scheduling is not yet required.

### M35–M36 — Make Paper Trading durable and continuous

M35 adds durable runtime claims, checkpoints, explicit controls, duplicate
prevention, and interruption recovery. M36 proves multi-session and multi-day
operation with reconciliation and Founder acceptance.

M36 is the continuous Paper Trading gate.

## Preserved Architecture

```text
Browser
  -> Next.js Founder Workspace
  -> fixed same-origin /api/backend gateway
  -> versioned FastAPI API
  -> thin application services
  -> existing domain modules and artifact readers
  -> isolated SQLite and authoritative artifact roots
```

- Domain modules remain financial and governance authority.
- Completed files remain authoritative artifact payloads.
- SQLite remains compact metadata and operational state.
- Raw API, domain, artifact, and audit values remain unchanged by localization.
- Paper Job state remains separate from lifecycle governance.
- Portfolio review status remains separate from strategy lifecycle and future
  Paper Account state.
- Lifecycle proposals remain non-executing.
- Human review remains explicit evidence.
- Demo and Standard storage remain isolated.
- The browser never directly accesses SQLite, files, Python, QMT, or a broker.

## Future Execution Direction

Broker-specific systems remain adapters behind broker-neutral domain and
application boundaries. No broker or live-execution work begins merely because
M36 is complete.

A later explicit roadmap decision must first establish execution-risk governance,
live-readiness controls, operational readiness, and Founder approval.

```text
Browser
  -> Web/API
  -> broker-neutral execution command
  -> isolated adapter/agent
  -> broker runtime
```

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
