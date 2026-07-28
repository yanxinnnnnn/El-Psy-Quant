# Sprint 193 — Market Time Persistence and API Layer

## Objective

Sprint 193 makes the approved Sprint 190–192 market-time authorities durable
and inspectable without adding financial authority or trading behavior.

## Persistence Architecture

Migration `0009_market_time_runtime` is additive to
`0008_market_time_foundation` and creates only:

```text
market_data_events
market_data_replays
market_data_replay_events
```

`market_data_events` stores the exact canonical Sprint 191 event JSON together
with its event schema version, identity, instrument identity, and event time.
Events are append-only. Reusing an event identity with different canonical
content fails closed.

`market_data_replay_events` stores immutable replay membership and zero-based
canonical event order. `market_data_replays` stores the Sprint 192 replay
session and cursor checkpoint. Replay identity, stream digest, event count, and
start time are immutable; only the engine-owned cursor position, last event,
current event time, and lifecycle status may be checkpointed.

The migration seeds no calendar, session, event, replay, account, ledger, order,
or execution state and does not modify M31 tables.

## Recovery Boundary

`MarketDataReplayRecord` binds one `ReplaySession` to its exact canonically
ordered event stream and provides deterministic JSON serialization. Repository
restore reconstructs every `MarketDataEvent`, validates its canonical JSON and
stored metadata, rebuilds the `ReplaySession`, and validates the cursor against
the exact stream through `MarketDataReplayEngine`.

Checkpoint replacement uses an exact expected cursor. A stale checkpoint is
not overwritten. Persistence does not interpret market payloads or invent
replay progression.

## Read-only API

The authenticated versioned API adds exactly four GET-only operations:

```text
GET /api/v1/market-time/calendars
GET /api/v1/market-time/calendars/{calendar_id}
GET /api/v1/market-time/replays
GET /api/v1/market-time/replays/{replay_id}
```

The routes provide deterministic calendar/session lists, replay status, cursor
inspection, and exact canonical event inspection. API payloads are presentation
only and cannot create, advance, pause, resume, or otherwise mutate a replay.

## Preserved Authority Boundaries

- `MarketDataEvent` remains authority for event representation, timestamp,
  instrument identity, and schema version.
- `MarketDataReplayEngine` remains authority for cursor validation, lifecycle,
  and deterministic progression.
- Persistence only stores and restores those authorities.
- M31 ledger events/postings remain financial authority.
- M31 Paper Account replay remains account-state authority.

Sprint 193 adds no strategy runtime, signal generation, order lifecycle,
pre-trade risk, execution simulation, account mutation, broker integration,
trading UI, live trading, or real-money behavior.

## Verification

Required verification is:

```text
uv run python scripts/check.py
uv run alembic heads
```

The expected single migration head is `0009_market_time_runtime`.
