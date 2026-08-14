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
- Never commit local `.env`, credentials, tokens, machine-specific paths,
  private endpoints, or local backups.

## Verification Boundary

Implementation sprints must run:

```text
uv run python scripts/check.py
```

Migration sprints must additionally run:

```text
uv run alembic heads
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
- M31 balances and positions derive from immutable ledger authority, not mutable
  duplicated fields.
- M32 calendar/session/event/replay values remain market-time authority.
- M33 Signal/Intent/Risk evidence remains immutable strategy-to-risk authority
  and must not be treated as execution or account mutation.

## Definition of Done

A task is complete only when:

- scope matches the authoritative Issue;
- deterministic tests are included where appropriate;
- documentation matches behavior;
- assumptions and limitations are explicit;
- authority boundaries remain intact;
- required verification passes;
- approved static checks pass where applicable;
- the PR is Ready for review; and
- the PR is not merged by Codex or the CTO.

## Completed Foundations

Milestones 1–33 are Complete through Sprint 206 closeout.

The recent productization and Paper Trading authority chain is:

```text
M25 — S137      Paper Trading Productization Planning
M26 — S138-S144 Paper Trading Application Service Foundation
M27 — S145-S151 Persistence and Paper Job Control Foundation
M28 — S152-S160 Founder Paper Trading Web Workspace
M29 — S161-S168 Product Feedback and Hardening
M30 — S169-S178 Portfolio-Level Decision Review Foundation
M31 — S179-S188 Stateful Paper Account and Ledger Foundation
M32 — S189-S196 Market Data Replay, Trading Calendar, and Session Clock
M33 — S197-S206 Strategy-to-Order and Pre-Trade Risk Pipeline
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

- immutable portfolio review source/analysis/human-decision evidence;
- exact aligned historical observations and explicit static scenarios;
- concentration, exposure, interaction, contribution, drawdown, and impact
  evidence;
- compact SQLite metadata/idempotency;
- four versioned API operations and bilingual Founder workflows; and
- deterministic isolated Demo evidence.

M30 review decisions remain governance evidence, not capital allocation or
execution authority.

### M31 delivered

- durable Paper Account identity and lifecycle;
- immutable cash and position ledger events/postings;
- exact Decimal money/quantity and deterministic ledger replay;
- projection rebuild/verification, snapshot, and reconciliation;
- append-only SQLite persistence and command idempotency/concurrency;
- exactly ten versioned Paper Account operations;
- bilingual Founder Paper Account workflows; and
- isolated Demo/recovery/upgrade evidence.

M31 ledger events/postings remain financial authority and ledger replay remains
Paper Account state authority.

### M32 delivered

- immutable Trading Calendar and Trading Session definitions;
- canonical `MarketDataEvent` values;
- deterministic replay ordering, cursor, lifecycle, and stream binding;
- durable persistence/restart recovery;
- read-only market-time APIs;
- bilingual Founder replay inspection; and
- isolated Demo/recovery evidence.

M32 remains market-time authority and does not mutate M31 financial state.

### M33 delivered

- one closed versioned moving-average runtime adapter and deterministic
  StrategySignal evaluation from an exact M32 replay prefix;
- immutable advisory StrategySignal identity/digest;
- exact account-bound buy/sell/no-action conversion from verified M31 state;
- immutable risk-pending M33 OrderIntent identity/idempotency;
- explicit long-only cash risk policy, latest-trade risk-price evidence, exact
  notional, four ordered rules, and immutable allow/reject Decision evidence;
- migration `0010_strategy_order_risk` with append-only Signal, Intent,
  Decision, and scoped receipt persistence;
- strict reconstruction, bounded reads, one-winner transactions, restart-safe
  replay, stale refusal, and corruption/no-repair;
- exactly nine versioned M33 API operations, stable errors/audit, OpenAPI, and
  generated TypeScript;
- one bilingual generated-contract-only `/strategy-to-risk` workspace; and
- deterministic isolated Demo v5 install/replay/restart/concurrency/upgrade/
  corruption-recovery/Standard-isolation evidence.

