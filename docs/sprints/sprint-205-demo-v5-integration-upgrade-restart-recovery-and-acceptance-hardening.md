# Sprint 205 — Demo v5, Integration, Upgrade, Restart, Recovery, and Acceptance Hardening

## Authority and status

GitHub Issue #404 is the authoritative Sprint 205 specification. Issue #389
remains the M33 architecture authority. Sprint 205 is **Complete** after PR #405
merged at `c5d1e0d1529517929784f3f48d4ce66916d994e9`.

## Delivered boundary

Demo source, dataset, and descriptor schema version 5 preserve the existing
isolated installer and add discovery metadata for one complete deterministic
journey:

```text
M31 active Paper Account at exact head
  + M32 paused replay at exact trade prefix
  -> StrategySignal
  -> buy OrderIntent
  -> allow PreTradeRiskDecision
  -> maximum_order_quantity_exceeded reject PreTradeRiskDecision
```

The installer creates all M33 records and receipts only by calling the merged
`StrategyOrderApplicationService`. It contains no SQL/ORM M33 payload insertion
and makes no HTTP call to the product. Descriptor metadata is non-authoritative
and cannot calculate side, quantity, price, notional, or risk.

## Verification and recovery

Read-only Demo verification strictly reopens Signal, Intent, both Decisions,
bounded lists, and all receipt relationships through production repositories
and application services. It never creates missing evidence, repairs a row,
advances replay, or changes Paper Account state.

Temporary SQLite coverage proves fresh install/reinstall convergence, exact
replay after service disposal/reopen, idempotency conflict, concurrent
alternate-key convergence on one Intent, same-command creation convergence on
one previously absent Signal authority, stale M31/M32 rejection with no partial
receipt, deliberate receipt corruption with no repair, and separate
Standard/Demo storage. Existing migration hardening proves populated
`0009_market_time_runtime -> 0010_strategy_order_risk` preservation and no
migration-time seed. The single migration head remains
`0010_strategy_order_risk`.

If strict verification fails, preserve the failed workspace and bounded logs.
Restore only a complete reviewed known-good workspace, or use the documented
Founder-owned reset for disposable Demo storage. Do not edit individual rows,
delete evidence, rerun commands to make verification green, or stamp Alembic.

## Founder-owned runtime acceptance

The Founder owns Standard and Demo Docker build/start/smoke, disposable Demo
reset and repeat-identity checks, preserved-volume upgrade/restart checks,
corruption/recovery acceptance, return-to-Standard isolation, and merge. Codex
did not run Docker, Compose, container smoke, volume removal, Demo reset, or
Standard/Demo runtime acceptance during S205.

The final reviewed CI baseline was Python `3061 passed` and Web
`449 passed / 47 files`, with Ruff/import/CLI/messages/contracts/lint/typecheck/
production build passing and migration head `0010_strategy_order_risk`.

## Non-goals

Sprint 205 adds no migration, M33 operation, mutable status, reservation,
execution order, fill, fee, ledger mutation, replay progression, worker,
scheduler, broker/QMT/MiniQMT integration, live behavior, or proxy change.
Risk allow remains evidence only. M34 remains the first execution milestone.
Sprint 206 owns only the documentation closeout and M34 handoff.
