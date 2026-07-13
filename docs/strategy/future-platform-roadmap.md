# Future Platform Roadmap — Founder-Level CTO Plan

## Purpose

This document captures the long-term company-level direction for El-Psy-Quant.

El-Psy-Quant should not become a loose collection of strategy scripts or a thin trading bot. The product direction is to build an AI-native quantitative research operating system that turns trading ideas into reproducible, auditable, risk-aware decisions before real capital is deployed.

## Strategic North Star

```text
Build an AI-native quant research operating system that turns trading ideas into reproducible, auditable, risk-aware decisions before any real capital is deployed.
```

The target is not a magic profitable strategy. The target is a trusted decision and operating pipeline.

## Capability Chain

```text
idea
  -> data
  -> research
  -> backtest
  -> portfolio
  -> execution assumptions
  -> paper trading
  -> persistence and audit
  -> configured workflow
  -> promotion governance
  -> paper comparison
  -> strategy decision governance
  -> report artifact
  -> lifecycle governance
  -> application/API boundary
  -> product persistence and job control
  -> founder product workspace
  -> portfolio-level review
  -> execution-risk governance
  -> controlled live readiness
```

## Company-Level Phases

```text
Phase 1 — Research & Artifact Foundation
Phase 2 — Workflow Integration Foundation
Phase 3 — Decision Intelligence Foundation
Phase 4 — Founder Paper Trading Productization
Phase 5 — Portfolio Decisions & Execution Governance
Phase 6 — Controlled Live Pilot & Production Operations
```

The priority order is:

```text
trusted local workflow
  > human-controlled governance
  > usable founder product
  > portfolio-level decisions
  > execution-risk controls
  > broker adapters
  > controlled live pilot
```

The wrong order is:

```text
broker > dashboard > live > strategy zoo
```

That path creates operational and financial risk before the platform earns complexity.

## Phase 1 — Research & Artifact Foundation

Status: Complete through Milestone 18.

This phase established:

- local data loading and validation
- reproducible research pipelines
- experiment artifacts and comparison
- strategy interfaces
- portfolio construction
- portfolio risk and attribution
- explicit execution realism
- paper account state, orders, fills, and sessions
- paper artifact persistence and audit
- explicit local paper-run boundaries

Completed milestone chain:

```text
M1-M8   research workflow and operations
M9      project quality foundation
M10     experiment artifact and comparison foundation
M11     strategy interface foundation
M12     data integrity and universe foundation
M13     portfolio construction foundation
M14     portfolio risk and attribution foundation
M15     backtest execution realism foundation
M16     paper trading foundation
M17     paper trading persistence and audit foundation
M18     paper trading workflow integration foundation
```

## Phase 2 — Workflow Integration Foundation

Status: Complete through Milestone 21.

### Milestone 19 — Configured Paper Workflow Wiring Foundation

Status: Complete.

```text
local config
  -> validated paper run request
  -> configured output layout
  -> paper workflow execution
  -> saved outputs and result references
```

### Milestone 20 — Research-to-Paper Promotion Foundation

Status: Complete.

```text
research evidence
  -> promotion candidate
  -> evidence summary
  -> explicit human promotion record
  -> promotion references and manifest
```

A promotion candidate is not approval. A promotion record does not imply live readiness.

### Milestone 21 — Paper Run Comparison and Review Foundation

Status: Complete.

```text
multiple paper runs
  -> explicit comparison input
  -> comparison summary
  -> human review decision
  -> review references and manifest
```

The comparison layer does not discover runs, rank strategies automatically, or make capital decisions.

## Phase 3 — Decision Intelligence Foundation

Status: Complete through Milestone 24.

### Milestone 22 — Decision Governance Foundation

Status: Complete.

```text
decision evidence
  -> strategy decision input
  -> caller-supplied summary
  -> explicit human decision record
  -> decision references and manifest
```

The layer records why a strategy should continue, pause, be rejected, or need more evidence without becoming an automatic decision engine.

### Milestone 23 — Report Artifact Foundation

Status: Complete.

```text
report source reference
  -> report section
  -> report artifact summary
  -> report reference and manifest
```

Report artifacts package completed governance records. They do not render dashboards, calculate new metrics, recommend decisions, or imply readiness.

### Milestone 24 — Strategy Review Workflow Foundation

Status: Complete.

```text
strategy review evidence reference
  -> lifecycle state snapshot
  -> transition proposal
  -> human-controlled transition record
  -> workflow reference and manifest
  -> closeout
```

