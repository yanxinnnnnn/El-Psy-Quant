# Sprint 201 — Pre-Trade Risk Decision and Evidence Foundation

## Status

**Complete after PR #397 merged.**

GitHub Issue #396 is the authoritative Sprint implementation specification.
GitHub Issue #389 remains the authoritative M33 architecture source.

## Objective

Add the first pure deterministic pre-trade risk evaluation over one complete
Sprint 200 M33 Order Intent and exact current M31/M32 authority.

Sprint 201 creates immutable risk evidence only. It does not persist M33 state,
reserve cash or positions, mutate an intent or Paper Account, advance replay,
create an execution order or fill, or expose API, Web, or Demo behavior.

## Policy and Command

`PreTradeRiskPolicyReference` selects only
`long_only_cash_risk_v1 / latest_trade_price_v1`. It has explicit optional exact
positive `PaperQuantity` and `PaperMoney` maximums. There are no hidden default
limits, leverage, margin, currency conversion, fees, or broker fields.

Its configuration digest covers only the exact nullable limit object. Its
reference digest covers the complete versioned policy reference.

`EvaluatePreTradeRiskCommand` accepts only one complete valid S200 M33
`OrderIntent`, one complete policy reference, and bounded normalized M31
idempotency-key/actor values. `OrderIntentNoAction`, the M15 backtest intent,
Paper orders, and arbitrary objects fail closed. The command contains no price,
balance, position, side, quantity, notional, outcome, reason, or timestamp.

## Exact Authority and Stale Binding

`evaluate_pre_trade_risk(...)` validates and recreates:

- the complete risk command and M33 Order Intent;
- the complete M31 `PaperAccountLedgerState`;
- the exact intent reference;
- the exact active-account reference for the intent instrument;
- the concrete M32 Trading Calendar and Trading Session;
- the complete replay stream, current cursor, current consumed event, and market
  reference; and
- the complete risk policy.

Any changed intent, account identity/lifecycle/head/event/chain/cash/available
cash/position, calendar/session, replay ID/stream/cursor/event/time/instrument,
or policy fails stale without a snapshot or decision. A changed account head or
cursor always requires new authority even when numeric values match. Replay
lifecycle-only changes remain identity-equivalent when the exact stream and
cursor prefix are unchanged.

M31 ledger replay remains Paper Account state authority. M32 calendar, event,
cursor, ordering, and replay remain market-time authority. S201 references are
immutable copied/derived evidence only.

## Latest-Trade Price Evidence

Evaluation searches backwards through only:

```text
replay_engine.events[:replay_engine.cursor.position]
```

It selects the first latest event with the exact intent instrument and
`event_type = trade`. Other instruments and event types are ignored; future
unconsumed events are never considered. The latest matching event must contain
one top-level concrete JSON integer or float `price`. It is converted with
`Decimal(str(value))` to one finite, strictly positive, exactly representable
`PaperMoney` value without rounding.

Missing, nested-only, null, boolean, string, zero, negative, excessive-precision,
overflow, NaN, or infinite price input fails closed. An invalid latest match is
not skipped for an older valid event.

`PreTradeRiskPriceReference` records the replay/stream/cursor, exact one-based
event position, event ID/time/instrument, digest of the complete canonical M32
event, exact price, and its own reference digest. This price is only pre-trade
notional evidence. It is not execution, fill, valuation, or replacement
market-data authority.

## Exact Notional and Ordered Rules

Estimated order notional is exactly:

```text
requested_quantity * reference_price
```

The product must be exactly representable as `PaperMoney`; no rounding is
permitted.

Every `PreTradeRiskInputSnapshot` contains four
`PreTradeRiskRuleEvidence` records in this exact order:

```text
insufficient_position_quantity
maximum_order_quantity_exceeded
maximum_order_notional_exceeded
insufficient_available_cash
```

- The position rule applies only to sells and passes when current quantity is at
  least requested quantity.
- The maximum-quantity rule applies only when its policy limit is configured.
- The maximum-notional rule applies only when its policy limit is configured.
- The available-cash rule applies only to buys and passes when available cash is
  at least estimated notional.

Non-applicable rules remain present, pass, and use JSON `null` for observed and
threshold values. Applicable records use exact canonical quantity or money
strings. Every rule has its own canonical digest.

## Snapshot and Decision Identity

The immutable snapshot binds the complete intent, market, account, policy,
price, side, requested quantity, verified available cash/current quantity,
estimated notional, and ordered rules.

```text
snapshot_id = risk_input_<snapshot_digest>
```

Command key, actor, command digest, and audit time are not snapshot fields and
do not affect snapshot identity.

`PreTradeRiskDecision` is `allow` exactly when every applicable rule passes.
Allow has no reasons. Reject contains every failed applicable rule exactly once
in stable rule order.

```text
decision_id = risk_decision_<decision_digest>
```

Decision identity covers the complete snapshot, outcome, and ordered reasons.
Origin key, command digest, actor, and explicit UTC `created_at` are audit
metadata excluded from identity. Validation cryptographically recomputes the
stored origin command digest from the stored intent reference, policy, key, and
actor. Different audit commands over identical exact authority converge on the
same snapshot and decision identity.

## Fail-Closed and Authority Boundary

Valid complete evidence with failed policy rules produces an immutable reject
decision. Invalid, missing, unsupported, tampered, stale, or unrepresentable
authority raises a deterministic domain error and creates no decision. No
exception or missing input defaults to allow.

A decision does not mutate an intent, assign a mutable risk status, reserve
cash/position, increment account version, pause/advance/checkpoint replay,
create/submit/route/cancel/execute an order, create a fill/fee/execution price,
or post to the ledger. M34 remains the first execution, fill, and fill-caused
Paper Account mutation milestone.

## Verification

Focused deterministic tests cover policy and command contracts, exact authority
binding, stale account/replay/calendar/session rejection, lifecycle-only replay
equivalence, latest-price selection and malformed-price failure, exact
notional, all rule outcomes and boundaries, deterministic snapshot/decision
identity, origin-command revalidation, tamper rejection, immutability, strict
JSON exports, and pure-package dependency boundaries.

Before completion Codex runs:

```text
uv run python scripts/check.py
```

Sprint 201 adds no migration. The migration head remains:

```text
0009_market_time_runtime
```

No Docker build or pull, Compose/container startup, container smoke, volume
operation, Demo reset, browser acceptance, or Standard/Demo runtime acceptance
is performed.

## Explicit Non-Goals

Sprint 201 adds no repository read, projection repair, persistence or durable
idempotency, SQLAlchemy, Alembic migration, application service, FastAPI,
OpenAPI, generated TypeScript, Next.js/Web/localization, Demo, mutable intent
status, reservation, replay mutation, execution lifecycle/pricing, slippage,
fees, commissions, fills, ledger mutation, worker, scheduler, broker, QMT,
MiniQMT, private-edge, live, real-money, or proxy behavior.

Sprint 202 is the current implementation sprint. S203–S206 remain Planned.
