# Milestone 27 — Persistence and Paper Job Control Foundation

## Status

In Progress.

Sprint 145 is complete. Sprint 146 is next.

## Objective

Add the smallest durable local product metadata and manually controlled paper-job
foundation needed by the Founder product while preserving existing domain,
artifact, lifecycle, and human-control authority.

## Architecture Boundary

```text
explicit local SQLite path
  -> SQLAlchemy product metadata and repositories
  -> durable local paper-job records and control
  -> explicit references to authoritative artifact files
```

Milestone 27 remains part of the modular monolith. It does not introduce a Web
UI, distributed queue, broker adapter, QMT, live execution, or capital behavior.

## Sprint Sequence

| Sprint | Status | Deliverable |
|---:|---|---|
| S145 | Complete | SQLite and SQLAlchemy Product Persistence Foundation. |
| S146 | Next | Artifact Index and Product Repository Foundation. |
| S147 | Planned | Durable Paper Job Record and Submission Foundation. |
| S148 | Planned | Simple Local Paper Job Runner and Manual Control. |
| S149 | Planned | Job Recovery, Idempotency, and Error Audit Foundation. |
| S150 | Planned | Durable Job API and Result Reference Integration. |
| S151 | Planned | Milestone 27 Closeout. |

## Sprint 145 Foundation

Sprint 145 provides:

- `EL_PSY_QUANT_PRODUCT_DATABASE_PATH` as the one explicit server-side/local
  product database setting
- one immutable normalized local SQLite file configuration
- one project-owned SQLAlchemy 2.x declarative metadata registry
- lazy engine construction with SQLite foreign-key enforcement
- caller-owned SQLAlchemy session factories and explicit transactions
- one Alembic environment and intentionally empty baseline revision
- upgrade-to-head and downgrade-to-base coverage

Local initialization is explicit. Ensure the parent directory exists, then run:

```powershell
$env:EL_PSY_QUANT_PRODUCT_DATABASE_PATH="C:\path\to\el-psy-quant-product.sqlite3"
uv run alembic upgrade head
```

Configuration resolution, imports, engine construction, and FastAPI application
construction do not create or migrate the database.

## Authority Boundaries

Existing local artifact files remain authoritative for completed research,
paper, comparison, governance, report, and lifecycle outputs. SQLite may later
store indexes, explicit references, jobs, and operational metadata, but it must
not silently copy complete artifact payloads.

Lifecycle current state remains a future derived read model from immutable
snapshots and approved human transition records. It must not become an
independently authoritative mutable field.

Future paper-job state is mutable operational state and remains separate from
lifecycle governance.

## Sprint 145 Non-Goals

Sprint 145 adds no:

- artifact index or product repository
- product business table
- durable paper job, job state, worker, retry, recovery, or idempotency behavior
- new or database-backed API endpoint
- request-scoped database dependency
- Web UI, Docker Compose, authentication, microservice, or distributed system
- broker, QMT, live execution, real-money trading, or capital allocation

## Exit Criteria

Milestone 27 will be complete only after product metadata and paper jobs are
durable and inspectable, local job control has explicit recovery and
idempotency behavior, artifact links preserve file authority, and the complete
quality gate passes without introducing distributed or live-trading behavior.

## Next Sprint

```text
Sprint 146 — Artifact Index and Product Repository Foundation
```
