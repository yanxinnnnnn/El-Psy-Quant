# Milestone 12 — Data Integrity & Universe Foundation

## Status

Planned.

## Product Goal

Make local research inputs harder to misuse before the project adds more strategies.

Milestone 11 established a strategy boundary. Milestone 12 should strengthen the data boundary that feeds it.

## Why This Comes Before More Strategies

A new strategy is only as trustworthy as its inputs.

Before adding more strategy implementations, the project should make these questions easier to answer:

- Which symbols are included in this run?
- Were symbol names normalized consistently?
- Were duplicates or blank symbols rejected early?
- Is the local price data structurally usable?
- Does each price DataFrame contain the required columns?
- Are close prices numeric and non-missing?
- Are index assumptions explicit?
- Do configured experiments fail before strategy execution when inputs are invalid?

This milestone is not about finding alpha. It is about reducing avoidable research mistakes.

## Planned Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S53 | Complete | Plan Milestone 12. | Data integrity and universe milestone scope. | No implementation during planning. |
| S54 | Planned | Validate local price data. | Small price DataFrame validation layer. | No live data or external validation. |
| S55 | Planned | Define symbol universe discipline. | Explicit configured symbol universe helper or representation. | No investable universe database. |
| S56 | Planned | Wire configured input validation. | Configured experiments validate inputs before strategy execution. | Preserve artifact schemas and CLI shape. |
| S57 | Planned | Close milestone. | Milestone 12 documentation refresh. | No scope expansion. |

## Planned Work

### Price Data Validation

The project should add a small local validation layer for price DataFrames.

Potential checks:

- DataFrame is not empty
- required `Close` column exists
- close values are numeric
- close values are not missing
- duplicate index values are rejected where relevant
- date/index order assumptions are explicit
- errors are clear and actionable

This should stay local and deterministic. It should not call live providers or external services.

### Symbol Universe Definition

The project should define what a configured research universe means.

Potential checks:

- symbols are normalized consistently
- blank symbols are rejected
- duplicates after normalization are rejected
- configured order is preserved
- the universe is documented as a research input list, not an investable universe database

### Configured Run Input Validation

Configured experiments should validate symbol and price inputs before strategy execution.

Invalid inputs should fail early and clearly. Valid configured runs should preserve existing output layout and artifact semantics.

## Guardrails

Milestone 12 should avoid:

- new trading strategies
- strategy protocol changes
- resolver changes
- config schema expansion unless a later sprint explicitly justifies it
- CLI redesign
- artifact schema changes
- portfolio construction
- databases or dashboards
- live or paper trading
- plugin frameworks
- dynamic imports
- parameter search or optimization

## Exit Criteria

Milestone 12 is complete when:

- local price data has a small validation boundary
- symbol universe inputs are normalized and validated consistently
- configured experiments validate inputs before strategy execution
- valid runs preserve existing artifact contracts
- invalid inputs fail early with clear errors
- the milestone documentation explains the data assumptions and remaining limits

## Relationship To Future Milestones

Milestone 12 prepares the project for future strategies by improving input trust.

Milestone 13 can then move toward portfolio construction with fewer hidden data and universe assumptions.

## Current Next Step

The next sprint should be:

```text
Sprint 54 — Price Data Validation Foundation
```

Start by validating the local price DataFrames that feed strategies. Do that before expanding the strategy count or adding portfolio logic.
