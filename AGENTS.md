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
- Implementation and closeout PR bodies must begin exactly with
  `Closes #<issue-number>`.
- PRs must be Ready for review, not left as Draft.

## Engineering Principles

- Use Python for backend/domain code and TypeScript/Next.js for the Founder Web.
- Prefer `uv`, a `src/` layout, `pytest`, `ruff`, explicit type hints, and small
  composable modules.
- Preserve deterministic tests and avoid hidden network calls.
- Prefer a modular monolith and local-first operation over premature distributed
  infrastructure.
- Keep financial calculations explicit and owned by domain modules.
- Keep broker-specific behavior behind future adapters.
- Do not add or modify proxy configuration in the repository.
- Do not change project files to solve a local proxy problem.
- Never commit local `.env`, credentials, tokens, machine-specific paths, private
  endpoints, or local backups.

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
- Lifecycle proposals remain non-executing.
- Human review records are governance evidence, not proof that execution occurred.
- Product guidance must not become strategy ranking, approval, or capital advice.
- Paper Job success is an operational outcome, not a financial conclusion.
- Portfolio-review approval is governance evidence, not capital allocation,
  account mutation, order authorization, or execution.
- Portfolio-review scenario weights are assumptions, not Paper Account holdings.
- Future account balances must be derived from an approved ledger authority, not
  mutable duplicated fields.

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

Milestones 1–30 are Complete after Sprint 178 merges.

The recent productization, hardening, and decision-governance chain is:

```text
M25 — S137      Paper Trading Productization Planning
M26 — S138-S144 Paper Trading Application Service Foundation
M27 — S145-S151 Persistence and Paper Job Control Foundation
M28 — S152-S160 Founder Paper Trading Web Workspace
M29 — S161-S168 Product Feedback and Hardening
M30 — S169-S178 Portfolio-Level Decision Review Foundation
```

### M29 delivered

- complete English and Simplified Chinese product support;
- a modern responsive Founder decision workspace;
- a bounded Founder Dashboard;
- explicit Paper Job replay, Run, Retry, Recover, conflict, and audit behavior;
- stable bilingual error presentation and sanitized local correlation events;
- fail-closed Standard/Demo startup and read-only verification;
- locked build/runtime inputs;
- isolated Standard and Demo volumes; and
- cold-backup, upgrade, Demo reset, and return-to-Standard guidance.

### M30 delivered

- one explicit immutable review source with 2–12 ordered components;
- typed evidence references and per-component research origin;
- exact aligned historical return observations;
- strict baseline/proposed static scenarios with no normalization;
- domain-calculated concentration, exposure, overlap, interaction, behavior,
  contribution, drawdown, and proposed impact;
- immutable source, analysis, and human-decision artifacts;
- compact SQLite metadata and idempotency state;
- migration head `0006_portfolio_reviews`;
- exactly four versioned portfolio-review API routes;
- complete bilingual Founder list/create/detail/decision workflows;
- explicit research/evidence composition without manufacturing return authority;
- deterministic isolated Demo v2 review, exact replay, decision persistence, and
  Standard isolation;
- installed-wheel Alembic migration resources for the runtime-only backend; and
- successful Founder Standard/Demo and bilingual runtime acceptance.

Closeout records:

```text
docs/milestones/milestone-029-product-feedback-and-hardening.md
docs/closeouts/milestone-029-product-feedback-and-hardening-closeout.md
docs/milestones/milestone-030-portfolio-level-decision-review-foundation.md
docs/closeouts/milestone-030-portfolio-level-decision-review-foundation-closeout.md
```

## Current Focus

The next milestone is:

```text
M31 — Stateful Paper Account and Ledger Foundation
```

M31 is **In Progress** through the approved S179–S188 sequence. Sprints 179–185
are Complete after PR #367 merged. Sprints 186–187 are
implementation-complete and pending Founder review/runtime acceptance. Sprint
186 exposes the durable application authority through the bilingual
generated-contract-only Paper Account list, create, detail, ledger, mutation,
snapshot, and reconciliation Founder Web workflows. Sprint 187 adds isolated
Demo v3 exact replay, non-repairing integration verification, packaged upgrade
preservation, and Founder-owned recovery/acceptance support.

