# Milestone 13 — Portfolio Construction Foundation

## Status

Complete.

## Product Goal

Introduce portfolio construction carefully after the project established data, universe, artifact, and strategy boundaries.

Milestone 13 defines how independent symbol-level strategy results become portfolio-level returns under explicit assumptions about date alignment, return aggregation, static weights, and artifact discipline.

## Final Portfolio Construction Chain

```text
strategy return streams -> aligned portfolio inputs -> portfolio return aggregation -> portfolio summary artifact
```

This is the first point where the project can treat multiple symbols as one portfolio-level research object instead of only summarizing independent per-symbol backtests.

## Why This Milestone Mattered

Before this milestone, the project supported independent multi-symbol research:

```text
prices_by_symbol -> per-symbol Strategy.run(...) -> summarize_multi_symbol_results(...)
```

That is useful, but it is not yet a portfolio. A portfolio also needs explicit rules for shared dates, symbol coverage, weights, aggregation, and recorded assumptions.

## Sprint History

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S58 | Complete | Plan Milestone 13. | Portfolio construction scope and sprint sequence. | No implementation during planning. |
| S59 | Complete | Align portfolio inputs. | Deterministic alignment of symbol return streams. | No allocation logic yet. |
| S60 | Complete | Add equal-weight portfolio returns. | Simple portfolio return aggregation with explicit assumptions. | No optimizer. |
| S61 | Complete | Add configurable portfolio weights. | Validate and apply user-supplied static weights. | No dynamic rebalancing model. |
| S62 | Complete | Add portfolio summary artifact. | Standalone machine-readable portfolio summary artifact. | No configured-run integration. |
| S63 | Complete | Close milestone. | Milestone 13 documentation refresh. | No scope expansion. |

## Delivered Capabilities

### Portfolio Input Alignment

Portfolio construction now starts from deterministic aligned return inputs. The alignment boundary makes date handling explicit before any portfolio return is computed.

### Equal-Weight Portfolio Returns

The project can compute a baseline equal-weight portfolio return from an already-aligned return table. Equal weight is treated as a simple baseline rule, not as an optimal allocation claim.

### Configurable Static Weights

The project can validate user-supplied static weights and apply them to aligned symbol returns.

The weight boundary is intentionally strict:

- symbols are normalized consistently
- weight keys must match the aligned symbols exactly
- weights must be numeric
- boolean weights are rejected
- missing weights are rejected
- negative weights are rejected
- weights must sum to 1.0
- no automatic scaling is performed

### Portfolio Summary Artifacts

Portfolio return series can now be summarized into a standalone machine-readable artifact.

The artifact records schema version, construction method, ordered symbols, optional validated static weights, evaluation assumptions, and portfolio-level metrics from existing performance helpers.

## Explicit Assumptions

Milestone 13 made these assumptions visible:

- portfolio return inputs must be aligned before aggregation
- equal weight is a baseline
- configurable weights are static and non-negative
- weight sums are validated rather than silently rescaled
- standalone portfolio artifacts are separate from configured experiment artifacts for now
- independent multi-symbol summaries remain different from portfolio-level construction

## Guardrails Preserved

Milestone 13 deliberately avoided:

- portfolio risk attribution
- factor attribution
- volatility targeting
- optimization engines
- parameter search
- dynamic rebalancing
- cash or financing models
- configured-run portfolio wiring
- YAML portfolio configuration
- broad CLI redesign
- strategy or resolver changes
- plugin frameworks or dynamic imports

## Exit Criteria Result

Milestone 13 is complete because portfolio inputs can be aligned, equal-weight returns can be computed, configured static weights can be validated and applied, portfolio outputs can be summarized, and assumptions are documented.

## Relationship To Future Milestones

Milestone 13 prepares the project for Milestone 14 — Portfolio Risk & Attribution Foundation.

Risk and attribution work should wait until portfolio construction assumptions are explicit. Otherwise, risk numbers can look precise while resting on unclear alignment, weighting, and aggregation rules.

## Current Next Step

```text
Sprint 64 — Milestone 14 Planning
```

Sprint 64 should plan Milestone 14 — Portfolio Risk & Attribution Foundation.
