# Strategy-to-Order and Pre-Trade Risk Architecture

## Status and Authority

Milestone 33 is **Complete** through the approved Sprint 197–206 sequence.
GitHub Issue #389 remains the authoritative M33 architecture and planning source
for the delivered boundary. The canonical closeout is
`docs/closeouts/milestone-033-strategy-to-order-and-pre-trade-risk-pipeline-closeout.md`.

The frozen authority chain is:

```text
M32 market/session/event/replay truth
  -> immutable StrategySignal recommendation evidence
  -> M31-account-bound OrderIntent request
  -> immutable PreTradeRiskDecision evidence
  -> future M34 execution candidate
```

Sprints 197–205 delivered the architecture, contracts, evaluation, persistence,
API, Web, and Demo/recovery evidence. Sprint 206 closes the milestone through
documentation only and freezes the M34 handoff. M33 adds no reservation,
execution, fill, replay progression, or M31/M32 mutation authority.

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
  execution assumption. It is not the account-bound M33 intent.
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

## Sprint 199 Deterministic Evaluation Boundary

`StrategySignalRuntimeAdapter` is the explicit closed runtime boundary. Exact
resolution supports only:

```text
moving_average_crossover / strategy v1 / adapter v1
```

There is no registry mutation, alias, dynamic import, entry point, filesystem
discovery, environment selection, or caller-supplied adapter.

`evaluate_strategy_signal(...)` validates the complete Sprint 198 command and
reconstructs an equivalent `MarketDataReplayEngine` from its exact canonical
events and cursor. It recreates the market reference from the concrete calendar,
session, replay session, and event at `cursor.position - 1`; every command anchor
must match exactly. Replay lifecycle alone is excluded, but a changed stream,
cursor, event, time, calendar version, session, or instrument fails closed. The
source replay engine is never advanced or mutated.

The adapter receives only `events[:cursor.position]`. In existing M32 order it
selects same-instrument `event_type == "trade"` events and requires one top-level
concrete JSON integer or float `payload.price` that converts to a finite,
strictly positive research value. Invalid selected prices fail the whole
evaluation; other instruments and non-trade events remain ignored. History is
all selected trades in the consumed prefix, including earlier sessions, and
requires at least `slow_window + 1` observations.

The adapter resolves the existing research
`Strategy("moving_average_crossover")`, passes only a deterministic `Close`
DataFrame and `fast_window`/`slow_window`, and strictly validates row count,
index alignment, and a complete long-only `position` column. The DataFrame,
moving averages, returns, costs, and other research results remain ephemeral
calculation details rather than Signal authority. Latest position `0` maps to
canonical zero; latest position `1` maps to the configured exact target
quantity. The trusted Sprint 198 constructor then creates the immutable Signal.

## Sprint 200 Account-Bound Intent Boundary

Sprint 200 adds a narrow public M31 state-validation seam and these immutable
pure M33 contracts:

```text
OrderIntentAccountReference
DeriveOrderIntentCommand
OrderIntent
OrderIntentNoAction
OrderIntentReference
```

The account reference is copied evidence from one exact validated active M31
ledger state. It binds account identity, currency, lifecycle, head version,
event and chain digest, cash, available cash, the Signal instrument, and its
exact current position quantity. A missing exact instrument position is
canonical zero. It does not become balance, position, account, ledger,
projection, reservation, or repair authority.

The command binds the complete compact Signal reference, complete account
reference, exact `target_position_quantity_delta_v1` policy, bounded
idempotency key, actor, and canonical command digest. Construction derives no
side or quantity and generates no timestamp.

Conversion recreates both references from the supplied concrete Signal and M31
state. Any changed Signal, account identity/lifecycle/head/event/chain,
cash/available-cash, position, instrument, or policy fails stale rather than
silently rebinding. Exact conversion is:

```text
target > current -> buy(target - current)
target < current -> sell(current - target)
target = current -> target_already_satisfied no-action
```

