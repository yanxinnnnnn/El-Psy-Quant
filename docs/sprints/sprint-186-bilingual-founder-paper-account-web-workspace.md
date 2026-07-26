# Sprint 186 — Bilingual Founder Paper Account Web Workspace

## Status

Implementation complete / pending Founder review.

GitHub Issue #368 is the authoritative Sprint 186 implementation
specification. Sprint 186 reuses the merged Sprint 185 API and generated
TypeScript contracts without changing Python, financial authority, persistence,
migrations, OpenAPI, Demo behavior, or Docker/runtime behavior.

## Founder routes

The bilingual Founder workspace adds Paper Accounts after Portfolio Reviews and
owns exactly:

```text
/paper-accounts
/paper-accounts/new
/paper-accounts/[accountId]
```

Nested routes preserve the Paper Accounts active-navigation state.

## Generated-contract boundary

The Web API client derives every request and response type from the checked-in
generated S185 contracts and covers all ten versioned Paper Account operations.
Runtime guards validate complete nested account, projection, identity,
position, approved-review, event, posting, snapshot, and reconciliation
responses plus their durable identity and head-anchor bindings. Malformed
success responses fail closed as `api_response_invalid`.

The browser never reads SQLite, persistence models, domain objects, filesystem
artifacts, or legacy Paper artifacts. It does not calculate balances, available
cash, positions, aggregate cost basis, average unit cost, digests, lifecycle
eligibility, snapshot content, reconciliation status, PnL, or equity.

## List and creation

The list preserves backend order and duplicates and exposes explicit lifecycle
and page-size filters, manual refresh, and opaque keyset next/previous
navigation. Failed refreshes retain the last valid page.

Creation submits only explicit display name, three-letter base currency,
canonical initial-cash string, actor, and caller-owned `Idempotency-Key`.
Drafts survive validation and API failures. `201` creation and `200` exact
replay remain distinct and return explicit navigation to authoritative detail.

## Detail and ledger inspection

Detail renders the complete backend account and validated projection, including
raw lifecycle/projection states, exact cash strings, ordered positions,
display-only average cost and rounding flags, approved M30 evidence references,
versions, timestamps, IDs, and full digests.

The ledger timeline preserves contiguous backend sequence and page order. It
renders typed event detail, complete cash and position postings, effective and
recorded timestamps, actors, reasons, event/entry IDs, and full command, entry,
event, and chain digests. Pagination is explicit; there is no polling,
reordering, deduplication, replay, or browser balance reconstruction.

## Explicit operations

The detail workspace provides generated-contract forms for:

- cash movement;
- position adjustment;
- approved M30 evidence link;
- lifecycle freeze, reactivate, or close;
- immutable snapshot creation; and
- immutable reconciliation creation.

Every mutation uses the exact displayed backend account version. Snapshot and
reconciliation also use the exact displayed head event ID and chain digest.
The Founder supplies actor, reason, an explicit caller-owned idempotency key,
and operation-specific values. The browser never invents or rotates keys and
never retries automatically.

All lifecycle actions remain explicit with no default. Backend authority alone
decides lifecycle eligibility, available-cash sufficiency, position/cost-basis
invariants, approved M30 reference validity, concurrency, and reconciliation.
Conflicts preserve the loaded authority and complete operation draft.

Successful commands expose the returned authoritative event and account state
and require an explicit refresh to reload the full ledger. Successful snapshot
and reconciliation operations retain and display the complete immutable
returned evidence in-page. Neither operation repairs a projection or adds a
ledger event.

## Localization, errors, and accessibility

English and Simplified Chinese catalogs cover the complete workspace, all
seventeen stable Paper Account errors, statuses, operations, validation, and
authority boundaries. Raw transport values remain untranslated.

Forms use semantic fieldsets and labels, explicit no-default selections,
preserved drafts, duplicate-submit prevention, confirmation for account
creation and lifecycle actions, focused error alerts, keyboard-accessible
tables, and responsive layouts.

## Verification

Focused deterministic Web coverage includes:

- exact route, query, encoding, header, and request-body behavior for all ten
  endpoints;
- deep malformed-response rejection;
- deterministic account and ledger pagination;
- exact backend version/head-anchor use;
- created and replayed command handling;
- bilingual raw-value preservation;
- operation validation and conflict draft preservation; and
- immutable snapshot/reconciliation inspection.

Required repository verification remains:

```text
uv run python scripts/check.py
```

No Docker build, pull, Compose/container startup, container smoke, volume
operation, Demo reset, browser runtime acceptance, or Founder runtime acceptance
is part of Sprint 186.

## Handoff

Sprint 187 retains integration, isolated Demo behavior, upgrade/recovery
hardening, and Founder Standard/Demo and bilingual runtime acceptance. Sprint
186 adds no order/fill, market-data, strategy-runtime, execution, worker,
broker, PnL/equity, live, or real-money behavior.
