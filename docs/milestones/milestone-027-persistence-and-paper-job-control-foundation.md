# Milestone 27 — Persistence and Paper Job Control Foundation

## Status

Complete.

Sprints 145 through 151 are complete.

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
| S147 | Complete | Durable Paper Job Record and Submission Foundation. |
| S148 | Complete | Simple Local Paper Job Runner and Manual Control. |
| S149 | Complete | Job Recovery, Idempotency, and Error Audit Foundation. |
| S150 | Complete | Durable Job API and Result Reference Integration. |
| S151 | Complete | Milestone 27 Closeout. |

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

## Sprint 147 Foundation

Sprint 147 provides:

- one validation-only `PaperRunCommand -> PaperRunRequest` boundary reused by
  synchronous execution and durable submission
- one strict deterministic request snapshot codec that reconstructs existing
  domain objects and preserves order/fill sequence
- one immutable paper-job record with canonical UUID, unique normalized run ID,
  approved status vocabulary, validated request, and UTC timestamps
- one `paper_jobs` table containing only the approved operational-input columns
- one focused caller-owned repository with add/get/get-by-run/list behavior
- one explicit application submission transaction that creates only queued rows
- explicit duplicate-run conflict and not-found application errors

The migration chain is exactly:

```text
0001_product_baseline -> 0002_artifact_index -> 0003_paper_jobs
```

The request snapshot is durable operational input for a future runner, not a
completed artifact payload. Artifact files remain completed-output authority.
Sprint 147 itself added no job runner, status transition, retry, recovery,
idempotency key, error/result column, result reference, worker, scheduler, or
API integration.

## Sprint 148 Foundation

Sprint 148 provides:

- one shared request-driven paper workflow reused by configured execution
- one immutable centralized transition contract with exactly:
  `queued -> running`, `queued -> canceled`, `running -> succeeded`, and
  `running -> failed`
- one conditional repository transition constrained by job ID and expected
  status under caller-owned transactions
- output preflight that rejects existing reserved files before claim
- one explicit runner that claims one caller-selected queued job once, commits
  before execution, and finalizes in a separate transaction
- workflow execution and authoritative file persistence outside any product
  database transaction or long-lived session
- expected local execution or persistence failure recording as `failed` without
  persisted error details
- queued-only manual cancellation

The migration chain remains exactly:

```text
0001_product_baseline -> 0002_artifact_index -> 0003_paper_jobs
```

Successful completed outputs remain the existing paper artifact and result
summary files. SQLite stores no result payload or reference. The explicit
runner does not scan, loop, poll, retry, recover, or start automatically.
Interrupted jobs may remain `running`, and partial output may remain after a
failure until an explicit Sprint 149 recovery or retry command is applied.

## Authority Boundaries

Existing local artifact files remain authoritative for completed research,
paper, comparison, governance, report, and lifecycle outputs. SQLite stores
indexes, explicit references, jobs, and operational metadata, but it does not
silently copy complete artifact payloads.

Lifecycle current state remains a future derived read model from immutable
snapshots and approved human transition records. It is not an independently
authoritative mutable field.

Paper-job status is mutable operational state and remains separate from
lifecycle governance. Submission creates the initial queued state, while later
transitions, recovery, retry, and cancellation remain explicit operational
commands.

## Sprint 149 Foundation

Sprint 149 provides:

- migration `0004_paper_job_recovery_audit` with exactly
  `paper_job_submission_keys` and `paper_job_attempts`
- optional caller keys bound to the exact canonical request SHA-256 digest,
  with exact replay and explicit mismatched-replay conflict
- compact immutable numbered attempts and approved sanitized error codes
- atomic job/attempt claim and completion under caller-owned transactions
- a strict result-summary reader and cross-file consistency validator
- explicit manual recovery, including legacy running jobs without attempts
- explicit failed-job retry after clean-output preflight

Output files remain authoritative. Keyed submission is replay-safe durable
creation, not exactly-once execution. Recovery and retry are manual and never
rewrite or delete output files.

## Sprint 150 Foundation

Sprint 150 provides:

- migration `0005_paper_job_result_references` with exactly one compact
  job-owned result-reference table
- atomic succeeded job, succeeded attempt, and result-reference creation for
  API-owned normal execution and valid-output recovery
- `EL_PSY_QUANT_PAPER_ARTIFACT_ROOT` and the fixed server-owned
  `jobs/<job-id>/paper/` output layout
- durable `/api/v1/paper-jobs` submission, bounded list/detail, attempt, run,
  cancel, retry, recover, and result routes
- one selected-job FastAPI post-response task with the Sprint 149 conditional
  claim and attempt audit remaining authoritative
- strict authoritative artifact and result-summary reads after the database
  session is closed, with no filesystem locator in the returned view
- a read-only request-time schema preflight that rejects missing, empty,
  unavailable, or pre-0005 product databases before any durable mutation

The database migration remains an explicit operator action:

```powershell
$env:EL_PSY_QUANT_PRODUCT_DATABASE_PATH="C:\path\to\product.sqlite3"
$env:EL_PSY_QUANT_PAPER_ARTIFACT_ROOT="C:\path\to\paper-artifacts"
uv run alembic upgrade head
```

Submission creates or replays only a queued job. `/run` handles one selected
job after the response and is not a worker or queue scanner. Result references
are compact pointers; the two files remain completed-output authority. The
existing synchronous `POST /api/v1/paper-runs` remains unchanged and
database-free.

## Exit Criteria Verification

Milestone 27 exit criteria are satisfied because:

- product metadata and paper jobs are durable and inspectable
- the migration chain is explicit through `0005_paper_job_result_references`
- artifact-index rows and result references remain compact metadata
- exact request snapshots remain durable operational input rather than completed
  result payloads
- duplicate-run conflicts and digest-bound idempotent replay are explicit
- claims, attempts, and terminal job updates use bounded atomic transactions
- workflow execution and authoritative file access occur outside long-lived
  database sessions
- interrupted-job recovery and failed-job retry are explicit manual controls
- API-owned success and valid-output recovery atomically create one compact
  result reference
- result reads reopen and strictly validate authoritative files
- HTTP requests neither accept nor expose arbitrary filesystem paths
- pre-0005 databases are rejected before durable writes begin
- the complete quality gate passed for each implementation sprint
- no distributed or live-trading behavior was introduced

## Preserved Guardrails

Milestone 27 did not add:

- automatic job scanning, worker loops, polling, scheduling, persistent workers,
  or startup execution
- automatic retry/recovery or an exactly-once execution claim
- raw persisted exception messages, tracebacks, or completed result payloads
- partial-output cleanup, deletion, relocation, or rewriting
- running-job cancellation, pause, or resume
- request-scoped SQLAlchemy `Session` ownership in route handlers
- a Web UI, Docker Compose, authentication, users, or tenants
- microservices or distributed infrastructure
- broker, QMT, live execution, real-money trading, or capital allocation

## Closeout Decision

Milestone 27 is complete.

The platform now has the durable local persistence and manually controlled
paper-job foundation needed by the Founder product. The next justified layer is
the first local Founder Web workspace over the existing versioned API. That UI
must consume the API rather than directly accessing SQLite, artifact files, or
Python domain modules.

## Next Milestone

```text
Milestone 28 — Founder Paper Trading Web Workspace
```

## Next Sprint

```text
Sprint 152 — Next.js Workspace Shell and API Client Foundation
```

Sprint 152 should establish only the smallest local Next.js workspace shell and
typed API-client foundation. It must not duplicate domain logic, bypass the API,
or introduce broker, QMT, live, capital, multi-tenant, or distributed behavior.
