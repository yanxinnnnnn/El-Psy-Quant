# Sprint 184 — Durable Paper Account Persistence, Migration, Concurrency, and Application Service Foundation

## Authority

GitHub Issue #364 is the authoritative Sprint 184 implementation
specification. Issue #355 remains the Milestone 31 architecture authority.

## Result

Sprint 184 makes the merged Sprint 180–183 Paper Account contracts durable
without creating a second financial, event, replay, projection, or digest
authority.

The single additive migration is:

```text
0006_portfolio_reviews
  -> 0007_paper_account_ledger
```

It adds:

```text
paper_accounts
paper_account_events
paper_cash_ledger_entries
paper_position_ledger_entries
paper_account_creation_keys
paper_account_projections
paper_account_position_projections
paper_account_snapshots
paper_account_reconciliations
```

No Paper Account rows are seeded. Upgrade preserves all prior product data and
downgrade removes only Sprint 184 objects.

## Durable authority

- Account events and cash/position entries are immutable mutation authority.
- `replay_paper_account_ledger(...)` remains state authority.
- Projection rows are replaceable caches only.
- Snapshot and reconciliation rows are immutable derived evidence.
- Canonical Decimal strings are stored without float conversion.
- Existing Sprint 181–183 command, entry, event, chain, projection, snapshot,
  and reconciliation digest formats remain unchanged.

Named SQLite triggers reject `UPDATE` and `DELETE` for events, postings,
creation keys, snapshots, and reconciliations. Account deletion and identity
mutation are also rejected. Projection rows remain replaceable by approved
repository/application operations.

## Strict reconstruction

Persistence mapping validates exact schema versions, strings, UTC timestamps,
integers, booleans, canonical JSON, canonical decimal strings, tuple ordering,
symbols, vocabularies, source anchors, and digests.

Loaded events are reconstructed as their exact domain commands and reapplied
through the merged pure operations. Each reconstructed event and posting is
compared with its durable row, progressive bundle state is derived, and the
complete history is passed through authoritative ledger replay. Missing or
extra postings, sequence gaps, malformed payloads, duplicate identities, digest
tampering, and head inconsistencies fail as typed persistence corruption.
Ordinary reads never repair persisted state.

## Transaction and idempotency order

Creation uses one explicit SQLite write transaction:

```text
normalize caller intent and digest
  -> resolve global creation key
  -> generate server-owned IDs and UTC time only for a new request
  -> invoke pure account creation
  -> insert account, key, event, initial-cash posting, and projection
  -> commit all-or-nothing
```

Existing-account mutations use:

```text
BEGIN IMMEDIATE
  -> resolve per-account command key before version rejection
  -> reconstruct and replay immutable history
  -> strictly verify the persisted projection
  -> require the exact expected version
  -> invoke one merged pure mutation
  -> append one event and posting group
  -> guarded compare-and-swap over account/version/event/chain
  -> atomically replace projection rows
  -> commit all-or-nothing
```

The guarded update gives exactly one winner. A loser rolls back all event,
posting, head, and projection writes. Same-key/same-digest retries return the
original accepted immutable-history prefix; conflicting digests fail closed.
SQLite busy/locked outcomes are typed and are not hiddenly retried.

## Projection, snapshot, and reconciliation behavior

Current projection reads require status `current`, exact account-head anchors,
strict nested validation, and an exact replay comparison. Missing, stale,
malformed, mismatched, or reconciliation-required projections fail closed.

Reconciliation records immutable matched/mismatched evidence and changes only
the compact projection status. It never modifies the candidate. Explicit
rebuild is the only non-mutation operation that replaces a stale or missing
projection; it replays immutable history and does not create an event or change
account version.

Snapshot and reconciliation operations have durable per-account operation
idempotency. They persist complete canonical Sprint 183 evidence without
creating account events or changing account version.

## Explicit boundary

Sprint 184 adds no:

- FastAPI route, OpenAPI schema, or generated TypeScript;
- Founder Web page, localization, or browser behavior;
- Demo seed, reset, install, or Docker runtime acceptance;
- filesystem snapshot/reconciliation artifact;
- durable order/fill, reservation, market, execution, PnL, equity, or tax-lot
  authority;
- worker, scheduler, broker, QMT, MiniQMT, private-edge, live, or real-money
  behavior.

Founder review, local runtime acceptance, and manual merge remain Founder-owned.
