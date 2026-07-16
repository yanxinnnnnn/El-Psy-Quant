# Future Platform Roadmap — Founder-Level CTO Plan

## Purpose

This document captures the long-term company-level direction for El-Psy-Quant.

El-Psy-Quant should not become a loose collection of strategy scripts or a thin trading bot. The product direction is to build an AI-native quantitative research operating system that turns trading ideas into reproducible, auditable, risk-aware decisions before real capital is deployed.

## Strategic North Star

```text
Build an AI-native quant research operating system that turns trading ideas into reproducible, auditable, risk-aware decisions before any real capital is deployed.
```

The target is not a magic profitable strategy. The target is a trusted decision and operating pipeline.

## Capability Chain

```text
idea
  -> data
  -> research
  -> backtest
  -> portfolio
  -> execution assumptions
  -> paper trading
  -> persistence and audit
  -> configured workflow
  -> promotion governance
  -> paper comparison
  -> strategy decision governance
  -> report artifact
  -> lifecycle governance
  -> application/API boundary
  -> product persistence and job control
  -> Founder product workspace
  -> multilingual product experience
  -> daily-use product hardening
  -> portfolio-level review
  -> execution-risk governance
  -> controlled live readiness
```

## Company-Level Phases

```text
Phase 1 — Research & Artifact Foundation
Phase 2 — Workflow Integration Foundation
Phase 3 — Decision Intelligence Foundation
Phase 4 — Founder Paper Trading Productization
Phase 5 — Portfolio Decisions & Execution Governance
Phase 6 — Controlled Live Pilot & Production Operations
```

Priority order:

```text
trusted local workflow
  > human-controlled governance
  > usable Founder product
  > hardened multilingual product experience
  > portfolio-level decisions
  > execution-risk controls
  > broker adapters
  > controlled live pilot
```

The wrong order is:

```text
broker > dashboard > live > strategy zoo
```

That path creates operational and financial risk before the platform earns complexity.

## Phase 1 — Research & Artifact Foundation

Status: **Complete through Milestone 18.**

This phase established:

- local data loading and validation;
- reproducible research pipelines;
- experiment artifacts and comparison;
- strategy interfaces;
- portfolio construction;
- portfolio risk and attribution;
- explicit execution realism;
- paper account state, orders, fills, and sessions;
- paper artifact persistence and audit; and
- explicit local paper-run boundaries.

Completed milestone chain:

```text
M1-M8   research workflow and operations
M9      project quality foundation
M10     experiment artifact and comparison foundation
M11     strategy interface foundation
M12     data integrity and universe foundation
M13     portfolio construction foundation
M14     portfolio risk and attribution foundation
M15     backtest execution realism foundation
M16     paper trading foundation
M17     paper trading persistence and audit foundation
M18     paper trading workflow integration foundation
```

## Phase 2 — Workflow Integration Foundation

Status: **Complete through Milestone 21.**

### Milestone 19 — Configured Paper Workflow Wiring Foundation

```text
local config
  -> validated paper-run request
  -> configured output layout
  -> paper workflow execution
  -> saved outputs and result references
```

### Milestone 20 — Research-to-Paper Promotion Foundation

```text
research evidence
  -> promotion candidate
  -> evidence summary
  -> explicit human promotion record
  -> promotion references and manifest
```

A promotion candidate is not approval. A promotion record does not imply live readiness.

### Milestone 21 — Paper Run Comparison and Review Foundation

```text
multiple paper runs
  -> explicit comparison input
  -> comparison summary
  -> human review decision
  -> review references and manifest
```

The comparison layer does not discover runs, rank strategies automatically, or make capital decisions.

## Phase 3 — Decision Intelligence Foundation

Status: **Complete through Milestone 24.**

### Milestone 22 — Decision Governance Foundation

```text
decision evidence
  -> strategy decision input
  -> caller-supplied summary
  -> explicit human decision record
  -> decision references and manifest
```

This layer records why a strategy should continue, pause, be rejected, or need more evidence without becoming an automatic decision engine.

