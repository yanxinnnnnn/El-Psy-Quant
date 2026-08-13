# Sprint 204 — Bilingual Founder Strategy-to-Risk Workspace

## Status

Current implementation sprint. Issue #402 is the authoritative Sprint
specification, and Issue #389 remains the authoritative Milestone 33
architecture source. Sprints 197–203 are Complete. Sprints 205–206 remain
Planned. Do not mark Sprint 204 Complete before Founder merge and acceptance.

## Delivered Web Boundary

Sprint 204 adds exactly one top-level Founder workspace:

```text
/strategy-to-risk
```

The route presents four ordered regions:

```text
1. Runtime and authority selection
2. Strategy Signal
3. Order Intent or no-action
4. Pre-Trade Risk Decision
```

The Web loads existing M31 Paper Account and M32 calendar/session/replay
authority through their generated-contract clients. It preserves the selected
head, chain, stream, cursor, event, session, and instrument anchors until the
Founder explicitly reloads or reselects them. Changing an upstream draft keeps
old evidence visible but blocks downstream continuation until a new explicit
command succeeds.

## Generated Contracts and Runtime Validation

All M33 request, response, list-filter, and detail types derive from:

```text
web/src/generated/api-types.ts
```

The existing same-origin client now provides thin functions for all nine S203
operations. No handwritten M33 transport authority, parallel HTTP stack, or
browser access to SQLite, Python, artifact roots, QMT, MiniQMT, or a broker is
introduced.

Runtime validators fail closed for incomplete or incompatible nested Signal,
Intent/no-action, and Decision authority. They require deterministic ID and
digest shapes, canonical fixed-point strings, UTC timestamps, discriminants,
complete nested references, allow/reject reason shape, and exactly these four
ordered rule records:

```text
insufficient_position_quantity
maximum_order_quantity_exceeded
maximum_order_notional_exceeded
insufficient_available_cash
```

Malformed success payloads become bounded `api_response_invalid` client errors
and never populate downstream workflow state.

## Explicit Commands and Idempotency

No command runs on mount, selection, detail load, refresh, or locale change.
Each explicit Signal, Intent, and Risk action owns an isolated browser-side
idempotency key. An exact unchanged retry reuses the same key. A materially
changed draft rotates to a fresh bounded key. Keys never cross step namespaces,
appear as authority, or render after success.

The Intent command sends only the selected server Signal ID, exact account
anchors, the closed conversion policy, and actor. It never sends caller-derived
side, quantity, position, or cash. The Risk command uses the dedicated
three-field expected-account block without `account_id`, plus exact selected
M32 anchors, closed policy configuration, persisted Intent ID, and actor. The
browser never selects a price event or calculates notional, rules, outcome, or
reasons.

## Evidence, Localization, and Errors

Signal, Intent, no-action, and Risk evidence remains complete and immutable.
The workspace distinguishes new evidence from idempotent replay, no-action from
Intent, valid allow from valid reject, and typed stale, reconciliation,
configuration, authority, storage, and sanitized unexpected failures. A valid
reject keeps all four ordered rules and ordered reasons visible; it is not an
API error. Allow remains pre-trade evidence only.

English and Simplified Chinese catalogs translate presentation copy while raw
IDs, versions, lifecycle/status/outcome/rule/reason codes, digests, canonical
quantity/money/price/notional strings, and timestamps remain byte-for-byte
unchanged. Locale refresh preserves the in-progress client state and does not
submit or refresh authority.

Stale, reconciliation, and conflict responses preserve drafts and upstream
evidence. The stable raw code, sanitized message, HTTP status, and server request
ID remain visible. The Founder may explicitly reload/reselect/retry, but the Web
never refreshes newer anchors and retries automatically.

## Preserved Authority Chain

```text
M31 immutable ledger and replayed Paper Account state
  + M32 calendar/session/event/replay state
    -> S198–S199 immutable Strategy Signal evidence
      -> S200 account-bound Intent or no-action evidence
        -> S201 immutable Risk snapshot and Decision
          -> S202 persistence/application orchestration
            -> S203 API/generated transport contracts
              -> S204 presentation and explicit command orchestration only
```

Sprint 204 does not redefine any M31, M32, or S198–S203 authority.

## Verification and Non-goals

Focused Web tests cover navigation and empty state, exact command construction,
step idempotency, no-action termination, allow/reject evidence, upstream
misalignment, stale/error preservation, malformed payload rejection, bilingual
state preservation, raw values, generated-contract sourcing, and absence of
account/replay mutation or execution controls.

Required verification:

```text
uv run python scripts/check.py
uv run alembic heads
```

Sprint 204 adds no domain, persistence, API, OpenAPI, generated-contract, Demo
v5, migration, worker, scheduler, reservation, Paper Account or replay mutation,
execution order, fill, fee, broker routing, automatic stale refresh-and-retry,
live/real-money, Docker runtime acceptance, or proxy behavior. The migration
head remains `0010_strategy_order_risk`.
