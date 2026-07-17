# Sprint 165 — Reliability, Idempotency, and Job Recovery Hardening

## Status

Implementation complete. Founder Standard/Demo reliability acceptance remains.

## Objective

Make the existing durable Paper Job workflow deterministic and understandable
under submission replay, duplicate commands, state races, execution failure,
interruption, Retry, Recover, and output/reference collision without adding
automatic processing or new quantitative capability.

## Preserved State Machine

Durable statuses remain exactly:

```text
queued
running
succeeded
failed
canceled
```

Approved transitions remain exactly:

```text
queued  -> running    explicit Run claim
queued  -> canceled   explicit Cancel
running -> succeeded  valid execution or valid-output recovery
running -> failed     expected execution failure or invalid/partial recovery
running -> queued     no-output interrupted recovery
failed  -> queued     explicit clean-output Retry
```

Attempts remain immutable numbered records with `running`, `succeeded`,
`failed`, or `interrupted` status and only the approved sanitized error codes.

## One Founder Action Matrix

The Web owns one bounded presentation policy:

| Durable status | Founder-visible mutation choices |
| --- | --- |
| `queued` | Run, Cancel |
| `running` | Recover |
| `failed` | Retry |
| `succeeded` | none |
| `canceled` | none |

Unknown future values show their raw value and no mutation. This matrix never
authorizes a transition; every backend command revalidates current durable
state atomically.

## Submission Outcome

`POST /api/v1/paper-jobs` continues to return HTTP 200 and now returns:

```text
PaperJobSubmissionResponse
  submission_outcome: created | replayed
  job: PaperJobResponse
```

`created` means the new queued job and optional key mapping committed in one
transaction. A successful no-key submission always reports `created`.

`replayed` means the exact original current job was returned for the same exact
key and canonical request. The returned job may now be in any durable status.
Replay creates no job, mapping, attempt, command, callback, output, or result
reference. The key and canonical digest are never echoed.

The existing `submit_paper_job(...)` caller remains compatible and returns only
the job. The outcome-aware `submit_paper_job_with_outcome(...)` boundary owns
the API result.

## Synchronous Run Claim Before HTTP 202

Run now performs:

```text
validate exact job and configured root
  -> reject either pre-existing reserved output
  -> reject an existing compact result reference
  -> atomically queued -> running
  -> atomically create one numbered running attempt
  -> return HTTP 202 with running job and latest attempt
  -> execute that existing claim in one post-response task
```

The background task cannot claim or create another attempt. It validates that
the exact claimed attempt remains the one active running attempt, executes the
workflow outside database transactions, and uses the existing atomic terminal
job/attempt/reference boundary.

The callback is still a non-durable FastAPI post-response task. It is not a
worker, queue, lease, heartbeat, scheduler, or exactly-once guarantee. A process
exit after claim leaves the job and attempt `running` for explicit Recover.

The public operator `run_paper_job_once(...)` remains backward compatible.

## Retry and Recover

Retry remains:

```text
failed -> queued
```

It requires clean reserved output paths and no compact result reference. It
creates no attempt, executes nothing, schedules nothing, removes nothing, and
preserves every prior attempt. A later explicit Run creates the next attempt
number. Concurrent Retry requests have one winner.

Recover requires an exact timezone-aware UTC `stale_before` value. The job must
still be `running`, and its exact observed `updated_timestamp` must be less than
or equal to the threshold. The Web shows that raw timestamp next to the field,
rejects invalid or earlier input before sending, and describes the value as the
Founder assertion that the observed execution is no longer active. Backend
validation and optimistic transition remain authoritative.

`POST /api/v1/paper-jobs/{job_id}/recover` now returns:

```text
PaperJobRecoveryResponse
  recovery_outcome: requeued | succeeded | failed
  job: PaperJobResponse
```

The outcomes remain:

| Inspection | Outcome | Job/attempt result |
| --- | --- | --- |
| no artifact and no summary | `requeued` | queued / interrupted / `interrupted_without_output` |
| two valid consistent outputs | `succeeded` | succeeded / succeeded / compact reference inserted |
| exactly one output | `failed` | failed / failed / `partial_output_detected` |
| two invalid or inconsistent outputs | `failed` | failed / failed / `invalid_output_detected` |
| unreadable or uncertain inspection | API failure | job and attempt remain running |

One active running attempt is required. A legacy running job with no attempt may
receive one synthetic attempt only during valid recovery. A terminal-only
attempt set or multiple active attempts fails closed. Finalization uses the
exact observed job timestamp, so concurrent Recover and normal completion have
one terminal winner.

## Collision and Rollback Authority

The product-owned paths remain:

