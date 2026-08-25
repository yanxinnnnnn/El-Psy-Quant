# Milestone 34 Closeout — Paper Execution Simulator and First True Paper Trading

## Status

Milestone 34 is Complete after the Sprint 216 closeout PR is merged.

Issue #408 remains the authoritative M34 architecture source for the delivered
boundary. Sprint 216 records the final repository closeout and freezes the
handoff to Milestone 35 without changing runtime behavior.

## Delivered Capability

M34 delivered the first genuine market/strategy-driven Paper Trading execution
chain in El-Psy-Quant:

```text
M31 immutable Paper Account ledger authority
  + M32 durable calendar/session/event/replay authority
  + immutable M33 OrderIntent + matching allow PreTradeRiskDecision
    -> immutable M34 PaperExecutionOrder
      -> explicit synchronous one-event Step
        -> immutable PaperExecutionAttempt
          -> optional immutable PaperExecutionFill
            -> exactly one atomic M31 execution settlement
        -> exact M32 checkpoint progression when one event is consumed
      -> strict historical reconstruction / live-freshness continuation
      -> read-only reconciliation
```

The Founder no longer supplies fill price or fill quantity as transaction truth.
Future replay events, the frozen execution policy, exact execution-time risk
revalidation, and M31/M32 authority determine the outcome.

M34 remains manual and synchronous. It does not add a durable execution loop,
worker, scheduler, claim/lease system, heartbeat, automatic recovery loop, or
multi-day operations.

## Completed Sprint Chain

| Sprint | Delivered boundary | Status |
|---:|---|---|
| S207 | Milestone 34 Architecture and Planning | Complete |
| S208 | Paper Execution Order, Policy, and Lifecycle Contract Foundation | Complete |
| S209 | Deterministic One-Event Execution, Pricing, Costs, and Fill Semantics | Complete |
| S210 | Atomic Execution Fill to M31 Ledger Domain Integration | Complete |
| S211 | Durable M34 Persistence, Migration, Transactions, Idempotency, and Reconciliation | Complete |
| S212 | Versioned Paper Execution API, Errors, Audit, and Generated Contracts | Complete |
| S213 | Bilingual Founder Paper Execution Workspace | Complete |
| S214 | Demo v6 and End-to-End First True Paper Trading Evidence | Complete |
| S215 | M34 Restart, Concurrency, Upgrade, Recovery, Corruption, and Isolation Hardening | Complete |
| S216 | Milestone 34 Closeout and M35 Handoff | Complete after merge |

## Final Authority Model

### PaperExecutionOrder

`PaperExecutionOrder` is immutable acceptance of one exact M33 Intent and
matching `allow` Decision into the M34 simulator under one explicit execution
policy and one exact verified M31/M32 handoff.

Order creation derives side, requested quantity, account, instrument, market
anchors, and trusted handoff facts from reconstructed upstream authority. The
caller does not author those values. Creation does not reserve cash or
positions, mutate M31, or advance M32.

### PaperExecutionAttempt

`PaperExecutionAttempt` is immutable evidence for one exact execution Step from
one exact prior M34/M31/M32 state. Execution version starts at `0` and increases
by exactly one for each committed Attempt, including no-fill and terminal
rejection attempts.

One Step processes at most one future in-session M32 event. Boundary exhaustion
can create a terminal rejection Attempt without consuming an out-of-session
event.

### PaperExecutionFill

`PaperExecutionFill` is immutable execution truth for one fill quantity at one
M34-owned execution price with exact slippage and cost evidence. Fill identity
is distinct from legacy backtest/Paper fill records and from M33 risk-price
evidence.

### ExecutionSettlementLink and M31

Every Fill has exactly one `ExecutionSettlementLink` to exactly one M31
`execution_fill_posted` event. That link is reconciliation evidence only; M31
ledger events/postings remain financial authority.

The matching M31 event owns exactly one `execution_settlement` cash posting and
one `execution_fill` position posting. Fill + settlement + M32 checkpoint + M34
Attempt/Fill/link + command receipt commit in one caller-owned database
transaction.

### Derived PaperExecutionOrderState

Order state is reconstructed from immutable Order/Attempt/Fill/settlement
history. There is no mutable execution-status authority row.

