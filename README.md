# El-Psy-Quant

An AI-native quantitative research and trading platform built in public.

## Mission

Build a production-ready quantitative research platform from zero to production,
using AI as an engineering teammate while keeping human judgment in control.

The goal is not to claim a magic profitable strategy. The goal is to build a
reproducible, auditable, risk-aware platform that can research, test, review,
operate, and improve trading ideas before real capital is deployed.

## Current Status

Milestones 1–28 are **Complete**.

The active milestone is:

```text
Milestone 29 — Product Feedback and Hardening — In Progress
```

The current implementation sprint is:

```text
Sprint 163 — Modern Visual System Foundation
```

Sprints 161 and 162 are complete. Sprint 163 implements one coherent modern
bilingual visual system across the complete Founder workspace. Implementation is
complete in the Sprint 163 branch; Founder local Standard/Demo rendered visual
acceptance and the merge decision remain pending. The next sprint may begin only
after both:

```text
Sprint 164 — Founder Dashboard and Workflow Information Architecture Refresh
```

## Product Direction

Milestone 28 delivered the first usable local Founder Web MVP:

- local Next.js Founder workspace;
- versioned FastAPI API;
- paired minimal Founder authentication;
- SQLite product/job persistence through Alembic and SQLAlchemy;
- authoritative research, governance, and paper artifact reads;
- explicit Paper Job submit, run, cancel, retry, recover, status, attempts, and
  result workflows;
- ordered result comparison without ranking or browser recomputation;
- non-executing lifecycle proposal and human-review workflows;
- reproducible Standard Docker Compose startup;
- isolated disposable Demo Workspace startup; and
- one complete guided Strategy-to-Human-Decision journey.

Milestone 29 turns that working MVP into a product suitable for routine Founder
use:

```text
complete English / Simplified Chinese experience
  -> modern AI Quant Decision Workspace visual system
  -> Founder Dashboard and workflow information architecture
  -> clearer idempotency, retry, and recovery
  -> actionable errors and audit information
  -> hardened migrations, tests, and local deployment
```

The target product remains local-first, Founder-only, minimally authenticated,
Paper Trading only, review-oriented, and explicitly human-controlled.

## M29 Sprint Sequence

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

Internationalization precedes the visual system so English and Simplified
Chinese both shape typography, component sizing, spacing, and content hierarchy.

## Approved Architecture

```text
Browser
  -> Next.js Founder workspace
  -> fixed same-origin /api/backend gateway
  -> versioned FastAPI API
  -> thin application services / use cases
  -> existing domain modules and artifact readers
  -> SQLite product repositories and local Paper Job runner
```

Authority rules:

- existing domain modules own financial, paper, comparison, governance, and
  lifecycle behavior;
- API handlers and the Web layer must not duplicate domain calculations;
- completed artifact files remain payload authority;
- SQLite stores compact indexes, references, idempotency data, attempts, jobs,
  and operational state rather than complete artifact payloads;
- Paper Job state remains separate from lifecycle governance;
- lifecycle proposals remain non-executing;
- human review records remain governance evidence and do not silently mutate an
  independently authoritative current state;
- the browser never directly accesses SQLite, artifact directories, Python
  modules, QMT, MiniQMT, or a broker; and
- Demo data remains isolated from real user data.

## M29 Product Architecture Documents

Sprint 161 establishes the M29 contracts in:

```text
docs/sprints/sprint-161-founder-feedback-and-product-experience-architecture.md
docs/product/founder-feedback-register.md
docs/architecture/internationalization.md
docs/product/localization-glossary.md
docs/product/product-experience-direction.md
docs/product/founder-dashboard-information-architecture.md
docs/product/milestone-029-product-feedback-and-hardening-plan.md
docs/sprints/sprint-162-multilingual-foundation-and-simplified-chinese-workspace.md
docs/product/visual-system.md
docs/sprints/sprint-163-modern-visual-system-foundation.md
```

Key approved directions:

