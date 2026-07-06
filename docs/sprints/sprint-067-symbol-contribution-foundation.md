# Sprint 67 — Symbol Contribution Foundation

## Objective

Add deterministic per-symbol portfolio return contribution from aligned symbol
returns and validated static weights.

## Implementation Scope

- Reuse aligned-return validation and static-weight normalization.
- Multiply each symbol return by its corresponding static weight.
- Preserve the aligned index and configured symbol column order.
- Summarize totals, arithmetic means, and positive, negative, and zero counts
  for each symbol in input order.
- Keep inputs unchanged and calculations deterministic.

## Contribution Scope

Sprint 67 adds static-weight per-symbol contribution only. A symbol's periodic
contribution is its aligned return multiplied by its validated static weight.
Row-wise contribution sums therefore equal the existing static-weight portfolio
return.

## Out of Scope

- Artifact schemas or writers and configured-run integration.
- YAML, CLI, manifest, or metrics changes.
- Dynamic weights, rebalancing, allocation changes, or broader attribution.
- Database, dashboard, strategy, resolver, or plugin changes.

## Acceptance Criteria

- Contribution returns preserve aligned dates and symbol order.
- Weight keys normalize through the existing static-weight boundary.
- Summary rows preserve symbol order and contain deterministic totals and counts.
- Invalid inputs fail clearly and inputs are not mutated.