The closed M34 lifecycle is:

```text
working
partially_filled
filled
rejected
partially_filled_rejected
```

## Preserved M31 / M32 / M33 Boundaries

M31 remains:

```text
immutable ledger events/postings = financial authority
deterministic ledger replay = Paper Account state authority
projection/snapshot/reconciliation = derived evidence/cache
```

M32 remains:

```text
TradingCalendar / TradingSession = calendar/session authority
MarketDataEvent = canonical market-state event authority
MarketDataReplayEngine = ordering/cursor/lifecycle/progression authority
```

M33 remains immutable:

```text
StrategySignal
  -> account-bound OrderIntent or no-action
  -> allow/reject PreTradeRiskDecision
```

An M33 `allow` Decision is historical evidence over one exact snapshot, not a
perpetual execution authorization. M34 Create/Step revalidates the exact frozen
freshness rules and never mutates Signal, Intent, or Decision records.

Later legitimate M31/M32 movement does not erase historical M34 evidence.
Historical reads remain inspectable while a genuinely new Step fails closed if
current live authority is stale or reconciliation is required.

## Execution, Pricing, Cost, and Risk Semantics

M34 execution timing uses future replay events after the M33 handoff cursor. The
M33 anchor event is never silently reused as execution-price authority.

The delivered v1 execution semantics remain:

```text
price policy:      consumed_trade_event_price_v1
slippage policy:   fixed_bps_slippage_v1
cost policy:       per_fill_bps_costs_v1
risk policy family: long_only_cash_risk_v1 revalidated at execution time
```

A fill-eligible event must be the exact consumed next M32 event, belong to the
same instrument, be a `trade`, and carry a supported positive price.
Different-instrument, non-trade, or otherwise ineligible consumed events create
immutable no-fill Attempts while advancing exactly one M32 cursor step.

Execution-time risk failure is a committed business rejection: the valid
in-session event is consumed, an immutable terminal rejection Attempt is
recorded, no Fill is created, and M31 is not mutated.

Stale, concurrency, idempotency, storage, or corruption failures are operational
refusals rather than business execution outcomes and must leave no partial
business authority.

## Persistence and Migration

Sprint 211 added the M34 schema revision:

```text
0010_strategy_order_risk
  -> 0011_paper_execution
```

The final migration head for M34 is exactly:

```text
0011_paper_execution
```

M34 durable authority uses append-only Order, Attempt, Fill,
SettlementLink, and command-receipt records with deterministic identities,
strict reconstruction, restrictive references, one-winner SQLite transactions,
M31/M32 CAS, and read-only reconciliation.

S215 confirmed a populated Standard `0010 -> 0011` upgrade preserves existing
M31/M32/M33 authority exactly, begins with empty M34 authority, and can
immediately Create/Step/reconcile through the normal application path.

No migration `0012` belongs to M34.

## API, Web, and Demo Surfaces

Sprint 212 exposes exactly nine authenticated Paper Execution operations for
Order create/list/detail, explicit one-event Step, Attempt list/detail, Fill
list/detail, and explicit reconciliation. Stable request IDs, bounded audit,
opaque pagination, canonical OpenAPI, and generated TypeScript are transport
surfaces only.

Sprint 213 adds one bilingual `/paper-execution` Founder workspace. The browser
loads durable M33 allow/Intent evidence, submits explicit raw-string execution
policy values, creates one Order, processes at most one event per click, and
inspects immutable Attempt/Fill/risk/settlement/reconciliation evidence. It does
not calculate execution, financial, risk, lifecycle, or replay authority.

Sprint 214 upgrades the isolated Demo system to source/descriptor/dataset v6.
Demo v6 includes one fresh manual Founder handoff plus deterministic completed,
execution-time-risk-rejection, and session/replay-exhaustion scenarios. Prebuilt
M34 authority is created only through merged application paths; M34 tables are
not direct-seeded.

Standard remains persistent and unseeded. Demo remains isolated and disposable.
Descriptor metadata remains discovery/verification metadata, not execution
authority.

## Hardening and Recovery Evidence

The merged S211–S215 implementation proves:

