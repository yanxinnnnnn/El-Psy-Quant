# AGENTS.md

This file defines the shared operating context for AI agents working on
El-Psy-Quant.

## Project Identity

El-Psy-Quant is an AI-native quantitative research and trading platform. It is a
long-lived product, not a one-off strategy script.

## Mission

Build a production-ready platform that turns trading ideas into reproducible,
auditable, risk-aware evidence and explicit human decisions before real capital
is deployed.

## Operating Model

- The human Founder makes final product decisions, performs local runtime
  acceptance, and manually merges pull requests.
- ChatGPT acts as CTO for milestone planning, architecture boundaries, GitHub
  Issue creation, documentation-only planning and closeout work, and PR review.
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
- Never commit local `.env`, credentials, tokens, machine-specific paths, or
  private endpoints.

## Verification Boundary

Codex must run:

```text
uv run python scripts/check.py
```

Codex may run non-starting static checks required by an Issue, for example:

```text
docker compose config
docker compose -f compose.yaml -f compose.demo.yaml config
```

Codex must not perform Docker runtime acceptance unless the Founder explicitly
changes this rule for the current sprint. This includes image builds or pulls,
Compose startup, container startup, container smoke tests, and volume removal.

The Founder owns Standard/Demo Docker startup, browser acceptance, data backup,
Demo reset, return-to-Standard verification, and the merge decision.

## Quant and Governance Principles

- Never claim a strategy is profitable without evidence.
- Avoid look-ahead and survivorship bias where applicable.
- Distinguish research, backtesting, Paper Trading, and future live execution.
- Risk and audit context matter as much as return metrics.
- A lifecycle proposal is non-executing.
- A human review record is governance evidence, not proof that execution
  occurred.
- Product guidance must not become strategy ranking, approval, or capital advice.
- A Paper Job success is an operational outcome, not a financial conclusion.
- A portfolio review approval is governance evidence, not capital allocation,
  account mutation, order authorization, or execution.
- Portfolio review scenario weights are assumptions, not Paper Account holdings.

## Definition of Done

A task is complete only when:

- scope matches the authoritative Issue;
- deterministic tests are included where appropriate;
- documentation matches behavior;
- assumptions and limitations are explicit;
- authority boundaries remain intact;
- `uv run python scripts/check.py` passes;
- approved static checks pass where applicable;
- the PR is Ready for review; and
- the PR is not merged by Codex or the CTO.

## Completed Foundations

Milestones 1–29 are Complete.

The productization and hardening chain is:

```text
M25 — S137      Paper Trading Productization Planning
M26 — S138-S144 Paper Trading Application Service Foundation
M27 — S145-S151 Persistence and Paper Job Control Foundation
M28 — S152-S160 Founder Paper Trading Web Workspace
M29 — S161-S168 Product Feedback and Hardening
```

M29 delivered:

- complete English and Simplified Chinese product support;
- a modern responsive AI Quant Decision Workspace visual system;
- a bounded decision-navigation Founder Dashboard;
- explicit Paper Job replay, Run, Retry, Recover, conflict, and audit behavior;
- stable bilingual error presentation and sanitized local correlation events;
- one exact migration chain and fail-closed Standard/Demo startup;
- locked Python build/runtime and Web dependency inputs;
- read-only workspace verification and non-mutating bilingual smoke;
- isolated Standard and Demo volumes and Demo-only reset; and
- cold-backup, upgrade, and restore-limitation guidance.

Closeout records:

```text
docs/milestones/milestone-029-product-feedback-and-hardening.md
docs/closeouts/milestone-029-product-feedback-and-hardening-closeout.md
```

## Current Focus

Milestone 30 is In Progress:

```text
M30 — Portfolio-Level Decision Review Foundation
```

Sprints 169–175 are Complete. Sprint 176 implementation is complete; Founder
Standard/Demo runtime acceptance remains. After Sprint 176 is merged and
Founder acceptance is complete, the next sprint is:

```text
Sprint 177 — Milestone 30 Closeout and M31 Handoff
```

Authoritative M30 planning:

```text
docs/architecture/portfolio-level-decision-review.md
docs/milestones/milestone-030-portfolio-level-decision-review-foundation.md
docs/sprints/sprint-169-milestone-30-architecture-and-planning.md
```

