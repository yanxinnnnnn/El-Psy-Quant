"""Tests for strategy lifecycle transition proposals."""

import inspect
import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.strategy_review import (
    PERMITTED_STRATEGY_LIFECYCLE_TRANSITIONS,
    STRATEGY_LIFECYCLE_TRANSITION_PROPOSAL_SCHEMA_VERSION,
    SUPPORTED_STRATEGY_LIFECYCLE_STATES,
    StrategyLifecycleTransitionProposal,
    create_strategy_lifecycle_state_snapshot,
    create_strategy_lifecycle_transition_proposal,
    create_strategy_review_evidence_reference,
)

EXPECTED_TRANSITIONS = (
    ("research_review", "paper_review"),
    ("research_review", "watchlist"),
    ("research_review", "on_hold"),
    ("research_review", "rejected"),
    ("paper_review", "research_review"),
    ("paper_review", "watchlist"),
    ("paper_review", "on_hold"),
    ("paper_review", "rejected"),
    ("watchlist", "research_review"),
    ("watchlist", "paper_review"),
    ("watchlist", "on_hold"),
    ("watchlist", "rejected"),
    ("on_hold", "research_review"),
    ("on_hold", "paper_review"),
    ("on_hold", "watchlist"),
    ("on_hold", "rejected"),
)


def _snapshot(state: str = "research_review"):
    return create_strategy_lifecycle_state_snapshot(
        snapshot_id="snapshot-1",
        strategy_id="strategy-1",
        lifecycle_state=state,
        rationale="Current caller-supplied state.",
    )


def _reference(reference_type: str, reference_id: str | None = None):
    return create_strategy_review_evidence_reference(
        reference_type=reference_type,
        reference_id=reference_id or reference_type,
    )


def _proposal(source: str = "research_review", target: str = "watchlist", **kwargs):
    evidence = kwargs.pop("evidence_references", None)
    if evidence is None:
        evidence = [_reference("strategy_decision_record")]
        if target.strip() == "paper_review":
            evidence.append(_reference("promotion_record"))
    return create_strategy_lifecycle_transition_proposal(
        proposal_id=kwargs.pop("proposal_id", "proposal-1"),
        source_snapshot=kwargs.pop("source_snapshot", _snapshot(source)),
        target_state=target,
        rationale=kwargs.pop("rationale", "Request a reviewed state change."),
        evidence_references=evidence,
        **kwargs,
    )


def test_transition_matrix_is_exact_deterministic_and_json_compatible():
    assert PERMITTED_STRATEGY_LIFECYCLE_TRANSITIONS == EXPECTED_TRANSITIONS
    json.dumps(PERMITTED_STRATEGY_LIFECYCLE_TRANSITIONS, allow_nan=False)


@pytest.mark.parametrize("source,target", EXPECTED_TRANSITIONS)
def test_every_permitted_pair_can_be_proposed(source: str, target: str):
    assert _proposal(source, target).target_state == target


@pytest.mark.parametrize("state", SUPPORTED_STRATEGY_LIFECYCLE_STATES)
def test_self_transitions_are_rejected(state: str):
    with pytest.raises(ValueError, match="permitted transition"):
        _proposal(state, state)


@pytest.mark.parametrize("target", SUPPORTED_STRATEGY_LIFECYCLE_STATES[:-1])
def test_outgoing_transitions_from_rejected_are_rejected(target: str):
    with pytest.raises(ValueError, match="permitted transition"):
        _proposal("rejected", target)


def test_unsupported_target_and_invalid_source_are_rejected():
    with pytest.raises(ValueError, match="unsupported target_state"):
        _proposal(target="live_ready")
    with pytest.raises(ValueError, match="source_snapshot"):
        _proposal(source_snapshot=object())


def test_target_and_string_fields_normalize():
    proposal = _proposal(
        target=" watchlist ",
        proposal_id=" proposal-1 ",
        rationale=" rationale ",
        requested_by=" reviewer ",
    )
    assert (proposal.proposal_id, proposal.target_state, proposal.rationale) == (
        "proposal-1",
        "watchlist",
        "rationale",
    )
    assert proposal.requested_by == "reviewer"
    assert _proposal(requested_by="  ").requested_by is None


@pytest.mark.parametrize("field", ["proposal_id", "rationale"])
@pytest.mark.parametrize("value", ["", "   ", object()])
def test_required_fields_reject_empty_and_invalid_values(field: str, value):
    with pytest.raises(ValueError, match=field):
        _proposal(**{field: value})


