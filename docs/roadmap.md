# El-Psy-Quant Roadmap

## Purpose

This rolling roadmap turns the sprint-by-sprint project plan into a milestone
timeline.

Guiding principle:

```text
Build a reproducible research and decision platform before adding operational
complexity or real capital.
```

## Timeline Overview

```mermaid
flowchart LR
    M1["M1-M8<br/>Research Workflow Foundations ✅"] --> M9["M9-M15<br/>Quality, Portfolio & Execution Realism ✅"]
    M9 --> M16["M16-M19<br/>Paper Trading & Configured Workflow ✅"]
    M16 --> M20["M20-M24<br/>Governance & Review Workflow ✅"]
    M20 --> M25["M25-M28<br/>Founder Paper Productization ✅"]
    M25 --> M29["M29<br/>Product Feedback & Hardening 🟡"]
    M29 --> M30["M30+<br/>Portfolio Decisions & Execution Readiness"]
```

## Milestone Table

| Milestone | Sprint Range | Status | Theme | Exit Criteria |
|---|---:|---|---|---|
| M1 — Research Pipeline Foundation | S1-7 | Complete | First reproducible strategy pipeline. | Prices produce signals, positions, returns, and equity. |
| M2 — Performance & Local Data Foundation | S8-12 | Complete | Metrics and deterministic local data. | Local research can be evaluated consistently. |
| M3 — Data Reproducibility & Research Workflow | S13-16 | Complete | Cache and reusable data workflows. | Inputs can be persisted and reused. |
| M4 — Research Experimentation Foundation | S17-20 | Complete | Repeatable experiments. | Parameter runs are reviewable without false alpha claims. |
| M5 — Strategy Realism Foundation | S21-24 | Complete | Costs, slippage, and trade visibility. | Backtests include explicit basic frictions. |
| M6 — Risk & Benchmark Foundation | S25-28 | Complete | Evaluation discipline. | Results include benchmark and risk context. |
| M7 — Multi-Asset Research Foundation | S29-32 | Complete | Multi-symbol research. | Independent symbol workflows can be summarized together. |
| M8 — Research Operations Foundation | S33-36 | Complete | Repeatable local operations. | Experiments can be configured and stored consistently. |
| M9 — Project Quality Foundation | S37-41 | Complete | Automated quality gates. | Pull requests are checked consistently. |
| M10 — Experiment Artifact & Comparison Foundation | S42-46 | Complete | Stable run artifacts. | Existing runs can be inspected and compared. |
| M11 — Strategy Interface Foundation | S47-52 | Complete | Stable strategy boundaries. | Strategies plug into configured workflows through an interface. |
| M12 — Data Integrity & Universe Foundation | S53-57 | Complete | Input and universe validation. | Invalid symbol and price inputs are rejected. |
| M13 — Portfolio Construction Foundation | S58-63 | Complete | Portfolio alignment and allocation. | Static portfolio assumptions are explicit. |
| M14 — Portfolio Risk & Attribution Foundation | S64-69 | Complete | Portfolio explanation. | Risk, drawdown, contribution, and attribution are available. |
| M15 — Backtest Execution Realism Foundation | S70-76 | Complete | Explicit execution assumptions. | Order intents, fills, and realism summaries are reviewable. |
| M16 — Paper Trading Foundation | S77-83 | Complete | Local paper state and records. | Accounts, orders, fills, sessions, and artifacts are explicit. |
| M17 — Paper Trading Persistence & Audit Foundation | S84-89 | Complete | Durable paper outputs. | Paper artifacts can be saved, loaded, validated, and summarized. |
| M18 — Paper Trading Workflow Integration Foundation | S90-95 | Complete | Explicit Paper Run boundary. | A paper request can produce and persist a local result. |
| M19 — Configured Paper Workflow Wiring Foundation | S96-102 | Complete | Config-driven paper runs. | Configured runs can produce and reference paper outputs. |
| M20 — Research-to-Paper Promotion Foundation | S103-109 | Complete | Human-controlled promotion governance. | Evidence, candidates, records, and manifests are explicit. |
| M21 — Paper Run Comparison and Review Foundation | S110-116 | Complete | Multi-run review governance. | Paper runs can be referenced, compared, and reviewed. |
| M22 — Decision Governance Foundation | S117-123 | Complete | Strategy-level human decisions. | Decision evidence and human records are explicit. |
| M23 — Report Artifact Foundation | S124-129 | Complete | Deterministic review packaging. | Report sources, summaries, references, and manifests are explicit. |
| M24 — Strategy Review Workflow Foundation | S130-136 | Complete | Human-controlled lifecycle governance. | Proposals and reviews remain non-executing evidence. |
| M25 — Paper Trading Productization Planning | S137 | Complete | Founder product architecture. | M26-M29 staged productization is explicit. |
| M26 — Paper Trading Application Service Foundation | S138-144 | Complete | Thin local API boundary. | Existing capabilities are exposed through versioned schemas. |
| M27 — Persistence and Paper Job Control Foundation | S145-151 | Complete | Durable controllable local jobs. | Product metadata and jobs are inspectable, idempotent, and recoverable. |
| M28 — Founder Paper Trading Web Workspace | S152-160 | Complete | First usable local Founder Web MVP. | The complete paper-decision journey is usable through Web/API. |
| M29 — Product Feedback and Hardening | S161-168 | In Progress | Bilingual product experience and daily-use reliability. | The modernized product is dependable enough for routine Founder use. |
| M30 — Portfolio-Level Decision Review Foundation | TBD | Deferred | Portfolio-level review. | Portfolio impact and concentration are included in human decisions. |

