# Milestone 35 Closeout — Durable Paper Runtime and Recovery

## Status

Milestone 35 is **Complete after Sprint 227 is merged**.

Authoritative architecture/planning source: GitHub Issue #429.
Authoritative closeout specification: GitHub Issue #448.

Final merged implementation baseline before this closeout:

- S226 PR #447 reviewed head: `9f57f030a7847a7176a09265a56be16faae2362e`;
- reviewed merge ref: `5741c33a49c454bed19169a9fba420c506edd3d4`;
- PR #447 merge commit / S227 baseline `main`: `6af41c166d4106c89c0189d3688773cde7d2cb77`;
- accepted GitHub Actions run: `34182537933`;
- quality job: `101924349050`;
- Python: `3396 passed`;
- Web: `501 passed / 51 files`;
- Ruff/import/CLI/messages/contracts/lint/typecheck/Next production build: PASS;
- migration head: `0012_durable_paper_runtime`;
- Demo source/descriptor/dataset: v7.

Sprint 227 is documentation-only. It does not change runtime behavior.

## What M35 Delivered

M35 turned the manually stepped M34 execution primitive into a durable,
restart-safe operational runtime without creating a second execution engine.

The final authority chain is:

```text
M31 immutable Paper Account ledger authority
  + M32 durable calendar/session/event/replay authority
  + immutable M33 Signal / OrderIntent / matching allow PreTradeRiskDecision
    -> immutable M34 PaperExecutionOrder
      -> M35 durable PaperRuntime operational orchestration
        -> durable claim / lease / heartbeat / fencing
        -> durable logical PaperRuntimeWork identity
        -> S222 recovery / S221 runner
          -> exact existing M34 one-event Step
            -> immutable PaperExecutionAttempt
              -> optional immutable PaperExecutionFill
                -> exactly one atomic M31 execution settlement
            -> exact M32 progression when one event is consumed
        -> M35 checkpoint/event observation of committed canonical truth
          -> S223 versioned API + dedicated runner/CLI
            -> S224 Founder runtime control/inspection workspace
              -> S225 hardening
                -> S226 Demo v7 E2E + Founder runtime acceptance
```

There is exactly **one execution path**. M35 requests the existing M34 Step;
it never calculates or authors execution truth directly.

## Final Authority Boundary

### M31–M34 remain canonical

- M31 ledger events/postings and deterministic replay remain financial/account
  authority.
- M32 calendar/session/event/replay/checkpoint remain market-time and cursor
  authority.
- M33 Signal/Intent/Risk records remain immutable upstream strategy-to-risk
  evidence.
- M34 Order/Attempt/Fill/SettlementLink plus history-derived Order state remain
  execution authority.
- M35 may observe and orchestrate those authorities. It may not repair, replace,
  rebase, rewind, or reinterpret them.

### PaperRuntime

A v1 `PaperRuntime` is durable operational orchestration authority only.

It binds immutably to one exact existing M34 Order ID + digest, the Order's
account/replay/trading-session identities, one stable logical actor, and one
runtime policy ID/version.

A runtime does not create or replace the M34 Order. One runtime is bound to one
exact M34 Order. Automatic creation of later M33 Decisions or M34 Orders is not
part of M35.

### Desired and observed lifecycle

Observed lifecycle:

```text
ready
running
stopped
completed
blocked
```

Desired lifecycle:

```text
running
stopped
```

A newly created runtime is `desired=stopped`, `observed=ready`.

- Start records durable desired-running intent only; HTTP does not execute a
  Step.
- Stop is cooperative. It prevents the next uncommitted Step after observation,
  but cannot cancel or roll back an M34 Step already inside its atomic
  transaction.
- Resume from settled stopped records desired-running intent only. External
  runner execution is still required for continuation.
- HTTP/Web Recover records `recover_requested` intent only. It does not claim,
  take over, create Work, catch up a checkpoint, or invoke M34.
- Active recovery remains the dedicated process path:
  `run-paper-runtime -> S222 recovery -> S221 runner`.
- `completed` and `blocked` are terminal for automatic continuation.

## Claim, Lease, Heartbeat, and Fencing

M35 ownership is database-backed and one-winner.

- Only one unexpired owner/fence may own a runtime.
- First acquisition and each later acquisition/takeover advance the monotonic
  fencing token according to the accepted claim model.
- Foreign active ownership fails explicitly.
- Renew/release/pre-Step/post-Step operations require the exact current
  `owner_id + fencing_token` and an active lease.
- An old fenced worker may finish an already-entered M34 Step because M34 owns
  that atomic transaction, but it may not write current-owner M35 observation or
  begin the next Step.
- Routine heartbeat advances mutable lease state and does not append an
  unbounded immutable audit row.
- Wall-clock lease time is operational time only; it never becomes M32 market
  time or execution pricing/fill authority.

