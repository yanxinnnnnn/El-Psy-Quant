# Milestone 27 — Persistence and Paper Job Control Foundation

## Status

In Progress.

Sprints 145 and 146 are complete. Sprint 147 is next.

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
| S146 | Complete | Artifact Index and Product Repository Foundation. |
| S147 | Next | Durable Paper Job Record and Submission Foundation. |
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

## Sprint 146 Foundation

Sprint 146 provides:

- one compact immutable index contract for research-run, strategy-decision,
  report-artifact, and strategy-review workflow manifests
- one `artifact_index_entries` table with logical-identity, locator, supported
  type/root, schema-version, and type-to-root constraints
- one focused SQLAlchemy repository whose session and transaction remain
  caller-owned
- root-isolated replacement, stale cleanup, deterministic exact/filter reads,
  empty-root clearing, and idempotent refresh behavior
- explicit refresh using only `list_research_runs(...)` and
  `list_evidence_manifests(...)`, with discovery before one multi-root database
  transaction
- repository-backed reads that do not reopen authoritative files

The migration chain is exactly:

```text
0001_product_baseline -> 0002_artifact_index
```

Index rows contain only schema version, artifact type, artifact key, root type,
POSIX relative path, and normalized source ID. They contain no complete payload,
absolute root, job state, lifecycle state, order, fill, or authentication data.

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

## Sprint 145–146 Non-Goals

Through Sprint 146, Milestone 27 adds no:

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
Sprint 147 — Durable Paper Job Record and Submission Foundation
```
