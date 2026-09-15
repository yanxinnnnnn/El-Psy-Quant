# Paper Trading Runtime Roadmap — M30 to M36

## Purpose

This document defines the Founder-approved route from portfolio decision review
to genuine market-driven, durable, and ultimately multi-day Paper Trading.

It is an architectural sequence, not a fixed date commitment. Each milestone
requires its own planning Issue, architecture review, implementation Issues,
Founder acceptance, and manual merge.

## Current Status

```text
M30 — Complete
M31 — Complete
M32 — Complete
M33 — Complete
M34 — Complete
M35 — Complete after S227 closeout merge through S217–S227
M36 — exact next milestone; architecture/planning begins with S228
```

M35 architecture is frozen by Issue #429. S217–S226 are Complete and S227 is the
current documentation-only closeout under Issue #448.

After S227 merge, the expected next Sprint is:

```text
Sprint 228 — Plan Milestone 36: Multi-day Paper Operations and Acceptance
```

No M36 implementation Sprint is approved before S228 architecture is accepted.

Current migration head:

```text
0012_durable_paper_runtime
```

Current Demo source/descriptor/dataset:

```text
v7
```

## Approved Sequence

```text
M30 Portfolio-Level Decision Review Foundation — Complete
  -> M31 Stateful Paper Account and Ledger Foundation — Complete
  -> M32 Market Data Replay, Trading Calendar, and Session Clock — Complete
  -> M33 Strategy-to-Order and Pre-Trade Risk Pipeline — Complete
  -> M34 Paper Execution Simulator and First True Paper Trading — Complete
  -> M35 Durable Paper Runtime and Recovery — Complete after S227 merge
  -> M36 Multi-day Paper Operations and Acceptance — exact next milestone
```

## M30 — Portfolio-Level Decision Review Foundation

**Status: Complete.**

M30 established explicit immutable portfolio-review evidence and one human
approve/reject/defer decision. That decision is governance evidence only; it
does not create/fund an account, allocate capital, create an order, or authorize
execution.

## M31 — Stateful Paper Account and Ledger Foundation

**Status: Complete.**

M31 established:

```text
Paper Account identity/lifecycle
  -> immutable cash and position events/postings
  -> deterministic ledger replay
  -> verified projection cache
  -> immutable snapshot/reconciliation evidence
```

M31 ledger events/postings are financial authority and ledger replay is account
state authority. M31 does not become market time, strategy, execution, or
runtime authority.

## M32 — Market Data Replay, Trading Calendar, and Session Clock

**Status: Complete.**

M32 established Trading Calendar/Session definitions, canonical versioned market
events, deterministic replay ordering/cursor/lifecycle, durable persistence,
restart recovery, read-only market-time APIs, bilingual replay inspection, and
isolated Demo verification.

M32 remains market-time and deterministic progression authority. It does not
create financial/account or execution truth.

## M33 — Strategy-to-Order and Pre-Trade Risk Pipeline

**Status: Complete through S197–S206.**

M33 established:

```text
exact versioned strategy runtime + exact M32 replay prefix
  -> immutable StrategySignal recommendation evidence
  -> exact M31 account head
  -> immutable account-bound OrderIntent or deterministic no-action
  -> exact risk/account/market snapshot
  -> immutable allow/reject PreTradeRiskDecision
```

M33 Intent is risk-pending evidence, not an accepted/executed order. Risk
`allow` is historical evidence over one exact snapshot, not perpetual execution
authorization.

Canonical closeout:

```text
docs/closeouts/milestone-033-strategy-to-order-and-pre-trade-risk-pipeline-closeout.md
```

## M34 — Paper Execution Simulator and First True Paper Trading

**Status: Complete through S207–S216.**

M34 established the execution boundary:

```text
M31 account authority
  + M32 market/replay authority
  + exact M33 Intent + matching allow Decision
    -> immutable PaperExecutionOrder
      -> explicit synchronous one-event Step
        -> immutable PaperExecutionAttempt
          -> optional immutable PaperExecutionFill
            -> exactly one atomic M31 execution settlement
        -> exact M32 progression when an event is consumed
      -> strict historical reconstruction / live freshness / reconciliation
```

M34 owns execution Order/Attempt/Fill authority. M31 remains settlement/financial
authority and M32 remains market-time/cursor authority.

