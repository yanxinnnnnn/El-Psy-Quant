# Sprint 170 — Portfolio Review Input and Scenario Contract Foundation

## Status

Implementation complete / pending Founder review.

## Objective

Establish the first runtime boundary of Milestone 30 as immutable,
deterministic, in-memory contracts for:

```text
portfolio review evidence pointers
  -> ordered strategy components
  -> exact aligned historical return observations
  -> one validated portfolio review source
  -> explicit baseline and proposed static scenarios
```

This sprint creates reproducible input authority for later analysis. It does not
perform portfolio analysis, artifact I/O, persistence, API or Web work, or
Paper Account behavior.

## Contract Boundary

The public package is:

```python
from el_psy_quant.portfolio_review import ...
```

It exports version constants, supported evidence-reference types, immutable
classes, and factories for:

```text
PortfolioReviewEvidenceReference
PortfolioReviewComponent
PortfolioReviewReturnObservation
PortfolioReviewSource
PortfolioReviewBaselineScenario
PortfolioReviewProposedScenario
PortfolioReviewScenarioPair
```

### Evidence references

An evidence reference is a pointer only. Its supported types are bounded to the
approved research, portfolio, governance, report, and lifecycle evidence
identities. Required strings are stripped and non-empty; optional blank strings
become `None`.

The contract does not discover, open, parse, validate, score, or rank the
referenced record.

### Components

Each component has one normalized `component_id`, one `strategy_id`, and an
ordered immutable evidence-reference tuple. At least one reference must have an
approved research origin. Duplicate `(reference_type, reference_id)` identities
inside one component are invalid.

`symbols=None` explicitly means symbol or universe evidence is unavailable.
Supplied symbols pass through the existing `build_symbol_universe(...)`
authority, so they are normalized, unique, immutable, and order-preserving. No
symbol is inferred from labels, IDs, or evidence prose.

### Return observations and source

The source factory consumes one already-aligned pandas `DataFrame`. It requires:

- 2–12 ordered components with unique component IDs;
- a `DatetimeIndex` with at least three strictly increasing unique timestamps;
- columns matching component IDs exactly and in exact component order;
- numeric, finite, non-boolean, non-missing returns; and
- no automatic join, sort, fill, drop, resample, or other alignment repair.

The DataFrame is converted into immutable timestamped observation rows. The
source does not retain the DataFrame as hidden mutable authority. Every return is
a Python `float`; negative zero becomes canonical `0.0`.

Evaluation frequency and creator are required. Optional periods per year is
either `None` or a positive finite Python `float`. The created timestamp must be
timezone-aware and is normalized to UTC. Assumptions, warnings, and
missing-evidence notes are stripped immutable tuples that preserve caller order
and duplicate prose.

Aligned returns are required because summary metrics cannot reproduce later
interaction, portfolio behavior, contribution, or proposed-impact calculations.
Sprint 170 accepts exact observations without calculating any of those results.

## Scenario Boundary

Baseline and proposed scenarios reference one exact source ID and source digest.
Each stores the complete component-weight set in source order.

Weights:

- must have exactly the source component IDs;
- are finite, numeric, non-boolean, and non-negative;
- may explicitly equal `0.0`;
- require at least one positive value;
- sum to `1.0` using the established absolute tolerance of `1e-12`; and
- are never normalized, scaled, optimized, proposed, or rounded.

The scenario pair requires distinct scenario IDs, matching source identity,
matching ordered component identity, at least one real weight change, and a real
weight change for the declared proposed component.

Scenario weights are review assumptions. They are not current holdings, account
cash, capital allocation, positions, orders, fills, ledger entries, or executable
instructions.

## Immutability and Determinism

All public value objects are frozen dataclasses. Caller sequences, mappings, and
DataFrames are copied into immutable normalized tuples or scalar values. Later
caller mutation cannot change a created source or scenario.

Source and scenario digests are SHA-256 over the exact normalized payload,
excluding the digest field itself. Canonical JSON uses:

```python
json.dumps(
    payload_without_digest,
    allow_nan=False,
    ensure_ascii=False,
    separators=(",", ":"),
    sort_keys=True,
)
```

UTF-8 encoding and lowercase hexadecimal output complete the digest contract.
Component and observation order remain material. Every export is strictly
JSON-compatible through `json.dumps(..., allow_nan=False)`.

Digest generation is pure in-memory behavior. Filesystem paths, artifact
contents, databases, API requests, environment values, and wall-clock state do
not participate.

## Tests

Focused deterministic tests cover:

- all supported and unsupported evidence types;
- string, symbol, evidence, and component normalization;
- research-origin and duplicate-evidence rules;
- immutable objects and caller-input isolation;
- 2- and 12-component source boundaries;
- exact three-observation acceptance;
- DataFrame type, index, order, dtype, finite-value, and missing-value failures;
- evaluation and UTC audit validation;
- strict JSON export and material source-digest changes;
- ordered strict baseline and proposed weights;
- zero-weight add/remove scenarios;
- scenario digest determinism;
- source, ID, ordered component, real-change, and proposed-component pair rules;
  and
- invalid numeric, missing, extra, non-normalized, and unchanged scenarios.

No test uses network access, artifact I/O, SQLite, migrations, FastAPI, Next.js,
Docker, a broker, QMT, or wall-clock-dependent values.

## Preserved Boundaries

Sprint 170 adds no:

- concentration, exposure, weight-delta, overlap, correlation, covariance,
  portfolio return, risk, drawdown, contribution, or proposed-impact calculation;
- analysis or decision artifact;
- artifact path, reader, writer, index, or filesystem behavior;
- persistence model, repository, migration, application service, API, OpenAPI,
  generated TypeScript, Web, Demo, Docker, worker, scheduler, or queue behavior;
- lifecycle, Paper Job, Paper Account, cash, position, order, fill, fee, ledger,
  reconciliation, market-data, calendar, clock, execution, broker, QMT, MiniQMT,
  live, or real-money behavior; or
- strategy ranking, recommendation, optimization, allocation, or approval.

Migration head remains:

```text
0005_paper_job_result_references
```

M30 remains In Progress. After this sprint is merged, the next implementation
sprint is:

```text
Sprint 171 — Concentration and Exposure Analysis Foundation
```

S171 may calculate the explicitly approved concentration and review-exposure
evidence from these contracts. Interaction and proposed impact remain S172 work;
artifacts remain S173; persistence and API remain S174; Web remains S175;
integration remains S176; and closeout/M31 handoff remains S177.