- exact Create/Step retries are restart-safe and historically replayable;
- changed-content idempotency-key reuse conflicts without partial writes;
- same-key and alternate-key concurrent Create/Step races converge on one
  durable authority with no duplicate Attempt, Fill, settlement, or M32 advance;
- real SQLite `BEGIN IMMEDIATE` lock contention is bounded, sanitized, and
  retryable;
- fill and no-fill transaction fault injection rolls back M34, M31, M32, and
  receipt changes atomically;
- deliberate corruption across M34/M31/M32/M33/receipt authority fails closed
  and is never auto-repaired or rebased;
- restart reconstructs version-0, no-fill, partial-fill, full-fill,
  execution-risk-rejection, and exhaustion states exactly;
- historical evidence remains inspectable after later legitimate external
  M31/M32 movement while unsupported continuation fails stale;
- API 409/503 surfaces remain sanitized and non-mutating; and
- cross-wired Standard/Demo runtime configuration fails before preparation,
  install, verification, or serving can touch the wrong workspace.

## Final Verification Baseline

The final reviewed Sprint 215 implementation baseline was PR #424 head:

```text
df82b44131726678f8f019a70835414fac297aef
```

PR #424 merged as:

```text
0725c80de0664b727fc76e772eb6522247a70ad5
```

Latest reviewed GitHub Actions run:

```text
32387052678
```

Verified results:

- Python: `3257 passed`;
- Web: `471 passed / 49 files`;
- Ruff/import/CLI/messages/contracts/lint/typecheck/production build: PASS;
- packaged migration-resource gate: PASS with head `0011_paper_execution`;
- Demo source/descriptor/dataset: v6; and
- S215 required no production-code changes beyond the already merged S208–S214
  implementation.

Codex did not run Docker/Compose/container startup, volume removal, Demo reset,
or Founder Standard/Demo/browser runtime acceptance in S215. Sprint 216 is
documentation-only and does not invent a new runtime-acceptance claim.

## Explicit M34 Non-Goals and Known Limitations

M34 closes without owning or authorizing:

- a durable worker, scheduler, queue, claim, lease, or heartbeat;
- automatic repeated execution Steps;
- start/stop/resume runtime controls;
- operational abandonment/recovery state beyond existing fail-closed manual
  continuation/reconciliation semantics;
- continuous or multi-day Paper Trading;
- multiple concurrent working Orders sharing one replay/session event stream;
- reservation/capital locking for unfilled quantity;
- broker, QMT, MiniQMT, private-edge, live, or real-money behavior;
- automatic strategy ranking, approval, optimization, or capital allocation; or
- public SaaS, distributed execution infrastructure, or multi-tenant behavior.

The M34 v1 single-working-order boundary for one
`(account_id, replay_id, trading_session_id)` remains intentional. Broader
runtime ownership and orchestration require explicit M35 architecture.

## Milestone 35 Handoff

Milestone 35 — Durable Paper Runtime and Recovery — is the exact next milestone.

M35 must reuse the merged M34 execution primitives rather than invent a second
execution path. In particular, M35 automation must continue to treat the M34
one-event Step transaction as the unit of execution truth.

After its own CTO planning gate, M35 may design:

- durable work ownership, claims, or leases;
- explicit start/stop/resume controls;
- heartbeat/stale-work detection where approved;
- durable execution loops that repeatedly invoke the existing M34 Step
  primitive;
- interruption recovery and durable runtime checkpoints;
- operational reconciliation; and
- bounded runtime observability.

M35 must not silently redefine M34 Order/Attempt/Fill identity or lifecycle,
execution-price/slippage/cost/risk semantics, event-to-fill semantics, M31
settlement authority, M32 event/cursor authority, M33 immutable authority,
Decimal/digest/idempotency/corruption behavior, Standard/Demo isolation, or the
browser authority boundary.

The exact next Sprint after this closeout is accepted and merged is a CTO-owned
architecture/planning Sprint:

```text
Sprint 217 — Plan Milestone 35: Durable Paper Runtime and Recovery
```

S217 must freeze runtime ownership, work identity, claim/lease semantics,
loop/checkpoint and recovery state machines, concurrency/crash behavior,
controls, API/Web/Demo/observability surfaces, migration needs, acceptance, and
the detailed M35 Sprint sequence before any M35 runtime implementation begins.
