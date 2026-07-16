# AGENTS.md

This file defines the shared context for AI agents working on El-Psy-Quant.

## Project Identity

El-Psy-Quant is an AI-native quantitative research and trading platform.

The project is built like a startup product, not a one-off learning script.

## Mission

Build an AI-native quant research operating system that turns trading ideas into reproducible, auditable, risk-aware decisions before any real capital is deployed.

## Operating Model

- The human Founder makes final decisions and performs merges.
- ChatGPT acts as CTO for milestone planning, sprint scope, architecture boundaries, Issue creation, PR review, and milestone closeout.
- Codex acts as the implementation developer for coding sprints.
- Documentation-only planning and closeout work may be handled directly by the CTO.
- Codex must not merge pull requests.
- The CTO must not merge pull requests.
- No pull request may be merged without explicit Founder action.
- The GitHub Issue body is the authoritative implementation specification.

## Engineering Principles

- Use Python for the backend and domain platform.
- Prefer modern Python packaging and tooling.
- Use `uv` for dependency management unless the Founder decides otherwise.
- Use a `src/` layout.
- Use `pytest` for Python tests.
- Use `ruff` for formatting and linting.
- Use strict TypeScript for the Web application.
- Use type hints for public Python functions.
- Keep modules small and composable.
- Avoid premature abstraction.
- Avoid hidden network calls in tests.
- Keep financial calculations explicit and documented.
- Keep broker-specific behavior behind adapters.
- Optimize for correctness, auditability, and maintainability rather than cleverness.

## Quant and Governance Principles

- Never claim a strategy is profitable without evidence.
- Avoid look-ahead bias.
- Avoid survivorship bias where possible.
- Distinguish research, backtesting, internal paper execution, external paper execution, and live execution.
- Prefer reproducible experiments.
- Risk metrics matter as much as return metrics.
- A promotion candidate is not approval.
- A lifecycle proposal is not execution.
- A human approval or review record is governance evidence, not proof that runtime execution occurred.
- Human decision authority must remain explicit.

## Definition of Done

A task is complete only when:

- runtime behavior works locally when runtime behavior changes;
- tests are included where appropriate;
- README or documentation is updated when behavior changes;
- assumptions and limitations are documented;
- the implementation is simple enough for a human reviewer to understand;
- `uv run python scripts/check.py` passes;
- the pull request is Ready for review, not Draft; and
- the PR body begins with an exact manually typed `Closes #<issue-number>` line.

## Long-Term Platform Direction

The founder-level roadmap is maintained in:

```text
docs/strategy/future-platform-roadmap.md
```

The priority order is:

```text
trusted local workflow
  > human-controlled governance
  > usable Founder product
  > portfolio-level decisions
  > execution-risk controls
  > broker adapters
  > controlled live pilot
```

## Completed Foundations

Milestones 1–28 are complete.

The recent completed chain is:

```text
M18 Paper Trading Workflow Integration Foundation
M19 Configured Paper Workflow Wiring Foundation
M20 Research-to-Paper Promotion Foundation
M21 Paper Run Comparison and Review Foundation
M22 Decision Governance Foundation
M23 Report Artifact Foundation
M24 Strategy Review Workflow Foundation
M25 Paper Trading Productization Planning
M26 Paper Trading Application Service Foundation
M27 Persistence and Paper Job Control Foundation
M28 Founder Paper Trading Web Workspace
```

Milestone 28 delivered the first usable local Founder Web MVP, including:

- the Next.js workspace shell and generated API client;
- strategy and research inspection;
- governance and report-manifest inspection;
- durable paper-job submission and manual control;
- authoritative portfolio-result inspection;
- explicit ordered paper-result comparison;
- lifecycle proposal and human-review commands;
- minimal paired Founder authentication;
- standard Docker Compose startup;
- an isolated disposable Demo Workspace;
- first-run guidance; and
- a complete guided Strategy-to-Human-Decision journey.

Formal records:

```text
docs/milestones/milestone-028-founder-paper-trading-web-workspace.md
docs/closeouts/milestone-028-founder-paper-trading-web-workspace-closeout.md
```

## Current Focus

The current milestone is:

```text
Milestone 29 — Product Feedback and Hardening
```

The next sprint is:

```text
Sprint 161 — Founder Feedback and Product Experience Architecture
```

Milestone 29 uses real Founder feedback to improve product usability and daily local reliability.

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

The multilingual foundation must precede the broad visual refresh so English and Simplified Chinese layouts both shape the visual system.

## Milestone 29 Product Feedback

### Product Experience Refresh

The current Web workspace is stable and professional, but it resembles an academic research portal or enterprise internal dashboard.

The target is an **AI Quant Decision Workspace** with:

- a modern neutral palette;
- clean sans-serif typography;
- stronger product identity;
- improved information hierarchy;
- clearer forms and tables;
- purposeful data visualization;
- a Founder Dashboard; and
- workflow-oriented next actions.

### Multilingual Product Foundation

