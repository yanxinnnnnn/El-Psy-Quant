"""Tests for synchronous in-memory lifecycle application commands."""

import inspect
import socket
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

import el_psy_quant.application.lifecycle_commands as service
from el_psy_quant.application import (
    LifecycleTransitionProposalCommand,
    LifecycleTransitionProposalCommandResult,
    LifecycleTransitionProposalInvalidError,
    LifecycleTransitionRecordInvalidError,
    LifecycleTransitionReviewCommand,
    LifecycleTransitionReviewCommandResult,
    StrategyLifecycleStateSnapshotCommandInput,
    StrategyLifecycleTransitionProposalView,
    StrategyLifecycleTransitionRecordView,
    StrategyReviewEvidenceReferenceCommandInput,
    create_lifecycle_transition_proposal,
    record_lifecycle_transition_review,
)


def _snapshot(
    state: object = " research_review ",
    *,
    strategy_id: object = " strategy-1 ",
    snapshot_id: object = " source-1 ",
) -> StrategyLifecycleStateSnapshotCommandInput:
    return StrategyLifecycleStateSnapshotCommandInput(
        snapshot_id=snapshot_id,
        strategy_id=strategy_id,
        lifecycle_state=state,
        rationale=" source rationale ",
        declared_by=" founder ",
        declared_timestamp="2026-07-13T13:00:00Z",
        notes=(" source note ",),
        warnings=(" source warning ",),
    )


def _reference(
    reference_type: object,
    reference_id: object,
) -> StrategyReviewEvidenceReferenceCommandInput:
    return StrategyReviewEvidenceReferenceCommandInput(
        reference_type=reference_type,
        reference_id=reference_id,
        label=" evidence label ",
    )


def _proposal(
    target_state: object = " paper_review ",
    *,
    source_snapshot: StrategyLifecycleStateSnapshotCommandInput | None = None,
    evidence_references: tuple[
        StrategyReviewEvidenceReferenceCommandInput, ...
    ]
    | None = None,
) -> LifecycleTransitionProposalCommand:
    references = evidence_references
    if references is None:
        references = (
            _reference("strategy_decision_record", "decision-1"),
            _reference("promotion_record", "promotion-1"),
            _reference("strategy_decision_record", "decision-1"),
        )
    return LifecycleTransitionProposalCommand(
        proposal_id=" proposal-1 ",
        source_snapshot=source_snapshot or _snapshot(),
        target_state=target_state,
        rationale=" proposal rationale ",
        evidence_references=references,
        requested_by=" founder ",
        requested_timestamp="2026-07-13T13:05:00Z",
        notes=(" proposal note 1 ", " proposal note 2 "),
        warnings=(" proposal warning 1 ", " proposal warning 2 "),
    )


def _review(
    outcome: object = "approved",
    *,
    proposal: LifecycleTransitionProposalCommand | None = None,
    resulting_snapshot: StrategyLifecycleStateSnapshotCommandInput | None = None,
) -> LifecycleTransitionReviewCommand:
    proposal_command = proposal or _proposal()
    if outcome == "approved" and resulting_snapshot is None:
        resulting_snapshot = _snapshot(
            "paper_review", snapshot_id="result-1"
        )
    return LifecycleTransitionReviewCommand(
        transition_record_id=" record-1 ",
        proposal=proposal_command,
        review_outcome=outcome,
        rationale=" review rationale ",
        resulting_snapshot=resulting_snapshot,
        reviewed_by=" founder ",
        reviewed_timestamp="2026-07-13T13:10:00Z",
        notes=(" record note 1 ", " record note 2 "),
        warnings=(" record warning 1 ", " record warning 2 "),
    )


def test_public_contracts_are_frozen_and_services_are_keyword_only() -> None:
    proposal_command = _proposal()
    review_command = _review(proposal=proposal_command)
    proposal_result = create_lifecycle_transition_proposal(
        command=proposal_command
    )
    review_result = record_lifecycle_transition_review(command=review_command)

    for function in (
        create_lifecycle_transition_proposal,
        record_lifecycle_transition_review,
    ):
        parameter = next(iter(inspect.signature(function).parameters.values()))
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    for value in (
        proposal_command,
        proposal_command.source_snapshot,
        proposal_command.evidence_references[0],
        review_command,
        review_command.resulting_snapshot,
        proposal_result,
        proposal_result.proposal,
        proposal_result.proposal.source_snapshot,
        proposal_result.proposal.evidence_references[0],
        review_result,
        review_result.transition_record,
    ):
        with pytest.raises(FrozenInstanceError):
            value.unexpected = "changed"  # type: ignore[union-attr]
    assert isinstance(proposal_command.evidence_references, tuple)
    assert isinstance(proposal_command.notes, tuple)
    assert isinstance(review_command.notes, tuple)