### Milestone 23 — Report Artifact Foundation

```text
report source reference
  -> report section
  -> report artifact summary
  -> report reference and manifest
```

Report artifacts package completed governance records. They do not calculate new metrics, recommend decisions, or imply readiness.

### Milestone 24 — Strategy Review Workflow Foundation

```text
strategy review evidence reference
  -> lifecycle state snapshot
  -> transition proposal
  -> human-controlled transition record
  -> workflow reference and manifest
  -> closeout
```

Lifecycle vocabulary:

```text
research_review
paper_review
watchlist
on_hold
rejected
```

Transition outcomes:

```text
approved
rejected
deferred
```

Milestone 24 preserved:

- no implicit initial state;
- no independently authoritative mutable current-state store;
- no automatic transition application;
- no automatic decision-status mapping;
- no evidence discovery or resolution;
- no paper execution triggered by governance records; and
- no broker, live-readiness, or capital behavior.

## Phase 4 — Founder Paper Trading Productization

Status: **Milestones 25–28 complete. Milestone 29 is in progress.**

The platform has enough domain depth. The company-level objective is now to make existing capabilities clear, usable, multilingual, and reliable for daily Founder operation.

This phase remains single-user and local-first. It is not a SaaS phase.

### Approved Product Architecture

```text
Browser
  -> React/Next.js Founder workspace
  -> fixed same-origin gateway
  -> versioned FastAPI application API
  -> thin application services / use cases
  -> existing El-Psy-Quant domain modules and artifact readers
  -> SQLite product repositories and simple local job runner
```

The implementation remains a modular monolith.

Approved baseline:

- FastAPI;
- explicit request and response schemas;
- SQLite + SQLAlchemy;
- repository boundaries;
- simple local jobs;
- React/Next.js;
- Docker Compose and local-first deployment; and
- single-user or minimal authentication.

### Product Target

The first product is:

- local-first;
- Founder-only;
- single-user or minimally authenticated;
- Paper Trading only;
- review-oriented rather than latency-oriented; and
- built around existing research, paper, governance, report, and lifecycle capabilities.

It is not:

- a live trading system;
- a broker integration project;
- a SaaS product;
- a multi-tenant platform;
- a professional real-time trading terminal; or
- an automatic strategy approval or capital-allocation engine.

### Founder Journey

```text
Strategy
  -> Research Evidence
  -> Governance Evidence
  -> Paper Run
  -> Portfolio Result
  -> Comparison
  -> Lifecycle Review
  -> Human Decision Evidence
```

Each step exposes existing facts, artifacts, or explicit human records. The product does not silently carry conclusions from one step to the next.

## Completed Milestone 25 — Paper Trading Productization Planning

Milestone 25 delivered:

- explicit Founder journeys and product non-goals;
- application, domain, artifact, persistence, lifecycle, paper-job, and UI ownership boundaries;
- API, security, authentication, and local deployment baselines;
- staged M26–M29 planning; and
- preserved QMT and live-readiness boundaries.

## Completed Milestone 26 — Paper Trading Application Service Foundation

Milestone 26 established:

- a deterministic FastAPI application factory;
- a versioned local API under `/api/v1`;
- explicit schemas rather than leaked internal objects;
- stable sanitized error responses;
- server-owned request IDs;
- safe configured artifact inspection;
- strategy catalog reads;
- synchronous paper-run commands; and
- stateless lifecycle proposal and review commands.

It added no product database, persistent worker, broker, QMT, live, or capital behavior.

## Completed Milestone 27 — Persistence and Paper Job Control Foundation

Milestone 27 established:

- SQLite product persistence;
- SQLAlchemy repository boundaries;
- Alembic migration discipline;
- a compact rebuildable artifact index;
- durable paper-job records;
- replay-safe keyed submission;
- compact attempt audit;
- explicit manual run, cancellation, retry, and recovery;
- fixed result references; and
- strict authoritative-file result reads.

Paper-job operational state remains separate from lifecycle governance.