M31 must establish independent durable account and ledger truth. It may reference
approved M30 review evidence, but that evidence cannot create, fund, or mutate an
account and is not a ledger entry.

The approved Issue #355 architecture defines:

- account identity and lifecycle;
- initial cash and controlled funding/adjustment semantics;
- immutable cash and position ledger entries;
- order and fill persistence boundaries without execution;
- fee and adjustment semantics;
- account versioning, optimistic concurrency, and idempotency;
- snapshots, reconciliation, and derived-balance authority;
- how approved M30 evidence is attached without becoming ledger truth;
- persistence, migration, artifact, API, Web, Demo, and Founder acceptance; and
- explicit deferral of M32+ market, order-generation, execution, and runtime work.

## Approved Route to Genuine Paper Trading

```text
M30 Portfolio-Level Decision Review Foundation — Complete
  -> M31 Stateful Paper Account and Ledger Foundation — In Progress
  -> M32 Market Data Replay, Trading Calendar, and Session Clock
  -> M33 Strategy-to-Order and Pre-Trade Risk Pipeline
  -> M34 Paper Execution Simulator and First True Paper Trading
  -> M35 Durable Paper Runtime and Recovery
  -> M36 Multi-day Paper Operations and Acceptance
```

M31 uses S179–S188. M32–M36 retain no sprint ranges; each milestone receives its
own planning Issue before implementation.

### M34 product gate

M34 is the first genuine Paper Trading gate. Market data and strategy output must
drive target exposure, order intent, risk checks, simulated fills, and a durable
Paper Account update. The Founder must no longer pre-supply orders and fills as
the transaction script.

### M36 product gate

M36 is the continuous multi-day Paper Trading gate. The same account must advance
across sessions with durable checkpoints, reconciliation, explicit controls,
duplicate prevention, and interruption recovery.

Authoritative runtime roadmap:

```text
docs/strategy/paper-trading-runtime-roadmap.md
```

## Preserved Architecture

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
- Raw IDs, states, versions, timestamps, values, digests, and artifact content
  remain untranslated.
- Paper Job, lifecycle, portfolio review, and future Paper Account state remain
  separate authorities.
- Standard and Demo storage remain isolated.
- The browser never directly accesses SQLite, artifact directories, Python, QMT,
  MiniQMT, or a broker.

## M31 Boundary

M31 implementation follows Issue #355 and the strict S179–S188 sequence. Sprint
184 reuses the Sprint 180–183 contracts and makes their account, ledger,
projection, snapshot, and reconciliation authority durable; it must not silently
reinterpret:

- M30 scenario weights as holdings;
- M30 approval as account authorization;
- Paper Job results as ledger events;
- lifecycle state as cash or position authority; or
- user-entered balances as a substitute for immutable ledger entries.

Sprint 184 account events and cash/position entries remain durable mutation
authority. `replay_paper_account_ledger(...)` remains state authority;
projection rows are replaceable caches; snapshot and reconciliation rows are
immutable derived evidence. Ordinary reads never repair a stale projection.
Sprint 185 exposes that authority through exactly ten `/api/v1/paper-accounts`
operations. API/OpenAPI/generated TypeScript payloads and bounded product logs
are presentation and correlation surfaces only; they are not financial,
ledger, projection, digest, snapshot, reconciliation, or governance authority.
Sprint 186 presents that boundary through three bilingual Founder routes and
never calculates financial truth. Sprint 187 Demo, Web, API, and descriptor
surfaces remain presentation and verification layers over the same authority.
No filesystem evidence artifact, Docker runtime acceptance, order/fill, market,
execution, or Sprint 188+ behavior exists yet.

M31 does not pre-authorize:

- market-data replay or a session clock;
- strategy evaluation for runtime order generation;
- pre-trade order risk;
- simulated execution;
- workers, scheduling, or multi-day operation;
- broker, QMT, MiniQMT, private-edge, live, or real-money behavior.

## Explicitly Deferred

Unless a future authoritative milestone approves them:

- broker, QMT, or MiniQMT integration;
- real-money execution;
- automatic strategy ranking, approval, optimization, or capital allocation;
- public SaaS, multi-tenancy, or complex RBAC;
- microservices, Kubernetes, Kafka, or Redis clusters;
- distributed job infrastructure; and
- broad real-time trading-terminal behavior.
