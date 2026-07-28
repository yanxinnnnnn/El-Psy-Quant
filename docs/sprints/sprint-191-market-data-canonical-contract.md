# Sprint 191 — Market Data Canonical Contract

## Objective

Sprint 191 establishes the immutable, version-aware `MarketDataEvent` domain
contract that future deterministic replay components may consume. It defines
market-state representation only and does not ingest, persist, replay, or act on
market data.

## Domain Authority

`MarketDataEvent` owns:

- a stable event identity;
- one canonical opaque instrument identity;
- the market event timestamp;
- a normalized event-type and source identity;
- one strict JSON-object payload; and
- the event schema version.

Instrument identifiers are trimmed, uppercased ASCII tokens using letters,
digits, `.`, `_`, `:`, `/`, and `-`. The contract does not infer exchange,
security master, currency, account position, or financial meaning from the
identifier.

Event time is the time assigned to the market-state event. It must be
timezone-aware and is normalized to UTC. It is not an ingestion, persistence,
processing, wall-clock, or account-ledger timestamp.

## Schema and Canonical Serialization

Schema version `1` is the only supported version. The constructor and strict
mapping/JSON readers reject booleans, non-integer versions, and unknown
versions. This fail-closed behavior prevents a future schema from being silently
interpreted with version-1 rules.

The serialized contract has exactly:

```text
schema_version
event_id
instrument_id
event_time
event_type
payload
source
```

`event_time` is serialized as a canonical UTC ISO 8601 string. Payloads must be
JSON objects composed only of string keys, null, booleans, integers, finite
floating-point values, strings, arrays, and nested objects. Non-finite numbers,
non-string keys, non-JSON Python values, invalid Unicode, duplicate JSON keys,
unknown event fields, and missing event fields are rejected.

Canonical JSON uses UTF-8-compatible Unicode, lexicographically sorted object
keys, no insignificant whitespace, and strict finite JSON numbers. The event
retains an immutable canonical payload snapshot and returns isolated payload
copies so caller mutation cannot change event authority.

## Deterministic Ordering

Market-data events are ordered by:

```text
(event_time in UTC, event_id)
```

`event_id` is the total-order tie breaker for events at the same instant. Event
identities must be unique within one ordered batch. Instrument, event type,
source, payload, and caller input order do not alter ordering.

## Preserved Boundaries

Sprint 191 adds no persistence or migration. M31 ledger events/postings remain
financial authority, and Paper Account replay remains account-state authority.
The market-data payload is opaque market state and cannot create, fund, mutate,
or authorize an account.

This sprint introduces no:

- market-data ingestion or live feed;
- Session Clock runtime or replay engine;
- strategy runtime, signal, or order generation;
- pre-trade risk or order lifecycle;
- execution simulator;
- API, Web, or Demo trading surface;
- broker integration; or
- live or real-money behavior.

## Verification

Deterministic tests cover creation, schema validation, instrument validation,
timestamp normalization, strict payload validation, immutable payload isolation,
canonical serialization, version-1 round trips, fail-closed unknown versions,
and deterministic ordering.

Required verification:

```text
uv run python scripts/check.py
```