Lifecycle vocabulary:

```text
research_review
paper_review
watchlist
on_hold
rejected
```

Transition outcomes:

```text
approved
rejected
deferred
```

Milestone 24 established explicit lifecycle governance while preserving these boundaries:

- no implicit initial state
- no mutable current-state store
- no automatic transition application
- no automatic decision-status mapping
- no evidence discovery, loading, or resolution
- no generic state-machine or workflow engine
- no paper execution triggered by governance records
- no broker behavior, live-readiness claim, or capital deployment

## Phase 4 — Founder Paper Trading Productization

Status: Milestones 25 and 26 complete; Milestone 27 is in progress through
Sprint 148.

The platform has enough domain depth. The current company-level objective is to make existing capabilities usable by the Founder through a coherent local product.

This phase is deliberately single-user and local-first. It is not a SaaS phase.

### Approved Product Architecture

```text
Browser
  -> React/Next.js founder workspace
  -> FastAPI application API
  -> thin application services / use cases
  -> existing El-Psy-Quant domain modules and artifact readers
  -> SQLite product repositories and simple local job runner
```

The implementation remains a modular monolith.

Approved baseline:

- FastAPI
- explicit request and response schemas
- SQLite + SQLAlchemy
- repository boundaries
- simple local background jobs
- React/Next.js
- Docker Compose / local-first deployment
- single-user or minimal authentication

### Product Target

The first product is:

- local-first
- Founder-only
- single-user or minimally authenticated
- Paper Trading only
- review-oriented rather than latency-oriented
- built around existing research, paper, governance, report, and lifecycle capabilities

It is not:

- a live trading system
- a broker integration project
- a SaaS product
- a multi-tenant platform
- a professional real-time trading terminal
- an automatic strategy approval or capital-allocation engine

### Founder Journeys

The staged product must support:

- strategy list and strategy detail
- research and backtest inspection
- governance evidence and report-artifact inspection
- paper-run launch and status
- equity, positions, orders, and fills
- paper-run comparison
- lifecycle transition proposals
- human review records
- lifecycle timeline

M28 must deliver the first usable Web MVP.

M29 must use real founder workflows to harden usability, reliability, recovery, audit visibility, migrations, tests, and local deployment.

### Product Ownership Boundaries

#### Domain Authority

Existing research, backtesting, paper, promotion, comparison, decision, report, and strategy-review modules remain authoritative for quantitative and governance behavior.

The application and UI layers must not duplicate financial calculations, paper execution semantics, comparison logic, governance validation, lifecycle validation, or human-control rules.

API route handlers remain thin and must not become a second domain layer.

#### Artifact Authority

Existing local artifact files remain authoritative for completed research, paper, comparison, governance, and report outputs.

SQLite may store:

- product indexes
- explicit artifact references
- paper job records
- operational status and errors
- idempotency data
- minimal local authentication data

SQLite must not silently copy complete artifact payloads and become a competing source of truth.

Artifact paths must resolve only under configured local roots. Reject path traversal and arbitrary filesystem access.

#### Lifecycle Authority

Do not create an independently authoritative mutable strategy lifecycle `current_state` field.

A current lifecycle view may be derived from immutable state snapshots and approved human transition records.

A transition proposal remains non-executing. A human review record remains governance evidence. Neither silently mutates lifecycle state.

#### Paper Job Authority

Paper job status is mutable operational state and remains separate from strategy lifecycle governance.

M27 may define durable local states equivalent to:

```text
queued
running
succeeded
failed
canceled
```

Exact transitions, retries, idempotency, recovery, and cancellation semantics belong in implementation issues. No distributed execution guarantees may be claimed.

#### Browser Boundary

The browser must use the Web/API boundary.

The UI must not directly access:

- SQLite
- local artifact directories
- Python domain modules
- QMT
- MiniQMT
- any broker

### API Baseline

Milestone 26 established:

- a versioned local API under `/api/v1`
- explicit schemas instead of leaked internal Python objects
- stable sanitized error responses
- server-owned request IDs
- synchronous read operations
- thin application commands over existing local domain behavior
- no product database requirement
- no background worker requirement
- no broker behavior

Milestone 26 production endpoints at closeout:

```text
GET  /api/v1/health
GET  /api/v1/strategies
GET  /api/v1/strategies/{strategy_name}
GET  /api/v1/research-runs
GET  /api/v1/research-runs/{experiment_slug}/{run_id}
GET  /api/v1/evidence-manifests
GET  /api/v1/evidence-manifests/{manifest_type}/{artifact_key}
POST /api/v1/paper-runs
POST /api/v1/lifecycle-transition-proposals
POST /api/v1/lifecycle-transition-records
```

