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
M30 — Portfolio-Level Decision Review Foundation            Next
M31-M36 — Stateful Paper Trading Runtime sequence           Planned
```

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

The authoritative detailed plan is:

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

Future sprint counts and dates remain `TBD`. Every milestone requires its own
planning Issue before implementation.

## M30 — Portfolio-Level Decision Review Foundation

### Purpose

Add portfolio-aware evidence to explicit human decisions before automatic order
generation is introduced.

### Target outcome

The Founder can review:

- concentration and exposure;
- strategy interaction and overlap;
- portfolio-level impact of a proposed strategy decision;
- evidence references and assumptions; and
- an explicit human decision record.

### Boundary

M30 must not allocate capital, generate orders, approve execution, mutate a
runtime account, or connect to a broker.

## M31 — Stateful Paper Account and Ledger Foundation

### Purpose

Create one durable source of truth for cash, positions, orders, fills, and
account snapshots across Paper sessions.

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
- automatic capital allocation;
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
11. Durable account truth precedes automatic order generation.
12. Market-driven Paper Trading precedes continuous runtime automation.
13. Continuous Paper Trading precedes any broker-readiness claim.
