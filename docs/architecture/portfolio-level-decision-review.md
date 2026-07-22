# Portfolio-Level Decision Review Architecture

## Status

**Implemented and accepted through Milestone 30.**

This document records the completed architecture. Formal closeout:

```text
docs/closeouts/milestone-030-portfolio-level-decision-review-foundation-closeout.md
```

## Purpose

Milestone 30 adds one explicit portfolio-aware review layer before stateful Paper
Account and market-driven runtime work begins.

The Founder can inspect how an explicit proposed strategy/component and static
scenario would have changed historical portfolio evidence, then record one
separate human decision.

M30 does not allocate capital, approve execution, mutate an account, generate
orders, simulate fills, or start a runtime.

## Architecture Overview

```text
Browser
  -> Next.js Founder Workspace
  -> fixed same-origin /api/backend gateway
  -> versioned FastAPI API
  -> thin portfolio-review application services
  -> portfolio-review domain modules and artifact readers/writers
  -> compact SQLite workflow state + authoritative artifact files
```

### Authority split

- Domain modules own validation and quantitative/governance calculations.
- Full source, analysis, and decision payloads are authoritative files.
- SQLite owns compact metadata, idempotency, status, version, and references.
- FastAPI owns the versioned transport boundary.
- The Web owns bilingual presentation and explicit draft composition only.
- Human decisions remain governance evidence.
- Standard and Demo storage remain isolated.

No competing browser, SQL, report-prose, or Demo-only financial authority exists.

## Core Objects

```text
PortfolioReviewSource
PortfolioReviewComponent
PortfolioReviewEvidenceReference
PortfolioReviewReturnObservation
PortfolioReviewBaselineScenario
PortfolioReviewProposedScenario
PortfolioReviewAnalysisArtifact
PortfolioReviewDecisionArtifact
PortfolioReviewRecord
```

## Review Source Contract

A source contains:

- one normalized source ID;
- 2–12 unique ordered components;
- one normalized component and strategy ID per component;
- one or more supported evidence references per component;
- at least one research-origin reference per component;
- optional non-empty authoritative symbols;
- at least three ordered aligned return observations;
- exactly one finite return per component per timestamp;
- evaluation frequency and optional periods per year;
- creator and timezone-aware creation timestamp;
- assumptions, warnings, and missing evidence; and
- a canonical digest.

The source is explicit. The product does not join, fill, sort, resample, infer, or
reconstruct aligned returns from summary metrics or unrelated records.

## Evidence References

Supported evidence types are a closed product vocabulary. References preserve:

```text
reference_type
reference_id
optional label
optional description
```

Exact duplicate `(reference_type, reference_id)` values are refused inside one
component. Evidence pointers do not imply automatic dereferencing, return
import, candidate selection, approval, or execution authority.

Existing research-run and evidence-manifest APIs may supply exact metadata and
compatible pointers after explicit Founder selection. Unsupported references
remain visible but cannot be silently mapped.

## Scenario Contract

Baseline and proposed scenarios:

- bind to the exact source;
- have distinct normalized scenario IDs;
- use every source component exactly once in source order;
- use finite non-negative static weights;
- require at least one positive weight;
- sum to `1.0` within absolute tolerance `1e-12`;
- include explicit rationale, assumptions, and warnings;
- require at least one changed weight; and
- require the explicit proposed component's own weight to change.

No automatic normalization, optimization, recommendation, ranking, allocation,
dynamic rebalancing, or target holding generation occurs.

## Quantitative Analysis

### Concentration and review exposure

For baseline and proposed scenarios, the domain calculates:

- largest component and weight;
- top-three weight;
- Herfindahl-Hirschman index;
- effective component count;
- ordered baseline/proposed weights and exact deltas;
- added, removed, increased, decreased, or unchanged classification;
- active flags; and
- source and active-scenario symbol-evidence coverage.

Declared symbols are review evidence. They are not runtime holdings, market value,
notional, leverage, margin, or broker exposure.

### Symbol overlap and return interaction

For every unique unordered component pair in source order, the domain exposes:

- symbol overlap availability;
- shared symbols and counts;
- union count;
- Jaccard overlap;
- pairwise Pearson historical correlation; and
- exact missing/undefined evidence reasons.

It also calculates the explicit proposed component's correlation to the baseline
portfolio using the exact aligned historical window and baseline weights.

Zero variance or missing evidence produces an explicit unavailable result, never
`NaN`, infinity, or fabricated zero.

### Historical behavior and proposed impact

The domain reuses existing portfolio return, risk, equity, drawdown, and
contribution authority to compare baseline and proposed historical scenarios.

Supported evidence includes:

- observation count and window identity;
- mean return and volatility;
- optional annualized volatility;
- loss rate and min/max period return;
- ending equity and cumulative return;
- worst drawdown context;
- ordered component contribution; and
- exact scalar and contribution deltas as `proposed - baseline`.

Results are historical scenario evidence only. They are not forecasts,
profitability claims, expected alpha, rankings, recommendations, or investment
advice.

## Artifact Authority

Logical artifact classes:

```text
portfolio review source
portfolio review analysis
portfolio review decision
```

Files are:

- versioned;
- deterministic and strictly JSON-compatible;
- digest-protected;
- written once under fixed server-owned hashed paths;
- reopened through strict schemas and cross-validation; and
- never overwritten by a conflicting request.

