# Sprint 147 — Durable Paper Job Record and Submission Foundation

## Status

Complete.

## Objective

Add the smallest durable local paper-job input and submission boundary needed
by a future local runner, without executing jobs or changing the existing
synchronous API.

## Delivered Chain

```text
PaperRunCommand
  -> shared validation-only PaperRunRequest normalization
  -> strict canonical request snapshot
  -> immutable queued PaperJobRecord
  -> caller-owned SQLAlchemy transaction
  -> paper_jobs row
  -> typed database-only reads
```

## Shared Validation Boundary

`create_paper_run_request_from_command(...)` requires the exact existing
command and nested command-input types. It reconstructs account states, orders,
fills, and the domain request through existing public paper factories. Invalid
input retains the sanitized `PaperRunInvalidError` behavior. The function does
not execute, persist, or perform filesystem access.

`execute_paper_run(...)` now reuses this validation function before calling
`run_paper_trading_request(...)`; its synchronous in-memory results and HTTP
behavior remain unchanged.

## Durable Request Snapshot

`serialize_paper_run_request(...)` accepts only a validated domain
`PaperRunRequest` and emits deterministic canonical JSON from its existing
`to_dict()` semantics. `deserialize_paper_run_request(...)` requires schema
version `1`, exact top-level and nested shapes, finite valid domain values, and
reconstructs the existing account, order, fill, and request objects. It
preserves request normalization plus caller order and fill sequence.

The codec rejects malformed JSON, duplicate keys, missing or unexpected fields,
unsupported schemas, booleans in numeric fields, NaN, Infinity, and invalid
nested values. It performs no execution or file I/O.

## Durable Paper Job Contract

`PaperJobRecord` is frozen and contains exactly:

```text
record_schema_version
job_id
run_id
status
request
submitted_timestamp
updated_timestamp
```

Job IDs are canonical UUID strings. Run IDs match the normalized request and
are unique in durable storage. Timestamps are timezone-aware UTC and the update
timestamp cannot precede submission. The full approved status vocabulary is
`queued`, `running`, `succeeded`, `failed`, and `canceled`, but Sprint 147
creates only queued records. The queued factory sets both timestamps equal.

The record contains no result, result reference, error, retry, attempt,
idempotency key, worker, lease, lifecycle, broker, approval, or capital state.

## Migration and Repository

The explicit migration chain is:

```text
0001_product_baseline -> 0002_artifact_index -> 0003_paper_jobs
```

Revision `0003_paper_jobs` creates only `paper_jobs` with the eight approved
non-null columns, primary job ID, unique run ID, fixed record/request schema
versions, and approved-status check. It leaves `artifact_index_entries`
unchanged; downgrade removes only `paper_jobs`.

`SqlAlchemyPaperJobRepository` receives one caller-owned session and never
commits, rolls back, or closes it. Additions accept only queued records plus a
codec-created immutable prepared request that binds the exact job request to its
hidden canonical payload. Raw payload strings are not a repository trust
boundary. Additions return typed immutable records and flush to surface
constraints. Reads rehydrate through the strict codec and support exact job/run
lookup plus deterministic status-filtered lists. It has no update or transition
method and does not execute or access files.

## Submission and Read Services

`submit_paper_job(...)` validates the complete request and creates its immutable
codec-prepared persistence input before opening the database transaction. It
then generates an application-owned UUID4 and UTC timestamp, creates one queued
record, and adds it in one transaction.
Invalid input creates no row. Duplicate job or run identity raises a sanitized
conflict; a duplicate run is not treated as idempotent success. Other database
failures roll back and are not retried.

`get_paper_job(...)`, `get_paper_job_by_run_id(...)`, and
`list_paper_jobs(...)` return typed records from SQLite. They do not execute,
read artifacts, or expose raw storage JSON.

## Explicit Migration

The database parent directory must already exist:

```powershell
$env:EL_PSY_QUANT_PRODUCT_DATABASE_PATH="C:\path\to\product.sqlite3"
uv run alembic upgrade head
```

Migration remains an explicit operator action. Imports, FastAPI startup,
submission, and repository construction do not migrate automatically.

## Preserved Boundaries

`POST /api/v1/paper-runs` remains synchronous, in memory, repeatable for the
same caller run ID, and usable without database configuration. Sprint 147 adds
no durable-job HTTP route, request-scoped database dependency, runner, status
transition, cancellation, polling, claim, lock, lease, heartbeat, thread,
process, subprocess, queue, scheduler, retry, recovery, idempotency design,
error audit, result payload/reference, paper-result indexing, authentication,
Web UI, Docker Compose, broker, QMT, market-data stream, live execution, or
capital behavior.

Artifact files remain authoritative for completed outputs. Paper-job state is
operational state separate from lifecycle governance; lifecycle current state
remains a future derived read model.

## Verification

Focused tests cover shared validation, strict codec behavior, immutable product
constraints, exact migration chain/schema, repository transaction ownership,
durability across a reopened engine, duplicate identities, atomic submission,
database-only reads, unchanged API behavior, and import/startup side effects.

The complete quality gate is:

```text
uv run python scripts/check.py
```

## Next Sprint

```text
Sprint 148 — Simple Local Paper Job Runner and Manual Control
```
