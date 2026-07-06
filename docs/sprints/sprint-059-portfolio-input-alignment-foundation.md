# Sprint 59 — Portfolio Input Alignment Foundation

## Objective

Align existing per-symbol strategy return streams on shared dates.

## Product Goal

Later portfolio-return logic should receive one deterministic table with
normalized, ordered symbols and only dates available for every symbol.

## Implementation Scope

- Validate symbols through the local research universe boundary.
- Validate result frame type, date index, and requested return column.
- Require numeric returns and reject missing returns on included dates.
- Inner-join return streams on dates shared by all symbols.
- Preserve configured symbol order and leave input frames unchanged.

## Alignment Policy

Sprint 59 uses shared dates only. It does not fill returns, infer calendars,
forward fill, or expose configurable alignment policies.

## Out of Scope

- Capital allocation or equal-weight portfolio return calculation.
- Configurable weights, rebalancing, cash, costs, or portfolio equity.
- Artifacts, configured-run wiring, CLI, risk, optimization, or trading changes.

## Acceptance Criteria

- Valid streams produce an ordered shared-date return table.
- Invalid symbols, frames, returns, and empty intersections fail clearly.
- Inputs are not mutated.
- No capital allocation or portfolio returns are computed.
