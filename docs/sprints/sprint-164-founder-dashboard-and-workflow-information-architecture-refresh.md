# Sprint 164 — Founder Dashboard and Workflow Information Architecture Refresh

## Status

**Implementation complete; Founder local Standard/Demo Dashboard acceptance
remains pending.**

Milestone 29 remains **In Progress**. Sprints 161, 162, and 163 are complete.
Sprint 165 becomes next only after this sprint is accepted and merged.

## Objective

Replace the Overview feature directory with a bounded Founder
decision-navigation Dashboard that answers:

```text
What workspace am I in?
Is the product healthy and configured?
What recent Paper Job activity exists?
Which explicit workflow conditions may need human attention?
What safe workflow action can I choose next?
```

The Dashboard uses the Sprint 163 visual system and existing backend authority.
It does not become a profitability surface, recommendation engine, command
console, live terminal, or independent lifecycle authority.

## Implemented Architecture

### Existing endpoint composition

The Web application composes:

```text
GET /api/v1/demo-workspace
GET /api/v1/health
GET /api/v1/research-runs
GET /api/v1/evidence-manifests
GET /api/v1/paper-jobs?limit=8
```

No aggregate backend endpoint was required. No OpenAPI, generated TypeScript,
database, migration, domain, artifact, authentication, or same-origin gateway
contract changed.

The workspace shell owns one Demo descriptor request and shares its bounded
state with Overview. The Dashboard independently owns health, research,
evidence, and Paper Job list resources. Requests may run concurrently. Existing
sequence guards prevent stale responses from overwriting newer explicit
refreshes.

There is:

- no background polling;
- no Dashboard mutation;
- no global client cache;
- no local-storage persistence;
- no browser financial calculation; and
- no duplicate command or Strict Mode mutation path.

## Dashboard Regions

### Workspace identity

- distinguishes Standard and Demo through the existing descriptor behavior;
- keeps active locale and authenticated local-Founder framing visible;
- shows Demo display/dataset identity from the descriptor;
- retains the persistent localized disposable-example warning; and
- never hardcodes Demo record identities.

### Readiness and configuration

- labels `/health` as API process health only;
- reports research, evidence, and product-database sources separately;
- distinguishes loading, healthy-empty, populated, invalid, unavailable, API
  unreachable, and partially available;
- never labels the aggregate ready when a required dependency failed;
- preserves stable code, sanitized backend detail, request ID, localized
  explanation, bounded recovery, and individual retry; and
- leaves independent successful sources visible during partial failure;
- preserves the last settled success count/request identity or failure
  code/request identity/detail/guidance while that source refreshes; and
- presents refresh or retry progress separately with the source action visible
  and disabled until the new outcome replaces the retained evidence.

### Human attention

The implemented allow-list contains only:

- queued Paper Job awaiting an explicit detail-page Run decision;
- failed Paper Job available for inspection;
- running or interrupted attempt available through the existing manual detail
  workflow;
- succeeded Paper Job with `result_available=true`;
- configured healthy workspace with no research or evidence; and
- unavailable or invalid product dependency.

Attention is operational workflow attention. It is not strategy quality,
profitability, approval, capital allocation, or live-trading readiness.

The lifecycle API has no durable GET/list/current-state contract. Overview does
not claim persistent pending lifecycle reviews and stores no browser-owned
lifecycle authority.

### Recent Paper Job activity

The bounded eight-record view:

- preserves backend order and duplicates;
- preserves exact job ID and run ID;
- pairs localized job/attempt status with raw transport values;
- shows submitted and updated timestamps with raw UTC;
- shows latest attempt identity/status where available;
- uses backend `result_available` without inference;
- links to the exact Paper Job and Portfolio Record routes; and
- links to the complete Paper Job list.

It provides no Run, Retry, Recover, Cancel, or submit command.

### Results and comparison continuation

- candidates exist only when `result_available=true`;
- exact Portfolio Record inspection remains available;
- checkboxes make selection explicit and keyboard-operable;
- selection order is the user's action order;
- duplicate backend rows remain visible in exact source order;
- only two to four distinct nonblank job IDs may be selected;
- a duplicate row cannot add an already selected ID;
- a fifth distinct selection is disabled until another ID is deselected;
- successful refresh removes missing, unavailable, blank, or accidental
  duplicate selections while preserving remaining click order;
- the Comparison URL uses repeated ordered `job_id` parameters; and
- the link is enabled only when the existing shared Comparison validator accepts
  the selection; selection remains component-local and side-effect free.

Nothing is auto-selected, ranked, scored, recommended, declared a winner, or
financially recomputed.

### Research and governance evidence

Research and evidence remain separate independently stateful regions.

- each preserves endpoint order and duplicates;
- research preserves exact experiment slug and run ID;
- evidence preserves its optional presentation label while always showing the
  exact raw manifest ID, schema version, manifest type, artifact key, and
  reference count;
- because the list response has no schema field, the at-most-five visible cards
  use the existing exact manifest-detail read for raw `schema_version`; loading
  or failed detail reads remain bounded and retryable without hiding the list
  record;
- each links to exact existing detail routes;
- each has separate loading, empty, invalid, unavailable, and retry behavior;
  and
