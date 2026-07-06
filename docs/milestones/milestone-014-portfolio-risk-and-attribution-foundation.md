# Milestone 14 — Portfolio Risk & Attribution Foundation

## Status

Planned.

## Product Goal

Make portfolio-level behavior explainable after portfolio construction has become explicit.

Milestone 13 answered how aligned symbol return streams become portfolio returns and summary artifacts. Milestone 14 should now explain where portfolio risk, drawdowns, and return contribution come from without jumping to optimization, dynamic rebalancing, or execution.

## Why This Comes Now

The project can now build a portfolio-level return series from:

```text
strategy return streams -> aligned portfolio inputs -> portfolio return aggregation -> portfolio summary artifact
```

That makes portfolio-level risk work meaningful. Before Milestone 13, risk attribution would have rested on unclear alignment and weighting assumptions. After Milestone 13, attribution can be tied to explicit static construction inputs.

## Planned Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S64 | Complete | Plan Milestone 14. | Portfolio risk and attribution scope and sprint sequence. | No implementation during planning. |
| S65 | Planned | Add portfolio risk metrics. | Small risk summary for portfolio return series. | No optimizer or factor model. |
| S66 | Planned | Add drawdown inspection. | Inspect portfolio drawdown periods and depth. | No stress-testing engine. |
| S67 | Planned | Add symbol contribution. | Attribute portfolio return contribution from aligned symbol returns and static weights. | No dynamic rebalancing. |
| S68 | Planned | Add attribution summary artifact. | Persist portfolio risk and contribution summary. | Preserve artifact discipline. |
| S69 | Planned | Close milestone. | Milestone 14 documentation refresh. | No scope expansion. |

## Planned Work

### Portfolio Risk Metrics

The first implementation sprint should add a small portfolio risk summary from portfolio return series.

Expected candidates include existing-style metrics such as:

- volatility
- downside or drawdown-oriented summary where scoped
- worst period return
- best period return
- positive / negative period counts if useful

The sprint should avoid pretending to be a full institutional risk model.

### Drawdown Inspection

Portfolio drawdown should become inspectable, not just summarized as one number.

The project should be able to identify simple drawdown windows and make the result easy to review. This should remain local and deterministic.

### Symbol Contribution

With aligned returns and static weights available, the project can compute simple per-symbol contribution to portfolio return.

The initial contribution model should be explicit:

```text
symbol_contribution[t] = aligned_return[t, symbol] * static_weight[symbol]
```

This is contribution under static-weight assumptions, not dynamic attribution, Brinson attribution, factor attribution, or optimization.

### Attribution Summary Artifact

Risk and contribution results should become inspectable and portable through a small artifact, following the existing artifact discipline.

## Guardrails

Milestone 14 should avoid:

- portfolio optimization
- dynamic weights
- rebalancing engines
- live or paper trading
- broker execution assumptions
- cash, financing, tax, borrow, or margin models
- covariance matrix optimization
- VaR or stress testing unless explicitly scoped later
- full factor models unless explicitly scoped later
- dashboards or databases
- broad configured-run integration
- broad CLI expansion
- strategy changes
- resolver changes
- plugin frameworks or dynamic loading

## Exit Criteria

Milestone 14 is complete when:

- portfolio return risk can be summarized under explicit assumptions
- drawdowns can be inspected in a deterministic local form
- symbol-level contribution can be calculated from aligned returns and static weights
- attribution outputs can be summarized or persisted consistently
- documentation explains assumptions, limits, and what remains out of scope

## Relationship To Future Milestones

Milestone 14 prepares the project for Milestone 15 — Backtest Execution Realism Foundation.

Execution realism should wait until portfolio behavior and risk are explainable. Otherwise, more realistic execution assumptions can make results look more sophisticated without making the portfolio easier to understand.

## Current Next Step

```text
Sprint 65 — Portfolio Risk Metrics Foundation
```

Start by adding simple portfolio risk metrics before moving into contribution or attribution artifacts.
