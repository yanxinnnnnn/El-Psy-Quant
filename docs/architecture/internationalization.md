# Internationalization Architecture

## Decision Status

Approved planning decision for Sprint 162 — Multilingual Foundation and
Simplified Chinese Workspace.

This document defines the implementation boundary. It does not itself add a
runtime dependency or change Web behavior.

## Context

The M28 Founder workspace is English-only. The Founder requires complete
Simplified Chinese support and an explicit language switcher.

The product is currently:

- local-first;
- Founder-only;
- minimally authenticated;
- served from one local origin;
- not dependent on multilingual SEO;
- not a multi-user SaaS product; and
- built with the Next.js App Router.

The architecture must add bilingual product copy without changing domain,
transport, artifact, authentication, or storage authority.

## Decision Summary

```text
Supported locales: en, zh-CN
Default locale: en
Fallback locale: en
URL strategy: no locale prefix
Persistence: local cookie
First-use hint: supported Accept-Language value
Implementation direction: next-intl
Backend localization: none
```

## Supported Locales

| Locale | Product label | Role |
|---|---|---|
| `en` | English | Default and fallback locale. |
| `zh-CN` | 简体中文 | First additional complete product locale. |

Unsupported, missing, malformed, or tampered locale values resolve to `en`.
There is no partially supported locale state.

## Routing Decision

Existing application routes remain unchanged:

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

The product will not introduce `/en/...` or `/zh-CN/...` route segments in S162.

Reasons:

- the product does not require multilingual SEO;
- users do not need language-specific shareable public URLs;
- preserving routes avoids unnecessary churn across navigation, Demo descriptor
  links, query handling, tests, and same-origin behavior;
- locale is a display preference, not part of domain identity; and
- the local product should remain operationally simple.

A future hosted or multi-user product may revisit this decision through a new
architecture issue. S162 must not keep both prefixed and unprefixed routing modes.

## Locale Resolution

The approved resolution order is:

```text
valid saved locale cookie
  -> supported browser Accept-Language on first use
  -> en
```

### Cookie contract

Recommended name:

```text
el_psy_quant_locale
```

Allowed values:

```text
en
zh-CN
```

Requirements:

- same-site local product cookie;
- no credentials or authentication material;
- no database persistence;
- no dependency on Founder username;
- bounded value length and exact allow-list validation;
- available to the server-rendered root layout; and
- shared by standard and Demo modes on the same local origin.

The implementation issue must make the final `Secure`, `HttpOnly`, `SameSite`,
path, and lifetime decisions consistent with a local browser-readable language
preference. The cookie must not become a security token.

## Language Switcher

The switcher belongs in the persistent workspace shell.

It must:

- expose both language names in a form understandable from either locale;
- be keyboard and screen-reader accessible;
- preserve the current pathname;
- preserve query parameters, including ordered repeated comparison `job_id`
  values;
- avoid navigation to a locale-prefixed route;
- update server-rendered locale state safely;
- update `<html lang>`;
- work in standard and Demo modes; and
- never submit a paper or lifecycle command.

Changing locale should not intentionally clear in-memory form state. Because a
server refresh can remount Client Components, S162 must test the Paper Job and
Lifecycle forms explicitly. If preserving every arbitrary unsaved state is not
technically reliable, the implementation must choose a bounded client-side
locale update or clearly constrain which state is preserved rather than silently
losing user input.

## Library Decision

`next-intl` is the approved implementation direction for S162.

Why:

- supports Next.js App Router Server and Client Components;
- supports message namespaces and interpolation;
- supports locale-aware date and number presentation;
- avoids building a custom translation context and format layer;
- supports typed and testable catalog workflows; and
- can operate without locale-prefixed routes.

S162 must pin the dependency through the existing npm lockfile and verify that
installation and build remain deterministic. No dependency is added in S161.

## Server and Client Boundary

### Server Components

Server-rendered layouts, metadata, and Server Components resolve the locale from
the approved request context and load only the approved static catalog.

### Client Components

Client Components receive locale/message context from the root provider and use
static namespace/key lookups.

Rules:

- no component reads arbitrary translation JSON from the network;
- no browser access to artifact roots or Python modules;
- no dynamic import path derived from an untrusted cookie;
- no unvalidated API value is passed directly as a translation key; and
- locale resolution must be consistent between server render and hydration.

## Catalog Ownership

Recommended structure:

```text
web/messages/
  en/
    common.json
    navigation.json
    overview.json
    strategies.json
    research.json
    evidence.json
    paper-jobs.json
    portfolio-records.json
    comparisons.json
    lifecycle.json
    errors.json
  zh-CN/
    common.json
    navigation.json
    overview.json
    strategies.json
    research.json
    evidence.json
    paper-jobs.json
    portfolio-records.json
    comparisons.json
    lifecycle.json
    errors.json

web/src/i18n/
  config.ts
  request.ts
  messages.ts
```

The exact file split may be adjusted in S162, but these ownership rules are
fixed:

- English is the source and fallback catalog.
- Every approved English key has exactly one Simplified Chinese key.
- Key identity is stable and semantic, not copied English prose.
- Product copy is not embedded directly in components once migrated.
- Message files contain product copy, not domain records or fixture payloads.
- Interpolation variables are explicit and typed where practical.
- HTML-rich messages are exceptional and must not accept unsafe API HTML.
- Plural/select behavior is defined through the message format rather than
  string concatenation.

