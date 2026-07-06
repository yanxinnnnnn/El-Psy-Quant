# Milestone 13 — Portfolio Construction Foundation

## Status

Planned.

## Product Goal

Introduce portfolio construction carefully after the project has established data, universe, artifact, and strategy boundaries.

Milestone 12 made local inputs harder to misuse. Milestone 13 should define how independent symbol-level results become portfolio-level returns under explicit assumptions.

## Why This Comes Now

The project already supports independent multi-symbol research:

```text
prices_by_symbol -> per-symbol Strategy.run(...) -> summarize_multi_symbol_results(...)
```

That is not yet a portfolio.

A portfolio requires explicit answers to different questions:

- Which return streams are combined?
- Which dates are included across symbols?
- How are missing symbol dates handled?
- How much capital is assigned to each symbol?
- Are weights equal, configured, static, or rebalanced?
- How are symbol returns aggregated into portfolio returns?
- Which assumptions are recorded for later inspection?

Milestone 13 should answer those questions before adding risk attribution or execution realism.

## Planned Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S58 | Complete | Plan Milestone 13. | Portfolio construction scope and sprint sequence. | No implementation during planning. |
| S59 | Planned | Align portfolio inputs. | Deterministic alignment of symbol return streams. | No allocation logic yet. |
| S60 | Planned | Add equal-weight portfolio returns. | Simple portfolio return aggregation with explicit assumptions. | No optimization engine. |
| S61 | Planned | Add configurable weights. | Validate and apply user-supplied static weights. | No dynamic rebalancing model unless explicitly scoped. |
| S62 | Planned | Add portfolio summary artifact. | Persist portfolio-level summary from local runs. | Preserve artifact discipline. |
| S63 | Planned | Close milestone. | Milestone 13 documentation refresh. | No scope expansion. |

## Planned Work

### Portfolio Input Alignment

The project should define how portfolio inputs are aligned before returns are combined.

Planning questions:

- Are inputs aligned by inner join on shared dates?
- Are missing dates rejected or dropped?
- What index assumptions are required?
- Is symbol order preserved from the validated universe?
- What error messages should users see when alignment is impossible?

The first implementation sprint should focus here before allocation logic.

### Equal-Weight Portfolio Returns

After alignment, the project should add a simple equal-weight portfolio return foundation.

This should be boring on purpose:

- no optimization
- no risk model
- no dynamic sizing
- no cash model
- no broker assumptions

Equal weight is a baseline construction rule, not a claim of optimality.

### Configurable Portfolio Weights

After equal-weight behavior is stable, the project can accept configured static weights.

Weight handling should be explicit:

- symbols must match the portfolio input universe
- weights must be numeric
- weights should be non-negative unless short exposure is explicitly introduced later
- weight sum rules should be documented and validated
- configured order should remain deterministic

### Portfolio Summary Artifact

Portfolio output should become inspectable without turning the project into a dashboard or database.

A later sprint in this milestone should define a small portfolio summary artifact that fits the existing local artifact discipline.

## Guardrails

Milestone 13 should avoid:

- portfolio risk attribution
- factor attribution
- volatility targeting
- optimization engines
- parameter search
- live or paper trading
- broker execution assumptions
- tax, borrow, margin, or financing models
- dashboards or databases
- strategy changes
- resolver changes
- plugin frameworks
- dynamic imports
- broad CLI redesign

## Exit Criteria

Milestone 13 is complete when:

- portfolio inputs can be aligned deterministically
- equal-weight portfolio returns can be computed under explicit assumptions
- configured static weights can be validated and applied
- portfolio-level outputs can be summarized or persisted consistently
- independent multi-symbol summaries are clearly distinguished from portfolio construction
- documentation explains assumptions, limits, and what remains out of scope

## Relationship To Future Milestones

Milestone 13 prepares the project for Milestone 14 — Portfolio Risk & Attribution Foundation.

Risk attribution should wait until portfolio construction assumptions are explicit. Otherwise, risk metrics can look precise while resting on unclear alignment, weighting, and aggregation rules.

## Current Next Step

The next sprint should be:

```text
Sprint 59 — Portfolio Input Alignment Foundation
```

Start by aligning symbol return streams deterministically. Do that before adding equal-weight returns or configurable weights.
