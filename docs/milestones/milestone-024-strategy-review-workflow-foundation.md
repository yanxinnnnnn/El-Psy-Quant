# Milestone 24 — Strategy Review Workflow Foundation

## Status

In progress.

Sprint 130 defined the milestone scope, lifecycle vocabulary, transition semantics, evidence requirements, sprint sequence, and guardrails. Sprint 131 added the first evidence-reference contract.

## Product Goal

Define a small, local, deterministic, human-controlled contract layer for strategy review lifecycle governance above the completed promotion, paper-review, decision-governance, and report-artifact layers.

Milestone 24 should make declared strategy review states and explicitly approved lifecycle transitions reviewable and auditable without introducing a runtime state machine, mutable state storage, workflow execution, broker behavior, live-readiness claims, or capital deployment.

## Strategic Context

Milestone 20 completed research-to-paper promotion governance:

```text
research evidence
  -> promotion candidate
  -> evidence summary
  -> explicit promotion record
  -> reviewable promotion references
```

Milestone 21 completed paper-run comparison and review governance:

```text
multiple paper runs
  -> explicit comparison set
  -> comparison summary
  -> review decision record
  -> reviewable comparison references
```

Milestone 22 completed strategy-level decision governance:

```text
decision evidence reference
  -> strategy decision input
  -> strategy decision summary
  -> explicit strategy decision record
  -> decision manifest and references
```

Milestone 23 completed deterministic report-artifact packaging:

```text
report source reference
  -> report section
  -> report artifact summary
  -> report artifact reference and manifest
```

Milestone 24 sits above these completed records. It does not replace or execute them. Its job is to declare where a strategy is in a human-controlled review lifecycle and to record an explicitly reviewed transition between declared states.

This is lifecycle governance, not lifecycle automation.

## Milestone Decision

Milestone 24 is contract-only.

It may add small immutable contracts, deterministic validation, constants, factories, JSON-compatible exports, and local reference/manifest structures. It must not add a transition executor, state repository, workflow engine, orchestration service, scheduler, queue, event bus, CLI lifecycle commands, or configured workflow changes.

## Planned Milestone Chain

```text
strategy review evidence reference contract
  -> strategy lifecycle state snapshot contract
  -> lifecycle transition proposal contract
  -> human-controlled lifecycle transition record
  -> strategy review workflow manifest and references
  -> strategy review workflow closeout
```

## Lifecycle Vocabulary

Milestone 24 uses this conservative vocabulary:

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

The current lifecycle path is closed within Milestone 24. Reopening a rejected lifecycle path is outside this milestone and requires later explicit planning.

Milestone 24 does not include `live_candidate`, `live_ready`, `approved_for_live`, or any equivalent state. Live-readiness semantics belong to a later dedicated milestone.

There is no implicit initial state. A state exists only when a caller explicitly declares a lifecycle state snapshot.

## Permitted Transition Matrix

```text
research_review -> paper_review | watchlist | on_hold | rejected
paper_review    -> research_review | watchlist | on_hold | rejected
watchlist       -> research_review | paper_review | on_hold | rejected
on_hold         -> research_review | paper_review | watchlist | rejected
rejected        -> no transitions in Milestone 24
```

Transition rules:

- no self-transitions
- no implicit transitions
- no automatic transition application
- a transition proposal does not change state
- every accepted transition requires a separate explicit human-controlled transition record
- rejected or deferred proposals leave the declared state unchanged
- existing decision statuses are evidence, not automatic lifecycle mappings
- a completed review decision can exist without causing a lifecycle transition

## Evidence Requirements

Milestone 24 references existing governance artifacts instead of duplicating or loading them.

Candidate evidence-reference types may cover explicit references to:

- promotion records and manifests
- paper comparison summaries
- paper review decision records and manifests
- strategy decision summaries, records, and manifests
- report artifact summaries and manifests

Minimum rules:

- every transition proposal includes at least one explicit strategy decision record reference
- a transition into `paper_review` additionally includes an explicit promotion record reference
- report artifacts may provide review context but are never sufficient by themselves to authorize a transition
- evidence references are pointers only
- evidence references do not discover, load, parse, score, rank, or validate referenced artifacts
- evidence sufficiency remains a human judgment supplied explicitly by the caller

## Human Approval Boundary

The intended governance flow is:

```text
existing governance evidence
  -> caller-supplied transition proposal
  -> explicit human review
  -> caller-supplied transition record
  -> declared lifecycle state snapshot/reference
```

A transition proposal describes a requested change. It does not approve or execute anything.

A transition record captures a human reviewer outcome, rationale, and resulting-state declaration when approved. It does not mutate stored state, run paper workflows, trigger strategy execution, approve broker behavior, claim live readiness, or deploy capital.

Milestone 22 decision statuses must not be automatically mapped to lifecycle states. The caller must make the lifecycle declaration explicitly and attach the relevant evidence references.