def test_proposal_uses_each_public_factory_and_preserves_order(monkeypatch) -> None:
    calls: list[str] = []
    expected_counts = {
        "create_strategy_lifecycle_state_snapshot": 1,
        "create_strategy_review_evidence_reference": 3,
        "create_strategy_lifecycle_transition_proposal": 1,
    }
    for name in expected_counts:
        original = getattr(service, name)

        def tracked(*args, _name=name, _original=original, **kwargs):
            calls.append(_name)
            return _original(*args, **kwargs)

        monkeypatch.setattr(service, name, tracked)

    result = create_lifecycle_transition_proposal(command=_proposal())

    assert {name: calls.count(name) for name in expected_counts} == expected_counts
    assert calls[-1] == "create_strategy_lifecycle_transition_proposal"
    assert tuple(
        reference.reference_id for reference in result.proposal.evidence_references
    ) == ("decision-1", "promotion-1", "decision-1")


def test_review_reconstructs_complete_chain_and_calls_record_factory(
    monkeypatch,
) -> None:
    calls: list[str] = []
    expected_counts = {
        "create_strategy_lifecycle_state_snapshot": 2,
        "create_strategy_review_evidence_reference": 3,
        "create_strategy_lifecycle_transition_proposal": 1,
        "create_strategy_lifecycle_transition_record": 1,
    }
    for name in expected_counts:
        original = getattr(service, name)

        def tracked(*args, _name=name, _original=original, **kwargs):
            calls.append(_name)
            return _original(*args, **kwargs)

        monkeypatch.setattr(service, name, tracked)

    result = record_lifecycle_transition_review(command=_review())

    assert {name: calls.count(name) for name in expected_counts} == expected_counts
    assert calls[-1] == "create_strategy_lifecycle_transition_record"
    assert isinstance(result, LifecycleTransitionReviewCommandResult)


def test_normalized_proposal_view_matches_domain_behavior() -> None:
    result = create_lifecycle_transition_proposal(command=_proposal())
    proposal = result.proposal

    assert isinstance(result, LifecycleTransitionProposalCommandResult)
    assert isinstance(proposal, StrategyLifecycleTransitionProposalView)
    assert proposal.schema_version == 1
    assert proposal.proposal_id == "proposal-1"
    assert proposal.source_snapshot.snapshot_id == "source-1"
    assert proposal.source_snapshot.strategy_id == "strategy-1"
    assert proposal.source_snapshot.lifecycle_state == "research_review"
    assert proposal.source_snapshot.declared_timestamp == (
        "2026-07-13T13:00:00+00:00"
    )
    assert proposal.target_state == "paper_review"
    assert proposal.requested_timestamp == "2026-07-13T13:05:00+00:00"
    assert proposal.notes == ("proposal note 1", "proposal note 2")
    assert proposal.warnings == (
        "proposal warning 1",
        "proposal warning 2",
    )


@pytest.mark.parametrize("target", ("paper_review", "watchlist", "on_hold", "rejected"))
def test_representative_permitted_proposals(target: str) -> None:
    references = (_reference("strategy_decision_record", "decision-1"),)
    if target == "paper_review":
        references += (_reference("promotion_record", "promotion-1"),)

    result = create_lifecycle_transition_proposal(
        command=_proposal(target, evidence_references=references)
    )

    assert result.proposal.target_state == target


@pytest.mark.parametrize("outcome", ("approved", "rejected", "deferred"))
def test_supported_human_review_outcomes(outcome: str) -> None:
    snapshot = _snapshot("paper_review", snapshot_id="result-1")
    command = _review(
        outcome,
        resulting_snapshot=snapshot if outcome == "approved" else None,
    )

    result = record_lifecycle_transition_review(command=command)
    record = result.transition_record

    assert isinstance(record, StrategyLifecycleTransitionRecordView)
    assert record.review_outcome == outcome
    assert (record.resulting_snapshot is not None) is (outcome == "approved")
    assert record.notes == ("record note 1", "record note 2")
    assert record.warnings == ("record warning 1", "record warning 2")


