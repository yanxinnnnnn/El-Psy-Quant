# Sprint 150 — Durable Job API and Result Reference Integration

## Status

Complete.

## Objective

Expose the existing durable paper-job services through the smallest safe local
`/api/v1` boundary and add compact deterministic references from API-owned
succeeded jobs to authoritative paper output files.

## Delivered Chain

```text
explicit HTTP submission
  -> existing paper command validation
  -> replay-safe durable queued job

explicit selected-job /run
  -> one FastAPI post-response task
  -> existing conditional claim and attempt audit
  -> authoritative files under one server-owned root
  -> atomic succeeded job + attempt + compact reference

result read
  -> database reference read and closed session
  -> safe contained file resolution
  -> strict artifact, summary, and cross-file validation
  -> explicit path-free response
```

## Migration and Result Reference

Migration head `0005_paper_job_result_references` follows the unchanged Sprint
149 revision and creates exactly one table: `paper_job_result_references`.
Each immutable row stores only fixed record/root/artifact/result-summary schema
versions, one job ID, two normalized relative POSIX paths, and an
application-owned UTC timestamp.

The exact API-owned paths are:

```text
jobs/<job-id>/paper/paper_run_artifact.json
jobs/<job-id>/paper/paper_run_result_summary.json
```

The table has a restrictive foreign key to `paper_jobs`, unique artifact and
summary paths, fixed-version constraints, and no result payload. It is separate
from `artifact_index_entries` and performs no historical backfill.

## Atomic Execution and Recovery

The public manual `run_paper_job_once(...)` and
`recover_interrupted_paper_job(...)` remain backward compatible for
operator-owned directories and may succeed without a product result reference.
Focused product-root wrappers derive the server-owned job directory and add a
reference only for API-owned success.

After both files are written outside every database session, one short success
transaction applies:

```text
running job -> succeeded
running attempt -> succeeded
insert result reference
```

One UTC timestamp owns all three records. Reference validation or insertion
failure rolls the terminal database changes back while preserving the files and
leaving the job and attempt running for explicit recovery. Valid-output recovery
uses the same atomic boundary. Expected workflow/filesystem failure retains the
Sprint 149 failed status and sanitized error-code behavior with no reference.

## Configuration and Layout

The database and paper root are explicit server-side settings:

```powershell
$env:EL_PSY_QUANT_PRODUCT_DATABASE_PATH="C:\path\to\product.sqlite3"
$env:EL_PSY_QUANT_PAPER_ARTIFACT_ROOT="C:\path\to\paper-artifacts"
uv run alembic upgrade head
```

Migration is always an operator action. Application import and construction do
not create, connect, migrate, schedule, or execute anything. A durable database
request refuses a missing file rather than allowing SQLite to create an empty
one. Execution, retry, recovery, and result routes also require an existing
paper root directory.

API-owned output uses exactly:

```text
<paper-root>/jobs/<job-id>/paper/paper_run_artifact.json
<paper-root>/jobs/<job-id>/paper/paper_run_result_summary.json
```

HTTP requests never accept a root, run directory, or file path. Root-relative
resolution validates containment and rejects escaping symlinks. Existing output
files are never overwritten, truncated, relocated, deleted, or cleaned.

## Durable API

Sprint 150 adds:

```text
POST /api/v1/paper-jobs
GET  /api/v1/paper-jobs
GET  /api/v1/paper-jobs/{job_id}
GET  /api/v1/paper-jobs/{job_id}/attempts
POST /api/v1/paper-jobs/{job_id}/run
POST /api/v1/paper-jobs/{job_id}/cancel
POST /api/v1/paper-jobs/{job_id}/retry
POST /api/v1/paper-jobs/{job_id}/recover
GET  /api/v1/paper-jobs/{job_id}/result
```

Submission accepts an optional exact `Idempotency-Key`, creates no directory,
and never executes automatically. Exact replay returns the original current job
representation. Lists are deterministic, status-filtered, and bounded to at
most 200 rows. Detail and attempt reads access SQLite only.

`/run` validates one selected queued job and schedules exactly one FastAPI
post-response callback. The callback invokes only the existing selected-job
runner through the product-root wrapper. Conditional claim remains the
concurrency authority, so duplicate callbacks create at most one attempt and
one result reference. This hook is not a durable worker guarantee, queue scan,
worker loop, poller, scheduler, or distributed queue.

Cancel remains queued-only. Retry remains failed-to-queued after clean-output
preflight and does not execute. Recovery accepts only a timezone-aware UTC
`stale_before` value and preserves Sprint 149 outcomes and optimistic guards.

## Result Reads and Errors

Result reads first load job and compact reference metadata, close the database
session, then strictly reopen and validate both authoritative files and their
cross-file/request consistency. Responses include the paper artifact, compact
audit summary, and reference metadata without either stored path. They expose no
database row, canonical request JSON, file bytes, local root, drive, traceback,
broker, lifecycle, user, or capital data.

Stable request-ID error envelopes distinguish invalid input, missing jobs,
identity/idempotency/state/output conflicts, unavailable or invalid results,
database unavailability, paper-root unavailability, and recovery uncertainty.
SQL, filesystem details, paths, idempotency keys, exception text, and
tracebacks remain private.

## Preserved Boundaries

`POST /api/v1/paper-runs` remains synchronous, in memory, repeatable, and
independent of database and paper-root configuration. Completed artifact and
result-summary files remain authoritative; SQLite stores no completed payload.
Paper-job operational state remains separate from lifecycle governance.

Sprint 150 adds no automatic scan, startup execution, persistent worker,
polling, scheduler, distributed queue, automatic retry/recovery, cleanup,
Web UI, authentication, users, tenants, CORS expansion, Docker Compose, broker,
QMT, MiniQMT, live execution, real-money trading, or capital behavior.

## Verification

Tests cover the exact migration chain and constraints, immutable path contract,
caller-owned repository transactions, atomic execution/recovery registration,
rollback with preserved files, manual compatibility, safe result reading,
configuration side effects, every endpoint, idempotency, bounded reads,
concurrent claim authority, path rejection, sanitized errors, OpenAPI schemas,
and the unchanged synchronous route.

The complete quality gate is:

```text
uv run python scripts/check.py
```

## Next Sprint

```text
Sprint 151 — Milestone 27 Closeout
```

Sprint 150 does not begin the closeout.