## Catalog Completeness

S162 must add a deterministic catalog check that fails CI when:

- locale key sets diverge;
- a required namespace is missing;
- a message has an invalid format;
- an unsupported locale directory exists;
- a duplicate or shadowed key is detected by the selected tooling; or
- a component uses a removed key.

Production must not silently render key names or partial English fallbacks on a
Simplified Chinese page. Unknown runtime errors may use a bounded fallback error
message, but planned product copy must be complete.

## Domain and Transport Preservation

The following remain raw and must not be translated or rewritten:

- strategy names and IDs;
- experiment slugs and run IDs;
- paper job, attempt, order, and transition record IDs;
- UUIDs, artifact keys, reference IDs, and idempotency keys;
- API routes and request/response field names;
- schema and record versions;
- paper-job statuses and lifecycle states as transport values;
- source artifact and user-entered text;
- error codes;
- raw UTC timestamps when used as audit evidence; and
- quantitative values and calculations.

The UI may add a localized explanation while preserving the raw value:

```text
已成功
succeeded
```

This pattern is especially appropriate for:

- paper-job status;
- lifecycle state;
- review outcome;
- error code;
- schema version; and
- audit timestamps.

The localized label is presentation. The raw value remains authoritative.

## Formatting Boundary

Locale formatting is display-only.

Allowed:

- localized date/time display derived from an API timestamp;
- localized decimal separators and grouping for presentation;
- localized percentage presentation using an existing raw value;
- localized labels for status and units; and
- explicit display of timezone context.

Prohibited:

- recalculating performance metrics;
- changing precision used for audit or persistence;
- interpreting timestamps without an explicit timezone;
- replacing the source UTC value when exact audit evidence matters;
- changing order, duplicates, or identity of API records; or
- applying currency assumptions not present in the authoritative response.

Where precision matters, display both a localized human-readable value and the
raw UTC or decimal representation through visible or progressively disclosed
audit detail.

## Error Localization

The backend remains responsible for:

- stable HTTP status;
- stable machine-readable error code;
- sanitized English contract message;
- request ID; and
- no internal exception leakage.

The Web layer may own a static approved mapping:

```text
error code
  -> localized title
  -> localized explanation
  -> bounded recovery guidance
```

Requirements:

- raw error code remains visible where useful;
- request ID remains visible;
- unknown errors receive a bounded generic localized message;
- backend message may be shown as technical detail when safe, but is not treated
  as a translation key;
- no stack trace, credential, path, SQL, or internal exception is exposed; and
- recovery guidance never suggests unsafe deletion or automatic lifecycle action.

## Metadata and Accessibility

S162 must localize:

- document title and description;
- navigation labels;
- headings and helper text;
- button text;
- form legends and field guidance;
- loading, empty, unavailable, invalid, success, and error states;
- confirmation dialog copy;
- retry and recovery guidance;
- `aria-label`, accessible names, and hidden explanatory text; and
- Demo Workspace identity and warning.

`<html lang>` must be exactly `en` or `zh-CN` for the active locale.

## Testing Contract

S162 coverage must include:

- locale validation and fallback;
- cookie resolution order;
- first-use browser-language resolution;
- switcher accessibility;
- route and query preservation;
- repeated comparison query parameter preservation;
- correct `<html lang>`;
- metadata localization;
- English and Chinese rendering for every top-level workspace;
- catalog key equality and format validity;
- no hardcoded fixture IDs introduced for localization;
- raw statuses/IDs remaining unchanged;
- stable error-code localization;
- unknown-error fallback;
- standard and Demo workspace copy;
- Paper Job and Lifecycle unsaved-form behavior during switching; and
- full production build and repository quality gate.

## Risks

| Risk | Mitigation |
|---|---|
| Partial translation creates mixed pages. | CI-enforced catalog completeness and full-workflow locale tests. |
| Server and client resolve different locales. | One validated request-level locale source and provider contract. |
| Switching language loses form state. | Explicit component tests and a bounded client/server switching design. |
| Dynamic API values become translation keys. | Static allow-listed mapping functions only. |
| Translation changes governance meaning. | Approved glossary and raw-value preservation. |
| Chinese typography breaks English-sized controls. | Internationalization before final visual tokens and bilingual layout tests. |
| New dependency weakens offline builds. | Pinned lockfile, deterministic install, and existing CI/build verification. |

## Rejected Alternatives

### Locale-prefixed routes

Rejected for the current local product because they add route and link churn
without SEO, sharing, or multi-user value.

### Backend-translated API responses

Rejected because it would mix presentation with transport contracts, weaken
stable error behavior, and complicate non-Web clients.

### Custom translation context

Rejected because the product needs Server Component, Client Component,
formatting, metadata, and catalog support that a maintained App Router library
already provides.

### Database-stored locale

Rejected because the product has no user database or account-preference model,
and locale is not product-domain state.

## Implementation Handoff

Sprint 162 may implement this decision. Any deviation in routing, supported
locales, backend responsibility, or raw-value preservation requires an explicit
Issue amendment or new architecture decision before code is merged.