Do not introduce Kafka, Redis clusters, distributed queues, Kubernetes, or multi-service orchestration for this local job model.

## Completed Milestone 28 — Founder Paper Trading Web Workspace

Milestone 28 delivered the first usable local Web MVP through Sprints 152–160.

Delivered chain:

```text
Next.js workspace shell and generated API client
  -> strategy and research views
  -> governance and report views
  -> durable paper-job launch and status
  -> authoritative portfolio-result views
  -> explicit paper-result comparison
  -> lifecycle proposal and human review
  -> minimal authentication and Docker Compose
  -> isolated Demo Workspace and first-run guidance
```

Productization delivered:

- a strict TypeScript Next.js App Router workspace;
- a fixed same-origin gateway;
- generated TypeScript contracts from OpenAPI;
- responsive and accessible Founder views;
- paired Founder HTTP Basic authentication;
- reproducible standard Compose startup;
- persistent local storage;
- a separate disposable Demo project and volume;
- deterministic Demo installation;
- standard empty-state onboarding;
- product-facing user documentation; and
- authenticated end-to-end smoke verification.

Milestone 28 preserved:

- domain authority for quantitative and governance behavior;
- completed-file artifact authority;
- compact SQLite ownership;
- the browser/API boundary;
- non-executing lifecycle proposals;
- explicit human decision authority;
- paper-job/lifecycle separation; and
- Demo/real-user storage isolation.

Closeout records:

```text
docs/milestones/milestone-028-founder-paper-trading-web-workspace.md
docs/closeouts/milestone-028-founder-paper-trading-web-workspace-closeout.md
```

## Active Milestone 29 — Product Feedback and Hardening

Status: **In Progress.**

Purpose:

Use real Founder workflows to transform the Engineering and Product MVP into a multilingual, modern, reliable daily-use local product without adding speculative financial or live-trading capability.

### Founder Feedback

#### Multilingual Product Foundation

The product must support:

```text
en      English, default
zh-CN   Simplified Chinese
```

The multilingual product must:

- provide an explicit language switcher;
- localize all Founder-facing navigation, product copy, forms, loading/empty/error states, confirmations, accessibility labels, and stable frontend error explanations;
- preserve current route paths unless a future sharing or SEO requirement justifies locale-prefixed URLs;
- preserve path and query parameters during language switching;
- preserve in-progress form state where practical;
- set the HTML language correctly;
- keep locale catalogs complete and type checked;
- fail verification on missing required messages rather than shipping mixed-language screens;
- preserve raw strategy names, domain identifiers, API values, UUIDs, run IDs, job IDs, artifact keys, schema versions, UTC timestamps, and artifact payloads without translation; and
- remain a Web product concern rather than changing backend transport semantics.

Internationalization must be implemented before the broad visual refresh so both English and Chinese inform component dimensions, typography, spacing, and content hierarchy.

#### Product Experience Refresh

The current product is stable but visually resembles an academic research portal or enterprise internal dashboard.

The target is an **AI Quant Decision Workspace** with:

- a modern neutral palette;
- clean sans-serif typography;
- stronger product identity;
- improved information hierarchy;
- clearer forms and tables;
- purposeful data visualization;
- a Founder Dashboard; and
- system-assisted workflow guidance without automated financial recommendations.

#### Daily-use Hardening

Milestone 29 must also improve:

- idempotency and replay clarity;
- paper-job recovery and interruption handling;
- actionable error surfaces;
- request, job, artifact, and audit correlation;
- migration reliability;
- test coverage;
- standard and Demo Compose operations; and
- local upgrade and rollback guidance.

### Milestone 29 Sprint Sequence

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

#### Sprint 161 — Founder Feedback and Product Experience Architecture

Planning and product-architecture sprint.

Required outcomes:

- prioritized Founder feedback backlog;
- product-experience north star;
- internationalization architecture decision;
- English/Simplified Chinese terminology contract;
- visual-system direction;
- Founder Dashboard and information-architecture boundaries;
- M29 acceptance metrics; and
- authoritative handoff to S162–S168.

