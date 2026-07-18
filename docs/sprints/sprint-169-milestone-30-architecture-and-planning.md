# Sprint 169 — Milestone 30 Architecture and Planning

## Status

Implementation complete / pending Founder review.

This is a documentation-only CTO sprint.

## Objective

Start Milestone 30 by converting the approved portfolio-level decision-review
direction into one explicit architecture, milestone boundary, data-authority
model, sprint sequence, and M31 handoff before implementation begins.

## Pre-start Verification

Verified before planning:

- repository: `yanxinnnnnn/El-Psy-Quant`;
- `main` HEAD: `f221ee5c596b2ee3d14cda5ad16922402e50e80a`;
- PR #334 was merged;
- Issue #333 was closed as completed;
- no open Issue existed;
- no open pull request existed;
- Milestones 1–29 were Complete;
- Sprints 161–168 were Complete; and
- migration head remained `0005_paper_job_result_references`.

## Audit Performed

Sprint 169 reviewed:

```text
docs/strategy/paper-trading-runtime-roadmap.md
docs/strategy/future-platform-roadmap.md
docs/roadmap.md
```

It also reviewed the completed portfolio construction, portfolio risk,
attribution, promotion, Paper Run comparison, strategy decision, report artifact,
strategy lifecycle, application service, persistence, API, Founder Web, Dashboard,
and related test boundaries.

## Key Findings

### Existing portfolio capability is useful but standalone

The project already supports:

- aligned return inputs;
- equal and caller-supplied static weights;
- weighted portfolio return aggregation;
- portfolio summaries;
- risk and drawdown inspection;
- static contribution summaries; and
- standalone portfolio/attribution artifacts.

It does not yet provide a product-owned portfolio review identity, strategy
interaction analysis, proposed scenario impact, durable review workflow, API, or
Web experience.

### Existing governance is explicit but mainly descriptive

Promotion, Paper comparison, strategy decision, report, and lifecycle contracts
provide strong immutable human-governance conventions. Their descriptive facts
are generally caller supplied.

M30 must reuse their identity and decision semantics, but concentration,
overlap, correlation, risk, drawdown, contribution, and scenario deltas must be
owned by domain calculations rather than typed prose.

### Existing research artifacts lack required return observations

Configured research artifacts expose manifests and summary metrics. They do not
preserve or expose the aligned strategy return observations needed to calculate
reproducible portfolio interaction and proposed impact.

M30 therefore needs a new explicit immutable review-source artifact. It must not
infer correlation or impact from summary metrics or connect unrelated records
silently.

### Existing product authority remains correct

The approved chain remains:

```text
Browser
  -> Next.js Founder Workspace
  -> fixed same-origin backend gateway
  -> versioned FastAPI API
  -> thin application services
  -> domain calculations and artifact readers/writers
  -> authoritative artifact roots and compact SQLite state
```

The Web must not become a financial calculation layer.

## Decisions Made

Sprint 169 approved these M30 decisions:

1. M30 reviews strategy-level portfolio scenarios, not runtime account positions.
2. Baseline and proposed scenarios use explicit static non-negative weights.
3. No automatic weight normalization, optimization, recommendation, or allocation
   is allowed.
4. The first version supports at most 12 explicitly selected components.
5. Baseline and proposed scenarios share one exact aligned historical source and
   evaluation window.
6. Concentration includes largest weight, top-three concentration, HHI, effective
   component count, and weight deltas.
7. Review exposure means scenario weights and authoritative universe coverage,
   not account holdings or notional exposure.
8. Interaction includes transparent symbol-set overlap and historical Pearson
   return correlation where valid.
9. Proposed impact compares baseline and proposed historical portfolio behavior
   using existing portfolio/risk/drawdown/contribution authority.
10. Undefined values remain unavailable with warnings; `NaN` and infinity are not
    serialized as product evidence.
11. Full source, analysis, and decision payloads remain immutable artifact files.
12. SQLite stores compact review identity, references, digests, status,
    idempotency, actor, timestamp, and conflict metadata only.
13. One review has at most one settled `approved`, `rejected`, or `deferred`
    decision.
14. Changed evidence, assumptions, or weights require a new review identity.
15. M30 approval is governance evidence only and has no lifecycle, account, order,
    execution, or broker side effect.
16. M31 may reference an M30 review, but must establish separate account and ledger
    truth.

## Planned API and Web Boundary

Conceptual API:

```text
POST /api/v1/portfolio-reviews
GET  /api/v1/portfolio-reviews
GET  /api/v1/portfolio-reviews/{review_id}
POST /api/v1/portfolio-reviews/{review_id}/decision
```

