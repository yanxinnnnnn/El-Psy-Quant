# Sprint 155 — Paper Run Launch and Status Workspace

## Status

Complete.

## Objective

Expose the existing durable paper-job submission, status, attempt audit, and
manual-control API through one deliberate Founder-facing Web workflow without
changing backend operational, domain, or artifact authority.

## Delivered Routes

```text
/paper-jobs
/paper-jobs/new
/paper-jobs/[jobId]
```

The list preserves API order and supports only the approved status and bounded
limit query parameters. The structured submission form starts with blank
identity and account fields plus empty position, order, and fill collections.
The detail route shows the exact backend job representation, independent
numbered attempts, result availability, and only the controls allowed by the
last successful backend status.

## Submission and Execution

Submission and execution remain separate:

```text
Submit queued job
  !=
Run selected queued job
```

The form consumes the generated `PaperRunCommandRequest` body, converts only
finite entered numeric transport values, rejects duplicate position symbols
before map construction, preserves order/fill row order, and sends blank fill
`order_id` as `null`. Optional `Idempotency-Key` is omitted when blank and sent
exactly when present. Successful submission navigates with the backend-returned,
independently encoded job ID and never calls Run.

Run is a separately confirmed POST that consumes the generated HTTP 202 Accepted
response type. Accepted does not mean claimed or completed; the Founder must use
manual Refresh status to observe later state.

## Manual Controls

The UI affordances are exactly:

```text
queued    -> Run, Cancel
running   -> Recover
failed    -> Retry
succeeded -> no mutation
canceled  -> no mutation
```

Every command identifies the exact job and run, requires confirmation, prevents
duplicate pending requests, and keeps loaded job data visible on bounded errors.
Cancel is queued-only. Retry returns failed state to queued without executing.
Recover sends the exact Founder-supplied timezone-aware UTC `stale_before` and
displays the returned current status without assuming a particular outcome.
State conflicts explicitly direct the Founder to refresh manually.

No mutation chains another command. No interval, timer, focus refresh,
automatic retry, polling, WebSocket, SSE, or background browser refresh exists.

## Configuration and Authority

The operator explicitly configures and migrates the existing product resources:

```powershell
$env:EL_PSY_QUANT_PRODUCT_DATABASE_PATH="C:\path\to\product.sqlite3"
$env:EL_PSY_QUANT_PAPER_ARTIFACT_ROOT="C:\path\to\paper-artifacts"
uv run alembic upgrade head
```

The database is required for durable reads and submission. Run, Retry, and
Recover also require the configured paper artifact root. The browser and Node.js
code never create, migrate, open, query, or inspect SQLite and never access the
artifact root directly.

Completed files remain authoritative. Paper-job status remains operational
state separate from lifecycle governance. The UI displays only the backend-owned
`result_available` boolean and a neutral Sprint 156 deferral. It does not call
the result endpoint, follow `result_url`, or render account state, equity,
positions, orders, fills, paths, locators, request snapshots, or result JSON.

## Client and Accessibility

Endpoint-specific clients derive all success and body types from the checked-in
FastAPI OpenAPI contract. Every dynamic job ID is encoded independently, the
browser base remains `/api/backend`, GET and POST preserve request IDs and
bounded errors, JSON headers are sent only when a body exists, and no arbitrary
request helper is exported.

The routes provide logical headings and landmarks, one effective loading region
per read, labeled form controls, associated field errors, keyboard-accessible
repeatable rows and confirmations, visible focus, text status, responsive exact
identifiers, and independent attempts and mutation alerts.

## Verification

Deterministic frontend coverage verifies navigation, list order/filter/limit and
manual refresh, structured submission and idempotency, generated request and 202
types, numeric/null conversion, duplicate blocking, status-dependent controls,
confirmation and pending guards, exact UTC recovery, independent attempts,
bounded error/request-ID behavior, malformed response sanitization, and the
absence of automatic execution or result consumption.

The authoritative gate remains:

```text
npm --prefix web ci
uv run python scripts/check.py
```

## Preserved Scope

Sprint 155 adds no result-detail view, equity, position, order, fill, comparison,
lifecycle, authentication, Docker Compose, broker, QMT, live, capital,
distributed, automatic worker, polling, scheduling, or Sprint 156–159 behavior.

## Next Sprint

```text
Sprint 156 — Equity, Positions, Orders, and Fills Views
```