#### Sprint 162 — Multilingual Foundation and Simplified Chinese Workspace

Implementation must add complete English and Simplified Chinese coverage before visual-system work begins.

It must not translate or mutate domain truth, API values, IDs, schemas, timestamps, or artifacts.

#### Sprint 163 — Modern Visual System Foundation

Build the reusable color, typography, spacing, surface, control, table, form, state, and responsive foundations validated in both languages.

#### Sprint 164 — Founder Dashboard and Workflow Information Architecture Refresh

Move the home experience from passive route discovery toward explicit product status, recent activity, pending decisions, and user-chosen next actions.

No automatic ranking, approval, or capital recommendation may be introduced.

#### Sprint 165 — Reliability, Idempotency, and Job Recovery Hardening

Improve daily operational confidence without adding distributed workers or queues.

#### Sprint 166 — Error Surface, Observability, and Audit Hardening

Make failures and audit context visible and actionable while preserving bounded public errors and secret redaction.

#### Sprint 167 — Migration, Test, and Local Deployment Hardening

Harden local upgrades, standard/Demo isolation, verification, rollback guidance, and multilingual end-to-end coverage.

#### Sprint 168 — Milestone 29 Closeout and M30 Handoff

Verify daily Founder use and decide whether the platform is ready to resume portfolio-level decision work.

### Milestone 29 Exit Criteria

- real Founder feedback is captured and prioritized;
- English and Simplified Chinese are complete and switchable;
- the modern visual system works in both languages;
- workflow and information architecture are clearer;
- job recovery and idempotency are reliable for local use;
- errors and audit information are actionable;
- migrations, tests, and local deployment are reliable enough for daily use;
- authority and human-control boundaries remain intact; and
- no broker, live, SaaS, or distributed-system scope is introduced.

## Product Ownership Boundaries

### Domain Authority

Existing research, backtesting, paper, promotion, comparison, decision, report, and strategy-review modules remain authoritative.

The application and UI layers must not duplicate financial calculations, paper execution semantics, comparison logic, governance validation, lifecycle validation, or human-control rules.

### Artifact Authority

Existing local artifact files remain authoritative for completed outputs.

SQLite may store compact indexes, explicit references, paper-job records, operational status, attempts, idempotency data, and result references. It must not silently copy complete artifact payloads.

### Lifecycle Authority

Do not create an independently authoritative mutable lifecycle current-state field.

A proposal remains non-executing. A review record remains governance evidence. Neither silently applies a transition.

### Paper Job Authority

Paper-job status is mutable operational state and remains separate from lifecycle governance.

### Browser Boundary

The browser must use the same-origin Web/API boundary and must not directly access SQLite, artifact roots, Python modules, Demo source files, QMT, MiniQMT, or a broker.

### Demo Authority

Demo data is deterministic, disposable, visibly labeled, and isolated from standard user storage. Demo startup and reset must not modify the standard workspace.

## Security and Local Deployment Baseline

- Bind published services to loopback by default.
- Use paired minimal Founder authentication.
- Avoid broad CORS.
- Never expose arbitrary filesystem paths.
- Never log credentials or authentication material.
- Keep `.env`, secrets, private endpoints, and machine-specific paths out of the repository.
- Do not commit proxy configuration.
- Support one local machine through Milestone 29.
- Preserve standard and Demo storage isolation.
- Keep the product operable without Kubernetes, cloud services, or external brokers.

## Phase 5 — Portfolio Decisions & Execution Governance

Status: **Future.**

### Milestone 30 — Portfolio-Level Decision Review Foundation

Evaluate strategies at portfolio level rather than only as standalone candidates.

Potential review inputs:

- marginal risk contribution;
- duplicated factor or symbol exposure;
- concentration;
- correlation with approved strategies;
- expected portfolio impact; and
- capital and turnover implications.

This remains human-controlled decision governance, not automatic portfolio optimization or capital allocation.

### Milestone 31 — Broker Abstraction Planning

