# Sprint 137 — Milestone 25 Paper Trading Productization Planning

## Status

Complete after this documentation PR is merged.

## Objective

Complete **Milestone 25 — Paper Trading Productization Planning** through documentation only.

This sprint defines the founder product boundary, architecture ownership rules, API and persistence direction, security and deployment baseline, and the implementation sequence for Milestones 26–29.

This is a CTO-owned planning sprint and is not delegated to Codex.

## Pre-Start Verification

Before Sprint 137 was created:

- PR #265 was merged
- Issue #264 was closed as completed
- Milestones 1–24 were complete
- no other open issue existed
- no open pull request existed
- no duplicate M25 or Sprint 137 work existed

## Planning Decision

Milestone 25 is a one-sprint planning milestone.

```text
S137 — Paper Trading Productization Planning
```

After this PR is merged:

```text
M25 — Complete
M26 — Next
```

## Founder Product Target

The first product is a local, founder-only Paper Trading workspace.

It is deliberately:

- local-first
- single-user or minimally authenticated
- Paper Trading only
- review-oriented
- built over existing domain and artifact foundations

It is not a live trading system, SaaS product, multi-tenant platform, broker project, or professional real-time terminal.

## Approved Founder Journeys

- strategy list and strategy detail
- research and backtest result inspection
- governance evidence and report artifact inspection
- start a paper run
- inspect paper-run status
- inspect equity, positions, orders, and fills
- compare paper runs
- create a lifecycle transition proposal
- create a human review record
- view a lifecycle timeline

Milestone 28 must deliver the first usable Web MVP for these journeys.

Milestone 29 must be driven by actual founder usage, workflow friction, and reliability evidence.

## Architecture Decision

```text
Browser
  -> React/Next.js founder workspace
  -> FastAPI application API
  -> thin application services / use cases
  -> existing domain modules and artifact readers
  -> SQLite product repositories and simple local job runner
```

The product remains a modular monolith.

Approved direction:

- FastAPI
- explicit API schemas
- SQLite + SQLAlchemy
- repository boundaries
- simple local background jobs
- React/Next.js
- Docker Compose / local-first deployment
- single-user or minimal authentication

## Critical Ownership Decisions

### Domain Rules

Existing domain modules remain authoritative. API handlers and UI code must not duplicate financial calculations, paper execution, comparison, governance, lifecycle validation, or human-control rules.

### Artifact Truth

Existing local artifact files remain authoritative.

SQLite may index and reference them, but must not silently copy complete artifact payloads and become a second source of truth.

### Lifecycle State

The product must not add an independently authoritative mutable lifecycle `current_state` field.

A current state view may be derived from immutable snapshots and approved transition records. Proposals and human review records remain non-executing governance artifacts.

### Paper Job State

Paper job status is separate operational state. M27 may persist statuses such as `queued`, `running`, `succeeded`, `failed`, and `canceled` with exact semantics defined by implementation issues.

### Browser Boundary

The browser must use the API. It must not directly access SQLite, local artifact directories, Python domain modules, QMT, MiniQMT, or a broker.

## Security and Deployment Decisions

- bind to loopback by default
- require authentication for non-loopback exposure
- keep single-user scope
- avoid multi-tenancy and complex RBAC
- use same-origin defaults
- restrict artifact access to configured roots
- reject path traversal
- do not log secrets
- support one local machine through M29
- use Docker Compose only when the Web MVP is introduced

## Planned Sequence

### M26 — Paper Trading Application Service Foundation

```text
S138 — Application Service and API Skeleton
S139 — Strategy Catalog and Detail Read Services
S140 — Research and Backtest Artifact Inspection Services
S141 — Governance, Report, and Lifecycle Evidence Inspection Services
S142 — Paper Run Application Command Boundary
S143 — Lifecycle Proposal and Human Review Application Commands
S144 — Milestone 26 Closeout
```

### M27 — Persistence and Paper Job Control Foundation

```text
S145 — SQLite and SQLAlchemy Product Persistence Foundation
S146 — Artifact Index and Product Repository Foundation
S147 — Durable Paper Job Record and Submission Foundation
S148 — Simple Local Paper Job Runner and Manual Control
S149 — Job Recovery, Idempotency, and Error Audit Foundation
S150 — Durable Job API and Result Reference Integration
S151 — Milestone 27 Closeout
```

### M28 — Founder Paper Trading Web Workspace

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

### M29 — Product Feedback and Hardening

```text
S160 — Founder Usage Review and Hardening Prioritization
S161 — Workflow and Information Architecture Hardening
S162 — Reliability, Idempotency, and Job Recovery Hardening
S163 — Error Surface, Observability, and Audit Hardening
S164 — Migration, Test, and Local Deployment Hardening
S165 — Milestone 29 Closeout and M30 Handoff
```

## M28 and M29 Outcomes

M28 delivers the first usable local Web MVP.

M29 should leave the Founder with a local Paper Trading Web MVP that has been used in real workflows and hardened for usability, recovery, errors, auditability, tests, migrations, and daily local operation.

Portfolio-level decision review remains deferred to M30 and is not canceled.

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

The browser must never connect directly to QMT. QMT-specific concepts must not leak into strategy, evaluation, governance, persistence, or UI domain models.

No live QMT implementation may begin before dedicated execution-risk and live-readiness governance exists.

## Scope Boundary

Sprint 137 changes documentation only.

It does not add:

- Python runtime code
- FastAPI dependencies or endpoints
- SQLAlchemy or database models
- background workers
- React or Next.js code
- Docker Compose files
- authentication implementation
- CLI changes
- artifact migration
- broker or QMT integration
- live execution

## Files Updated

```text
README.md
AGENTS.md
docs/roadmap.md
docs/strategy/future-platform-roadmap.md
docs/milestones/milestone-025-paper-trading-productization-planning.md
docs/sprints/sprint-137-milestone-25-paper-trading-productization-planning.md
```

## Validation

```text
uv run python scripts/check.py
```

## Next Step

```text
Sprint 138 — Application Service and API Skeleton
```

Sprint 138 is a Codex implementation sprint and must be created only after the Founder decides whether to merge this planning PR.
