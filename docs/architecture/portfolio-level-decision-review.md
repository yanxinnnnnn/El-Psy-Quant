# Portfolio-Level Decision Review Architecture

## Status

Approved planning architecture for Milestone 30.

Sprint 169 is documentation-only. No M30 runtime capability exists until the
subsequent implementation sprints are merged and accepted.

## Purpose

Milestone 30 adds one explicit portfolio-aware review layer before stateful Paper
Account and market-driven runtime work begins.

The Founder should be able to answer:

```text
What portfolio scenario is being reviewed?
Which strategies and evidence are included?
Where is concentration located?
What exposure and universe overlap exist?
How do the strategy return streams interact?
How would the proposed scenario have changed historical portfolio behavior?
Which assumptions and warnings limit the conclusion?
What explicit human decision was recorded?
```

The architecture is designed to improve human judgment. It is not an optimizer,
recommendation engine, allocation engine, account ledger, order pipeline, or
execution runtime.

## Audited Starting Point

### Portfolio calculation foundations

Milestones 13 and 14 already provide deterministic domain helpers for:

- aligned strategy-return inputs;
- equal-weight and caller-supplied static-weight portfolio returns;
- strict non-negative weights summing to `1.0`;
- portfolio performance summaries;
- portfolio return distribution and loss-frequency summaries;
- worst drawdown inspection;
- static-weight symbol contribution; and
- standalone portfolio and attribution summary artifacts.

Those foundations are intentionally static. They do not provide optimization,
dynamic rebalancing, account holdings, factor exposure, VaR, stress testing, or
runtime execution.

### Governance foundations

Milestones 20–24 provide local immutable contracts for:

- research-to-paper promotion evidence;
- Paper Run comparison and review;
- strategy-level decision governance;
- report artifact packaging; and
- non-executing lifecycle proposals and human reviews.

Those contracts establish useful identity, reference, rationale, actor,
timestamp, warning, and immutable-record conventions. Most summary facts are
caller supplied. M30 must reuse their governance semantics without reducing
portfolio analysis to caller-written prose.

### Product and persistence foundations

Milestones 26–29 provide:

```text
Browser
  -> Next.js Founder Workspace
  -> fixed same-origin /api/backend gateway
  -> versioned FastAPI API
  -> thin application services
  -> domain modules and artifact readers
  -> isolated SQLite and authoritative artifact roots
```

SQLite currently owns compact artifact index and Paper Job operational metadata.
Completed files own full artifact payloads. The Web does not calculate financial
truth.

### Identified data gap

Configured research runs currently expose manifest and summary-metric artifacts.
They do not preserve or expose the aligned strategy return observations needed to
reproduce portfolio interaction and proposed-impact calculations.

M30 therefore requires a new explicit review-source artifact boundary. It must
not fabricate interaction from summary metrics or silently connect unrelated
runs.

## Product Model

### Portfolio review source

A `PortfolioReviewSource` is one immutable, versioned, digestible input package
containing the data and references required to reproduce a review.

It contains at minimum:

- stable source ID;
- ordered component definitions;
- strategy/component identity;
- explicit research and governance evidence references;
- ordered aligned return observations for every component;
- one shared `DatetimeIndex`-equivalent timestamp sequence;
- evaluation frequency and optional periods-per-year assumption;
- component symbol/universe coverage where authoritative;
- source creator and UTC timestamp;
- assumptions, warnings, and missing-evidence notes;
- schema version; and
- deterministic payload digest.

The source artifact may be produced by an explicit local importer, CLI, or
approved programmatic writer. It is not discovered automatically by the browser.
Existing research runs are not retroactively declared compatible merely because
they have summary metrics.

### Portfolio component

A component is one explicitly identified strategy return stream used in a review.
For the first M30 version:

- components are strategy-level review inputs, not runtime positions;
- component order is explicit and stable;
- every component has a unique component ID within one source;
- every component has one finite aligned historical return observation per source
  timestamp;
- every component may declare an ordered symbol/universe set when supported by
  evidence; and
- missing symbol metadata remains visible rather than inferred.

A component is not an account position, order, fill, broker instrument, or capital
reservation.

### Baseline scenario

A baseline scenario is the Founder's explicit description of the portfolio before
the proposed decision.

It contains:

- stable scenario ID;
- source ID and source digest;
- ordered component weights;
- rationale;
- assumptions and warnings; and
- exact evaluation identity inherited from the source.

### Proposed scenario

A proposed scenario uses the same source, timestamps, and evaluation assumptions
as the baseline but changes at least one explicit component weight.

It additionally identifies the proposed strategy/component under review.

