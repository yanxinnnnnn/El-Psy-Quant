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
  Issue creation, documentation-only planning/closeout work, and PR review.
- Codex acts as implementation developer for coding sprints.
- Documentation-only planning and closeout work is CTO-owned; do not delegate it
  to Codex unless the Founder explicitly requests otherwise.
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
- VPN, proxy, and network settings are Founder/machine environment, not product
  or repository authority. Do not assume a specific provider, endpoint, port,
  environment variable, or network topology.
- If dependency or network access fails, report the observed failure. Do not add
  repository-level proxy settings or change unrelated project files merely to
  work around the local network environment.
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

## Authority Chain Through M35

```text
M31 immutable ledger/account authority
  + M32 calendar/session/event/replay authority
  + M33 immutable Signal/Intent/Risk authority
    -> M34 immutable Order/Attempt/Fill execution authority
      -> M35 durable operational runtime orchestration
        -> exact existing M34 one-event Step
```

- M31 ledger events/postings remain financial authority and ledger replay remains
  Paper Account state authority.
- M32 calendar/session/event/replay remain market-time and cursor authority.
- M33 Signal/Intent/Risk evidence remains immutable strategy-to-risk authority.
- M34 Order/Attempt/Fill remain immutable execution authority; linked M31
  settlement remains financial truth.
- M35 owns runtime/work/claim/lease/fence/checkpoint/audit orchestration only.
  It does not own execution price, fills, settlement, M31 state, M32 cursor, or
  M33 authority.
- There is exactly one execution path: M35 invokes the existing M34 Step.
- M35 operational checkpoints may catch up coherent missing observation but must
  never repair canonical M31–M34 corruption.

## Definition of Done

A task is complete only when scope matches the authoritative Issue, documentation
matches behavior, assumptions and limitations are explicit, authority boundaries
remain intact, required verification passes, the PR is Ready for review, and the
PR is not merged by Codex or the CTO.

## Completed Foundations

Milestones 1–34 are Complete. Milestone 35 is closing through Sprint 227 and is
Complete after the S227 closeout PR is merged.

Recent Paper Trading milestones:

```text
M30 — S169-S178 Portfolio-Level Decision Review Foundation
M31 — S179-S188 Stateful Paper Account and Ledger Foundation
M32 — S189-S196 Market Data Replay, Trading Calendar, and Session Clock
M33 — S197-S206 Strategy-to-Order and Pre-Trade Risk Pipeline
M34 — S207-S216 Paper Execution Simulator and First True Paper Trading
M35 — S217-S227 Durable Paper Runtime and Recovery
```

### M35 delivered

- one `PaperRuntime` immutably bound to one exact existing M34 Order;
- desired/observed lifecycle with control-only Start/Resume/Recover-request and
  cooperative Stop;
- database-backed one-winner claims, leases, heartbeat, and monotonic fencing;
- one durable `PaperRuntimeWork` per execution version with stable M34 Step
  key/actor/version across retry, restart, and takeover;
- an M35-before / exact-M34-Step / M35-after transaction boundary;
- crash/restart/stale-lease recovery across windows A–F;
- mutation-free reconciliation and fail-closed no-repair behavior;
- migration `0012_durable_paper_runtime`;
- exactly twelve runtime HTTP operations plus dedicated `run-paper-runtime` CLI;
- bilingual `/paper-runtimes` control/inspection workspace;
- concurrency/idempotency/recovery/observability/isolation hardening; and
- deterministic Demo v7 E2E plus Founder Docker/browser acceptance.

Final accepted S226 baseline:

```text
Python: 3396 passed
Web: 501 passed / 51 files
migration head: 0012_durable_paper_runtime
Demo: v7
```

Canonical M35 records:

```text
docs/milestones/milestone-035-durable-paper-runtime-and-recovery.md
docs/closeouts/milestone-035-durable-paper-runtime-and-recovery-closeout.md
```

## Current Focus

Sprint 227 is the documentation-only Milestone 35 closeout and M36 handoff under
Issue #448. S217–S226 are Complete. After the S227 PR is merged, Milestones
1–35 and S217–S227 are Complete.

The exact next milestone is:

```text
M36 — Multi-day Paper Operations and Acceptance
```

The expected next Sprint is the CTO-owned planning gate:

```text
Sprint 228 — Plan Milestone 36: Multi-day Paper Operations and Acceptance
```

S228 must define multi-day operating identity, session/day rollover,
overnight/closed-market behavior, M32 continuation across days, EOD checkpoints,
cross-day restart/recovery, M31 freshness, future M33/M34 creation boundaries,
higher-level orchestration over one-Order M35 runtimes, scheduling, concurrency,
idempotency, reconciliation, API/Web/Demo evolution, migration needs, isolation,
and the detailed M36 sprint sequence before implementation begins.

Current migration head:

```text
0012_durable_paper_runtime
```

Current Demo source/descriptor/dataset:

```text
v7
```

## Approved Route to Genuine Paper Trading

```text
M30 Portfolio-Level Decision Review Foundation — Complete
  -> M31 Stateful Paper Account and Ledger Foundation — Complete
  -> M32 Market Data Replay, Trading Calendar, and Session Clock — Complete
  -> M33 Strategy-to-Order and Pre-Trade Risk Pipeline — Complete
  -> M34 Paper Execution Simulator and First True Paper Trading — Complete
  -> M35 Durable Paper Runtime and Recovery — Complete after S227 merge
  -> M36 Multi-day Paper Operations and Acceptance — exact next milestone
```

Authoritative runtime roadmap:

```text
docs/strategy/paper-trading-runtime-roadmap.md
```

## Explicitly Deferred

Unless a future authoritative milestone approves them:

- multi-day Paper Trading policy before M36 planning;
- broker, QMT, or MiniQMT integration;
- real-money execution;
- automatic strategy ranking, approval, optimization, or capital allocation;
- public SaaS, multi-tenancy, or complex RBAC;
- microservices, Kubernetes, Kafka, or Redis clusters;
- distributed job infrastructure; and
- broad real-time trading-terminal behavior.