- neither participates in a fabricated unified chronology.

The Dashboard bounds each source entry list to five records and links to the
complete source list.

### Guided workflow continuation

Demo mode uses only descriptor values for:

- canonical strategy;
- research run;
- evidence manifests;
- Paper Jobs and Portfolio Records;
- comparison candidate order;
- lifecycle proposal example;
- human-decision evidence identity; and
- Paper Job submission example identity.

Standard mode provides generic browse choices and does not infer a current next
record or connect independent records.

### Technical detail and recovery

The technical region names each endpoint owner and exposes available request
identity. Every source has an explicit manual refresh. The region documents the
no-polling, no-cache, no-persistence, no-aggregate-API, and no-command boundary.
During a pending refresh, technical detail and operational attention continue to
reflect the same last settled evidence as readiness, so a known dependency
failure cannot disappear or become healthy before the replacement read settles.

## Bilingual, Responsive, and Accessible Behavior

- `en` and `zh-CN` catalogs retain exact namespace/key parity;
- Dashboard copy follows the approved localization glossary;
- raw IDs, statuses, error codes, request IDs, UTC timestamps, schema values,
  order, duplicates, artifact/user text, and quantitative truth remain
  unchanged;
- region headings and page structure are semantic;
- loading uses live status meaning and failures use alerts;
- retry controls and comparison selection have localized accessible names;
- status is text plus color and includes raw values where authoritative;
- focus and reduced-motion behavior remain owned by the Sprint 163 system;
- the desktop two-column grid becomes one column at tablet/narrow widths;
- cards and controls have no fixed text height; and
- long IDs and Chinese copy wrap without forcing global page overflow.

Representative Founder acceptance widths are approximately `360px`, `768px`,
and `1280px+`.

## Deterministic Coverage

Focused tests cover:

- Standard and Demo identity;
- process health versus product readiness;
- populated, healthy-empty, unavailable, invalid, and partial availability;
- raw stable code and request ID;
- independent source retry;
- deferred error retry and success refresh with retained settled evidence;
- stale-response suppression;
- manual refresh without polling;
- Paper Job backend order and duplicates;
- allow-listed attention only;
- localized/raw job and attempt status;
- neutral unknown future status presentation;
- exact job/result links;
- backend result availability;
- explicit ordered repeated comparison parameters for two to four distinct
  nonblank job IDs;
- duplicate-row, maximum-selection, deselection, and successful-refresh
  reconciliation behavior;
- no auto-selection, command controls, ranking, winner, recommendation, or
  browser calculation;
- separate research/evidence ordering and duplicates, including complete raw
  Evidence Manifest audit identity in both locales;
- generic Standard workflow;
- descriptor-driven Demo workflow without hardcoded identities;
- English and Simplified Chinese;
- semantic headings, alerts, retry names, fieldset/checkbox behavior, and
  keyboard-operable links; and
- existing locale, route/query, form state, authentication, gateway,
  generated-contract, production-build, and workflow regressions through the
  full repository gate.

## Verification Boundary

Codex must run:

```text
uv run python scripts/check.py
```

The final PR records the exact test count and production-build result.

Codex intentionally does not run:

```text
docker compose build
docker compose up
Docker image pulls
container startup
container smoke tests
```

Founder local Standard/Demo Dashboard runtime acceptance remains pending under
project policy.

## Founder Acceptance Checklist

In Standard and Demo, in both locales and at representative narrow, tablet, and
desktop widths:

1. Confirm shell and Dashboard workspace identities agree.
2. Confirm Demo identities and exact links come from the descriptor.
3. Confirm health, empty, invalid, unavailable, and partial readiness meaning.
4. Confirm one failed region does not erase successful regions.
5. Confirm stable error code, sanitized detail, request ID, localized guidance,
   and individual retry.
6. Confirm refresh/retry progress keeps prior settled evidence visible across
   readiness, attention, and technical detail, disables the pending source
   action, and replaces the evidence only when the read settles.
7. Confirm no polling and no command request occurs on refresh.
8. Confirm Paper Job order, duplicates, IDs, raw/localized statuses, attempt
   summary, timestamps, result authority, and exact links.
9. Confirm only allow-listed operational attention appears.
10. Confirm explicit result selection and exact repeated ordered comparison
   parameters.
11. Confirm research and evidence remain separate and source ordered.
12. Confirm Standard guidance does not connect records and Demo guidance
    preserves the exact descriptor journey.
13. Confirm no Dashboard command, ranking, recommendation, winner, profitability
    claim, or durable lifecycle pending-review claim.
14. Confirm keyboard focus, named regions/actions, alerts, disclosures, wrapping,
    and no global horizontal page overflow.

## Known Limitations and S165 Handoff

- readiness remains frontend composition of independent endpoint truth;
- there is no durable lifecycle read model;
- there is no unified cross-source chronology;
- deterministic layout contracts do not replace rendered browser review; and
- Founder local Dashboard acceptance remains the final pre-merge gate.

Sprint 165 owns reliability, idempotency, and Paper Job recovery hardening only
after Sprint 164 is accepted and merged. This sprint does not begin S165 work.
