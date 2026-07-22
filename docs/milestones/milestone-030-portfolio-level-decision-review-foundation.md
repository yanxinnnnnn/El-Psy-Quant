# Milestone 30 — Portfolio-Level Decision Review Foundation

## Status

**Complete after Sprint 178 merges.**

Completed sprint range:

```text
S169–S178
```

Formal closeout:

```text
docs/closeouts/milestone-030-portfolio-level-decision-review-foundation-closeout.md
```

## Product Goal

Milestone 30 adds one explicit portfolio-aware decision layer before stateful
Paper Account and market-driven runtime work begins.

The Founder can answer:

```text
What portfolio source and scenarios are under review?
Which strategy and evidence inputs are included?
Where is concentration located?
Which component and universe exposures change?
How do return streams and symbol sets interact?
How would the proposed scenario have changed historical behavior?
Which assumptions, warnings, and missing evidence limit the review?
What explicit human decision was recorded?
```

M30 remains human-controlled portfolio governance. It does not allocate capital,
mutate an account, generate orders, simulate fills, or start a runtime.

## Delivered Product Chain

```text
explicit immutable review source
  -> explicit baseline and proposed static scenarios
  -> domain-calculated concentration and review exposure
  -> symbol overlap and historical return interaction
  -> baseline/proposed historical behavior and impact
  -> immutable analysis evidence
  -> explicit approve / reject / defer decision
  -> bilingual Founder inspection and audit
```

## Core Product Authority

### Review source

One source owns:

- 2–12 ordered components;
- explicit component and strategy identities;
- supported evidence references;
- at least one research-origin reference per component;
- optional authoritative symbol metadata;
- at least three exact ordered aligned historical return observations;
- evaluation and audit identity;
- assumptions, warnings, and missing evidence; and
- a canonical SHA-256 digest.

The product never reconstructs aligned returns from summary metrics, prose,
screenshots, comparisons, or unrelated records.

### Baseline and proposed scenarios

Both scenarios:

- bind to the same exact source;
- use the complete source component set in source order;
- use explicit non-negative static weights summing to one;
- preserve exact caller values without normalization;
- have distinct scenario identities; and
- require a real weight change for the explicit proposed component.

Weights are review assumptions, not holdings, cash, available capital, reserved
capital, or account allocation.

### Analysis

Domain-owned analysis includes:

- largest-component weight;
- top-three concentration;
- Herfindahl-Hirschman index;
- effective component count;
- ordered component exposure and weight changes;
- declared-symbol evidence and active coverage;
- shared symbols and Jaccard overlap;
- pairwise historical return correlation;
- proposed-component-to-baseline correlation;
- baseline/proposed historical risk and behavior;
- equity and drawdown context;
- ordered component contribution; and
- exact proposed-minus-baseline deltas.

Undefined or missing evidence remains explicitly unavailable. Results are
historical scenario evidence, not forecasts, rankings, recommendations, expected
alpha, or investment advice.

### Human decision

One review supports at most one settled immutable decision:

```text
approved
rejected
deferred
```

The decision contains exact review and analysis identity, reviewer, UTC timestamp,
rationale, notes, warnings, scope, and digest. Approval is governance evidence
only; it does not approve execution or create account state.

## Artifact and Persistence Authority

Full source, analysis, and decision payloads remain separate write-once files
under fixed server-owned hashed paths. Readers reject unsafe paths, symlinks,
duplicate JSON keys, non-finite values, schema/digest conflicts, and mismatched
nested authority.

SQLite stores compact product metadata and workflow state only:

- review/source/scenario/analysis/decision identity and digests;
- safe relative artifact references;
- create and decision idempotency bindings;
- status and optimistic version state;
- actor and UTC timestamps; and
- deterministic one-winner settlement state.

It does not store full observations, matrices, calculations, complete artifact
payloads, account balances, positions, orders, fills, or ledger entries.

The exact migration chain is:

```text
0001_product_baseline
  -> 0002_artifact_index
  -> 0003_paper_jobs
  -> 0004_paper_job_recovery_audit
  -> 0005_paper_job_result_references
  -> 0006_portfolio_reviews
```

Single head:

```text
0006_portfolio_reviews
```

The installed backend wheel contains the complete authoritative Alembic resource
tree. Runtime startup does not depend on `/app/src` or a repository checkout.

## API and Web Boundary

The portfolio-review API remains exactly:

```text
POST /api/v1/portfolio-reviews
GET  /api/v1/portfolio-reviews
GET  /api/v1/portfolio-reviews/{review_id}
POST /api/v1/portfolio-reviews/{review_id}/decision
```

The bilingual Founder Web provides:

- exact backend-ordered list/filter/refresh;
- a complete manual create builder;
- explicit research-run and compatible evidence-manifest composition;
- strict finite input validation without browser financial calculation;
- complete authoritative detail and audit presentation;
- visible unavailable-evidence meaning;
- one awaiting-only explicit decision action; and
- immutable settled-decision presentation.