The product must support:

```text
en      English, default
zh-CN   Simplified Chinese
```

Internationalization requirements:

- provide an explicit language switcher;
- localize all Founder-facing navigation, page copy, forms, states, confirmations, accessibility labels, and stable frontend error explanations;
- keep route paths stable unless a future requirement justifies locale-prefixed URLs;
- preserve current path and query parameters when switching language;
- preserve in-progress form state when practical;
- set the HTML language correctly;
- keep locale catalogs structurally complete and type checked;
- fail tests or builds on missing required messages rather than silently shipping mixed-language UI;
- preserve raw domain identifiers, API values, UUIDs, run IDs, job IDs, artifact keys, schema versions, UTC timestamps, and source payloads without translation; and
- keep internationalization in the Web product layer rather than changing backend transport semantics.

## Approved Product Architecture

```text
Browser
  -> React/Next.js Founder workspace
  -> fixed same-origin /api/backend gateway
  -> versioned FastAPI application API
  -> thin application services / use cases
  -> existing El-Psy-Quant domain modules and artifact readers
  -> SQLite product repositories and simple local job runner
```

The implementation remains a modular monolith.

Do not introduce premature microservices, Kubernetes, Kafka, Redis clusters, distributed queues, multi-tenancy, complex RBAC, cloud SaaS behavior, broad real-time dashboards, or broker integration.

## Product Ownership Boundaries

### Domain authority

Existing research, backtesting, paper, promotion, comparison, decision, report, and strategy-review modules remain authoritative for quantitative and governance behavior.

The application and Web layers must not duplicate:

- financial calculations;
- paper execution semantics;
- comparison logic;
- governance validation;
- lifecycle transition validation; or
- human-control rules.

FastAPI route handlers remain thin and must not become a second domain layer.

### Artifact authority

Existing artifact files remain authoritative for completed research, paper, comparison, governance, and report outputs.

SQLite may store:

- compact artifact indexes;
- explicit references;
- paper-job requests and operational status;
- attempts and bounded error codes;
- idempotency data; and
- compact result references.

SQLite must not silently copy complete artifact payloads and become a competing source of truth.

Artifact paths must remain under configured local roots. Reject path traversal and arbitrary filesystem access.

### Lifecycle authority

Do not create an independently authoritative mutable strategy lifecycle `current_state` field.

A current-state view may be derived from explicit immutable snapshots and approved human records.

A transition proposal remains non-executing. A human review record remains governance evidence. Neither silently mutates lifecycle state.

### Paper-job authority

Paper-job status is mutable operational state and remains separate from strategy lifecycle governance.

Durable local states are:

```text
queued
running
succeeded
failed
canceled
```

### Browser boundary

The browser uses the Web/API boundary and must not directly access:

- SQLite;
- artifact directories;
- Python modules;
- Demo source files;
- QMT;
- MiniQMT; or
- any broker.

### Demo boundary

Standard startup remains unseeded. Demo startup uses separate storage, deterministic validated records, and visible Demo identity. Demo reset must never delete standard user data.

## API, Security, and Deployment Baselines

- Use the versioned local API under `/api/v1`.
- Use explicit schemas instead of leaking internal Python objects.
- Preserve stable sanitized errors and server-owned request IDs.
- Keep the fixed same-origin Web gateway.
- Bind published services to loopback by default.
- Require authentication for non-loopback exposure.
- Avoid broad CORS.
- Never log credentials or authentication material.
- Support one local machine through M29.
- Preserve standard and Demo Docker Compose storage isolation.
- Do not add distributed infrastructure without a separate roadmap decision.

## Future QMT Boundary

QMT is a future execution adapter only.

```text
Browser
  -> Web/API
  -> broker-neutral execution command
  -> Windows QMT agent
  -> MiniQMT
  -> broker
```

Future broker-neutral concepts may include:

```text
OrderIntent
ExecutionOrder
ExecutionFill
AccountSnapshot
PositionSnapshot
BrokerOrderReference
```

Never connect the browser directly to QMT. Do not add live QMT behavior before portfolio review, execution-risk controls, operational readiness, and explicit human approval exist.

## Issue and PR Requirements

Every implementation Issue must define:

- objective and user outcome;
- exact scope and deliverables;
- architecture and ownership boundaries;
- required tests and verification;
- documentation updates;
- explicit non-goals; and
- acceptance criteria.

Execution rules:

- Treat the Issue body as the authoritative specification.
- Keep separate Codex prompts short and refer to the Issue.
- Do not add or commit proxy configuration.
- Do not modify project files for proxy setup.
- Local temporary network configuration, when needed, must remain outside committed project files.
- Do not submit `.env` files, credentials, secrets, private endpoints, or machine-specific paths.
- Run `uv run python scripts/check.py` before opening a PR.
- Open one focused PR against `main`.
- Start the PR body with `Closes #<issue-number>`.
- Mark the PR Ready for review.
- Do not merge unless the Founder explicitly performs the merge.
