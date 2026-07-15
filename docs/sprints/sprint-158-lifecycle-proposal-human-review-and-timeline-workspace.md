# Sprint 158 — Lifecycle Proposal, Human Review, and Timeline Workspace

## Status

Complete.

## Objective

Deliver the Founder-facing lifecycle governance workspace over the existing
stateless application commands without creating an automatic strategy state
machine.

## Delivered Route and API Boundary

Sprint 158 adds exactly:

```text
/lifecycle-review
```

The browser calls only:

```text
POST /api/v1/lifecycle-transition-proposals
POST /api/v1/lifecycle-transition-records
```

Both endpoint clients derive request and HTTP 200 success types from the
checked-in generated OpenAPI contract and use the fixed same-origin
`/api/backend/api/v1/...` boundary. No backend, OpenAPI, database, domain,
dependency, persistence, artifact, or filesystem behavior changed.

## Proposal and Human Review Flow

The Founder supplies a complete source snapshot, proposal, ordered evidence
references, and optional notes, warnings, and metadata. After the backend
returns a normalized proposal, the Founder may separately submit a complete
human review command carrying that normalized proposal. A resulting snapshot
is an explicit optional caller input rather than a browser-derived value.

Lifecycle states, permitted transitions, minimum evidence types, human review
outcomes, and outcome/resulting-snapshot relationships remain free-form
transport strings in the Web layer. Existing backend domain factories remain
the sole authority that accepts or rejects those values. Bounded endpoint
errors and request IDs remain visible.

## Immutable Inspection and Timeline

The workspace displays the latest successful normalized command responses in
the current browser session:

```text
caller-supplied source snapshot
  -> non-executing proposal
  -> human review governance record
  -> optional caller-supplied resulting snapshot
```

Evidence references remain unresolved pointers whose exact order and duplicates
are preserved. Notes and warnings also retain backend order and duplicates. The
timeline is a presentation of the response chain currently visible on the page;
it is not persisted and is not a globally authoritative current-state view.

## Human-Control Boundary

A proposal is not approval. A review record is not transition execution. Even
an approved record or returned resulting snapshot does not automatically apply
a transition, promote a strategy, establish globally current state, allocate
capital, or trigger a paper run. The workspace performs none of those actions.

## Navigation and Next Step

Lifecycle Review is enabled only for `/lifecycle-review`. All Sprint 152–157
routes retain their existing route-family behavior. The next separately scoped
sprint is:

```text
Sprint 159 — Minimal Authentication, Docker Compose, and End-to-End MVP Closeout
```

Sprint 158 adds no authentication, Docker Compose, broker, QMT, live execution,
automatic governance, or Sprint 159 behavior.

## Verification

```text
npm --prefix web ci
uv run python scripts/check.py
```

The unified gate continues to cover generated-contract freshness, linting,
strict TypeScript, frontend and Python tests, and a production build without a
running backend, product database, artifact root, or external network.
