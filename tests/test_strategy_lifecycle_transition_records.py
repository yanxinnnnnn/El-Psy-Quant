import inspect
import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.strategy_review import (
    STRATEGY_LIFECYCLE_TRANSITION_RECORD_SCHEMA_VERSION,
    SUPPORTED_STRATEGY_LIFECYCLE_TRANSITION_RECORD_OUTCOMES,
    StrategyLifecycleTransitionRecord,
    create_strategy_lifecycle_state_snapshot,
    create_strategy_lifecycle_transition_proposal,
    create_strategy_lifecycle_transition_record,
    create_strategy_review_evidence_reference,
)


def _snapshot(
    state: str = "research_review",
    *,
    strategy_id: str = "strategy-1",
    snapshot_id: str = "snapshot-1",
):
    return create_strategy_lifecycle_state_snapshot(
        snapshot_id=snapshot_id,
        strategy_id=strategy_id,
        lifecycle_state=state,
        rationale="Caller-supplied state.",
    )


def _proposal(target: str = "watchlist"):
    references = [
        create_strategy_review_evidence_reference(
            reference_type="strategy_decision_record",
            reference_id="decision-1",
        )
    ]
    if target == "paper_review":
        references.append(
            create_strategy_review_evidence_reference(
                reference_type="promotion_record",
                reference_id="promotion-1",
            )
        )
    return create_strategy_lifecycle_transition_proposal(
        proposal_id="proposal-1",
        source_snapshot=_snapshot(),
        target_state=target,
        rationale="Request a reviewed transition.",
        evidence_references=references,
    )


def _record(outcome: str = "approved", **kwargs):
    proposal = kwargs.pop("proposal", _proposal())
    snapshot = kwargs.pop("resulting_snapshot", None)
    if (
        isinstance(outcome, str)
        and outcome.strip() == "approved"
        and snapshot is None
        and hasattr(proposal, "target_state")
    ):
        snapshot = _snapshot(
            proposal.target_state,
            snapshot_id="snapshot-2",
            strategy_id=proposal.source_snapshot.strategy_id,
        )
    return create_strategy_lifecycle_transition_record(
        transition_record_id=kwargs.pop("transition_record_id", "record-1"),
        proposal=proposal,
        review_outcome=outcome,
        rationale=kwargs.pop("rationale", "Human review outcome."),
        resulting_snapshot=snapshot,
        **kwargs,
    )


def test_public_constants_are_exact():
    assert STRATEGY_LIFECYCLE_TRANSITION_RECORD_SCHEMA_VERSION == 1
    assert SUPPORTED_STRATEGY_LIFECYCLE_TRANSITION_RECORD_OUTCOMES == (
        "approved",
        "rejected",
        "deferred",
    )


@pytest.mark.parametrize("outcome", ("approved", "rejected", "deferred"))
def test_all_supported_outcomes_create_valid_records(outcome: str):
    kwargs = {} if outcome == "approved" else {"resulting_snapshot": None}
    assert _record(outcome, **kwargs).review_outcome == outcome


@pytest.mark.parametrize("outcome", ("approved", "rejected", "deferred"))
def test_outcomes_trim_whitespace(outcome: str):
    kwargs = {} if outcome == "approved" else {"resulting_snapshot": None}
    assert _record(f" {outcome} ", **kwargs).review_outcome == outcome


@pytest.mark.parametrize("value", ("accepted", "", "   ", object()))
def test_invalid_outcomes_are_rejected(value):
    with pytest.raises(ValueError, match="review_outcome"):
        _record(value, resulting_snapshot=None)


def test_invalid_proposal_type_is_rejected():
    with pytest.raises(ValueError, match="proposal"):
        _record(proposal=object())


def test_proposal_identity_and_immutability_are_preserved():
    proposal = _proposal()
    before = proposal.to_dict()
    record = _record(proposal=proposal)
    assert record.proposal is proposal
    assert proposal.to_dict() == before


def test_approved_requires_a_resulting_snapshot():
    proposal = _proposal()
    with pytest.raises(ValueError, match="require resulting_snapshot"):
        create_strategy_lifecycle_transition_record(
            transition_record_id="record-1",
            proposal=proposal,
            review_outcome="approved",
            rationale="Approved by a human.",
        )


def test_approved_rejects_invalid_resulting_snapshot_type():
    with pytest.raises(ValueError, match="StrategyLifecycleStateSnapshot"):
        _record(resulting_snapshot=object())


def test_approved_rejects_mismatched_strategy_and_target_state():
    with pytest.raises(ValueError, match="strategy_id"):
        _record(
            resulting_snapshot=_snapshot(
                "watchlist", strategy_id="strategy-2", snapshot_id="snapshot-2"
            )
        )
    with pytest.raises(ValueError, match="target_state"):
        _record(
            resulting_snapshot=_snapshot(
                "on_hold", strategy_id="strategy-1", snapshot_id="snapshot-2"
            )
        )


def test_approved_accepts_matching_snapshot_and_preserves_identity():
    proposal = _proposal("paper_review")
    snapshot = _snapshot("paper_review", snapshot_id="snapshot-2")
    before = snapshot.to_dict()
    record = _record(proposal=proposal, resulting_snapshot=snapshot)
    assert record.resulting_snapshot is snapshot
    assert snapshot.to_dict() == before


