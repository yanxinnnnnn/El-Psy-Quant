# Sprint 162 — Multilingual Foundation and Simplified Chinese Workspace

## Status

Implementation complete; Founder local bilingual browser acceptance and merge
remain pending.

Milestone 29 — Product Feedback and Hardening remains **In Progress**. Sprint
163 must not begin until Sprint 162 is merged and the Founder has accepted the
English and Simplified Chinese Standard/Demo journeys.

## Objective

Implement the approved `en` / `zh-CN` presentation layer across the complete
Founder workspace while preserving every existing route, transport contract,
domain authority, artifact payload, operational workflow, and human-control
boundary.

## Delivered Architecture

```text
request
  -> validated locale cookie
  -> supported Accept-Language hint
  -> English fallback
  -> statically loaded next-intl catalog
  -> shared Server/Client message context
```

- `next-intl` `4.13.2` is pinned.
- Supported locales are exactly `en` and `zh-CN`; English is the default and
  fallback.
- Existing routes remain unprefixed and unchanged.
- `el_psy_quant_locale` is an `HttpOnly`, `SameSite=Lax`, root-path, one-year
  local preference cookie changed through `POST /api/locale`.
- The persistent switcher exposes `English` and `简体中文`, updates the server
  request locale through `router.refresh()`, and performs no route navigation.
- Root metadata and `<html lang>` follow the resolved locale.
- Eleven static namespaces per locale cover common shell, navigation, Overview,
  strategies, research, evidence, Paper Jobs, Portfolio Records, comparisons,
  lifecycle review, and errors.
- Typed message keys and a deterministic validator prevent planned missing-key
  fallback or mixed-locale pages.

## Translation Coverage

The implementation translates:

- root metadata and document language;
- persistent shell, navigation, Standard/Demo identity, and first-run guidance;
- every existing top-level and detail workspace;
- headings, helper copy, tables, legends, fields, actions, confirmations, and
  manual refresh/retry/recovery guidance;
- loading, empty, unavailable, invalid, success, and error states;
- accessibility labels and hidden status announcements; and
- static frontend explanations for known backend error codes.

The approved S161 glossary governs core terminology. Product copy now resides in
the catalogs rather than page/component literals.

## Raw-Value and Authority Preservation

The workspace may show a localized label beside a raw value, for example:

```text
已失败  failed
```

It never translates or mutates raw IDs, routes, field names, statuses,
lifecycle states, outcomes, error codes, timestamps, schema versions, artifact
text, backend-provided text, user-entered text, quantitative values, ordering,
or duplicates. Locale-aware numbers, percentages, and timestamps are
display-only and retain a visible raw representation. No calculation was added
to the browser.

Backend, OpenAPI, generated transport, domain, artifact, lifecycle, Paper Job,
authentication, same-origin, and Standard/Demo isolation boundaries remain
unchanged.

## Deterministic Validation

`npm run messages:check` runs before the existing Web gate and rejects:

- unsupported or missing locale directories;
- missing or extra namespace files;
- malformed JSON and duplicate keys;
- non-object catalogs, arrays, non-string leaves, and empty messages;
- English/Simplified Chinese key drift; and
- invalid messages that cannot load through the public `next-intl` translator.

TypeScript message augmentation makes removed or misspelled static component
keys fail type checking. Tests cover locale precedence/fallback, cookie
validation, switcher accessibility, unprefixed route and repeated-query
preservation, English/Chinese rendering, stable raw values and error codes, and
unsaved Paper Job/Lifecycle form behavior.

## Preserved Boundaries

Sprint 162 adds no backend, OpenAPI, generated API type, database, migration,
artifact, Compose, authentication, financial, paper-execution, lifecycle,
broker, QMT, live-trading, capital, S163 visual-system, or S164 Dashboard change.

Docker build, startup, image pull, container smoke, and bilingual runtime
acceptance are intentionally Founder-owned under project policy.

## Verification

Required deterministic gate:

```text
uv run python scripts/check.py
```

The final PR records the exact test and production-build results. Founder local
Standard/Demo startup and full browser acceptance remain pending.

Final deterministic result:

- `uv run python scripts/check.py` passed;
- Python: 2,125 passed and 3 skipped;
- message catalogs: 2 locales across 11 namespaces validated;
- Web: 29 test files and 243 tests passed;
- Ruff, package import, CLI help, OpenAPI/generated-contract freshness, ESLint,
  and TypeScript all passed; and
- Next.js 16.2.10 production build compiled successfully and generated all 12
  page-data entries before finalizing the unprefixed dynamic route set.

Docker build/start, image pull, container startup, and container smoke were
intentionally not attempted under project policy.
