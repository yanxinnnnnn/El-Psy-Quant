"""Tests for paper run review decision records."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.paper_review import (
    PAPER_RUN_REVIEW_DECISION_SCHEMA_VERSION,
    SUPPORTED_PAPER_RUN_REVIEW_DECISION_STATUSES,
    PaperRunComparisonSummary,
    PaperRunReviewDecision,
    create_paper_run_comparison_input,
    create_paper_run_comparison_summary,
    create_paper_run_reference,
    create_paper_run_review_decision,
)


def _comparison_summary() -> PaperRunComparisonSummary:
    first = create_paper_run_reference(
        reference_type="paper_result_summary",
        reference="outputs/run-1/paper/paper_run_result_summary.json",
        run_id="run-1",
        artifact_id="paper_result_summary",
        label="Run 1 summary",
    )
    second = create_paper_run_reference(
        reference_type="paper_artifact",
        reference="outputs/run-2/paper/paper_run_artifact.json",
        run_id="run-2",
        artifact_id="paper_artifact",
        label="Run 2 artifact",
    )
    comparison_input = create_paper_run_comparison_input(
        comparison_id="comparison-1",
        paper_run_references=[first, second],
        purpose="Compare paper runs for manual review.",
    )
    return create_paper_run_comparison_summary(
        summary_id="summary-1",
        comparison_input=comparison_input,
        comparison_facts=["Run 1 and Run 2 were supplied explicitly."],
    )


def test_valid_review_decision_creation() -> None:
    comparison_summary = _comparison_summary()

    decision = create_paper_run_review_decision(
        decision_id="decision-1",
        comparison_summary=comparison_summary,
        decision_status="needs_more_evidence",
        rationale="Need more paper review before any later decision.",
    )

    assert isinstance(decision, PaperRunReviewDecision)
    assert decision.decision_id == "decision-1"
    assert decision.comparison_summary is comparison_summary
    assert decision.decision_status == "needs_more_evidence"
    assert decision.rationale == "Need more paper review before any later decision."
    assert decision.reviewed_by is None
    assert decision.reviewed_timestamp is None
    assert decision.notes == ()
    assert decision.warnings == ()


def test_supported_decision_statuses_are_explicit_and_deterministic() -> None:
    assert SUPPORTED_PAPER_RUN_REVIEW_DECISION_STATUSES == (
        "needs_more_evidence",
        "approved_for_further_paper_review",
        "rejected_for_now",
        "put_on_hold",
    )


@pytest.mark.parametrize("decision_id", ["", "   "])
def test_decision_id_validation(decision_id: str) -> None:
    with pytest.raises(ValueError, match="decision_id"):
        create_paper_run_review_decision(
            decision_id=decision_id,
            comparison_summary=_comparison_summary(),
            decision_status="needs_more_evidence",
            rationale="Need more evidence.",
        )


def test_decision_id_trimming() -> None:
    decision = create_paper_run_review_decision(
        decision_id=" decision-1 ",
        comparison_summary=_comparison_summary(),
        decision_status="needs_more_evidence",
        rationale="Need more evidence.",
    )

    assert decision.decision_id == "decision-1"


def test_comparison_summary_type_validation() -> None:
    with pytest.raises(ValueError, match="PaperRunComparisonSummary"):
        create_paper_run_review_decision(
            decision_id="decision-1",
            comparison_summary=object(),  # type: ignore[arg-type]
            decision_status="needs_more_evidence",
            rationale="Need more evidence.",
        )


def test_decision_status_validation_includes_supported_statuses() -> None:
    with pytest.raises(ValueError, match="needs_more_evidence"):
        create_paper_run_review_decision(
            decision_id="decision-1",
            comparison_summary=_comparison_summary(),
            decision_status="approved_for_live_trading",
            rationale="This should not be supported.",
        )


def test_decision_status_trimming() -> None:
    decision = create_paper_run_review_decision(
        decision_id="decision-1",
        comparison_summary=_comparison_summary(),
        decision_status=" needs_more_evidence ",
        rationale="Need more evidence.",
    )

    assert decision.decision_status == "needs_more_evidence"


@pytest.mark.parametrize("rationale", ["", "   "])
def test_rationale_validation(rationale: str) -> None:
    with pytest.raises(ValueError, match="rationale"):
        create_paper_run_review_decision(
            decision_id="decision-1",
            comparison_summary=_comparison_summary(),
            decision_status="needs_more_evidence",
            rationale=rationale,
        )


def test_rationale_trimming() -> None:
    decision = create_paper_run_review_decision(
        decision_id="decision-1",
        comparison_summary=_comparison_summary(),
        decision_status="needs_more_evidence",
        rationale=" Need more evidence. ",
    )

    assert decision.rationale == "Need more evidence."


def test_optional_reviewed_by_normalization() -> None:
    decision = create_paper_run_review_decision(
        decision_id="decision-1",
        comparison_summary=_comparison_summary(),
        decision_status="needs_more_evidence",
        rationale="Need more evidence.",
        reviewed_by="  ",
    )
    reviewed_decision = create_paper_run_review_decision(
        decision_id="decision-2",
        comparison_summary=_comparison_summary(),
        decision_status="put_on_hold",
        rationale="Hold until later paper review.",
        reviewed_by=" reviewer-1 ",
    )

    assert decision.reviewed_by is None
    assert reviewed_decision.reviewed_by == "reviewer-1"


def test_invalid_reviewed_by_type_raises_value_error() -> None:
    with pytest.raises(ValueError, match="reviewed_by"):
        create_paper_run_review_decision(
            decision_id="decision-1",
            comparison_summary=_comparison_summary(),
            decision_status="needs_more_evidence",
            rationale="Need more evidence.",
            reviewed_by=object(),  # type: ignore[arg-type]
        )


def test_notes_and_warnings_normalize_to_immutable_tuples() -> None:
    notes = [" note "]
    warnings = [" warning "]

    decision = create_paper_run_review_decision(
        decision_id="decision-1",
        comparison_summary=_comparison_summary(),
        decision_status="needs_more_evidence",
        rationale="Need more evidence.",
        notes=notes,
        warnings=warnings,
    )
    notes.append("new note")
    warnings.append("new warning")

    assert decision.notes == ("note",)
    assert decision.warnings == ("warning",)


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("notes", {"notes": "note"}),
        ("warnings", {"warnings": "warning"}),
    ],
)
def test_bare_strings_rejected_for_sequence_fields(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "decision_id": "decision-1",
        "comparison_summary": _comparison_summary(),
        "decision_status": "needs_more_evidence",
        "rationale": "Need more evidence.",
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_paper_run_review_decision(**arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("notes", {"notes": [""]}),
        ("notes", {"notes": ["  "]}),
        ("notes", {"notes": [object()]}),
        ("warnings", {"warnings": [""]}),
        ("warnings", {"warnings": ["  "]}),
        ("warnings", {"warnings": [object()]}),
    ],
)
def test_invalid_sequence_elements_rejected(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "decision_id": "decision-1",
        "comparison_summary": _comparison_summary(),
        "decision_status": "needs_more_evidence",
        "rationale": "Need more evidence.",
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_paper_run_review_decision(**arguments)  # type: ignore[arg-type]


def test_optional_empty_sequences_allowed() -> None:
    decision = create_paper_run_review_decision(
        decision_id="decision-1",
        comparison_summary=_comparison_summary(),
        decision_status="needs_more_evidence",
        rationale="Need more evidence.",
        notes=[],
        warnings=[],
    )

    assert decision.notes == ()
    assert decision.warnings == ()


def test_timestamp_normalizes_to_deterministic_export() -> None:
    decision = create_paper_run_review_decision(
        decision_id="decision-1",
        comparison_summary=_comparison_summary(),
        decision_status="needs_more_evidence",
        rationale="Need more evidence.",
        reviewed_timestamp="2026-01-02T03:04:05",
    )

    assert decision.to_dict()["reviewed_timestamp"] == "2026-01-02T03:04:05"


def test_invalid_timestamp_raises_value_error() -> None:
    with pytest.raises(ValueError, match="reviewed_timestamp"):
        create_paper_run_review_decision(
            decision_id="decision-1",
            comparison_summary=_comparison_summary(),
            decision_status="needs_more_evidence",
            rationale="Need more evidence.",
            reviewed_timestamp="not-a-timestamp",
        )


def test_to_dict_is_deterministic_and_json_compatible() -> None:
    comparison_summary = _comparison_summary()
    decision = create_paper_run_review_decision(
        decision_id="decision-1",
        comparison_summary=comparison_summary,
        decision_status="approved_for_further_paper_review",
        rationale="Evidence supports more paper review, not live trading.",
        reviewed_by="reviewer-1",
        reviewed_timestamp="2026-01-02T03:04:05",
        notes=["Continue local paper review only."],
        warnings=["This is not a live-readiness claim."],
    )

    expected = {
        "schema_version": PAPER_RUN_REVIEW_DECISION_SCHEMA_VERSION,
        "decision_id": "decision-1",
        "comparison_summary": comparison_summary.to_dict(),
        "decision_status": "approved_for_further_paper_review",
        "rationale": "Evidence supports more paper review, not live trading.",
        "reviewed_by": "reviewer-1",
        "reviewed_timestamp": "2026-01-02T03:04:05",
        "notes": ["Continue local paper review only."],
        "warnings": ["This is not a live-readiness claim."],
    }

    assert decision.to_dict() == expected
    assert decision.to_dict() == expected
    json.dumps(decision.to_dict(), allow_nan=False)


def test_schema_version_is_json_compatible() -> None:
    assert PAPER_RUN_REVIEW_DECISION_SCHEMA_VERSION == 1
    json.dumps(
        {"schema_version": PAPER_RUN_REVIEW_DECISION_SCHEMA_VERSION},
        allow_nan=False,
    )


def test_paper_run_review_decision_is_immutable() -> None:
    decision = create_paper_run_review_decision(
        decision_id="decision-1",
        comparison_summary=_comparison_summary(),
        decision_status="needs_more_evidence",
        rationale="Need more evidence.",
    )

    with pytest.raises(FrozenInstanceError):
        decision.decision_id = "other"  # type: ignore[misc]


def test_paper_review_package_exports_review_decision_public_api() -> None:
    from el_psy_quant import paper_review

    assert (
        paper_review.PAPER_RUN_REVIEW_DECISION_SCHEMA_VERSION
        == PAPER_RUN_REVIEW_DECISION_SCHEMA_VERSION
    )
    assert (
        paper_review.SUPPORTED_PAPER_RUN_REVIEW_DECISION_STATUSES
        == SUPPORTED_PAPER_RUN_REVIEW_DECISION_STATUSES
    )
    assert paper_review.PaperRunReviewDecision is PaperRunReviewDecision
    assert (
        paper_review.create_paper_run_review_decision
        is create_paper_run_review_decision
    )


def test_paper_review_package_does_not_expose_forbidden_runtime_behavior() -> None:
    from el_psy_quant import paper_review

    forbidden_names = {
        "approve_live_trading",
        "allocate_capital",
        "route_orders",
        "create_paper_order",
        "create_paper_fill",
        "create_broker_order",
        "mark_live_ready",
        "mark_real_money_ready",
        "automatically_promote_strategy",
        "run_paper_workflow",
        "create_dashboard",
        "render_paper_run_report",
    }

    for forbidden_name in forbidden_names:
        assert not hasattr(paper_review, forbidden_name)