- supported locales are `en` and `zh-CN`;
- English is the default and fallback;
- existing routes remain unchanged without locale prefixes;
- locale is stored as a local browser/cookie preference, not database state;
- `next-intl` is the approved Sprint 162 implementation direction;
- backend API values and error codes remain stable and untranslated;
- raw IDs, states, versions, timestamps, and artifact content remain
  authoritative;
- the persistent `English` / `简体中文` switcher updates a validated same-origin
  locale cookie without changing the current route or ordered query parameters;
- deterministic catalog validation enforces exact locale, namespace, and key
  parity before the Web quality gate proceeds;
- the target experience is an **AI Quant Decision Workspace**, not a marketing
  dashboard or autonomous trading terminal; and
- Dashboard guidance remains operational navigation, not strategy ranking,
  approval, or capital recommendation.

Implemented Sprint 163 direction:

- exact semantic tokens own the light neutral palette, bilingual system
  typography, spacing, shape, elevation, controls, focus, motion, and responsive
  thresholds;
- the modern shell keeps Standard/Paper or persistent Demo identity and the
  language switcher visible across every route and representative viewport;
- shared action, status, card, panel, table, form, disclosure, audit, and state
  contracts cover the complete existing workflow; and
- raw values, product behavior, API/domain authority, and human-control
  boundaries remain unchanged.

## Quick Start

### Standard Founder Workspace

Prerequisites:

- Docker Desktop with Compose v2;
- a local checkout; and
- a local-only Founder password.

```powershell
Copy-Item .env.example .env
# Edit .env and replace EL_PSY_QUANT_FOUNDER_PASSWORD.
docker compose up --build --detach
docker compose ps
```

Open:

```text
http://127.0.0.1:3000
```

Run the authenticated smoke verification:

```powershell
docker compose exec web node /app/verify-mvp.mjs
```

Stop while preserving the standard `mvp-data` volume:

```powershell
docker compose down
```

The Standard workspace remains unseeded.

### Isolated Demo Workspace

Stop the Standard instance first because both modes publish the same loopback
ports:

```powershell
docker compose down
docker compose -f compose.yaml -f compose.demo.yaml up --build --detach
docker compose -f compose.yaml -f compose.demo.yaml ps
```

The Demo overlay uses a separate Compose project and `demo-data` volume. The
backend validates and installs the versioned deterministic Demo dataset before
serving.

Stop while preserving Demo storage:

```powershell
docker compose -f compose.yaml -f compose.demo.yaml down
```

Reset only disposable Demo storage:

```powershell
docker compose -f compose.yaml -f compose.demo.yaml down --volumes
docker compose -f compose.yaml -f compose.demo.yaml up --build --detach
```

Do not use the Standard `down --volumes` command unless its real local database
and authoritative artifacts may be deleted.

See:

```text
docs/founder-mvp-local-operations.md
docs/user-guide/README.md
```

## Direct Development and Quality Gate

Install Python and Web dependencies:

```bash
uv sync
npm --prefix web ci
```

Run the complete repository gate:

```bash
uv run python scripts/check.py
```

The gate includes Python tests and linting, package/CLI checks, OpenAPI and
generated TypeScript freshness, ESLint, TypeScript, Web tests, and production
build.

## Explicitly Deferred

Unless a future milestone changes the boundary, do not add:

- broker integration;
- QMT or MiniQMT runtime integration;
- live or real-money trading;
- automatic strategy ranking or recommendation;
- automatic lifecycle transition or approval;
- capital allocation;
- multi-tenancy or complex RBAC;
- cloud SaaS hosting;
- microservices, Kubernetes, Kafka, or Redis clusters; or
- broad real-time trading-terminal behavior.

## Project Documentation

```text
docs/roadmap.md
docs/strategy/future-platform-roadmap.md
docs/milestones/milestone-028-founder-paper-trading-web-workspace.md
docs/closeouts/milestone-028-founder-paper-trading-web-workspace-closeout.md
docs/product/milestone-029-product-feedback-and-hardening-plan.md
```
