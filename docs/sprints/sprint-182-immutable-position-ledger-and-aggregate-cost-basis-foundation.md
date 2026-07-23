# Sprint 182 — Immutable Position Ledger and Aggregate Cost Basis Foundation

## Status

**Implementation complete / pending Founder review.** GitHub Issue #360 is the
authoritative implementation specification. Issue #355 remains the
authoritative M31 architecture source.

## Objective

Extend the merged Sprint 180–181 pure domain authority with immutable position
postings, exact aggregate-cost-basis replay, and one complete cash-plus-position
derived state without adding persistence or later-sprint runtime behavior.

## Implemented boundary

The `el_psy_quant.paper_account` package now provides:

- `PostPaperPositionAdjustmentCommand` for one normalized symbol with exact
  signed `PaperQuantity` and `PaperMoney` deltas;
- exactly `opening_balance`, `manual_correction`, `corporate_action`, and
  `other` adjustment categories;
- immutable `PaperPositionLedgerEntry` records at exact entry index zero;
- the typed `position_adjustment_posted` account event;
- `PaperAccountPosition` with exact quantity and aggregate cost basis;
- `PaperAccountLedgerState` with identity, lifecycle, cash, available cash,
  ordered current positions, approved M30 references, and head identity;
- pure `apply_paper_position_adjustment(...)`; and
- fail-closed `replay_paper_account_ledger(...)` for mixed cash, position,
  evidence-link, and lifecycle histories.

Position events reuse the single Sprint 181 sequence, version, event, and chain
authority. They contain exactly one position entry and no cash entry.
Non-position events contain no position entries.

## Position and cost-basis authority

For each normalized symbol, current quantity and aggregate cost basis are the
exact ordered sums of their explicit posting deltas. Replay rejects negative
intermediate or resulting quantity, negative aggregate cost basis, and zero
quantity with non-zero aggregate cost basis.

Reducing quantity never infers a cost-basis reduction. Changing cost basis never
infers a quantity change. No cash posting, price, execution, proceeds, fee, tax,
or realized return is inferred. When both exact authorities reach zero, the
symbol is omitted from current positions while immutable history remains.

Shorting, borrowing, margin, tax lots, FIFO/LIFO, realized or unrealized PnL,
market value, equity, leverage, exposure, and buying power are absent.

## Average unit cost

Average unit cost is display-only:

```text
aggregate_cost_basis / quantity
```

For positive quantity it is exported as a canonical fixed-point string with at
most eight fractional digits. Non-terminating or more precise quotients use
explicit `ROUND_HALF_EVEN`, independent of ambient Decimal context, and expose
whether rounding occurred. Zero quantity yields no average and a false rounded
flag at the internal value boundary; zero positions are omitted from current
state.

The rounded value never participates in replay, command or posting digests,
validation, mutation, or reconstruction.

## Digest compatibility and replay

Existing Sprint 181 events retain their exact digest payload shape and fixed
regression vector. A position event adds a distinct unambiguous
`position_entries` digest member covering the complete ordered position-entry
export. The entry digest is therefore covered transitively by the event and
chain digests.

Full replay verifies exact scalar types, normalized symbols, posting
cardinality, unique event and entry IDs, contiguous versions, command
reconstruction, entry/event/chain digests, lifecycle restrictions, evidence
uniqueness, intermediate financial invariants, supplied bundle states, and the
empty-account close rule. It performs no repair and writes nothing.

The Sprint 181 cash-only state remains an explicitly incomplete compatibility
view. Full state is always rebuilt from the same immutable mixed event chain.

## Verification

Focused tests cover all four categories, normalization, exact scalar rejection,
position application, quantity-only and cost-only corrections, reductions,
ordering, average-cost rounding, mixed history through terminal close, stable
Sprint 181 digests, and tamper rejection.

The required repository-wide command is:

```text
uv run python scripts/check.py
```

## Explicit non-goals

Sprint 182 adds no persistence, SQLite, SQLAlchemy, Alembic migration,
snapshot, reconciliation, projection rebuild, application service, transaction,
API, OpenAPI, generated TypeScript, Founder Web, localization, Demo, Docker or
runtime behavior, order/fill persistence, reservation, execution, slippage,
market data, session clock, strategy-to-order pipeline, pre-trade risk, tax
lots, PnL, market value, worker, scheduler, broker, QMT, MiniQMT, private-edge,
live, or real-money behavior.

The existing `el_psy_quant.paper` package remains unchanged. Migration head
remains `0006_portfolio_reviews`.
