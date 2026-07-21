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

## Manual Portfolio Review Inputs

Portfolio Reviews permit explicit composition from current public research-run
and evidence-manifest reads, but only bounded metadata and exact compatible
references are copied. There is no persisted public paper-comparison-summary
discovery contract, aligned-return import, inferred lifecycle relationship,
candidate recommendation, weight optimizer, automatic normalization, or default
decision outcome. The browser validates
input shape and displays entered weight totals but does not recalculate
concentration, overlap, correlation, behavior, drawdown, contribution, or
impact.

Unavailable overlap or correlation evidence remains unavailable with its raw
reason and affected component IDs. It is not zero. A portfolio-review approval
is governance evidence only and does not create holdings, allocate capital,
mutate lifecycle state, create an account, place an order, or execute.

## Stateless Lifecycle Review

Lifecycle proposals and human review records are synchronous, non-executing
responses. The page does not list past reviews, persist its in-session timeline,
derive a globally current lifecycle state, or apply a transition. Approval
evidence is not execution evidence.

## Manual Refresh

The workspace has no polling, scheduled refresh, automatic retry, WebSocket, or
live dashboard. Use the explicit refresh and retry actions, especially after a
paper Run response.

## Local Upgrade and Backup Limits

The product supports one forward Alembic chain to
`0006_portfolio_reviews` and a read-only Standard/Demo workspace
verifier. It does not provide automatic backup, rollback, downgrade, repair,
restore, retention, encryption/key management, cloud snapshots, or production
disaster recovery.

A complete Standard backup requires the backend to be stopped and the entire
`/data` set—SQLite plus research, evidence, and paper roots—to be copied
together. Copying only SQLite or copying it live is not a complete,
transactionally consistent workspace backup. Restore must be staged into a
new empty reviewed workspace first; never merge or overwrite an active
non-empty Standard volume. External backup storage security remains the
Founder's responsibility. Demo data should normally be reinstalled.

Committed dependency locks make reviewed versions reproducible but do not make
a cold image build offline. Uncached base images and package artifacts remain
external availability risks, and upstream image tags are not content-addressed.

## Presentation Localization Only

English and Simplified Chinese catalogs translate product-owned interface copy.
They do not translate backend messages, artifact contents, user-entered text,
raw IDs, status/lifecycle transport values, error codes, or audit values. A
localized number or timestamp is a display aid, not a recalculation or a
replacement for the adjacent raw representation. Unsupported or tampered locale
preferences fall back to English; there is no partial third-locale mode.

These limitations preserve the central product boundary: evidence informs a
human decision, and the human remains the final authority.