## Completed Milestone 28

M28 delivered:

```text
Next.js Founder workspace
  -> strategy and research inspection
  -> governance and report inspection
  -> durable Paper Job operation
  -> authoritative result inspection
  -> ordered comparison
  -> lifecycle proposal and human review
  -> minimal authentication and Compose startup
  -> isolated Demo Workspace and first-run journey
```

Preserved boundaries:

- domain modules remain financial and governance authority;
- completed artifact files remain payload authority;
- SQLite stores compact metadata and operational state;
- Paper Job state remains separate from lifecycle governance;
- lifecycle proposals remain non-executing;
- the browser uses only the same-origin API boundary; and
- Demo data remains isolated from real user data.

Closeout records:

```text
docs/milestones/milestone-028-founder-paper-trading-web-workspace.md
docs/closeouts/milestone-028-founder-paper-trading-web-workspace-closeout.md
```

## Active Milestone 29 — Product Feedback and Hardening

M29 begins from direct Founder use rather than speculative feature work.

### Product priorities

1. Complete English and Simplified Chinese product support.
2. Move toward an AI Quant Decision Workspace visual identity.
3. Replace Overview feature-directory behavior with bounded decision navigation.
4. Make idempotency, retry, recovery, errors, audit, migrations, and local
   deployment understandable and dependable.
5. Preserve explicit human control and all M28 authority boundaries.

### M29 Sprint Sequence

| Sprint | Deliverable | Status |
|---:|---|---|
| S161 | Founder Feedback and Product Experience Architecture | Complete |
| S162 | Multilingual Foundation and Simplified Chinese Workspace | Complete |
| S163 | Modern Visual System Foundation | Complete |
| S164 | Founder Dashboard and Workflow Information Architecture Refresh | Complete |
| S165 | Reliability, Idempotency, and Job Recovery Hardening | Complete; merged at `61cd11ad7f680509d44e27180bfb33c8a9193896` |
| S166 | Error Surface, Observability, and Audit Hardening | Implementation complete; Founder error/observability acceptance remains |
| S167 | Migration, Test, and Local Deployment Hardening | Next only after S166 acceptance and merge |
| S168 | Milestone 29 Closeout and M30 Handoff | Planned |

Internationalization precedes visual implementation so both languages determine
component sizing, typography, spacing, and content hierarchy.

### Sprint 161 decisions

```text
Locales: en, zh-CN
Default/fallback: en
Routing: existing routes, no locale prefix
Persistence: validated locale cookie
Implementation direction: next-intl
Backend translation: none
Raw domain/transport values: unchanged
Product direction: AI Quant Decision Workspace
Dashboard direction: operational attention and workflow choices, not ranking
```

Architecture and product records:

```text
docs/sprints/sprint-161-founder-feedback-and-product-experience-architecture.md
docs/product/founder-feedback-register.md
docs/architecture/internationalization.md
docs/product/localization-glossary.md
docs/product/product-experience-direction.md
docs/product/founder-dashboard-information-architecture.md
docs/product/milestone-029-product-feedback-and-hardening-plan.md
```

### Sprint 162 implementation

Sprint 162 now provides complete static `en` and `zh-CN` catalogs, validated
cookie/browser/English locale resolution, an accessible route-preserving
language switcher, localized metadata and workspace copy, localized display
formatting with visible raw audit values, static error-code explanations, and a
deterministic catalog gate. Existing unprefixed routes and all M28 authority
boundaries remain unchanged.

Founder local Standard/Demo bilingual browser acceptance is complete and Sprint
162 is merged.

### Sprint 163 implementation

Sprint 163 now provides one exact semantic token system, bilingual-safe system
typography, a modern responsive workspace shell, persistent Standard/Demo
identity, and shared action, status, card, panel, table, form, disclosure,
audit-detail, and state contracts across every current route. Operational state
remains distinct from financial performance; localized meaning remains paired
with raw transport/audit values. Founder local rendered visual acceptance and
the merge decision are complete.

