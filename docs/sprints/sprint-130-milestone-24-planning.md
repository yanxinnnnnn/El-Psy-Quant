# Sprint 130 — Milestone 24 Planning

## Status

Complete after this documentation PR is merged.

## Objective

Plan **Milestone 24 — Strategy Review Workflow Foundation** after Milestone 23 closed.

Sprint 130 defines a conservative, contract-only strategy review lifecycle layer above completed promotion, paper-review, decision-governance, and report-artifact records.

This is a CTO-owned planning and documentation sprint. It does not add runtime behavior and is not delegated to Codex.

## Completed Context

Milestones 20–23 now provide:

```text
promotion governance
  -> paper comparison and review
  -> strategy decision governance
  -> deterministic report artifacts
```

These layers can record evidence, paper reviews, strategy decisions, and review packages. They do not yet declare a strategy's human-controlled review lifecycle state or record an explicitly approved change between declared states.

## Milestone 24 Decision

Milestone 24 is:

```text
Strategy Review Workflow Foundation
```

It is contract-only.

The milestone may add immutable typed contracts, deterministic validation, constants, factories, JSON-compatible exports, and local manifest/reference structures. It must not add a runtime state machine, mutable state store, transition executor, orchestration service, scheduler, queue, event bus, CLI lifecycle commands, or configured workflow changes.

## Planned Chain

```text
strategy review evidence reference contract
  -> strategy lifecycle state snapshot contract
  -> lifecycle transition proposal contract
  -> human-controlled lifecycle transition record
  -> strategy review workflow manifest and references
  -> milestone closeout
```

## Approved Lifecycle Vocabulary

```text
research_review
paper_review
watchlist
on_hold
rejected
```

- `research_review` means explicit research-level review only.
- `paper_review` means explicit paper-evidence review only.
- `watchlist` means active evidence monitoring without progression.
- `on_hold` means review is intentionally paused.
- `rejected` closes the current lifecycle path within Milestone 24.

There is no implicit initial state. A lifecycle state exists only when explicitly declared by the caller.

Milestone 24 does not include `live_candidate`, `live_ready`, `approved_for_live`, or any equivalent state. Live-readiness semantics remain a later dedicated milestone.

## Permitted Transitions

```text
research_review -> paper_review | watchlist | on_hold | rejected
paper_review    -> research_review | watchlist | on_hold | rejected
watchlist       -> research_review | paper_review | on_hold | rejected
on_hold         -> research_review | paper_review | watchlist | rejected
rejected        -> no transitions in Milestone 24
```

Rules:

- no self-transitions
- no implicit transitions
- no automatic transition application
- a proposal does not change state
- every accepted transition requires a separate human-controlled transition record
- rejected or deferred proposals leave state unchanged
- existing decision statuses are evidence, not automatic lifecycle mappings
- a decision record may exist without causing a lifecycle transition
- reopening `rejected` is outside Milestone 24

## Evidence Boundary

Milestone 24 references existing records rather than duplicating or loading them.

Evidence references may point to:

- promotion records and manifests
- paper comparison summaries
- paper review decision records and manifests
- strategy decision summaries, records, and manifests
- report artifact summaries and manifests

Minimum rules:

- every transition proposal includes at least one strategy decision record reference
- entry into `paper_review` additionally includes a promotion record reference
- report artifacts may provide context but cannot authorize a transition by themselves
- evidence references remain pointers only
- evidence sufficiency remains explicit human judgment

## Human Approval Boundary

```text
existing governance evidence
  -> caller-supplied transition proposal
  -> explicit human review
  -> caller-supplied transition record
  -> declared lifecycle state snapshot/reference
```

A proposal is a request, not an action.

A transition record is a governance artifact, not a transition executor. It may record an approved, rejected, or deferred reviewer outcome and an explicitly declared resulting-state reference when approved. It does not mutate stored state or trigger any workflow.

