# AGENTS.md

This file defines the shared context and operating rules for AI agents working on
El-Psy-Quant.

## Project Identity

El-Psy-Quant is an AI-native quantitative research and trading platform built as
a startup product, not a one-off strategy script.

## Mission

Build a production-ready platform that turns trading ideas into reproducible,
auditable, risk-aware evidence and explicit human decisions before real capital
is deployed.

## Operating Model

- The human Founder makes final product decisions, performs local startup
  acceptance, and manually merges pull requests.
- ChatGPT acts as CTO for milestone planning, architecture boundaries, Issue
  creation, documentation-only planning/closeout work, and PR review.
- Codex acts as implementation developer for coding sprints.
- The CTO and Codex must not merge PRs unless the Founder explicitly requests it.
- The GitHub Issue body is the authoritative implementation specification.
- Implementation PR bodies must begin exactly with `Closes #<issue-number>`.
- PRs must be Ready for review, not left as Draft.

## Engineering Principles

- Use Python for backend/domain code and TypeScript/Next.js for the Founder Web
  workspace.
- Prefer `uv`, a `src/` layout, `pytest`, `ruff`, explicit type hints, and small
  composable modules.
- Preserve deterministic tests and avoid hidden network calls.
- Prefer a modular monolith and local-first operation over premature distributed
  infrastructure.
- Keep financial calculations explicit and owned by domain modules.
- Keep broker-specific behavior behind future adapters.
- Do not add or modify proxy configuration in the repository.
- Do not modify project files to accommodate a development proxy.
- Never commit local `.env`, credentials, tokens, machine-specific paths, or
  private endpoints.

## Codex Verification Boundary

Codex must complete deterministic repository verification before opening a PR:

```text
uv run python scripts/check.py
```

Codex may also run non-starting, non-network-heavy static checks when required by
an Issue, for example:

```text
docker compose config
docker compose -f compose.yaml -f compose.demo.yaml config
```

Codex must **not** attempt:

- `docker compose build`;
- `docker compose up`;
- image pulls performed solely for local product acceptance;
- container startup;
- container-based MVP smoke verification; or
- any equivalent Docker runtime acceptance step.

Reason: Docker image dependency downloads are vulnerable to unstable local proxy
conditions and can produce non-product timeouts.

The PR must state truthfully that:

- repository tests/static checks passed;
- Docker build/start was intentionally not attempted under project policy; and
- local Standard/Demo startup acceptance remains the Founder’s responsibility.

Failure to run Docker build/start is not an implementation failure when the
required deterministic tests and static configuration checks pass.

## Quant and Governance Principles

- Never claim a strategy is profitable without evidence.
- Avoid look-ahead and survivorship bias where applicable.
- Distinguish research, backtesting, Paper Trading, and future live execution.
- Risk and audit context matter as much as return metrics.
- A lifecycle proposal is non-executing.
- A human review record is governance evidence, not proof that runtime execution
  occurred.
- Product guidance must not become strategy ranking, approval, or capital advice.

## Definition of Done

A task is complete only when:

- scope matches the authoritative Issue;
- deterministic tests are included where appropriate;
- documentation matches behavior;
- assumptions and limitations are explicit;
- authority boundaries remain intact;
- `uv run python scripts/check.py` passes;
- approved static Compose checks pass where applicable;
- the PR records that Founder Docker startup acceptance remains pending;
- the PR is Ready for review; and
- the PR is not merged by Codex or the CTO.

## Completed Foundations

Milestones 1–28 are Complete.

The completed productization sequence is:

```text
M25 — S137      Paper Trading Productization Planning
M26 — S138-S144 Paper Trading Application Service Foundation
M27 — S145-S151 Persistence and Paper Job Control Foundation
M28 — S152-S160 Founder Paper Trading Web Workspace
```

Milestone 28 delivered:

- a local Founder-only Next.js workspace;
- versioned FastAPI application API;
- paired minimal Founder authentication;
- SQLite/Alembic product persistence;
- durable manually controlled Paper Jobs;
- authoritative result and evidence inspection;
- explicit ordered result comparison;
- non-executing lifecycle proposal and human-review workflows;
- Standard Docker Compose startup;
- isolated disposable Demo Workspace startup; and
- one complete Strategy-to-Human-Decision Demo journey.

## Current Focus

The active milestone is:

```text
Milestone 29 — Product Feedback and Hardening — In Progress
```

The current sprint is:

```text
Sprint 163 — Modern Visual System Foundation
```

Sprints 161 and 162 are complete. Sprint 163 implementation is complete in its
review branch. Founder Standard/Demo rendered visual acceptance and the merge
decision remain pending. Do not begin the next sprint until both are complete:

```text
Sprint 164 — Founder Dashboard and Workflow Information Architecture Refresh
```

## M29 Product Outcome

M29 must turn the working M28 MVP into a product reliable enough for routine
Founder use:

```text
complete English / Simplified Chinese product
  -> modern AI Quant Decision Workspace visual system
  -> Founder Dashboard and workflow information architecture
  -> understandable idempotency, retry, and recovery
  -> actionable errors and audit information
  -> hardened migrations, tests, and local deployment
```

Approved sequence:

```text
S161 Founder Feedback and Product Experience Architecture
S162 Multilingual Foundation and Simplified Chinese Workspace
S163 Modern Visual System Foundation
S164 Founder Dashboard and Workflow Information Architecture Refresh
S165 Reliability, Idempotency, and Job Recovery Hardening
S166 Error Surface, Observability, and Audit Hardening
S167 Migration, Test, and Local Deployment Hardening
S168 Milestone 29 Closeout and M30 Handoff
```

Internationalization precedes visual-system implementation so English and
Simplified Chinese both shape component sizing, typography, spacing, and content
hierarchy.

## M29 Architecture Documents

```text
docs/sprints/sprint-161-founder-feedback-and-product-experience-architecture.md
docs/product/founder-feedback-register.md
docs/architecture/internationalization.md
docs/product/localization-glossary.md
docs/product/product-experience-direction.md
docs/product/founder-dashboard-information-architecture.md
docs/product/milestone-029-product-feedback-and-hardening-plan.md
docs/product/visual-system.md
docs/sprints/sprint-163-modern-visual-system-foundation.md
```

Approved internationalization direction:

- locales: `en`, `zh-CN`;
- English default/fallback;
- no locale-prefixed URLs;
- cookie/browser/fallback locale resolution;
- `next-intl` implementation direction;
- complete static catalogs;
- frontend-owned localized explanations;
- backend contracts remain stable and untranslated; and
- raw IDs, states, values, timestamps, schemas, and artifact content remain
  authoritative.

Implemented Sprint 162 contract:

- `next-intl` owns App Router message context and locale-aware presentation;
- supported locale values remain exactly `en` and `zh-CN`;
- a validated `el_psy_quant_locale` cookie is changed only through the
  same-origin `/api/locale` route;
- the language switcher preserves unprefixed routes, ordered query parameters,
  and in-progress Paper Job and Lifecycle form state;
- message catalogs are static and checked for exact locale, namespace, and key
  parity before the Web gate continues; and
- frontend explanations may be localized, but raw transport, domain, artifact,
  user-entered, timestamp, ordering, duplicate, and quantitative truth is never
  translated or recomputed.

Implemented Sprint 163 contract:

- one Web-owned semantic token system defines the exact light palette,
  bilingual system-font typography, spacing, radius, borders, elevation,
  controls, focus, motion, shell dimensions, content widths, and responsive
  thresholds;
- the solid workspace shell, route-aware navigation, language switcher, and
  Standard/Paper or persistent Demo identity remain visible and accessible;
- shared actions, links, cards, panels, status badges, notices, states, tables,
  forms, disclosures, audit details, and workflow steps cover every current
  route and state;
- status uses localized text plus raw values and never communicates strategy
  profitability or execution authority; and
- representative layout contracts cover `360px`, `768px`, and `1280px+` with
  bounded table/navigation scrolling and reduced-motion behavior.

## Approved Product Architecture

```text
Browser
  -> Next.js Founder workspace
  -> fixed same-origin /api/backend gateway
  -> versioned FastAPI application API
  -> thin application services / use cases
  -> existing domain modules and artifact readers
  -> SQLite product repositories and local Paper Job runner
```

Authority boundaries:

- domain modules own financial, paper, comparison, governance, and lifecycle
  behavior;
- completed artifact files remain payload authority;
- SQLite stores compact metadata and operational state;
- Paper Job state remains separate from lifecycle governance;
- lifecycle proposals remain non-executing;
- human review remains explicit governance evidence;
- the browser never directly accesses SQLite, artifact roots, Python modules,
  QMT, MiniQMT, or a broker;
- Standard and Demo storage remain isolated; and
- authentication and same-origin behavior remain unchanged unless an explicit
  future Issue changes them.

## Explicitly Deferred

Do not add without a future approved milestone/Issue:

- broker or QMT/MiniQMT runtime integration;
- live or real-money trading;
- automatic strategy ranking or recommendation;
- automatic lifecycle transition or approval;
- capital allocation;
- SaaS, multi-tenancy, or complex RBAC;
- microservices, Kafka, Redis clusters, or Kubernetes; or
- broad live-market trading-terminal behavior.