M34 delivered migration `0011_paper_execution`, exactly nine versioned execution
operations, bilingual `/paper-execution`, Demo v6, and adversarial concurrency,
upgrade, rollback, corruption/no-repair, restart, API, and isolation evidence.

Canonical closeout:

```text
docs/closeouts/milestone-034-paper-execution-simulator-and-first-true-paper-trading-closeout.md
```

## M35 — Durable Paper Runtime and Recovery

### Status

**Complete after the S227 closeout PR is merged.**

Architecture/planning authority: Issue #429.
Closeout authority: Issue #448.

Canonical records:

```text
docs/milestones/milestone-035-durable-paper-runtime-and-recovery.md
docs/closeouts/milestone-035-durable-paper-runtime-and-recovery-closeout.md
```

### User-visible outcome

The Founder can create and inspect a durable runtime bound to one exact existing
M34 Order, record Start/Stop/Resume/Recover control intent, inspect health,
reconciliation, audit, Work, and checkpoints, and use the dedicated runner
process to continue/recover execution across process interruption without
creating duplicate execution/financial/market-time effects.

### Final authority model

M35 owns operational orchestration only:

```text
PaperRuntime
  -> desired/observed lifecycle
  -> claim / lease / heartbeat / fencing
  -> one durable PaperRuntimeWork per M34 execution version
  -> S222 recovery / S221 runner
    -> exact existing M34 one-event Step
  -> operational checkpoint/audit observation
```

M35 does not own M31 ledger truth, M32 cursor/event truth, M33 strategy/risk
truth, or M34 execution/fill truth.

There remains exactly one execution path:

```text
M35 -> existing M34 Step -> Attempt -> optional Fill -> M31 settlement / M32 progression
```

### Runtime identity and lifecycle

One v1 runtime binds immutably to one exact M34 Order ID + digest, its exact
account/replay/session, one stable logical actor, and runtime policy ID/version.

Observed states:

```text
ready | running | stopped | completed | blocked
```

Desired states:

```text
running | stopped
```

- Start records desired running; HTTP does not run execution.
- Stop is cooperative and cannot undo an already-entered M34 transaction.
- Resume records desired running from settled stopped; runner execution is still
  required.
- HTTP/Web Recover records recovery request intent only.
- Active recovery remains the dedicated process path.
- completed/blocked are terminal for automatic continuation.

### Claim, lease, heartbeat, fencing

- ownership is database-backed and one-winner;
- only one unexpired owner/fence may own a runtime;
- takeover is limited to absent/expired ownership and advances fencing
  monotonically;
- renew/release/pre-Step/post-Step require the exact active owner + fence;
- a fenced old worker may finish an already-entered M34 transaction but may not
  observe as current owner or begin a next Step;
- heartbeat updates current operational lease state without unbounded immutable
  audit spam;
- lease wall clock is operational only and never M32 market time.

### Durable Work and idempotency

Each logical Work fixes:

```text
runtime_id
execution_order_id + digest
expected_execution_version
stable M34 Step idempotency key
stable runtime logical actor
```

Retry/restart/takeover of the same logical iteration reuses the exact same M34
key/actor/version. The transient owner/process ID is never the M34 actor.

### Runner transaction boundary

The runner remains deliberately split:

```text
M35 pre-Step transaction -> commit/close
exact existing M34 Step transaction
M35 post-Step observation transaction
```

No M35 transaction wraps M34 Step.

M35 never directly consumes a market event, derives a Fill, calls M31
settlement, or advances the M32 cursor.

### Recovery

The delivered recovery model closes the frozen crash windows:

- A: crash before Work creation;
- B: Work committed before Step;
- C: ambiguous Step outcome;
- D: Step committed before M35 observation;
- E: lease expires while old worker is inside Step;
- F: contradictory/corrupt authority.

Recovery may retry the same stable M34 identity or catch up a missing M35
observation. It may never repair canonical M31–M34 authority.

The accepted ambiguous case where a canonical Attempt exists but the pending
Work-key M34 receipt is absent converges by retrying the same Work identity; it
is not automatically corruption.

### API, CLI, Web

M35 exposes exactly twelve authenticated runtime HTTP operations for create,
list/detail, lifecycle control, health/reconciliation, and bounded audit/Work/
checkpoint inspection.

