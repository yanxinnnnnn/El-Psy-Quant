# Sprint 192 — Deterministic Market Data Replay Engine Foundation

## Objective

Sprint 192 establishes the first deterministic replay runtime over the approved
Sprint 191 `MarketDataEvent` contract. It consumes immutable market-state events
and owns replay ordering, cursor progression, and lifecycle state only.

## Replay Architecture

`MarketDataReplayEngine` accepts a bounded in-memory batch of canonical market
events. It validates unique event identities and orders every input by the
Sprint 191 total ordering key:

```text
(event_time in UTC, event_id)
```

`ReplayCursor` is an immutable checkpoint containing:

- the replay identity;
- a SHA-256 binding to the exact canonically ordered event stream;
- the number of consumed events;
- the last consumed event identity and event time; and
- the replay lifecycle status.

`ReplaySession` is an immutable inspection snapshot. Its start time is the first
canonical event time, its current time is the last consumed event time, and its
status and cursor are kept exact. An empty replay has no fabricated market time.

## Determinism and Restart Behavior

Identical replay identity and event input produce the same canonical event
sequence, stream digest, cursor states, and session snapshots regardless of
caller input order. Each successful `next_event()` consumes exactly the event at
the current zero-based cursor position and advances the position by one.

A new engine can restore an immutable cursor against the same event input.
Restore validates the replay identity, complete stream digest, cursor bounds,
last event identity, current event time, lifecycle status, and end-of-stream
state before any further event can be consumed. A changed, truncated, expanded,
or reordered-authority event stream therefore cannot silently duplicate or skip
events.

## Lifecycle

The lifecycle is:

```text
ready -> running
running -> paused
paused -> running
running -> completed
```

Only a ready replay may start, only a running replay may pause or consume an
event, and only a paused replay may resume. Consuming the final event moves the
replay directly to `completed`. Completion is terminal. Invalid state or
transition requests fail closed without advancing the cursor.

Starting an empty replay completes it immediately with position zero and no
event identity or market time.

## Persistence Result

Sprint 192 adds no persistence and no migration. Replay state is in memory, and
the immutable cursor provides the validated restart checkpoint boundary for the
future persistence layer. No M31 table or financial/account authority changes.

## Preserved Boundaries

`MarketDataEvent` remains authority for event representation, event time,
instrument identity, and schema version. The replay engine does not inspect or
interpret the opaque event payload and does not create financial meaning.

M31 remains unchanged:

- immutable ledger events and postings remain financial authority; and
- Paper Account ledger replay remains account-state authority.

This sprint adds no API, Web, Demo, strategy, signal, order, pre-trade-risk,
execution, broker, live-trading, or real-money behavior. Replay never imports,
creates, or mutates Paper Account state.

## Verification

Deterministic tests cover canonical ordering, identical progression, lifecycle
transitions, pause/resume behavior, immutable cursor/session snapshots, exact
cursor restoration, no duplicate or skipped events after restore, changed-input
rejection, invalid-cursor rejection, and empty replay completion.

Required verification:

```text
uv run python scripts/check.py
```