## Durable Work Identity

There is at most one `PaperRuntimeWork` for one runtime and one expected M34
execution version.

Each Work permanently fixes:

```text
runtime_id
execution_order_id + digest
expected_execution_version
stable M34 Step idempotency key
stable runtime logical actor
```

Retry, process restart, stale-lease takeover, or ambiguous failure for the same
logical iteration must reuse the exact same M34 key/actor/version.

The transient worker/owner identity is not the M34 actor.

The accepted S222 ambiguity remains valid: a pending Work may coexist with one
canonical M34 Attempt for the same version while the Work-key M34 receipt is
absent. Recovery retries the same M34 identity and lets M34 converge to the
canonical Attempt; this is not automatically corruption.

## Runner Transaction Boundary

The delivered runner preserves three phases:

1. M35 transaction validates desired state, owner/fence/lease and canonical
   readiness, then creates or loads exact Work;
2. that M35 transaction commits and closes;
3. the exact existing `PaperExecutionApplicationService.step_order(...)` runs
   in its own established atomic M34 transaction;
4. M35 opens a new transaction to revalidate ownership/fence and observe the
   committed canonical result.

No M35 transaction wraps M34 Step.

M35 never directly consumes an M32 event, derives a Fill, posts M31 settlement,
or mutates the M32 cursor.

## Checkpoint and Audit Authority

`PaperRuntimeCheckpoint` and runtime events are operational evidence only.
Canonical progression remains:

```text
M34 history -> execution progression
M32 replay/checkpoint -> market progression
M31 ledger -> financial progression
```

A missing M35 observation may be caught up from coherent canonical authority.
Contradictory canonical authority is not repaired.

Meaningful claim/control/work/completion/block events are durable audit evidence.
Routine heartbeat state is not an immutable audit stream.

## Recovery and Crash Windows

M35 explicitly closes the accepted recovery windows:

- **A — crash before Work creation:** reconstruct authority and create the normal
  next Work.
- **B — Work committed before Step:** retry the same Work identity.
- **C — ambiguous Step outcome:** retry the same M34 command identity.
- **D — Step committed before M35 observation:** observe/catch up that committed
  Step before any next Step.
- **E — lease expires while old worker is inside Step:** the higher-fence owner
  converges on the same Work/M34 identity; the old fence cannot observe or
  continue.
- **F — contradictory/corrupt authority:** fail closed and block where safely
  recordable; no automatic repair.

Allowed reconciliation outcomes remain:

1. pending Work with no canonical Step -> retry same M34 identity;
2. coherent canonical Step with missing M35 observation -> catch up operational
   observation;
3. terminal M34 Order -> runtime completed;
4. legitimate later M31/M32 live divergence -> historical inspection remains
   valid while new continuation fails stale/blocking as defined.

Cross-wired IDs/digests, impossible version/cursor relationships, corrupt
receipts, impossible Fill/settlement relationships, and inherited M31–M34
corruption remain fail closed.

## Persistence and Migration

M35 added the linear migration:

```text
0011_paper_execution
  -> 0012_durable_paper_runtime
```

The M35 persistence layer includes:

- `paper_runtimes`;
- `paper_runtime_work`;
- `paper_runtime_checkpoints`;
- `paper_runtime_events`; and
- `paper_runtime_command_receipts`.

The schema preserves restrictive relationships and append-only/immutable
operational evidence where required. Persistence stores/restores M35 authority;
it does not become M31–M34 authority.

## Transport and Founder Surfaces

M35 delivered exactly twelve authenticated `/api/v1/paper-runtimes` operations:

1. create runtime;
2. list runtimes;
3. runtime detail;
4. start;
5. stop;
6. resume;
7. recover request;
8. health;
9. reconciliation;
10. audit;
11. Work inspection;
12. checkpoint inspection.

No HTTP endpoint hosts the durable runner.

`run-paper-runtime` is the supported dedicated process/CLI surface. It composes
S222 recovery before the S221 runner and uses the same application authority as
the product.

The bilingual `/paper-runtimes` Founder workspace is control + inspection only.
The browser does not claim/renew/release/take over leases, generate fences, run
M34 Step, create Work/checkpoints, mutate M31/M32, or infer that an accepted
control command proves execution progressed.

## Sprint Reconciliation

M35 delivered through the approved S217–S227 sequence:

| Sprint | Delivery | Final status |
|---:|---|---|
| S217 | Plan Milestone 35: Durable Paper Runtime and Recovery — Issue #429 | Complete |
| S218 | Runtime contracts, persistence, receipts, migration `0012` — Issue #430 / PR #431 | Complete |
| S219 | Claims, leases, heartbeat, fencing, control idempotency — Issue #432 / PR #433 | Complete |
| S220 | Lifecycle Create/Start/Stop/Resume/Recover request services — Issue #434 / PR #435 | Complete |
| S221 | Durable runner loop over exact M34 one-event Step — Issue #436 / PR #437 | Complete |
| S222 | Crash/restart/stale-lease recovery and reconciliation — Issue #438 / PR #439 | Complete |
| S223 | Twelve runtime API operations, errors/audit, generated contracts, dedicated CLI — Issue #440 / PR #441 | Complete |
| S224 | Founder Durable Paper Runtime Web Workspace — Issue #442 / PR #443 | Complete |
| S225 | Concurrency/idempotency/recovery/observability/isolation hardening — Issue #444 / PR #445 | Complete |
| S226 | Demo v7 deterministic E2E and Founder runtime acceptance — Issue #446 / PR #447 | Complete |
| S227 | Milestone 35 closeout and M36 handoff — Issue #448 | Complete after merge |

## S225 Hardening Evidence

S225 proved, among other things:

- expired-takeover one-winner fencing;
- stale-owner refusal before/after Step;
- takeover while an old worker is inside the exact M34 Step seam;
- cooperative Stop during an entered Step;
- concurrent exact control-command convergence and changed-content conflicts;
- bounded heartbeat behavior without heartbeat audit spam;
- real SQLite M35 write contention;
- direct Work/Attempt/checkpoint/Fill/SettlementLink/M31/M32 cardinalities;
- deterministic bounded pagination with strict resource-anchor validation;
- the accepted ambiguous Work + Attempt + missing Work-key receipt recovery;
- Standard/Demo cross-wire refusal and isolation.

## Demo v7 and Founder Acceptance

S226 upgraded the isolated Demo workspace to v7 and added one deterministic M35
authority chain built through the merged M31–M35 application paths.

Founder acceptance passed with this exact journey:

```text
fresh runtime: stopped/ready, unowned, fence 0, Work 0, checkpoint 0
Start: control-only
HTTP Recover request: control-only
worker A: fence 1, one no-fill Work/Attempt/checkpoint, M32 4 -> 5
worker B: fence 2, second Work/Attempt/checkpoint,
          exactly one Fill + SettlementLink + M31 execution_fill_posted,
          M32 5 -> 6
Stop + worker C: fence 3, stopped/stopped, runner not run,
                 no third Work/effect
Resume: control-only
worker D: fence 4, third boundary-rejected Work/Attempt/checkpoint,
          runtime completed, no second Fill/settlement/posting,
          M32 remains 6
completed re-entry: no fourth Work/Attempt/completion or new M31/M32 effect
Demo restart: durable authority preserved
return to Standard: Demo M35 authority absent and Standard unchanged
```

This proves durable identity continuity, restart-safe recovery, monotonic fencing,
cooperative lifecycle control, exact cardinality, one execution path, persistence,
and Standard/Demo isolation without making browser or Demo state authoritative.

## Known Limitations and Non-Goals

M35 intentionally does not add:

- automatic generation of future M33 Signals/Intents/Decisions or M34 Orders;
- multi-day session/day rollover;
- overnight scheduling or closed-market operating policy;
- multi-account allocation;
- multiple concurrent working Orders over one shared market stream beyond the
  existing M34 boundary;
- reservation/capital locking for unfilled quantity;
- distributed queue, Redis, cluster scheduler, or multi-host coordination;
- broker/QMT/MiniQMT/private-edge/live/real-money integration;
- public SaaS/multi-tenant runtime behavior; or
- automatic corruption repair.

## M36 Handoff

The exact next milestone after this closeout is:

```text
Milestone 36 — Multi-day Paper Operations and Acceptance
```

The expected next Sprint is the CTO-owned architecture/planning gate:

```text
Sprint 228 — Plan Milestone 36: Multi-day Paper Operations and Acceptance
```

S228 must plan before implementation:

- multi-day durable identity and operating unit;
- session/day rollover and closed-market/overnight semantics;
- how M32 market-time authority continues across trading days;
- EOD checkpoints and cross-day restart/recovery;
- cross-day M31 freshness/reconciliation;
- whether and how new M33/M34 authority is created for later decisions/orders;
- whether one M35 runtime remains one Order or a higher-level operation composes
  multiple runtimes;
- operator lifecycle and scheduling/process model;
- cross-day concurrency/idempotency/reconciliation;
- API/Web/Demo evolution and migration needs;
- Standard/Demo isolation;
- multi-account/shared-stream/reservation boundaries;
- whether Demo v8 is required; and
- the detailed M36 sprint sequence.

M36 must preserve the M31–M35 authority chain. Sprint 227 does not implement any
M36 behavior.

## Closeout State After Sprint 227 Merge

```text
Milestones 1–35 — Complete
S217–S227 — Complete
M36 — next milestone: Multi-day Paper Operations and Acceptance
S228 — CTO architecture/planning gate
Demo — v7
migration head — 0012_durable_paper_runtime
```
