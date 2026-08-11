# Sprint 203 — Versioned Strategy-to-Risk API, Errors, Audit, and Generated Contracts

## Status

Complete after Founder merge of PR #401. Issue #400 is the authoritative Sprint
specification, and Issue #389 remains the authoritative Milestone 33
architecture source. Sprints 197–203 are Complete. Sprint 204 is the current
implementation sprint; Sprints 205–206 remain Planned.

## Delivered Boundary

Sprint 203 exposes the durable S198–S202 authority through exactly these nine
founder-authenticated operations:

```text
POST /api/v1/strategy-signals/evaluate
GET  /api/v1/strategy-signals
GET  /api/v1/strategy-signals/{signal_id}

POST /api/v1/order-intents
GET  /api/v1/order-intents
GET  /api/v1/order-intents/{intent_id}

POST /api/v1/pre-trade-risk-decisions
GET  /api/v1/pre-trade-risk-decisions
GET  /api/v1/pre-trade-risk-decisions/{decision_id}
```

Requests contain only approved runtime or policy selections, durable references,
expected account/replay/session/event/instrument anchors, an actor, and the
existing idempotency header. One server-owned UTC timestamp and the existing
server-owned request ID cross the route boundary. Route handlers do not
calculate strategy output, target quantity, side, requested quantity, current
cash or position, reference price, notional, rule results, outcome, reasons,
identity, digest, or command provenance.

## Inspection and Read Contract

Responses expose complete approved immutable Signal, Intent/no-action, and
Decision projections. Quantities, money, price, and notional remain canonical
fixed-point strings. Raw stable IDs, digests, versions, timestamps, outcomes,
and ordered reasons are not localized. Command idempotency keys, ORM rows,
paths, database details, SQL, exception messages, and raw market event payloads
are never returned.

No-action remains command/replay evidence only. It has no list or detail route
and cannot be evaluated as an Intent.

List operations expose only the indexed S202 filters, enforce a 1–200 limit,
and use canonical unpadded URL-safe opaque keyset cursors. Each cursor is bound
to exactly one collection and contains only its schema, collection kind,
normalized UTC ordering timestamp, resource-ID tie-breaker, and checksum.
Malformed, tampered, duplicate-field, non-canonical, overlong, or cross-
collection cursors fail closed. Strict repository reconstruction means one
corrupt row fails the complete read.

## Errors, Correlation, and Audit

Central translation preserves the existing `ApiErrorResponse` envelope and
maps the closed not-found, idempotency, stale-authority, reconciliation,
invalid-runtime, invalid-policy, invalid-decimal, invalid-cursor,
schema-incompatible, authority-unavailable, storage-busy, and storage-failure
conditions to fixed sanitized public messages.

`RequestIdMiddleware` remains the sole request-ID authority. Caller request IDs
are ignored. Successful POST commands emit one bounded event for Signal
evaluation, Intent/no-action derivation, or risk evaluation. Events include
only correlation and durable identity/anchor fields; they exclude keys, actors,
runtime payloads, event payloads, financial values, SQL, paths, credentials,
and exception text.

## Generated Contracts

The existing side-effect-free export path updates:

```text
web/src/generated/openapi.json
web/src/generated/api-types.ts
```

The nine operation IDs are explicit and stable. The Intent/no-action command is
a strict discriminated union, closed vocabularies remain closed, canonical
decimals remain strings, and every documented route error uses the shared
stable envelope. No Web client, hook, page, navigation, component, or
localization behavior is added.

## Verification and Non-goals

Focused tests cover command status and replay semantics, convergence, strict
projections, filters, pagination, cursor integrity, stable errors, request IDs,
audit bounds, generated contracts, strict reads, and M31/M32 non-mutation. Full
verification uses `uv run python scripts/check.py` and `uv run alembic heads`.

Sprint 203 adds no migration, Demo data, worker, scheduler, reservation,
execution order, fill, fee, ledger mutation, replay progression, broker, live,
real-money, Docker, runtime-acceptance, or proxy behavior. The migration head
remains `0010_strategy_order_risk`.
