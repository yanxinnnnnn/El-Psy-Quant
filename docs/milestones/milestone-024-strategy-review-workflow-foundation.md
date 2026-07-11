# Milestone 24 — Strategy Review Workflow Foundation

## Status

Complete.

Milestone 24 was completed through Sprints 130–136.

## Product Goal

Define a small, local, deterministic, human-controlled contract layer for strategy review lifecycle governance above the completed promotion, paper-review, decision-governance, and report-artifact layers.

Milestone 24 makes declared strategy review states and explicitly reviewed lifecycle transitions reviewable and auditable without introducing runtime state mutation, workflow execution, broker behavior, live-readiness claims, or capital deployment.

## Completed Milestone Chain

```text
strategy review evidence reference contract
  -> strategy lifecycle state snapshot contract
  -> lifecycle transition proposal contract
  -> human-controlled lifecycle transition record
  -> strategy review workflow manifest and references
  -> milestone closeout
```

## Delivered Contracts

Milestone 24 delivered:

- typed strategy-review evidence references to completed M20–M23 governance artifacts
- immutable caller-supplied lifecycle state snapshots
- deterministic lifecycle transition proposals
- explicit human-controlled lifecycle transition records
- compact workflow references and immutable grouped manifests

The public contract layer remains local, deterministic, caller-supplied, and non-executing.

## Lifecycle Vocabulary

Milestone 24 uses exactly these states:

```text
research_review
paper_review
watchlist
on_hold
rejected
```

### `research_review`

The strategy is under explicit research-level review. This state does not imply paper eligibility.

### `paper_review`

The strategy is under explicit paper-evidence review. This state does not imply broker readiness, live readiness, or approval for capital deployment.

### `watchlist`

The strategy remains under active evidence monitoring without progression to another review stage.

### `on_hold`

The review lifecycle is intentionally paused.

### `rejected`

The current lifecycle path is closed within Milestone 24. Reopening a rejected lifecycle path requires later explicit planning.

There is no implicit initial state. A lifecycle state exists only when a caller explicitly supplies a state snapshot.

Milestone 24 does not include `live_candidate`, `live_ready`, `approved_for_live`, or any equivalent state.

## Permitted Transition Matrix

```text
research_review -> paper_review | watchlist | on_hold | rejected
paper_review    -> research_review | watchlist | on_hold | rejected
watchlist       -> research_review | paper_review | on_hold | rejected
on_hold         -> research_review | paper_review | watchlist | rejected
rejected        -> no transitions in Milestone 24
```

The matrix contains exactly 16 permitted ordered pairs.

Transition rules:

- no self-transitions
- no implicit transitions
- no automatic transition application
- a transition proposal does not change state
- every accepted transition requires a separate human-controlled transition record
- rejected or deferred review outcomes leave the declared source state unchanged
- decision statuses remain evidence rather than automatic lifecycle mappings

## Evidence Rules

Milestone 24 references completed governance artifacts rather than duplicating or loading them.

Minimum proposal rules:

- every proposal includes at least one `strategy_decision_record` reference
- entry into `paper_review` additionally requires a `promotion_record` reference
- report artifacts may provide context but cannot authorize a transition by themselves
- evidence references remain compact pointers only
- evidence references do not discover, load, resolve, parse, inspect, score, rank, or validate payloads
- evidence sufficiency remains explicit human judgment

## Human Review Boundary

The governance flow is:

```text
existing governance evidence
  -> caller-supplied transition proposal
  -> explicit human review
  -> caller-supplied transition record
  -> separately declared resulting state snapshot when approved
```

A proposal is a request, not an action.

A transition record captures one human review outcome using exactly:

```text
approved
rejected
deferred
```

An approved record requires a separately caller-supplied resulting snapshot matching the proposal strategy and target state. Rejected and deferred records prohibit a resulting snapshot.

Approval is governance evidence only. The record does not execute the transition, mutate either snapshot, make a snapshot current, or trigger a paper workflow.

## Workflow Reference and Manifest Boundary

Milestone 24 added compact references for exactly:

```text
strategy_lifecycle_state_snapshot
strategy_lifecycle_transition_proposal
strategy_lifecycle_transition_record
```

Workflow manifests group these references in separate immutable sequences.

Manifests:

- preserve caller order and duplicates
- may be partial
- require at least one reference total
- do not require one reference of every type
- do not validate artifact existence, same-strategy membership, chronological order, or chain completeness
- do not resolve IDs, load artifacts, make snapshots current, or execute transitions

## Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S130 | Complete | Plan Milestone 24. | Scope, vocabulary, transitions, evidence rules, sequence, and guardrails. | Documentation only. |
| S131 | Complete | Define strategy review evidence references. | Typed pointers to completed M20–M23 records and manifests. | No discovery, loading, parsing, scoring, ranking, evaluation, or workflow execution. |
| S132 | Complete | Define lifecycle state snapshots. | Immutable caller-supplied declarations using the five approved states. | No implicit initial state, mutable state store, persistence, state-machine service, or transition behavior. |
| S133 | Complete | Define lifecycle transition proposals. | Immutable proposals with exact permitted-pair validation and minimum evidence-type rules. | No approval, execution, or mutation. |
| S134 | Complete | Add human-controlled transition records. | `approved`, `rejected`, and `deferred` records with conditional resulting snapshots. | Governance approval only; no execution or current-state behavior. |
| S135 | Complete | Add workflow manifests and references. | Compact stable-ID pointers and immutable grouped manifests. | No resolution, chain validation, file I/O, persistence, state mutation, or workflow execution. |
| S136 | Complete | Close Milestone 24. | Documentation refresh, exit verification, and productization pivot. | No runtime scope expansion. |

## Exit Criteria Verification

Milestone 24 is complete because:

- strategy-review evidence references are explicit and typed
- lifecycle states use the approved five-state vocabulary
- state snapshots are caller-supplied and immutable
- the exact permitted transition matrix is deterministic and documented
- proposals remain non-executing requests
- transition records remain explicit human-controlled governance artifacts
- workflow references and manifests remain local pointer/index contracts
- completed M20–M23 artifacts remain separate and are referenced rather than duplicated or loaded
- no live-readiness state was introduced
- assumptions, human-approval boundaries, and future-readiness boundaries are documented

## Preserved Guardrails

Milestone 24 did not introduce:

- runtime lifecycle execution
- automatic state transitions
- mutable current-state storage
- automatic decision-status-to-state mapping
- automatic approval, rejection, promotion, deferral, or reopening
- artifact discovery, loading, resolution, scoring, ranking, or recommendation
- paper execution triggered by governance records
- configured workflow behavior changes
- a generic state-machine or workflow engine
- schedulers, queues, event buses, or hosted orchestration
- file or database persistence from lifecycle contracts
- dashboards, report generation, or hosted workflow products
- broker integration, live execution, or real-money behavior
- broker-readiness or live-readiness claims
- capital allocation or deployment
- strategy expansion

## Closeout Decision

Milestone 24 completes the contract-only governance foundation above research, paper trading, promotion, comparison, decisions, and report artifacts.

The next step is not another abstract governance layer. The platform should now turn its existing capabilities into a usable founder-only paper-trading product while preserving the human-controlled decision boundaries established through Milestone 24.

## Next Milestone

```text
Milestone 25 — Paper Trading Productization Planning
```

Milestone 25 will plan the application boundary, persistence and job-control direction, founder web workspace, and staged productization sequence. It remains planning-only and must not implement the application service or web UI prematurely.

See:

```text
docs/sprints/sprint-136-milestone-24-closeout-and-productization-pivot.md
docs/strategy/future-platform-roadmap.md
```
