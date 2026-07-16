# Current Limitations

The Founder Workspace is intentionally narrow. Review these limits before using
its evidence in a decision.

## Local, Single-Founder Access

The workspace is designed for one local machine and one configured Founder
credential pair. It has no registration, user database, roles, password reset,
OAuth, multi-user review, or SaaS security model. It should remain bound to the
local machine.

## Demo Evidence Is Disposable

The opt-in Demo Workspace contains fixed example artifacts and records for a
guided product tour. It is visibly labeled, stored in a volume distinct from
the standard workspace, and must not be treated as real research, approval,
performance evidence, trading advice, or live readiness. Resetting Demo removes
only its isolated volume when the documented overlay command is used.

## Paper Trading Only

There is no live trading, broker connection, QMT or MiniQMT connection, capital
allocation, or browser-to-market path. Orders and fills shown in Portfolio
Records are paper artifacts, not broker confirmations.

## No Automated Strategy Selection

The workspace does not use AI or a scoring rule to select a winning strategy. It
does not rank research runs, guarantee returns, or claim that historical or
paper performance will continue. The Founder must evaluate assumptions, risk,
data quality, and missing evidence.

## Read-Only Research and Evidence

The Web workspace does not run research, edit strategy parameters, recompute
metrics, render report contents, download artifacts, or resolve evidence
references. Empty, unavailable, and invalid evidence states must be interpreted
differently.

## Incomplete Portfolio Valuation

Portfolio Records provide cash, quantities, orders, fills, summaries, and audit
facts. They do not provide market prices for open positions, total
marked-to-market equity, profit and loss, return, exposure, or equity-history
charts. The browser does not calculate missing values.

## Read-Only Comparisons

Comparisons show two to four backend results without cross-run calculations,
trade alignment, aggregation, ranking, recommendations, or a persisted
comparison decision. The Founder supplies the interpretation.

## Stateless Lifecycle Review

Lifecycle proposals and human review records are synchronous, non-executing
responses. The page does not list past reviews, persist its in-session timeline,
derive a globally current lifecycle state, or apply a transition. Approval
evidence is not execution evidence.

## Manual Refresh

The workspace has no polling, scheduled refresh, automatic retry, WebSocket, or
live dashboard. Use the explicit refresh and retry actions, especially after a
paper Run response.

## Presentation Localization Only

English and Simplified Chinese catalogs translate product-owned interface copy.
They do not translate backend messages, artifact contents, user-entered text,
raw IDs, status/lifecycle transport values, error codes, or audit values. A
localized number or timestamp is a display aid, not a recalculation or a
replacement for the adjacent raw representation. Unsupported or tampered locale
preferences fall back to English; there is no partial third-locale mode.

These limitations preserve the central product boundary: evidence informs a
human decision, and the human remains the final authority.