No HTTP endpoint hosts the runner.

Supported active process surface:

```text
run-paper-runtime -> S222 recovery -> S221 runner
```

The bilingual `/paper-runtimes` workspace remains control + inspection only.
The browser does not claim leases, generate fences, run M34 Step, create Work or
checkpoints, or mutate M31/M32.

### Persistence and acceptance

M35 migration:

```text
0012_durable_paper_runtime
```

Final accepted S226 implementation baseline:

```text
reviewed head: 9f57f030a7847a7176a09265a56be16faae2362e
reviewed merge ref: 5741c33a49c454bed19169a9fba420c506edd3d4
merged main baseline: 6af41c166d4106c89c0189d3688773cde7d2cb77
Python: 3396 passed
Web: 501 passed / 51 files
Demo: v7
Founder Docker/browser runtime acceptance: PASS
```

Founder acceptance proved the deterministic v7 journey:

```text
fresh stopped/ready runtime
Start control-only
Recover request control-only
worker A: no-fill, fence 1, M32 4 -> 5
worker B: one Fill/SettlementLink/M31 posting, fence 2, M32 5 -> 6
Stop + worker C: stopped/stopped, fence 3, runner not run
Resume control-only
worker D: boundary rejection, runtime completed, fence 4, M32 remains 6
completed re-entry: no fourth Work/Attempt/effect
restart persistence: passed
return-to-Standard isolation: passed
```

### M35 boundary

M35 intentionally does not add automatic future M33/M34 generation, multi-day
rollover, overnight scheduling, multi-account allocation, reservations,
distributed scheduling, broker/live behavior, or automatic corruption repair.

## M36 — Multi-day Paper Operations and Acceptance

### Status

**Exact next milestone after S227 merge. Planning begins with S228.**

Expected planning Sprint:

```text
Sprint 228 — Plan Milestone 36: Multi-day Paper Operations and Acceptance
```

### Product gate

M36 is the continuous multi-session/multi-day Paper Trading gate.

### Planning questions for S228

S228 must explicitly decide before implementation:

- what durable identity owns a multi-day operating run;
- whether one M35 runtime remains one Order and a higher-level operation composes
  multiple runtimes;
- session/day rollover rules;
- overnight/closed-market behavior;
- how M32 replay/calendar/session authority advances across trading days;
- EOD checkpoints and cross-day restart/recovery;
- cross-day M31 freshness and reconciliation;
- when/how later M33 Signal/Intent/Decision and M34 Order authority is created;
- operating scheduler/process boundaries;
- concurrency/idempotency/duplicate-day prevention;
- multi-account/shared-stream/reservation boundaries;
- API/Web/operator-control surfaces;
- migration needs;
- Standard/Demo isolation and whether Demo v8 is required;
- Founder multi-day acceptance; and
- the detailed M36 sprint sequence.

M36 must preserve M31–M35 authority rather than bypassing it.

## Authority Boundaries Across M31–M36

```text
M30 review evidence
  != M31 ledger truth
  != M32 market/session truth
  != M33 signal/intent/risk truth
  != M34 execution/fill truth
  != M35 runtime orchestration truth
  != M36 future multi-day operating authority
```

Each layer may reference earlier evidence, but it must not silently copy,
reinterpret, or repair another layer's authority.

The preserved architecture remains:

```text
Browser
  -> Next.js Founder Workspace
  -> fixed same-origin gateway
  -> versioned FastAPI API
  -> thin application services
  -> domain, ledger, market, risk, execution, and runtime authorities
  -> compact SQLite state and authoritative artifacts
```

## Broker and Live Direction After M36

Broker-specific behavior remains behind a future broker-neutral adapter boundary.
M36 completion would not automatically authorize live trading.

A later explicit milestone must define broker-neutral execution commands,
credential/secret handling, external submit/ack/reject/partial-fill/cancel/
replace semantics, reconciliation, kill-switch/risk controls, operational
ownership, rollback, live readiness, and Founder real-money acceptance.

No browser-to-QMT direct connection is allowed.

## Planning Rule

Only one milestone is planned and implemented at a time.

Current action:

```text
complete Sprint 227 documentation-only M35 closeout under Issue #448
```

After S227 merge, create/accept S228 architecture before any M36 implementation
begins.
