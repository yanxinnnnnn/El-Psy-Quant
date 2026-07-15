import type {
  LifecycleTransitionProposalRequest,
  LifecycleTransitionProposalResponse,
} from "@/lib/api-client";

type Proposal = LifecycleTransitionProposalResponse["proposal"];

function snapshotResponseToRequest(
  snapshot: Proposal["source_snapshot"],
): LifecycleTransitionProposalRequest["source_snapshot"] {
  return {
    snapshot_id: snapshot.snapshot_id,
    strategy_id: snapshot.strategy_id,
    lifecycle_state: snapshot.lifecycle_state,
    rationale: snapshot.rationale,
    declared_by: snapshot.declared_by,
    declared_timestamp: snapshot.declared_timestamp,
    notes: [...snapshot.notes],
    warnings: [...snapshot.warnings],
  };
}

export function proposalResponseToRequest(
  proposal: Proposal,
): LifecycleTransitionProposalRequest {
  return {
    proposal_id: proposal.proposal_id,
    source_snapshot: snapshotResponseToRequest(proposal.source_snapshot),
    target_state: proposal.target_state,
    rationale: proposal.rationale,
    evidence_references: proposal.evidence_references.map((reference) => ({
      reference_type: reference.reference_type,
      reference_id: reference.reference_id,
      label: reference.label,
      description: reference.description,
    })),
    requested_by: proposal.requested_by,
    requested_timestamp: proposal.requested_timestamp,
    notes: [...proposal.notes],
    warnings: [...proposal.warnings],
  };
}

export function lifecycleCommandErrorTitle(code: string): string {
  const titles: Readonly<Record<string, string>> = {
    lifecycle_transition_proposal_invalid: "Lifecycle proposal is invalid",
    lifecycle_transition_record_invalid: "Human review record is invalid",
    request_validation_error: "Lifecycle command structure is invalid",
  };
  return titles[code] ?? "Lifecycle command unavailable";
}
