# Sprint 156 — Equity, Positions, Orders, and Fills Views

## Status

Complete.

## Objective

Deliver immutable Founder-facing inspection of authoritative completed paper
results through the existing durable-job API without adding backend behavior,
financial calculations, downloads, or automatic refresh.

## Delivered Routes and Journey

```text
/portfolio-records
/portfolio-records/[jobId]
```

The list reads succeeded jobs in exact API order, keeps the bounded limit and
Refresh controls manual, displays backend-owned result availability, and links
to operational paper-job detail. Only an available backend result receives a
result-detail link. A direct detail route reads the exact selected result and
links back to both route families.

## Existing Endpoints Consumed

```text
GET /api/v1/paper-jobs?status=succeeded&limit=<1..200>
GET /api/v1/paper-jobs/{job_id}/result
```

Both clients derive success types from the checked-in OpenAPI-generated
TypeScript contract. The browser continues to call only the fixed same-origin
`/api/backend/api/v1/...` boundary. Dynamic job IDs are encoded independently,
and the UI never follows or displays backend `result_url` values.

## Artifact and Reference Authority

Completed paper artifact and result-summary files remain authoritative. The
backend reopens and cross-validates those files before returning the path-free
result response. The Web layer renders the returned compact reference,
identity, account states, session summary, positions, position changes, orders,
fills, and result audit without opening files, querying SQLite, repeating
cross-file validation, or persisting result payloads.

Every returned array remains in exact API order. Duplicate symbols, position
rows, changes, orders, fills, and values remain visible; stable rendering keys
include the array index so no duplicate row is collapsed. Successful empty
collections have explicit empty states.

## Account Cash and Equity Limitation

The current API provides cash and quantity snapshots. It does not provide market
prices for open positions, a total marked-to-market equity field, or an equity
history. The UI therefore labels starting and current values as account cash and
does not manufacture valuation, profit, return, exposure, or chart data.

Cash changes, quantity changes, and all counts are displayed exactly as supplied
by the backend. They are not recomputed or reconciled in the browser.

## Errors, Navigation, and Manual Refresh

The workspace distinguishes product-database and paper-root configuration
failures, missing jobs, unavailable results, invalid results, malformed success
responses, and transport failures with bounded titles, public messages, and
request IDs when available. Missing jobs offer back navigation without a retry
loop; all recoverable reads use explicit manual Retry or Refresh only.

Portfolio Records is enabled for both new route families. Paper Runs remains
active only for its S155 routes. The operational detail page exposes a result
link only when its last successful backend representation has
`result_available=true`; it never loads result contents automatically.

## Preserved Scope

Sprint 156 adds no backend route, schema, persistence, artifact-reader or writer
change; no calculation, chart, export, download, comparison, lifecycle action,
authentication, Docker Compose, broker, QMT, live, or capital behavior; and no
polling, timer, automatic retry, worker, WebSocket, or SSE. Sprints 157 through
159 remain out of scope.

## Verification

```text
npm --prefix web ci
uv run python scripts/check.py
```

The production build requires no running API, database, artifact root, or
external network.

## Next Sprint

```text
Sprint 157 — Paper Run Comparison Workspace
```
