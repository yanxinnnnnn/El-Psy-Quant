# El-Psy-Quant Roadmap

## Purpose

This roadmap turns the sprint-by-sprint project plan into a clear milestone timeline.

It is a rolling plan rather than a permanent contract. The order may change when the project learns something important, but the guiding principle remains:

```text
Build a reproducible research and decision platform before adding operational complexity or real capital.
```

For the founder-level strategic plan, see:

```text
docs/strategy/future-platform-roadmap.md
```

## Timeline Overview

```mermaid
flowchart LR
    M1["M1-M8<br/>Research Workflow Foundations ✅"] --> M9["M9-M15<br/>Quality, Portfolio & Execution Realism ✅"]
    M9 --> M16["M16-M19<br/>Paper Trading & Configured Workflow ✅"]
    M16 --> M20["M20-M24<br/>Governance & Review Workflow ✅"]
    M20 --> M25["M25-M28<br/>Founder Paper Productization ✅"]
    M25 --> M29["M29<br/>Product Feedback & Hardening 🟡"]
    M29 --> M30["M30+<br/>Portfolio Decisions & Execution Readiness"]
```

## Milestone Table

| Milestone | Sprint Range | Status | Theme | Exit Criteria |
|---|---:|---|---|---|
| M1 — Research Pipeline Foundation | S1-7 | Complete | First reproducible strategy pipeline. | Prices produce signals, positions, returns, and equity. |
| M2 — Performance & Local Data Foundation | S8-12 | Complete | Metrics and deterministic local data. | Local CSV research can be evaluated consistently. |
| M3 — Data Reproducibility & Research Workflow | S13-16 | Complete | Cache and reusable data workflows. | Inputs can be persisted and reused. |
| M4 — Research Experimentation Foundation | S17-20 | Complete | Repeatable experiments. | Parameter runs can be summarized without false alpha claims. |
| M5 — Strategy Realism Foundation | S21-24 | Complete | Costs, slippage, and trade visibility. | Backtests include realistic basic frictions. |
| M6 — Risk & Benchmark Foundation | S25-28 | Complete | Evaluation discipline. | Results include benchmark and risk-adjusted context. |
| M7 — Multi-Asset Research Foundation | S29-32 | Complete | Multi-symbol research. | Independent symbol workflows can be summarized together. |
| M8 — Research Operations Foundation | S33-36 | Complete | Repeatable local operations. | Experiments can be configured and stored consistently. |
| M9 — Project Quality Foundation | S37-41 | Complete | Automated quality gates. | Pull requests are checked consistently. |
| M10 — Experiment Artifact & Comparison Foundation | S42-46 | Complete | Stable run artifacts. | Existing runs can be inspected and compared. |
| M11 — Strategy Interface Foundation | S47-52 | Complete | Stable strategy boundaries. | Strategies plug into configured workflows through an interface. |
| M12 — Data Integrity & Universe Foundation | S53-57 | Complete | Input and universe validation. | Strategy boundaries reject invalid symbol and price inputs. |
| M13 — Portfolio Construction Foundation | S58-63 | Complete | Portfolio alignment and allocation. | Static portfolio construction assumptions are explicit. |
| M14 — Portfolio Risk & Attribution Foundation | S64-69 | Complete | Portfolio explanation. | Risk, drawdown, contribution, and attribution are available. |
| M15 — Backtest Execution Realism Foundation | S70-76 | Complete | Explicit execution assumptions. | Order intents, fills, and realism summaries are reviewable. |
| M16 — Paper Trading Foundation | S77-83 | Complete | Local paper state and records. | Accounts, orders, fills, sessions, and artifacts are explicit. |
| M17 — Paper Trading Persistence & Audit Foundation | S84-89 | Complete | Durable paper outputs. | Paper artifacts can be saved, loaded, validated, and summarized. |
| M18 — Paper Trading Workflow Integration Foundation | S90-95 | Complete | Explicit paper-run boundary. | A paper request can produce and persist a local result. |
| M19 — Configured Paper Workflow Wiring Foundation | S96-102 | Complete | Config-driven paper runs. | Configured runs can produce and reference paper outputs. |
| M20 — Research-to-Paper Promotion Foundation | S103-109 | Complete | Human-controlled promotion governance. | Evidence, candidates, records, and manifests are explicit. |
| M21 — Paper Run Comparison and Review Foundation | S110-116 | Complete | Multi-run review governance. | Paper runs can be referenced, compared, and reviewed. |
| M22 — Decision Governance Foundation | S117-123 | Complete | Strategy-level human decisions. | Decision evidence, summaries, records, and manifests are explicit. |
| M23 — Report Artifact Foundation | S124-129 | Complete | Deterministic review packaging. | Report sources, sections, summaries, references, and manifests are explicit. |
| M24 — Strategy Review Workflow Foundation | S130-136 | Complete | Human-controlled lifecycle governance. | States, proposals, transition records, references, manifests, and guardrails are explicit without runtime lifecycle execution. |
| M25 — Paper Trading Productization Planning | S137 | Complete | Founder product boundary and staged architecture. | A reviewed implementation plan exists for M26-M29 without premature implementation. |
| M26 — Paper Trading Application Service Foundation | S138-144 | Complete | Thin local application-service and API boundary. | Existing capabilities are exposed through explicit local schemas. |
| M27 — Persistence and Paper Job Control Foundation | S145-151 | Complete | Product persistence and controllable local jobs. | Product metadata and paper jobs are durable, inspectable, idempotent, recoverable, and manually controlled. |
| M28 — Founder Paper Trading Web Workspace | S152-160 | Complete | First usable local Founder Web MVP. | The Founder can start, understand, and verify the complete paper-decision journey through the Web/API boundary. |
| M29 — Product Feedback and Hardening | S161-168 | In Progress | Improve product experience and daily local reliability from real use. | The multilingual, modernized product is reliable enough for daily Founder use. |
| M30 — Portfolio-Level Decision Review Foundation | TBD | Deferred | Resume portfolio-level strategy review. | Portfolio impact and concentration are included in human decisions. |

