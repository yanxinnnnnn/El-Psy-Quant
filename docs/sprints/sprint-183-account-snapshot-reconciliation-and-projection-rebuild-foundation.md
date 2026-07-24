# Sprint 183 — Account Snapshot, Reconciliation, and Projection Rebuild Foundation

## Status

**Implementation complete / pending Founder review.** GitHub Issue #362 is the
authoritative implementation specification. Issue #355 remains the
authoritative M31 architecture source.

## Objective

Extend the merged Sprint 180–182 pure domain authority with deterministic
complete projection rebuild, strict projection verification, immutable account
snapshot evidence, and immutable projection-reconciliation evidence without
adding persistence or later-sprint runtime behavior.

## Implemented boundary

Sprint 183 adds the approved pure equivalents of:

- `CreatePaperAccountSnapshotCommand` and
  `ReconcilePaperAccountProjectionCommand`;
- `PaperAccountProjection` and `PaperAccountPositionProjection`;
- `PaperAccountProjectionVerification`;
- `PaperAccountSnapshot`;
- `PaperAccountReconciliation`;
- projection rebuild and verification; and
- snapshot creation and projection reconciliation.

Every complete projection is rebuilt only through
`replay_paper_account_ledger(...)`. It contains canonical account identity,
lifecycle, cash and available cash, normalized-symbol positions, ordered
approved-M30 provenance references, exact source account/event/chain anchors,
and one canonical digest. Quantity and aggregate cost basis remain exact;
average unit cost remains display-only.

## No-silent-repair verification

Candidate projections are deeply validated before comparison. Cross-account
candidates and malformed types, decimals, symbols, tuple orderings, nested
records, average-cost fields, or digests fail closed with `ValueError`.

Valid same-account candidates return exactly one status:

```text
current
reconciliation_required
```

Mismatch codes are deduplicated in this fixed order:

```text
source_account_version_mismatch
source_event_id_mismatch
source_chain_digest_mismatch
identity_mismatch
lifecycle_status_mismatch
cash_balance_mismatch
available_cash_mismatch
positions_mismatch
evidence_references_mismatch
```

Verification and reconciliation never mutate, replace, invalidate, persist, or
repair the candidate projection.

## Snapshot and reconciliation evidence

Snapshot and reconciliation commands contain exact account-head anchors,
operation idempotency key, actor, reason, and canonical command digest.
Idempotency is contractual in S183; S184 now provides durable enforcement.

Snapshots embed one exact replayed projection and bind it to an explicit
snapshot ID and normalized UTC timestamp. Reconciliation artifacts record a
`matched` or `mismatched` outcome, ordered mismatch codes, and exact candidate
and authoritative projection anchors and digests. Both operations are allowed
for active, frozen, and closed accounts.

All operation commands, projections, snapshots, and reconciliation artifacts
use versioned canonical JSON and lowercase SHA-256 digests. Validation rejects
boolean/float integer aliases, non-canonical decimals, malformed strings and
digests, unordered/duplicate nested values, timestamp tampering, and digest
mismatches.

## Authority and mutation boundary

Events and cash/position postings remain the only mutation authority.
Projection, snapshot, and reconciliation are immutable derived evidence only.
They create no account event or posting, increment no account version, and
change no lifecycle, cash, positions, evidence links, event digests, or chain
digests. Existing Sprint 181 and Sprint 182 digest formats and vectors remain
unchanged.

## Explicit non-goals

Sprint 183 adds no SQLite, SQLAlchemy, repository, transaction, migration,
durable idempotency, projection-row persistence/invalidation, filesystem
artifact, application service, API, OpenAPI, generated TypeScript, Founder Web,
localization, Demo, Docker/runtime behavior, order, fill, market data, PnL,
equity, tax lot, worker, scheduler, broker, QMT, MiniQMT, private-edge, live, or
real-money behavior.

S183 itself adds no persisted or usable durable Founder Paper Account workflow.
S184 now provides persistence and internal application transaction authority at
migration head `0007_paper_account_ledger`; public API, Web, and Demo behavior
remain later scope.

M32–M36 retain no sprint ranges. M34 remains the first genuine
market/strategy-driven Paper Trading gate, and M36 remains the continuous
multi-day Paper Trading gate.
