# Sprint 174 — Durable Portfolio Review Persistence and Application/API Foundation

## Status

Complete.

## Objective

Make the merged Sprint 170–173 portfolio-review authority durable and
inspectable through one bounded local workflow:

```text
validated source and scenarios
  -> source.json and analysis.json
  -> compact awaiting_decision SQLite record
  -> exact list and detail reads
  -> one explicit human decision
  -> decision.json and one settled SQLite outcome
```

Sprint 174 adds artifact I/O, compact persistence, application orchestration,
idempotency, conflict handling, one-winner settlement, versioned API contracts,
OpenAPI, and generated TypeScript. It adds no Founder Web route or component,
Demo data, lifecycle mutation, Paper Account, order, execution, broker, or live
behavior.

## Immutable File Authority

The existing configured evidence artifact root remains the only root. It must
already exist as a real non-symlink directory. The server owns the exact layout:

```text
portfolio-reviews/
  sources/<source-key>/source.json
  reviews/<review-key>/analysis.json
  reviews/<review-key>/decision.json
```

`source-key` and `review-key` are lowercase SHA-256 hashes of the exact
normalized UTF-8 source and review IDs. Raw IDs never become path fragments.
Unicode, slash, backslash, traversal-like, drive-like, and absolute-looking IDs
therefore cannot change the fixed hierarchy.

Every selected directory and file is checked for containment, shape, and
symlinks. API contracts expose no filesystem path.

Files use deterministic UTF-8 JSON with sorted keys, two-space indentation,
non-ASCII preservation, non-finite rejection, and one trailing newline. New
publication uses a sibling exclusive temporary file and atomic no-replace hard
link. An existing target is never overwritten, deleted, repaired, or renamed.

Exact validated existing content may be reused. Different valid authority
conflicts. Malformed, duplicate-key, non-finite, unsupported, digest-mismatched,
truncated, unsafe, or schema-invalid content is rejected.

## Strict Reopen and Recalculation

Source reopen reconstructs every evidence reference, ordered component, symbol
tuple, timestamp, and return vector through the Sprint 170 factories. Its full
export must equal `source.json`.

Analysis reopen first reopens the exact source, reconstructs both scenarios,
creates their exact pair, and calls
`create_portfolio_review_analysis_artifact(...)`. Sprint 171 concentration and
exposure plus Sprint 172 interaction and impact are recalculated; saved derived
financial values are never deserialized into trusted domain objects.

Decision reopen first reopens the exact analysis and then calls
`create_portfolio_review_decision_artifact(...)` from the saved human input. Its
full export must equal `decision.json`.

## Compact SQLite Authority

Migration `0006_portfolio_reviews` follows
`0005_paper_job_result_references` and adds exactly one table:

```text
portfolio_reviews
```

The row owns compact review/source/scenario/analysis identity, fixed relative
locators, create and decision idempotency bindings, status, actors, UTC
timestamps, outcome, and version. It stores no full source, scenario,
observation, analysis, overlap, correlation, contribution, or decision payload.
It also stores no account, cash, position, order, fill, fee, ledger, market, or
broker value.

Supported states are exactly:

```text
awaiting_decision
approved
rejected
deferred
```

An awaiting row has no decision fields and version `1`. A settled row has every
decision field, matching status and outcome, and version `2`. SQLite-naive
timestamp round trips are explicitly restored as UTC.

The SQLAlchemy repository is caller-transaction-owned. It flushes but never
commits. List order is `created_timestamp DESC`, then `review_id ASC`. Decision
settlement is one conditional SQL update against exact awaiting status, version
`1`, and absent decision fields.

## Idempotency and Transaction Ordering

Both POST commands require an explicit key matching:

```text
[A-Za-z0-9._:-]{1,128}
```

The create command digest is canonical SHA-256 over:

```json
{"source": "<exact source export>", "analysis": "<exact analysis export>"}
```

The decision command digest is canonical SHA-256 over the exact decision export.
The key itself is excluded.

Create reserves and flushes the compact row before publishing files. It writes
or exactly reuses `source.json` and `analysis.json`, reopens both, and commits
only after complete cross-validation. A file failure rolls back the row.

Decision reopens the exact analysis, builds the human decision, conditionally
reserves every settlement field, writes or exactly reuses `decision.json`,
reopens it, and commits only after complete cross-validation. A file failure
rolls the row back to `awaiting_decision`.

If a process fails after exact files are published but before database commit,
the exact matching retry may reuse those orphan files. Different content cannot
adopt or overwrite them. An awaiting row ignores an unreferenced orphan
`decision.json`. Concurrent different decisions have one database winner; the
loser receives a settled-review conflict and cannot overwrite either authority.

## Application and API Boundary

Application services own transaction boundaries and provide compact summaries,
exact detail, created/replayed results, and one decision command. Detail always
reopens and cross-validates every database identity, digest, schema, locator,
status, actor, timestamp, outcome, and version.

The authenticated API adds exactly:

```text
POST /api/v1/portfolio-reviews
GET  /api/v1/portfolio-reviews
GET  /api/v1/portfolio-reviews/{review_id}
POST /api/v1/portfolio-reviews/{review_id}/decision
```

Create and decision return `201` for a new command and `200` for an exact
replay. List supports optional status plus limit `1–200` with default `50`.
Every source, scenario, Sprint 171 result, Sprint 172 result, analysis,
decision, record, and detail value has an explicit Pydantic response schema.
No authoritative artifact is returned as an opaque dictionary.

Stable public errors cover not found, invalid commands, identity conflicts,
idempotency conflicts, settled conflicts, artifact conflicts/invalidity/
unavailability, unavailable artifact root, and unavailable product database.
Messages and bounded completion events contain no path, SQL, source returns,
weights, rationale, notes, warnings, or full payload.

The checked-in OpenAPI snapshot and generated TypeScript contracts include the
new explicit requests, responses, unions, and nullable values. Sprint 174 adds
no Next.js route, page, form, component, CSS, message catalog, or Web test
behavior.

## Governance Boundary

`approved`, `rejected`, and `deferred` remain human portfolio-review governance
evidence only. Approval does not mutate lifecycle state, approve a Paper Job,
create or fund a Paper Account, allocate capital, create positions or orders,
simulate fills, start a worker, or authorize a broker or live execution.

## Verification

Deterministic tests cover hashed paths, containment and root checks,
write-once/exact-reuse behavior, strict JSON reopen, recalculation, migration
shape and downgrade, record/repository behavior, create and decision
idempotency, rollback, concurrent settlement, API statuses and errors, OpenAPI,
and generated contract freshness.

Required repository gates are:

```text
uv run python scripts/check.py
uv run alembic heads
```

The expected one migration head is:

```text
0006_portfolio_reviews
```

No Docker build, pull, Compose startup, container startup, container smoke,
volume removal, broker, QMT, MiniQMT, private-edge, or external-network test is
part of Sprint 174 acceptance.

## Handoff

Milestone 30 remains In Progress. Sprint 175 — Founder Portfolio Decision Review
Web Workspace implementation is complete pending Founder review. Sprint 176
owns integration, isolated Demo evidence, and Founder acceptance hardening.
Sprint 177 owns closeout and the strict handoff to a separately authoritative
M31 Paper Account and ledger.
