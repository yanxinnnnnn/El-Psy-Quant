# Sprint 166 — Error Surface, Observability, and Audit Hardening

## Status

Implementation complete. Founder Standard/Demo error-surface and observability
acceptance remains.

## Objective

Make local failures understandable, recoverable, and correlatable without
changing the public API error envelope, durable product state, artifact
authority, or explicit Founder control.

## Stable Error Contract

The API error envelope remains exactly:

```json
{
  "error": {
    "code": "stable_error_code",
    "message": "Bounded public message"
  },
  "request_id": "server-generated-uuid"
}
```

`X-Request-ID` remains server-generated and matches the body `request_id`.
Client-supplied request IDs are not trusted. The static backend inventory
classifies every current stable code as authentication, not found, invalid,
conflict, unavailable, protocol, or internal. Duplicate inventory entries fail
deterministically.

The matching Web inventory provides complete English and Simplified Chinese
title, explanation, and safe recovery guidance. Unknown future codes use a
generic fallback while preserving the exact raw code. Backend messages, codes,
IDs, statuses, timestamps, artifact values, and quantitative values remain
untranslated.

## Founder Error Surface

One reusable error state now presents:

- a localized category and context-appropriate heading;
- a localized explanation and bounded recovery action;
- operation, HTTP status, and relevant entity identity when known;
- the exact stable code;
- the exact server request ID when present, never an invented substitute; and
- the bounded backend public message in an accessible disclosure.

Empty, not-found, invalid, unavailable, conflict, protocol, internal, and
unknown states remain distinct. Reads retain source-specific manual retry.
Not-found detail views return to their authoritative list instead of blindly
retrying. Mutation conflicts preserve settled evidence and require a new
explicit Founder decision.

Long raw values wrap at narrow widths. Audit labels remain readable at
representative `360px`, `768px`, and `1280px+` widths, and disclosures remain
keyboard accessible.

## Paper Job Attempt Audit

The six approved attempt codes remain unchanged:

```text
workflow_validation_failed
output_conflict
filesystem_io_failed
interrupted_without_output
partial_output_detected
invalid_output_detected
```

Each code now has a bilingual label, meaning, and safe recovery instruction,
shown alongside the raw code. The guidance never implies that interrupted work
never started, never authorizes overwrite or cleanup, and never treats Retry or
Recover as automatic. Unknown future attempt codes preserve the raw value and
use bounded fallback guidance.

## Local Product Events

Observability uses Python standard-library logging through the dedicated
`el_psy_quant.product_events` logger. Application code installs no handler,
remote exporter, file sink, telemetry SDK, or durable log record.

Every handled API request emits one completion event with only:

```text
event
request_id
method
operation
route_template
status_code
duration_ms
error_code
```

Operation names and route templates come from a static approved catalog.
Concrete paths and query strings are never emitted. Unmatched routes use the
literal `unmatched`. Durations use monotonic time and a bounded non-negative
integer.

Successful Paper Job commands emit a second bounded event with the server
request ID, command, job ID, durable status, and only the applicable attempt,
submission outcome, or recovery outcome. Rejected commands emit no success
correlation event.

The already-claimed Run callback emits exactly one terminal event:

```text
paper_job_execution_completed
paper_job_execution_failed
paper_job_execution_uncertain
```

Expected failures use only the approved persisted attempt code. Unexpected or
unverifiable outcomes use the fixed `internal_execution_failure` sentinel and
do not expose exception text. These events are transient process diagnostics,
not governance evidence and not a replacement for SQLite state or completed
artifact files.

## Logging Denylist

Product events never contain:

- credentials, authorization values, headers, or cookies;
- query strings, request bodies, or response bodies;
- idempotency keys or canonical request digests;
- concrete filesystem paths, SQL, exception text, or tracebacks;
- run payloads, financial values, or artifact payloads; or
- arbitrary user-entered values.

The approved static operation and route-template catalog is the only route
identity recorded.

## Preserved Authority and Persistence

Sprint 166 does not change the Paper Job state machine, request-ID contract,
public error envelope, generated API contract, artifact authority, or
Standard/Demo isolation. The migration head remains:

```text
0005_paper_job_result_references
```

No migration, durable audit/log table, telemetry platform, remote reporting,
worker, queue, scheduler, polling, lifecycle automation, public debug field,
cleanup, force overwrite, financial calculation, or broker behavior is added.

## Deterministic Verification

Backend coverage verifies inventory completeness, duplicate refusal, request
event cardinality, bounded timing, status/error correlation, concurrent request
IDs, Paper Job command and execution correlation, rejection behavior, durable
attempt-code use, unexpected-failure sanitization, and the denylist.

Web coverage verifies exact catalog parity, category and unknown fallback
behavior, contextual headings, technical audit fields, missing request-ID
behavior, accessible disclosures, narrow wrapping, and bilingual attempt
meaning/recovery guidance.

The authoritative repository gate is:

```text
uv run python scripts/check.py
```

Docker build, image pull, container startup, and container smoke verification
remain outside Codex verification under project policy.

## Founder Local Acceptance

In isolated Standard and Demo workspaces, both locales, and representative
widths:

- exercise empty, not found, invalid, unavailable, conflict, and unexpected
  failure surfaces;
- confirm localized meaning and recovery remain paired with raw operation,
  entity, code, request ID, status, timestamp, and attempt values;
- confirm a missing request ID is not fabricated;
- inspect all six Paper Job attempt-code explanations;
- correlate one request, one successful Paper Job command, and Run completion,
  expected failure, and uncertain execution in bounded backend events;
- verify no denylisted data appears in those events;
- confirm refresh, Retry, and Recover remain distinct manual actions;
- confirm no polling, cleanup, overwrite, automation, or financial claim; and
- confirm Standard and Demo product state and artifacts remain isolated.

Record Founder acceptance before merging Sprint 166 or beginning Sprint 167.
