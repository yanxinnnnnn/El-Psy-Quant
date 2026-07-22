# Sprint 179 — Milestone 31 Architecture and Planning

## Status

**Complete.** Founder-approved GitHub Issue #355 is the authoritative source.
Sprint 179 was CTO-owned documentation-only planning and created no runtime PR.

## Result

The approved plan defines:

- SQLite events and postings as future account mutation authority;
- deterministic replay and verified projections;
- immutable snapshot and reconciliation evidence;
- exact Decimal string contracts and one immutable base currency;
- account identity, lifecycle, close, idempotency, version, and concurrency rules;
- cash, position, aggregate-cost-basis, fee, tax, and adjustment semantics;
- a bounded approved-M30 governance evidence link;
- transaction ordering and failure behavior;
- persistence, migration, API, bilingual Web, Demo, recovery, observability, and
  Founder acceptance boundaries; and
- the strict S179–S188 implementation sequence.

## Authority boundary

```text
explicit account command
  -> immutable ordered account event
  -> immutable cash and/or position postings
  -> deterministic ledger replay
  -> verified current projection
  -> derived snapshot and reconciliation evidence
```

Existing `PaperAccountState`, `PaperOrderLedger`, `PaperFill`, session summaries,
and Paper Trading artifacts remain legacy evidence. They are not reinterpreted
as M31 durable account or ledger truth.

## Approved handoff

Sprint 180 is the first implementation sprint. It may add only pure immutable
identity, lifecycle, decimal, command, and approved-evidence-reference contracts.
Ledger events and cash replay begin in S181 only.

At the S179 handoff:

- M31 is In Progress;
- migration head is `0006_portfolio_reviews`;
- S181–S188 remain planned after S180;
- M32–M36 have no sprint ranges;
- M34 remains the first genuine Paper Trading gate; and
- M36 remains the continuous multi-day Paper Trading gate.
