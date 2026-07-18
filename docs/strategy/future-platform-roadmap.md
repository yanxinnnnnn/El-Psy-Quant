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
  -> stateful market-driven Paper Trading
  -> durable multi-day Paper operations
  -> execution-risk and live-readiness controls
  -> broker-neutral adapter
  -> tightly controlled live pilot
```

## Current State

Milestones 1–29 are Complete.

```text
M25 — Paper Trading Productization Planning                 Complete
M26 — Paper Trading Application Service Foundation          Complete
M27 — Persistence and Paper Job Control Foundation          Complete
M28 — Founder Paper Trading Web Workspace                   Complete
M29 — Product Feedback and Hardening                        Complete
M30 — Portfolio-Level Decision Review Foundation            In Progress (S169-S177)
M31-M36 — Stateful Paper Trading Runtime sequence           Planned
```

Sprint 169 establishes the M30 architecture and milestone plan. Sprint 170 is the
next implementation sprint after Founder review and merge of the S169 planning
PR.

M29 completed the transition from a working local MVP to a bilingual, modern,
actionable, and dependable Founder product.

## Completed Milestone 29 — Product Feedback and Hardening

### Outcome

```text
working local MVP
  -> complete English / Simplified Chinese product
  -> AI Quant Decision Workspace visual system
  -> Founder Dashboard and workflow information architecture
  -> understandable idempotency, retry, and recovery
  -> actionable errors and audit information
  -> hardened migrations, tests, and local deployment
  -> formal closeout and Paper Trading runtime handoff
```

### Delivered sprint chain

| Sprint | Deliverable | Status |
|---:|---|---|
| S161 | Founder Feedback and Product Experience Architecture | Complete |
| S162 | Multilingual Foundation and Simplified Chinese Workspace | Complete |
| S163 | Modern Visual System Foundation | Complete |
| S164 | Founder Dashboard and Workflow Information Architecture Refresh | Complete |
| S165 | Reliability, Idempotency, and Job Recovery Hardening | Complete |
| S166 | Error Surface, Observability, and Audit Hardening | Complete |
| S167 | Migration, Test, and Local Deployment Hardening | Complete |
| S168 | Milestone 29 Closeout and M30–M36 Handoff | Complete |

### Product principles proven by M29

- Bilingual completeness over partial translation.
- Decision clarity over dashboard density.
- Visible state over hidden automation.
- Actionable recovery over generic errors.
- Local-first simplicity over distributed infrastructure.
- Human judgment over automatic recommendation or approval.
- Raw domain and artifact truth over presentation convenience.
- Accessibility and responsive behavior in both languages.
- Direct Founder feedback over speculative product features.

### Preserved authority

```text
Browser
  -> Next.js Founder Workspace
  -> fixed same-origin /api/backend gateway
  -> versioned FastAPI API
  -> thin application services
  -> existing domain modules and artifact readers
  -> isolated SQLite and authoritative artifact roots
```

- Domain modules remain financial and governance authority.
- Completed files remain authoritative artifact payloads.
- SQLite remains compact metadata and operational state.
- Backend contracts and raw values remain untranslated.
- Paper Job state remains separate from lifecycle governance.
- Lifecycle proposals remain non-executing.
- Human review remains explicit governance evidence.
- Standard and Demo storage remain isolated.
- The browser never directly accesses SQLite, files, Python, QMT, or a broker.

### What M29 did not deliver

M29 did not add:

- a persistent stateful Paper Account ledger across sessions;
- market-data replay tied to a trading calendar and session clock;
- automatic strategy-to-order conversion;
- pre-trade risk for automatically generated orders;
- a runtime order lifecycle or execution simulator;
- a durable multi-session worker/checkpoint loop;
- continuous multi-day Paper Trading;
- broker, QMT, MiniQMT, or real-money execution;
- automatic strategy ranking, approval, or capital allocation; or
- distributed infrastructure.

These are explicit future boundaries, not hidden omissions.

Closeout records:

```text
docs/milestones/milestone-029-product-feedback-and-hardening.md
docs/closeouts/milestone-029-product-feedback-and-hardening-closeout.md
```

## Approved M30–M36 Sequence

The authoritative detailed runtime plan is:

```text
docs/strategy/paper-trading-runtime-roadmap.md
```

```text
M30 Portfolio-Level Decision Review Foundation
  -> M31 Stateful Paper Account and Ledger Foundation
  -> M32 Market Data Replay, Trading Calendar, and Session Clock
  -> M33 Strategy-to-Order and Pre-Trade Risk Pipeline
  -> M34 Paper Execution Simulator and First True Paper Trading
  -> M35 Durable Paper Runtime and Recovery
  -> M36 Multi-day Paper Operations and Acceptance
