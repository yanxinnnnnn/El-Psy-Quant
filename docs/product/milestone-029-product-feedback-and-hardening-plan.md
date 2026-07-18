# Milestone 29 — Product Feedback and Hardening Plan

## Status

Milestone 29 is **In Progress**.

Sprints 161, 162, 163, and 164 are complete. Sprint 165 implementation is
complete in its review branch; Founder Standard/Demo reliability acceptance and
the merge decision remain pending. Sprint 166 must not begin before both are
complete.

## Milestone Objective

Turn the completed M28 local Founder Web MVP into a bilingual, modern,
actionable, and dependable product suitable for routine Founder use.

M29 does not pursue new quantitative capability. It hardens the existing
Strategy-to-Human-Decision workflow.

```text
usable local MVP
  -> complete English / Simplified Chinese product
  -> coherent modern visual system
  -> decision-oriented Founder Dashboard
  -> understandable job and recovery workflows
  -> actionable errors and audit detail
  -> reliable local upgrade and deployment
```

## Product Boundaries

The product remains:

- local-first;
- Founder-only;
- minimally authenticated;
- Paper Trading only;
- review-oriented;
- a modular monolith; and
- explicitly human-controlled.

M29 does not add:

- new strategy research capability;
- financial calculations in the browser;
- strategy ranking or recommendation;
- automatic lifecycle transitions;
- automatic approval or capital allocation;
- broker, QMT, MiniQMT, or live trading;
- SaaS, multi-tenancy, or complex RBAC;
- Kubernetes, Kafka, Redis clusters, or microservices; or
- real-money readiness claims.

## Success Measures

By M29 closeout:

- every Founder workflow is complete in `en` and `zh-CN`;
- supported locales do not expose missing-key mixed-language pages;
- the active language is explicit, persistent, and accessible;
- raw domain, API, artifact, and audit values remain unchanged;
- the product uses one coherent bilingual visual system;
- Overview communicates workspace mode, readiness, relevant paper activity,
  bounded attention conditions, and safe workflow continuation;
- Paper Job replay, retry, recovery, and state conflicts are understandable;
- supported failures provide localized explanation, stable technical identity,
  request ID where available, and bounded next steps;
- migrations and Standard/Demo Compose workflows are safe and reproducible;
- the complete Strategy-to-Human-Decision journey remains intact; and
- the full repository quality gate passes.

M29 success is not based on profitability, alpha, approval rate, or live-trading
activity.

## Sprint Sequence

### Sprint 161 — Founder Feedback and Product Experience Architecture

**Objective**

Convert direct Founder feedback into the product, internationalization, visual,
Dashboard, risk, and implementation contracts for M29.

**Deliverables**

- Founder feedback register;
- M29 principles and measurable outcomes;
- internationalization architecture decision;
- English/Simplified Chinese glossary;
- product-experience direction;
- Founder Dashboard information architecture;
- S162–S167 implementation contracts; and
- M29 risk register.

**Boundary**

Documentation only. No runtime, dependency, component, API, migration, or
reliability implementation.

**Founder verification**

Review terminology, locale strategy, product direction, Dashboard scope, and
M29 sequence before merge.

### Sprint 162 — Multilingual Foundation and Simplified Chinese Workspace

**Objective**

Implement complete English and Simplified Chinese product localization before
the visual system is finalized.

**Major deliverables**

- approved App Router internationalization dependency and configuration;
- supported locale allow-list: `en`, `zh-CN`;
- cookie/browser/fallback locale resolution;
- persistent accessible language switcher;
- no locale-prefixed URL change;
- modular translation catalogs;
- complete translation of navigation, metadata, pages, forms, states,
  confirmations, accessibility labels, Demo identity, and stable frontend error
  explanations;
- localized display formatting with raw audit values preserved;
- catalog completeness/static validation;
- English and Simplified Chinese component and route tests; and
- updated user documentation.

**Dependencies**

- `docs/architecture/internationalization.md`;
- `docs/product/localization-glossary.md`; and
- existing Next.js App Router and generated API contracts.

