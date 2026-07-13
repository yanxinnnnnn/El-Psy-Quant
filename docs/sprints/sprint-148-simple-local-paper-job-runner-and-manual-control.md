# Sprint 148 — Simple Local Paper Job Runner and Manual Control

## Status

Complete.

## Objective

Add the smallest explicit local paper-job runner, conditional operational
state transitions, and queued-only manual cancellation on top of the Sprint 147
durable job input without beginning recovery or API integration.

## Delivered Chain

```text
durable queued PaperJobRecord
  -> conditional queued-to-running claim and commit
  -> shared request-driven paper workflow outside database transactions
  -> existing paper artifact and result-summary files
  -> conditional running-to-succeeded completion

expected local workflow failure
  -> conditional running-to-failed completion

manual control
  -> conditional queued-to-canceled transition
```

## Shared Request-Driven Workflow

`run_paper_workflow_request(...)` accepts the exact existing
`PaperRunRequest` and one explicit existing run directory. It reuses the
configured output-path contract, paper execution, artifact persistence, file
payload, audit summary, and result-summary semantics. It creates only the
`paper` directory and writes only:

```text
<run_dir>/paper/paper_run_artifact.json
<run_dir>/paper/paper_run_result_summary.json
```

`run_configured_paper_workflow(...)` converts validated configuration to the
domain request and delegates to this shared boundary while retaining its
existing public result and behavior.

## Operational Transition Contract

The only legal transitions are:

```text
queued  -> running
queued  -> canceled
running -> succeeded
running -> failed
```

`transition_paper_job_record(...)` returns a new immutable record, requires an
application-supplied timezone-aware UTC timestamp that does not move backward,
and preserves every field except status and updated timestamp. Same-state,
queued-to-terminal, running-to-canceled, and all terminal-state transitions are
rejected.

The repository applies one conditional SQL update constrained by job ID and
expected status. Sessions and transactions remain caller-owned; the repository
does not commit, roll back, close, execute workflows, or access files. This
ensures only one explicit claim or cancellation can win for a queued job.

## Explicit One-Job Runner

`run_paper_job_once(...)` executes exactly one caller-selected job once:

1. validate the job ID and existing run directory
2. resolve reserved output paths and reject either existing file without
   claiming or creating the paper directory
3. conditionally claim `queued -> running` in one short committed transaction
4. execute and persist the shared workflow with no open product-database
   transaction or session
5. conditionally record `running -> succeeded` in a new short transaction

Missing jobs are explicit not-found failures. Non-queued jobs and concurrent
losers are state conflicts. A repeated invocation of a succeeded job does not
execute again.

Expected local domain or filesystem failures conditionally record
`running -> failed`, then raise a stable sanitized error chained from the
original exception. No error code, message, traceback, attempt, or retry data is
persisted. Programming and database failures are not broadly swallowed.

If execution stops after claim, the job may remain running. If output writing
fails partway through, partial files remain. Sprint 148 performs no automatic
retry, reset, cleanup, reconciliation, or recovery.

## Manual Cancellation

`cancel_paper_job(...)` applies only `queued -> canceled` in one short
transaction. It does not write or remove files, interrupt execution, persist a
reason, or add a cancellation-request flag. Running, succeeded, failed, and
already-canceled jobs conflict.

## Persistence and Authority

The schema and migration chain remain unchanged:

```text
0001_product_baseline -> 0002_artifact_index -> 0003_paper_jobs
```

Submission still creates queued jobs only. SQLite stores the validated request,
identity, operational status, and timestamps. The paper artifact and result
summary files remain authoritative completed outputs; no result payload or
reference is stored in SQLite.

Paper-job operational state remains separate from lifecycle governance.
Lifecycle current state remains a future derived read model from immutable
snapshots and approved human transition records.

## Preserved Boundaries

Sprint 148 adds no queue scan, claim-next behavior, worker loop, polling, sleep,
thread, process, subprocess, scheduler, background task, startup execution,
automatic migration, retry, recovery, idempotency, exactly-once claim, persisted
error audit, result reference, paper-result indexing, partial-output cleanup,
running-job cancellation, API route or schema, request-scoped database
dependency, Web UI, broker, QMT, live execution, real-money trading, or capital
behavior.

The existing synchronous `POST /api/v1/paper-runs` remains unchanged,
repeatable, in memory, and database-free. FastAPI construction remains
side-effect free.

## Verification

Focused tests cover shared workflow reuse, every legal and illegal transition,
repository transaction ownership and conditional races, output preflight,
successful selected-job execution, expected and unexpected failures, partial
output retention, queued-only cancellation, unchanged migration schema, and API
regressions.

The complete quality gate is:

```text
uv run python scripts/check.py
```

## Next Sprint

```text
Sprint 149 — Job Recovery, Idempotency, and Error Audit Foundation
```
