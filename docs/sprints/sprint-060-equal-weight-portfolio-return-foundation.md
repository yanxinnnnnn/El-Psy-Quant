# Sprint 60 — Equal-Weight Portfolio Return Foundation

## Objective

Compute baseline equal-weight portfolio returns from already-aligned inputs.

## Product Goal

An aligned per-symbol return table should produce one inspectable portfolio
return series using the simplest explicit allocation rule.

## Implementation Scope

- Validate aligned return table type, date index, columns, and values.
- Require numeric, complete returns for at least one symbol.
- Compute the row-wise arithmetic mean across all symbol columns.
- Preserve the aligned index and return a `portfolio_return` Series.
- Leave the aligned input unchanged.

## Equal-Weight Assumption

Every included symbol contributes equally on every already-aligned date. This
helper performs no alignment, optimization, or dynamic allocation.

## Out of Scope

- Configurable weights, weight validation, rebalancing, or cash modeling.
- Costs, slippage, portfolio equity, summaries, or artifacts.
- Configured-run, CLI, risk, benchmark, optimization, or trading changes.

## Acceptance Criteria

- One or more aligned symbol columns produce arithmetic-mean returns.
- Invalid, incomplete, or non-numeric tables fail clearly.
- The result preserves the index and is named `portfolio_return`.
- Inputs are not mutated.