Conceptual Web routes:

```text
/portfolio-reviews
/portfolio-reviews/new
/portfolio-reviews/[reviewId]
```

Exact contracts belong to later implementation Issues.

## Approved Sprint Sequence

```text
S169 architecture and planning
  -> S170 portfolio review source/input and scenario contracts
  -> S171 concentration and review-exposure analysis
  -> S172 strategy interaction and proposed-impact analysis
  -> S173 immutable review and human-decision artifacts
  -> S174 persistence, application service, and API
  -> S175 bilingual Founder Web workflow
  -> S176 workflow integration, Demo, and acceptance hardening
  -> S177 M30 closeout and M31 handoff
```

### S170 — Portfolio Review Input and Scenario Contract Foundation

Owner: Codex.

Define immutable source/component/evidence/aligned-return contracts and baseline /
proposed scenario contracts.

Do not add analysis, artifact writing, persistence, API, Web, account, market,
order, or runtime behavior.

### S171 — Concentration and Exposure Analysis Foundation

Owner: Codex.

Add deterministic concentration, weight-delta, review-exposure, and available
universe-coverage summaries.

Do not add correlation, proposed portfolio risk impact, optimization,
recommendation, or automatic allocation.

### S172 — Strategy Interaction and Proposed Portfolio Impact Foundation

Owner: Codex.

Add supported symbol overlap, historical return interaction, baseline/proposed
portfolio behavior, contribution context, and explicit deltas.

Do not add forecasts, factor models, VaR, stress engines, ranking, allocation,
account behavior, market data, or execution.

### S173 — Portfolio Review Artifact and Human Decision Foundation

Owner: Codex.

Define immutable analysis and decision artifacts, schema/digest rules, references,
write-once behavior, and exact human outcomes.

Do not add SQLite, migration, application service, API, Web, lifecycle mutation,
or execution.

### S174 — Durable Portfolio Review Persistence and Application/API Foundation

Owner: Codex.

Add one explicitly reviewed migration, compact repositories, artifact I/O,
idempotent application commands, list/detail/decision API, OpenAPI, generated
contracts, and stable errors.

Do not add Paper Account/ledger, market session, strategy-to-order, execution,
worker, scheduler, or broker behavior.

### S175 — Founder Portfolio Decision Review Web Workspace

Owner: Codex.

Add complete English/Simplified Chinese list, create, detail, analysis, warning,
audit, and explicit decision experience.

Do not calculate financial values, normalize weights, auto-select evidence,
recommend a strategy, or allocate capital in the browser.

### S176 — Portfolio Review Workflow Integration, Demo, and Acceptance Hardening

Owner: Codex.

Complete explicit source integration, deterministic isolated Demo evidence,
end-to-end tests, errors, audit, documentation, and Founder acceptance guidance.

Codex must not perform Docker runtime acceptance. M31+ remains out of scope.

### S177 — Milestone 30 Closeout and M31 Handoff

Owner: CTO.

Verify exit criteria, record Founder acceptance, close M30, and create the exact
handoff to M31 account/ledger planning.

Documentation only.

## Documentation Delivered

Added:

```text
docs/architecture/portfolio-level-decision-review.md
docs/milestones/milestone-030-portfolio-level-decision-review-foundation.md
docs/sprints/sprint-169-milestone-30-architecture-and-planning.md
```

Updated project planning context to mark M30 In Progress and identify S170 as the
next implementation sprint after Founder merge.

## Preserved Boundaries

Sprint 169 did not add or modify:

- Python or TypeScript runtime behavior;
- tests;
- financial calculations;
- dependencies or lockfiles;
- OpenAPI or generated contracts;
- API or Web routes;
- persistence models, repositories, or migrations;
- migration head `0005_paper_job_result_references`;
- Demo data or installer behavior;
- Docker or Compose behavior;
- proxy configuration;
- lifecycle semantics;
- Paper Job behavior;
- account, market, order, fill, execution, worker, scheduler, broker, QMT, or
  real-money behavior.

## Verification Boundary

No Docker runtime command was authorized or performed.

The complete repository gate remains:

```text
uv run python scripts/check.py
```

The documentation PR relies on repository CI where the CTO connector environment
cannot execute the local checkout gate. The Founder retains merge authority.

## Next Step

After the Sprint 169 PR is merged and Issue #335 is closed as completed, verify
`main` and create the authoritative implementation Issue for:

```text
Sprint 170 — Portfolio Review Input and Scenario Contract Foundation
```

Do not hand Codex a broader M30 implementation prompt before the S170 Issue body
exists.
