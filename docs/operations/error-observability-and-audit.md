# Error, Observability, and Audit Operations

This runbook explains how to interpret the Sprint 166 Founder error surface and
bounded local product events. It does not authorize a state transition,
artifact change, cleanup, or retry.

## Correlation Workflow

1. Preserve the visible stable error code, server request ID, operation, HTTP
   status, and relevant entity ID.
2. Read the localized explanation and recovery guidance without translating or
   editing raw values.
3. Inspect local backend output for `el_psy_quant.product_events` entries with
   the exact request ID.
4. Compare transient events with durable Paper Job/job-attempt state and
   authoritative completed files.
5. Choose Refresh, Retry, Recover, or no action explicitly. Events never choose
   for you.

The Web never invents a missing request ID. A request completion event describes
one handled HTTP request. A Paper Job command event means a command committed
successfully. A Run terminal event describes the bounded callback outcome. None
of these events is durable governance evidence.

## Troubleshooting Matrix

| Surface | Meaning | Safe next step | Do not infer or do |
| --- | --- | --- | --- |
| Empty | The source is valid but contains no supported records | Configure or create authoritative input, then refresh | Do not treat empty as unavailable or seed hidden data |
| Not found | The exact route or entity does not exist | Return to the relevant list and choose an available identity | Do not blindly retry the same missing ID |
| Invalid | Input, response, or authoritative artifact failed validation | Preserve evidence, inspect the bounded detail and source contract, then correct the source explicitly | Do not overwrite or delete evidence |
| Unavailable | A local service, database, or configured root cannot currently be read | Verify local service/configuration and retry the read manually | Do not treat this as an empty source |
| Conflict | Current durable state or preserved output does not allow the requested mutation | Refresh current state and make a new explicit decision | Do not auto-retry, force, clean, or overwrite |
| Authentication | The paired local Founder credential was not accepted | Verify both local services use the same configured credential | Never record credentials in an issue or log |
| Protocol | The local route or HTTP method is unsupported | Return to a documented workspace action | Do not craft alternate methods or payloads |
| Internal/unknown | The API sanitized an unexpected or future failure | Record code/request ID, preserve state, inspect bounded events, and stop if authority is unclear | Do not seek exception text, traceback, SQL, or paths in public output |

## Paper Job Attempt Codes

| Raw code | Meaning | Safe recovery |
| --- | --- | --- |
| `workflow_validation_failed` | The selected workflow input failed approved validation during the claimed attempt | Review the request and preserved attempt, then use Retry only if the job is failed and outputs/references are absent |
| `output_conflict` | A reserved output already existed, so overwrite was refused | Preserve the output and inspect its authority; there is no force overwrite |
| `filesystem_io_failed` | A bounded local file operation failed | Verify local storage access and preserve partial evidence before another explicit decision |
| `interrupted_without_output` | Recover found no completed output; this does not prove execution never started | Review the interrupted attempt and queued job before choosing a later Run |
| `partial_output_detected` | Recover found exactly one of the two required outputs | Preserve the partial file; do not clean or Retry over it |
| `invalid_output_detected` | Recover found outputs that were invalid or inconsistent | Preserve both files and inspect validation evidence; do not force success or overwrite |

## Product Event Fields

The dedicated logger emits a static event name plus a bounded subset of:

```text
request_id, method, operation, route_template, status_code, duration_ms,
error_code, command, job_id, durable_status, attempt_id, attempt_number,
submission_outcome, recovery_outcome
```

The `internal_execution_failure` value is a fixed sentinel for an unexpected or
unverifiable callback outcome. It is not a persisted attempt error code.

Never expect or add credentials, headers, cookies, query strings, bodies,
idempotency keys, paths, SQL, exception text, tracebacks, financial values, or
artifact payloads. If any appear, preserve the minimum necessary local evidence
without sharing it and treat the behavior as a defect.

## Transient Versus Authoritative Evidence

```text
local product event
  -> transient process diagnostic

SQLite Paper Job and attempt records
  -> durable operational state

completed artifact files
  -> payload authority

human review record
  -> governance evidence, not runtime execution proof
```

An absent terminal event does not rewrite durable state. A completion event does
not prove a lifecycle transition, profitability, live readiness, or broker
execution. Standard and Demo logs may share one console during separate local
runs, but their databases and artifact roots remain isolated.

## Limitations

There is no durable log store, distributed trace, telemetry backend, remote
reporting, user analytics, worker, queue, scheduler, heartbeat, polling, cleanup
service, or automatic recovery. Process restart can discard transient events.
Use the exact visible request ID only for bounded local correlation and rely on
durable state and authoritative files for decisions.
