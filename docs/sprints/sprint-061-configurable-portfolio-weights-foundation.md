# Sprint 61 — Configurable Portfolio Weights Foundation

## Objective

Validate user-supplied static weights and compute weighted portfolio returns.

## Product Goal

Already-aligned symbol returns should support one explicit user-defined static
allocation for comparison with the equal-weight baseline.

## Implementation Scope

- Normalize configured symbols and weight keys through the universe boundary.
- Require exact symbol coverage and preserve configured symbol order.
- Require numeric, non-missing, non-negative weights summing to 1.0.
- Compute the row-wise weighted sum of validated aligned symbol returns.
- Preserve the aligned date index and leave all inputs unchanged.

## Static-Weight Assumption

Weights are supplied directly and remain constant for every aligned row. The
code does not scale, optimize, rebalance, or infer weights.

## Out of Scope

- Dynamic weights, optimization, rebalancing, cash, costs, or portfolio equity.
- Portfolio artifacts, configured-run or YAML wiring, CLI, risk, or trading.
- Databases, dashboards, plugins, or execution integration.

## Acceptance Criteria

- Valid weights are normalized and returned in configured symbol order.
- Invalid symbol coverage, values, and totals fail clearly.
- Weighted returns preserve the index and are named `portfolio_return`.
- Input mappings and DataFrames are not mutated.
