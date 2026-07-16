# Sprint 163 — Modern Visual System Foundation

## Status

Implementation complete; Founder local Standard/Demo rendered visual acceptance
and the merge decision remain pending.

Milestone 29 — Product Feedback and Hardening remains **In Progress**. Sprint
164 becomes next only after this sprint is accepted and merged.

## Objective

Establish one modern, calm, precise, accessible, bilingual, audit-friendly
visual system across every existing Founder Web route without changing product
behavior, information architecture, transport contracts, financial authority,
or human-control semantics.

## Delivered visual foundation

- one exact semantic token system for color, typography, spacing, radius,
  border, elevation, control height, focus, motion, content width, shell
  dimensions, and responsive thresholds;
- a Windows/macOS/Simplified-Chinese-safe system sans stack and a bounded
  monospace stack, with no downloaded fonts;
- a solid modern workspace header, responsive navigation, visible skip link,
  persistent language switcher, and explicit Standard/Paper identity;
- persistent localized Demo identity and disposable-data warning on every route;
- standardized action, link, card, panel, status, notice, empty/error/loading,
  table, form, disclosure, raw-value, audit, and workflow-step contracts; and
- shared status presentation that pairs localized meaning with authoritative raw
  values and treats unknown values neutrally.

The exact implementation reference is:

```text
docs/product/visual-system.md
```

## Complete route and state coverage

The shared shell and class contracts cover:

```text
/
/strategies
/strategies/[strategyName]
/research-runs
/research-runs/[experimentSlug]/[runId]
/evidence-manifests
/evidence-manifests/[manifestType]/[artifactKey]
/paper-jobs
/paper-jobs/new
/paper-jobs/[jobId]
/portfolio-records
/portfolio-records/[jobId]
/comparisons
/lifecycle-review
```

Coverage includes both locales and modes; list/detail/form/table/timeline views;
loading, empty, unavailable, invalid, error, conflict, success, pending, and
partial-failure surfaces; long IDs and raw values; ordered duplicate comparison
records; Paper Job controls; and non-executing lifecycle proposal/review flows.
No legacy route-specific theme remains.

## Preserved behavior and authority

Sprint 163 changes only presentation markup, shared status presentation, and
CSS. It preserves:

- all routes, query parameters, repeated ordered `job_id` values, locale-cookie
  behavior, language switching, and unsaved Paper Job/Lifecycle form state;
- backend, OpenAPI, generated API, database, migration, domain, artifact,
  authentication, same-origin, and Standard/Demo isolation contracts;
- financial, Paper Job, lifecycle, review, confirmation, and human-control
  behavior; and
- raw IDs, states, outcomes, codes, timestamps, versions, text, quantitative
  values, API order, and duplicates.

Operational completion styling is not a profitability claim. Human approval is
informational governance evidence, not execution. A lifecycle proposal is
recorded with an informational treatment and an explicit non-executing label.

## Responsive and accessibility contract

- representative widths: `360px`, `768px`, and `1280px+`;
- no global narrow-screen horizontal overflow; tables/navigation own bounded
  scrolling;
- single-column form and repeatable-row collapse where required;
- visible Standard/Demo identity and language switching at narrow widths;
- semantic headings, landmarks, captions, fieldsets, legends, labels, alerts,
  status regions, and accessible disclosures;
- three-pixel focus indication, legible disabled controls, text-plus-color state,
  and no hover-only information; and
- deterministic `prefers-reduced-motion` behavior.

## Deterministic verification

Meaning-focused tests cover semantic token ownership, absence of independent
legacy value ownership, system-font direction, action/state/disclosure
contracts, responsive thresholds, reduced motion, safe table/raw-value
behavior, operational status variants, unknown raw state preservation,
Standard/Demo identity, and both locale presentations. Existing regression
coverage continues to verify routes, ordered queries, locale state, form state,
commands, transport values, errors, and complete production build behavior.

Required final gate:

```text
uv run python scripts/check.py
```

Final deterministic result:

- `uv run python scripts/check.py` passed;
- Python: 2,125 passed and 3 skipped;
- message catalogs: 2 locales across 11 namespaces validated;
- Web: 31 test files and 263 tests passed;
- Ruff, package import, CLI help, OpenAPI/generated-contract freshness, ESLint,
  and TypeScript all passed; and
- Next.js 16.2.10 production build compiled successfully and generated all 12
  page-data entries before finalizing the complete unprefixed dynamic route set.

Docker image build/pull, Compose startup, container startup, and container smoke
verification were intentionally not attempted under project policy.

## Founder acceptance

The Founder owns local Standard/Demo rendered acceptance. Follow the checklist
in `docs/product/visual-system.md` and
`docs/founder-mvp-local-operations.md`, covering both locales, representative
viewport widths, every route, available state surfaces, long raw values,
keyboard flow, and unchanged command semantics.

## Roadmap handoff

```text
S161 Complete
S162 Complete
S163 Implementation complete; Founder visual acceptance remains
S164 Next only after S163 Founder acceptance and merge
M29  In Progress
```

No S164 Dashboard aggregation, information-architecture refresh, chart,
ranking, recommendation, financial calculation, backend endpoint, or product
behavior was added.
