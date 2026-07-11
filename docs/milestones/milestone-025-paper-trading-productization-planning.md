# Milestone 25 — Paper Trading Productization Planning

## Status

Complete after the Sprint 137 documentation PR is merged.

Milestone 25 is a one-sprint planning milestone completed through Sprint 137.

## Product Goal

Define the product boundary and implementation sequence for a local, founder-only Paper Trading product before adding application, persistence, job-control, or Web UI runtime behavior.

Milestone 25 converts the productization direction approved at the Milestone 24 closeout into an explicit architecture and staged plan for Milestones 26–29.

## Product Target

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

## Founder Journeys

The staged product must support:

- strategy list and strategy detail
- research and backtest result inspection
- governance evidence and report artifact inspection
- starting a paper run
- inspecting paper-run status
- inspecting equity, positions, orders, and fills
- comparing paper runs
- creating a lifecycle transition proposal
- creating a human review record
- viewing a lifecycle timeline

Milestone 28 must deliver the first usable Web MVP containing these journeys.

Milestone 29 must harden the product from real founder usage rather than speculative feature expansion.

## Approved Architecture Direction

```text
Browser
  -> React/Next.js founder workspace
  -> FastAPI application API
  -> thin application services / use cases
  -> existing El-Psy-Quant domain modules and artifact readers
  -> SQLite product repositories and simple local job runner
```

The implementation remains a modular monolith.

Recommended baseline:

- FastAPI
- explicit request and response schemas
- SQLite + SQLAlchemy
- repository boundaries
- simple local background jobs
- React/Next.js
- Docker Compose / local-first deployment
- single-user or minimal authentication

## Ownership Boundaries

### Existing Domain Modules

Existing research, backtesting, paper, promotion, comparison, decision, report, and strategy-review modules remain authoritative for quantitative and governance rules.

The application and UI layers must not duplicate:

- financial calculations
- paper execution semantics
- comparison logic
- governance validation
- lifecycle transition validation
- human-control rules

### Application Service

The application layer may:

- coordinate existing domain calls
- translate product requests into existing domain inputs
- build explicit product read models
- translate domain failures into stable API errors
- authorize local product actions
- connect product records to immutable artifact references

It must remain thin. API route handlers must not become a second domain layer.

### Artifact Ownership

Existing local artifact files remain authoritative for completed research, paper, comparison, governance, and report outputs.

SQLite may store:

- product indexes
- stable references to existing artifacts
- paper job records
- operational status and errors
- idempotency data
- local user or session data when minimal authentication is introduced

SQLite must not silently copy full artifact payloads and become a competing source of truth.

Artifact paths must resolve only under explicitly configured local roots. Arbitrary filesystem access and path traversal must be rejected.

### Lifecycle State Ownership

The product must not introduce an independently authoritative mutable `current_state` field for strategy lifecycle governance.

A current lifecycle view may be derived from explicit immutable state snapshots and approved human transition records.

A transition proposal remains non-executing. A human review record remains governance evidence. Neither may silently mutate lifecycle state.

### Paper Job Ownership

Paper job status is mutable operational state and is separate from strategy lifecycle governance.

M27 may introduce durable job states equivalent to:

```text
queued
running
succeeded
failed
canceled
```

Exact transitions, retries, and cancellation behavior belong in the relevant implementation issues. No distributed execution guarantees may be claimed.

### UI Boundary

The browser must use the Web/API boundary.

The UI must not directly access:

- SQLite
- local artifact directories
- Python domain modules
- QMT
- MiniQMT
- any broker

## Provisional Product Concepts

The product layer may define concepts equivalent to:

- strategy summary and strategy detail
- artifact reference and artifact inspection result
- paper-run submission
- paper job and paper job status
- paper-run result reference
- paper-run comparison view
- lifecycle proposal submission
- human review submission
- lifecycle timeline item

These are planning concepts rather than approved implementation schemas. Exact names and fields belong in the implementation issues.

## API Baseline

Milestone 26 should establish:

- a versioned local API initially under `/api/v1`
- explicit schemas rather than leaked internal Python objects
- stable error responses
- request IDs and job IDs where applicable
- synchronous read operations
- application commands over existing local domain behavior
- no database requirement
- no background worker requirement
- no broker behavior

Long-running paper execution should move behind durable local job control in M27 rather than blocking Web requests indefinitely.

## Persistence and Job-Control Baseline

Milestone 27 should establish:

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

## Security Baseline

- Bind to loopback by default.
- A loopback-only deployment may use a minimal single-user trust model.
- Any non-loopback exposure must require authentication.
- Do not introduce multi-tenancy or complex RBAC.
- Use same-origin defaults and avoid broad CORS.
- Do not expose arbitrary filesystem paths.
- Do not log secrets, credentials, or authentication material.
- Validate all user-supplied identifiers and paths at the application boundary.

The exact minimal authentication mechanism is deferred to an M28 implementation issue.

## Local Deployment Baseline

- One local machine is the supported target through M29.
- FastAPI and Next.js remain separate logical components but do not require distributed infrastructure.
- Docker Compose may provide convenient startup in M28.
- SQLite data and artifact roots must use explicit local volumes or mounts.
- The product must remain operable without Kubernetes, cloud services, or external message brokers.

## Planned Milestone and Sprint Sequence

### Milestone 26 — Paper Trading Application Service Foundation

