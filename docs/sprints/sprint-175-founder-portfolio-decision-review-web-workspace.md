# Sprint 175 — Founder Portfolio Decision Review Web Workspace

## Status

Implementation complete / pending Founder review.

## Objective

Expose the merged Sprint 170–174 portfolio-review authority through one
responsive English and Simplified Chinese Founder workflow:

```text
backend-ordered review list
  -> manual structured source and scenario construction
  -> authoritative reopened evidence detail
  -> one explicit human governance decision
```

Sprint 175 is a Web-only product increment. It uses the checked-in Sprint 174
OpenAPI-generated TypeScript contracts and changes no Python, domain,
persistence, migration, API, OpenAPI, or generated-contract file.

## Routes and Navigation

The Founder workspace adds **Portfolio Reviews** after **Comparisons** and before
**Lifecycle Review**. It owns exactly:

```text
/portfolio-reviews
/portfolio-reviews/new
/portfolio-reviews/[reviewId]
```

Nested routes retain the Portfolio Reviews active-navigation state.

## Generated-Contract Client Boundary

The Web API client provides typed GET and POST behavior for all four Sprint 174
portfolio-review routes. Both mutations require an explicit caller-supplied
`Idempotency-Key`, accept `201 created` and `200 replayed`, and never invent or
rotate the key.

Composable runtime guards validate every nested compact record, source,
scenario, concentration, exposure, coverage, overlap, correlation, behavior,
drawdown, contribution, impact, analysis, decision, and command-wrapper value.
Malformed nested success responses fail as `api_response_invalid`.

## List Workspace

The list renders every compact record in exact backend order, including
duplicates. It exposes the raw review, source, proposed-component, status,
timestamp, and full analysis-digest values plus an exact encoded detail link.

Status and limit values remain drafts until **Apply filters** is selected.
Refresh is manual. A refresh keeps the previous successful list visible until a
new valid response replaces it; failures retain that evidence and expose stable
operation, error-code, and request-ID audit context.

The browser does not rank, sort, deduplicate, recommend, or poll.

## Structured Create Workspace

Because Sprint 175 has no source-list endpoint, creation is manual and
structured. The form supports:

- explicit review identity and idempotency key;
- source actors, timestamps, evaluation settings, prose, and missing evidence;
- 2–12 ordered components with ordered evidence references and optional
  declared symbols;
- at least three ordered aligned return observations;
- exact baseline and proposed scenario identities, weights, assumptions, and
  warnings;
- explicit proposed-component selection;
- analysis audit fields, assumptions, warnings, and missing evidence; and
- an explicit local historical-evidence and non-execution confirmation.

Dynamic rows use browser-only stable keys that never enter the request payload.
Component changes update dependent observation and weight controls while
preserving authoritative component order.

Numeric drafts remain strings. They become JSON numbers only after strict finite
decimal validation that rejects exponent notation. The browser displays each
entered weight total and validates the exact backend tolerance, but never
normalizes, rounds, suggests, auto-selects, or changes a value.

Validation and API failures preserve the complete draft. Duplicate in-flight
submission is prevented. A successful created or replayed response remains on
the page with an explicit link to authoritative detail; the browser does not
redirect automatically.

## Evidence Detail

Detail renders reopened backend authority without financial calculation:

- source audit, ordered components, references, and full observations;
- baseline and proposed scenarios and exact weights;
- concentration, review exposure, and universe coverage;
- declared-symbol overlap and pairwise/candidate correlations;
- historical behavior, drawdown, contribution, and exact
  proposed-minus-baseline impact;
- assumptions, warnings, and missing evidence;
- schema versions, digests, raw timestamps, and audit identity; and
- the human decision, when one exists.

Repeated values and prose remain repeated. Numeric values are rendered from the
response with no percentage formatting, rounding, scoring, ranking, or
better/worse styling. Unavailable evidence stays unavailable and displays its
raw reason and affected component IDs; it is never replaced by zero.

Manual refresh replaces detail only after a complete valid response. A failed
refresh leaves the previously loaded evidence visible.

## Human Decision

Only an `awaiting_decision` review exposes the form. It requires an explicit
idempotency key, decision ID, one non-default outcome, rationale, reviewer,
timezone-aware timestamp, notes, warnings, and governance-only/non-execution
confirmation.

Success replaces the page with the authoritative returned detail. Conflict or
failure preserves both the loaded evidence and every decision draft value.
Settled reviews show only the immutable decision and cannot submit another.

`approved`, `rejected`, and `deferred` remain governance evidence. They do not
change lifecycle state, allocate capital, create or fund an account, create
orders, or execute.

## Localization, Errors, and Accessibility

Complete English and Simplified Chinese catalogs cover routes, evidence,
validation, decisions, status/outcome labels, and all nine Sprint 174 stable
portfolio-review errors. Raw IDs, transport values, codes, timestamps, digests,
and numeric values remain untranslated.

Forms use semantic fieldsets, labels, required/optional guidance, inline
validation association, focused alerts, disabled duplicate submission, and
explicit confirmations. Tables and card layouts remain horizontally safe or
stack on narrow screens.

## Verification

Synthetic frontend fixtures exercise unusual exact numeric values, duplicate
prose and records, unavailable evidence, 2- and 12-component boundaries,
created/replayed commands, invalid nested responses, filters, refresh retention,
decision settlement, and conflict draft preservation.

Required repository gates are:

```text
uv run python scripts/check.py
uv run alembic heads
```

The expected migration head remains:

```text
0006_portfolio_reviews
```

No Docker runtime acceptance is part of Sprint 175.

## Handoff

Milestone 30 remains In Progress. Sprint 176 owns integration, isolated Demo
evidence, complete error/audit inventory, and Founder runtime acceptance
hardening. Sprint 177 owns closeout and the strict handoff to the separately
authoritative M31 Paper Account and ledger.
