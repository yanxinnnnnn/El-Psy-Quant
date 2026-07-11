# AGENTS.md

This file defines the shared context for AI agents working on El-Psy-Quant.

## Project Identity

El-Psy-Quant is an AI-native quantitative research and trading platform.

The project is built like a startup product, not a one-off learning script.

## Mission

Build a production-ready platform that can ingest market data, research strategies, run backtests, generate reviewable artifacts, and eventually support paper trading and tightly controlled live trading.

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

## Quant Principles

- Never claim a strategy is profitable without evidence.
- Avoid look-ahead bias.
- Avoid survivorship bias where possible.
- Always distinguish research code, backtesting code, and execution code.
- Prefer reproducible experiments.
- Risk metrics matter as much as return metrics.

## Definition of Done

A task is done only when:

- The code runs locally.
- Tests are included where appropriate.
- README or docs are updated when behavior changes.
- Assumptions and limitations are documented.
- The implementation is simple enough for a human reviewer to understand.
- The PR is marked Ready for review, not left as Draft.

## Long-Term Platform Direction

Build an AI-native quant research operating system that turns trading ideas into reproducible, auditable, risk-aware decisions before any real capital is deployed.

The long-term phase roadmap is maintained in:

```text
docs/strategy/future-platform-roadmap.md
```

## Current Focus

Milestone 18 — Paper Trading Workflow Integration Foundation is complete.

Milestone 19 — Configured Paper Workflow Wiring Foundation is complete.

Milestone 20 — Research-to-Paper Promotion Foundation is complete.

Milestone 21 — Paper Run Comparison and Review Foundation is complete.

Milestone 22 — Decision Governance Foundation is complete.

Milestone 23 — Report Artifact Foundation is complete.

Sprint 130 planned **Milestone 24 — Strategy Review Workflow Foundation** as a contract-only, human-controlled lifecycle-governance layer.

The planned Milestone 24 chain is:

```text
strategy review evidence reference contract
  -> strategy lifecycle state snapshot contract
  -> lifecycle transition proposal contract
  -> human-controlled lifecycle transition record
  -> strategy review workflow manifest and references
  -> strategy review workflow closeout
```

The approved lifecycle vocabulary is limited to:

```text
research_review
paper_review
watchlist
on_hold
rejected
```

There is no implicit initial state, no automatic mapping from decision statuses, no automatic transition application, and no `live_candidate` or live-readiness state.

Milestone 24 remains local and contract-only. It must not add mutable state storage, a transition executor, a generic state-machine or workflow engine, automatic decisions, evidence discovery or loading, paper execution, configured workflow changes, broker/live behavior, capital deployment, databases, hosted orchestration, or readiness claims.

Sprint 131 added explicit strategy-review evidence references to completed M20–M23 governance artifacts. These are pointers only: they do not inspect payloads, infer lifecycle state, propose or execute transitions, or imply readiness.

Sprint 132 added immutable caller-supplied lifecycle state snapshots using the approved five-state vocabulary. Snapshots have no implicit initial state, are not mutable current state, do not automatically map decision statuses, and do not request, approve, reject, validate, or execute transitions.

Sprint 133 added immutable caller-supplied transition proposals with the exact permitted-pair matrix and minimum evidence-reference type rules. Proposals remain non-approving, non-executing, non-mutating, and do not create resulting snapshots or imply readiness.

Sprint 134 added immutable caller-supplied human-review transition records with exactly `approved`, `rejected`, and `deferred` outcomes. Approved records require a separately supplied matching resulting snapshot; rejected and deferred records prohibit one. Records are governance evidence only and do not execute transitions, mutate or make snapshots current, map decision statuses automatically, or imply paper execution, broker/live readiness, or capital deployment.

The next focus is:

```text
Sprint 135 — Strategy Review Workflow Manifest and Reference Foundation
```

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
- Run `uv run python scripts/check.py` before opening the PR.
- The PR body must start with a clean manually typed `Closes #<issue-number>` line.
- After opening the PR, mark it Ready for review. Do not leave it as Draft.