```text
jobs/<job-id>/paper/paper_run_artifact.json
jobs/<job-id>/paper/paper_run_result_summary.json
```

Before Run, either existing file or a compact result reference blocks claim;
the job remains queued and no attempt is created. During execution, both file
writes remain exclusive. Expected workflow/output/filesystem failure
atomically fails the running job and attempt with an approved code.

Successful execution and valid-output recovery use one short transaction:

```text
running job -> succeeded
running attempt -> succeeded
insert immutable compact result reference
```

Any validation or insertion failure rolls back every terminal database change.
Written files remain untouched and the job/attempt remain running for explicit
recovery. Retry never ignores a file or reference. Recover never rewrites,
moves, deletes, or cleans output. Partial and invalid evidence remains
inspectable.

There is no cleanup endpoint, force overwrite, force retry, or result
replacement.

## Founder Experience

Submission success keeps the completed form and exact key visible, distinguishes
Created from Exact replay, shows localized and raw current status, and links the
exact job. It never generates a key, resubmits, or runs.

Run success states that claim and attempt creation completed before HTTP 202,
shows attempt number and ID, does not imply completion, does not poll, and
requires manual refresh.

Every command keeps the last settled job and attempts visible while pending or
after failure. Duplicate browser submission is disabled while pending. Stable
raw code and request ID remain visible. State conflicts require refresh;
idempotency conflict explains changed canonical request without claiming a
field diff; output conflict confirms evidence preservation; recovery uncertainty
confirms the job remains running.

Matching `en` and `zh-CN` catalogs cover these distinctions. Localized labels
remain paired with raw statuses, attempt values, codes, IDs, and timestamps.
Confirmations remain keyboard accessible, pending controls remain visible and
disabled, and recovery errors are associated with their field.

## Deterministic Verification

Backend coverage includes:

- created/replayed outcomes, every-status replay, keyed concurrency, changed
  request conflicts, and no-key run-ID uniqueness;
- claim-before-execution, one concurrent Run winner, Run/Cancel winner/loser,
  callback interruption, and duplicate claimed-execution rejection;
- non-executing Retry, next attempt numbering, concurrent Retry, and
  output/reference refusal;
- strict UTC/staleness, every recovery outcome, inspection uncertainty,
  concurrency, legacy zero-attempt recovery, inconsistent attempts, and
  transactional reference rollback;
- exclusive file preservation, path-free result reads, and file authority.

Web coverage includes:

- Created and Exact replay without automatic Run;
- conflict form/key preservation;
- the centralized action matrix and unknown-status refusal;
- claimed Run attempt evidence and manual refresh;
- pending double-click suppression and settled-evidence preservation;
- Retry/Recover distinction and outcome-specific recovery;
- exact UTC validation against loaded timestamp;
- raw codes, request IDs, attempt values, both locales, field errors, and
  generated contract freshness.

The authoritative repository gate is:

```text
uv run python scripts/check.py
```

## Persistence Boundary

Migration head remains:

```text
0005_paper_job_result_references
```

Sprint 165 adds no table, column, migration, durable status, attempt status,
lease, heartbeat, worker identity, queue ownership, or cleanup record. Old
migrations are unchanged.

## Founder Local Acceptance

In Standard and Demo, both locales, and representative `360px`, `768px`, and
`1280px+` widths:

- exercise Created, Exact replay, idempotency conflict, and form preservation;
- verify Run returns running plus one attempt before later manual refresh;
- verify duplicate Run and Run/Cancel stable winner/loser behavior;
- exercise failure, clean Retry, blocked Retry, and the next Run attempt number;
- exercise all recovery outcomes and uncertain inspection;
- verify raw timestamps, codes, IDs, request IDs, and attempts remain visible;
- verify no polling, automatic command, overwrite, cleanup, or financial claim;
- verify keyboard confirmations, disabled pending controls, field errors,
  focus, wrapping, and language-switch form preservation; and
- confirm Standard and Demo storage remain isolated.

Founder reliability acceptance remains pending.

## Known Limitations and S166 Handoff

- The FastAPI callback is process-local and non-durable.
- Execution is replay-safe at submission and conditionally claimed, but is not
  exactly once.
- Interrupted running work requires a human stale-time assertion and explicit
  Recover.
- There is no queue scan, startup execution, scheduler, worker loop, polling,
  push update, cleanup, or force repair.
- Errors remain sanitized and bounded; the broader product error inventory,
  observability, audit-detail consistency, and logging review belong to Sprint
  166.

Milestone 29 remains **In Progress**. S161–S164 are **Complete**. S165 is
**Implementation complete; Founder reliability acceptance remains**. Sprint
166 becomes next only after Sprint 165 is merged and Founder acceptance is
complete.