**Acceptance themes**

- complete bilingual workflows;
- correct `<html lang>` and metadata;
- no missing-key mixed page;
- route/query preservation;
- no transport or domain mutation;
- no form loss without an explicit bounded design;
- Standard and Demo coverage; and
- full quality gate.

**Out of scope**

- broad visual refresh;
- Dashboard redesign;
- backend-translated responses;
- locale-prefixed routes;
- database locale preferences; and
- financial or lifecycle changes.

**Founder verification**

Use both locales across the full Demo journey and representative Standard empty
and error states.

**Implementation status**

Complete and merged. The implementation uses pinned
`next-intl`, static matching `en` and `zh-CN` catalogs, validated cookie/browser
locale resolution, an accessible same-origin shell switcher, localized metadata
and complete workspace copy, display-only localized formatting with raw values,
static error-code explanations, and deterministic catalog validation. Founder
local bilingual runtime acceptance is complete.

### Sprint 163 — Modern Visual System Foundation

**Objective**

Replace the current academic/internal-tool presentation with a coherent modern
bilingual product system without changing workflow or domain semantics.

**Major deliverables**

- design tokens for color, typography, spacing, radius, elevation, borders, and
  state presentation;
- bilingual-safe system font stack or separately reviewed font dependency;
- modern workspace shell and navigation treatment;
- standardized cards, tables, forms, buttons, status indicators, empty states,
  error states, and audit-detail patterns;
- responsive behavior;
- contrast and accessibility verification;
- persistent unmistakable Demo identity; and
- representative English/Chinese visual regression or layout coverage.

**Dependencies**

- S162 localization runtime and complete catalogs;
- `docs/product/product-experience-direction.md`.

**Acceptance themes**

- coherent system across all existing routes;
- Chinese and English both fit without clipping or fixed-height failures;
- raw audit data remains accessible;
- no operational status is mistaken for financial performance;
- no workflow behavior change; and
- full quality gate.

**Out of scope**

- new Dashboard aggregation;
- new chart platform without authoritative data;
- new financial calculations;
- marketing-site redesign; and
- broker/live terminal behavior.

**Founder verification**

Review the complete Demo journey in both languages at desktop and narrow widths.

**Implementation status**

Complete and merged. One exact semantic token system, bilingual-safe system
typography, the responsive workspace shell, persistent Standard/Demo identity,
and shared action/status/state/table/form/audit contracts cover every existing
route. Founder local rendered visual acceptance is complete.

### Sprint 164 — Founder Dashboard and Workflow Information Architecture Refresh

**Objective**

Turn Overview from a feature directory into a bounded decision-navigation
workspace using the S163 visual system and existing authoritative data where
possible.

**Major deliverables**

- workspace mode and product readiness summary;
- recent paper activity;
- authoritative result/review continuation;
- explicit operational/human-attention conditions;
- research/governance evidence entry points;
- Demo descriptor-driven exact journey;
- Standard generic workflow guidance without false record relationships;
- clear distinction between existing API coverage and any newly approved thin
  backend contract; and
- bilingual accessible responsive layout.

**Dependencies**

- S162 localization;
- S163 visual system;
- `docs/product/founder-dashboard-information-architecture.md`.

**Acceptance themes**

- answers the five Dashboard questions;
- no ranking or recommendation;
- no unsupported persistent lifecycle state;
- no hidden job/lifecycle commands;
- partial failures remain visible;
- no browser financial recomputation; and
- full quality gate.

**Out of scope**

- auto-run, auto-retry, auto-recover, auto-approve;
- strategy ranking;
- capital allocation;
- live market widgets; and
- implicit cross-record relationships.

**Founder verification**

Confirm the Dashboard improves daily navigation without overstating what the
backend knows.

**Implementation status**

Complete and merged. Overview composes
the existing process-health, Demo descriptor, research-run list,
evidence-manifest list, and Paper Job list contracts into independently stateful
regions. Partial availability, stable error identity, individual retry,
backend order and duplicates, exact job/result links, explicit repeated ordered
comparison selection for two to four distinct nonblank job IDs, complete raw
Evidence Manifest identity, separate research/evidence authority, Standard
generic workflow choices, and Demo descriptor relationships are preserved.

