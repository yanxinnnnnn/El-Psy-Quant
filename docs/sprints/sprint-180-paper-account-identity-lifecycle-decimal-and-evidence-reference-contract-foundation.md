# Sprint 180 — Paper Account Identity, Lifecycle, Decimal, and Evidence Reference Contract Foundation

## Status

**Complete.** PR #357 is merged. GitHub Issue #356 is the authoritative
implementation specification. Issue #355 remains the authoritative M31
architecture source.

## Objective

Create the first pure immutable M31 domain-contract slice without adding ledger,
persistence, API, Web, Demo, or runtime behavior.

## Implemented boundary

The new `el_psy_quant.paper_account` package provides:

- `PaperMoney` and `PaperQuantity` with canonical fixed-point parsing, exact
  `Decimal` access, bounded scale/magnitude, immutable hashing/equality, and
  JSON-compatible exports;
- `PaperAccountIdentity` and `PaperAccountReference` with bounded opaque IDs,
  one normalized base currency, explicit actor, and UTC creation timestamp;
- the exact `active`, `frozen`, and `closed` lifecycle vocabulary;
- `PaperAccountCloseEligibility` and pure transition validation for the four
  approved transitions;
- `CreatePaperAccountCommand`, `FreezePaperAccountCommand`,
  `ReactivatePaperAccountCommand`, `ClosePaperAccountCommand`, and
  `LinkApprovedPortfolioReviewCommand`;
- canonical JSON payloads and lowercase SHA-256 command digests; and
- `ApprovedPortfolioReviewReference`, created only through a trusted factory
  from a genuine governance-only approved M30 decision artifact whose exact
  digest is revalidated.

The approved-review reference stores only review/source/analysis/decision IDs,
digests, schema version, and the approved outcome. It copies no scenario,
return, calculation, rationale, note, warning, allocation, or financial state.

## Decimal grammar

Public parsing accepts already-canonical strings such as `0`, `12`, `-12`,
`0.5`, `-0.5`, and `12.345`. It does not normalize caller mistakes. Floats,
booleans, exponent notation, non-finite values, plus signs, commas, whitespace,
leading zeroes, trailing fractional zeroes, signed zero, excessive scale, and
excessive magnitude fail validation.

Money supports at most 8 fractional digits; quantity supports at most 12. Both
support at most 18 integer digits.

## Verification

Focused deterministic tests cover decimals, identity, lifecycle, commands,
digest stability/sensitivity, approved-M30 reference trust, immutability, JSON
compatibility, and import isolation. The repository-wide required command is:

```text
uv run python scripts/check.py
```

## Explicit non-goals

Sprint 180 adds no cash or position entries, event chain, replay, balance,
available cash, cost basis, snapshots, reconciliation, projection, persistence,
migration, application service, API, OpenAPI, TypeScript contract, Founder Web,
localization, Demo, Docker, order/fill persistence, reservation, execution,
market/session behavior, worker, scheduler, broker, QMT, MiniQMT, private-edge,
live, or real-money capability.

The existing `el_psy_quant.paper` package is unchanged. Migration head remains
`0006_portfolio_reviews`. Sprint 181 builds its cash/event authority on these
contracts without changing their meaning.