The approved M30 sprint chain is:

```text
S169 architecture and planning
  -> S170 source/input and scenario contracts
  -> S171 concentration and review-exposure analysis
  -> S172 interaction and proposed-impact analysis
  -> S173 immutable review and human-decision artifacts
  -> S174 persistence, application services, and API
  -> S175 bilingual Founder Web workflow
  -> S176 integration, Demo, and acceptance hardening
  -> S177 closeout and M31 handoff
```

Implemented Sprint 170 contract:

- bounded immutable evidence references require explicit research provenance;
- ordered components preserve optional authoritative symbol metadata without
  inference;
- one source owns 2–12 ordered components and at least three exact aligned,
  finite historical return observations;
- source and scenario exports are deterministic, strictly JSON-compatible, and
  protected by canonical SHA-256 digests;
- baseline and proposed scenarios use complete strict non-negative static
  weights in source order and require a real proposed-component change; and
- no analysis, artifact I/O, persistence, migration, API, Web, Demo, Docker,
  account, market, order, execution, broker, or live behavior was added.

Implemented Sprint 171 analysis:

- one pure public factory cross-validates an exact source and scenario pair;
- baseline and proposed concentration use explicit largest-component, top-three,
  HHI, and effective-component-count formulas with source-order tie behavior;
- ordered component exposure preserves exact weights, deltas, active flags,
  change classifications, strategy IDs, and optional declared symbols;
- source-level symbol-evidence availability and active-scenario coverage
  completeness remain explicit without inferring or combining symbols; and
- no overlap, correlation, portfolio behavior, artifact, persistence, API, Web,
  M31, private-edge, broker, or live capability was added.

Implemented Sprint 172 analysis:

- one pure public factory revalidates the exact source and scenario-pair
  authority and reconstructs the aligned source table only in memory;
- source-ordered symbol overlap preserves explicit missing-evidence semantics;
- pairwise and candidate-to-baseline Pearson evidence preserves exact
  zero-variance unavailability without non-finite placeholders;
- baseline and proposed behavior reuses existing return, risk, equity,
  drawdown, and contribution authority;
- every scalar and component impact is exactly proposed minus baseline; and
- no artifact, decision, persistence, migration, API, Web, M31, private-edge,
  broker, or live capability was added.

Implemented Sprint 173 artifacts:

- one immutable analysis artifact binds the exact source and scenarios while
  composing S171 concentration/exposure and S172 interaction/impact internally;
- full source return observations remain solely in the separate source authority;
- one immutable governance-only decision links to the exact analysis digest and
  supports exactly `approved`, `rejected`, or `deferred`;
- canonical SHA-256 digests use strictly JSON-compatible normalized payloads and
  UTC-normalized audit timestamps;
- typed immutable references contain only source, analysis, or decision IDs and
  digests; and
- no file I/O, persistence, migration, application service, API, Web, M31,
  private-edge, broker, or live capability was added.

Implemented Sprint 174 durable product/API boundary:

- source, analysis, and decision files use fixed server-owned hashed paths under
  the configured evidence root and strict write-once exact-reuse semantics;
- source reopen reconstructs S170 inputs, analysis reopen recalculates S171/S172
  evidence, and decision reopen reconstructs through the exact analysis;
- SQLite owns one compact portfolio-review record with create/decision
  idempotency, transaction/file ordering, and one-winner settlement;
- four authenticated versioned API routes expose explicit typed nested contracts;
- checked-in OpenAPI and generated TypeScript contracts are current; and
- no Founder Web, Demo data, lifecycle, Paper Account, order, execution, M31,
  private-edge, broker, or live capability was added.

Implemented Sprint 175 Founder Web workspace:

- three bilingual routes provide exact backend-ordered list/filter/refresh,
  manual structured review creation, full authoritative evidence detail, and one
  explicit governance-only decision workflow;
- the typed API client uses checked-in generated contracts plus complete nested
  runtime validation and explicit caller-supplied idempotency keys;
- the browser validates strict numeric form shape and displays entered weight
  totals without normalizing, rounding, recommending, or recalculating
  financial evidence;
