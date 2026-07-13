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
    M20 --> M25["M25-M26<br/>Productization Planning & API ✅"]
    M25 --> M27["M27-M29<br/>Founder Paper Productization 🟡"]
    M27 --> M30["M30+<br/>Portfolio Decisions & Execution Readiness"]
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
| M26 — Paper Trading Application Service Foundation | S138-144 | Complete | Add a thin local application-service boundary. | Existing capabilities are exposed through explicit local API schemas without persistence, background workers, broker behavior, or Web UI. |
| M27 — Persistence and Paper Job Control Foundation | S145-151 | In Progress | Add product persistence and controllable local jobs. | Product metadata and paper jobs are durable, inspectable, idempotent, recoverable, and manually controlled. |
| M28 — Founder Paper Trading Web Workspace | S152-159 | Planned | Deliver the first usable Founder Web MVP. | The Founder can inspect strategies and operate paper workflows locally through the Web/API boundary. |
| M29 — Product Feedback and Hardening | S160-165 | Planned | Improve usability and reliability from real usage. | Founder feedback is incorporated and the local product is reliable enough for daily use. |
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

## Completed Milestone 25 — Paper Trading Productization Planning

Milestone 25 converts the productization pivot into an explicit implementation plan.

Approved product architecture:

```text
Browser
  -> React/Next.js founder workspace
  -> FastAPI application API
  -> thin application services / use cases
  -> existing domain modules and artifact readers
  -> SQLite product repositories and simple local job runner
```

Critical ownership decisions:

- existing domain modules remain authoritative for financial and governance rules
- existing artifact files remain authoritative for completed outputs
- SQLite stores product metadata and references rather than silently duplicating full artifact payloads
- lifecycle current state is derived from immutable snapshots and approved human records
- paper job status is separate mutable operational state
- the browser uses the API and never directly accesses the database, filesystem, Python modules, QMT, or a broker

### M26 Sprint Sequence

| Sprint | Deliverable |
|---:|---|
| S138 | Application Service and API Skeleton. **Complete.** |
| S139 | Strategy Catalog and Detail Read Services. **Complete.** |
| S140 | Research and Backtest Artifact Inspection Services. **Complete.** |
| S141 | Governance, Report, and Lifecycle Evidence Inspection Services. **Complete.** |
| S142 | Paper Run Application Command Boundary. **Complete.** |
| S143 | Lifecycle Proposal and Human Review Application Commands. **Complete.** |
| S144 | Milestone 26 Closeout. **Complete.** |

### M27 Sprint Sequence

| Sprint | Deliverable |
|---:|---|
| S145 | SQLite and SQLAlchemy Product Persistence Foundation. **Complete.** |
| S146 | Artifact Index and Product Repository Foundation. **Complete.** |
| S147 | Durable Paper Job Record and Submission Foundation. **Complete.** |
| S148 | Simple Local Paper Job Runner and Manual Control. **Complete.** |
| S149 | Job Recovery, Idempotency, and Error Audit Foundation |
| S150 | Durable Job API and Result Reference Integration |
| S151 | Milestone 27 Closeout |

### M28 Sprint Sequence

| Sprint | Deliverable |
|---:|---|
| S152 | Next.js Workspace Shell and API Client Foundation |
| S153 | Strategy List, Detail, Research, and Backtest Views |
| S154 | Governance Evidence and Report Artifact Views |
| S155 | Paper Run Launch and Status Workspace |
| S156 | Equity, Positions, Orders, and Fills Views |
| S157 | Paper Run Comparison Workspace |
| S158 | Lifecycle Proposal, Human Review, and Timeline Workspace |
| S159 | Minimal Authentication, Docker Compose, and End-to-End MVP Closeout |

### M29 Sprint Sequence

| Sprint | Deliverable |
|---:|---|
| S160 | Founder Usage Review and Hardening Prioritization |
| S161 | Workflow and Information Architecture Hardening |
| S162 | Reliability, Idempotency, and Job Recovery Hardening |
| S163 | Error Surface, Observability, and Audit Hardening |
| S164 | Migration, Test, and Local Deployment Hardening |
| S165 | Milestone 29 Closeout and M30 Handoff |

See:

```text
docs/milestones/milestone-025-paper-trading-productization-planning.md
docs/sprints/sprint-137-milestone-25-paper-trading-productization-planning.md
```

## Completed Milestone 26 — Paper Trading Application Service Foundation

Milestone 26 established a thin local application/API boundary without replacing existing domain or artifact authority.

Completed chain:

```text
application/API skeleton
  -> strategy catalog reads
  -> research and backtest artifact inspection
  -> governance, report, and lifecycle evidence inspection
  -> synchronous paper-run command
  -> lifecycle proposal and human-review commands
  -> closeout
```

