# Sprint 181 — Immutable Cash Ledger and Account Event Foundation

## Status

**Implementation complete / pending Founder review.** GitHub Issue #358 is the
authoritative implementation specification. Issue #355 remains the authoritative
M31 architecture source.

## Objective

Add the pure immutable account-event and cash-ledger authority that follows the
merged Sprint 180 contracts, without adding position state, persistence, API,
Web, Demo, Docker, market, order, fill, or execution behavior.

## Implemented boundary

The `el_psy_quant.paper_account` package now provides:

- `PostPaperCashMovementCommand` with exactly deposit, withdrawal,
  manual-adjustment, fee, commission, and tax semantics;
- immutable `PaperAccountEvent` records for creation, cash movement,
  approved-M30 evidence linking, freeze, reactivation, and close;
- immutable `PaperCashLedgerEntry` records, including creation-only
  `initial_cash`;
- explicit event and entry IDs supplied to pure factories, with no generated
  identity or timestamp;
- sequence and resulting account version starting at one and remaining
  contiguous;
- canonical command verification and deterministic entry, event, and chain
  SHA-256 digests;
- a fixed genesis-chain digest and exact
  `SHA-256(previous_chain_digest + event_digest)` linkage;
- `PaperAccountCashState` with exact non-negative `PaperMoney` replay and
  `available_cash == cash_balance`;
- pure creation, cash, evidence-link, and lifecycle application functions; and
- fail-closed replay that verifies commands, entries, events, chain continuity,
  lifecycle rules, evidence uniqueness, cash cardinality, and intermediate
  non-negative balances without repair.

All event details are bounded typed records. M30 references remain governance
provenance only and create no cash, position, allocation, order, fill, or
execution authority.

## Authority and limitations

Events and cash entries are immutable. Financial events contain exactly one
entry at index zero; evidence and lifecycle events contain none. Caller
timestamps never determine ordering. Frozen and closed accounts cannot accept
cash movements, closed is terminal, and close requires zero replayed cash plus
the explicit Sprint 180 eligibility facts.

The resulting cash state is pure and rebuildable in memory. It is not persisted,
is not a complete position-aware account, and is not yet a usable durable
Founder workflow. Position and aggregate-cost-basis authority remain S182.
Snapshot and reconciliation remain S183; persistence remains S184; API, Web,
Demo, and Founder acceptance remain S185–S187.

## Digest scheme

Command digests retain the Sprint 180 canonical JSON rules. Entry digests cover
the exact entry payload excluding the digest. Event digests cover the normalized
event header, typed details, and complete ordered cash-entry exports. Chain
digests concatenate the two fixed-length lowercase hexadecimal digests as ASCII
with no delimiter before SHA-256.

The exported genesis digest has semantic seed:

```text
el-psy-quant:paper-account-chain-genesis:v1
```

Replay recomputes every available digest and rejects malformed, mismatched,
reordered, incomplete, duplicated, or semantically invalid records. It never
silently repairs history.

## Verification

Focused tests cover cash commands, creation, all cash movements, lifecycle and
evidence rules, exact replay, immutability, JSON compatibility, and tamper
rejection. The required repository-wide command is:

```text
uv run python scripts/check.py
```

## Explicit non-goals

Sprint 181 adds no position posting, quantity, aggregate cost basis, average
cost, snapshot, reconciliation, projection persistence, SQLite, SQLAlchemy,
Alembic migration, application service, transaction, API, OpenAPI, generated
TypeScript, Founder Web, localization, Demo, Docker/runtime, order, fill,
reservation, execution, market data, session clock, strategy-to-order, risk
pipeline, worker, scheduler, broker, QMT, MiniQMT, private-edge, live, or
real-money behavior.

The existing `el_psy_quant.paper` package remains unchanged. Migration head
remains `0006_portfolio_reviews`.