The first version supports a bounded union of at most 12 components across the
baseline and proposed scenarios. Each scenario contains at least one positive
weight. Weight keys must match the approved scenario component set exactly,
weights must be finite and non-negative, and each scenario must sum to `1.0`
through the existing strict weight-validation boundary. No automatic scaling is
performed.

A component absent from one scenario may be represented explicitly with weight
`0.0` when the scenario contract requires a common ordered union. Hidden missing
keys are not treated as zero.

### Portfolio review analysis

A review analysis is immutable financial and contextual evidence calculated from
one source, one baseline scenario, and one proposed scenario.

It contains:

- stable review ID;
- exact source/scenario identities and digests;
- concentration summaries;
- review-exposure and universe-overlap summaries;
- strategy interaction evidence;
- baseline and proposed portfolio summaries;
- baseline-versus-proposed deltas;
- contribution/attribution context;
- assumptions, warnings, missing evidence, and sample limitations;
- calculation/schema versions;
- creator and UTC timestamp; and
- deterministic analysis digest.

### Portfolio review decision

A decision is a separate immutable human governance artifact linked to one exact
analysis digest.

Supported outcomes are exactly:

```text
approved
rejected
deferred
```

A decision contains:

- stable decision ID;
- review ID and analysis digest;
- outcome;
- required human rationale;
- reviewer identity;
- reviewed UTC timestamp;
- notes and warnings; and
- schema version and deterministic digest.

`approved` means approved as portfolio-review governance evidence only.

A review has at most one settled decision in M30. Reconsideration, changed
weights, changed evidence, or changed assumptions require a new review identity.
Settled analysis and decision artifacts are never overwritten.

## Quantitative Boundary

## Input validation

The source calculation boundary requires:

- at least three aligned observations;
- a monotonic, unique timestamp sequence;
- one exact timestamp sequence for all components;
- no missing, non-numeric, boolean, infinite, or NaN returns;
- unique nonblank component IDs;
- deterministic component and timestamp order;
- an explicit positive periods-per-year value when annualized values are
  requested; and
- immutable caller inputs.

A constant return series is valid evidence but makes Pearson correlation
undefined. The analysis must return an explicit unavailable value and warning,
not `NaN`, infinity, or a fabricated zero correlation.

## Concentration

For each scenario, calculate at minimum:

```text
largest_component_weight
largest_component_id
top_3_weight
herfindahl_hirschman_index
effective_component_count
```

Definitions:

```text
top_3_weight = sum of the three largest weights,
               or all weights when fewer than three components exist

herfindahl_hirschman_index = sum(weight_i ** 2)

effective_component_count = 1 / herfindahl_hirschman_index
```

Also expose ordered per-component weight deltas:

```text
proposed_weight - baseline_weight
```

The product must not label lower concentration as automatically better or higher
concentration as automatically unacceptable.

## Review exposure

M30 uses the term **review exposure** narrowly.

It means:

- static strategy/component weights in the reviewed scenarios;
- added, removed, increased, decreased, and unchanged component weight;
- declared symbol/universe coverage from source evidence; and
- missing/incompatible coverage evidence.

It does not mean current account holdings, market value, notional exposure,
delta, beta, sector exposure, leverage, margin, financing, or broker position.
Those values must not be inferred.

## Symbol and universe overlap

Where both components provide authoritative symbol sets, calculate transparent
set evidence:

```text
shared_symbol_count
union_symbol_count
jaccard_overlap = shared_symbol_count / union_symbol_count
shared_symbols
```

If either side lacks symbol metadata, overlap is unavailable with an explicit
warning. No natural-language or model-generated similarity substitutes for
missing evidence.

## Return interaction

Using the one shared aligned historical window, calculate:

- pairwise Pearson return correlation for every ordered component pair;
- candidate-to-baseline-portfolio return correlation; and
- observation count and evaluation window for every interaction result.

Correlation is descriptive historical evidence. The product must not turn it
into a recommendation, score, ranking, clustering result, or diversification
claim.

Covariance-derived values are not required for the first M30 version. Adding one
later requires an explicit implementation Issue amendment with formula, units,
sample behavior, and UI meaning.

## Baseline and proposed portfolio behavior

Use existing portfolio authority where practical:

```text
aligned component returns
  -> validated static weights
  -> weighted portfolio return
  -> equity curve
  -> portfolio risk summary
  -> drawdown inspection
  -> component contribution
```

For both scenarios expose an approved subset including:

- observation count;
- arithmetic mean return;
- sample volatility;
- optional annualized volatility;
- minimum and maximum period return;
- positive, negative, and zero period counts;
- loss rate;
- worst drawdown and its peak/trough/recovery context; and
- component contribution summaries.