Define broker-neutral concepts before connecting to any broker:

```text
OrderIntent
ExecutionOrder
ExecutionFill
AccountSnapshot
PositionSnapshot
BrokerOrderReference
```

Define idempotency, retries, reconciliation, error handling, manual approval, and kill-switch boundaries.

### Milestone 32 — Simulated Broker Adapter Foundation

Exercise broker-like acknowledgements, fills, rejections, reconnects, and reconciliation locally without external dependencies.

### Milestone 33 — Execution Risk Control Foundation

Potential controls:

- maximum order size;
- maximum position size;
- maximum turnover;
- loss thresholds;
- symbol allowlists;
- trading windows;
- manual approval requirements; and
- emergency stop behavior.

### Milestone 34 — Live Readiness Checklist Foundation

```text
strategy evidence
  + paper evidence
  + portfolio review
  + execution-risk controls
  + operational checks
  + explicit human approval
  -> live-readiness record
```

### Milestone 35 — QMT Paper Adapter Foundation

QMT may enter only as an execution adapter after broker-neutral commands and risk boundaries exist.

```text
Browser
  -> Web/API
  -> broker-neutral execution command
  -> Windows QMT agent
  -> MiniQMT
  -> broker
```

QMT must not leak into strategy, evaluation, governance, persistence, or UI domain models.

## Phase 6 — Controlled Live Pilot & Production Operations

Status: **Future and conditional.**

This phase begins only after strong research evidence, paper evidence, portfolio review, execution-risk controls, operational readiness, and explicit human approval exist.

Potential scope:

- tiny-capital controlled live pilot;
- live account and order reconciliation;
- operational monitoring and alerts;
- incident records and kill switch;
- deployment and rollback runbooks; and
- production review processes.

Guardrails:

- no unattended scaling;
- no autonomous capital allocation;
- strict exposure limits;
- complete audit trail;
- manual kill switch; and
- staged rollout.

## Founder Product Architecture Principles

1. Use existing domain contracts rather than rewriting them in the API layer.
2. Keep the product local and single-user through M29.
3. Prefer one modular application before microservices.
4. Prefer SQLite until real usage proves otherwise.
5. Prefer simple local jobs before distributed queues.
6. Keep artifact files authoritative.
7. Keep paper-job state separate from lifecycle governance.
8. Keep UI state separate from financial truth.
9. Keep broker-specific behavior behind adapters.
10. Treat auditability and human review as product features.
11. Make failure visible rather than hiding it behind automation.
12. Use real Founder feedback rather than speculative product additions.
13. Design internationalization before finalizing the visual system.
14. Delay multi-tenancy, complex RBAC, cloud orchestration, and SaaS behavior.

## Core Assets To Preserve

### Research Memory

Every experiment, strategy, parameter set, data assumption, and result should remain traceable.

### Paper Trading Memory

Every paper request, order, fill, account change, session, job, attempt, and result should remain inspectable.

### Promotion and Decision Ledger

Every nomination, review, pause, rejection, and lifecycle change should remain explicit, evidence-backed, and human-controlled.

### Report and Lifecycle Memory

Every review package, declared state, proposal, transition record, and manifest should remain tied to stable IDs without implying runtime execution.

### Product Audit Trail

Application and Web layers should make existing audit records easier to use, not replace them with opaque UI state.

### Product Language Contract

Product copy may be localized. Domain identities and evidence payloads must remain stable and auditable across languages.

### Execution Readiness

Live trading should be the outcome of trusted research, paper evidence, product operation, portfolio review, risk controls, operational governance, and explicit approval—not the starting point.

## Explicit Non-priorities

Do not prioritize these too early:

```text
strategy count for its own sake
real-money trading
live broker integration
browser-to-broker direct connectivity
high-frequency trading
deep-learning alpha
microservice architecture
Kubernetes
Kafka
Redis clusters
distributed queues
multi-tenancy
complex RBAC
large cloud infrastructure
SaaS behavior
real-time dashboard complexity
```