@pytest.mark.parametrize(
    "command",
    (
        _proposal("research_review"),
        _proposal(
            evidence_references=(
                _reference("report_artifact_manifest", "private-evidence"),
            )
        ),
    ),
)
def test_proposal_domain_failures_use_fixed_sanitized_error(
    command: LifecycleTransitionProposalCommand,
) -> None:
    with pytest.raises(LifecycleTransitionProposalInvalidError) as raised:
        create_lifecycle_transition_proposal(command=command)

    assert str(raised.value) == "lifecycle transition proposal is invalid"
    assert "private-evidence" not in str(raised.value)


def test_record_outcome_and_resulting_snapshot_failures_are_sanitized() -> None:
    cases = (
        replace(_review(), resulting_snapshot=None),
        _review(
            resulting_snapshot=_snapshot(
                "paper_review", strategy_id="private-strategy", snapshot_id="result-1"
            )
        ),
        _review(resulting_snapshot=_snapshot("watchlist", snapshot_id="result-1")),
        _review(
            "rejected",
            resulting_snapshot=_snapshot("paper_review", snapshot_id="result-1"),
        ),
        _review(
            "deferred",
            resulting_snapshot=_snapshot("paper_review", snapshot_id="result-1"),
        ),
    )

    for command in cases:
        with pytest.raises(LifecycleTransitionRecordInvalidError) as raised:
            record_lifecycle_transition_review(command=command)
        assert str(raised.value) == "lifecycle transition record is invalid"
        assert "private-strategy" not in str(raised.value)


def test_exact_outer_and_nested_command_types_are_checked_before_access() -> None:
    with pytest.raises(
        LifecycleTransitionProposalInvalidError,
        match="^lifecycle transition proposal is invalid$",
    ):
        create_lifecycle_transition_proposal(command=object())  # type: ignore[arg-type]
    invalid_proposals = (
        replace(_proposal(), source_snapshot=object()),  # type: ignore[arg-type]
        replace(_proposal(), evidence_references=(object(),)),  # type: ignore[arg-type]
        replace(_proposal(), evidence_references=object()),  # type: ignore[arg-type]
        replace(
            _proposal(),
            source_snapshot=replace(_snapshot(), notes="bare"),  # type: ignore[arg-type]
        ),
        replace(_proposal(), notes="bare"),  # type: ignore[arg-type]
    )
    for command in invalid_proposals:
        with pytest.raises(LifecycleTransitionProposalInvalidError):
            create_lifecycle_transition_proposal(command=command)

    with pytest.raises(
        LifecycleTransitionRecordInvalidError,
        match="^lifecycle transition record is invalid$",
    ):
        record_lifecycle_transition_review(command=object())  # type: ignore[arg-type]
    invalid_reviews = (
        replace(_review(), proposal=object()),  # type: ignore[arg-type]
        replace(
            _review(),
            proposal=replace(_proposal(), source_snapshot=object()),  # type: ignore[arg-type]
        ),
        replace(
            _review(),
            proposal=replace(_proposal(), evidence_references=(object(),)),  # type: ignore[arg-type]
        ),
        replace(_review(), resulting_snapshot=object()),  # type: ignore[arg-type]
        replace(_review(), notes="bare"),  # type: ignore[arg-type]
    )
    for command in invalid_reviews:
        with pytest.raises(LifecycleTransitionRecordInvalidError) as raised:
            record_lifecycle_transition_review(command=command)
        assert "object at" not in str(raised.value)
        assert "AttributeError" not in str(raised.value)


def test_source_proposal_and_resulting_snapshot_commands_remain_unchanged() -> None:
    proposal = _proposal()
    resulting_snapshot = _snapshot("paper_review", snapshot_id="result-1")
    review = _review(proposal=proposal, resulting_snapshot=resulting_snapshot)
    before = (proposal, proposal.source_snapshot, resulting_snapshot)

    create_lifecycle_transition_proposal(command=proposal)
    record_lifecycle_transition_review(command=review)

    assert before == (proposal, proposal.source_snapshot, resulting_snapshot)


def test_commands_have_no_io_network_or_persistence_side_effects(
    tmp_path: Path, monkeypatch
) -> None:
    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("forbidden side effect")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(Path, "write_bytes", forbidden)
    monkeypatch.setattr(Path, "mkdir", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)

    proposal = create_lifecycle_transition_proposal(command=_proposal())
    review = record_lifecycle_transition_review(command=_review())

    assert proposal.proposal.proposal_id == "proposal-1"
    assert review.transition_record.transition_record_id == "record-1"
    assert list(tmp_path.iterdir()) == []
    for result in (proposal, review):
        for forbidden_name in (
            "applied",
            "executed",
            "current",
            "path",
            "job_id",
            "status",
            "repository",
            "broker",
        ):
            assert not hasattr(result, forbidden_name)