No backend or generated contract, database, domain, authentication, gateway,
locale-routing, command, financial-calculation, polling, or durable lifecycle
read-model change was made. Founder local Standard/Demo Dashboard acceptance is
complete.

### Sprint 165 — Reliability, Idempotency, and Job Recovery Hardening

**Objective**

Make existing durable Paper Job semantics understandable and dependable for
routine Founder operation.

**Major deliverables**

- review and harden keyed replay behavior and conflict explanations;
- clear submission versus Run semantics;
- clearer status-dependent available actions;
- safe Retry versus Recover guidance;
- explicit stale-time input and validation experience;
- stronger concurrent/state-conflict tests;
- bounded result/artifact collision handling;
- no hidden automatic retry or recovery; and
- bilingual user and operations documentation.

**Dependencies**

- S162 localized copy/error mapping;
- S163 action and form system;
- existing M27 durable job contracts.

**Acceptance themes**

- no exactly-once claim;
- no state transition weakening;
- deterministic idempotency conflicts;
- safe manual control;
- clear operational audit; and
- full quality gate.

**Out of scope**

- distributed queues;
- automatic job scheduler;
- multiple workers;
- broker execution; and
- lifecycle automation.

**Founder verification**

Exercise submit/replay/conflict, Run, failure, Retry, and Recover scenarios.

**Implementation status**

Implementation complete; Founder reliability acceptance remains. Submission
reports `created` or `replayed`; Run atomically commits one running job and
attempt before HTTP 202; the non-durable post-response task executes the
existing claim; Retry stays clean-output, non-executing, and attempt-free; and
Recover reports `requeued`, `succeeded`, or `failed` from the exact
Founder-supplied UTC threshold. One centralized bilingual Web action policy,
conflict guidance, collision protection, optimistic reconciliation, and focused
concurrency/rollback coverage preserve settled evidence and artifact authority.

No migration, table, column, status, lease, heartbeat, worker, scheduler,
polling, cleanup, force overwrite, financial calculation, lifecycle automation,
or Sprint 166 behavior was added. S166 becomes next only after Sprint 165 is
merged and Founder Standard/Demo reliability acceptance is complete.

### Sprint 166 — Error Surface, Observability, and Audit Hardening

**Objective**

Make failures and audit evidence actionable without exposing sensitive internal
detail or introducing a distributed observability platform.

**Major deliverables**

- inventory and classify stable product error codes;
- localized error title/explanation/recovery mapping;
- consistent request-ID display;
- bounded operation/job correlation detail;
- clearer unavailable versus invalid versus empty states;
- audit detail presentation patterns;
- operator troubleshooting matrix;
- sanitized logging review; and
- deterministic error/regression coverage.

**Dependencies**

- S162 localization/error catalogs;
- S163 visual error/audit patterns;
- existing request ID and sanitized API error contracts.

**Acceptance themes**

- errors remain stable and bounded;
- no internal exception leakage;
- recovery guidance is safe;
- raw error code/request ID remain available;
- no hidden telemetry dependency; and
- full quality gate.

**Out of scope**

- cloud APM;
- distributed tracing infrastructure;
- user analytics;
- external log service; and
- credentials or payload logging.

**Founder verification**

Trigger representative unavailable, invalid, not-found, conflict, and job
failure cases in both languages.

### Sprint 167 — Migration, Test, and Local Deployment Hardening

**Objective**

Make local installation, upgrade, startup, verification, and reset dependable
for daily use and future milestone handoff.

**Major deliverables**

- migration-chain and upgrade-path verification;
- Standard and Demo data-volume isolation regression coverage;
- Compose build/start/health/smoke hardening;
- deterministic reinstall and safe Demo reset;
- standard real-data preservation guidance;
- bilingual end-to-end verification;
- fresh-checkout and existing-volume test matrix;
- dependency/offline-install risk review;
- local backup/restore or export guidance only where current contracts support it;
- consolidated operations runbook.