## Completed Milestone 24 — Strategy Review Workflow Foundation

Milestone 24 completed:

```text
strategy review evidence reference
  -> immutable lifecycle state snapshot
  -> non-executing transition proposal
  -> human-controlled transition record
  -> workflow reference and manifest
  -> closeout
```

Approved lifecycle vocabulary:

```text
research_review
paper_review
watchlist
on_hold
rejected
```

Milestone 24 added no runtime state mutation, automatic transition, automatic decision mapping, paper execution, broker behavior, live readiness, or capital deployment.

## Completed Milestone 25 — Paper Trading Productization Planning

Milestone 25 established the approved product architecture:

```text
Browser
  -> React/Next.js Founder workspace
  -> FastAPI application API
  -> thin application services / use cases
  -> existing domain modules and artifact readers
  -> SQLite product repositories and simple local job runner
```

Critical ownership decisions:

- existing domain modules remain authoritative;
- completed artifact files remain payload authority;
- SQLite stores compact metadata and operational state rather than complete payloads;
- lifecycle state is derived from immutable evidence rather than an independent mutable field;
- paper-job state remains separate operational state; and
- the browser uses the API rather than direct database or filesystem access.

## Completed Milestone 26 — Paper Trading Application Service Foundation

Sprint sequence:

| Sprint | Deliverable | Status |
|---:|---|---|
| S138 | Application Service and API Skeleton | Complete |
| S139 | Strategy Catalog and Detail Read Services | Complete |
| S140 | Research and Backtest Artifact Inspection Services | Complete |
| S141 | Governance, Report, and Lifecycle Evidence Inspection Services | Complete |
| S142 | Paper Run Application Command Boundary | Complete |
| S143 | Lifecycle Proposal and Human Review Application Commands | Complete |
| S144 | Milestone 26 Closeout | Complete |

M26 established versioned FastAPI routes, explicit schemas, stable sanitized errors, server-owned request IDs, bounded artifact reads, and thin synchronous commands without product persistence or background-job requirements.

## Completed Milestone 27 — Persistence and Paper Job Control Foundation

Sprint sequence:

| Sprint | Deliverable | Status |
|---:|---|---|
| S145 | SQLite and SQLAlchemy Product Persistence Foundation | Complete |
| S146 | Artifact Index and Product Repository Foundation | Complete |
| S147 | Durable Paper Job Record and Submission Foundation | Complete |
| S148 | Simple Local Paper Job Runner and Manual Control | Complete |
| S149 | Job Recovery, Idempotency, and Error Audit Foundation | Complete |
| S150 | Durable Job API and Result Reference Integration | Complete |
| S151 | Milestone 27 Closeout | Complete |

M27 delivered SQLite and Alembic ownership, a compact artifact index, durable queued jobs, replay-safe submission, attempt audit, manual control and recovery, compact result references, and strict authoritative-file result reads.

## Completed Milestone 28 — Founder Paper Trading Web Workspace

Sprint sequence:

