# AGENTS.md

This file defines the shared context for AI agents working on El-Psy-Quant.

## Project Identity

El-Psy-Quant is an AI-native quantitative research and trading platform.

The project is built like a startup product, not a one-off learning script.

## Mission

Build a production-ready platform that can ingest market data, research strategies, run backtests, generate reports, and eventually support paper trading and small-scale live trading.

## Operating Model

- The human founder makes final decisions.
- AI agents may implement code, tests, and documentation.
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

Sprint 117 planned the conservative decision-governance layer after promotion governance and paper run comparison/review.

Sprint 118 added typed decision evidence references for existing promotion and paper-review evidence without artifact loading, scoring, automatic discovery, workflow execution, broker behavior, or readiness claims.

Sprint 119 added explicit strategy decision inputs that group decision evidence references with purpose and review context without automatic evidence discovery, scoring, decision making, workflow execution, broker behavior, or readiness claims.

Sprint 120 added caller-supplied strategy decision summaries with facts, assumptions, warnings, and missing-evidence notes without recommendation engines, metric calculation, scoring, dashboards, reports, workflow execution, broker behavior, or readiness claims.

Sprint 121 added explicit human-controlled strategy decision records with supported statuses, rationale, notes, warnings, and reviewer context without automatic approval, promotion, capital allocation, broker behavior, workflow execution, reports, or readiness claims.

Sprint 122 added local strategy decision manifests and compact summary/record references without file I/O, database behavior, persistence services, artifact loading, reports, workflow execution, broker behavior, or readiness claims.

Sprint 123 closed Milestone 22 with a documentation-only refresh and preserved the decision-governance guardrails.

Sprint 124 planned Milestone 23 — Report Artifact Foundation. It defines the next conservative platform layer after decision governance: deterministic report artifacts that reference completed governance records without adding runtime behavior during planning.

Milestone 23 should plan explicit report source references, report sections, report artifact summaries, and report manifests before dashboards, broad report engines, broker readiness, live-readiness claims, capital deployment, databases, hosted services, SaaS behavior, or automatic decisions.

Sprint 125 added typed report source references for completed governance records and manifests without evidence discovery, artifact loading, report generation, rendering, scoring, ranking, workflow execution, broker behavior, database behavior, or readiness claims.

Sprint 126 added caller-supplied report sections with explicit report source references without rendering pipelines, dashboards, markdown/PDF generation, workflow execution, broker behavior, or readiness claims.

The next focus is Sprint 127 — Report Artifact Summary Foundation. It should add a deterministic caller-supplied report artifact summary without automatic metric calculation, recommendation, ranking, dashboards, reports, workflow execution, broker behavior, or readiness claims.

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

- Do not use `--global`
- Do not commit proxy config
- Do not modify project files for proxy setup
