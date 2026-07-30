# Sprint 198 — Strategy Runtime Reference and Signal Contract Foundation

## Status

**Complete.**

GitHub Issue #390 is the authoritative Sprint implementation specification.
GitHub Issue #389 remains the authoritative M33 architecture source.

## Objective

Create the first pure M33 domain-contract layer without performing strategy
evaluation, account access, order derivation, risk evaluation, persistence, API,
Web, Demo, replay mutation, or execution.

## Delivered Contracts

The new `el_psy_quant.strategy_order` package provides:

```text
StrategyRuntimeReference
create_moving_average_crossover_runtime_reference(...)

StrategySignalMarketReference
create_strategy_signal_market_reference(...)

EvaluateStrategySignalCommand
create_evaluate_strategy_signal_command(...)

StrategySignal

StrategySignalReference
create_strategy_signal_reference(...)
```

The package root exports only supported constants, immutable public types, safe
public factories, and validators. The trusted evaluator-to-signal constructor
remains internal to the signal module and is reused by Sprint 199.

## Runtime Boundary

The closed v1 runtime is:

```text
moving_average_crossover / strategy v1 / adapter v1
runtime_sizing_semantics = target_position_quantity
parameters = fast_window, slow_window, target_position_quantity
```

Windows are positive concrete integers with `fast_window < slow_window`.
Configured target quantity is an exact positive M31 `PaperQuantity`. Runtime
construction never resolves or executes the research strategy.

## M32 Binding

The market-reference factory requires concrete valid M32 calendar, trading
session, replay session/cursor, and current event objects. It verifies:

- a positive consumed cursor position;
- paired last-event ID and current-event time;
- exact cursor/current-event ID and time equality;
- `signal_event_id == last_event_id`;
- inclusive trading-session boundaries; and
- exact event-derived UTC time and instrument.

It copies no payload, source, event type, or replay status and does not mutate or
advance replay state.

## Signal and Identity Boundary

The evaluation command contains only exact runtime and market references,
bounded actor/idempotency values, and a deterministic command digest. Command
construction produces no Signal.

The internal trusted signal boundary accepts only a complete command, exact
`PaperQuantity` evaluation result, and timezone-aware audit timestamp. Version 1
accepts target zero or the configured positive runtime target only.

Signal digest and `sig_<digest>` identity cover the runtime reference, market
reference, target semantic, and exact target quantity. Actor, idempotency key,
command digest, and `created_at` do not affect signal identity.

The compact signal reference contains only schema version, signal ID, and signal
digest and can be created only from a complete valid Signal.

## Canonical and Immutability Guarantees

- lowercase SHA-256 over the approved canonical UTF-8 JSON form;
- canonical fixed-point quantity strings;
- canonical UTC ISO 8601 timestamps;
- strict JSON-compatible primitive exports;
- immutable, hash/equality-stable authority objects;
- blocked arbitrary direct construction; and
- isolated exports and defensive snapshots.

## Verification

Focused Sprint 198 tests cover runtime validation, closed vocabularies, digest
stability/sensitivity, exact M32 binding, mismatch and tamper rejection, replay
non-mutation, command purity, target restrictions, identity independence,
direct-construction protection, compact references, strict JSON export, and
caller-mutation isolation.

Before completion Codex runs:

```text
uv run python scripts/check.py
```

Sprint 198 adds no migration. The migration head remains:

```text
0009_market_time_runtime
```

No Docker build, pull, Compose/container startup, container smoke, volume
removal, Demo reset, or Standard/Demo runtime acceptance is performed.

## Explicit Non-Goals

Sprint 199 adds only strategy evaluation, versioned trade-price extraction, and
ephemeral pandas construction over the Sprint 198 contracts. S200–S206 retain
Order Intent/no-action derivation, pre-trade risk, persistence, `0010` migration,
application services, API/OpenAPI/generated contracts, Web, localization, Demo
v5, recovery hardening, and M33 closeout.

M34 retains execution orders, reservations, fills, execution pricing, fees,
ledger posting, and account mutation. Broker, QMT, MiniQMT, live, and real-money
behavior remain excluded.