Arithmetic uses exact `PaperQuantity` decimal values without rounding. Intent
identity binds the complete Signal, market, account, target/current, derived
side/delta, and policy evidence. No-action identity binds the same applicable
authority plus its closed reason code. Command key, actor, command digest, and
`created_at` are audit facts excluded from either deterministic result identity,
so different audit commands over identical authority converge.

An Order Intent is only a risk-pending request. No-action evidence is not an
intent and cannot produce an intent reference or enter risk evaluation. Neither
result reserves, executes, advances replay, or mutates the Paper Account.

## Sprint 201 Pre-Trade Risk Evidence Boundary

Sprint 201 adds these immutable pure M33 contracts:

```text
PreTradeRiskPolicyReference
EvaluatePreTradeRiskCommand
PreTradeRiskPriceReference
PreTradeRiskRuleEvidence
PreTradeRiskInputSnapshot
PreTradeRiskDecision
```

The only policy is `long_only_cash_risk_v1`, with explicit optional exact
maximum quantity and notional limits and no hidden defaults. Its price policy is
`latest_trade_price_v1`. Evaluation searches backwards through only the exact
consumed replay prefix for the latest same-instrument `trade` event, records the
complete event digest and one-based stream position, and rejects an invalid
latest match rather than falling back to older data. The exact reference price
is risk-notional evidence only; it is not execution, fill, or valuation
authority.

Estimated notional is exact requested quantity multiplied by reference price,
without rounding. Every snapshot contains these four rule records in order:

```text
insufficient_position_quantity
maximum_order_quantity_exceeded
maximum_order_notional_exceeded
insufficient_available_cash
```

Non-applicable rules remain present, pass, and use null observed/threshold
values. An allow decision has no reasons. A reject decision contains all and
only failed applicable rules in the same order.

Evaluation validates the complete command, intent, M31 ledger state, calendar,
session, replay engine, cursor, current event, policy, and selected price. It
recreates the exact intent, account, and market references before calculating
evidence. Changed account head or replay cursor always fails stale, while
replay lifecycle-only changes with the same prefix remain identity-equivalent.
Invalid, missing, unsupported, tampered, stale, or unrepresentable input raises
a deterministic domain error and creates no decision; no path defaults to
allow.

Snapshot identity binds the complete current authority and evidence but excludes
command/audit facts. Decision identity binds the snapshot, outcome, and ordered
reasons. Different valid keys, actors, command digests, or audit timestamps over
identical authority converge on the same snapshot and decision identity. A
decision is immutable evidence only and cannot mutate an intent, reserve
cash/position, advance replay, execute, fill, or post to the ledger.

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

## Sprint 202 Durable Boundary

Migration `0010_strategy_order_risk` adds append-only Signal, Intent, Decision,
and scoped command-receipt tables. Canonical full payloads remain durable
authority; indexed relational columns support bounded lookup and must agree
exactly with reconstructed payload metadata. Duplicate-key, non-canonical,
malformed, incomplete, digest-mismatched, or cross-reference-mismatched rows
fail closed as corrupt authority.

Repository reads are by deterministic identity, unique digest, or bounded
cursor page. Application services use one `BEGIN IMMEDIATE` transaction to
verify exact M31 ledger replay/projection and M32 calendar/session/replay
authority, call the unchanged S198–S201 pure functions, and atomically store
the complete result plus one scoped command receipt. Identical concurrent
commands converge on one result; reuse of a key for a different command fails
as an idempotency conflict. No-action is durable receipt evidence and does not
create an Order Intent row.

## Sprint 203 API Boundary

Sprint 203 exposes exactly nine founder-authenticated `/api/v1` operations:
create/list/detail for Strategy Signals, Order Intents, and Pre-Trade Risk
Decisions, with Signal creation named `evaluate`. No-action evidence is returned
only by the Intent command and is not a list/detail resource.

