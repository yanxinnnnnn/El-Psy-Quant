# Lifecycle Review

Lifecycle Review creates a non-executing transition proposal and then records a
separate, explicit human review response. It is a governance workspace, not an
automatic state machine.

## Prepare the Evidence

Before opening the form, confirm the strategy identity, source lifecycle
snapshot, proposed target, rationale, and exact evidence reference IDs.

Supported lifecycle states are:

- `research_review`
- `paper_review`
- `watchlist`
- `on_hold`
- `rejected`

A proposal may move between different non-rejected states or from a
non-rejected state to `rejected`. A `rejected` state has no outgoing transition.

Every proposal requires at least one evidence reference and must include a
`strategy_decision_record`. A proposal targeting `paper_review` must also
include a `promotion_record`. Other supported reference types are
`promotion_manifest`, `paper_comparison_summary`, `paper_review_decision`,
`paper_review_manifest`, `strategy_decision_summary`,
`strategy_decision_manifest`, `report_artifact_summary`, and
`report_artifact_manifest`.

References are unresolved pointers. Enter only exact IDs from evidence you have
already reviewed.

## Step 1: Create a Proposal

Enter the source snapshot ID, strategy ID, lifecycle state, and rationale.
Optional declaration metadata, notes, and warnings may be added. Then enter the
proposal ID, target state, rationale, optional request metadata, and ordered
evidence references.

Choose **Create non-executing proposal**. The backend validates the states,
transition, and evidence requirements and returns a normalized proposal for
inspection. This response is not approval and does not change the strategy.

## Step 2: Record the Human Review

After a proposal response is available, enter the transition record ID, outcome,
rationale, reviewer metadata, notes, and warnings. Supported outcomes are:

- `approved`
- `rejected`
- `deferred`

An `approved` review requires an explicit resulting snapshot for the same
strategy and the proposal's target state. A `rejected` or `deferred` review must
not include a resulting snapshot.

Choose **Record human review evidence**. The workspace displays the normalized
record and an in-session timeline containing the source snapshot, proposal,
human review record, and optional resulting snapshot.

## Human Authority and Session Limits

The outcome is entered by the human reviewer; the workspace does not infer it
from metrics, evidence quantity, or proposal content. A returned review record
does not prove transition execution, promote the strategy, mark a snapshot as
globally current, allocate capital, or start a paper job.

The page is stateless. Its proposal, review response, and timeline are visible
only in the current browser session and are not a persisted lifecycle history.
Human-controlled governance outside this page remains responsible for any later
action.
