# Milestone 30 — Portfolio-Level Decision Review Foundation

## Status

**In Progress.**

Planned sprint range:

```text
S169–S177
```

Sprints 169–172 are Complete. Sprint 173 portfolio-review artifact and human
decision implementation is complete pending Founder review. Sprint 174 is next
after merge.

## Product Goal

Before a strategy is considered by the future stateful Paper Trading runtime,
the Founder can review it in the context of an explicit portfolio scenario.

The completed milestone should answer:

```text
What portfolio and proposal are under review?
Which strategy and evidence inputs are included?
How concentrated is the baseline and proposed scenario?
Which component and universe exposures change?
How do strategy return streams and symbol sets overlap?
How would the proposal have changed historical portfolio behavior?
What assumptions, missing evidence, and warnings limit the review?
What explicit human decision was recorded?
```

M30 remains human-controlled portfolio decision review. It does not allocate
capital, approve execution, mutate an account, generate orders, simulate fills,
or start a runtime.

## Why This Milestone Comes Now

Milestones 13 and 14 established static portfolio construction, risk, drawdown,
contribution, and attribution foundations.

Milestones 20–24 established human-controlled promotion, comparison, decision,
report, and lifecycle governance.

Milestones 26–29 exposed and hardened those capabilities through a local
bilingual Founder product.

The next missing decision layer is not another strategy-level record. It is the
ability to inspect the effect of a proposed strategy on the portfolio as a whole
before future account and execution automation is introduced.

The approved sequence remains:

```text
M30 portfolio decision review
  -> M31 durable Paper Account and ledger truth
  -> M32 market-session truth
  -> M33 strategy-to-order and pre-trade risk truth
  -> M34 execution truth
  -> M35 durable runtime truth
  -> M36 multi-day operations
```

## Audited Existing Capability

### Reused portfolio authority

M30 should reuse existing domain behavior for:

- return alignment;
- strict static-weight validation;
- weighted portfolio returns;
- equity construction;
- portfolio risk summaries;
- worst drawdown inspection;
- component contribution; and
- deterministic artifact conventions.

### Reused governance authority

M30 should follow existing conventions for:

- stable IDs and schema versions;
- typed evidence references;
- immutable descriptive and decision records;
- required rationale;
- reviewer and timestamp identity;
- assumptions, warnings, and missing evidence;
- deterministic JSON-compatible export; and
- explicit human control.

### Reused product authority

M30 should preserve:

```text
Browser
  -> Next.js Founder Workspace
  -> same-origin backend gateway
  -> versioned FastAPI API
  -> thin application services
  -> domain modules and artifact readers/writers
  -> authoritative artifact roots and compact SQLite state
```

### Capability gap M30 must close

Current research artifacts expose manifests and summary metrics but not the
aligned strategy return observations required to calculate reproducible
interaction and proposed portfolio impact.

M30 must introduce an explicit immutable review-source artifact. It must not infer
correlation or portfolio impact from summary metrics, screenshots, user prose, or
unrelated records.

## User Journey

The target Founder journey is:

```text
select validated portfolio review source
  -> declare baseline static weights
  -> declare proposed static weights and candidate
  -> submit explicit review command
  -> inspect immutable concentration/exposure/interaction/impact evidence
  -> inspect assumptions, warnings, raw identities, and source digests
  -> record approve / reject / defer with rationale
  -> retain immutable decision evidence for later reference
```

A proposal is not automatically approved. An approval is not execution.

## Core Product Objects

M30 introduces bounded equivalents of:

```text
PortfolioReviewSource
PortfolioReviewComponent
PortfolioReviewScenario
PortfolioReviewAnalysis
PortfolioReviewDecision
PortfolioReviewReference / compact product record
```

Exact names are implementation decisions, but competing hidden authorities are
not allowed.

### Source

The source contains explicit component identities, evidence references, aligned
historical return observations, symbol/universe metadata where authoritative,
evaluation assumptions, and a deterministic digest.

### Scenarios

Baseline and proposed scenarios use the same source and evaluation window. They
contain explicit non-negative static weights summing to `1.0`. No automatic
scaling, optimization, or weight recommendation occurs.

The first M30 version supports a union of at most 12 explicitly selected strategy
components. At least one proposed weight differs from baseline.

### Analysis

The analysis contains domain-calculated concentration, review exposure, symbol
or universe overlap, return interaction, baseline/proposed historical behavior,
and explicit deltas.

### Decision

The decision is separate immutable human evidence with exactly:

```text
approved
rejected
deferred
```

One M30 review has at most one settled decision. Changed evidence, assumptions,
or weights create a new review.

## Quantitative Scope

## Concentration

At minimum:

- largest component and weight;
- top-three concentration;
- Herfindahl-Hirschman index;
- effective component count; and
- ordered baseline/proposed weight deltas.

## Review exposure

M30 review exposure means:

