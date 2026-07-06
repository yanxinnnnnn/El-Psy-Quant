# Sprint 54 — Price Data Validation Foundation

## Objective

Add one reusable structural validation boundary for local daily price data.

## Product Goal

Loaders, cache writers, and future configured workflows should share explicit
requirements for price columns, close values, and the date index.

## Implementation Scope

- Define the required OHLCV price columns.
- Reject empty, incomplete, non-DataFrame, or non-datetime-indexed inputs.
- Reject missing or duplicate dates and missing or non-numeric close values.
- Reuse validation in local cache writes while preserving cache behavior.
- Preserve existing CSV parsing, indexing, and sorting behavior.

## Validation Discipline

Validation observes structure only. It does not sort, mutate, coerce, fill,
download, or otherwise transform the input DataFrame.

## Out of Scope

- Configured experiment wiring or symbol universe implementation.
- Strategy, resolver, artifact, CLI, portfolio, or trading changes.
- External validation services or live download behavior changes.

## Acceptance Criteria

- Valid local daily prices pass reusable validation.
- Invalid structures raise clear `ValueError`s.
- Validation leaves input values, columns, and index unchanged.
- Valid cache-write and CSV-load behavior remains stable.
