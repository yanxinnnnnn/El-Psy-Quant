# Founder Feedback Register

## Purpose

This register records direct Founder feedback that governs Milestone 29 — Product
Feedback and Hardening.

It is not a market-research document. It does not claim external users,
conversion data, retention data, customer demand, or product analytics that do
not exist.

## Priority Scale

| Priority | Meaning |
|---|---|
| P0 | Blocks safe or understandable daily use. |
| P1 | Materially weakens product usability or trust. |
| P2 | Valuable improvement after core daily-use problems are solved. |

## Feedback Register

| ID | Feedback | Evidence / source | User impact | Priority | Target sprint | Measurable outcome | Non-goals / risks |
|---|---|---|---|---:|---:|---|---|
| F-001 | Add complete Simplified Chinese support and an explicit language switcher while preserving English. | Direct Founder request after local M28 Demo verification. | The current English-only interface is less natural for the Founder and prevents the product from being evaluated as a bilingual workspace. | P0 | S162 | Every Founder-facing workflow is complete in `en` and `zh-CN`; no missing catalog key produces mixed-language UI; active locale persists safely. | Do not translate raw IDs, transport fields, domain values, source artifacts, or financial calculations. |
| F-002 | Replace the current academic / older enterprise presentation with a modern product experience. | Direct Founder feedback after using the complete workspace. | The product works, but its identity and hierarchy do not yet communicate a focused AI-native decision workspace. | P1 | S163–S164 | A reviewed bilingual visual system is applied consistently; Overview becomes a decision-oriented workspace rather than a feature directory. | Do not turn the product into a marketing site, dense trading terminal, or autonomous recommendation engine. |
| F-003 | Make product errors explain the problem and the safe next action. | Founder usage feedback and existing bounded API error surfaces. | Generic or highly technical failures slow local operation and require code knowledge. | P1 | S166 | Supported failures show localized explanation, stable error code, request ID when available, and bounded recovery guidance. | Do not expose internal exceptions, filesystem paths, credentials, or stack traces. |
| F-004 | Make idempotency, retry, recovery, and job-state conflicts easier to understand. | Existing Paper Job workflow and Founder daily-use target. | Correct backend semantics exist, but operational intent and failure recovery still require expert understanding. | P1 | S165 | The Founder can identify safe replay, retry, recovery, and conflict actions without weakening backend rules. | Do not claim exactly-once execution or add hidden automatic retries. |
| F-005 | Harden migrations, Compose startup, upgrades, and local reset behavior for routine use. | M28 local startup and Demo verification workflow. | Daily use depends on predictable startup, storage isolation, migration state, and safe reset instructions. | P1 | S167 | Standard and Demo startup, upgrade, verification, stop, and reset paths are deterministic, documented, and covered by tests. | Do not introduce cloud deployment, Kubernetes, or distributed infrastructure. |
| F-006 | Keep the complete Strategy-to-Human-Decision journey visible and understandable. | Founder successfully verified the S160 Demo journey. | The end-to-end workflow is a core product strength and should remain the product’s organizing narrative. | P0 | S162–S164 | Both locales preserve the full journey and each stage offers an explicit user-chosen next action. | Do not falsely connect unrelated real records or infer recommendations. |
| F-007 | Preserve unmistakable standard versus Demo identity and storage isolation. | M28 Founder verification and S160 trust boundary. | Confusing Demo evidence with real evidence would damage product trust. | P0 | All M29 | Demo identity remains persistent and accessible; storage and reset paths remain isolated. | No shared default volume, implicit seed, or browser-triggered installation. |
| F-008 | Preserve raw evidence, audit identifiers, and explicit human control during the experience refresh. | Existing M20–M28 authority model. | Product polish must not hide the facts needed for governance and audit. | P0 | All M29 | Raw domain values remain available; proposals remain non-executing; review remains explicit evidence. | Do not replace domain truth with localized or visual approximations. |
| F-009 | Improve Overview so it answers what needs attention and what can be done next. | Founder product-experience feedback and current feature-directory Overview. | The Founder must manually infer workspace health, recent activity, and workflow continuation. | P1 | S164 | Overview communicates mode, health/configuration, recent paper activity, bounded attention items, and user-chosen next actions. | No strategy ranking, profitability recommendation, automatic approval, or capital allocation. |

## Preserved Strengths

Milestone 29 must preserve these M28 outcomes:

- local-first, Founder-only operation;
- minimal paired authentication;
- fixed same-origin Web/API gateway;
- complete strategy, research, governance, paper, result, comparison, and
  lifecycle review journey;
- explicit loading, empty, unavailable, invalid, and failed states;
- isolated standard and Demo workspaces;
- file-authoritative completed artifacts;
- compact SQLite product and job state;
- explicit manual job and lifecycle controls; and
- complete repository quality gates.

## Product Success Boundary

M29 product success is not measured by:

- strategy profitability;
- alpha;
- Sharpe ratio improvement;
- approval rate;
- trading volume;
- live execution;
- external-user acquisition; or
- capital allocation.

M29 is successful when the existing product becomes bilingual, understandable,
modern, recoverable, and reliable enough for routine Founder use while preserving
all established authority and safety boundaries.