Long-running paper execution should move behind durable local job control in M27 rather than blocking Web requests indefinitely.

### Persistence and Job-Control Baseline

M27 should establish:

- SQLite product persistence
- SQLAlchemy repository boundaries
- migration discipline
- durable paper job records
- idempotent paper-run submission
- inspectable job errors
- a simple in-process or local-process runner
- explicit recovery and restart behavior
- deterministic links from jobs to existing artifact outputs

Do not introduce Kafka, Redis clusters, distributed queues, Kubernetes, or multi-service orchestration.

### Security Baseline

- Bind to loopback by default.
- A loopback-only deployment may use a minimal single-user trust model.
- Any non-loopback exposure must require authentication.
- Do not introduce multi-tenancy or complex RBAC.
- Use same-origin defaults and avoid broad CORS.
- Do not expose arbitrary filesystem paths.
- Do not log secrets, credentials, or authentication material.
- Validate all user-supplied identifiers and paths at the application boundary.

The exact minimal authentication mechanism is deferred to an M28 implementation issue.

### Local Deployment Baseline

- One local machine is the supported target through M29.
- FastAPI and Next.js remain separate logical components without requiring distributed infrastructure.
- Docker Compose may provide convenient startup in M28.
- SQLite data and artifact roots use explicit local volumes or mounts.
- The product remains operable without Kubernetes, cloud services, or external message brokers.

### Milestone 25 — Paper Trading Productization Planning

Status: Complete.

Sprint:

```text
S137 — Paper Trading Productization Planning
```

M25 delivered:

- explicit founder journeys and product non-goals
- application, domain, artifact, persistence, lifecycle, paper-job, and UI ownership boundaries
- API, security, authentication, and local deployment baselines
- M26–M29 sprint sequences and milestone exit criteria
- confirmation that M28 delivers the first Web MVP
- confirmation that M29 is founder-feedback and hardening driven
- preserved QMT and live-readiness boundaries

M25 is documentation-only. It does not implement FastAPI endpoints, database models, job workers, Web screens, deployment files, authentication, QMT, or live behavior.

### Milestone 26 — Paper Trading Application Service Foundation

Status: Complete.

Sprint sequence:

```text
S138 — Application Service and API Skeleton — Complete
S139 — Strategy Catalog and Detail Read Services — Complete
S140 — Research and Backtest Artifact Inspection Services — Complete
S141 — Governance, Report, and Lifecycle Evidence Inspection Services — Complete
S142 — Paper Run Application Command Boundary — Complete
S143 — Lifecycle Proposal and Human Review Application Commands — Complete
S144 — Milestone 26 Closeout — Complete
```

M26 delivered:

- deterministic local FastAPI application construction
- a versioned `/api/v1` boundary
- server-owned request IDs and stable sanitized errors
- explicit request and response schemas
- deterministic strategy catalog reads
- bounded configured research-run and saved-metrics inspection
- bounded configured governance, report, and lifecycle manifest inspection
- a synchronous in-memory explicit-input paper-run command
- synchronous stateless lifecycle proposal and human-review commands

M26 preserved:

- existing domain modules as quantitative and governance authority
- existing local artifact files as completed-output authority
- unresolved evidence pointers
- non-executing lifecycle proposals and human review records
- no independently authoritative lifecycle current-state field
- no product database, durable job, worker, Web UI, broker, QMT, live, or capital behavior

See:

```text
docs/milestones/milestone-026-paper-trading-application-service-foundation.md
docs/sprints/sprint-144-milestone-26-closeout.md
```

### Milestone 27 — Persistence and Paper Job Control Foundation

Status: In Progress.

Sprint sequence:

```text
S145 — SQLite and SQLAlchemy Product Persistence Foundation — Complete
S146 — Artifact Index and Product Repository Foundation — Complete
S147 — Durable Paper Job Record and Submission Foundation — Complete
S148 — Simple Local Paper Job Runner and Manual Control — Complete
S149 — Job Recovery, Idempotency, and Error Audit Foundation
S150 — Durable Job API and Result Reference Integration
S151 — Milestone 27 Closeout
```

Exit criteria:

- product metadata is durable in SQLite
- existing artifacts remain authoritative and are linked by explicit references
- paper-run submissions create durable inspectable jobs
- a simple local runner executes and records jobs
- restart, failure, idempotency, and manual-control behavior are documented and tested
- no distributed infrastructure, broker integration, or Web UI exists