```

M30 now has an approved S169–S177 architecture. M31–M36 sprint counts and dates
remain `TBD`. Every milestone receives its own planning Issue before
implementation.

## Milestone 30 — Portfolio-Level Decision Review Foundation

### Status

In Progress through S169–S177.

Authoritative M30 planning:

```text
docs/architecture/portfolio-level-decision-review.md
docs/milestones/milestone-030-portfolio-level-decision-review-foundation.md
docs/sprints/sprint-169-milestone-30-architecture-and-planning.md
```

### Purpose

Add reproducible portfolio-aware evidence to explicit human decisions before a
stateful account, automatic order generation, or execution simulation is
introduced.

### Target outcome

The Founder can explicitly compare a baseline and proposed static portfolio
scenario and inspect:

- strategy/component concentration;
- review exposure and component-weight changes;
- supported symbol/universe overlap;
- historical return interaction;
- baseline/proposed portfolio risk, drawdown, and contribution context;
- explicit historical scenario deltas;
- source identity, evaluation window, assumptions, warnings, and missing evidence;
  and
- one explicit `approved`, `rejected`, or `deferred` human decision.

### Data authority

M30 requires a new immutable portfolio-review source artifact because existing
configured research artifacts expose summary metrics but not the aligned strategy
return observations required to reproduce interaction and proposed impact.

The source remains explicit and selected. M30 does not automatically discover
runs or infer relationships between unrelated records.

### Quantitative boundary

The first version uses explicit non-negative static weights summing to `1.0` and a
bounded union of at most 12 selected strategy components.

Approved evidence includes a bounded subset of:

```text
largest weight / top-three concentration / HHI / effective count
component weight deltas and declared universe coverage
shared symbols and Jaccard overlap
pairwise historical Pearson return correlation
candidate-to-baseline portfolio correlation
baseline/proposed mean, volatility, loss rate, drawdown, and contribution
proposed minus baseline scalar deltas
```

Undefined values remain unavailable with warnings. Outputs are historical
scenario evidence, not forecasts, rankings, recommendations, or allocation
instructions.

### Product and persistence boundary

```text
explicit Founder source/scenario selection
  -> versioned API command
  -> thin application service
  -> domain calculations
  -> immutable source/analysis/decision artifacts
  -> compact SQLite identity/reference/idempotency metadata
  -> bilingual Founder list/create/detail/decision workflow