Routes accept only runtime/policy selections, durable resource references,
expected M31/M32 anchors, actors, and idempotency keys. They construct the two
approved references and delegate all strategy output, target, delta, price,
notional, outcome, reason, identity, digest, and command provenance authority to
the unchanged S198–S202 chain.

Strict projections preserve canonical fixed-point strings and raw stable
authority values while omitting command idempotency keys and raw market event
payloads. Bounded repository reads use collection-specific integrity-checked
opaque keyset cursors. Stable sanitized errors distinguish not-found,
idempotency, stale authority, reconciliation, invalid selection, corrupt or
unavailable authority, incompatible schema, busy storage, and storage failure.
The existing server request ID is returned on commands and included with
bounded non-financial completion events. Canonical OpenAPI and generated
TypeScript are presentation contracts only.

## Sprint 204 Web Boundary

Sprint 204 adds exactly one top-level `/strategy-to-risk` Founder workspace.
The bilingual Web uses only generated S203 transport types and fail-closed
runtime validators while explicitly orchestrating Signal evaluation, Intent or
no-action derivation, and pre-trade Risk evaluation. It preserves selected
expected M31/M32 anchors until explicit Founder refresh or reselection, reuses a
step key only for an unchanged retry, and never refreshes stale authority and
retries automatically.

The Web renders raw identities, digests, codes, canonical decimals, timestamps,
the discriminated no-action result, and all four ordered Risk rule records
without recalculation or localization. It adds no domain, persistence, API,
OpenAPI, generated-contract, Demo, migration, Paper Account/replay mutation,
reservation, execution-order, fill, or broker authority.

## Sprint 205 Demo and Recovery Boundary

Demo v5 creates M33 authority only through the merged S202 application/domain/
repository path. It exposes deterministic discovery metadata for one non-zero
Signal, one buy Intent, one allow Decision, and one explicit quantity-limit
reject Decision while keeping the descriptor non-authoritative.

Read-only verification reopens strict M31/M32/M33 authority and command receipts
without command rerun, repair, replay advancement, or account mutation. Focused
integration evidence proves exact restart replay, idempotency conflict,
alternate-key convergence, a one-winner same-command creation race on previously
absent Signal authority, stale-anchor refusal, corruption/no-repair, populated
`0009 -> 0010` upgrade preservation, explicit post-upgrade Demo installation,
and Standard/Demo isolation.

The final reviewed S205 CI baseline is Python `3061 passed` and Web
`449 passed / 47 files`.

## Completed M33 Sequence

```text
S197 architecture and planning — Complete
S198 runtime reference and signal contracts — Complete
S199 deterministic signal evaluation — Complete
S200 account-bound Order Intent — Complete
S201 pre-trade risk decision/evidence — Complete
S202 persistence, migration, concurrency, and application service — Complete
S203 versioned API, errors, audit, and generated contracts — Complete
S204 bilingual Founder workspace — Complete
S205 Demo v5, recovery, and acceptance hardening — Complete
S206 M33 closeout and M34 handoff — Complete after merge
```

The migration head is exactly `0010_strategy_order_risk`.

## Execution Boundary and M34 Handoff

M33 owns no accepted order, reservation, fill, execution price, fee, ledger
posting, worker, scheduler, broker, QMT, MiniQMT, live, or real-money behavior.
M34 remains the first milestone allowed to own execution, fills, execution
pricing/fees, and fill-caused Paper Account mutation.

M34 may consume only an M33 Intent with a matching `allow` Decision and exact
verified M31/M32 anchors. It must revalidate account and market freshness at the
execution handoff and must separately define execution command identity,
execution-order lifecycle, fill timing and price authority, rejection/partial-
fill semantics, fees/commission/tax treatment, atomic fill-to-M31-ledger
postings, and execution idempotency/reconciliation.

M34 must not mutate M33 Signal, Intent, or Decision records and requires its own
CTO-owned architecture/planning Sprint before implementation.
