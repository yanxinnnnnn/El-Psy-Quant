# Stateful Paper Account and Ledger Architecture

## Authority and status

GitHub Issue #355 is the authoritative Milestone 31 architecture specification.
This document records the approved repository-level architecture. If this
summary and Issue #355 differ, Issue #355 controls.

Milestone 31 is **In Progress** through Sprints 179–188. Sprints 179–182 are
Complete. Sprint 183 is implementation-complete and pending Founder review; it
adds only pure projection rebuild/verification and immutable snapshot and
reconciliation evidence on the merged Sprint 180–182 replay authority.

## Product goal

M31 establishes one durable local Paper Account whose identity, lifecycle,
cash, positions, aggregate cost basis, history, snapshots, and reconciliation
can be reconstructed from one auditable authority across restarts.

The authority chain is:

```text
explicit account command
  -> immutable ordered account event
  -> immutable cash and/or position postings
  -> deterministic ledger replay
  -> verified current projection
  -> derived snapshot and reconciliation evidence
```

SQLite event and posting rows will be mutation authority. Projections will be
rebuildable caches. Snapshot and reconciliation artifacts will be derived
evidence, not competing account truth.

## Existing Paper model boundary

The existing `el_psy_quant.paper` package remains unchanged. Its
`PaperAccountState`, `PaperOrderLedger`, `PaperFill`, session summary, and Paper
Trading artifact contracts remain valid evidence for their existing workflows.
They are not M31 account, event, posting, version, or ledger authority.

M31 does not import legacy float-valued artifacts into an account, rename those
types, wrap them as durable state, or infer account mutation from an order or
fill record.

## Exact numeric boundary

M31 financial values use `Decimal` in Python and canonical fixed-point strings
at JSON and future SQLite boundaries. Inputs reject floating point, booleans,
non-finite values, exponent notation, locale formatting, signed zero, implicit
rounding, unnecessary leading zeroes, and trailing fractional zeroes.

- money and aggregate cost basis: at most 8 fractional digits;
- position quantity: at most 12 fractional digits;
- both: at most 18 integer digits in absolute value;
- one immutable uppercase three-letter base currency per account; and
- no FX conversion, margin currency, or multi-currency cash book.

## Identity and lifecycle

Account creation owns a server-supplied opaque account ID, display label, base
currency, actor, UTC timestamp, explicit non-negative initial cash, and initial
`active` lifecycle status. Account IDs never become caller-controlled paths.

The closed lifecycle vocabulary is exactly:

```text
active
frozen
closed
```

Allowed transitions are exactly `active -> frozen`, `frozen -> active`,
`active -> closed`, and `frozen -> closed`. Closing is terminal and requires
ledger-derived proof of zero cash, zero position quantity, and zero aggregate
cost basis. Accounts are never deleted.

## Event, posting, and replay direction

Each accepted mutation will create one immutable ordered event. Per-account
sequence starts at 1, is contiguous, and equals the resulting account version.
Commands will be protected by explicit idempotency keys, canonical command
digests, expected versions, and one-winner optimistic concurrency.

Sprint 181 added:

- append-only cash postings and exact cash replay;
- exact event and chain digests;
- contiguous per-account sequence and version rules;
- exact cash-only state with `available_cash == cash_balance`; and
- no negative cash.

Sprint 182 adds:

- append-only position and aggregate-cost-basis postings;
- no negative quantity or aggregate cost basis;
- zero cost basis whenever quantity reaches zero; and
- no shorting, margin, tax lots, market value, or PnL;
- display-only average unit cost with explicit eight-place half-even rounding;
- one complete deterministic cash-plus-position ledger state; and
- mixed cash, position, evidence, and lifecycle replay through the same event
  and chain authority.

Fee, commission, tax, and corporate-action inputs remain explicit manual facts.
They are not calculated or inferred from market data.

## Approved M30 evidence relationship

An M31 account may link one exact M30 decision only after authoritative M30
artifacts verify the decision is governance-only and `approved`. The reference
stores bounded review/source/analysis/decision IDs and digests only.

It copies no weights, returns, calculations, rationale, notes, or warnings. It
creates no cash, position, order, fill, allocation, or execution authority.
Rejected, deferred, awaiting, missing, or digest-invalid evidence cannot be
attached as approved evidence.

## Persistence and transaction direction

S184 will add one additive migration after `0006_portfolio_reviews`, expected as
`0007_paper_account_ledger`, and the approved equivalent of account, event,
posting, creation-key, projection, snapshot, and reconciliation tables.

Every later account mutation will be one SQLite transaction that resolves
idempotent replay before version rejection, verifies the current projection,
conditionally advances the head, appends the event and postings, updates the
projection, and commits all-or-nothing. Ordinary reads never silently repair a
stale projection.

Snapshot and reconciliation files will be generated only through separate
explicit idempotent operations after committed ledger truth exists. File writes
will not be account-mutation authority.

## API, Web, Demo, and acceptance direction