```

Full quantitative payloads remain artifact authority. SQLite does not become a
return-series or matrix store.

### Human-control boundary

An M30 approval is portfolio-review governance evidence only. It does not:

- change strategy lifecycle state automatically;
- allocate or reserve capital;
- create or mutate a Paper Account;
- create positions, orders, fills, or ledger entries;
- start a market session, worker, or scheduler; or
- authorize broker or live execution.

### Approved M30 sprint chain

| Sprint | Deliverable | Owner | Status |
|---:|---|---|---|
| S169 | Milestone 30 Architecture and Planning | CTO | In review |
| S170 | Portfolio Review Input and Scenario Contract Foundation | Codex | Next after S169 merge |
| S171 | Concentration and Exposure Analysis Foundation | Codex | Planned |
| S172 | Strategy Interaction and Proposed Portfolio Impact Foundation | Codex | Planned |
| S173 | Portfolio Review Artifact and Human Decision Foundation | Codex | Planned |
| S174 | Durable Portfolio Review Persistence and Application/API Foundation | Codex | Planned |
| S175 | Founder Portfolio Decision Review Web Workspace | Codex | Planned |
| S176 | Portfolio Review Workflow Integration, Demo, and Acceptance Hardening | Codex | Planned |
| S177 | Milestone 30 Closeout and M31 Handoff | CTO | Planned |

### Boundary

M30 must not optimize weights, recommend a strategy, allocate capital, mutate a
runtime account, generate orders or fills, add market-data/session behavior,
create a worker/scheduler, or connect to a broker.

## M31 — Stateful Paper Account and Ledger Foundation

### Purpose

Create one durable source of truth for cash, positions, orders, fills, and
account snapshots across Paper sessions.

### M30 handoff boundary

M31 may reference an approved M30 review ID and immutable decision evidence, but
must establish a separate account and ledger authority.

M30 scenario weights are review assumptions. They are not balances, positions,
reserved cash, orders, fills, ledger entries, or executable allocation
instructions. No M30 approval creates or funds an account.

### Boundary

M31 does not add market-data automation, strategy-to-order conversion, or
continuous execution. It establishes durable account truth first.

## M32 — Market Data Replay, Trading Calendar, and Session Clock

### Purpose

Provide deterministic historical market sessions with explicit calendar,
timezone, completeness, duplicate, missing-data, and stale-data rules.

### Boundary

Historical replay is sufficient. M32 does not require live streaming, exchange
connectivity, or a broker feed.

## M33 — Strategy-to-Order and Pre-Trade Risk Pipeline

### Purpose

Convert approved strategy output and current account state into target exposure,
idempotent order intent, and bounded risk-checked Paper orders.

### Boundary

The pipeline remains broker-neutral and Paper-only. It must not execute live or
automatically approve a strategy.

## M34 — Paper Execution Simulator and First True Paper Trading

### First true Paper Trading gate

At M34 completion, the Founder can choose an approved strategy, explicit account,
symbols, and a historical market session. The platform itself:

```text
reads validated market data
  -> evaluates the strategy
  -> derives target exposure and order intent
  -> applies pre-trade risk
  -> simulates order lifecycle and fills
  -> updates the durable Paper Account and ledger
  -> exposes complete audit evidence
```

The Founder no longer supplies orders and fills as the transaction script.
Manual session start is allowed. Automatic scheduling and continuous operation
are not yet required.

### Boundary

M34 remains Paper-only and local-first. It does not authorize live execution,
QMT, or broker integration.

## M35 — Durable Paper Runtime and Recovery

### Purpose

Make session execution durable under interruption and duplicate commands.

Expected capability includes:

- durable session/work identity;
- claim and checkpoint semantics;
- explicit start, pause, resume, and recover controls;
- duplicate event and execution prevention;
- deterministic replay and reconciliation; and
- safe failure evidence.

A single-process local runtime remains acceptable. Distributed workers are not a
default requirement.

## M36 — Multi-day Paper Operations and Acceptance

### Continuous Paper Trading gate

At M36 completion, the same account advances across multiple sessions and
trading days with:

- durable checkpoints;
- daily/session reconciliation;
- explicit operational controls;
- interruption recovery;
- duplicate prevention;
- bounded monitoring and audit; and
- Founder operational acceptance.

This is the first point at which El-Psy-Quant can claim a continuous multi-day
Paper Trading product.

M36 is still not permission for real-money execution.

## Future Execution Direction After M36

Broker-specific systems remain adapters behind broker-neutral domain and
application models:

```text
Browser
  -> Web/API
  -> broker-neutral execution command
  -> isolated adapter or Windows agent
  -> QMT / MiniQMT or another broker runtime
  -> broker
```

No browser-to-QMT direct connection is allowed.

No live work begins merely because M36 completes. A later explicit milestone must
first approve:

- execution-risk governance;
- live-readiness controls;
- operational readiness;
- broker-adapter boundaries;
- capital limits and kill controls; and
- explicit Founder authorization.

## Codex and Founder Verification Policy

Codex owns deterministic repository verification:

```text
uv run python scripts/check.py
```

Codex may run approved non-starting static checks when relevant. Codex does not
perform Docker runtime acceptance unless the Founder explicitly changes the
policy for the current sprint.

The Founder owns local Docker runtime, browser acceptance, backup/reset actions,
and manual merge decisions.

## Explicitly Deferred

Unless a future milestone explicitly approves them:

- broker, QMT, or MiniQMT integration;
- real-money execution;
- automatic strategy ranking or approval;
- automatic portfolio optimization or capital allocation;
- public SaaS, multi-tenancy, or complex RBAC;
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
11. Portfolio review assumptions do not become account truth.
12. Durable account truth precedes automatic order generation.
13. Market-driven Paper Trading precedes continuous runtime automation.
14. Continuous Paper Trading precedes any broker-readiness claim.
