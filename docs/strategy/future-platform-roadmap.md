# Future Platform Roadmap — Founder-Level CTO Plan

## Purpose

El-Psy-Quant is an AI-native quantitative research operating system that turns
trading ideas into reproducible, auditable, risk-aware evidence and explicit
human decisions before real capital is deployed.

The platform must not become a loose collection of strategy scripts, an
autonomous trading bot, or a premature distributed system.

## Long-Term Product Chain

```text
trusted research evidence
  -> realistic backtest and Paper Trading evidence
  -> explicit comparison and governance
  -> usable Founder decision workspace
  -> portfolio-level decision review
  -> execution-risk and live-readiness controls
  -> broker-neutral adapter
  -> tightly controlled live pilot
```

## Current State

Milestones 1–28 are Complete.

```text
M25 — Paper Trading Productization Planning                 Complete
M26 — Paper Trading Application Service Foundation          Complete
M27 — Persistence and Paper Job Control Foundation          Complete
M28 — Founder Paper Trading Web Workspace                   Complete
M29 — Product Feedback and Hardening                        In Progress
M30 — Portfolio-Level Decision Review Foundation            Deferred
```

Milestone 28 delivered the first usable local Founder Web MVP and one complete
Strategy-to-Human-Decision Demo journey.

Milestone 29 now converts that working MVP into a bilingual, modern, actionable,
and dependable daily-use product.

## Active Milestone 29 — Product Feedback and Hardening

### Objective

```text
working local MVP
  -> complete English / Simplified Chinese product
  -> AI Quant Decision Workspace visual system
  -> Founder Dashboard and workflow information architecture
  -> understandable idempotency, retry, and recovery
  -> actionable errors and audit information
  -> hardened migrations, tests, and local deployment
```

### Product Principles

- Bilingual completeness over partial translation.
- Decision clarity over dashboard density.
- Visible state over hidden automation.
- Actionable recovery over generic errors.
- Local-first simplicity over distributed infrastructure.
- Human judgment over automatic recommendation or approval.
- Raw domain and artifact truth over presentation convenience.
- Accessibility and responsive behavior in both languages.
- Direct Founder feedback over speculative product features.

### M29 Sprint Sequence

| Sprint | Deliverable | Status |
|---:|---|---|
| S161 | Founder Feedback and Product Experience Architecture | Complete |
| S162 | Multilingual Foundation and Simplified Chinese Workspace | Complete |
| S163 | Modern Visual System Foundation | Complete |
| S164 | Founder Dashboard and Workflow Information Architecture Refresh | Complete |
| S165 | Reliability, Idempotency, and Job Recovery Hardening | Implementation complete; Founder reliability acceptance remains |
| S166 | Error Surface, Observability, and Audit Hardening | Next only after S165 acceptance and merge |
| S167 | Migration, Test, and Local Deployment Hardening | Planned |
| S168 | Milestone 29 Closeout and M30 Handoff | Planned |

Internationalization precedes visual-system implementation so English and
Simplified Chinese both shape typography, spacing, component sizing, and content
hierarchy. Visual foundations precede Dashboard restructuring.

## Sprint 161 Architecture Decisions

### Internationalization

```text
Supported locales: en, zh-CN
Default/fallback: en
Routes: unchanged, no locale prefix
Locale persistence: validated cookie
First-use hint: supported browser language
Implementation direction: next-intl
Backend-translated responses: rejected
Database locale preference: rejected
```

The Web layer owns product localization. Backend API values, schemas, error
codes, IDs, timestamps, and artifact payloads remain stable and untranslated.

Localized labels may be shown alongside raw authoritative values:

```text
已成功
succeeded
```

Locale formatting is display-only and must not recompute financial values or
replace exact audit representations.

Sprint 162 implements this decision through pinned `next-intl`, exact static
catalogs, validated request-level locale resolution, a same-origin locale-cookie
route, and an accessible shell switcher. Existing unprefixed routes, generated
transport, backend ownership, and Standard/Demo isolation remain unchanged.
Founder bilingual runtime acceptance is complete and Sprint 162 is merged.