- unavailable overlap and correlation evidence remains explicitly unavailable
  with its raw reason and affected component IDs;
- creation and decision failures preserve drafts, detail refresh failures
  preserve prior evidence, and settled reviews expose no second decision form;
  and
- no backend, generated contract, Demo, lifecycle, Paper Job, Paper Account,
  M31, private-edge, broker, execution, or live capability was added.

Implemented Sprint 176 integration and acceptance hardening:

- existing public research and evidence reads support only explicit metadata and
  compatible-reference composition; aligned returns and scenarios remain manual;
- Demo dataset/descriptor v2 seeds one exact isolated `awaiting_decision` review
  through existing domain/application authority and preserves valid decisions on replay;
- the Demo create example is an explicit replace-confirmed prefill, never an
  automatic submit or decision;
- Dashboard and read-only verification cover portfolio reviews without mutation;
- Standard remains unseeded and isolated from disposable Demo storage; and
- Founder Docker, persistence, reset, and browser runtime acceptance remain pending.

Migration head is `0006_portfolio_reviews`.

### M30 architecture boundary

M30 must provide real domain-calculated portfolio review evidence from explicit
aligned historical inputs. It must preserve:

- explicit static non-negative scenario weights;
- no automatic weight normalization, optimization, recommendation, or allocation;
- concentration, review exposure, overlap, interaction, risk, drawdown,
  contribution, and proposed-impact calculations in domain modules;
- immutable source, analysis, and decision artifact authority;
- compact SQLite metadata and idempotency only;
- complete bilingual API/Web inspection without browser financial calculation;
- one explicit `approved`, `rejected`, or `deferred` human decision; and
- a strict handoff that keeps M31 Paper Account and ledger truth separate.

M30 does not add account balances, positions, orders, fills, market data, session
clock, strategy-to-order conversion, execution simulation, worker, scheduler,
broker, QMT, or live behavior.

## Founder-Approved Runtime Sequence

```text
M30 Portfolio-Level Decision Review Foundation
M31 Stateful Paper Account and Ledger Foundation
M32 Market Data Replay, Trading Calendar, and Session Clock
M33 Strategy-to-Order and Pre-Trade Risk Pipeline
M34 Paper Execution Simulator and First True Paper Trading
M35 Durable Paper Runtime and Recovery
M36 Multi-day Paper Operations and Acceptance
```

Authoritative runtime plan:

```text
docs/strategy/paper-trading-runtime-roadmap.md
```

### M34 product gate

M34 is the first genuine Paper Trading gate. Market data and strategy output must
drive target exposure, order intent, risk checks, simulated fills, and a durable
Paper Account update. The Founder must no longer pre-supply orders and fills as
the transaction script.

### M36 product gate

M36 is the continuous multi-day Paper Trading gate. The same account must advance
across sessions with durable checkpoints, reconciliation, explicit operational
controls, duplicate prevention, and interruption recovery.

## Preserved Architecture

```text
Browser
  -> Next.js Founder Workspace
  -> fixed same-origin /api/backend gateway
  -> versioned FastAPI API
  -> thin application services
  -> domain modules and artifact readers/writers
  -> isolated SQLite and authoritative artifact roots
```

- Domain modules remain financial and governance authority.
- Completed files remain authoritative artifact payloads.
- SQLite remains compact metadata and operational state.
- Raw API, domain, artifact, and audit values remain untranslated.
- Paper Job state remains separate from lifecycle governance.
- Portfolio review status remains separate from lifecycle and Paper Account truth.
- Lifecycle proposals remain non-executing.
- Human review remains explicit evidence.
- Demo and Standard storage remain isolated.
- The browser never directly accesses SQLite, files, Python, QMT, or a broker.

## Explicitly Deferred

Until a future authoritative milestone approves them:

- broker, QMT, or MiniQMT integration;
- real-money execution;
- automatic strategy ranking or approval;
- automatic portfolio optimization or capital allocation;
- public SaaS, multi-tenancy, or complex RBAC;
- microservices, Kubernetes, Kafka, or Redis clusters;
- distributed job infrastructure; and
- broad real-time trading-terminal behavior.
