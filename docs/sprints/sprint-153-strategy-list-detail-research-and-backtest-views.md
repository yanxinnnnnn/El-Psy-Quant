# Sprint 153 — Strategy List, Detail, Research, and Backtest Views

## Status

Complete.

## Objective

Deliver the first Founder-facing business workspace in Milestone 28 by exposing
the existing read-only strategy catalog and configured research-run inspection
APIs through focused, accessible Web views.

## Delivered Routes

```text
/strategies
/strategies/[strategyName]
/research-runs
/research-runs/[experimentSlug]/[runId]
```

The strategy list preserves backend order and links exact strategy names to
read-only detail pages. Strategy detail shows backend-provided descriptions and
descriptive parameter metadata without editable controls or duplicated domain
validation.

The research list preserves backend order and shows configured manifest identity,
strategy, data source, and symbols. Research detail shows manifest and metrics
schema versions, parameters, evaluation settings, bounded artifact references,
and every saved per-symbol metric field returned by the API.

All four route families remain inside the Founder workspace shell during loading,
empty, unavailable, invalid, and not-found states. Meaningful failures include a
manual retry and bounded request ID when available. Detail failures also include
a safe route-appropriate back link.

## Research Artifact Configuration

Research inspection requires the FastAPI server setting:

```powershell
$env:EL_PSY_QUANT_RESEARCH_ARTIFACT_ROOT="C:\path\to\experiment-outputs"
uv run uvicorn el_psy_quant.api.app:app --host 127.0.0.1 --port 8000
```

A configured readable root containing no supported runs is a successful empty
state. An unset, missing, unreadable, or otherwise unavailable root is a bounded
`research_artifact_root_unavailable` failure. A malformed supported artifact is
a bounded `research_artifact_invalid` failure. The UI does not convert either
failure into an empty list and never displays the configured root.

## Metric and Artifact Authority

The Web layer displays saved metric values returned by the existing detail API.
It does not recompute returns, drawdowns, CAGR, volatility, Sharpe ratio, or any
other financial value. It does not aggregate, compare, rank, score, grade, or
recommend strategies or runs. Percentage and number rendering is presentation
formatting only, API row order is preserved, and nullable annualized metrics are
shown as `Not available`.

Artifact references are API-supplied bounded strings displayed as read-only text.
They are not file links, download links, arbitrary URLs, or filesystem helpers.
There is no chart because the current endpoint exposes no authoritative time
series; no equity curve or return series is reconstructed.

## Client and Transport Boundary

The endpoint-specific client capabilities are:

```text
fetchStrategies
fetchStrategyDetail
fetchResearchRuns
fetchResearchRunDetail
```

Their success types derive from the checked-in generated OpenAPI paths. Dynamic
path segments are encoded independently, lightweight runtime checks validate
transport shape only, and stable backend envelopes remain bounded
`ApiClientError` values with request IDs. Network failures, malformed JSON,
unexpected payloads, and non-envelope errors remain sanitized.

The browser continues to call only:

```text
/api/backend/api/v1/...
```

The unchanged Next.js rewrite forwards that fixed same-origin boundary to the
loopback FastAPI origin. No route handler, BFF domain layer, CORS change, retry,
polling, cache, persistence, browser filesystem access, SQLite access, or Python
import was added. The generated OpenAPI artifacts did not change because no
backend contract correction was necessary.

## Navigation and Accessibility

Overview and Strategies/Research are the only enabled workspace destinations.
Only the matching route family is marked current. Governance and Reports through
Lifecycle Review remain unavailable and have no placeholder routes. A reusable
section navigation links Strategies and Research runs.

The views use logical headings, labeled navigation, semantic lists, definition
lists and tables, visible focus treatment, live loading announcements, bounded
alerts, meaningful links, table captions, and contained horizontal scrolling for
wide tables on narrow screens.

## Verification

Focused deterministic frontend coverage verifies:

- route-family navigation and future unavailable destinations
- strategy list loading, success, empty, failure, and retry
- strategy detail success and bounded not-found behavior
- research list success, empty, unavailable/invalid failure, and retry
- research detail rendering of every saved metric field and nullable values
- fixed same-origin endpoint paths and dynamic segment encoding
- generated success-type consumption
- stable error envelopes, request IDs, malformed payloads, and network failures
- the unchanged narrow rewrite boundary
- backend-independent tests and production build

The authoritative repository gate remains:

```text
npm --prefix web ci
uv run python scripts/check.py
```

## Preserved Scope

Sprint 153 added no research execution, parameter editing, metric computation,
chart, artifact download or mutation, governance/report page, paper-job control,
portfolio record, comparison, lifecycle action, authentication, Docker Compose,
broker, QMT, live, real-money, distributed, or S154–S159 behavior.

## Next Sprint

```text
Sprint 154 — Governance Evidence and Report Artifact Views
```