### Milestone 28 — Founder Paper Trading Web Workspace

Status: Planned.

Sprint sequence:

```text
S152 — Next.js Workspace Shell and API Client Foundation
S153 — Strategy List, Detail, Research, and Backtest Views
S154 — Governance Evidence and Report Artifact Views
S155 — Paper Run Launch and Status Workspace
S156 — Equity, Positions, Orders, and Fills Views
S157 — Paper Run Comparison Workspace
S158 — Lifecycle Proposal, Human Review, and Timeline Workspace
S159 — Minimal Authentication, Docker Compose, and End-to-End MVP Closeout
```

Exit criteria:

- the Founder can use the first local Web MVP end to end
- all approved founder journeys are available through the UI
- the browser uses the API rather than direct filesystem or database access
- local startup is documented and reproducible
- authentication matches the approved local exposure model
- no broad real-time terminal, broker integration, or live behavior exists

### Milestone 29 — Product Feedback and Hardening

Status: Planned.

Sprint sequence:

```text
S160 — Founder Usage Review and Hardening Prioritization
S161 — Workflow and Information Architecture Hardening
S162 — Reliability, Idempotency, and Job Recovery Hardening
S163 — Error Surface, Observability, and Audit Hardening
S164 — Migration, Test, and Local Deployment Hardening
S165 — Milestone 29 Closeout and M30 Handoff
```

Exit criteria:

- actual founder usage produces a prioritized feedback record
- high-value workflow friction is reduced
- job recovery and idempotency are reliable for local use
- product errors and audit information are visible and actionable
- API, persistence, and UI boundaries have meaningful test coverage
- local deployment is reliable enough for daily founder use
- speculative features, broker work, and live behavior remain excluded

## Phase 5 — Portfolio Decisions & Execution Governance

Status: Future.

### Milestone 30 — Portfolio-Level Decision Review Foundation

Status: Deferred, not canceled.

Purpose:

Evaluate strategies at portfolio level rather than only as standalone candidates.

Potential review inputs:

- marginal risk contribution
- duplicated factor or symbol exposure
- concentration
- correlation with existing approved strategies
- expected portfolio impact
- capital and turnover implications

This remains human-controlled decision governance, not automatic portfolio optimization or capital allocation.

### Milestone 31 — Broker Abstraction Planning

Define broker-neutral concepts before connecting to any broker:

```text
OrderIntent
ExecutionOrder
ExecutionFill
AccountSnapshot
PositionSnapshot
BrokerOrderReference
```

Define idempotency, retries, reconciliation, error handling, manual approval, and kill-switch boundaries.

### Milestone 32 — Simulated Broker Adapter Foundation

Exercise broker-like acknowledgements, fills, rejections, reconnects, and reconciliation locally without external dependencies.

### Milestone 33 — Execution Risk Control Foundation

Add explicit pre-trade and operational guardrails such as:

- maximum order size
- maximum position size
- maximum turnover
- loss thresholds
- symbol allowlists
- trading windows
- manual approval requirements
- emergency stop behavior

### Milestone 34 — Live Readiness Checklist Foundation

Define eligibility for a controlled live pilot without executing live trades.

```text
strategy evidence
  + paper evidence
  + portfolio review
  + execution-risk controls
  + operational checks
  + explicit human approval
  -> live-readiness record
```

### Milestone 35 — QMT Paper Adapter Foundation

QMT may enter only as an execution adapter after broker-neutral commands and risk boundaries exist.

Preferred architecture:

```text
Browser
  -> Web/API
  -> broker-neutral execution command
  -> Windows QMT agent
  -> MiniQMT
  -> broker
```

Potential venues:

```text
internal_paper
qmt_paper
qmt_live
```

QMT must not leak into strategy, evaluation, governance, persistence, or UI domain models.

Required future concerns include:

- reconnect behavior
- order and fill reconciliation
- internal-to-broker ID mapping
- manual-trade reconciliation
- agent authentication
- command idempotency
- audit trail

Never connect the browser directly to QMT.

## Phase 6 — Controlled Live Pilot & Production Operations

Status: Future and conditional.

This phase begins only after strong paper evidence, portfolio review, execution-risk controls, operational readiness, and explicit human approval exist.

Potential milestones:

- tiny-capital controlled live pilot
- live account and order reconciliation
- operational monitoring and alerts
- incident records and kill switch
- deployment, rollback, and runbooks
- production review processes

Guardrails:

- no unattended scaling
- no autonomous capital allocation
- strict exposure limits
- complete audit trail
- manual kill switch
- staged rollout

## Founder Product Architecture Principles

1. Use existing domain contracts rather than rewriting them in the API layer.
2. Keep the first product local and single-user.
3. Prefer one application service before microservices.
4. Prefer SQLite before a larger database unless real usage proves otherwise.
5. Prefer simple local jobs before distributed queues.
6. Keep existing artifact files authoritative.
7. Keep operational paper-job state separate from strategy lifecycle governance.
8. Keep UI state separate from financial domain truth.
9. Keep broker-specific behavior behind adapters.
10. Treat auditability and human review as product features.
11. Make failure states visible rather than hiding them behind automation.
12. Delay multi-tenancy, complex RBAC, cloud orchestration, and SaaS behavior.

## Core Assets To Preserve

### Research Memory

Every experiment, strategy, parameter set, data assumption, and result should remain traceable.

### Paper Trading Memory

Every paper request, order, fill, account change, session, job, and result should remain inspectable.

### Promotion and Decision Ledger

Every nomination, review, pause, rejection, and lifecycle change should remain explicit, evidence-backed, and human-controlled.

### Report and Lifecycle Memory

Every review package, declared state, proposal, transition record, and manifest should remain tied to stable IDs without implying runtime execution.

### Product Audit Trail

Future application and Web layers should make existing audit records easier to use, not replace them with opaque UI state.

### Execution Readiness

Live trading should be the outcome of trusted research, paper evidence, product operation, portfolio review, risk controls, and operational governance—not the starting point.

## Explicit Non-Priorities

The project should not prioritize these too early:

```text
strategy count for its own sake
real-money trading
live broker integration
browser-to-broker direct connectivity
high-frequency trading
deep-learning alpha
microservice architecture
Kubernetes
Kafka
Redis clusters
distributed queues
multi-tenancy
complex RBAC
large cloud infrastructure
SaaS behavior
real-time dashboard complexity
```

Sprint 145 established one explicitly configured local SQLite file, a
project-owned SQLAlchemy metadata boundary, lazy engine and caller-owned session
factories, and an empty Alembic baseline. No artifact index, product repository,
durable paper job, mutable paper-job state, API database dependency, lifecycle
current-state store, Web UI, broker, QMT, live, or capital behavior was added.
Existing artifact files remain authoritative.

Sprint 146 added one compact, rebuildable artifact index for the existing
research-run and three evidence-manifest layouts. Its repository keeps
transactions caller-owned; explicit refresh discovers all supplied roots before
one atomic replacement transaction; read services query only SQLite. Rows store
no complete payload, absolute root, job state, or lifecycle current state. No
API, automatic refresh, paper job, worker, broker, QMT, live, or capital behavior
was added.

Sprint 147 added a strict canonical durable request codec, immutable paper-job
record, constrained `paper_jobs` table, caller-owned repository, and explicit
submit/get/list services. Submission creates one queued row only after request
validation and serialization. Duplicate run IDs are conflicts. The snapshot is
durable operational input rather than completed artifact authority. No runner,
status transition, retry, recovery, error/result persistence, API endpoint, Web
UI, broker, QMT, live, or capital behavior was added. The existing synchronous
paper-run API remains database-free.

Sprint 148 added one shared request-driven paper workflow, exactly four legal
operational transitions, conditional caller-owned repository updates, one
explicit selected-job runner, and queued-only manual cancellation. The runner
commits a queued-to-running claim before executing and persists files outside
database transactions, then records success or an expected failure separately.
Artifact and result-summary files remain completed-output authority; SQLite
stores no result reference, result payload, or error detail. The migration chain
remains `0001 -> 0002 -> 0003`.

Sprint 148 added no automatic queue scan, worker, poller, scheduler, retry,
recovery, idempotency, error audit, partial-output cleanup, running-job
cancellation, durable-job API, Web UI, broker, QMT, live, or capital behavior.
Interrupted jobs may remain running and partial output may remain after failure.

## Current Next Step

```text
Sprint 149 — Job Recovery, Idempotency, and Error Audit Foundation
```

Sprint 149 should add the smallest explicit recovery, idempotency, and
error-audit foundation while preserving the Sprint 148 single-job runner,
transaction boundaries, artifact authority, and separation from lifecycle
governance.

## One-Line Strategy

```text
Do not rush to find a magic strategy or connect a broker. Build a trusted founder operating system for research, paper trading, and decisions first.
```