| Sprint | Goal |
|---:|---|
| S138 | Application Service and API Skeleton |
| S139 | Strategy Catalog and Detail Read Services |
| S140 | Research and Backtest Artifact Inspection Services |
| S141 | Governance, Report, and Lifecycle Evidence Inspection Services |
| S142 | Paper Run Application Command Boundary |
| S143 | Lifecycle Proposal and Human Review Application Commands |
| S144 | Milestone 26 Closeout |

M26 exit criteria:

- a small local FastAPI application boundary exists
- explicit API schemas and stable errors exist
- strategies and existing artifacts are inspectable through application services
- existing paper-run behavior is available through a thin command boundary
- lifecycle proposals and human review records use existing domain contracts
- no product database, background worker, Web UI, broker integration, or live behavior exists

### Milestone 27 — Persistence and Paper Job Control Foundation

| Sprint | Goal |
|---:|---|
| S145 | SQLite and SQLAlchemy Product Persistence Foundation |
| S146 | Artifact Index and Product Repository Foundation |
| S147 | Durable Paper Job Record and Submission Foundation |
| S148 | Simple Local Paper Job Runner and Manual Control |
| S149 | Job Recovery, Idempotency, and Error Audit Foundation |
| S150 | Durable Job API and Result Reference Integration |
| S151 | Milestone 27 Closeout |

M27 exit criteria:

- product metadata is durable in SQLite
- existing artifacts remain authoritative and are linked by explicit references
- paper-run submissions create durable inspectable jobs
- a simple local runner can execute and record jobs
- restart, failure, idempotency, and manual-control behavior are documented and tested
- no distributed infrastructure, broker integration, or Web UI exists

### Milestone 28 — Founder Paper Trading Web Workspace

| Sprint | Goal |
|---:|---|
| S152 | Next.js Workspace Shell and API Client Foundation |
| S153 | Strategy List, Detail, Research, and Backtest Views |
| S154 | Governance Evidence and Report Artifact Views |
| S155 | Paper Run Launch and Status Workspace |
| S156 | Equity, Positions, Orders, and Fills Views |
| S157 | Paper Run Comparison Workspace |
| S158 | Lifecycle Proposal, Human Review, and Timeline Workspace |
| S159 | Minimal Authentication, Docker Compose, and End-to-End MVP Closeout |

M28 exit criteria:

- the Founder can use the first local Web MVP end to end
- all approved founder journeys are available through the UI
- the browser uses the API rather than direct filesystem or database access
- local startup is documented and reproducible
- authentication behavior matches the approved local exposure model
- no broad real-time terminal, broker integration, or live behavior exists

### Milestone 29 — Product Feedback and Hardening

| Sprint | Goal |
|---:|---|
| S160 | Founder Usage Review and Hardening Prioritization |
| S161 | Workflow and Information Architecture Hardening |
| S162 | Reliability, Idempotency, and Job Recovery Hardening |
| S163 | Error Surface, Observability, and Audit Hardening |
| S164 | Migration, Test, and Local Deployment Hardening |
| S165 | Milestone 29 Closeout and M30 Handoff |

M29 exit criteria:

- actual founder usage produces a prioritized feedback record
- high-value workflow friction is reduced
- job recovery and idempotency are reliable for local use
- product errors and audit information are visible and actionable
- API, persistence, and UI boundaries have meaningful test coverage
- local deployment is reliable enough for daily founder use
- speculative features, broker work, and live behavior remain excluded

## Future QMT Boundary

QMT remains a future execution adapter only.

```text
Browser
  -> Web/API
  -> broker-neutral execution command
  -> Windows QMT agent
  -> MiniQMT
  -> broker
```

Future broker-neutral concepts remain:

```text
OrderIntent
ExecutionOrder
ExecutionFill
AccountSnapshot
PositionSnapshot
BrokerOrderReference
```

QMT-specific behavior must not leak into strategy, evaluation, governance, persistence, or UI domain models.

The browser must never connect directly to QMT. No live QMT implementation may begin before separate execution-risk and live-readiness governance is complete.

## Explicitly Deferred

Milestone 25 does not introduce:

- Python production code
- FastAPI dependencies or endpoints
- SQLAlchemy or database models
- background jobs or workers
- React or Next.js code
- Docker Compose files
- authentication implementation
- CLI behavior changes
- artifact migration
- broker or QMT integration
- live execution

Milestones 26–29 do not introduce without a separate roadmap decision:

- microservices
- Kubernetes
- Kafka
- Redis clusters
- distributed queues
- multi-tenancy
- complex RBAC
- cloud SaaS hosting
- broad real-time market dashboards
- streaming market-data infrastructure
- browser-to-QMT communication
- automatic lifecycle transitions
- automatic strategy approval
- automatic capital allocation
- real-money trading

## Exit Criteria Verification

Milestone 25 is complete after the planning PR is merged because:

- the product target and non-goals are explicit
- founder journeys are explicit
- application, domain, artifact, persistence, lifecycle, paper-job, and UI ownership boundaries are explicit
- API, security, and local deployment baselines are explicit
- M26–M29 sprint sequences and milestone exit criteria are explicit
- M28 is the first usable Web MVP
- M29 is driven by real founder usage and reliability hardening
- M30 remains deferred, not canceled
- QMT remains an isolated future adapter
- no runtime implementation was added

## Next Milestone

```text
Milestone 26 — Paper Trading Application Service Foundation
```

The next issue should be Sprint 138 — Application Service and API Skeleton, created only after the Founder merges the Sprint 137 planning PR.
