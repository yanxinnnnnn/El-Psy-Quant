# Sprint 133 — Lifecycle Transition Proposal Foundation

## Status

Complete.

## Goal

Add immutable caller-supplied requests for a permitted strategy lifecycle transition without approving, executing, or applying that transition.

## Delivered

- Exact deterministic 16-pair permitted transition matrix.
- Rejection of self-transitions and every outgoing transition from `rejected`.
- Minimum evidence-type presence rules.
- Caller-order-preserving immutable evidence references.
- Timestamp and string-sequence normalization.
- Deterministic JSON-compatible nested serialization.

## Public API

```text
STRATEGY_LIFECYCLE_TRANSITION_PROPOSAL_SCHEMA_VERSION
PERMITTED_STRATEGY_LIFECYCLE_TRANSITIONS
StrategyLifecycleTransitionProposal
create_strategy_lifecycle_transition_proposal(...)
```

## Contract Shape

```text
schema_version
proposal_id
source_snapshot
target_state
rationale
evidence_references
requested_by
requested_timestamp
notes
warnings
```

## Transition Rules

Only the documented 16 ordered state pairs are accepted. Self-transitions and all outgoing transitions from `rejected` are invalid. Validation checks a requested pair but does not approve, reject, defer, execute, or mutate anything. The source snapshot remains unchanged, and proposal creation does not create a resulting snapshot.

## Evidence Rules

Every proposal requires at least one `strategy_decision_record` reference. Entering `paper_review` additionally requires a `promotion_record` reference. Report artifacts may provide context but are insufficient alone. References remain pointers: payloads are not discovered, loaded, parsed, validated, scored, ranked, or evaluated, and decision statuses are not mapped automatically.

## Scope Guardrails

Sprint 133 adds no review outcome, transition record, reviewer fields, resulting snapshot, mutable current state, transition execution, persistence, file I/O, workflow engine, broker/live behavior, readiness claim, or capital allocation.

## Next Step

```text
Sprint 134 — Human-Controlled Lifecycle Transition Record Foundation
```

Sprint 134 should record explicit human review outcomes without turning governance records into transition execution.
