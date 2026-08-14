# Sprint 195 — Demo and Recovery Hardening

## Authority

GitHub Issue #385 is the authoritative Sprint 195 implementation
specification. Issue #374 remains the Milestone 32 architecture authority.
Sprints 190–194 retain their calendar, canonical event, replay, persistence,
API, and Founder Web authority boundaries.

## Result

Sprint 195 adds deterministic Demo and recovery evidence over the existing
market-time capability without adding trading behavior. Demo source and
descriptor schema/dataset version 4 add:

- one immutable XNYS calendar;
- two ordered regular trading sessions;
- four canonical market-data events;
- one replay paused after exactly two events;
- the exact event-stream digest and durable checkpoint; and
- the expected remaining event identities and completed recovery state.

The Demo installer validates every fixture field before inspecting or changing
the target. A fresh install persists the calendar, sessions, events, replay
membership, and paused cursor only through the existing domain and repository
authorities.

## Restart and Recovery Verification

Existing-dataset startup reopens the database and requires an exact match with
the validated source calendar, sessions, canonical event stream, stream digest,
and paused replay session. The verifier reconstructs
`MarketDataReplayEngine` from the durable cursor, resumes a copy, consumes the
two remaining events in memory, and requires the exact completed state.

Verification then reopens the replay and confirms that the durable checkpoint
is still paused at position 2. It does not update a checkpoint, repair a stream,
replace an event, or reseed a conflicting dataset. Deterministic tests prove a
validly shaped but source-inconsistent checkpoint fails closed and remains
unchanged.

## Founder Workspace Evidence

The path-free Demo descriptor exposes the exact calendar, session, replay,
stream-digest, checkpoint, and recovery identities. The Founder first-run and
Dashboard journeys link to the existing read-only replay detail workspace.
English and Simplified Chinese copy describe inspection and recovery evidence,
not trading behavior.

## Authority Boundary

- `MarketDataEvent` still owns market-event representation, timestamp,
  instrument identity, and schema version.
- `MarketDataReplayEngine` still owns cursor validation, lifecycle, and
  deterministic progression.
- Persistence only stores and restores those existing authorities.
- Web and Demo remain presentation and verification layers.
- M31 ledger events/postings remain financial authority.
- M31 Paper Account replay remains account-state authority.

The market-time fixture does not create or mutate a Paper Account. It adds no
strategy runtime, signals, strategy-to-order conversion, pre-trade risk, order
lifecycle, execution simulation, broker integration, live trading, or
real-money behavior.

## Acceptance Boundary

Repository verification is:

```text
uv run python scripts/check.py
```

No migration is introduced. The existing single migration head remains
`0009_market_time_runtime`.

Docker build/pull, Compose or container startup, container smoke, volume
operations, Demo reset, browser acceptance, restart acceptance, return to
Standard, and the merge decision remain Founder-owned.