- static strategy/component scenario weights;
- added, removed, increased, decreased, and unchanged components; and
- declared symbol/universe coverage from authoritative source evidence.

It does not mean runtime holdings, account market value, notional, leverage,
margin, financing, or broker exposure.

## Interaction and overlap

At minimum where evidence is available:

- shared-symbol counts and explicit shared-symbol identity;
- Jaccard symbol-set overlap;
- pairwise Pearson historical return correlation;
- candidate-to-baseline-portfolio correlation; and
- observation count and evaluation-window identity.

Undefined correlation remains unavailable with a warning. It is never serialized
as `NaN`, infinity, or a fabricated zero.

## Proposed impact

Use the same aligned historical observations and assumptions for baseline and
proposed scenarios. Compare an approved subset of:

- mean return;
- volatility and optional annualized volatility;
- loss rate;
- min/max period return;
- worst drawdown;
- concentration;
- component contribution; and
- interaction/overlap context.

Scalar deltas are `proposed - baseline`. Non-scalar evidence is shown side by
side.

All results are historical scenario evidence, not forecasts, rankings,
recommendations, or investment advice.

## Data and Artifact Authority

Full payload authority remains immutable files under a safe configured artifact
root.

Recommended logical artifacts:

```text
portfolio review source artifact
portfolio review analysis artifact
portfolio review decision artifact
```

They remain separate, versioned, digestible, deterministic, and cross-validatable.
No API accepts an arbitrary path. No settled artifact is overwritten.

Existing old research runs remain readable. They are not modified or falsely
upgraded into M30 sources without the required return evidence.

## Persistence Requirement

M30 is expected to add one reviewed Alembic migration in Sprint 174. Sprint 169
does not change migration head `0005_paper_job_result_references`.

SQLite stores compact product-owned metadata only, including an approved subset
of:

- review/source identity and digests;
- analysis/decision artifact references and digests;
- workflow status;
- create and decision idempotency bindings;
- actor and UTC timestamps;
- deterministic conflict/version information; and
- sanitized stable failure identity where approved.

SQLite does not store full return observations, matrices, full analysis payloads,
full decision payloads, account balances, positions, orders, fills, or ledger
entries.

## API Requirement

The target bounded API is equivalent to:

```text
POST /api/v1/portfolio-reviews
GET  /api/v1/portfolio-reviews
GET  /api/v1/portfolio-reviews/{review_id}
POST /api/v1/portfolio-reviews/{review_id}/decision
```

Required behavior:

- explicit idempotency for creation and decision;
- compact neutral list semantics;
- exact immutable detail reads;
- authoritative artifact reopen and cross-validation;
- stable conflict, invalid, unavailable, and not-found errors;
- existing request-ID and sanitized observability conventions;
- one deterministic winner for concurrent conflicting decisions; and
- no lifecycle, account, order, execution, or broker side effect.

## Web Requirement

Target routes are equivalent to:

```text
/portfolio-reviews
/portfolio-reviews/new
/portfolio-reviews/[reviewId]
```

The Web must provide:

- complete English and Simplified Chinese copy;
- explicit source and scenario selection;
- visible weight validation without silent normalization;
- concentration, review exposure, overlap, interaction, behavior, delta,
  contribution, assumptions, warning, and audit presentation;
- one explicit decision action;
- immutable settled decision presentation;
- accessible loading, empty, unavailable, invalid, conflict, partial, and settled
  states; and
- raw IDs, versions, digests, timestamps, values, and error codes.

The Web does not calculate financial values, select a candidate, propose weights,
rank strategies, or infer record relationships.

## Human-Control Boundary

M30 decision outcomes are governance evidence.

They do not:

- automatically change an M24 lifecycle state;
- approve Paper Job execution;
- create a Paper Account;
- reserve or allocate cash;
- create positions, orders, fills, or ledger entries;
- trigger a worker or scheduler; or
- imply broker or live readiness.

A later workflow may reference an approved M30 decision only through a separately
approved milestone contract.

## Sprint Sequence

