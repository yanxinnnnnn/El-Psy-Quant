# Founder Feedback Register

## Purpose

This register records direct Founder feedback that governed Milestone 29 —
Product Feedback and Hardening.

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
| F-001 | Add complete Simplified Chinese support and an explicit language switcher while preserving English. | Direct Founder request after local M28 Demo verification. | The English-only interface was less natural for the Founder and prevented bilingual product evaluation. | P0 | S162 | Every workflow is complete in `en` and `zh-CN`; no missing catalog key produces mixed-language UI; locale persists safely. | Do not translate raw IDs, transport fields, domain values, source artifacts, or financial calculations. |
| F-002 | Replace the academic / older enterprise presentation with a modern product experience. | Direct Founder feedback after using the complete workspace. | The product worked but did not yet communicate a focused AI-native decision workspace. | P1 | S163–S164 | A reviewed bilingual visual system is applied consistently; Overview becomes decision-oriented rather than a feature directory. | Do not create a marketing site, dense trading terminal, or autonomous recommendation engine. |
| F-003 | Make product errors explain the problem and the safe next action. | Founder usage feedback and existing bounded API error surfaces. | Generic or highly technical failures slowed local operation and required code knowledge. | P1 | S166 | Supported failures show localized explanation, stable error code, request ID when available, and bounded recovery guidance. | Do not expose internal exceptions, filesystem paths, credentials, or stack traces. |
| F-004 | Make idempotency, retry, recovery, and job-state conflicts easier to understand. | Existing Paper Job workflow and Founder daily-use target. | Correct backend semantics existed, but operational intent and recovery still required expert understanding. | P1 | S165 | The Founder can distinguish safe replay, Retry, Recover, and conflict handling without weakening backend rules. | Do not claim exactly-once execution or add hidden automatic retries. |
| F-005 | Harden migrations, Compose startup, upgrades, and local reset behavior for routine use. | M28 local startup and Demo verification workflow. | Daily use depended on predictable startup, storage isolation, migration state, and safe reset instructions. | P1 | S167 | Standard and Demo startup, upgrade, verification, stop, and reset paths are deterministic, documented, and tested. | Do not introduce cloud deployment, Kubernetes, or distributed infrastructure. |
| F-006 | Keep the complete Strategy-to-Human-Decision journey visible and understandable. | Founder successfully verified the S160 Demo journey. | The end-to-end workflow is a core product strength and must remain the organizing narrative. | P0 | S162–S164 | Both locales preserve the full journey and each stage offers an explicit user-chosen next action. | Do not falsely connect unrelated real records or infer recommendations. |
| F-007 | Preserve unmistakable Standard versus Demo identity and storage isolation. | M28 Founder verification and S160 trust boundary. | Confusing Demo evidence with real evidence would damage product trust. | P0 | All M29 | Demo identity remains persistent and accessible; storage and reset paths remain isolated. | No shared default volume, implicit seed, or browser-triggered installation. |
| F-008 | Preserve raw evidence, audit identifiers, and explicit human control during the experience refresh. | Existing M20–M28 authority model. | Product polish must not hide facts needed for governance and audit. | P0 | All M29 | Raw domain values remain available; proposals remain non-executing; review remains explicit evidence. | Do not replace domain truth with localized or visual approximations. |
| F-009 | Improve Overview so it answers what needs attention and what can be done next. | Founder product-experience feedback and the original feature-directory Overview. | The Founder had to infer workspace health, recent activity, and workflow continuation manually. | P1 | S164 | Overview communicates mode, readiness, recent Paper activity, bounded attention, and user-chosen next actions. | No strategy ranking, profitability recommendation, automatic approval, or capital allocation. |

## M29 Closeout Outcome

| ID | Closeout status | Delivered outcome |
|---|---|---|
| F-001 | Complete | Exact static `en` and `zh-CN` catalogs, validated locale resolution, accessible route-preserving switcher, localized metadata/copy, and raw-value preservation. |
| F-002 | Complete | One modern bilingual-safe visual system and responsive shell across every current route; Overview now uses bounded decision navigation. |
| F-003 | Complete | Complete stable error inventory, semantic categories, localized explanation/recovery, raw technical audit detail, request correlation, and sanitized local product events. |
| F-004 | Complete | Explicit `created`/`replayed`, Run claim, state conflicts, Retry, Recover, collision, settled-evidence, and manual-control presentation without hidden automation. |
| F-005 | Complete | Exact migration chain, historical upgrade matrix, fail-closed startup, read-only workspace verification, locked build/runtime inputs, isolated volumes, bilingual non-mutating smoke, and backup/reset runbooks. |
| F-006 | Complete | Strategy-to-Human-Decision remains the product journey in both locales and both workspace modes. |
| F-007 | Complete | Persistent localized Demo identity, separate Compose projects and named volumes, Standard preflight, Demo-only reset, and verified return to Standard. |
| F-008 | Complete | Raw IDs, states, timestamps, codes, quantitative values, source order, duplicates, artifact text, and explicit human controls remain visible and authoritative. |
| F-009 | Complete | Dashboard communicates mode, readiness, partial failures, operational attention, recent Paper activity, explicit comparison continuation, and safe navigation without ranking or recommendation. |

The closeout status means the direct M29 feedback was addressed within the
approved product boundary. It does not imply external-user validation, customer
analytics, profitability, live-trading readiness, or market demand.

## Preserved Strengths

Milestone 29 preserved these M28 outcomes:

- local-first, Founder-only operation;
- minimal paired authentication;
- fixed same-origin Web/API gateway;
- complete strategy, research, governance, paper, result, comparison, and
  lifecycle review journey;
- explicit loading, empty, unavailable, invalid, conflict, and failed states;
- isolated Standard and Demo workspaces;
- file-authoritative completed artifacts;
- compact SQLite product and Paper Job state;
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

M29 is successful because the existing product became bilingual,
understandable, modern, recoverable, and reliable enough for routine Founder use
while preserving all established authority and safety boundaries.

## Handoff

The remaining limitations now move to the approved Paper Trading runtime roadmap:

```text
docs/strategy/paper-trading-runtime-roadmap.md
```

M30 begins portfolio-level decision review. M31–M36 then build the durable
account, market session, strategy-to-order, execution simulator, runtime, and
multi-day operations needed for genuine Paper Trading.