S185–S187 will add the separately approved API, bilingual Founder workspace,
isolated Demo seed, upgrade/recovery hardening, and Founder acceptance support.
The browser will display canonical backend values and will not calculate
financial truth. Standard will remain unseeded; Demo storage will remain
isolated.

Founder acceptance, Docker startup, backup, reset, restart, browser inspection,
and merge remain Founder-owned operations.

## Sprint 180 boundary

Sprint 180 adds only:

- `el_psy_quant.paper_account` as a separate pure domain package;
- `PaperMoney` and `PaperQuantity`;
- immutable account identity and references;
- lifecycle vocabulary, close-eligibility facts, and pure transition checks;
- create, freeze, reactivate, close, and approved-review-link commands;
- canonical JSON command payloads and SHA-256 command digests; and
- a trusted bounded reference from a genuine approved M30 decision artifact.

Sprint 180 adds no event, posting, replay, balance, position, persistence,
migration, API, Web, Demo, Docker, order, fill, execution, market, worker,
broker, private-edge, or live behavior. Migration head remains
`0006_portfolio_reviews`.

## Sprint 181 boundary

Sprint 181 adds only pure domain authority:

- `PostPaperCashMovementCommand` for deposit, withdrawal, manual adjustment,
  fee, commission, and tax facts;
- immutable `PaperAccountEvent` and `PaperCashLedgerEntry` records;
- creation and `initial_cash`, cash-movement, approved-M30 evidence-link, and
  lifecycle event construction;
- deterministic command verification plus entry, event, and chain digests;
- exact contiguous per-account sequence/version rules;
- `PaperAccountCashState` with exact non-negative cash and
  `available_cash == cash_balance`;
- pure command application; and
- fail-closed replay that verifies command, entry, event, and chain integrity
  without repair.

This cash-only state remains a supported incomplete compatibility view. Sprint
181 is Complete after PR #359 merged. Its valid event exports and digests remain
byte-for-byte stable under the Sprint 182 extension.

## Sprint 182 boundary

Sprint 182 adds only pure domain authority:

- `PostPaperPositionAdjustmentCommand` with the four approved manual
  adjustment categories and normalized one-symbol scope;
- immutable `PaperPositionLedgerEntry` records;
- the typed `position_adjustment_posted` event in the existing sequence and
  digest chain;
- exact long-only quantity and aggregate-cost-basis application;
- `PaperAccountPosition` with display-only average unit cost rounded explicitly
  with `ROUND_HALF_EVEN` to at most eight fractional digits;
- `PaperAccountLedgerState` as the complete cash-plus-position derived state;
- a position event bundle that contains exactly one position entry and no cash
  entry; and
- fail-closed full replay of mixed cash, position, evidence, and lifecycle
  histories.

Quantity and aggregate cost basis remain the exact replay authorities. Reducing
one does not infer a change to the other, position adjustments infer no cash
posting, and zero quantity requires zero aggregate cost basis before the symbol
is omitted from current positions. Average unit cost never enters a command,
posting, digest, replay, validation, or reconstruction calculation.

This complete state is rebuildable in memory only. Sprint 182 is Complete after
PR #361 merged, and its event, posting, and chain digest formats remain stable.

## Sprint 183 boundary

Sprint 183 adds only pure derived-domain capability:

- non-mutating snapshot and reconciliation operation commands anchored to one
  exact replayed account head;
- `PaperAccountProjection`, rebuilt only through
  `replay_paper_account_ledger(...)`, with canonical cash, ordered positions,
  ordered approved-M30 evidence references, source anchors, and digest;
- strict candidate verification returning only `current` or
  `reconciliation_required` with closed, ordered mismatch codes;
- immutable `PaperAccountSnapshot` evidence embedding one exact projection; and
- immutable `PaperAccountReconciliation` evidence recording matched or
  mismatched candidate and authoritative anchors.

Projection verification validates the candidate before comparison and never
silently repairs, replaces, or invalidates it. Projection, snapshot, and
reconciliation are rebuildable derived evidence only: they create no event or
posting, increment no account version, and change no lifecycle, cash, position,
evidence-link, event-digest, or chain-digest authority.

No persistence, migration, filesystem artifact, application service, API, Web,
localization, Demo, Docker, order/fill, market, execution, worker, broker, or
usable durable Founder account workflow is added. Those boundaries remain
S184–S187. Migration head remains `0006_portfolio_reviews`.

## Explicit deferrals

M32–M36 retain their approved sequence but no sprint ranges:

```text
M32 Market Data Replay, Trading Calendar, and Session Clock
M33 Strategy-to-Order and Pre-Trade Risk Pipeline
M34 Paper Execution Simulator and First True Paper Trading
M35 Durable Paper Runtime and Recovery
M36 Multi-day Paper Operations and Acceptance
```

M34 remains the first genuine market/strategy-driven Paper Trading gate. M36
remains the continuous multi-day Paper Trading gate. M31 does not implement
either capability.
