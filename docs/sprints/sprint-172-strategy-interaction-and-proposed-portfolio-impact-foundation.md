# Sprint 172 — Strategy Interaction and Proposed Portfolio Impact Foundation

## Status

Implementation complete / pending Founder review.

## Objective

Add one pure domain-owned analysis boundary that derives deterministic,
immutable historical interaction, baseline/proposed behavior, and exact
proposed-impact evidence from one validated Sprint 170 source and scenario pair.

The public entrypoint is:

```python
analyze_portfolio_review_interaction_and_impact(
    *,
    source: PortfolioReviewSource,
    scenario_pair: PortfolioReviewScenarioPair,
) -> PortfolioReviewInteractionImpactAnalysis
```

It reconstructs the exact source observation table only in memory,
cross-validates the exact source and scenario authority, and does not accept any
caller-authored derived metric.

## Pair Ordering and Declared-Symbol Overlap

Unique unordered component pairs follow exact source order:

```text
(component_1, component_2)
(component_1, component_3)
...
(component_n-1, component_n)
```

When both components have authoritative Sprint 170 symbol tuples, shared
symbols preserve the left component's order. Shared and union counts produce
the exact Jaccard value. Disjoint available sets remain valid zero overlap.

If either symbol tuple is missing, the pair is explicitly unavailable with
`missing_symbol_evidence`. Missing component IDs remain in pair order and all
calculated overlap fields are `None`; missing evidence is never interpreted as
an empty symbol set.

## Historical Return Interaction

Pairwise interaction uses the exact shared Sprint 170 observation window. The
Pearson calculation is:

```text
left_mean  = arithmetic mean of left returns
right_mean = arithmetic mean of right returns

numerator = sum((left_i - left_mean) * (right_i - right_mean))
left_ss   = sum((left_i - left_mean) ** 2)
right_ss  = sum((right_i - right_mean) ** 2)

correlation = numerator / sqrt(left_ss * right_ss)
```

Deterministic finite arithmetic uses `math.fsum(...)`. No sorting, joining,
filling, dropping, resampling, tolerance-based variance classification, or
window repair occurs. When either centered sum of squares is exactly zero,
correlation is unavailable with `zero_variance`, the exact constant-series
identities, and `correlation=None`. Non-finite placeholders are never exported.

The candidate interaction uses the proposed scenario's exact
`proposed_component_id` and correlates that component return stream with the
existing-authority baseline static-weight portfolio return stream. The
candidate is not removed or residualized when it already has positive baseline
weight. Candidate weight and self-inclusion are historical scenario context,
not independent alpha or diversification evidence.

## Baseline and Proposed Historical Behavior

Both scenarios use identical source timestamps, component order, return
observations, and evaluation assumptions. Scenario weights come only from the
validated pair.

Sprint 172 reuses:

```text
weighted_portfolio_return(...)
portfolio_risk_summary(...)
equity_curve(..., initial_capital=1.0)
inspect_portfolio_drawdown(...)
symbol_contribution_returns(...)
summarize_symbol_contributions(...)
```

Each behavior result exposes observation identity, arithmetic mean, existing
sample and optional annualized volatility, min/max return, positive/negative/
zero period counts, loss rate, ending compounded equity, cumulative return,
worst-drawdown context, and one contribution row per source component.

Zero-weight components remain visible with zero contribution and all periods
counted as zero. Drawdown dates, recovery state, and durations preserve existing
domain meaning. Before equity or drawdown calculation, any scenario portfolio
period return at or below `-1.0` fails explicitly.

No mutable pandas return or equity series appears in a public result.

## Exact Proposed Impact

Every compatible scalar and component contribution impact is literally:

```text
proposed value - baseline value
```

No rounding, inversion, percentage formatting, ranking, or qualitative
improved/worsened label is applied. This includes the existing negative
max-drawdown number. Annualized volatility impact is `None` when the source has
no periods-per-year assumption. Drawdown dates and recovery context remain
side-by-side in the two behavior records.

## Immutability and Determinism

All derived public result classes are frozen and constructor protected. The
module-owned factory is their only normal construction path. Caller sources,
scenarios, observations, components, weights, and symbols are not mutated.

Every export preserves source order, uses only JSON-compatible Python values,
canonicalizes numerical zero, rejects non-finite derived values, and passes:

```python
json.dumps(payload, allow_nan=False)
```

Sprint 172 adds no analysis ID, digest, creator, timestamp, decision identity,
or artifact path. Sprint 173 owns authoritative analysis and decision
artifacts.

## Tests

Focused synthetic pure in-memory tests cover:

- two-, three-, and twelve-component pair count and ordering;
- partial, full, disjoint, and missing-evidence symbol overlap;
- perfect, nontrivial, zero-variance, and near-constant correlation;
- candidate zero weight, self-inclusion, and constant-series behavior;
- existing return, risk, equity, drawdown, and contribution authority reuse;
- optional annualization and positive/recovered/unrecovered drawdown context;
- rejection of scenario returns at or below `-1.0`;
- exact scalar and component proposed-minus-baseline deltas;
- source and scenario authority validation;
- constructor protection, immutability, input isolation, deterministic export,
  and strict JSON compatibility; and
- absence of artifact, persistence, API, Web, M31, private-edge, broker, and
  live fields.

All identities, symbols, returns, and weights are synthetic. Tests use no
network, artifact I/O, database, API, Web, Docker runtime, broker, QMT, private
data, real universe, or wall-clock-dependent value.

## Preserved Boundaries and Handoff

These results are descriptive historical scenario evidence. They are not a
forecast, expected alpha, profitability claim, diversification advice,
investment recommendation, capital allocation, account holding, order, or
execution instruction.

Sprint 172 adds no artifact or decision contract, digest, file I/O, persistence,
migration, application service, API, OpenAPI, generated TypeScript, Web, Demo,
Docker, lifecycle, Paper Job, Paper Account, market, order, execution, worker,
scheduler, private trading edge, broker, QMT, MiniQMT, live, or real-money
capability.

Migration head remains:

```text
0005_paper_job_result_references
```

Milestone 30 remains In Progress. After Sprint 172 is merged, the next
implementation sprint is:

```text
Sprint 173 — Portfolio Review Artifact and Human Decision Foundation
```

Sprint 173 may compose the exact Sprint 171 and Sprint 172 domain results into
immutable analysis and decision evidence. Persistence and API remain Sprint
174; Web remains Sprint 175; integration and Demo remain Sprint 176; closeout
and the strict M31 handoff remain Sprint 177.
