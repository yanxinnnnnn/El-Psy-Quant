# Milestone 23 — Report Artifact Foundation

## Status

In progress.

## Product Goal

Define a conservative report-artifact layer above the completed governance records from Milestones 20, 21, and 22.

Milestone 23 should make report artifacts explicit, deterministic, reproducible, and reviewable without turning the project into a dashboard, broad report engine, automated decision system, broker-readiness workflow, live-readiness workflow, database-backed service, or SaaS product.

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

Milestone 22 completed strategy-level decision governance:

```text
decision evidence reference contract
  -> strategy decision input contract
  -> strategy decision summary
  -> explicit strategy decision record
  -> decision manifest and references
```

Milestone 23 should sit above those governance records. Its job is to define deterministic report artifacts that can summarize and reference completed governance records for human review.

This is report artifact governance, not report generation automation.

## Milestone 23 Decision

Milestone 23 should be:

```text
Report Artifact Foundation
```

## Why This Is The Right Next Step

The project now has explicit governance records for:

- promotion evidence and promotion decisions
- paper run comparison and review decisions
- strategy-level decision inputs, summaries, records, manifests, and references

The missing layer is a stable report artifact contract that can package those completed records into a reviewable artifact without inventing new decisions or pulling runtime behavior into the platform.

Without this milestone, the project has two bad options:

1. jump straight to dashboards or broad report generation before report semantics are stable
2. keep governance records isolated without a deterministic way to package them for founder review

Both are premature.

The right next step is to define a small report-artifact boundary that can answer:

- what report is being declared
- which completed governance records are referenced
- what sections the report contains
- what assumptions, warnings, and missing evidence remain
- what schema version and artifact identity make the report reproducible
- what local references make the report auditable

A report artifact is a review package. It is not a dashboard, recommendation engine, approval engine, or readiness claim.

## Planned Milestone 23 Chain

```text
report source reference contract
  -> report section contract
  -> report artifact summary
  -> report manifest and references
  -> report artifact closeout
```

The exact sprint names can change during execution, but the milestone should preserve this direction:

1. define small references to completed governance records
2. define deterministic report section metadata
3. define caller-supplied report artifact summaries
4. define compact report references and manifests
5. close the milestone with documentation refresh only

## Candidate Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S124 | Complete | Plan Milestone 23. | Report artifact scope, sequence, and guardrails. | No runtime behavior during planning. |
| S125 | Complete | Define report source references. | Small typed references to completed governance records and manifests. | No artifact loading, discovery, parsing, scoring, or report generation. |
| S126 | Planned | Define report section contract. | Explicit section metadata and caller-supplied section content boundaries. | No rendering pipeline, dashboard, markdown/PDF generation, or workflow execution. |
| S127 | Planned | Define report artifact summary. | Deterministic caller-supplied report summary with facts, assumptions, warnings, and missing-evidence notes. | No automatic metric calculation, recommendation, ranking, or decision making. |
| S128 | Planned | Add report manifest and references. | Local manifest/reference contracts for report summaries and report artifacts. | No file I/O, database, hosted service, dashboard, or report engine. |
| S129 | Planned | Close milestone. | Milestone 23 documentation refresh. | No scope expansion. |

## Included Capabilities

Milestone 23 may include:

- a minimal report source reference contract for completed governance records
- deterministic report section contracts
- caller-supplied report artifact summaries
- assumptions, warnings, missing-evidence, and review-context fields
- local report manifest/reference contracts
- documentation of report artifact assumptions, limits, and future dashboard boundaries

## Explicitly Out Of Scope

Milestone 23 must not introduce:

- runtime behavior
- automatic report generation
- report rendering pipelines
- dashboards
- broad reporting UI
- plotting behavior
- markdown, HTML, PDF, notebook, or hosted report generation
- automatic evidence discovery
- artifact loading, parsing, scoring, or validation beyond explicit contract validation
- metric calculation, comparison, ranking, winner selection, or recommendation
- automatic decision making
- automatic approval
- automatic rejection
- automatic promotion
- automatic strategy lifecycle automation
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
- workflow execution changes
- configured paper workflow behavior changes
- database behavior
- hosted services or SaaS behavior
- strategy expansion

## Design Notes For Implementation Sprints

Implementation sprints should preserve the existing architecture rule:

```text
CLI and operations should wrap stable functions, not drive architecture.
```

The safest shape is:

```text
governance records stay separate
report source references stay explicit
report sections stay caller-supplied
report summaries stay descriptive
report manifests stay local reference contracts
rendering, dashboards, and workflows stay separate
```

Report artifacts should reference completed governance records. They should not discover records automatically, load artifacts, calculate metrics, rank strategies, create decisions, or imply readiness for broker or live trading.

## Implementation Sprint Issue Requirements

Future implementation sprint issues must include the Windows proxy prelude when Codex implementation is requested:

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

## Longer-Term Roadmap Alignment

The long-term platform direction is maintained in:

```text
docs/strategy/future-platform-roadmap.md
```

The broad phases remain:

```text
Phase 1 — Research & Artifact Foundation
Phase 2 — Workflow Integration Foundation
Phase 3 — Decision Intelligence Foundation
Phase 4 — Broker Readiness & Execution Governance
Phase 5 — Controlled Live Pilot & Production Operations
```

Milestone 23 is still part of Phase 3. It packages completed governance records into deterministic report artifacts before dashboards, broad report engines, broker readiness, live-readiness claims, or capital deployment decisions.

## Exit Criteria

Milestone 23 is ready to close when:

- report source references are explicit and typed
- report sections can be represented without rendering or dashboard behavior
- report artifact summaries can record caller-supplied facts, assumptions, warnings, and missing-evidence notes
- report manifests and references can be inspected locally
- documentation explains report artifact assumptions, limits, and future dashboard boundaries
- dashboards, broad report generation, broker behavior, live behavior, runtime execution expansion, database behavior, automatic capital deployment decisions, and strategy expansion remain outside the milestone

## Next Step

```text
Sprint 126 — Report Section Contract Foundation
```

Sprint 126 should add a small report section contract without rendering pipelines, dashboards, markdown/PDF generation, workflow execution, broker behavior, or readiness claims.
