# Milestone 35 — Durable Paper Runtime and Recovery

## Status

**Complete after Sprint 227 closeout merge.**

Architecture/planning authority: GitHub Issue #429.
Closeout authority: GitHub Issue #448.

Milestone 35 spans S217–S227.

## Goal

Add durable operational orchestration around the already-merged M34 one-event
Paper Execution Step so one exact existing `PaperExecutionOrder` can progress
safely across process interruption, restart, stale ownership, explicit Founder
control, and recovery without creating a second execution path.

## Final Authority Boundary

M35 owns operational runtime orchestration only:

- durable `PaperRuntime` identity;
- durable logical `PaperRuntimeWork` identity;
- desired/observed lifecycle;
- claim/lease/heartbeat/fencing state;
- the right to request the next existing M34 Step;
- operational checkpoint/audit evidence;
- restart/stale-owner recovery orchestration;
- operational reconciliation and bounded inspection.

M35 does not own or redefine:

- M31 ledger/account authority;
- M32 event/replay/cursor authority;
- M33 Signal/Intent/Risk authority;
- M34 Order/Attempt/Fill/Settlement execution authority;
- execution price, slippage, cost, fill, or execution-time risk semantics;
- M34 command idempotency identity;
- canonical corruption repair.

The canonical chain remains:

```text
M31 + M32 + M33
  -> M34 PaperExecutionOrder
    -> M35 decides when the next Step may be requested
      -> exact existing M34 one-event Step
        -> Attempt
          -> optional Fill
            -> exact M31 settlement
        -> exact M32 progression
      -> M35 observes committed canonical truth
```

## Delivered Runtime Model

One v1 runtime binds immutably to one exact M34 Order ID + digest, its account,
replay and trading session, one stable runtime logical actor, and one runtime
policy ID/version.

Observed lifecycle:

```text
ready | running | stopped | completed | blocked
```

Desired lifecycle:

```text
running | stopped
```

New runtimes begin `stopped/ready`.

- Start records desired-running intent only.
- Stop is cooperative and cannot cancel an already-entered M34 Step.
- Resume records desired-running intent after stopped reconciliation; the runner
  is still required for execution.
- HTTP/Web Recover records recovery request intent only.
- Active recovery belongs to the dedicated process path.
- `completed` and `blocked` are terminal for automatic continuation.

## Ownership and Durable Work

Runtime ownership is database-backed with one-winner claims, leases, heartbeat,
and monotonic fencing.

The runner validates exact active owner/fence before each new Step and again
before post-Step M35 observation. A fenced worker may finish an already-entered
M34 transaction but cannot observe as current owner or start another Step.

Each logical Work is unique for one runtime and expected execution version and
permanently fixes the stable M34 Step idempotency key, stable runtime logical
actor, exact Order reference, and expected version. Retry/restart/takeover reuse
that same identity.

## Runner and Recovery

The accepted process composition is:

```text
run-paper-runtime
  -> S222 recovery
  -> S221 runner
  -> exact existing M34 PaperExecutionApplicationService.step_order(...)
```

M35 transaction boundaries remain separated from M34 Step:

```text
M35 pre-Step transaction -> commit/close
M34 Step transaction
M35 post-Step observation transaction
```

Recovery covers the frozen crash windows A–F: before Work, after Work/before
Step, ambiguous Step, committed Step before observation, lease expiry while an
old worker is inside Step, and corruption/fail-closed handling.

A coherent missing M35 observation may be caught up. Canonical M31–M34 authority
is never repaired or rewritten by recovery.

## Persistence, API, CLI, and Web

Migration head:

```text
0012_durable_paper_runtime
```

M35 storage includes runtime, Work, checkpoint, runtime event, and M35 control
receipt authority.

S223 exposes exactly twelve authenticated runtime HTTP operations for lifecycle
and bounded inspection. No HTTP operation hosts the runner.

`run-paper-runtime` is the supported dedicated runner process/CLI.

The bilingual `/paper-runtimes` workspace is control + inspection only. It does
not own leases/fences, execute M34 Step, create Work/checkpoints, or mutate
M31/M32.

## Sprint Sequence

| Sprint | Delivery | Status |
|---:|---|---|
| S217 | Plan M35 architecture — Issue #429 | Complete |
| S218 | Contracts, persistence, migration `0012` — #430 / PR #431 | Complete |
| S219 | Claims, leases, heartbeat, fencing, idempotency — #432 / PR #433 | Complete |
| S220 | Runtime lifecycle services — #434 / PR #435 | Complete |
| S221 | Durable runner over existing M34 Step — #436 / PR #437 | Complete |
| S222 | Crash/restart/stale-lease recovery — #438 / PR #439 | Complete |
| S223 | Runtime API, CLI, audit, generated contracts — #440 / PR #441 | Complete |
| S224 | Founder Durable Paper Runtime Web Workspace — #442 / PR #443 | Complete |
| S225 | Concurrency/recovery/observability/isolation hardening — #444 / PR #445 | Complete |
| S226 | Demo v7 and E2E/Founder acceptance — #446 / PR #447 | Complete |
| S227 | M35 closeout and M36 handoff — #448 | Complete after merge |

## Final Accepted Baseline

- reviewed S226 head: `9f57f030a7847a7176a09265a56be16faae2362e`;
- reviewed merge ref: `5741c33a49c454bed19169a9fba420c506edd3d4`;
- merged S226 `main`: `6af41c166d4106c89c0189d3688773cde7d2cb77`;
- GitHub Actions run: `34182537933`;
- quality job: `101924349050`;
- Python: `3396 passed`;
- Web: `501 passed / 51 files`;
- migration head: `0012_durable_paper_runtime`;
- Demo: v7;
- Founder fresh Docker/browser runtime acceptance: PASS.

## Non-Goals / Known Limitations

M35 intentionally does not provide automatic future M33/M34 creation, multi-day
rollover, overnight scheduling, multi-account allocation, unfilled-quantity
reservation, distributed queue/scheduler infrastructure, broker/live integration,
or automatic corruption repair.

## Next Milestone

After S227 merge:

```text
Milestone 36 — Multi-day Paper Operations and Acceptance
Sprint 228 — expected CTO architecture/planning gate
```

M36 must preserve the M31–M35 authority chain and explicitly plan multi-day
identity, day/session rollover, cross-day market/account continuity, scheduling,
new decision/order generation boundaries, recovery, reconciliation, API/Web/Demo
evolution, migration needs, and acceptance before implementation begins.