### Sprint 164 implementation

Sprint 164 replaces Overview feature-directory behavior with a bounded
decision-navigation Dashboard. It composes only existing process-health, Demo
descriptor, research, evidence, and Paper Job list contracts. Independent
regions preserve partial success, source-specific error identity and retry,
backend order and duplicates, exact job/result links, explicit repeated ordered
comparison parameters for two to four distinct nonblank IDs, complete raw
Evidence Manifest identity, separate research/evidence authority, generic
Standard workflow choices, and descriptor-driven Demo relationships.

No backend contract, database schema, domain behavior, authentication, gateway,
locale routing, Paper Job command, lifecycle command, financial calculation,
ranking, recommendation, polling, or durable lifecycle read model was added.
Founder local Standard/Demo Dashboard acceptance and merge are complete.

### Sprint 165 implementation

Sprint 165 makes durable Paper Job commands explicit under replay, duplicate
clicks, races, interruption, recovery, and output/reference collision.
Submission now reports `created` or `replayed`; Run atomically claims the queued
job and creates one running attempt before HTTP 202; Retry remains a clean,
attempt-free `failed -> queued` transition; and Recover reports `requeued`,
`succeeded`, or `failed` from a Founder-supplied exact UTC threshold.

The Web uses one bounded status/action matrix, preserves settled job and attempt
evidence on command failure, distinguishes request-read retry from the Paper Job
Retry command, and presents matching English/Simplified Chinese collision and
recovery guidance. Existing files are never overwritten or cleaned, and
terminal job/attempt/reference finalization remains one transaction. No
migration, new durable status, worker, lease, heartbeat, scheduler, polling, or
automatic command was added. Founder local Standard/Demo reliability acceptance
and the Sprint 165 merge are complete.

### Sprint 166 implementation

Sprint 166 adds one static stable-error inventory and matching complete English
and Simplified Chinese presentation inventory. Shared error and technical-audit
surfaces distinguish empty, not found, invalid, unavailable, conflict,
protocol, internal, and unknown conditions while preserving raw operation,
HTTP status, entity, stable code, request ID, and bounded public detail.

Python standard-library logging now emits only bounded sanitized request
completion, successful Paper Job command, and terminal claimed-execution
events. Static operation and route-template catalogs prevent concrete paths or
query strings from entering product events. Expected execution failures use
only approved persisted attempt codes; unexpected or unverifiable outcomes use
the fixed `internal_execution_failure` sentinel.

All six Paper Job attempt error codes now have bilingual label, meaning, and
safe recovery guidance beside their raw value. Migration head remains
`0005_paper_job_result_references`; no durable logs, migration, telemetry
platform, worker, queue, scheduler, polling, cleanup, overwrite, financial
calculation, or automation was added. Founder local Standard/Demo
error-surface and observability acceptance remains pending; S167 becomes next
only after that acceptance and the Sprint 166 merge.

## Codex and Founder Verification Boundary

Codex runs deterministic tests and allowed static checks, but does not perform
Docker runtime acceptance.

```text
Codex
  -> uv run python scripts/check.py
  -> optional docker compose config checks
  -> Ready-for-review PR

Founder
  -> Docker build/start
  -> Standard/Demo runtime and browser acceptance
  -> manual merge decision
```

Codex must not attempt `docker compose build`, `docker compose up`, container
startup, or container smoke verification unless the Founder explicitly requests
an exception for that sprint.

See:

```text
docs/engineering/codex-docker-verification-boundary.md
```

## Founder Product Boundary

The product remains:

- local-first;
- Founder-only;
- minimally authenticated;
- Paper Trading only;
- review-oriented;
- a modular monolith; and
- explicitly human-controlled.

It is not a live system, broker project, SaaS platform, multi-tenant product, or
autonomous strategy/capital engine.

## Roadmap Principles

1. Reproducibility beats convenience.
2. Evaluation discipline precedes strategy complexity.
3. Costs, slippage, benchmarks, and risk context precede serious claims.
4. Stable interfaces precede strategy proliferation.
5. Paper state and auditability precede broker integration.
6. Promotion, review, decision, and lifecycle records remain human-controlled.
7. A proposal is not an action and approval evidence is not runtime execution.
8. Artifact files remain authoritative for completed outputs.
9. Product metadata must not replace domain or artifact truth.
10. Visible failure is better than hidden automation.
11. Real Founder feedback outranks speculative product features.
12. Internationalization must be designed before visual-system finalization.
13. Docker runtime acceptance belongs to the Founder, not Codex.
14. Real capital remains deferred until research, paper evidence, portfolio review,
    execution-risk controls, operational readiness, and explicit approval are
    strong.
