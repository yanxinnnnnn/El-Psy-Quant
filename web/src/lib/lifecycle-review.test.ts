import { describe, expect, it } from "vitest";

import type { LifecycleTransitionProposalResponse } from "@/lib/api-client";
import {
  lifecycleCommandErrorTitle,
  proposalResponseToRequest,
} from "@/lib/lifecycle-review";

const proposal: LifecycleTransitionProposalResponse["proposal"] = {
  schema_version: 1,
  proposal_id: "proposal-158",
  source_snapshot: {
    schema_version: 1,
    snapshot_id: "snapshot-source",
    strategy_id: "moving_average_crossover",
    lifecycle_state: "research_review",
    rationale: "normalized source",
    declared_by: "founder",
    declared_timestamp: "2026-07-15T10:00:00+00:00",
    notes: ["source note", "source note"],
    warnings: [],
  },
  target_state: "paper_candidate",
  rationale: "normalized proposal",
  evidence_references: [
    {
      schema_version: 1,
      reference_type: "strategy_decision_record",
      reference_id: "decision-a",
      label: "Decision A",
      description: null,
    },
    {
      schema_version: 1,
      reference_type: "strategy_decision_record",
      reference_id: "decision-a",
      label: null,
      description: "duplicate pointer remains explicit",
    },
  ],
  requested_by: null,
  requested_timestamp: "2026-07-15T10:05:00+00:00",
  notes: ["proposal note"],
  warnings: ["proposal warning"],
};

describe("lifecycle review transport helpers", () => {
  it("projects the normalized proposal response into the generated review request shape", () => {
    expect(proposalResponseToRequest(proposal)).toEqual({
      proposal_id: "proposal-158",
      source_snapshot: {
        snapshot_id: "snapshot-source",
        strategy_id: "moving_average_crossover",
        lifecycle_state: "research_review",
        rationale: "normalized source",
        declared_by: "founder",
        declared_timestamp: "2026-07-15T10:00:00+00:00",
        notes: ["source note", "source note"],
        warnings: [],
      },
      target_state: "paper_candidate",
      rationale: "normalized proposal",
      evidence_references: [
        {
          reference_type: "strategy_decision_record",
          reference_id: "decision-a",
          label: "Decision A",
          description: null,
        },
        {
          reference_type: "strategy_decision_record",
          reference_id: "decision-a",
          label: null,
          description: "duplicate pointer remains explicit",
        },
      ],
      requested_by: null,
      requested_timestamp: "2026-07-15T10:05:00+00:00",
      notes: ["proposal note"],
      warnings: ["proposal warning"],
    });
  });

  it("uses bounded endpoint-specific titles without interpreting governance outcomes", () => {
    expect(lifecycleCommandErrorTitle("lifecycle_transition_proposal_invalid")).toBe(
      "Lifecycle proposal is invalid",
    );
    expect(lifecycleCommandErrorTitle("lifecycle_transition_record_invalid")).toBe(
      "Human review record is invalid",
    );
    expect(lifecycleCommandErrorTitle("private_exception")).toBe(
      "Lifecycle command unavailable",
    );
  });
});
