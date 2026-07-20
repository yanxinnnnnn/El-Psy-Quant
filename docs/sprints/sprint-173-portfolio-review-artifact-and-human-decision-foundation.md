# Sprint 173 — Portfolio Review Artifact and Human Decision Foundation

## Status

Implementation complete / pending Founder review.

## Objective

Freeze the immutable in-memory payload authority for one portfolio review
analysis, one separate human governance decision linked to that exact analysis,
and compact digest-bearing references to source, analysis, and decision
artifacts.

Sprint 173 composes the merged Sprint 170–172 authority. It does not add
artifact files, persistence, application services, API or Web behavior, or any
Paper Account or execution capability.

## Authority Separation

The three payload authorities remain distinct:

```text
PortfolioReviewSource
  -> exact component identity and aligned historical return observations

PortfolioReviewAnalysisArtifact
  -> exact reviewed scenarios and internally calculated S171/S172 evidence

PortfolioReviewDecisionArtifact
  -> one human governance outcome linked to the exact analysis digest
```

The analysis references the source ID and source digest but does not duplicate
the source's aligned return observations. The source therefore remains the only
authority for the historical input table.

The analysis contains the complete baseline and proposed scenario payloads
because their ordered static weights, rationale, assumptions, and warnings are
the reviewed scenario assumptions. These values are not holdings, capital
allocation, or executable instructions.

The decision contains copied review, source, and scenario identities plus the
exact analysis digest. It does not embed, rewrite, or mutate the analysis.

## Analysis Artifact

The public factory is:

```python
create_portfolio_review_analysis_artifact(
    *,
    review_id,
    source,
    scenario_pair,
    created_by,
    created_timestamp,
    assumptions=(),
    warnings=(),
    missing_evidence=(),
)
```

It accepts only the exact public Sprint 170 source and scenario-pair types,
cross-validates source ID, source digest, and complete component order, and
internally calls both approved factories:

```text
analyze_portfolio_review_concentration_and_exposure
analyze_portfolio_review_interaction_and_impact
```

It then verifies that both derived results preserve the source, component,
scenario, and proposed-component authority. No caller can supply concentration,
exposure, overlap, correlation, behavior, drawdown, contribution, impact, or
digest values.

The fixed evidence scope is:

```text
historical_scenario_evidence
```

It identifies descriptive historical scenario evidence, not forecast
performance, expected alpha, a recommendation, capital allocation, investment
advice, or an execution instruction.

All artifact and nested calculated result objects are immutable. The analysis
does not retain or export a mutable pandas `DataFrame` or `Series`.

## Human Decision Artifact

The public decision factory accepts one exact analysis artifact and exactly one
of:

```text
approved
rejected
deferred
```

It requires a decision ID, rationale, reviewer identity, and timezone-aware
reviewed timestamp. Notes and warnings remain ordered immutable human prose.

The fixed decision scope is:

```text
portfolio_review_governance_only
```

`approved` means approved as portfolio-review governance evidence only. It does
not change lifecycle state, approve a Paper Job, create or fund a Paper Account,
reserve cash, create positions or orders, start a worker, or authorize broker,
QMT, MiniQMT, live, or real-money execution.

Sprint 173 is a pure payload contract and cannot enforce that a review has only
one settled decision. Durable one-winner settlement, idempotency, conflict
handling, and concurrency belong to Sprint 174.

## Canonical Digests and UTC Audit Identity

Analysis and decision digests use their complete normalized export payload,
excluding the digest field itself:

```python
json.dumps(
    payload_without_digest,
    allow_nan=False,
    ensure_ascii=False,
    separators=(",", ":"),
    sort_keys=True,
)
```

The UTF-8 bytes are hashed with SHA-256 and exported as lowercase hexadecimal
text. No digest includes itself. Ordering remains material.

Creation and review timestamps must be timezone-aware and normalize to UTC
before export and digest calculation. Equivalent timezone representations of
the same instant therefore produce the same digest. No path, file metadata,
database state, environment value, API request, wall clock, or mutable object
participates.

## Artifact References

`PortfolioReviewArtifactReference` supports exactly:

```text
portfolio_review_source
portfolio_review_analysis
portfolio_review_decision
```

Each immutable reference contains an artifact type, artifact ID, artifact
digest, and optional descriptive label and description. Typed helpers copy:

```text
source   -> source_id / source_digest
analysis -> review_id / analysis_digest
decision -> decision_id / decision_digest
```

References contain no filesystem path, URL, artifact root, database ID, or
mutable payload. They do not discover, resolve, load, parse, or validate files.

## Tests

Focused deterministic tests use only synthetic identities, actors, evidence,
symbols, returns, weights, notes, and decisions. They cover:

- all reference types, helpers, normalization, digest validation, immutability,
  JSON compatibility, and path-free semantics;
- valid 2- and 12-component analysis construction;
- exact internal S171/S172 composition and identity preservation;
- explicit unavailable symbol/correlation evidence;
- source-observation separation and absence of retained mutable pandas values;
- UTC normalization and equivalent-instant digest identity;
- canonical analysis and decision digest behavior;
- constructor protection, frozen nested results, and caller-input isolation;
- invalid source, pair, component order, audit, prose, timestamp, outcome, and
  caller-override inputs;
- all three exact human outcomes and governance-only scope; and
- deterministic repeated decisions without hidden settlement state.

Tests use no network, artifact I/O, SQLite, migration execution, FastAPI,
OpenAPI, Next.js, Docker runtime, broker, QMT, private data, real universe, or
wall-clock-dependent values.

## Preserved Boundaries and Handoff

Sprint 173 adds no:

- artifact filename, path, root, traversal, symlink, containment, reader,
  writer, collision, reopen, or filesystem behavior;
- SQLite model, repository, migration, idempotency, concurrency, or settlement;
- application service, API, OpenAPI, generated TypeScript, Web, Demo, or Docker
  behavior;
- lifecycle mutation, Paper Job, Paper Account, cash, position, market, order,
  fill, fee, ledger, execution, worker, scheduler, broker, QMT, MiniQMT, private
  trading edge, live, or real-money capability; or
- optimization, normalization, ranking, recommendation, capital allocation,
  forecast, expected-alpha, or investment-advice semantics.

Migration head remains:

```text
0005_paper_job_result_references
```

Milestone 30 remains In Progress. After Sprint 173 is merged, the next
implementation sprint is:

```text
Sprint 174 — Durable Portfolio Review Persistence and Application/API Foundation
```

Sprint 174 owns safe artifact I/O, compact SQLite metadata, application
services, idempotency, settlement, concurrency, migration, and versioned API.
Sprint 175 owns the bilingual Founder Web workflow; Sprint 176 owns integration,
Demo, and acceptance hardening; Sprint 177 owns closeout and the strict M31
handoff.
