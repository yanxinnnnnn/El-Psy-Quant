# Sprint 143 — Lifecycle Proposal and Human Review Application Commands

## Status

Complete.

## Objective

Expose the existing strategy lifecycle transition proposal and human-controlled transition record contracts through thin synchronous application commands and versioned API endpoints.

## Delivered Boundary

Sprint 143 adds immutable transport commands, explicit immutable product views, strict request schemas, explicit response schemas, focused sanitized errors, and exactly two production endpoints:

```text
POST /api/v1/lifecycle-transition-proposals
POST /api/v1/lifecycle-transition-records
```

Both requests complete synchronously and return HTTP 200 with fresh normalized in-memory views. Caller-supplied IDs remain domain identities rather than durable resource or job IDs, so repeated IDs across independent requests are accepted.

## Domain Authority

The application layer reconstructs the complete governance chain only through the existing public strategy-review factories:

```text
create_strategy_review_evidence_reference(...)
create_strategy_lifecycle_state_snapshot(...)
create_strategy_lifecycle_transition_proposal(...)
create_strategy_lifecycle_transition_record(...)
```

These factories remain authoritative for evidence types, lifecycle states, permitted transitions, normalization, timestamps, human review outcomes, and resulting-snapshot rules. The API layer enforces only strict JSON shape, primitive types, arrays, and unknown-field rejection.

The review command carries the complete proposal because Sprint 143 has no repository, persistence, resource lookup, or filesystem search. Evidence references remain compact unresolved pointers; the commands do not load, inspect, verify, score, or rank referenced artifacts.

## Human-Control Boundary

An approved record requires a separate caller-supplied resulting snapshot whose strategy and lifecycle state match the proposal. Rejected and deferred records prohibit a resulting snapshot.

Approval is governance evidence only. Neither a proposal nor a review record executes or applies a transition, mutates a snapshot, creates a snapshot automatically, establishes globally current state, triggers a paper workflow, or implies broker or live readiness.

## Errors

Structurally valid commands rejected during proposal construction return:

```text
HTTP 422
lifecycle_transition_proposal_invalid
Lifecycle transition proposal is invalid
```

Structurally valid commands rejected during proposal reconstruction or transition-record construction return:

```text
HTTP 422
lifecycle_transition_record_invalid
Lifecycle transition record is invalid
```

Both application errors contain fixed sanitized messages only. Malformed request structures continue to use the existing `request_validation_error` envelope, and server-owned request IDs remain consistent between response headers and error bodies.

## Guardrails

Sprint 143 adds no artifact, proposal, record, snapshot, timeline, status, or current-state persistence. It adds no filesystem access, evidence resolution, repository, registry, SQLite, SQLAlchemy, idempotency, job, queue, worker, scheduler, polling, retry, cancellation, paper execution, strategy execution, network behavior, broker, QMT, live execution, real-money behavior, or capital allocation.

## Next Step

```text
Sprint 144 — Milestone 26 Closeout
```
