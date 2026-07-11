import pytest

from el_psy_quant.strategy_review import (
    PERMITTED_STRATEGY_LIFECYCLE_TRANSITIONS,
    StrategyLifecycleTransitionProposal,
    create_strategy_lifecycle_state_snapshot,
    create_strategy_lifecycle_transition_proposal,
    create_strategy_review_evidence_reference,
)


def _snapshot(state: str):
    return create_strategy_lifecycle_state_snapshot(
        snapshot_id="s",
        strategy_id="strategy",
        lifecycle_state=state,
        rationale="rationale",
    )


def _evidence(*types: str):
    return [
        create_strategy_review_evidence_reference(
            reference_type=value, reference_id=value
        )
        for value in types
    ]


def test_transition_tuple_is_exact_size_and_immutable():
    assert len(PERMITTED_STRATEGY_LIFECYCLE_TRANSITIONS) == 16
    assert PERMITTED_STRATEGY_LIFECYCLE_TRANSITIONS[0] == (
        "research_review",
        "paper_review",
    )


@pytest.mark.parametrize("source,target", PERMITTED_STRATEGY_LIFECYCLE_TRANSITIONS)
def test_all_permitted_pairs_create(source: str, target: str):
    types = (
        ("strategy_decision_record", "promotion_record")
        if target == "paper_review"
        else ("strategy_decision_record",)
    )
    proposal = create_strategy_lifecycle_transition_proposal(
        proposal_id="p",
        source_snapshot=_snapshot(source),
        target_state=target,
        rationale="rationale",
        evidence_references=_evidence(*types),
    )
    assert isinstance(proposal, StrategyLifecycleTransitionProposal)
    assert proposal.target_state == target


def test_minimum_evidence_and_invalid_pairs_are_rejected():
    with pytest.raises(ValueError, match="strategy_decision_record"):
        create_strategy_lifecycle_transition_proposal(
            proposal_id="p",
            source_snapshot=_snapshot("research_review"),
            target_state="watchlist",
            rationale="r",
            evidence_references=_evidence("report_artifact_summary"),
        )
    with pytest.raises(ValueError, match="promotion_record"):
        create_strategy_lifecycle_transition_proposal(
            proposal_id="p",
            source_snapshot=_snapshot("research_review"),
            target_state="paper_review",
            rationale="r",
            evidence_references=_evidence("strategy_decision_record"),
        )
    with pytest.raises(ValueError, match="permitted transition"):
        create_strategy_lifecycle_transition_proposal(
            proposal_id="p",
            source_snapshot=_snapshot("rejected"),
            target_state="watchlist",
            rationale="r",
            evidence_references=_evidence("strategy_decision_record"),
        )


def test_serialization_preserves_nested_contracts_and_order():
    proposal = create_strategy_lifecycle_transition_proposal(
        proposal_id=" p ",
        source_snapshot=_snapshot("research_review"),
        target_state=" watchlist ",
        rationale=" r ",
        evidence_references=_evidence(
            "strategy_decision_record", "report_artifact_summary"
        ),
        notes=[" n "],
    )
    assert (
        proposal.to_dict()["evidence_references"][1]["reference_type"]
        == "report_artifact_summary"
    )
    assert proposal.notes == ("n",)
