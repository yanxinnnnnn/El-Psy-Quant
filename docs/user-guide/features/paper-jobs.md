# Paper Jobs

Paper Jobs provides deliberate submission, execution, status, attempt, retry,
recovery, and cancellation controls for local paper workflows.

## Prepare a Submission

Choose **Paper Runs** and **Submit queued job**. Prepare the values before you
submit because the workspace does not derive account or trading fields for you.
The form includes:

- run ID and created timestamp;
- an optional idempotency key;
- starting and ending account timestamps, starting cash, current cash, and
  optional symbol/quantity positions;
- optional ordered rows with order ID, timestamp, symbol, side, quantity, and
  status; and
- optional ordered fill rows with timestamp, symbol, side, quantity, price, and
  an optional order ID.

Numeric fields must contain finite decimal values. Position symbols cannot be
duplicated within one account state. Order and fill row order is preserved.

Required and optional labels, placeholders, and nearby format hints describe
the unchanged backend transport: timestamps use explicit UTC, and cash,
quantity, and price use finite decimal input. The browser does not derive or
invent account values.

Use an idempotency key when you need an exact replay-safe submission. Reusing a
key with the same canonical request returns the original current job with an
**Exact replay** outcome; reusing it with a different canonical request
conflicts. The conflict does not claim a field-level difference. Leaving the
field blank sends no key and every successful no-key submission reports
**Created**.
The key is submission identity, not a password or a job ID.

In Demo Workspace mode, **Load demo example** may fill the form only from the
validated backend descriptor. It does not read the versioned source directly,
hardcode fixture values in the browser, submit the command, or run a job.

## Submit, Then Run

**Submit queued job** returns one of:

- **Created** — one new durable `queued` job exists; nothing has run and no
  attempt exists.
- **Exact replay** — the original current job was returned in whatever durable
  status it now has; no new job, attempt, execution, output, or result reference
  was created.

The completed form and exact entered idempotency key remain visible after
success or conflict. The workspace never generates a replacement key,
resubmits, or starts Run automatically. Follow the exact job link when ready.

Review the job identity, then select **Run** and confirm. Before HTTP 202 is
returned, the backend checks for conflicting authoritative outputs and compact
references, atomically changes `queued -> running`, and creates exactly one
numbered running attempt. The displayed attempt was claimed; completion is not
implied. Execution is still one non-durable FastAPI post-response task, so there
is no exactly-once guarantee. The browser does not poll; use **Refresh status**
manually before taking another action.

## Status and Manual Controls

| Status | Meaning | Available control |
| --- | --- | --- |
| `queued` | Stored and waiting for an explicit decision | **Run** or **Cancel** |
| `running` | Claimed for local processing | **Recover** |
| `failed` | An attempt ended with an approved failure code | **Retry** |
| `succeeded` | Processing completed | No mutation |
| `canceled` | A queued job was canceled | No mutation |

**Retry** first requires no authoritative output and no compact result
reference, then returns a failed job to `queued`. It creates no attempt, runs
nothing, and schedules no callback. A later separately confirmed Run creates
the next attempt number.

**Recover** is different. It checks a running job against the exact UTC **Stale
before** value you supply. The loaded raw `updated_timestamp` is shown beside
the field, and the threshold must be at or after it. Entering the threshold is
your explicit assertion that the observed execution is no longer active. The
browser never generates or autofills a cutoff.

Recovery reports one explicit outcome:

| Authoritative output inspection | Outcome | Durable result |
| --- | --- | --- |
| no artifact and no summary | `requeued` | job queued; active attempt interrupted with `interrupted_without_output` |
| two valid consistent outputs | `succeeded` | job/attempt succeeded and one compact reference inserted |
| exactly one output | `failed` | job/attempt failed with `partial_output_detected` |
| two invalid or inconsistent outputs | `failed` | job/attempt failed with `invalid_output_detected` |
| unreadable or uncertain inspection | API failure | job and attempt remain running for another explicit decision |

Recover never rewrites, relocates, deletes, or cleans files and never chains
Retry or Run.

Every mutation requires confirmation. State conflicts mean the displayed job
may be stale; the last settled job and attempt evidence remains visible, and
you must refresh it before deciding what to do next. An output conflict means
existing evidence was preserved and no overwrite occurred. No cleanup or force
retry control exists.

## Review Attempts and Results

The Attempts table shows numbered operational attempts, timestamps, statuses,
and approved error codes. A succeeded job exposes a Portfolio Record only when
the backend reports **Result available: Yes**.

There is no automatic refresh, polling, broker connection, or live order
execution. Paper-job status is operational state and is separate from strategy
lifecycle governance.