Delivered boundaries:

- deterministic FastAPI application construction and `/api/v1`
- server-owned request IDs and stable sanitized errors
- explicit request and response schemas
- safe configured artifact inspection
- synchronous in-memory commands over existing paper and lifecycle factories
- no product persistence or operational job control

Preserved guardrails:

- existing artifact files remain authoritative
- lifecycle current state is not stored as an independent mutable field
- paper-job status remains separate from lifecycle governance
- no database, repository, worker, queue, Web UI, broker, QMT, live, or capital behavior was added

See:

```text
docs/milestones/milestone-026-paper-trading-application-service-foundation.md
docs/sprints/sprint-144-milestone-26-closeout.md
```

## Founder Product Target

The first product is local, Founder-only, single-user or minimally authenticated, and Paper Trading only.

It supports:

- strategy list and detail
- research and backtest inspection
- governance evidence and report-artifact inspection
- paper-run launch and status
- equity, positions, orders, and fills
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

Explicitly defer microservices, Kubernetes, Kafka, Redis clusters, distributed queues, multi-tenancy, complex RBAC, cloud SaaS hosting, broad real-time dashboards, broker integration, automatic lifecycle transitions, automatic capital allocation, and real-money trading.

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
11. Existing artifact files remain authoritative; product persistence should index and operate around them.
12. Operational paper-job state must remain separate from strategy lifecycle governance.
13. Broker-specific concerns must remain behind adapters.
14. Real capital requires separate risk, operational, and live-readiness governance.

## Milestone 27 Progress

Sprint 145 established:

- one explicit local SQLite file selected through `EL_PSY_QUANT_PRODUCT_DATABASE_PATH`
- a project-owned SQLAlchemy 2.x declarative metadata boundary
- lazy SQLite engine construction with foreign-key enforcement
- caller-owned session factories and explicit transactions
- an intentionally empty Alembic baseline that upgrades and downgrades cleanly

It did not add artifact indexes, product repositories, durable paper jobs,
workers, new APIs, lifecycle current-state storage, Web UI, broker, QMT, live,
or capital behavior. Existing artifact files remain authoritative.

Sprint 146 established:

- one immutable six-field index entry for exactly four supported manifest types
- one constrained `artifact_index_entries` table and `0002_artifact_index`
  migration directly after the unchanged Sprint 145 baseline
- root-isolated replacement with stale cleanup under caller-owned transactions
- explicit multi-root refresh using only existing authoritative list readers
- database-only exact and filtered index reads with no artifact payload access

It did not copy payloads or absolute roots into SQLite and added no automatic
refresh, API endpoint, paper-job record, job status, worker, retry, recovery,
idempotency, lifecycle mutation, Web UI, broker, QMT, live, or capital behavior.

Sprint 147 established:

- one shared validation-only command-to-domain request boundary used by the
  existing synchronous execution command
- one strict canonical `PaperRunRequest` codec and immutable paper-job record
- one constrained `paper_jobs` table and `0003_paper_jobs` migration
- one caller-owned repository with add, exact reads, deterministic list, and
  supported-status filtering
- explicit submission that validates and serializes before transactionally
  creating one queued row
- unique durable run IDs with explicit conflicts rather than idempotent success

The durable request snapshot is operational input, not completed artifact
authority. Sprint 147 added no runner, status transition, retry, recovery,
idempotency key, error/result persistence, API endpoint, Web UI, broker, QMT,
live, or capital behavior. The existing synchronous paper-run API remains
unchanged and database-free.

Sprint 148 established:

- one shared request-driven paper workflow reused by configured execution
- exactly four immutable transitions: queued-to-running, queued-to-canceled,
  running-to-succeeded, and running-to-failed
- conditional repository updates under caller-owned transactions
- one explicit runner for one caller-selected queued job, with output preflight
  and workflow execution outside database transactions
- expected local failure recording without persisted error details
- queued-only manual cancellation

The migration chain remains `0001 -> 0002 -> 0003`. Completed paper outputs
remain authoritative files; SQLite stores no result payload or reference.
Sprint 148 adds no queue scan, worker loop, polling, scheduler, retry, recovery,
idempotency, error audit, partial-output cleanup, running-job cancellation, API
endpoint, Web UI, broker, QMT, live, or capital behavior. Interrupted jobs may
remain running and partial output may remain after failure.

## Current Next Step

```text
Sprint 149 — Job Recovery, Idempotency, and Error Audit Foundation
```

Sprint 149 should add only the explicitly designed recovery, idempotency, and
error-audit foundation while preserving Sprint 148's selected-job execution,
file authority, transaction ownership, and lifecycle-separation boundaries.
