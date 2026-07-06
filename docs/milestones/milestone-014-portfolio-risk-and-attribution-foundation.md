# Milestone 14 — Portfolio Risk & Attribution Foundation

## Status

Complete.

## Product Goal

Make portfolio-level behavior explainable after portfolio construction has become explicit.

Milestone 13 answered how aligned symbol return streams become portfolio returns and summary artifacts. Milestone 14 explains where portfolio risk, drawdowns, and return contribution come from without jumping to optimization, dynamic rebalancing, or execution.

## Why This Came Now

The project can now build a portfolio-level return series from:

```text
strategy return streams -> aligned portfolio inputs -> portfolio return aggregation -> portfolio summary artifact
```

That made portfolio-level risk work meaningful. Before Milestone 13, risk attribution would have rested on unclear alignment and weighting assumptions. After Milestone 13, attribution could be tied to explicit static construction inputs.

## Completed Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S64 | Complete | Plan Milestone 14. | Portfolio risk and attribution scope and sprint sequence. | No implementation during planning. |
| S65 | Complete | Add portfolio risk metrics. | Small risk summary for portfolio return series. | No optimizer or factor model. |
| S66 | Complete | Add drawdown inspection. | Inspect the single worst portfolio drawdown event. | No stress-testing engine. |
| S67 | Complete | Add symbol contribution. | Static-weight contribution returns and summaries from aligned symbol returns. | No dynamic rebalancing. |
| S68 | Complete | Add attribution summary artifact. | Standalone artifact composed from risk, drawdown, and contribution summaries. | Preserve artifact discipline. |
| S69 | Complete | Close milestone. | Milestone 14 documentation refresh. | No scope expansion. |

## Completed Work

### Portfolio Risk Metrics

Sprint 65 added `portfolio_risk_summary(...)` for an existing portfolio return Series.

It reports deterministic, JSON-compatible distribution and loss-frequency values, including:

- periods
- arithmetic mean return
- sample volatility for two or more observations
- one-observation volatility as `0.0`
- min and max return
- positive, negative, and zero period counts
- loss rate
- optional annualized volatility when an explicit frequency is supplied

These metrics describe the portfolio return series itself. They do not claim to be a full institutional risk model.

### Drawdown Inspection

Sprint 66 added `inspect_portfolio_drawdown(...)` for an existing portfolio equity Series.

It identifies the single worst running-peak drawdown event and reports:

- max drawdown
- peak date
- trough date
- recovery date
- recovered flag
- observation-count duration fields

Dates are serialized as ISO strings. Increasing, flat, and one-observation equity series are treated as explicit zero-drawdown cases.

### Symbol Contribution

Sprint 67 added static-weight per-symbol contribution returns and summaries.

The contribution model is explicit:

```text
symbol_contribution[t] = aligned_return[t, symbol] * static_weight[symbol]
```

The contribution helpers preserve aligned dates and symbol order. Row-wise contribution sums equal the existing static-weight portfolio return.

### Attribution Summary Artifact

Sprint 68 added `build_attribution_summary_artifact(...)` as a standalone, machine-readable artifact builder.

The artifact composes existing helper outputs instead of reimplementing their calculations:

```text
portfolio_return -> risk metrics
portfolio_equity -> drawdown inspection
aligned_returns + static_weights -> symbol contribution
risk + drawdown + contribution -> attribution summary artifact
```

The artifact records construction metadata, risk, drawdown, contribution summary records, and evaluation assumptions in deterministic JSON-compatible form.

## Assumptions

Milestone 14 keeps the assumptions deliberately conservative:

- portfolio returns already exist before risk is summarized
- portfolio equity already exists before drawdown is inspected
- aligned symbol returns and static weights already exist before contribution is calculated
- static weights are validated through the existing weight boundary
- symbol order is explicit and preserved
- durations are observation counts, not calendar-day durations
- attribution artifacts are standalone local research outputs, not configured-run artifacts

## Guardrails

Milestone 14 deliberately did not add:

- portfolio optimization
- dynamic weights
- rebalancing engines
- live or paper trading
- broker execution assumptions
- cash, financing, tax, borrow, or margin models
- covariance matrix optimization
- VaR or stress testing
- full factor models
- dashboards or databases
- broad configured-run integration
- YAML configuration changes
- broad CLI expansion
- strategy changes
- resolver changes
- plugin frameworks or dynamic loading

## Exit Criteria

Milestone 14 is complete because:

- portfolio return risk can be summarized under explicit assumptions
- drawdowns can be inspected in a deterministic local form
- symbol-level contribution can be calculated from aligned returns and static weights
- attribution outputs can be summarized in a standalone artifact
- documentation explains assumptions, limits, and what remains out of scope

## Relationship To Future Milestones

Milestone 14 prepares the project for Milestone 15 — Backtest Execution Realism Foundation.

Execution realism should wait until portfolio behavior and risk are explainable. Otherwise, more realistic execution assumptions can make results look more sophisticated without making the portfolio easier to understand.

## Current Next Step

```text
Sprint 70 — Milestone 15 Planning
```

Plan Milestone 15 before adding execution realism behavior.