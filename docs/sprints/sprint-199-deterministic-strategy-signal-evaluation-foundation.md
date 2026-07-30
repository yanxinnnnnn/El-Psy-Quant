# Sprint 199 — Deterministic Strategy Signal Evaluation Foundation

## Status

**Complete.**

GitHub Issue #392 is the authoritative Sprint implementation specification.
GitHub Issue #389 remains the authoritative M33 architecture source.

## Objective

Add the first pure deterministic evaluation path from one complete Sprint 198
command and exact concrete M32 replay authority to one immutable Sprint 198
Strategy Signal. No account, intent, risk, persistence, product, or execution
authority is introduced.

## Closed Runtime Adapter

`StrategySignalRuntimeAdapter` exposes only the exact strategy name, strategy
version, adapter version, and a pure target-evaluation operation. The resolver
supports exactly:

```text
moving_average_crossover / v1 / v1
```

Resolution validates the complete runtime reference and has no plugin registry,
dynamic import, entry point, filesystem discovery, environment selection, or
side effect.

## Exact M32 Binding

`evaluate_strategy_signal(...)` accepts a complete evaluation command, concrete
`TradingCalendar`, `TradingSession`, `MarketDataReplayEngine`, and explicit
timezone-aware audit timestamp. It reconstructs and validates an equivalent
replay engine from exact canonical events and cursor, identifies the current
event at `events[cursor.position - 1]`, and recreates the Sprint 198 market
reference. Every calendar, session, replay, stream, cursor, current-event, time,
instrument, and digest anchor must match the command exactly.

Replay lifecycle-only pause/resume does not change Signal identity. A stale or
mismatched authority fails closed. Evaluation neither advances nor mutates the
source replay engine and supplies only the consumed prefix to the adapter.

## Price, History, and Research Rules

The v1 adapter preserves M32 prefix order and selects only same-instrument
`event_type == "trade"` events. Each selected event must contain one top-level
JSON integer or float `price` that converts without overflow to a finite,
strictly positive research value. Invalid selected events are never skipped;
other instruments and non-trade events are ignored.

All valid selected trades in the consumed prefix contribute, including earlier
sessions. At least `slow_window + 1` observations are required. Event IDs form
the deterministic pandas index, avoiding duplicated-timestamp ordering.

The adapter resolves and runs the existing research
`moving_average_crossover` Strategy with only `fast_window` and `slow_window`.
It requires an exactly aligned result with a complete `position` column holding
only long-only states `0` or `1`. Pandas input and research output, including
moving averages, returns, costs, and equity, are ephemeral calculation details
and never become Signal authority.

## Target and Signal Mapping

```text
latest position 0 -> PaperQuantity.parse("0")
latest position 1 -> configured target_position_quantity
```

The trusted Sprint 198 internal constructor produces the immutable Signal.
`created_at` is explicit UTC-normalized audit metadata and remains excluded from
Signal identity. Actor, command idempotency key, and command digest also remain
command facts rather than Signal identity inputs.

## Verification

Focused Sprint 199 tests cover exact adapter resolution, replay reconstruction,
staleness, lifecycle independence, non-mutation, future-event exclusion, mixed
events and instruments, M32 total order, price validation, history sufficiency,
prior-session history, research seam reuse and tamper rejection, target mapping,
and Signal identity determinism.

Before completion Codex runs:

```text
uv run python scripts/check.py
```

Sprint 199 adds no migration. The migration head remains:

```text
0009_market_time_runtime
```

No Docker build, pull, Compose/container startup, container smoke, volume
removal, Demo reset, or Standard/Demo runtime acceptance is performed.

## Explicit Non-Goals

Sprint 199 adds no Paper Account read, account-bound Order Intent, no-action
contract, side or delta, pre-trade risk, persistence, migration, application
service, API/OpenAPI/generated contract, Web/localization, Demo, replay
progression, reservation, execution order, fill, fee, ledger posting, worker,
scheduler, broker, QMT, MiniQMT, live, or real-money behavior.

Sprint 200 is the current implementation sprint. S201–S206 remain Planned. M34
remains the first execution, fill, and fill-caused account-mutation milestone.
