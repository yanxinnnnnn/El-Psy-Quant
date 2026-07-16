# Sprint 161 — Founder Feedback and Product Experience Architecture

## Status

Implementation complete; Founder review and merge remain pending.

Milestone 29 — Product Feedback and Hardening remains **In Progress**.

After this planning sprint is merged, the next sprint is:

```text
Sprint 162 — Multilingual Foundation and Simplified Chinese Workspace
```

## Objective

Convert the Founder’s real M28 usage feedback into explicit product and
architecture contracts for the remaining M29 implementation sprints.

This sprint is documentation-only. It does not add internationalization,
visual-system code, dashboard behavior, new API contracts, reliability changes,
or financial capability.

## Founder Feedback Used

The planning is based on direct Founder verification of the completed M28 Demo
Workspace and complete Strategy-to-Human-Decision journey.

The leading product gaps are:

1. the workspace needs complete Simplified Chinese support and an explicit
   language switcher;
2. the current presentation feels closer to an academic research portal or an
   older enterprise internal dashboard than a modern product;
3. daily-use failures, recovery, migrations, and local startup must become more
   actionable and dependable;
4. the explicit workflow, Demo isolation, artifact authority, and human-control
   model are strengths that must be preserved.

No external-user demand, market evidence, conversion data, or product analytics
is claimed.

## M29 Product Principles

1. **Bilingual completeness over partial translation.** English and Simplified
   Chinese must cover complete Founder workflows rather than selected labels.
2. **Decision clarity over dashboard density.** Primary actions and review state
   must be obvious without burying the Founder in widgets.
3. **Visible state over hidden automation.** Loading, empty, unavailable,
   failed, queued, running, and review states must remain explicit.
4. **Actionable recovery over generic errors.** Supported failures should state
   what happened, preserve stable technical identity, and explain the next safe
   action.
5. **Human judgment over automatic recommendation.** Workflow guidance may help
   the Founder continue, but must not rank strategies, infer approval, or
   allocate capital.
6. **Raw truth over presentation convenience.** Domain values, IDs, API values,
   artifact payloads, and audit timestamps remain authoritative.
7. **Local-first simplicity over distributed infrastructure.** M29 hardens one
   local modular monolith rather than introducing operational platforms.
8. **Accessibility and responsiveness in both languages.** English-only layout
   success is not sufficient.
9. **Real Founder feedback over speculative features.** M29 priorities must be
   traceable to observed product use or explicit Founder decisions.

## Bounded Success Measures

M29 success is verified through product behavior and deterministic tests rather
than new analytics infrastructure.

- Every Founder-facing workflow is complete in `en` and `zh-CN`.
- No supported locale exposes a mixed-language product page because a catalog
  key is missing.
- Locale switching preserves the active route and query parameters and does not
  intentionally reset in-memory form state.
- The document language, metadata, visible copy, and accessibility labels match
  the active locale.
- Raw domain identifiers and transport values remain visible and unchanged where
  audit or governance precision matters.
- Both locales pass component coverage, type checking, production build, and
  the complete repository quality gate.
- The Founder can identify standard versus Demo mode and choose an explicit next
  workflow action.
- Supported failures expose a stable error code, request ID where available,
  localized explanation, and bounded recovery guidance.
- Standard and Demo Compose paths remain isolated, reproducible, and safe to
  reset independently.
- No product success metric is based on profitability, alpha, approval rate, or
  trading performance.

## Architecture Decisions

### Internationalization

- Supported locales: `en` and `zh-CN`.
- English is the default and fallback locale.
- Existing routes remain unchanged; no `/en` or `/zh-CN` path prefix is added.
- Locale resolution order is saved cookie, supported browser language on first
  use, then English fallback.
- Locale persistence is browser/cookie based, not database or user-account based.
- `next-intl` is the approved S162 implementation direction for the Next.js App
  Router, subject to the exact dependency and lockfile change being reviewed in
  that sprint.
- Translation catalogs are static application-owned files. Dynamic API values
  are never used as unchecked translation keys.
- Backend error contracts remain stable and untranslated. The Web layer maps
  approved stable codes to localized explanations and recovery copy.
- Locale formatting is display-only. It must not recompute financial values.
- Exact raw UTC and decimal representations remain available where audit
  precision matters.

See:

```text
docs/architecture/internationalization.md
docs/product/localization-glossary.md
```

### Product Experience

The product direction is an **AI Quant Decision Workspace** rather than an
academic portal, marketing dashboard, or autonomous trading terminal.

The visual implementation must prioritize:

- neutral, modern product identity;
- clear hierarchy and restrained density;
- bilingual-safe typography and component sizing;
- readable forms and tables;
- strong workspace-mode and operational-state identity;
- progressive disclosure of raw IDs and audit detail;
- accessible loading, empty, unavailable, invalid, and failure states; and
- workflow choices without financial recommendation.

See:

```text
docs/product/product-experience-direction.md
```

### Founder Dashboard

The future Overview should answer:

```text
What workspace am I in?
Is the product configured and reachable?
What recent paper activity exists?
Which records may need explicit human attention?
What workflow action can I choose next?
```

The blueprint distinguishes information available through existing APIs from
concepts that would require a later explicit backend contract. S161 adds no API.

See:

```text
docs/product/founder-dashboard-information-architecture.md
```

## M29 Implementation Sequence

```text
S161 Founder Feedback and Product Experience Architecture
S162 Multilingual Foundation and Simplified Chinese Workspace
S163 Modern Visual System Foundation
S164 Founder Dashboard and Workflow Information Architecture Refresh
S165 Reliability, Idempotency, and Job Recovery Hardening
S166 Error Surface, Observability, and Audit Hardening
S167 Migration, Test, and Local Deployment Hardening
S168 Milestone 29 Closeout and M30 Handoff
```

Internationalization precedes the visual system so English and Chinese both
shape typography, spacing, component sizing, and content hierarchy. The visual
foundation precedes the broader Dashboard and information-architecture refresh.

See:

```text
docs/product/milestone-029-product-feedback-and-hardening-plan.md
```

## Preserved Authority

```text
Browser
  -> Next.js Founder workspace
  -> fixed same-origin /api/backend gateway
  -> versioned FastAPI API
  -> thin application services
  -> existing repositories, domain modules, and artifact readers
  -> isolated SQLite and authoritative artifact roots
```

- Domain modules remain authoritative for financial, paper, comparison,
  governance, and lifecycle rules.
- Completed artifact files remain payload authority.
- SQLite remains compact product metadata and operational state.
- Paper-job operational state remains separate from lifecycle governance.
- Lifecycle proposals remain non-executing.
- Human review remains explicit governance evidence.
- The browser never directly accesses SQLite, artifact roots, Python modules,
  QMT, MiniQMT, or a broker.
- Demo data remains isolated from real user data.
- Authentication and same-origin boundaries remain unchanged.

## Non-goals

Sprint 161 adds no runtime code, dependency, translation catalog, CSS, component,
API, OpenAPI, database, migration, Compose, authentication, Demo, job execution,
financial, lifecycle, broker, QMT, live-trading, or capital behavior.

## Verification

Required final verification:

```text
uv run python scripts/check.py
```

The implementation PR must remain documentation-only, be Ready for review, and
begin with `Closes #318`. The CTO must not merge it.