**Dependencies**

- S162–S166 product behavior;
- existing Alembic, Compose, Demo installer, and quality gates.

**Acceptance themes**

- no real data deletion during Demo operations;
- migration failures are bounded;
- startup is reproducible;
- smoke path covers both locales and modes;
- documented commands match actual behavior; and
- full quality gate.

**Out of scope**

- cloud deployment;
- Kubernetes;
- production SaaS backup systems;
- multi-machine coordination; and
- live broker operations.

**Founder verification**

Test fresh Standard startup, Demo startup/reset, return to Standard, and an
upgrade of an existing local volume.

### Sprint 168 — Milestone 29 Closeout and M30 Handoff

**Objective**

Verify the bilingual modernized product and daily-use hardening, record remaining
limitations, and decide the next portfolio-level review scope.

**Major deliverables**

- Founder acceptance across both locales and modes;
- completed M29 success-measure review;
- authority and non-goal verification;
- final operations/user documentation;
- remaining product-debt register;
- Milestone 29 closeout record; and
- explicit M30 handoff decision.

**Boundary**

Documentation and verification closeout unless a separately approved blocker
must be fixed first.

## Cross-Sprint Architecture Rules

```text
Browser
  -> Next.js Founder workspace
  -> fixed same-origin /api/backend gateway
  -> versioned FastAPI API
  -> thin application services
  -> existing repositories, domain modules, and artifact readers
  -> isolated SQLite and authoritative artifact roots
```

- Domain modules remain financial and governance authority.
- Artifact files remain completed-output payload authority.
- SQLite remains compact metadata and operational state.
- Raw API values remain unchanged by localization.
- Paper-job state remains separate from lifecycle governance.
- Lifecycle proposals remain non-executing.
- Human review remains explicit evidence.
- Demo and Standard storage remain isolated.
- No browser access to SQLite, files, Python, QMT, or broker.
- Every command remains explicit and user-controlled.

## Milestone Risk Register

| Risk | Primary sprint | Mitigation |
|---|---:|---|
| Partial translation creates mixed pages. | S162 | Catalog equality checks and complete locale route tests. |
| Hardcoded English remains hidden in components/tests. | S162 | Inventory, static search/checks, and both-locale coverage. |
| Translation changes financial/governance meaning. | S162 | Approved glossary and raw-value preservation. |
| Locale switch loses unsaved form state. | S162 | Explicit Paper Job/Lifecycle tests and bounded switching architecture. |
| Server/client locale disagreement causes hydration errors. | S162 | One validated request locale source and provider contract. |
| Chinese typography breaks English-sized layouts. | S163 | Bilingual design tokens and representative content tests. |
| Visual refresh hides audit data. | S163 | Progressive disclosure with exact detail retained. |
| Dashboard requires unavailable backend truth. | S164 | API coverage matrix; no inferred relationships/state. |
| Workflow guidance is interpreted as investment advice. | S164 | Operational navigation only; no ranking or recommendation. |
| Hardening introduces hidden automation. | S165 | Explicit manual commands and state transition regression tests. |
| Error detail leaks sensitive internals. | S166 | Stable sanitized contracts and logging review. |
| Dependency additions weaken local/offline builds. | S162/S167 | Pinned lockfiles, deterministic install, and build verification. |
| Migration/reset damages real data. | S167 | Volume isolation, refusal rules, upgrade matrix, and destructive-command warnings. |
| Product polish weakens Demo identity. | S163/S164 | Persistent semantic Demo label and warning in both locales. |

## Founder Review Gates

Founder review is required after each implementation PR. No M29 PR is merged by
Codex or the CTO.

Particular product gates:

- S162: terminology and complete bilingual experience;
- S163: visual identity and bilingual layouts;
- S164: Dashboard usefulness and non-recommendation boundary;
- S165: operational replay/retry/recovery clarity;
- S166: actionable and safe errors;
- S167: fresh and existing local deployment workflows; and
- S168: milestone closeout.