### Product Experience

The target is an **AI Quant Decision Workspace**:

- modern neutral product identity;
- bilingual-safe sans-serif typography;
- clear information hierarchy;
- readable forms and ordered tables;
- strong state and workspace-mode identity;
- progressive disclosure of raw IDs and audit details;
- accessible empty/error/recovery states; and
- workflow guidance without strategy recommendation.

It is not a marketing site, live trading terminal, academic archive, or
autonomous AI decision engine.

Sprint 163 implements that direction with one exact Web-owned semantic token
system; bilingual-safe system typography; a modern responsive shell; persistent
Standard/Paper and Demo identity; standardized action, status, state, table,
form, disclosure, and audit patterns; and deterministic responsive/accessibility
contracts. Founder local rendered visual acceptance and merge are complete.

### Founder Dashboard

Overview should help answer:

```text
What workspace am I in?
Is the product healthy and configured?
What recent paper activity exists?
Which records may need explicit human attention?
What safe workflow action can I choose next?
```

Dashboard “attention” must be based on explicit operational/workflow state, not
strategy quality. No ranking, recommendation, automatic approval, or capital
allocation is permitted.

Existing APIs must be used without inventing relationships or lifecycle state.
Any missing aggregate/read contract requires a separate authoritative Issue.

Sprint 164 implements this Dashboard through bounded frontend composition of
the existing health, Demo descriptor, research-run list, evidence-manifest list,
and Paper Job list contracts. Regions retain independent states and read retry;
Paper Job activity preserves backend order, duplicates, raw status, timestamps,
attempt detail, result authority, and exact links; comparison continuation is
explicit and preserves two to four distinct nonblank IDs as repeated ordered
`job_id` values; Evidence Manifest label and complete raw identity remain
visible; research and evidence remain separate; Standard guidance stays
generic; and Demo relationships remain descriptor-driven.

The implementation adds no backend contract, durable lifecycle state, unified
cross-source chronology, ranking, recommendation, browser financial
calculation, polling, or Dashboard command. Founder local Dashboard acceptance
and merge are complete.

### Paper Job reliability

Sprint 165 exposes explicit `created`/`replayed` submission and
`requeued`/`succeeded`/`failed` recovery outcomes. Run now owns a deterministic
synchronous claim transaction before HTTP 202, while execution remains one
non-durable post-response callback over the already-created attempt. This
strengthens duplicate-command winner/loser behavior without claiming
exactly-once execution.

Retry remains non-executing `failed -> queued`; Recover remains explicit
Founder-directed reconciliation against a required UTC threshold. Exclusive
file creation, immutable attempts, optimistic recovery, and one atomic
job/attempt/reference terminal transaction preserve artifact authority and
rollback recoverability. Migration head remains `0005`; no cleanup, overwrite,
worker, lease, heartbeat, scheduler, polling, automatic command, financial
ranking, or lifecycle behavior is added. Founder reliability acceptance remains
before merge; S166 becomes next only after acceptance and merge.

## Product and Architecture Records

```text
docs/sprints/sprint-161-founder-feedback-and-product-experience-architecture.md
docs/product/founder-feedback-register.md
docs/architecture/internationalization.md
docs/product/localization-glossary.md
docs/product/product-experience-direction.md
docs/product/founder-dashboard-information-architecture.md
docs/product/milestone-029-product-feedback-and-hardening-plan.md
```

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

### Domain authority

Existing research, evaluation, Paper Trading, comparison, promotion, decision,
report, and lifecycle modules remain authoritative.

The Web and API layers must not duplicate:

- financial calculations;
- Paper Trading execution semantics;
- comparison meaning;
- governance validation;
- lifecycle transition rules; or
- human-control requirements.

### Artifact authority

Completed research, paper, governance, and report payloads remain authoritative
in files under configured roots.

