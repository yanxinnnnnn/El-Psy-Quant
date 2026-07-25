# Sprint 185 — Versioned Paper Account API, Errors, and Audit Surface Foundation

## Authority

GitHub Issue #366 is the authoritative Sprint 185 implementation
specification. Issue #355 remains the Milestone 31 architecture authority.
Sprint 185 reuses the merged Sprint 180–184 contracts without changing their
domain, digest, persistence, transaction, idempotency, or concurrency meaning.

## Result

Sprint 185 exposes durable Paper Account application authority through exactly:

```text
POST /api/v1/paper-accounts
GET  /api/v1/paper-accounts
GET  /api/v1/paper-accounts/{account_id}
GET  /api/v1/paper-accounts/{account_id}/ledger
POST /api/v1/paper-accounts/{account_id}/cash-movements
POST /api/v1/paper-accounts/{account_id}/position-adjustments
POST /api/v1/paper-accounts/{account_id}/evidence-links
POST /api/v1/paper-accounts/{account_id}/lifecycle
POST /api/v1/paper-accounts/{account_id}/snapshots
POST /api/v1/paper-accounts/{account_id}/reconciliations
```

There is no unversioned alias, singular alias, generic action route, or public
projection-rebuild route.

## Authority boundary

The HTTP boundary calls `PaperAccountApplicationService`. It does not query ORM
rows, own sessions or transactions, calculate financial state, build command
digests, repair projections, or reinterpret durable records.

```text
immutable account events and postings
  -> replay_paper_account_ledger(...)
  -> verified projection
  -> application service
  -> strict presentation-only API payload
```

SQLite events and postings remain mutation authority. Replay remains state
authority. Projection rows remain replaceable caches. Snapshot and
reconciliation rows remain immutable derived evidence. API dictionaries,
OpenAPI, generated TypeScript, browsers, and logs are not financial, ledger,
projection, digest, snapshot, reconciliation, or governance authority.

## Request and response contracts

Financial inputs and outputs are canonical fixed-point strings. JSON floats,
booleans used as integers, exponent notation, non-finite values, signed zero,
implicit rounding, locale formatting, leading zeroes, and trailing fractional
zeroes fail closed through the strict schema/domain boundary.

Creation accepts only display name, base currency, initial cash, and actor.
Account mutations accept the exact expected version and explicit command
meaning. Snapshot and reconciliation operations accept exact ledger-head
anchors. IDs, timestamps, event/posting identity, resulting state, and digests
remain server/domain owned.

Every POST requires one exact normalized `Idempotency-Key`. New accepted
operations return `201` with `replayed: false`; exact replay returns `200` with
`replayed: true`; changed intent fails with the endpoint-appropriate conflict.
The key is never returned or logged.

## Bounded reads

Account listing uses durable keyset order:

```text
created_timestamp DESC
account_id ASC
```

The opaque cursor contains only validated ordering anchors and an integrity
check. Repository queries apply the anchor and `limit + 1`; routes never load
and slice all accounts.

Ledger reads use exclusive `after_sequence_number` plus a bounded limit.
Repository queries load one page and its postings, validate exact command
meaning, posting values and digests, event digests, contiguous sequence, prior
chain anchor, and current account head when present. They do not replay and
return an unbounded history prefix for every page.

Detail reads require a strictly verified current projection. Missing, stale,
malformed, mismatched, or `reconciliation_required` projection state fails
closed and is never repaired by an ordinary read.

## Stable errors and request correlation

Sprint 185 adds the closed Paper Account error inventory:

```text
paper_account_not_found
paper_account_version_conflict
paper_account_idempotency_conflict
paper_account_frozen
paper_account_closed
paper_account_close_not_empty
paper_account_insufficient_available_cash
paper_account_negative_position
paper_account_negative_cost_basis
paper_account_zero_quantity_nonzero_cost_basis
paper_account_invalid_decimal
paper_account_invalid_m30_reference
paper_account_projection_stale
paper_account_reconciliation_failed
paper_account_snapshot_conflict
paper_account_storage_busy
paper_account_schema_incompatible
```

One central translator maps typed domain/application/persistence failures to
sanitized `404`, `409`, `422`, or `503` responses. Framework authentication,
request validation, not-found, method-not-allowed, and unexpected-error
contracts remain unchanged. Every success and handled error carries the same
server-owned UUID request ID in its response surface.

## Bounded audit correlation

Successful accepted or replayed commands, snapshots, and reconciliations emit
bounded correlation events containing only operation, request ID, HTTP status,
durable account/event/evidence identity, version, event/outcome status, replay
status, and projection status where applicable.

They never contain request/response bodies, idempotency keys, actor or reason
text, symbols, cash, quantity, M30 identities, digests, SQL, paths, tracebacks,
or exception details. Read routes emit no mutation event. Logs are not required
for durable reconstruction.

## Generated contracts

The deterministic OpenAPI snapshot and generated TypeScript API types are
regenerated through the repository generators. Financial fields remain
strings, versions remain integers, booleans remain booleans, nullable fields
remain explicit, and all closed vocabularies generate stable enums.

## Preserved boundary

Migration head remains:

```text
0007_paper_account_ledger
```

Sprint 185 adds no migration, durable authority, Founder Web page, hook, form,
navigation, localization catalog, Demo account/data/reset behavior, filesystem
snapshot/reconciliation artifact, Docker runtime acceptance, market data,
order/fill, reservation, execution, worker, scheduler, broker, QMT, MiniQMT,
private-edge, live, or real-money behavior.

S186 remains the bilingual Founder Paper Account Web workspace. S187 remains
workflow integration, Demo, upgrade/recovery, and Founder acceptance hardening.
M32–M36 remain planned milestones with no allocated sprint ranges.

Founder review, local runtime acceptance, manual merge, and any Docker runtime
acceptance remain Founder-owned.
