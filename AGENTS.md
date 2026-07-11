# AGENTS.md

This file defines the shared context for AI agents working on El-Psy-Quant.

## Project Identity

El-Psy-Quant is an AI-native quantitative research and trading platform.

The project is built like a startup product, not a one-off learning script.

## Mission

Build a production-ready platform that can ingest market data, research strategies, run backtests, generate reviewable artifacts, operate paper-trading workflows, and eventually support tightly controlled live trading.

## Operating Model

- The human founder makes final decisions.
- ChatGPT acts as CTO for milestone planning, sprint scope, architecture boundaries, and PR review.
- Codex acts as the implementation developer for coding sprints.
- Documentation-only planning and closeout sprints may be handled directly by the CTO.
- AI-generated code must be reviewable, tested, and simple.
- Do not optimize for cleverness. Optimize for correctness and maintainability.

## Engineering Principles

- Use Python.
- Prefer modern Python packaging and tooling.
- Prefer `uv` for dependency management unless the founder decides otherwise.
- Use a `src/` layout.
- Use `pytest` for testing.
- Use `ruff` for formatting and linting.
- Use type hints for public functions.
- Keep modules small and composable.
- Avoid premature abstraction.
- Avoid hidden network calls in tests.
- Keep financial calculations explicit and well documented.
- Keep broker-specific behavior behind adapters rather than leaking it into strategy, evaluation, governance, or UI domain models.

## Quant Principles

- Never claim a strategy is profitable without evidence.
- Avoid look-ahead bias.
- Avoid survivorship bias where possible.
- Always distinguish research code, backtesting code, paper execution code, and live execution code.
- Prefer reproducible experiments.
- Risk metrics matter as much as return metrics.
- Human approval records are governance evidence, not proof that runtime execution occurred.

## Definition of Done

A task is done only when:

- The code runs locally when runtime behavior changes.
- Tests are included where appropriate.
- README or docs are updated when behavior changes.
- Assumptions and limitations are documented.
- The implementation is simple enough for a human reviewer to understand.
- The complete quality gate passes.
- The PR is marked Ready for review, not left as Draft.

## Long-Term Platform Direction

Build an AI-native quant research operating system that turns trading ideas into reproducible, auditable, risk-aware decisions before any real capital is deployed.

The long-term phase roadmap is maintained in:

```text
docs/strategy/future-platform-roadmap.md
```

## Completed Governance Foundation

Milestones 18–24 are complete:

```text
M18 — Paper Trading Workflow Integration Foundation
M19 — Configured Paper Workflow Wiring Foundation
M20 — Research-to-Paper Promotion Foundation
M21 — Paper Run Comparison and Review Foundation
M22 — Decision Governance Foundation
M23 — Report Artifact Foundation
M24 — Strategy Review Workflow Foundation
```

Milestone 24 delivered this contract-only, human-controlled chain:

```text
strategy review evidence reference contract
  -> strategy lifecycle state snapshot contract
  -> lifecycle transition proposal contract
  -> human-controlled lifecycle transition record
  -> strategy review workflow manifest and references
  -> milestone closeout
```

Its lifecycle vocabulary is exactly:

```text
research_review
paper_review
watchlist
on_hold
rejected
```

Milestone 24 added:

- typed evidence pointers to completed M20–M23 governance artifacts
- immutable caller-supplied lifecycle state snapshots
- deterministic validation of the approved 16-pair transition matrix
- non-executing lifecycle transition proposals
- human-controlled records with exactly `approved`, `rejected`, and `deferred` outcomes
- compact stable-ID references and immutable grouped manifests

Milestone 24 did not add mutable current-state storage, automatic transitions, decision-status mapping, artifact discovery or loading, workflow execution, paper execution from governance records, broker behavior, live-readiness claims, capital deployment, databases, hosted orchestration, dashboards, or SaaS behavior.

## Current Focus

The next milestone is:

```text
Milestone 25 — Paper Trading Productization Planning
```

The provisional productization sequence is:

```text
M25 — Paper Trading Productization Planning
M26 — Paper Trading Application Service Foundation
M27 — Persistence and Paper Job Control Foundation
M28 — Founder Paper Trading Web Workspace
M29 — Product Feedback and Hardening
M30 — Portfolio-Level Decision Review Foundation
```

Portfolio-level review is deferred, not canceled.

## Founder-Only Product Direction

The first usable product target is a local, single-user founder workspace that supports:

- strategy list and detail
- research, backtest, governance, and evidence inspection
- starting and reviewing paper runs
- paper-run status, equity, positions, orders, and fills
- paper-run comparison
- lifecycle transition proposals and human review records
- lifecycle timeline

Recommended direction for the next productization milestones:

- FastAPI application service
- SQLite with SQLAlchemy
- simple local background jobs
- React/Next.js web workspace
- Docker Compose and local-first deployment
- single-user or minimal authentication

Do not introduce premature microservices, Kubernetes, Kafka, Redis clusters, multi-tenancy, complex RBAC, real-time dashboards, or broker integration.

## Future QMT Boundary

QMT is a future execution adapter only.

Preferred boundary:

```text
Browser
  -> Web/API
  -> broker-neutral execution command
  -> Windows QMT agent
  -> MiniQMT
  -> broker
```

Future broker-neutral execution concepts may include:

```text
OrderIntent
ExecutionOrder
ExecutionFill
AccountSnapshot
PositionSnapshot
BrokerOrderReference
```

Potential venues may include `internal_paper`, optional future `qmt_paper`, and future `qmt_live`.

Never connect the browser directly to QMT. Do not add live QMT behavior before dedicated execution-risk and live-readiness governance exists.

## Implementation Sprint Issue Requirements

Future Codex implementation sprint issues must include the Windows proxy prelude:

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7892"
$env:HTTPS_PROXY="http://127.0.0.1:7892"
$env:ALL_PROXY="http://127.0.0.1:7892"

git config http.proxy http://127.0.0.1:7892
git config https.proxy http://127.0.0.1:7892
```

They must also state:

- Do not use `--global`.
- Do not commit proxy config.
- Do not modify project files for proxy setup.
- Recommend a Codex model and reasoning effort for the specific sprint.
- Use GPT-5.6 Terra with Medium reasoning for normal implementation sprints unless complexity justifies another choice.
- Use GPT-5.6 Sol with High or stronger reasoning for architecture-heavy, ambiguous, high-risk, or difficult cross-module work.
- Use GPT-5.6 Luna with Light or Medium reasoning for mechanical or documentation-only corrections.
- Treat the GitHub issue body as the authoritative specification; keep the separate Codex execution prompt short.
- Run `uv run python scripts/check.py` before opening the PR.
- The PR body must start with a clean manually typed `Closes #<issue-number>` line.
- After opening the PR, mark it Ready for review. Do not leave it as Draft.
- Do not merge the PR unless the founder explicitly requests it.
