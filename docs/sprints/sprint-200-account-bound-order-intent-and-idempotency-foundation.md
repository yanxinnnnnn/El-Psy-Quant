# Sprint 200 — Account-Bound Order Intent and Idempotency Foundation

## Status

**Implementation complete in this PR; pending Founder review and manual merge.**

GitHub Issue #394 is the authoritative Sprint implementation specification.
GitHub Issue #389 remains the authoritative M33 architecture source.

## Objective

Add the first pure deterministic conversion from one immutable Strategy Signal
and one exact validated M31 Paper Account ledger state into either one immutable
account-bound, risk-pending Order Intent or deterministic target-satisfied
no-action evidence.

Sprint 200 adds no risk evaluation, persistence, migration, application
service, API, Web, Demo, reservation, execution, fill, replay progression, or
account mutation.

## M31 Validation and Account Evidence

`validate_paper_account_ledger_state(...)` exposes the existing complete pure
M31 validation path without duplicating account invariants in M33. It accepts
only an exact `PaperAccountLedgerState`, validates its identity, lifecycle,
cash/available-cash invariant, ordered positions, exact quantities and cost
bases, evidence references, and head anchors, and returns the same immutable
state without repair or side effects.

`OrderIntentAccountReference` copies evidence from one exact active M31 ledger
state and binds it to the Signal instrument. It contains account identity,
currency, lifecycle, head version/event/chain, cash, available cash, exact
instrument, and current exact position quantity. A missing exact instrument is
canonical zero. Frozen and closed states fail closed.

The reference is not a second account, balance, position, ledger, projection,
snapshot, reconciliation, or reservation authority. Authoritative state still
comes from M31 ledger replay.

## Command and Stale Binding

`DeriveOrderIntentCommand` contains the complete compact Signal reference,
complete account reference, exact
`target_position_quantity_delta_v1` policy, bounded M31 idempotency key and
actor, and canonical command digest. Construction has no side effect, creates
no timestamp, and derives no side or requested quantity.

`derive_order_intent(...)` validates the command, concrete Signal, and concrete
M31 state, then recreates both references. Any changed Signal identity or market
anchor, account identity/lifecycle/head/event/chain, cash, available cash,
instrument quantity, or policy fails closed. A new account version always
requires a new command and result even when the position is numerically
unchanged.

## Exact Buy, Sell, and No-Action Conversion

Conversion uses only exact M31 `PaperQuantity` arithmetic:

```text
target > current
  -> buy
  -> requested_quantity = target - current

target < current
  -> sell
  -> requested_quantity = current - target

target = current
  -> target_already_satisfied no-action
  -> no Order Intent
```

There is no caller-authored side or quantity, implicit rounding, float
conversion, signed zero, price, notional, fee, cash sufficiency, risk check, or
reservation.

## Deterministic Identity and Idempotency

An `OrderIntent` is immutable risk-pending request evidence. Its
`oi_<digest>` identity binds the complete Signal, market, account, target,
current quantity, derived side, requested quantity, and policy evidence.

`OrderIntentNoAction` is separate immutable evidence with reason
`target_already_satisfied`. Its `no_action_<digest>` identity binds the same
applicable authority and policy. It contains no side or requested quantity, is
not an Order Intent, cannot produce an intent reference, and cannot enter future
pre-trade risk evaluation.

Command idempotency key, actor, command digest, and `created_at` are audit facts
excluded from result identity. Therefore:

- same key and same normalized command content produces the same command digest;
- same key and different content produces a different digest for future S202
  conflict handling;
- different keys or actors over identical authority converge on the same result
  identity;
- repeated exact conversion reproduces the same identity; and
- changed Signal or account head produces a different result identity.

S200 creates no durable idempotency store. One-winner transactions and duplicate
mappings remain S202 scope.

## Closed Lifecycle Vocabulary

The exact future derived risk-status vocabulary is:

```text
proposed
risk_allowed
risk_rejected
```

S200 intents are semantically proposed/risk-pending because no S201 decision
exists. Status is not a mutable S200 field, and there is no status mutation or
execution behavior.

## Verification

Focused tests cover M31 validation, exact account evidence, frozen/closed and
tampered-state rejection, command bounds and digest sensitivity, complete stale
binding, exact buy/sell/no-action conversion, maximum-scale arithmetic,
deterministic identities, idempotent convergence, compact references, direct
construction blocking, immutability, strict JSON exports, closed vocabularies,
and absence of persistence/application/execution dependencies.

Before completion Codex runs:

```text
uv run python scripts/check.py
```

Sprint 200 adds no migration. The migration head remains:

```text
0009_market_time_runtime
```

No Docker build or pull, Compose/container startup, container smoke, volume
operation, Demo reset, browser acceptance, or Standard/Demo runtime acceptance
is performed.

## Explicit Non-Goals

Sprint 200 adds no repository read, projection repair, ledger event/posting,
account-version mutation, pre-trade risk, reference price, reservation,
persistence/idempotency table, SQLAlchemy, Alembic migration, application
service, API/OpenAPI/generated contract, Web/localization, Demo, replay
mutation, accepted/execution order lifecycle, cancellation, routing, fill, fee,
worker, scheduler, broker, QMT, MiniQMT, private-edge, live, real-money, or proxy
behavior.

S201–S206 remain Planned. M34 remains the first execution, fill, and
fill-caused Paper Account mutation milestone.