## Planned Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S130 | Complete | Plan Milestone 24. | Scope, lifecycle vocabulary, transition matrix, evidence rules, sprint sequence, and guardrails. | Documentation only; no runtime behavior. |
| S131 | Complete | Define strategy review evidence references. | Small typed pointers to completed M20–M23 governance records and manifests. | No discovery, loading, parsing, scoring, ranking, evaluation, or workflow execution. |
| S132 | Planned | Define lifecycle state snapshots. | Explicit caller-supplied strategy review state snapshots using the approved vocabulary. | No implicit initial state, mutable state store, persistence, or state-machine service. |
| S133 | Planned | Define lifecycle transition proposals. | Explicit from-state, target-state, rationale, evidence references, and requester context. | A proposal does not change state or approve anything. |
| S134 | Planned | Add human-controlled lifecycle transition records. | Explicit reviewer outcome, rationale, approval context, and declared resulting-state reference. | No automatic approval, transition execution, paper execution, broker behavior, or readiness claim. |
| S135 | Planned | Add workflow manifests and references. | Local references and manifests for state snapshots, proposals, and transition records. | No file I/O, database, hosted orchestration, dashboard, or workflow engine. |
| S136 | Planned | Close Milestone 24. | Documentation refresh and closeout. | No scope expansion. |

## Included Capabilities

Milestone 24 may include:

- typed strategy review evidence references to completed M20–M23 governance records
- a fixed supported lifecycle-state vocabulary
- immutable caller-supplied lifecycle state snapshots
- deterministic validation of the documented transition matrix
- immutable caller-supplied lifecycle transition proposals
- explicit human-controlled transition records
- local references and manifests for lifecycle governance artifacts
- documentation of lifecycle assumptions, human approval boundaries, and future readiness boundaries

## Architecture Boundary

The safest implementation shape is:

```text
existing M20-M23 records remain separate
strategy review inputs remain explicit
state snapshots remain immutable declarations
transition proposals remain non-executing requests
transition records remain human-controlled governance artifacts
manifests remain local reference contracts
runtime workflow execution remains separate
broker and live readiness remain separate
```

Do not create a generic workflow engine or reusable state-machine framework. Milestone 24 needs narrow domain contracts, not infrastructure.

## Explicitly Out Of Scope

Milestone 24 must not introduce:

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
- CLI commands for lifecycle operations
- file I/O from lifecycle contracts
- persistence services or databases
- generic workflow or state-machine engines
- schedulers, queues, event buses, or hosted orchestration
- dashboards, broad reporting UI, or report generation
- broker integration or broker readiness
- live execution or live readiness
- `live_candidate`, `live_ready`, or equivalent states
- real-money behavior
- capital allocation or deployment
- strategy-signal-to-order conversion
- market-data streaming
- real account synchronization
- hosted services or SaaS behavior
- strategy expansion

## Implementation Sprint Requirements

Every Codex implementation sprint issue must include the Windows proxy prelude:

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7892"
$env:HTTPS_PROXY="http://127.0.0.1:7892"
$env:ALL_PROXY="http://127.0.0.1:7892"

git config http.proxy http://127.0.0.1:7892
git config https.proxy http://127.0.0.1:7892
```

Implementation issues must also state:

- Do not use `--global`.
- Do not commit proxy config.
- Do not modify project files for proxy setup.
- Include the recommended Codex model and reasoning effort.
- Run `uv run python scripts/check.py` before opening the PR.
- Start the PR body with a clean manually typed `Closes #<issue-number>` line.
- Mark the PR Ready for review rather than leaving it as Draft.

## Exit Criteria

Milestone 24 is complete only when:

- strategy review evidence references are explicit and typed
- lifecycle states use the approved vocabulary
- state snapshots are caller-supplied and immutable
- permitted transitions are deterministic and documented
- transition proposals remain non-executing requests
- transition records remain explicit human-controlled governance artifacts
- workflow manifests and references remain local contracts
- existing M20–M23 records remain separate and are referenced rather than duplicated or loaded
- no live-readiness state is introduced
- documentation explains assumptions, human approval boundaries, and future readiness boundaries
- runtime mutation, workflow execution, automatic decisions, broker/live behavior, capital deployment, databases, hosted orchestration, and strategy expansion remain outside the milestone

## Next Step

```text
Sprint 132 — Strategy Lifecycle State Snapshot Foundation
```

Sprint 131 added the smallest useful typed pointers to completed M20–M23 governance records. They do not discover, load, parse, validate, score, rank, or evaluate artifacts; declare lifecycle states; propose, approve, reject, or execute transitions; or imply paper eligibility, broker readiness, live readiness, or capital deployment.

Sprint 132 should define explicit caller-supplied lifecycle state snapshots without implicit state, mutable storage, persistence, or a state-machine service.
