# Sprint 171 — Concentration and Exposure Analysis Foundation

## Status

Implementation complete / pending Founder review.

## Objective

Add one pure domain-owned analysis boundary that derives deterministic,
immutable concentration, ordered component weight-change, declared-symbol
evidence, and active-scenario coverage results from one exact Sprint 170 source
and scenario pair.

The public entrypoint is:

```python
analyze_portfolio_review_concentration_and_exposure(
    *,
    source: PortfolioReviewSource,
    scenario_pair: PortfolioReviewScenarioPair,
) -> PortfolioReviewConcentrationExposureAnalysis
```

It cross-validates the source ID, source digest, and complete ordered component
set before calculating any result. Callers cannot pass derived financial values,
and the public result classes have no normal public construction path.

## Concentration

For each exact baseline and proposed scenario, Sprint 171 calculates:

```text
largest_component_weight = maximum component weight
largest_component_id     = first component in source order at that maximum

top_3_weight = sum of the three largest weights,
               or all weights when fewer than three components exist

herfindahl_hirschman_index = sum(weight_i ** 2)

effective_component_count = 1 / herfindahl_hirschman_index
```

The calculations consume validated Sprint 170 Python `float` weights in source
order. `math.fsum(...)` is used for the top-three and HHI sums. Explicit zero
weights participate in HHI, and source order resolves largest-weight ties.
Values are not rounded, clamped, normalized, rescaled, graded, or interpreted
as good or bad.

## Ordered Component Weight Change

Exactly one component exposure record is produced for every source component in
source order. Each record preserves the source-owned component ID, strategy ID,
and optional symbol tuple.

The exact calculations are:

```text
weight_delta    = proposed_weight - baseline_weight
baseline_active = baseline_weight > 0.0
proposed_active = proposed_weight > 0.0
```

Classification is exact over validated normalized floats:

```text
baseline == 0 and proposed > 0  -> added
baseline > 0 and proposed == 0  -> removed
proposed > baseline             -> increased
proposed < baseline             -> decreased
proposed == baseline            -> unchanged
```

`added` and `removed` take precedence. No tolerance, rounding, ranking, or
recommendation changes the classification. A numerically equal zero delta is
exported as `0.0`.

Active means only that the exact scenario weight is greater than `0.0`. It does
not mean the component is an account holding, funded allocation, position,
order, or executable exposure.

## Declared-Symbol Evidence and Coverage

Symbol evidence status is:

```text
available -> the Sprint 170 component has a validated non-empty symbol tuple
missing   -> the Sprint 170 component has symbols=None
```

Missing evidence remains `None`. Symbols are never inferred from strategy IDs,
evidence references, prose, or return columns.

Each scenario coverage result distinguishes:

- source-level metadata availability across every component; and
- active-scenario completeness across only components with weight greater than
  `0.0`.

An inactive zero-weight component with missing symbols remains visible in the
component exposure and source-level missing-evidence counts, but it does not
make active coverage incomplete. Active coverage is complete exactly when every
active component has declared symbol evidence. All component-ID tuples preserve
source order.

Declared symbols are metadata evidence only. They are not holdings, weighted
symbol exposure, market value, notional, leverage, sector or factor exposure,
tradability evidence, overlap, diversification, or a recommendation. Duplicate
symbols declared independently by different components remain independently
preserved; Sprint 171 does not combine or compare them.

## Why Return Observations Are Not Used

Aligned return observations are part of the source identity and remain required
Sprint 170 authority for later reproducible analysis. Concentration and review
exposure depend only on exact static scenario weights and declared component
metadata, so Sprint 171 does not calculate any return-based value.

Changing return observations changes the source digest and therefore the exact
analysis binding. It does not introduce portfolio returns, equity, performance,
volatility, risk, drawdown, contribution, attribution, correlation, covariance,
or proposed historical impact into the Sprint 171 payload.

## Immutability and Determinism

The result, concentration, component exposure, and universe coverage classes are
frozen derived values constructed only inside the module-owned analysis
boundary. Every export:

- preserves exact source and scenario identities;
- uses source component order;
- contains only Python scalars, lists, dictionaries, and `None`;
- is accepted by `json.dumps(..., allow_nan=False)`; and
- is identical for repeated identical normalized inputs.

Sprint 171 adds no analysis artifact ID, digest, creator, timestamp, path,
reader, writer, or file behavior. Immutable analysis and decision artifacts
belong to Sprint 173.

## Tests

Focused pure in-memory tests cover:

- two-, three-, and four-component top-three behavior;
- largest-component source-order ties;
- exact HHI and effective-component-count formulas;
- equal weights, zero weights, and no rounding or clamping;
- all five exact weight-change classifications in one scenario pair;
- exact deltas, active flags, component order, strategy IDs, and symbols;
- available and missing symbol evidence;
- source-level and active-scenario coverage counts and ordered IDs;
- inactive missing-symbol behavior and duplicate symbol preservation;
- input non-mutation and result immutability;
- constructor protection, exact factory signature, and JSON compatibility;
- source ID, digest, and component-order cross-validation;
- materially changed weights versus changed return observations; and
- deterministic repeated exports.

All identities, symbols, evidence, weights, and return observations are
synthetic. Tests use no network, filesystem artifact I/O, database, API, Web,
Docker runtime, account, market, order, execution, broker, or wall-clock state.

## Preserved Boundaries and Handoff

Sprint 171 intentionally adds no:

- unique or shared symbol union, overlap count, Jaccard, or overlap matrix;
- correlation, covariance, return interaction, or candidate interaction;
- weighted portfolio return, equity, performance, volatility, risk, drawdown,
  contribution, attribution, or proposed historical impact;
- optimizer, normalization, allocation, ranking, recommendation, or winner;
- analysis or decision artifact, digest, path, reader, or writer;
- persistence, migration, application service, API, OpenAPI, Web, or Demo;
- lifecycle, Paper Job, Paper Account, cash, position, order, fill, fee, ledger,
  market-data, calendar, clock, execution, worker, scheduler, queue, broker,
  QMT, MiniQMT, private-edge, live, or real-money behavior.

Migration head remains:

```text
0005_paper_job_result_references
```

Milestone 30 remains In Progress. After Sprint 171 is merged, the next
implementation sprint is:

```text
Sprint 172 — Strategy Interaction and Proposed Portfolio Impact Foundation
```

Sprint 172 owns approved symbol overlap, return interaction, baseline/proposed
historical portfolio behavior, and proposed-impact calculations. Sprint 173 owns
immutable analysis and human-decision artifacts; Sprint 174 owns persistence,
application services, migration, and API; Sprint 175 owns the bilingual Web;
Sprint 176 owns integration, Demo, and acceptance hardening; Sprint 177 owns
closeout and the strict M31 handoff.
