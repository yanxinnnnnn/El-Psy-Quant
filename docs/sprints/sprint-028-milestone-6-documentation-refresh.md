# Sprint 28 — Milestone 6 Documentation Refresh

## Objective

Close Milestone 6 by documenting the risk and benchmark foundation.

Sprint 25 added CAGR and annualized volatility with explicit period assumptions. Sprint 26 added Sharpe-style evaluation with explicit risk-free-rate assumptions. Sprint 27 added local buy-and-hold benchmark comparison. Sprint 28 updates the project documentation so the repository reflects the current state of the platform.

## Product Goal

As the founder, I want the repository documentation to clearly explain what Milestone 6 achieved, why it matters, and what direction the next milestone should take.

## Implementation Scope

### Must Have

Add a Milestone 6 summary document:

```text
docs/milestones/milestone-006-risk-and-benchmark-foundation.md
```

Update README to reflect:

- Milestone 6 is complete.
- The current platform supports CAGR and annualized volatility with explicit period assumptions.
- The current platform supports Sharpe-style evaluation with explicit frequency and risk-free-rate assumptions.
- The current platform can compare strategy results against a local CSV buy-and-hold benchmark over shared dates.
- The current documentation includes Milestone 1 through Milestone 6 summaries.
- The next milestone is now Milestone 7.

Update roadmap to reflect:

- Milestone 6 is complete.
- Sprints 25-28 are complete.
- Current next step is Sprint 29.

## Documentation Themes

The Milestone 6 summary should cover:

- Why total return alone is not enough.
- Why annualization assumptions must be explicit.
- Why Sharpe-style metrics are useful but not proof of strategy quality.
- Why benchmark comparison matters.
- How Sprint 25, Sprint 26, and Sprint 27 connect.
- What was deliberately avoided:
  - alpha and beta
  - information ratio
  - tracking error
  - rolling metrics
  - factor models
  - statistical significance tests
  - charts and dashboards
  - multi-benchmark or multi-asset research
- Why the next milestone should focus on multi-asset research.

## Acceptance Criteria

- Milestone 6 documentation exists.
- README current milestone section is updated.
- README current capabilities are updated.
- README next milestone section is updated.
- Roadmap marks Milestone 6 and Sprints 25-28 as complete.
- The documentation stays concise and does not overclaim profitability, strategy quality, statistical validity, or benchmark outperformance.

## Review Notes

The founder should review:

- Whether the milestone summary matches the actual project state.
- Whether the README is accurate and not overhyped.
- Whether the roadmap next step is practical.
- Whether the documentation keeps a clear line between basic evaluation discipline and advanced portfolio analytics.