@pytest.mark.parametrize("value", ["text", object(), [], [object()]])
def test_invalid_evidence_sequences_are_rejected(value):
    with pytest.raises(ValueError, match="evidence_references"):
        _proposal(evidence_references=value)


def test_evidence_is_immutable_ordered_and_not_deduplicated():
    first = _reference("strategy_decision_record", "decision-1")
    second = _reference("report_artifact_summary", "report-1")
    values = [first, second, first]
    proposal = _proposal(evidence_references=values)
    values.append(second)
    assert proposal.evidence_references == (first, second, first)


def test_minimum_evidence_rules():
    with pytest.raises(ValueError, match="strategy_decision_record"):
        _proposal(evidence_references=[_reference("report_artifact_manifest")])
    with pytest.raises(ValueError, match="promotion_record"):
        _proposal(
            target="paper_review",
            evidence_references=[_reference("strategy_decision_record")],
        )
    proposal = _proposal(
        target="paper_review",
        evidence_references=[
            _reference("promotion_record"),
            _reference("strategy_decision_record"),
        ],
    )
    assert proposal.target_state == "paper_review"


def test_timestamp_and_sequences_normalize_and_validate():
    proposal = _proposal(
        requested_timestamp="2026-01-02T03:04:05",
        notes=[" note "],
        warnings=[" warning "],
    )
    assert proposal.to_dict()["requested_timestamp"] == "2026-01-02T03:04:05"
    assert proposal.notes == ("note",)
    assert proposal.warnings == ("warning",)
    for value in ("invalid", "NaT"):
        with pytest.raises(ValueError, match="requested_timestamp"):
            _proposal(requested_timestamp=value)
    for field in ("notes", "warnings"):
        for value in ("bare", [""], [object()]):
            with pytest.raises(ValueError, match=field):
                _proposal(**{field: value})


def test_complete_serialization_is_deterministic_and_nested():
    source = _snapshot()
    evidence = [
        _reference("strategy_decision_record"),
        _reference("report_artifact_summary"),
    ]
    proposal = _proposal(
        source_snapshot=source,
        evidence_references=evidence,
        requested_by="reviewer",
        requested_timestamp="2026-01-02T03:04:05",
        notes=["note"],
        warnings=["warning"],
    )
    expected = {
        "schema_version": STRATEGY_LIFECYCLE_TRANSITION_PROPOSAL_SCHEMA_VERSION,
        "proposal_id": "proposal-1",
        "source_snapshot": source.to_dict(),
        "target_state": "watchlist",
        "rationale": "Request a reviewed state change.",
        "evidence_references": [item.to_dict() for item in evidence],
        "requested_by": "reviewer",
        "requested_timestamp": "2026-01-02T03:04:05",
        "notes": ["note"],
        "warnings": ["warning"],
    }
    assert proposal.to_dict() == expected == proposal.to_dict()
    json.dumps(proposal.to_dict(), allow_nan=False)
    assert proposal.source_snapshot is source
    assert source == _snapshot()


def test_immutable_explicit_public_contract_and_exports():
    proposal = _proposal()
    with pytest.raises(FrozenInstanceError):
        proposal.target_state = "on_hold"  # type: ignore[misc]
    parameters = inspect.signature(
        create_strategy_lifecycle_transition_proposal
    ).parameters
    assert "kwargs" not in parameters
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in parameters.values()
    )
    from el_psy_quant import strategy_review

    assert (
        strategy_review.StrategyLifecycleTransitionProposal
        is StrategyLifecycleTransitionProposal
    )
    assert (
        strategy_review.PERMITTED_STRATEGY_LIFECYCLE_TRANSITIONS == EXPECTED_TRANSITIONS
    )


def test_package_does_not_expose_outcomes_execution_or_live_behavior():
    from el_psy_quant import strategy_review

    forbidden = {
        "LifecycleTransitionRecord",
        "approve_lifecycle_transition",
        "reject_lifecycle_transition",
        "defer_lifecycle_transition",
        "apply_lifecycle_transition",
        "create_resulting_snapshot",
        "get_current_lifecycle_state",
        "mark_live_ready",
        "allocate_capital",
    }
    assert all(not hasattr(strategy_review, name) for name in forbidden)
