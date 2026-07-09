# Milestone 22 — Decision Governance Foundation

## Status

In progress.

## Product Goal

Define a conservative, human-controlled decision-governance layer above promotion governance and paper run review.

Milestone 22 should record higher-level strategy decisions using existing promotion and paper-review evidence without introducing dashboards, broad reporting, broker readiness, live-readiness claims, automatic approval, automatic promotion, capital deployment, or runtime execution expansion.

## Strategic Context

Milestone 20 completed research-to-paper promotion governance:

```text
research evidence
  -> promotion candidate
  -> evidence summary
  -> explicit promotion record
  -> reviewable promotion references
```

Milestone 21 completed paper run comparison and review governance:

```text
multiple paper runs
  -> explicit comparison set
  -> comparison summary
  -> review decision record
  -> reviewable comparison references
```

Milestone 22 should sit above those records. It should not duplicate promotion records or paper review decisions. Its job is to make the next strategy-level decision explicit, evidence-backed, and auditable.

This is governance, not automation.

## Planned Chain

```text
decision evidence reference contract
  -> strategy decision input contract
  -> strategy decision summary
  -> explicit strategy decision record
  -> decision manifest and references
  -> decision governance closeout
```

## Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S117 | Complete | Plan Milestone 22. | Decision governance scope, sequence, and guardrails. | No implementation during planning. |
| S118 | Complete | Define decision evidence references. | Small typed references to existing promotion records, promotion manifests, paper comparison summaries, review decisions, and review manifests. | No evidence discovery, loading, parsing, scoring, ranking, or decision making. |
| S119 | Complete | Define strategy decision input contract. | Explicit input object grouping evidence references, decision purpose, review context, and reviewer metadata. | No automatic decision generation, scoring, recommendation, or lifecycle automation. |
| S120 | Complete | Add strategy decision summary. | Deterministic caller-supplied facts, assumptions, warnings, missing evidence, and decision context. | No recommendation engine, metric calculation, scoring, dashboards, or reports. |
| S121 | Planned | Add explicit strategy decision record. | Human-controlled decision status, rationale, reviewer context, and timestamp tied to a decision summary. | No automatic approval, promotion, capital allocation, broker behavior, or readiness claim. |
| S122 | Planned | Add decision manifest and references. | Local manifest/reference contracts for strategy decision summaries and records. | No file I/O, database, hosted service, dashboard, report, or workflow execution. |
| S123 | Planned | Close milestone. | Milestone 22 documentation refresh. | No scope expansion. |

## Included Capabilities

Milestone 22 may include:

- a minimal decision evidence reference contract for existing promotion and paper-review evidence
- an explicit strategy decision input object
- deterministic strategy decision summary data supplied by callers
- assumptions, warnings, and missing-evidence fields for decision review
- a human-controlled strategy decision record with explicit status and rationale
- local manifest/reference contracts for decision summaries and decision records
- documentation of decision assumptions, limits, and future readiness boundaries

## Decision Boundary Semantics

A decision evidence reference is only a pointer to existing evidence. It does not load, parse, score, validate, or discover the referenced artifact.

A strategy decision input is only an explicit grouping of evidence and review context. It defines what is being considered and why.

A strategy decision summary is descriptive context. Facts, assumptions, warnings, and missing-evidence notes are caller-supplied and do not form an automatic recommendation engine.

A strategy decision record is a human-controlled governance artifact. It records status and rationale, but it is not live readiness, real-money readiness, broker approval, autonomous strategy approval, or a capital deployment decision.

A decision manifest is a local reference contract for inspection. It does not read from disk, write to disk, create reports, persist data, use a database, or run workflows.

## Questions The Milestone Should Answer

- What evidence is being considered?
- Which promotion records or paper-review decisions support this decision?
- What decision status was chosen?
- What rationale was provided?
- What warnings or missing evidence remain?
- Who reviewed it and when?
- What local references make the decision auditable?

## Assumptions And Limits

- decision governance remains explicit-input driven
- promotion records remain separate from decision records
- paper review decisions remain separate from strategy-level decision records
- evidence references do not imply artifact loading
- decision summaries are descriptive, not autonomous recommendation engines
- decision records are human-controlled records
- decision records do not approve live trading or real-money deployment
- decision manifests are local reference contracts, not persistence or database behavior
- configured paper workflow behavior remains unchanged
- local typed contracts are enough for this milestone

## Explicitly Out Of Scope

Milestone 22 must not introduce:

- runtime behavior
- product code beyond the planned contract layer
- dashboards
- broad report generation
- plotting behavior
- broker readiness
- live readiness
- real-money readiness claims
- capital deployment
- capital allocation
- order routing
- broker integration
- exchange APIs
- live execution
- market data streaming
- scheduler behavior
- real account synchronization
- strategy expansion
- automatic approval
- automatic promotion
- automatic strategy lifecycle automation
- automatic decision making
- automatic evidence discovery
- artifact loading/parsing/scoring
- metric calculation, comparison, ranking, or winner selection
- workflow execution changes
- configured paper workflow behavior changes
- database behavior
- hosted services or SaaS behavior

## Exit Criteria

Milestone 22 should be considered complete only when:

- decision evidence references are explicit and typed
- strategy decision inputs can group existing evidence without discovering or loading artifacts automatically
- strategy decision summaries can record caller-supplied facts, assumptions, warnings, and missing-evidence notes
- explicit strategy decision records capture status, rationale, reviewer context, and timestamp
- decision manifests and references can be inspected locally
- documentation explains decision-governance assumptions, limits, and future readiness boundaries
- dashboards, broad reporting, broker behavior, live behavior, runtime execution expansion, database behavior, automatic capital deployment decisions, and strategy expansion remain outside the milestone

## Next Step

```text
Sprint 121 — Explicit Strategy Decision Record Foundation
```

Sprint 121 should add human-controlled strategy decision records tied to strategy decision summaries without automatic approval, promotion, capital allocation, broker behavior, or readiness claims.