## Planned Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S130 | Complete after planning PR merge | Plan Milestone 24. | Scope, lifecycle vocabulary, transition matrix, evidence rules, sequence, and guardrails. | Documentation only; no runtime behavior. |
| S131 | Planned | Define strategy review evidence references. | Small typed references to completed M20–M23 governance records and manifests. | No discovery, loading, parsing, scoring, ranking, or workflow execution. |
| S132 | Planned | Define lifecycle state snapshots. | Explicit caller-supplied strategy review state snapshots. | No implicit initial state, mutable state store, persistence, or state-machine service. |
| S133 | Planned | Define lifecycle transition proposals. | Explicit from-state, target-state, rationale, evidence references, and requester context. | A proposal does not change state or approve anything. |
| S134 | Planned | Add human-controlled lifecycle transition records. | Explicit reviewer outcome, rationale, approval context, and resulting-state reference. | No automatic approval, transition execution, paper execution, broker behavior, or readiness claim. |
| S135 | Planned | Add workflow manifests and references. | Local references and manifests for state snapshots, proposals, and transition records. | No file I/O, database, hosted orchestration, dashboard, or workflow engine. |
| S136 | Planned | Close Milestone 24. | Documentation refresh and closeout. | No scope expansion. |

## Alternatives Rejected

### Runtime State Machine

Rejected.

The project does not need a mutable lifecycle service before the domain contracts and human approval boundaries are stable.

### Automatic Decision-to-State Mapping

Rejected.

Milestone 22 decision statuses are evidence. Automatically translating them into lifecycle state would turn governance records into hidden workflow execution.

### `live_candidate` State

Rejected for Milestone 24.

The phrase can be mistaken for live readiness or capital-deployment approval. A dedicated future live-readiness milestone should define those semantics after risk and operational controls exist.

### Generic Workflow Engine

Rejected.

A broad state-machine or orchestration abstraction would create infrastructure before the narrow strategy-review domain needs it.

### Database Or Hosted Workflow

Rejected.

Milestone 24 remains local and contract-driven. Persistence services, hosted orchestration, team workspaces, and SaaS behavior are later productization concerns.

## Scope Guardrails

Sprint 130 and Milestone 24 do not add:

- Python source code or tests during planning
- public API or schema changes during planning
- strategy lifecycle runtime execution
- automatic strategy state transitions
- mutable current-state storage
- automatic mapping from decision statuses to lifecycle states
- automatic approval, rejection, promotion, or reopening
- automatic evidence discovery
- artifact loading, parsing, scoring, ranking, or recommendation
- metric calculation or winner selection
- paper workflow execution from lifecycle records
- configured workflow behavior changes
- CLI lifecycle operations
- file I/O from lifecycle contracts
- persistence services or databases
- generic workflow or state-machine engines
- schedulers, queues, event buses, or hosted orchestration
- dashboards, broad reporting UI, or report generation
- broker integration or broker readiness
- live execution or live readiness
- real-money behavior
- capital allocation or deployment
- strategy-signal-to-order conversion
- market-data streaming
- real account synchronization
- hosted services or SaaS behavior
- strategy expansion

## Implementation Sprint Handoff

Sprint 130 is planning-only, so it does not require the Windows proxy prelude.

Every later Codex implementation sprint issue must include the Windows proxy prelude, proxy safety warnings, a recommended Codex model and reasoning effort, the full quality gate, a clean first-line `Closes #<issue-number>`, and the requirement to open the PR Ready for review rather than as Draft.

Default implementation recommendation:

```text
Codex model: GPT-5.6 Terra
Reasoning effort: Medium
```

Use GPT-5.6 Sol with High or stronger reasoning only when a later sprint is architecture-heavy, ambiguous, cross-module, or high-risk. Use GPT-5.6 Luna for mechanical documentation-only corrections.

## Documentation Changes

Sprint 130 updates:

- `README.md`
- `AGENTS.md`
- `docs/roadmap.md`
- adds `docs/milestones/milestone-024-strategy-review-workflow-foundation.md`
- adds `docs/sprints/sprint-130-milestone-24-planning.md`
- `docs/strategy/future-platform-roadmap.md`

No Python source, tests, runtime behavior, workflow behavior, persistence, or execution behavior changes.

## Next Step

```text
Sprint 131 — Strategy Review Evidence Reference Contract Foundation
```

Sprint 131 should be created as a separate implementation issue only after the founder decides whether to merge the Sprint 130 planning PR.
