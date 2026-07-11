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
    M20 --> M25["M25-M29<br/>Founder Paper Productization 🟡"]
    M25 --> M30["M30+<br/>Portfolio Decisions & Execution Readiness"]
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
| M25 — Paper Trading Productization Planning | TBD | Next | Plan the founder product boundary and staged architecture. | A reviewed implementation plan exists for M26-M29 without premature implementation. |
| M26 — Paper Trading Application Service Foundation | TBD | Planned | Add the application-service boundary. | Existing domain capabilities are exposed through a small local API without broker behavior. |
| M27 — Persistence and Paper Job Control Foundation | TBD | Planned | Add product persistence and controllable local jobs. | Product entities and paper jobs are durable, inspectable, and manually controlled. |
| M28 — Founder Paper Trading Web Workspace | TBD | Planned | Deliver a usable founder UI. | The founder can inspect strategies and operate paper workflows locally. |
| M29 — Product Feedback and Hardening | TBD | Planned | Improve usability and reliability. | Founder feedback is incorporated and the local product is hardened. |
| M30 — Portfolio-Level Decision Review Foundation | TBD | Deferred | Resume portfolio-level strategy review. | Portfolio impact and concentration are included in human decisions. |

## Completed Milestone 24 — Strategy Review Workflow Foundation

Milestone 24 completed this chain:

```text
strategy review evidence reference contract
  -> strategy lifecycle state snapshot contract
  -> lifecycle transition proposal contract
  -> human-controlled lifecycle transition record
  -> strategy review workflow manifest and references
  -> milestone closeout
```

Approved lifecycle vocabulary:

```text
research_review
paper_review
watchlist
on_hold
rejected
```

Sprint sequence:

| Sprint | Status | Deliverable | Guardrail |
|---:|---|---|---|
| S130 | Complete | M24 scope, vocabulary, matrix, evidence rules, sequence, and guardrails. | Planning only. |
| S131 | Complete | Typed pointers to completed M20-M23 governance artifacts. | No discovery, loading, scoring, or execution. |
| S132 | Complete | Immutable caller-supplied state snapshots. | No implicit or mutable current state. |
| S133 | Complete | Non-executing proposals using the exact 16-pair matrix. | No approval or mutation. |
| S134 | Complete | Human-controlled `approved`, `rejected`, and `deferred` transition records. | Governance evidence only. |
| S135 | Complete | Compact workflow references and grouped manifests. | No ID resolution, chain validation, persistence, or execution. |
| S136 | Complete | Closeout and productization pivot. | Documentation only. |

Milestone 24 did not add runtime state mutation, automatic transitions, automatic decision mapping, artifact loading, workflow orchestration, broker behavior, live readiness, capital deployment, databases, dashboards, or hosted SaaS behavior.

See:

```text
docs/milestones/milestone-024-strategy-review-workflow-foundation.md
docs/sprints/sprint-136-milestone-24-closeout-and-productization-pivot.md
```

## Productization Pivot

The project now has deep foundations for research, paper trading, persistence, review, decisions, reporting, and lifecycle governance. The highest-value next move is to make those capabilities usable through a coherent founder product rather than adding another abstract contract layer.

Provisional sequence:

```text
M25 — Paper Trading Productization Planning
M26 — Paper Trading Application Service Foundation
M27 — Persistence and Paper Job Control Foundation
M28 — Founder Paper Trading Web Workspace
M29 — Product Feedback and Hardening
M30 — Portfolio-Level Decision Review Foundation
```

Portfolio-level review is deferred, not canceled.

## Founder Product Target

The first product should be local and single-user. It should support:

- strategy list and detail
- research and backtest inspection
- governance evidence and report-artifact inspection
- starting and reviewing paper runs
- paper status, equity, positions, orders, and fills
- paper-run comparison
- lifecycle proposals and human transition records
- lifecycle timeline

Planning baseline:

```text
FastAPI
SQLite + SQLAlchemy
simple local background jobs
React/Next.js
Docker Compose / local-first
single-user or minimal authentication
```

Explicitly defer microservices, Kubernetes, Kafka, Redis clusters, multi-tenancy, complex RBAC, real-time dashboards, and broker integration.

## Future Execution Direction

Broker-specific systems must remain adapters behind broker-neutral domain models.

Future QMT boundary:

```text
Browser
  -> Web/API
  -> broker-neutral execution command
  -> Windows QMT agent
  -> MiniQMT
  -> broker
```

No browser-to-QMT direct connection and no live QMT work before dedicated execution-risk and live-readiness governance.

## Roadmap Principles

1. Reproducibility beats convenience.
2. Evaluation discipline comes before strategy complexity.
3. Parameter search is not alpha discovery.
4. Costs, slippage, benchmarks, and risk context precede serious claims.
5. Stable interfaces should come before strategy proliferation.
6. Paper state and auditability should precede broker integration.
7. Promotion, review, decision, and lifecycle records remain human-controlled.
8. A proposal is not an action and an approval record is not runtime execution.
9. Productization should wrap stable domain capabilities rather than rewrite them.
10. Start with one founder and one local deployment before multi-user or cloud complexity.
11. Broker-specific concerns must remain behind adapters.
12. Real capital requires separate risk, operational, and live-readiness governance.

## Current Next Step

```text
Milestone 25 — Paper Trading Productization Planning
```

M25 is planning-only. It should define the founder journeys, application boundary, product data model, API surface, persistence ownership, job-control semantics, UI scope, deployment shape, security baseline, and sprint sequence for M26-M29.