Analysis reopen reconstructs the source and scenarios and recalculates derived
M30 evidence. Decision reopen reconstructs the exact analysis relationship.

Raw caller IDs never become filesystem path fragments. No API accepts an
arbitrary path.

## Persistence Architecture

SQLite stores one compact `portfolio_reviews` record per review with:

- record and artifact schema versions;
- review, source, scenario, proposed-component, analysis, and decision identity;
- digests and safe relative artifact paths;
- create and decision idempotency bindings and command digests;
- workflow status and outcome;
- actor and UTC timestamps; and
- optimistic version state.

SQLite does not store full return observations, full analysis results, matrices,
contributions, full decision payloads, balances, positions, orders, fills, fees,
or ledger entries.

Concurrent conflicting decisions use a conditional status/version update so one
settlement wins. A losing request cannot overwrite files or durable state.

Migration chain:

```text
0001_product_baseline
  -> 0002_artifact_index
  -> 0003_paper_jobs
  -> 0004_paper_job_recovery_audit
  -> 0005_paper_job_result_references
  -> 0006_portfolio_reviews
```

The installed project wheel owns the Alembic migration resources used by the
runtime-only backend image.

## Application and API Architecture

Application services own transaction boundaries and file/database ordering.
Routes remain thin and translate stable domain/application failures to bounded
public error codes.

Exact API:

```text
POST /api/v1/portfolio-reviews
GET  /api/v1/portfolio-reviews
GET  /api/v1/portfolio-reviews/{review_id}
POST /api/v1/portfolio-reviews/{review_id}/decision
```

Both POST routes require explicit caller-supplied idempotency keys and distinguish
created from replayed outcomes. Reads reopen authoritative artifacts rather than
trusting stale duplicated payloads.

No update, delete, recommendation, optimization, source-discovery, import,
lifecycle bridge, account bridge, or execution route exists.

## Founder Web Architecture

Routes:

```text
/portfolio-reviews
/portfolio-reviews/new
/portfolio-reviews/[reviewId]
```

The Web provides complete English and Simplified Chinese presentation for:

- loading, empty, available, partial, stale, failed, invalid, conflict, awaiting,
  and settled states;
- raw IDs, statuses, versions, digests, timestamps, values, and error codes;
- exact backend ordering and duplicate visibility;
- a complete manual source/scenario builder;
- explicit research/evidence composition;
- entered weight totals without normalization;
- authoritative analysis and unavailable evidence; and
- one explicit governance-only decision.

Drafts are not stored in URLs, cookies, logs, analytics, or browser storage.
Integration read failures do not disable valid manual submission.

## Demo Architecture

Demo dataset/descriptor v2:

- uses a separate Compose project and volume;
- validates one exact synthetic source before installation;
- seeds one exact durable review through existing authority;
- exposes one path-free explicit create prefill;
- requires replace confirmation;
- never auto-submits or decides;
- replays exactly through the normal create service;
- preserves a valid later decision; and
- never writes to Standard storage.

The read-only verifier includes portfolio-review list/detail checks and issues no
portfolio-review mutation.

## Observability and Error Boundary

Portfolio-review events contain bounded operation, route, request, review,
decision, status, and outcome identity only.

They exclude:

- credentials and authentication material;
- request/response bodies;
- idempotency keys;
- return observations and weights;
- financial payloads;
- filesystem paths;
- SQL;
- exception text and tracebacks; and
- artifact contents.

Known migration-resource absence fails before database mutation, Demo
installation, or serving with a bounded safe identity.

## Human-Control Boundary

An M30 decision does not:

- change strategy lifecycle automatically;
- approve a Paper Job;
- create or fund a Paper Account;
- reserve or allocate cash;
- create positions, orders, fills, fees, or ledger entries;
- trigger a worker or scheduler; or
- imply broker or live readiness.

A later milestone may reference an approved M30 review only through a separately
approved contract.

## Accepted Runtime Boundary

Founder acceptance confirmed:

- preserved Standard 0005-to-0006 upgrade;
- Standard verification and non-mutating smoke;
- Standard remains unseeded;
- Demo v2 seeded review and explicit prefill;
- exact create/replay and authoritative detail;
- explicit decision persistence across restart;
- return-to-Standard isolation; and
- bilingual browser behavior with unchanged raw truth.

## M31 Handoff

M31 must create a separate durable Paper Account and ledger source of truth.

M30 scenario weights remain review assumptions. M30 decisions remain governance
evidence. Neither may become cash, positions, available capital, orders, fills,
fees, or ledger events by implication.

M31 planning must decide account identity, ledger entries, funding and adjustment
semantics, order/fill persistence boundaries, fees, concurrency, idempotency,
snapshots, reconciliation, derived balances, evidence links, migrations, API,
Web, Demo, and acceptance before implementation begins.

## Explicit Non-goals

M30 does not add:

- automatic strategy approval, ranking, recommendation, or optimization;
- capital allocation or dynamic rebalancing;
- account, cash, position, fee, order, fill, or ledger truth;
- market-data replay, trading calendar, or session clock;
- strategy-to-order generation or pre-trade order risk;
- execution simulation;
- worker, scheduler, queue, checkpoint, or multi-day runtime;
- broker, QMT, MiniQMT, private-edge, live, or real-money behavior;
- distributed infrastructure; or
- public SaaS or multi-tenancy.