The browser never reads files or SQLite, calculates portfolio evidence, infers a
candidate, normalizes weights, or records a decision automatically.

## Demo and Standard Workspace

Demo dataset/descriptor v2 provides:

- one isolated exact synthetic source and durable review;
- one explicit replace-confirmed create prefill;
- no automatic submit or decision;
- exact create replay through the existing API;
- preservation of a valid later human decision; and
- read-only verifier coverage.

Standard remains unseeded. Standard and Demo use separate project identities,
volumes, databases, and artifact roots.

## Completed Sprint Sequence

| Sprint | Outcome | Status |
|---:|---|---|
| S169 | Architecture, scope, data authority, acceptance model, sprint plan, and M31 boundary | Complete |
| S170 | Immutable source, component, evidence, aligned-return, and scenario contracts | Complete |
| S171 | Concentration, exposure, and declared-symbol coverage analysis | Complete |
| S172 | Overlap, correlation, historical behavior, contribution, and proposed impact | Complete |
| S173 | Immutable analysis, decision, digest, and typed-reference artifacts | Complete |
| S174 | Write-once artifact I/O, compact persistence, migration, application services, and API | Complete |
| S175 | Bilingual Founder list/create/detail/decision workspace | Complete |
| S176 | Explicit workflow integration, Demo v2, verification, errors, and acceptance hardening | Complete |
| S177 | Installed-wheel Alembic resource packaging and preserved-volume startup recovery | Complete |
| S178 | Formal closeout and M31 planning handoff | Complete after merge |

## Verification and Founder Acceptance

Deterministic implementation gates covered Python tests and linting, package and
CLI behavior, installed-wheel migration resources, OpenAPI/generated TypeScript,
locale catalogs, Web lint/type/tests/build, Alembic head, and static Compose
configuration.

Founder local acceptance confirmed:

- the preserved Standard volume upgraded from 0005 to 0006;
- Standard read-only verification and non-mutating smoke passed;
- Standard remained unseeded;
- Demo Workspace v2 installed and verified;
- the exact create prefill did not auto-submit;
- exact create/replay and authoritative detail passed;
- one explicit decision persisted across Demo restart;
- returning to Standard preserved data isolation; and
- English and Simplified Chinese browser acceptance passed while raw values
  remained unchanged.

## Exit Criteria

M30 completed every approved exit criterion:

- reproducible explicit source and scenarios;
- inspectable concentration, exposure, overlap, interaction, behavior, and impact;
- visible assumptions, warnings, missing evidence, versions, timestamps, and
  digests;
- immutable source, analysis, and decision authority;
- compact SQLite state and explicit idempotency;
- exact versioned API and bilingual Web workflow;
- write-once settled evidence;
- preserved Standard/Demo isolation;
- successful Founder acceptance; and
- no premature M31–M36 behavior.

## Explicit Non-goals and Remaining Debt

M30 does not introduce:

- durable Paper Account, cash, position, fee, order, fill, or ledger truth;
- account funding or capital allocation from scenario weights;
- market-data replay, trading calendar, or session clock;
- strategy-signal-to-order generation;
- pre-trade risk for generated orders;
- order lifecycle or execution simulation;
- durable worker, scheduler, checkpoints, or multi-session runtime;
- continuous multi-day Paper Trading;
- broker, QMT, MiniQMT, private-edge, live, or real-money behavior;
- automatic strategy ranking, approval, optimization, or recommendation;
- public SaaS, multi-tenancy, or complex RBAC; or
- automatic backup or full restore tooling.

## M31 Handoff

The next milestone is:

```text
M31 — Stateful Paper Account and Ledger Foundation
```

M31 must create an independent durable account and ledger source of truth. An
approved M30 review may be attached as evidence, but it cannot create, fund, or
mutate an account and is not ledger truth.

M31 planning must explicitly decide:

- account identity and lifecycle;
- initial cash and controlled funding/adjustment semantics;
- immutable cash and position ledger entries;
- order/fill persistence boundaries without execution;
- fee and adjustment semantics;
- versioning, optimistic concurrency, and idempotency;
- snapshots, reconciliation, and derived-balance authority;
- the exact M30 evidence-reference relationship;
- persistence, artifact, API, Web, Demo, migration, and Founder acceptance; and
- deferral of M32+ market/session/order-generation/execution/runtime behavior.

After Sprint 178 merges, the next action is an M31 architecture-and-planning
Issue, not direct implementation.

## Authoritative Records

```text
docs/architecture/portfolio-level-decision-review.md
docs/closeouts/milestone-030-portfolio-level-decision-review-foundation-closeout.md
docs/sprints/sprint-178-milestone-030-closeout-and-m31-handoff.md
docs/strategy/paper-trading-runtime-roadmap.md
```