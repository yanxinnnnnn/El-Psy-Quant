# Sprint 66 — Portfolio Drawdown Inspection Foundation

## Objective

Add deterministic inspection of the single worst drawdown in an existing
portfolio equity series.

## Implementation Scope

- Validate a non-empty, positive numeric equity Series with a DatetimeIndex.
- Identify the worst running-peak percentage decline.
- Report its peak, trough, first recovery, and observation-count durations.
- Serialize dates as ISO strings and return JSON-compatible values.
- Treat increasing, flat, and one-observation equity as recovered zero-drawdown
  cases at the first observation.

## Drawdown Scope

Sprint 66 inspects one worst portfolio drawdown only. Duration fields count
observations between event positions, not calendar days. `max_drawdown` follows
the existing project convention and is reported as a negative return, or `0.0`
when no drawdown exists.

## Out of Scope

- Lists, rankings, tables, charts, or exports of drawdowns.
- Underwater curves or configured-run artifact integration.
- Symbol contribution or attribution artifacts.
- Allocation, rebalancing, strategy, resolver, YAML, CLI, or schema changes.

## Acceptance Criteria

- Recovered and unrecovered drawdowns identify deterministic event dates.
- Recovery is the first observation at or above the prior peak.
- Durations use observation counts.
- Inputs remain unchanged and results are JSON-compatible.
