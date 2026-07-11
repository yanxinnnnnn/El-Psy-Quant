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

Completed chain:

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

Status: Next.

The platform now has enough domain depth. The next company-level objective is to make existing capabilities usable by the founder through a coherent local product.

This phase is deliberately single-user and local-first. It is not a SaaS phase.

### Milestone 25 — Paper Trading Productization Planning

Status: Next.

Purpose:

Define the product boundary and implementation sequence before building the application layer.

M25 should decide:

- primary founder journeys
- application-service responsibilities
- domain-to-API boundaries
- product persistence ownership
- local job-control semantics
- UI information architecture
- security and authentication baseline
- local deployment model
- observability and error-surface expectations
- M26-M29 sprint sequence and exit criteria

M25 is planning-only. It must not implement FastAPI endpoints, database models, job workers, or web screens.

### Milestone 26 — Paper Trading Application Service Foundation

Status: Planned.

Purpose:

Expose existing research, paper, comparison, decision, report, and lifecycle capabilities through a small local application-service boundary.

Recommended direction:

- FastAPI
- explicit request/response schemas
- thin application services over existing domain contracts
- no broker integration
- no domain logic duplicated in API handlers

Initial API capabilities may include:

- list and inspect strategies
- inspect research/backtest artifacts
- inspect governance and report artifacts
- submit a local paper-run request
- inspect paper-run results
- create lifecycle proposals and human review records

### Milestone 27 — Persistence and Paper Job Control Foundation

Status: Planned.

Purpose:

Add product-level durability and controllable local execution without turning the system into distributed infrastructure.

Recommended direction:

- SQLite
- SQLAlchemy
- explicit repository boundaries
- simple local background jobs
- manually controllable job lifecycle
- durable job status and errors
- deterministic links to existing domain artifacts

Do not introduce Kafka, distributed queues, Redis clusters, Kubernetes, or multi-service orchestration.

### Milestone 28 — Founder Paper Trading Web Workspace

Status: Planned.

Purpose:

Deliver the first usable founder product.

The workspace should support:

- strategy list and strategy detail
- research and backtest inspection
- governance evidence and report-artifact inspection
- start paper run
- paper-run status
- equity, positions, orders, and fills
- compare paper runs
- lifecycle transition proposal
- human review record
- lifecycle timeline

Recommended direction:

- React/Next.js
- clean founder-focused information architecture
- Web/API separation
- local-first operation
- Docker Compose for convenient local startup
- single-user or minimal authentication

Do not build a broad real-time trading dashboard. Focus on reviewability and operation of existing paper workflows.

### Milestone 29 — Product Feedback and Hardening

Status: Planned.

Purpose:

Use the founder workspace in real workflows and fix the highest-value usability, reliability, audit, and operational issues.

Expected focus:

- workflow friction
- missing product state
- error handling
- idempotency
- job recovery
- audit visibility
- migration discipline
- test coverage across API, persistence, and UI boundaries
- local deployment reliability

This milestone should be driven by actual founder usage rather than speculative features.

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

QMT must not leak into strategy, evaluation, governance, or UI domain models.

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
6. Keep UI state separate from financial domain truth.
7. Keep broker-specific behavior behind adapters.
8. Treat auditability and human review as product features.
9. Make failure states visible rather than hiding them behind automation.
10. Delay multi-tenancy, complex RBAC, cloud orchestration, and SaaS behavior.

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

Future application and web layers should make existing audit records easier to use, not replace them with opaque UI state.

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
multi-tenancy
complex RBAC
large cloud infrastructure
SaaS behavior
real-time dashboard complexity
```

## Current Next Step

```text
Milestone 25 — Paper Trading Productization Planning
```

M25 should turn the productization direction into an explicit, reviewable architecture and sprint plan while preserving the local-first, human-controlled, non-live boundaries established by Milestones 1–24.

## One-Line Strategy

```text
Do not rush to find a magic strategy or connect a broker. Build a trusted founder operating system for research, paper trading, and decisions first.
```