@pytest.mark.parametrize("outcome", ("rejected", "deferred"))
def test_non_approved_outcomes_require_no_resulting_snapshot(outcome: str):
    assert _record(outcome, resulting_snapshot=None).resulting_snapshot is None
    with pytest.raises(ValueError, match="must not include"):
        _record(
            outcome,
            resulting_snapshot=_snapshot("watchlist", snapshot_id="snapshot-2"),
        )


def test_source_snapshot_remains_unchanged():
    proposal = _proposal()
    source = proposal.source_snapshot
    before = source.to_dict()
    _record("rejected", proposal=proposal, resulting_snapshot=None)
    assert proposal.source_snapshot is source
    assert source.to_dict() == before


def test_required_and_optional_strings_normalize():
    record = _record(
        transition_record_id=" record-1 ",
        rationale=" rationale ",
        reviewed_by=" reviewer ",
    )
    assert record.transition_record_id == "record-1"
    assert record.rationale == "rationale"
    assert record.reviewed_by == "reviewer"
    assert _record(reviewed_by="  ").reviewed_by is None


@pytest.mark.parametrize("field", ("transition_record_id", "rationale"))
@pytest.mark.parametrize("value", ("", "   ", object()))
def test_empty_and_invalid_required_fields_are_rejected(field: str, value):
    with pytest.raises(ValueError, match=field):
        _record(**{field: value})


def test_invalid_reviewed_by_is_rejected():
    with pytest.raises(ValueError, match="reviewed_by"):
        _record(reviewed_by=object())


def test_timestamp_normalizes_and_serializes():
    record = _record(reviewed_timestamp="2026-01-02T03:04:05")
    assert record.to_dict()["reviewed_timestamp"] == "2026-01-02T03:04:05"


@pytest.mark.parametrize("value", ("invalid", "NaT", object()))
def test_invalid_timestamps_are_rejected(value):
    with pytest.raises(ValueError, match="reviewed_timestamp"):
        _record(reviewed_timestamp=value)


def test_notes_and_warnings_are_trimmed_immutable_tuples():
    notes = [" note "]
    warnings = [" warning "]
    record = _record(notes=notes, warnings=warnings)
    notes.append("later")
    warnings.append("later")
    assert record.notes == ("note",)
    assert record.warnings == ("warning",)


@pytest.mark.parametrize("field", ("notes", "warnings"))
@pytest.mark.parametrize("value", ("bare", [""], [object()], object()))
def test_invalid_notes_and_warnings_are_rejected(field: str, value):
    with pytest.raises(ValueError, match=field):
        _record(**{field: value})


def test_complete_approved_serialization_is_deterministic_and_json_compatible():
    proposal = _proposal()
    snapshot = _snapshot("watchlist", snapshot_id="snapshot-2")
    record = _record(
        proposal=proposal,
        resulting_snapshot=snapshot,
        reviewed_by="reviewer",
        reviewed_timestamp="2026-01-02T03:04:05",
        notes=["note"],
        warnings=["warning"],
    )
    expected = {
        "schema_version": STRATEGY_LIFECYCLE_TRANSITION_RECORD_SCHEMA_VERSION,
        "transition_record_id": "record-1",
        "proposal": proposal.to_dict(),
        "review_outcome": "approved",
        "rationale": "Human review outcome.",
        "resulting_snapshot": snapshot.to_dict(),
        "reviewed_by": "reviewer",
        "reviewed_timestamp": "2026-01-02T03:04:05",
        "notes": ["note"],
        "warnings": ["warning"],
    }
    assert record.to_dict() == expected == record.to_dict()
    json.dumps(record.to_dict(), allow_nan=False)


@pytest.mark.parametrize("outcome", ("rejected", "deferred"))
def test_complete_non_approved_serialization(outcome: str):
    record = _record(outcome, resulting_snapshot=None)
    assert record.to_dict()["resulting_snapshot"] is None
    assert record.to_dict()["review_outcome"] == outcome
    json.dumps(record.to_dict(), allow_nan=False)


def test_frozen_explicit_keyword_only_factory_and_package_exports():
    record = _record()
    with pytest.raises(FrozenInstanceError):
        record.review_outcome = "rejected"  # type: ignore[misc]
    parameters = inspect.signature(
        create_strategy_lifecycle_transition_record
    ).parameters
    assert "kwargs" not in parameters
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in parameters.values()
    )
    from el_psy_quant import strategy_review

    assert (
        strategy_review.StrategyLifecycleTransitionRecord
        is StrategyLifecycleTransitionRecord
    )
    assert strategy_review.SUPPORTED_STRATEGY_LIFECYCLE_TRANSITION_RECORD_OUTCOMES == (
        "approved",
        "rejected",
        "deferred",
    )


def test_package_has_no_execution_current_state_persistence_or_live_behavior():
    from el_psy_quant import strategy_review

    forbidden = {
        "apply_lifecycle_transition",
        "execute_lifecycle_transition",
        "create_resulting_snapshot",
        "get_current_lifecycle_state",
        "set_current_lifecycle_state",
        "save_transition_record",
        "run_strategy_review_workflow",
        "mark_broker_ready",
        "mark_live_ready",
        "allocate_capital",
    }
    assert all(not hasattr(strategy_review, name) for name in forbidden)
