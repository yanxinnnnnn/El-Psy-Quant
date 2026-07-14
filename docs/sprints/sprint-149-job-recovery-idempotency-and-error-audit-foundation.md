# Sprint 149 — Job Recovery, Idempotency, and Error Audit Foundation

## Status

Complete.

## Objective

Add the smallest explicit submission-idempotency, execution-attempt audit,
interrupted-job recovery, and failed-job retry foundation without adding API or
automatic processing behavior.

## Delivered Chain

```text
validated submission + optional caller key
  -> exact canonical request SHA-256 digest
  -> atomic queued job and optional key mapping
  -> exact replay returns the original job

explicit selected-job claim
  -> atomic running job and numbered attempt
  -> workflow outside database transactions
  -> atomic job and attempt completion

explicit operator recovery or retry
  -> inspect/preflight caller-supplied run directory
  -> deterministic manual state reconciliation
```

## Migration and Compact Audit

The migration chain is:

```text
0001_product_baseline
  -> 0002_artifact_index
  -> 0003_paper_jobs
  -> 0004_paper_job_recovery_audit
```

Revision `0004` creates only `paper_job_submission_keys` and
`paper_job_attempts`. It does not alter existing tables. Submission mappings
store no request copy; attempts store no exception message, traceback, request,
path, result, worker, lease, or lifecycle state.

## Submission Idempotency

Optional caller keys use exact validation and map to the lowercase SHA-256
digest of the already prepared canonical UTF-8 request payload. Same-key,
same-request replay returns the original job in any status. Changed-request
replay conflicts. A different key does not weaken unique run-ID conflicts.

This makes durable creation replay-safe. It does not claim exactly-once workflow
execution.

## Attempts and Sanitized Errors

Every new successful claim creates one numbered running attempt in the same
transaction as `queued -> running`. Success and expected failure complete the
job and active attempt atomically in a separate short transaction. Expected
workflow and filesystem failures persist only approved sanitized codes;
original exception detail remains only in the application exception chain.
Programming and database-finalization failures may leave both records running
for explicit recovery.

## Manual Recovery and Retry

Recovery requires an operator-supplied original run directory and stale
threshold. File inspection occurs outside database sessions. Neither output
requeues with an interrupted audit; two valid consistent outputs succeed; one
output fails as partial; invalid or inconsistent outputs fail as invalid.
Permission or read uncertainty leaves state running. Finalization uses the exact
observed job timestamp and supports legacy Sprint 148 running jobs by creating
one synthetic attempt only during recovery.

Retry applies only to failed jobs after clean-output preflight. It requeues
without execution or a new attempt; a later explicit run creates the next
attempt number. Recovery and retry never remove, rewrite, relocate, or clean up
outputs.

## Preserved Boundaries

Output files remain completed-output authority. The existing synchronous paper
API remains database-free and unchanged. Sprint 149 adds no result reference,
artifact-index type, durable-job API, request-scoped database dependency, queue
scan, worker, polling, scheduler, background task, automatic recovery/retry,
cleanup, lease, heartbeat, lifecycle mutation, Web UI, broker, QMT, live
execution, or capital behavior.

## Verification

Tests cover the exact migration, keyed replay and concurrency, immutable attempt
contracts, atomic rollback, sanitized failure classification, strict summary
validation, every recovery outcome, optimistic recovery races, legacy running
jobs, retry and next-attempt behavior, API/configured-runner regressions, and
import/startup side effects.

The complete quality gate is:

```text
uv run python scripts/check.py
```

## Next Sprint

```text
Sprint 150 — Durable Job API and Result Reference Integration
```