The final reviewed S205 CI baseline was Python `3061 passed` and Web
`449 passed / 47 files`, and the migration head is
`0010_strategy_order_risk`.

M33 closes without execution order, fill, reservation, execution pricing/fees,
fill-caused ledger mutation, replay progression, worker/scheduler, broker, live,
or real-money behavior.

Closeout records include:

```text
docs/closeouts/milestone-029-product-feedback-and-hardening-closeout.md
docs/closeouts/milestone-030-portfolio-level-decision-review-foundation-closeout.md
docs/closeouts/milestone-031-stateful-paper-account-and-ledger-foundation-closeout.md
docs/closeouts/milestone-032-market-data-replay-trading-calendar-and-session-clock-closeout.md
docs/closeouts/milestone-033-strategy-to-order-and-pre-trade-risk-pipeline-closeout.md
```

## Current Focus

The exact next milestone is:

```text
M34 — Paper Execution Simulator and First True Paper Trading
```

**Do not begin M34 runtime implementation until a CTO-owned architecture and
planning Sprint has frozen the execution boundary.**

M34 may consume only an M33 OrderIntent with a matching `allow`
PreTradeRiskDecision and exact verified M31/M32 anchors. It must revalidate
account and market freshness at execution time; an M33 allow result is not
automatically fresh execution authorization.

The M34 planning Sprint must explicitly decide:

- execution command identity;
- execution order lifecycle;
- fill timing and execution-price authority;
- rejection and partial-fill semantics;
- slippage, fees, commission, and tax treatment;
- atomic fill-to-M31-ledger postings;
- execution idempotency and reconciliation;
- persistence and migration;
- API, Web, Demo, recovery, and Founder acceptance.

M34 must own execution/fill/ledger effects separately and must not mutate M33
Signal, Intent, or Decision records.

## Approved Route to Genuine Paper Trading

```text
M30 Portfolio-Level Decision Review Foundation — Complete
  -> M31 Stateful Paper Account and Ledger Foundation — Complete
  -> M32 Market Data Replay, Trading Calendar, and Session Clock — Complete
  -> M33 Strategy-to-Order and Pre-Trade Risk Pipeline — Complete
  -> M34 Paper Execution Simulator and First True Paper Trading — next planning milestone
  -> M35 Durable Paper Runtime and Recovery
  -> M36 Multi-day Paper Operations and Acceptance
```

M34–M36 retain no sprint ranges until each receives its own CTO-owned planning
Issue.

### M34 product gate

M34 is the first genuine Paper Trading execution gate. Verified market, account,
Signal, Intent, and Risk evidence must drive simulated execution orders, fills,
and atomic durable Paper Account effects. The Founder must no longer pre-supply
orders and fills as the transaction script.

### M36 product gate

M36 is the continuous multi-day Paper Trading gate. The same account must
advance across sessions with durable checkpoints, reconciliation, explicit
controls, duplicate prevention, and interruption recovery.

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
- M31 ledger events/postings and replay remain financial/account authority.
- M32 calendar/session/event/replay remain market-time authority.
- M33 Signal/Intent/Risk records remain immutable strategy-to-risk authority.
- SQLite remains compact durable state and must not introduce competing
  authority.
- Raw IDs, states, versions, timestamps, values, digests, and artifact content
  remain untranslated.
- Standard and Demo storage remain isolated.
- The browser never directly accesses SQLite, artifact directories, Python,
  QMT, MiniQMT, or a broker.

## Explicitly Deferred

Unless a future authoritative milestone approves them:

- broker, QMT, or MiniQMT integration;
- real-money execution;
- automatic strategy ranking, approval, optimization, or capital allocation;
- public SaaS, multi-tenancy, or complex RBAC;
- microservices, Kubernetes, Kafka, or Redis clusters;
- distributed job infrastructure; and
- broad real-time trading-terminal behavior.
