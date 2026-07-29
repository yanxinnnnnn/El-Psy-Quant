# Strategy-to-Order and Pre-Trade Risk Architecture

## Status and Authority

Milestone 33 is **In Progress** through the approved Sprint 197–206 sequence.
GitHub Issue #389 is the authoritative M33 architecture and planning source.
GitHub Issue #390 is the authoritative Sprint 198 implementation specification.

The frozen authority chain is:

```text
M32 market/session/event/replay truth
  -> immutable StrategySignal recommendation evidence
  -> M31-account-bound OrderIntent request
  -> immutable PreTradeRiskDecision evidence
  -> future M34 execution candidate
```

Sprint 198 implements only the first pure contract layer. It does not evaluate a
strategy, derive an order, perform risk checks, persist M33 state, expose product
routes, or execute anything.

## Preserved Earlier Authorities

M31 remains unchanged:

```text
immutable ledger events/postings = financial authority
deterministic ledger replay = Paper Account state authority
projection/snapshot/reconciliation = derived evidence/cache
API/Web/Demo = presentation and verification only
```

M32 remains unchanged:

```text
TradingCalendar / TradingSession = calendar/session authority
MarketDataEvent = canonical market-state event authority
MarketDataReplayEngine = ordering, cursor, lifecycle, and progression authority
persistence = store and restore existing authority only
API/Web/Demo = presentation and verification only
```

M33 can reference exact M31 quantities and exact M32 provenance. It cannot
reinterpret or mutate either domain.

## Existing Contracts That Are Not M33 Authority

- `el_psy_quant.strategies.Strategy` remains a research interface returning
  pandas research results. A DataFrame row is not durable Strategy Signal
  authority.
- `el_psy_quant.execution.OrderIntent` remains the float-valued M15 backtest
  execution assumption. It is not the future account-bound M33 intent.
- `PaperOrderRecord`, `PaperOrderLedger`, `PaperFill`, and related Paper
  artifacts remain legacy Paper evidence. They are not M33 intent, risk, fill,
  reservation, or account authority.

These existing types are not renamed, wrapped, subclassed, or promoted by M33.

## Sprint 198 Pure Contract Boundary

The separate `el_psy_quant.strategy_order` package introduces:

```text
StrategyRuntimeReference
StrategySignalMarketReference
EvaluateStrategySignalCommand
StrategySignal
StrategySignalReference
```

Every contract is immutable, versioned, deterministic, explicitly exported to
strict JSON primitives, and protected by a trusted construction boundary.

### Runtime reference

The only supported runtime configuration is:

```text
strategy_name = moving_average_crossover
strategy_version = v1
adapter_version = v1
runtime_sizing_semantics = target_position_quantity
```

Its exact parameters are `fast_window`, `slow_window`, and the positive M31
`PaperQuantity` `target_position_quantity`. Runtime construction does not
resolve or run the research strategy.

### Market reference

The trusted market-reference factory accepts concrete `TradingCalendar`,
`TradingSession`, `ReplaySession`/`ReplayCursor`, and `MarketDataEvent` values.
It binds the consumed cursor to the exact current event and preserves calendar,
session, replay, stream, cursor, event, time, and instrument anchors.

The reference does not copy event payload, source, event type, or replay status.
It does not reorder events, interpret price, or advance replay.

### Evaluation command

The command contains only the runtime reference, market reference, bounded
idempotency key, actor, schema version, and deterministic command digest.
Construction has no side effect and produces no signal.

### Strategy Signal

A Strategy Signal is immutable evidence that one exact runtime evaluation
recommended one exact target from one exact M32 prefix. The recommendation is
advisory and non-executing.

Version 1 supports only `target_position_quantity`. The target must be either
canonical zero or the configured positive runtime target. Signal identity is:

```text
signal_id = sig_<signal_digest>
```

The digest covers the complete runtime reference, complete market reference,
target semantic, and exact target quantity. It excludes actor, command
idempotency key, command digest, `created_at`, ID, and the digest itself.

`created_at` is UTC-normalized server audit metadata. Market signal time remains
the exact referenced M32 event time.

### Compact signal reference

The compact reference contains only schema version, signal ID, and signal
digest. It can be created only from a complete valid Strategy Signal and copies
no parameters, market content, target, account, order, risk, or execution data.

## Canonicalization

All M33 digests use lowercase SHA-256 over UTF-8 canonical JSON:

```python
json.dumps(
    payload,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False,
    allow_nan=False,
)
```

Quantities export as canonical fixed-point strings and timestamps export as
canonical UTC ISO 8601 strings. Exported payloads contain JSON primitives only.

## Planned M33 Sequence

```text
S197 architecture and planning — Complete
S198 runtime reference and signal contracts — implementation in progress
S199 deterministic signal evaluation — Planned
S200 account-bound Order Intent — Planned
S201 pre-trade risk decision/evidence — Planned
S202 persistence, migration, concurrency, and application service — Planned
S203 versioned API, errors, audit, and generated contracts — Planned
S204 bilingual Founder workspace — Planned
S205 Demo v5, recovery, and acceptance hardening — Planned
S206 M33 closeout and M34 handoff — Planned
```

The migration head remains `0009_market_time_runtime` until S202.

## Execution Boundary

M33 owns no accepted order, reservation, fill, execution price, fee, ledger
posting, worker, scheduler, broker, QMT, MiniQMT, live, or real-money behavior.
M34 remains the first milestone allowed to own execution, fills, and
fill-caused Paper Account mutation.