| Sprint | Deliverable | Status |
|---:|---|---|
| S152 | Next.js Workspace Shell and API Client Foundation | Complete |
| S153 | Strategy List, Detail, Research, and Backtest Views | Complete |
| S154 | Governance Evidence and Report Artifact Views | Complete |
| S155 | Paper Run Launch and Status Workspace | Complete |
| S156 | Portfolio Result Views | Complete |
| S157 | Paper Run Comparison Workspace | Complete |
| S158 | Lifecycle Proposal, Human Review, and Timeline Workspace | Complete |
| S159 | Minimal Authentication, Docker Compose, and Engineering MVP Closeout | Complete |
| S160 | Founder Demo Workspace and First-run Experience | Complete |

M28 delivered:

- one local-first Founder-only Web workspace;
- paired minimal authentication for the Web and API;
- reproducible standard Docker Compose startup;
- isolated persistent standard storage;
- an isolated disposable Demo Workspace;
- strategy, research, governance, paper-job, result, comparison, and lifecycle views;
- explicit first-run empty-state guidance;
- product-facing user and operations documentation; and
- one complete guided Strategy-to-Human-Decision journey.

Preserved boundaries:

- domain modules remain authoritative for quantitative and governance behavior;
- artifact files remain payload authority;
- SQLite remains compact product and operational state;
- the browser uses only the same-origin API boundary;
- lifecycle proposals remain non-executing;
- human review remains explicit governance evidence;
- paper-job state remains separate from lifecycle governance; and
- Demo data remains isolated from real user data.

Closeout records:

```text
docs/milestones/milestone-028-founder-paper-trading-web-workspace.md
docs/closeouts/milestone-028-founder-paper-trading-web-workspace-closeout.md
```

## Active Milestone 29 — Product Feedback and Hardening

Milestone 29 begins from real Founder usage rather than speculative features.

### Founder feedback priorities

1. **Multilingual product foundation**
   - English remains the default.
   - Simplified Chinese (`zh-CN`) is the first additional language.
   - Product copy, navigation, forms, states, confirmations, accessibility labels, and stable frontend error explanations must be localized.
   - Raw domain identifiers, API values, IDs, timestamps, schemas, and artifact payloads must remain unchanged.

2. **Product experience refresh**
   - move from an academic portal / internal dashboard toward an AI Quant Decision Workspace;
   - use a modern neutral palette and clean sans-serif typography;
   - improve hierarchy, forms, tables, and data visualization;
   - strengthen product identity; and
   - add a Founder Dashboard and workflow-oriented next actions.

3. **Daily-use hardening**
   - improve idempotency and recovery experience;
   - make errors and audit information actionable;
   - harden migrations, tests, and local deployment; and
   - preserve all existing authority and safety boundaries.

### M29 Sprint Sequence

| Sprint | Deliverable | Status |
|---:|---|---|
| S161 | Founder Feedback and Product Experience Architecture | Next |
| S162 | Multilingual Foundation and Simplified Chinese Workspace | Planned |
| S163 | Modern Visual System Foundation | Planned |
| S164 | Founder Dashboard and Workflow Information Architecture Refresh | Planned |
| S165 | Reliability, Idempotency, and Job Recovery Hardening | Planned |
| S166 | Error Surface, Observability, and Audit Hardening | Planned |
| S167 | Migration, Test, and Local Deployment Hardening | Planned |
| S168 | Milestone 29 Closeout and M30 Handoff | Planned |

Internationalization precedes visual-system implementation so English and Chinese both shape component sizing, typography, spacing, and content hierarchy.

## Founder Product Target

The product remains:

- local-first;
- Founder-only;
- Paper Trading only;
- review-oriented;
- minimally authenticated; and
- a modular monolith.

It is not a live system, broker project, SaaS platform, multi-tenant product, or autonomous strategy and capital engine.

## Future Execution Direction

Broker-specific systems remain adapters behind broker-neutral domain models.

```text
Browser
  -> Web/API
  -> broker-neutral execution command
  -> Windows QMT agent
  -> MiniQMT
  -> broker
```

No browser-to-QMT direct connection and no live QMT work before portfolio review, execution-risk governance, live-readiness controls, and explicit human approval.

## Roadmap Principles

1. Reproducibility beats convenience.
2. Evaluation discipline comes before strategy complexity.
3. Parameter search is not alpha discovery.
4. Costs, slippage, benchmarks, and risk context precede serious claims.
5. Stable interfaces come before strategy proliferation.
6. Paper state and auditability precede broker integration.
7. Promotion, review, decision, and lifecycle records remain human-controlled.
8. A proposal is not an action and an approval record is not runtime execution.
9. Artifact files remain authoritative for completed outputs.
10. Product metadata must not silently replace domain or artifact truth.
11. Visible failure is better than hidden automation.
12. Real Founder feedback outranks speculative product features.
13. Internationalization must be designed before the visual system is finalized.
14. Real capital remains deferred until research, paper evidence, portfolio review, execution-risk controls, operational readiness, and explicit approval are all strong.