SQLite stores compact product indexes, references, Paper Job state, attempts,
idempotency records, and result references. It must not become a competing full
artifact store.

### Lifecycle authority

- No independently authoritative mutable lifecycle `current_state` field.
- Proposals remain non-executing.
- Human review remains governance evidence.
- Product state may only be derived from approved immutable evidence through an
  explicit future contract.

### Paper Job authority

Paper Job state remains mutable operational state separate from lifecycle
governance:

```text
queued
running
succeeded
failed
canceled
```

Idempotency is replay-safe submission identity, not exactly-once execution.
Retry and recovery remain explicit manual operations.

### Browser boundary

The browser never directly accesses:

- SQLite;
- artifact directories;
- Python domain modules;
- Demo source files;
- QMT or MiniQMT; or
- any broker.

## Codex and Founder Verification Policy

Codex owns deterministic repository verification:

```text
uv run python scripts/check.py
```

Codex may run non-starting static Compose checks when relevant:

```text
docker compose config
docker compose -f compose.yaml -f compose.demo.yaml config
```

Codex does not attempt Docker image build, Compose startup, container startup, or
container smoke verification because proxy instability makes network-dependent
runtime checks unreliable.

The Founder owns local Docker runtime and browser acceptance before merge.

See:

```text
docs/engineering/codex-docker-verification-boundary.md
```

## M29 Success Boundary

By M29 closeout:

- all Founder workflows are complete in English and Simplified Chinese;
- the product uses one coherent bilingual visual system;
- Overview supports bounded daily decision navigation;
- operational replay/retry/recovery is understandable;
- supported failures expose actionable localized guidance and stable technical
  identity;
- Standard and Demo local operation remains reproducible and isolated;
- raw domain/artifact/audit truth remains intact; and
- the complete repository quality gate passes.

M29 success is not measured through strategy profitability, alpha, approval
rate, trading volume, or live execution.

## Deferred Milestone 30

Milestone 30 resumes portfolio-level decision review only after M29 proves that
the local Founder product is understandable and dependable.

Potential scope may include:

- portfolio-level evidence references;
- concentration and exposure context;
- strategy interaction review;
- portfolio impact in explicit human decisions; and
- new governance contracts without automatic capital allocation.

M30 is not permission for broker or live-trading work.

## Future Execution Direction

Broker-specific systems remain adapters behind broker-neutral domain models:

```text
Browser
  -> Web/API
  -> broker-neutral execution command
  -> Windows QMT agent
  -> MiniQMT
  -> broker
```

No browser-to-QMT direct connection is allowed. No live QMT work begins before
portfolio review, execution-risk governance, live-readiness controls,
operational readiness, and explicit human approval exist.

## Explicitly Deferred

Unless a future milestone explicitly approves them:

- broker integration;
- QMT/MiniQMT runtime integration;
- real-money trading;
- automatic strategy ranking or recommendation;
- automatic lifecycle transition or approval;
- automatic capital allocation;
- SaaS, multi-tenancy, or complex RBAC;
- microservices, Kubernetes, Kafka, or Redis clusters;
- distributed job infrastructure; and
- broad real-time trading-terminal behavior.

## Founder-Level Principles

1. Reproducibility beats convenience.
2. Evaluation discipline precedes strategy complexity.
3. Costs, slippage, benchmarks, and risk context precede serious claims.
4. Stable interfaces precede strategy proliferation.
5. Paper state and auditability precede broker integration.
6. Governance evidence remains human-controlled.
7. A proposal is not execution.
8. Artifact files remain completed-output authority.
9. Product metadata must not replace domain truth.
10. Visible failure is better than hidden automation.
11. Real Founder feedback outranks speculative features.
12. Internationalization precedes visual-system finalization.
13. Codex tests code; the Founder accepts Docker runtime behavior.
14. Real capital remains deferred until the full evidence, portfolio, risk,
    operational, and approval chain is strong.
