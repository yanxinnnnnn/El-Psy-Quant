# Sprint 190 — Trading Calendar Foundation

## Objective

Sprint 190 establishes the first runtime foundation of M32 by adding a
deterministic, versioned market-calendar authority that remains separate from
M31 financial and account-state authority.

## Domain Authority

`TradingCalendar` owns:

- stable calendar identity;
- normalized market identity;
- an IANA market timezone;
- a positive calendar version; and
- its timezone-aware creation timestamp.

`TradingSession` owns:

- stable session identity;
- its exact calendar reference and trading date;
- timezone-aware absolute open and close boundaries; and
- a normalized session-type identifier.

Calendar-relative validation requires the session open boundary to fall on its
trading date in the calendar timezone. The close boundary may fall on that local
date or the immediately following local date so bounded overnight sessions are
representable. Session boundaries must be strictly increasing and sessions in
one calendar cannot overlap.

## Persistence and Query Boundary

Migration `0008_market_time_foundation` adds only:

```text
trading_calendars
trading_sessions
```

Both tables are immutable after insertion. Calendar versions are unique per
market. Sessions retain a restrictive calendar foreign key and a deterministic
calendar/date/open-boundary index. The migration seeds no calendar, session,
market-data, account, or financial state and does not alter any M31 table.

The caller-transaction-owned repository supports:

- exact calendar and session lookup;
- deterministic calendar ordering by market, version, and identity;
- deterministic session ordering by trading date and boundaries;
- bounded date and session-type filtering; and
- session-derived trading-day availability.

No read repairs or inferred holiday records exist. A date is available only
when the selected persisted calendar version contains at least one session for
that date.

## Preserved Boundaries

Ledger events and postings remain financial authority, and deterministic ledger
replay remains Paper Account state authority. Sprint 190 introduces no:

- Session Clock runtime;
- MarketDataEvent ingestion;
- replay engine;
- strategy or signal runtime;
- order or pre-trade-risk pipeline;
- execution simulation;
- API or Web trading surface;
- broker integration; or
- live or real-money behavior.

## Verification

The implementation is covered by deterministic domain, persistence, migration,
downgrade, installed-wheel resource, restart, ordering, holiday-availability,
overlap, and append-only tests. Required verification is:

```text
uv run python scripts/check.py
uv run alembic heads
```

The expected single head is `0008_market_time_foundation`.
