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

## Sign In

Open `http://127.0.0.1:3000` on the machine running El-Psy-Quant. Enter the
Founder credentials in the browser's sign-in prompt.

The current sign-in protects one local Founder workspace. It is not a
multi-user account system. On a shared machine, close all browser windows for
this local site when you finish because browsers may retain the credentials for
the session.

## Check Workspace Availability

The Overview page shows whether the local application is reachable. If it is
unavailable, use the displayed retry action. A request ID may appear with an
error; keep it when reporting a problem.

An empty page and an unavailable page mean different things:

- an empty state means the configured source was reached but contains no
  supported records;
- an unavailable or invalid state means the source could not be read safely.

Do not treat an unavailable evidence source as evidence that no records exist.

On a healthy new standard workspace, Overview states that the application is
running but no workspace evidence has been loaded. It offers two operator-owned
paths: start the isolated Demo Workspace with the documented terminal commands,
or load/create real artifacts through the documented workflows. The browser
does not seed data, initialize the database, or run an installer.

## Choose Standard or Demo

Use the standard workspace for real local research, governance, and paper
artifacts. It starts clean and remains separate from examples.

Use the Demo Workspace only for a disposable first tour. Its header always says
**Demo Workspace** and warns that the data is example evidence, not real user
data. Overview provides exact links from the backend descriptor through the
Moving Average Crossover strategy, saved research and governance evidence, two
succeeded paper results, comparison, lifecycle review, and human decision
evidence. These identities are not guessed by the browser.

Standard and Demo use different storage volumes but the same loopback ports, so
an operator must stop one before starting the other. See the
[local operations guide](../founder-mvp-local-operations.md) for start, replay,
safe Demo reset, and return-to-standard commands.

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