| Sprint | Status | Owner | Goal | Main deliverable | Guardrail |
|---:|---|---|---|---|---|
| S169 | Complete | CTO | Plan M30. | Architecture, milestone scope, data authority, sprint sequence, and M31 handoff. | Documentation only. |
| S170 | Complete | Codex | Define review sources and scenarios. | Immutable source/component/evidence/aligned-return and baseline/proposed scenario contracts. | No analysis, persistence, API, or Web. |
| S171 | Complete | Codex | Add concentration and exposure evidence. | Deterministic concentration, weight-delta, review-exposure, and available universe-coverage summaries. | No correlation, optimization, or recommendation. |
| S172 | Complete | Codex | Add interaction and proposed impact. | Symbol overlap, return interaction, baseline/proposed portfolio behavior, and historical deltas. | No forecast, allocation, factor model, VaR, or runtime. |
| S173 | Implementation complete / pending Founder review | Codex | Add review and decision artifacts. | Immutable analysis/decision payloads, references, digest rules, and explicit outcomes. | No database, API, Web, lifecycle mutation, or execution. |
| S174 | Planned | Codex | Add durable product and API boundary. | Compact SQLite persistence, migration, artifact I/O, application services, OpenAPI, and versioned API. | No account ledger or M31 behavior. |
| S175 | Planned | Codex | Add Founder Web workflow. | Bilingual list/create/detail/decision workspace using generated contracts. | No browser financial calculation or recommendation. |
| S176 | Planned | Codex | Integrate and harden acceptance. | Source workflow integration, deterministic Demo evidence, errors, tests, docs, and Founder acceptance checklist. | Founder owns Docker/browser runtime acceptance; no M31+. |
| S177 | Planned | CTO | Close M30 and hand off to M31. | Exit verification, closeout record, roadmap update, and account/ledger handoff. | Documentation only. |

Future implementation Issues must be created one sprint at a time after the
predecessor is merged.

## Sprint Dependencies

### S170 depends on

- merged S169 architecture;
- existing portfolio alignment and static-weight rules;
- existing immutable governance-contract conventions; and
- an explicit decision on source artifact schema and return observation format.

### S171 depends on

- validated source/component/scenario contracts; and
- exact weight ordering and scenario-union rules.

### S172 depends on

- aligned finite return observations;
- deterministic scenario portfolio returns;
- exact sample/undefined-correlation behavior; and
- reused M13/M14 helpers.

### S173 depends on

- settled analysis schemas;
- exact assumptions/warning semantics; and
- explicit `approved`, `rejected`, `deferred` decision meaning.

### S174 depends on

- stable artifact payload schemas and digests;
- one approved migration design;
- exact idempotency and conflict semantics; and
- safe root/path/write-once contracts.

### S175 depends on

- checked-in OpenAPI and generated TypeScript contracts;
- stable list/detail/decision APIs; and
- complete bilingual terminology.

### S176 depends on

- end-to-end backend and Web behavior;
- deterministic isolated Demo source/review data;
- error and audit inventories; and
- non-destructive Standard/Demo verification.

### S177 depends on

- Founder local acceptance of the complete supported workflow;
- green repository gates;
- all S170–S176 Issues closed and PRs merged; and
- no unresolved M30 blocker.

## Milestone Exit Criteria

M30 completes only when:

- one explicit validated review source can support reproducible portfolio analysis;
- baseline and proposed scenarios have stable identity and strict static weights;
- concentration and review exposure are inspectable;
- supported overlap and interaction evidence are inspectable with sample limits;
- baseline/proposed historical behavior and deltas are domain calculated;
- assumptions, warnings, missing evidence, source versions, and digests are visible;
- one immutable human decision can be recorded with reviewer, timestamp, outcome,
  and rationale;
- full source/analysis/decision payloads remain authoritative artifacts;
- SQLite contains only compact product metadata and idempotency state;
- the complete workflow is available through versioned API and bilingual Web;
- settled evidence cannot be silently overwritten;
- Standard/Demo isolation and existing product hardening remain intact;
- Founder acceptance confirms the workflow improves portfolio-level judgment; and
- no M31–M36 behavior has been implemented prematurely.

## Explicit Non-goals

M30 does not introduce:

- automatic strategy approval;
- automatic portfolio optimization;
- automatic weight generation or normalization;
- automatic capital allocation;
- strategy scoring, ranking, recommendation, or winner selection;
- dynamic weights or rebalancing;
- factor models, VaR, stress-test engines, leverage, margin, or financing;
- durable account, cash, position, order, fill, fee, or ledger truth;
- market-data replay, trading calendar, session clock, or live feed;
- strategy signal evaluation for runtime order generation;
- pre-trade order risk;
- simulated execution;
- worker, scheduler, queue, checkpoint, or multi-day runtime;
- broker, QMT, MiniQMT, or real-money behavior;
- microservices or distributed infrastructure; or
- public SaaS, multi-tenancy, or complex RBAC.

## M31 Handoff

M31 may reference approved M30 review evidence but must create an independent
Paper Account and ledger source of truth.

M30 scenario weights remain review assumptions. They are not account cash,
positions, available capital, reserved capital, orders, fills, or ledger events.
No M30 decision creates or funds an account.

M31 planning must explicitly decide:

- account identity;
- cash and position ledger entries;
- order/fill persistence;
- fee and adjustment semantics;
- account versioning and concurrency;
- snapshots and reconciliation; and
- how an approved M30 review reference is attached without becoming ledger truth.

## Authoritative Architecture

See:

```text
docs/architecture/portfolio-level-decision-review.md
```

That architecture constrains S170–S177 unless an authoritative Issue amendment is
approved before implementation.
