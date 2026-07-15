# Sprint 157 — Paper Run Comparison Workspace

## Status

Complete.

## Objective

Deliver one read-only Founder-facing workspace for explicit side-by-side
inspection of a small ordered set of completed authoritative paper results.

## Delivered Route and Selection

Sprint 157 adds exactly:

```text
/comparisons
```

The Founder selects two to four distinct succeeded jobs whose backend-owned
`result_available` value is true, then explicitly applies the set. The applied
selection is navigation state represented by repeated ordered query parameters:

```text
/comparisons?job_id=<job-a>&job_id=<job-b>
```

Blank, duplicate, one-item, and more-than-four-item direct selections are
rejected before any result request. Candidate API order determines chooser
application order, while direct query order determines comparison display
order. Every dynamic job ID is independently encoded.

## Existing Endpoints Consumed

The browser uses only:

```text
GET /api/v1/paper-jobs?status=succeeded&limit=<1..200>
GET /api/v1/paper-jobs/{job_id}/result
```

The list and exact result clients keep using generated OpenAPI success types and
the fixed same-origin `/api/backend/api/v1/...` boundary. No backend, OpenAPI,
schema, database, domain, persistence, or dependency change was introduced.

## Authoritative and Partial-Error Behavior

Every selected immutable result loads independently. The workspace preserves
the selected URL order regardless of response completion order, suppresses
responses from stale comparison batches, and keeps successful runs visible when
another selected run fails. Each failed run has its own bounded error, request
ID when supplied, and manual retry. One manual **Refresh comparison** action
reloads every selected result once.

There is no polling, focus refresh, scheduled refresh, automatic retry, or
successful-result refetch loop. At most one primary loading live region is
announced while chooser or comparison requests are pending.

## Read-Only Juxtaposition

The selected runs display backend-returned fields only:

- identity, compact result reference, artifact, result-summary, and audit
  provenance
- starting and ending account-cash snapshots
- session-summary timestamps, cash values, and order/fill counts
- the separate backend result audit and all of its counts
- artifact and session-summary starting and ending positions
- backend-provided session-summary position changes

Every returned position and position-change array retains exact order and
duplicates. Successful empty collections remain visible. Full orders and fills
remain on the exact Sprint 156 Portfolio Record route and are linked rather than
duplicated or aligned.

## No-Calculation and M21 Boundary

The workspace does not calculate cross-run cash or quantity deltas, total
equity, valuation, P&L, return, risk, exposure, fees, slippage, or any other
financial metric. It does not rank, score, recommend, identify a winner, imply
superiority, or create a review decision.

Milestone 21 comparison facts, assumptions, warnings, missing evidence,
summaries, decisions, references, and manifests remain explicit caller-supplied
governance contracts. Sprint 157 does not construct or persist them from browser
calculations.

## Navigation and Next Step

Comparisons is enabled only for `/comparisons`. Paper Runs and Portfolio Records
retain their exact route-family active states, and Lifecycle Review remains
unavailable. Portfolio Records links clearly to the comparison chooser.

Milestone 28 remains in progress. The next planned workspace is:

```text
Sprint 158 — Lifecycle Proposal, Human Review, and Timeline Workspace
```

## Verification

```text
npm --prefix web ci
uv run python scripts/check.py
```

The unified gate continues to cover generated-contract freshness, linting,
strict TypeScript, frontend and Python tests, and a production build without a
running backend, database, artifact root, or external network.