Proposed impact is the deterministic difference:

```text
proposed value - baseline value
```

for compatible scalar values. Non-scalar context is shown side by side rather
than collapsed into a misleading number.

Every page and artifact must identify this as historical scenario evidence, not
forecast performance, expected alpha, an investment recommendation, or an
execution instruction.

## Artifact Authority

M30 uses immutable files for full payload authority.

Recommended logical layout under the configured evidence artifact root:

```text
portfolio-reviews/
  sources/<source-id>/source.json
  reviews/<review-id>/analysis.json
  reviews/<review-id>/decision.json
```

The exact safe path contract belongs to implementation, but it must preserve:

- root containment;
- no arbitrary HTTP paths;
- no absolute or traversal references;
- no symlink escape;
- schema and digest validation;
- deterministic JSON-compatible values;
- write-once collision refusal; and
- reopen/cross-validation before API return.

Source, analysis, and decision payloads remain separate. A decision does not
rewrite the analysis artifact.

## SQLite Persistence Boundary

M30 is expected to add one reviewed Alembic migration after Sprint 169. The
migration name and exact table shape belong to Sprint 174's authoritative Issue.

SQLite may store compact product-owned metadata such as:

- review ID;
- source ID and source digest;
- baseline/proposed request digest;
- analysis artifact key and digest;
- decision artifact key and digest when settled;
- workflow status;
- create-command idempotency key and digest;
- decision-command idempotency key and digest;
- created/reviewed actor and UTC timestamps;
- optimistic version or other deterministic conflict field; and
- sanitized stable failure identity where approved.

SQLite must not store:

- full aligned returns;
- full symbol-overlap matrices;
- full correlation matrices;
- complete analysis payloads;
- complete decision payloads;
- account cash or positions;
- orders, fills, or ledger entries.

Recommended review workflow statuses are:

```text
awaiting_decision
approved
rejected
deferred
```

They describe the M30 review record only. They are not strategy lifecycle state
and are not Paper Job state.

## Idempotency and Concurrency

### Review creation

`POST /api/v1/portfolio-reviews` requires one explicit idempotency key.

```text
same key + same normalized command digest -> exact replay
same key + different digest                -> stable conflict
new key + existing analysis identity       -> explicit duplicate/collision policy
```

The application must settle the authoritative analysis artifact and compact
record consistently. Partial write failures remain visible and recoverable only
through an explicitly specified bounded contract; they are never hidden by
creating competing artifacts.

### Decision recording

`POST /api/v1/portfolio-reviews/{review_id}/decision` also requires explicit
idempotency.

```text
same key + same decision digest -> exact replay
same key + different digest     -> stable conflict
already-settled different input -> settled-review conflict
```

Concurrent different decisions have one deterministic winner. The loser receives
a stable conflict and can inspect the settled decision.

No command automatically creates a lifecycle proposal, Paper Account, order,
fill, or Paper Job.

## Application and API Boundary

The approved API shape is conceptually:

```text
POST /api/v1/portfolio-reviews
GET  /api/v1/portfolio-reviews
GET  /api/v1/portfolio-reviews/{review_id}
POST /api/v1/portfolio-reviews/{review_id}/decision
```

Implementation rules:

- request schemas remain bounded and versioned;
- handlers only translate transport to application commands/views;
- application services coordinate repositories, artifact readers/writers, and
  domain calculations;
- list responses contain compact product metadata only;
- detail responses reopen and cross-validate authoritative artifacts;
- raw source, analysis, decision, schema, digest, timestamp, and warning identity
  remain visible;
- errors use stable codes, request IDs, sanitized messages, and existing
  observability rules;
- no endpoint accepts an arbitrary filesystem path;
- no update/delete endpoint mutates settled evidence; and
- no account, lifecycle, order, execution, or broker side effect exists.

Expected error families include bounded source unavailable/invalid/not found,
review invalid/not found/conflict, artifact collision/invalid/unavailable,
decision invalid, and review already settled. Exact codes belong to S174.

## Founder Web Boundary

Recommended routes are:

```text
/portfolio-reviews
/portfolio-reviews/new
/portfolio-reviews/[reviewId]
```

### List

Show compact review identity, source, candidate, status, created/reviewed time,
and exact detail link. Preserve backend ordering. Do not sort by return, risk, or
approval outcome unless an explicit product contract later defines neutral
ordering.

### Create

The Founder explicitly selects one approved source, baseline/proposed weights,
the proposed component, and rationale. The form validates shape for usability,
but the backend remains authority.

The UI must not:

- discover or auto-select a candidate;
- normalize weights silently;
- propose weights;
- infer relationships between unrelated evidence;
- calculate concentration, correlation, risk, drawdown, or impact; or
- submit automatically.

### Detail and decision

Display:

- review identity and source audit;
- baseline and proposed weights;
- concentration;
- review exposure and symbol overlap;
- interaction matrix/evidence;
- baseline/proposed portfolio behavior and deltas;
- contribution context;
- assumptions, limitations, warnings, and missing evidence;
- raw schema/digest/timestamp values; and
- explicit decision form or immutable settled decision.

Charts are optional and must visualize backend-owned values without recomputation.
Tables and accessible text remain sufficient authority.

### Product language

The entire M30 workflow is complete in `en` and `zh-CN`. Raw strategy names,
component IDs, source/review/decision IDs, status values, schema versions,
digests, timestamps, weights, metrics, and error codes remain inspectable and
untranslated. Localized explanations may accompany them.

## Dashboard Boundary

After durable review list semantics exist, the Overview may provide a neutral
link or bounded attention item for `awaiting_decision` reviews.

It must not:

- recommend approval or rejection;
- rank reviews;
- call lower risk or correlation automatically better;
- infer pending reviews from in-memory state; or
- hide source-specific failures.

Any Dashboard change belongs to the Web implementation Issue.

## Demo and Standard Workspace

S176 should provide deterministic Demo source/review examples that visibly remain
Demo-only and disposable.

Standard startup remains unseeded. Demo installation never writes to Standard
storage. Existing backup, volume-isolation, and fail-closed rules remain in force.

Codex does not run Docker builds, pulls, Compose startup, container smoke, or
volume removal. The Founder owns local Standard/Demo and browser acceptance.

## M31 Handoff

M30 hands M31:

- stable portfolio review identity;
- immutable source and analysis evidence;
- explicit human decision evidence;
- scenario assumptions and warnings; and
- a compact auditable reference boundary.

M30 does **not** hand M31 account truth.

M31 may reference an approved M30 decision, but must separately establish:

- Paper Account identity;
- cash and position ledger truth;
- orders and fills;
- account versioning;
- snapshot derivation;
- reconciliation; and
- deterministic write concurrency.

M30 weights are review assumptions. They are not account balances, current
holdings, reserved cash, orders, fills, ledger events, or executable allocation
instructions. No approved review automatically creates or funds an account.

## Approved Sprint Dependencies

```text
S169 architecture and planning
  -> S170 source/input and scenario contracts
  -> S171 concentration and review-exposure analysis
  -> S172 interaction and proposed-impact analysis
  -> S173 immutable review/decision artifacts
  -> S174 persistence, application services, and API
  -> S175 bilingual Founder Web workflow
  -> S176 integration, Demo, and acceptance hardening
  -> S177 closeout and M31 handoff
```

Each sprint receives its own authoritative Issue after its predecessor is merged.
No future Issue may weaken this architecture silently. Material changes require
an explicit Issue amendment and CTO review.

## Architecture Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Summary metrics are mistaken for enough interaction evidence. | Require aligned return observations and exact evaluation identity. |
| M30 becomes another caller-supplied governance shell. | Domain calculations own concentration, overlap, correlation, risk, drawdown, and deltas. |
| Review weights are mistaken for capital allocation. | Label them scenario assumptions and separate them from M31 account truth. |
| Correlation is presented as recommendation. | Preserve raw descriptive values, sample limits, and neutral copy. |
| Missing symbol metadata is silently inferred. | Return unavailable overlap with explicit warnings. |
| Old research runs are declared compatible without returns. | Require a validated M30 source artifact; no retroactive compatibility claim. |
| Full payloads bloat SQLite. | Keep files authoritative and persist compact identity/reference metadata only. |
| Concurrent decisions overwrite evidence. | One settled decision, idempotency, deterministic winner/loser conflict. |
| Web duplicates financial calculations. | Generated API contracts and backend-owned values only. |
| M30 leaks into M31–M36. | Explicit account, market, order, runtime, broker, and live non-goals. |
| Demo evidence contaminates Standard. | Preserve visible mode identity and isolated volumes/roots. |

## Exit Architecture

M30 is architecturally complete only when the Founder can create and inspect one
reproducible portfolio review, understand concentration/exposure/interaction and
historical proposed impact, record one explicit human decision, and inspect all
raw evidence and limitations through the bilingual product.

Completion must still prove:

- no automatic allocation;
- no optimization or recommendation;
- no account or ledger mutation;
- no market/session runtime;
- no order or fill generation;
- no worker or scheduler;
- no broker/QMT/live behavior; and
- a clean handoff to a separately authoritative M31 account/ledger milestone.
