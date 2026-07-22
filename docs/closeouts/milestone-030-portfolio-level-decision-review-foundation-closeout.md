# Milestone 30 — Portfolio-Level Decision Review Foundation Closeout

## Closeout Decision

Milestone 30 is **Complete** after Sprint 178 merges.

The completed milestone gives the Founder a reproducible, portfolio-aware,
human-controlled review workflow before any durable Paper Account, market-session,
order-generation, or execution runtime is introduced.

The closeout decision is based on:

- merged Sprints 169–177;
- green deterministic repository gates;
- migration head `0006_portfolio_reviews`;
- successful preserved-volume Standard recovery from revision
  `0005_paper_job_result_references` to `0006_portfolio_reviews`;
- successful Standard read-only verification and MVP smoke;
- successful Demo Workspace dataset/descriptor v2 verification;
- exact portfolio-review create prefill and replay;
- one explicit human decision preserved across Demo restart;
- verified return-to-Standard storage isolation; and
- successful English and Simplified Chinese browser acceptance.

This is Founder local product acceptance. It is not external-customer validation,
strategy-profitability evidence, broker readiness, or live-trading evidence.

## Sprint and Pull Request Chain

| Sprint | Issue | Pull Request | Outcome |
|---:|---:|---:|---|
| S169 | #335 | #336 | M30 architecture, source authority, scope, sprint sequence, and M31 boundary approved. |
| S170 | #337 | #338 | Immutable review source, component, evidence, aligned-return, and scenario contracts. |
| S171 | #339 | #340 | Deterministic concentration, exposure, and symbol-evidence coverage analysis. |
| S172 | #341 | #342 | Symbol overlap, historical interaction, portfolio behavior, contribution, and proposed impact. |
| S173 | #343 | #344 | Immutable analysis, decision, digest, and typed-reference artifacts. |
| S174 | #345 | #346 | Write-once artifact I/O, compact persistence, migration `0006`, application services, and four API routes. |
| S175 | #347 | #348 | Bilingual Founder list/create/detail/decision workspace. |
| S176 | #349 | #350 | Explicit research/evidence composition, Demo v2, read-only verification, error and acceptance hardening. |
| S177 | #351 | #352 | Installed-wheel Alembic resource packaging and preserved-volume startup recovery. |
| S178 | #353 | pending | Formal M30 closeout and M31 planning handoff. |

## Product Outcome

### Explicit review authority

M30 introduced one immutable portfolio-review source containing:

- 2–12 ordered components;
- explicit strategy identities;
- supported typed evidence references;
- research-origin evidence for every component;
- optional authoritative symbols;
- at least three ordered aligned historical return observations;
- evaluation and audit identity;
- assumptions, warnings, and missing evidence; and
- one canonical source digest.

No source relationship, return observation, symbol, component, or candidate is
silently inferred.

### Strict scenario authority

Baseline and proposed scenarios:

- reference the same exact source;
- use complete non-negative static weights;
- sum to one within the approved deterministic tolerance;
- preserve exact source component order;
- identify one explicit proposed component; and
- require a real proposed-component weight change.

The product does not normalize, optimize, recommend, rank, or allocate weights.
Scenario weights remain review assumptions, not account holdings or capital.

### Portfolio-level evidence

Domain modules calculate and expose:

- largest-component weight;
- top-three concentration;
- Herfindahl-Hirschman index;
- effective component count;
- ordered component weight changes and active-state meaning;
- declared-symbol evidence and coverage;
- pairwise symbol overlap and Jaccard overlap;
- pairwise historical-return correlation;
- proposed-component-to-baseline-portfolio correlation;
- baseline and proposed historical portfolio behavior;
- risk, volatility, loss-rate, equity, and drawdown context;
- ordered component contribution; and
- exact proposed-minus-baseline impact.

Unavailable evidence remains explicitly unavailable. The product never serializes
`NaN`, infinity, or a fabricated zero to disguise missing or undefined evidence.
All analysis is historical scenario evidence, not a forecast or recommendation.

### Immutable artifacts and durable workflow

M30 delivered separate write-once source, analysis, and decision artifacts under
fixed server-owned hashed paths. Strict readers reconstruct and cross-validate
product authority; analysis reopen recalculates derived evidence from the exact
source and scenarios.

SQLite stores compact product metadata and workflow state only, including:

- source, scenario, analysis, and decision identity and digests;
- safe relative artifact references;
- create and decision idempotency bindings;
- workflow status and version;
- actor and UTC timestamps; and
- one-winner decision settlement state.

Full returns, matrices, calculations, and decision payloads remain file-authoritative.
The single current migration head is:

```text
0006_portfolio_reviews
```

### API and Founder Web

The versioned API remains exactly:

```text
POST /api/v1/portfolio-reviews
GET  /api/v1/portfolio-reviews
GET  /api/v1/portfolio-reviews/{review_id}
POST /api/v1/portfolio-reviews/{review_id}/decision
```

The bilingual Founder workspace provides:

- backend-ordered list and filters;
- a complete manual source/scenario builder;
- explicit research-run and compatible evidence-manifest composition;
- strict input validation without browser financial calculation;
- complete authoritative detail and audit inspection;
- explicit unavailable-evidence presentation;
- one awaiting-only `approved`, `rejected`, or `deferred` decision; and
- immutable settled-decision presentation.

Failures preserve drafts and previously loaded authoritative evidence where
appropriate. The browser never reads SQLite or artifact files directly.

### Demo and local operations

Demo Workspace dataset/descriptor v2 provides one isolated synthetic review and
one explicit replace-confirmed create prefill. It never auto-submits or chooses a
decision. Exact replay preserves a later valid human decision.

Standard remains unseeded. Standard and Demo use separate project identities,
volumes, databases, and artifact roots. Read-only verification and bilingual MVP
smoke do not issue portfolio-review, Paper Job, or lifecycle mutations.

The backend runtime now resolves the complete Alembic tree from the installed
project wheel rather than a repository checkout. The S177 defect was diagnosed
without deleting or hand-editing the Standard volume; the existing healthy 0005
database subsequently completed the supported upgrade to 0006.

## Exit Criteria Review

| Exit criterion | Closeout result |
|---|---|
| Explicit validated source supports reproducible analysis | Complete |
| Stable baseline/proposed scenario identity and strict weights | Complete |
| Concentration and review exposure inspectable | Complete |
| Overlap and interaction inspectable with evidence limits | Complete |
| Historical behavior and deltas domain-calculated | Complete |
| Assumptions, warnings, missing evidence, versions, and digests visible | Complete |
| One immutable explicit human decision recordable | Complete |
| Full payloads remain authoritative artifacts | Complete |
| SQLite remains compact metadata and idempotency state | Complete |
| Versioned API and bilingual Web complete | Complete |
| Settled evidence cannot be silently overwritten | Complete |
| Standard/Demo isolation and product hardening preserved | Complete |
| Founder acceptance confirms portfolio-level review usefulness | Complete |
| No M31–M36 behavior implemented prematurely | Complete |

## Founder Acceptance Evidence

Founder acceptance confirmed all of the following against the merged runtime:

```text
preserved Standard volume
  -> supported 0005-to-0006 migration
  -> Standard workspace verification
  -> Standard non-mutating smoke
  -> Standard remains unseeded

isolated Demo v2
  -> exact seeded review visible
  -> explicit prefill without auto-submit
  -> exact create/replay
  -> explicit human decision
  -> restart preserves decision
  -> return to Standard preserves isolation

English and Simplified Chinese
  -> route and workflow presentation accepted
  -> raw IDs, statuses, timestamps, digests, values, and ordering unchanged
```

## Preserved Authority Boundaries

```text
Browser
  -> Next.js Founder Workspace
  -> fixed same-origin /api/backend gateway
  -> versioned FastAPI API
  -> thin application services
  -> domain modules and artifact readers/writers
  -> compact SQLite state and authoritative artifact roots
```

- Domain modules remain quantitative and governance authority.
- Completed files remain full artifact payload authority.
- SQLite remains compact metadata and operational state.
- Localization never changes raw product truth.
- Paper Job, lifecycle, portfolio review, and future account state remain separate.
- Human approval remains governance evidence only.
- Standard and Demo remain isolated.
- No browser-to-filesystem, database, Python, QMT, MiniQMT, or broker path exists.

## Remaining Product Debt and Explicit Non-goals

The following remain intentionally undelivered:

- no durable Paper Account or cash/position ledger;
- no account-funded interpretation of M30 scenario weights;
- no automatic capital allocation;
- no market-data replay, trading calendar, or session clock;
- no strategy-signal-to-order pipeline;
- no pre-trade risk for automatically generated orders;
- no runtime order lifecycle or execution simulator;
- no durable worker, scheduler, queue, checkpoint, or multi-session loop;
- no continuous multi-day Paper Trading;
- no broker, QMT, MiniQMT, private-edge, live, or real-money behavior;
- no automatic strategy ranking, approval, optimization, or recommendation;
- local single-Founder minimal authentication remains; and
- cold backup and restore remain explicit manual operator workflows with documented limitations.

These boundaries are the planned handoff to later milestones, not evidence that
M30 failed.

## M31 Handoff

The next milestone is:

```text
M31 — Stateful Paper Account and Ledger Foundation
```

M31 must create an independent durable source of truth for account state. An
approved M30 review may be attached as evidence, but it cannot create, fund, or
mutate an account and is not a ledger entry.

M31 architecture planning must decide:

- account identity and lifecycle;
- initial cash and controlled funding/adjustment semantics;
- immutable cash and position ledger entries;
- order and fill persistence boundaries without implementing execution;
- fee and adjustment semantics;
- versioning, optimistic concurrency, and idempotency;
- snapshots, reconciliation, and derived-balance authority;
- the exact evidence-reference link to an approved M30 review;
- persistence, artifact, API, Web, Demo, migration, and acceptance boundaries; and
- explicit deferral of M32+ market, order-generation, execution, and runtime behavior.

After Sprint 178 merges, the next action is an M31 architecture-and-planning
Issue. Direct implementation must not begin before that plan is approved.