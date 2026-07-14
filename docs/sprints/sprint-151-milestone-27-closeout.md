# Sprint 151 — Milestone 27 Closeout

## Status

Complete.

## Objective

Close **Milestone 27 — Persistence and Paper Job Control Foundation** after
Sprints 145–150 delivered the planned local persistence, artifact index,
durable paper-job controls, recovery, idempotency, result references, and
versioned durable-job API.

This sprint changes documentation only and hands the roadmap to:

```text
Sprint 152 — Next.js Workspace Shell and API Client Foundation
```

## Completed Chain

```text
S145 persistence foundation
  -> S146 compact artifact index
  -> S147 durable job submission
  -> S148 selected-job runner and cancellation
  -> S149 idempotency, attempt audit, recovery, and retry
  -> S150 durable job API and result references
  -> S151 closeout
```

## Closeout Verification

Milestone 27 is complete because:

- the explicit Alembic chain ends at `0005_paper_job_result_references`
- imports and `create_app()` do not create or migrate the product database
- artifact-index rows, attempts, submission keys, and result references remain
  bounded product metadata rather than completed-output payloads
- existing artifact files remain authoritative for completed outputs
- paper-run request snapshots and job operational state are durable
- duplicate-run conflicts and digest-bound idempotent replay are explicit
- job claims and attempt creation are atomic
- workflow execution occurs outside database transactions
- job/attempt completion is atomic, and API-owned success atomically adds one
  compact result reference
- only approved sanitized attempt error codes are persisted
- interrupted-job recovery and failed-job retry remain explicit manual controls
- result reads reopen and strictly validate authoritative files after database
  sessions close
- durable API requests neither accept nor expose arbitrary filesystem paths
- missing, unavailable, empty, or pre-0005 databases are rejected before
  durable mutation
- the synchronous `POST /api/v1/paper-runs` endpoint remains database-independent
- `/run` schedules one selected post-response callback without scanning,
  polling, a persistent worker, scheduler, or distributed queue

## Authority Boundaries

SQLite stores product indexes, exact job input snapshots, operational job state,
idempotency metadata, compact attempt audit, and compact result references. It
does not silently copy complete research, paper, governance, comparison, report,
or lifecycle artifacts.

Paper-job status remains mutable operational state separate from strategy
lifecycle governance. Lifecycle current state remains a future derived read
model from immutable snapshots and approved human transition records, not an
independently authoritative mutable field.

The future browser must consume the versioned API and must not directly access
SQLite, local artifact directories, Python domain modules, QMT, MiniQMT, or a
broker.

## Preserved Guardrails

Milestone 27 added no automatic scanning, claim-next loop, persistent worker,
automatic retry or recovery, exactly-once guarantee, output cleanup or rewrite,
request-scoped SQLAlchemy session ownership, Web UI, authentication, Docker
Compose, microservices, broker, QMT, live execution, real-money trading, or
capital allocation.

## Closeout Decision

Milestone 27 is complete. The platform now has the stable local persistence and
manually controlled durable paper-job foundation needed beneath the first
Founder-facing Web workspace.

## Next Milestone

```text
Milestone 28 — Founder Paper Trading Web Workspace
```

## Next Sprint

```text
Sprint 152 — Next.js Workspace Shell and API Client Foundation
```

Sprint 152 must remain API-first and local-first. It should add only the
workspace shell, navigation, configuration, and typed client foundation needed
for later Founder views, without duplicating backend domain behavior.
