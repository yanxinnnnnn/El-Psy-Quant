# Getting Started

Use this guide for your first review session in the Founder Workspace.

## Before You Begin

Confirm that:

- the local workspace has been started by its operator;
- you have the single Founder username and password;
- the intended research, evidence, and paper data are available locally; and
- you understand that this environment is for paper trading and review only.

For installation, storage, and startup operations, see the
[local operations guide](../founder-mvp-local-operations.md). Those tasks are
separate from the product workflow described here.

Before serving a fresh, upgraded, or restored workspace, the operator should
complete the explicit read-only `verify-local-workspace` check. Existing
Standard upgrades require a cold complete-`/data` backup first; see the
[install, upgrade, and recovery runbook](../operations/local-install-upgrade-and-recovery.md).

## Sign In

Open `http://127.0.0.1:3000` on the machine running El-Psy-Quant. Enter the
Founder credentials in the browser's sign-in prompt.

The current sign-in protects one local Founder workspace. It is not a
multi-user account system. On a shared machine, close all browser windows for
this local site when you finish because browsers may retain the credentials for
the session.

## Use the Founder Dashboard

Overview is a bounded Founder decision-navigation Dashboard. It identifies the
workspace and active language, reports API process health separately from
research, evidence, and product-database readiness, shows allow-listed
operational attention, preserves a bounded backend-ordered Paper Job view, and
offers safe read-only workflow continuation.

Each source loads and fails independently. If one source is unavailable or
invalid, successful regions remain visible and readiness says **Partially
available** rather than claiming the whole product is healthy. Use the failed
source's named retry action. Keep its raw error code and request ID when
reporting a problem. Refresh is explicit; Overview does not poll.

An empty page and an unavailable page mean different things:

- an empty state means the configured source was reached but contains no
  supported records;
- an unavailable or invalid state means the source could not be read safely.

Do not treat an unavailable evidence source as evidence that no records exist.

## Choose English or Simplified Chinese

Use the persistent **English** / **简体中文** control in the workspace header.
The selected language applies to the current unprefixed route and is remembered
on the same local origin for both Standard and Demo modes. Switching language
does not intentionally navigate, reorder repeated comparison `job_id` values,
submit a command, or clear an in-progress Paper Job or Lifecycle form.

Translated labels and explanations are presentation only. Raw strategy names,
run/job/reference IDs, statuses, lifecycle values, error codes, UTC timestamps,
artifact text, user-entered text, and quantitative values remain visible and
unchanged. When a localized date or number is shown, use its accompanying raw
value for exact audit comparison.

On a healthy new Standard Workspace, Overview reports configured-empty sources
separately and creates only the allow-listed no-research/evidence attention
condition. Generic browse actions do not claim that unrelated real records form
one chain. The browser does not seed data, initialize the database, run an
installer, or infer a current record.

## Choose Standard or Demo

Use the standard workspace for real local research, governance, and paper
artifacts. It starts clean and remains separate from examples.

Use the Demo Workspace only for a disposable first tour. Its header always says
**Demo Workspace** and warns that the data is example evidence, not real user
data. Overview provides exact links from the backend descriptor through the
Moving Average Crossover strategy, saved research and governance evidence, two
succeeded paper results, comparison, lifecycle review, and human decision
evidence. These identities are not guessed by the browser.

The Dashboard's result area uses only the backend `result_available` flag.
Select comparison candidates explicitly in the desired order; each choice
becomes one repeated `job_id` parameter, including a repeated ID if the source
contains duplicates. Overview never auto-selects, ranks, recommends, declares a
winner, or recalculates financial metrics. Paper Job Run, Retry, Recover,
Cancel, submission, and lifecycle commands remain on their existing exact
workspaces, never on Dashboard cards.

Standard and Demo use different storage volumes but the same loopback ports, so
an operator must stop one before starting the other. See the
[local operations guide](../founder-mvp-local-operations.md) for start, replay,
safe Demo reset, and return-to-standard commands.

The documented Demo reset removes only the isolated Demo project volume. There
is no supported Standard volume-reset helper. Protect real Standard data with a
cold complete-workspace backup before code/image upgrades.

## Learn the Navigation

- **Strategies and Research** contains built-in strategy definitions and saved
  research results.
- **Governance and Reports** contains evidence manifests and unresolved
  references.
- **Paper Runs** creates and controls durable local paper jobs.
- **Portfolio Records** opens authoritative results from succeeded jobs.
- **Comparisons** places two to four available results side by side.
- **Lifecycle Review** creates a non-executing proposal and records a separate
  human review response.

All refreshes are manual. The workspace does not poll in the background, so use
the page's **Refresh**, **Refresh status**, or retry action when you need newer
information.

## Your First Review

Begin with a strategy definition and its parameter metadata. Find saved research
that uses the intended strategy and confirm its data source, symbols, parameters,
evaluation settings, and metrics. Then inspect the relevant governance evidence
before preparing any paper job.

Continue through the complete [Founder workflow](founder-workflow.md). Keep a
written rationale for every conclusion, especially when evidence is incomplete,
conflicting, or unavailable.
