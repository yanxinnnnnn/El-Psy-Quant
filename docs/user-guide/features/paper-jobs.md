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
key with the same request can return the existing submission; reusing it with a
different request conflicts. Leaving the field blank sends no key.
The key is submission identity, not a password or a job ID.

In Demo Workspace mode, **Load demo example** may fill the form only from the
validated backend descriptor. It does not read the versioned source directly,
hardcode fixture values in the browser, submit the command, or run a job.

## Submit, Then Run

**Submit queued job** creates a durable `queued` record and opens its detail
page. It never runs the job.

Review the job identity, then select **Run** and confirm. Run acceptance is not
completion. The displayed state is intentionally treated as stale after
acceptance; use **Refresh status** before taking another action.

## Status and Manual Controls

| Status | Meaning | Available control |
| --- | --- | --- |
| `queued` | Stored and waiting for an explicit decision | **Run** or **Cancel** |
| `running` | Claimed for local processing | **Recover** |
| `failed` | An attempt ended with an approved failure code | **Retry** |
| `succeeded` | Processing completed | No mutation |
| `canceled` | A queued job was canceled | No mutation |

**Retry** returns a failed job to `queued`; it does not run it. **Recover** checks
a running job against the exact UTC **Stale before** value you supply and returns
the backend's current result. It does not silently choose a cutoff or chain a
retry. Use recovery only when you understand why a job may have been
interrupted.

Every mutation requires confirmation. State conflicts mean the displayed job
may be stale; refresh it before deciding what to do next.

## Review Attempts and Results

The Attempts table shows numbered operational attempts, timestamps, statuses,
and approved error codes. A succeeded job exposes a Portfolio Record only when
the backend reports **Result available: Yes**.

There is no automatic refresh, polling, broker connection, or live order
execution. Paper-job status is operational state and is separate from strategy
lifecycle governance.
