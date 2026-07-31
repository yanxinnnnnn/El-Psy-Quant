# Sprint 202 — Durable M33 Persistence, Migration, Concurrency, and Application Service

## Status

**Implementation complete in this PR; pending Founder review and manual merge.**

GitHub Issue #398 is the authoritative Sprint implementation specification.
GitHub Issue #389 remains the authoritative M33 architecture source.

## Objective

Persist and strictly reconstruct the complete Sprint 198–201 Strategy Signal,
Order Intent or no-action, and Pre-Trade Risk Decision chain without changing
any existing domain authority or digest contract.

Sprint 202 adds product-database durability, deterministic one-winner
transactions, scoped idempotency receipts, bounded repositories, and thin
application services. It does not add an API, Web workflow, execution, or any
M31/M32 mutation.

## Migration and Schema

The additive Alembic migration is:

```text
0009_market_time_runtime
  -> 0010_strategy_order_risk
```

It creates four product-database tables:

- `strategy_signals`;
- `order_intents`;
- `pre_trade_risk_decisions`; and
- `strategy_order_command_receipts`.

Each authority table stores its complete canonical JSON payload together with
indexed relational metadata. Deterministic identities and digests are unique,
foreign references preserve the Signal-to-Intent-to-Decision chain, and
database triggers reject updates and deletes. Command receipts are unique by
operation namespace and caller idempotency key and bind that key to the exact
command digest and result kind.

## Strict Reconstruction

Repository reads parse JSON with duplicate-key detection, require canonical
serialization, reconstruct every nested frozen Sprint 198–201 contract, and
rerun its existing validators. Stored relational metadata, identities, digests,
and cross-authority references must exactly match the reconstructed payload.

Malformed, incomplete, unsupported, non-canonical, digest-mismatched, or
reference-mismatched data fails closed as corrupt authority. Read paths do not
repair, normalize, or silently replace persisted facts.

## Repositories

The Sprint adds focused repositories for Signal, Intent, Decision, and command
receipt records. Supported reads are:

- exact deterministic identity;
- exact unique digest where applicable;
- indexed, explicitly filtered keyset pages capped at 200 records; and
- exact receipt namespace and idempotency key.

There is no unbounded `list_all`, update, delete, or projection-repair path.
Adding an already-identical deterministic record converges; conflicting
identity or digest reuse fails closed.

## One-Winner Transactions and Idempotency

Every mutating application operation runs in one SQLite `BEGIN IMMEDIATE`
transaction. It reopens and verifies required authority, calls the unchanged
pure domain function, stores all new authority rows, and stores the receipt
before one commit.

The same scoped key and same command digest replays the original exact result
across retries and restart. The same key with a different command digest is an
idempotency conflict. Concurrent identical commands have one winner and
converge on one immutable result. Busy/locked storage is surfaced as a typed
retryable boundary failure; partial rows or orphan receipts are never committed.

No-action is stored only as canonical receipt result evidence. It never creates
an Order Intent row and cannot become an executable authority.

## Application Service

The thin `StrategyOrderApplicationService` supports:

- evaluate and store one Strategy Signal;
- derive and store one Order Intent or exact no-action result;
- evaluate and store one allow/reject Pre-Trade Risk Decision; and
- strict identity reads of stored Signal, Intent, and Decision authority.

Before evaluation it reopens and validates persisted upstream M33 authority,
exact M31 account ledger replay and projection, and exact M32 calendar, session,
replay, cursor, and consumed-prefix authority. It then delegates all
calculation, canonical payload construction, and digest identity to the
unchanged Sprint 198–201 pure functions.

The service never derives financial or market-time truth from duplicated M33
columns, advances replay, repairs account state, or redefines existing
authorities.

## Errors

The application/repository boundary exposes typed failures for:

- not found;
- idempotency conflict;
- stale authority;
- reconciliation required;
- corrupt authority;
- retryable storage busy/locked; and
- generic storage failure.

These errors are internal Sprint 202 boundaries. Public API and bilingual
presentation mapping remain Sprint 203 and Sprint 204 work.

## Verification

Deterministic coverage includes migration shape and lineage, installed migration
resources, append-only enforcement, strict round trips, tamper/corruption
rejection, allow and reject decisions, no-action receipt replay, alternate-key
convergence, restart behavior, bounded reads, idempotency conflicts, and
concurrent retry behavior.

Required verification:

```text
uv run python scripts/check.py
uv run alembic heads
```

The expected head is:

```text
0010_strategy_order_risk (head)
```

No Docker build or pull, Compose/container startup, container smoke, volume
operation, Demo reset, browser acceptance, or Standard/Demo runtime acceptance
is performed.

## Explicit Non-Goals

Sprint 202 adds no FastAPI route, OpenAPI schema, generated TypeScript, Next.js
or Founder Web behavior, localization, Demo v5, worker, scheduler, mutable
intent status, reservation, accepted order, execution lifecycle or pricing,
slippage, fees, commission, fill, ledger event/posting, Paper Account mutation,
replay progression, broker, QMT, MiniQMT, private edge, live or real-money
behavior, or proxy configuration.

S203–S206 remain Planned. M34 remains the first milestone allowed to own
execution, fills, and fill-caused account mutation.
