"""Tests for strategy decision records."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.decision_governance import (
    STRATEGY_DECISION_RECORD_SCHEMA_VERSION,
    SUPPORTED_STRATEGY_DECISION_RECORD_STATUSES,
    DecisionEvidenceReference,
    StrategyDecisionInput,
    StrategyDecisionRecord,
    StrategyDecisionSummary,
    create_decision_evidence_reference,
    create_strategy_decision_input,
    create_strategy_decision_record,
    create_strategy_decision_summary,
)


def _evidence_reference() -> DecisionEvidenceReference:
    return create_decision_evidence_reference(
        reference_type="promotion_record",
        reference_id="promotion-record-1",
        label="Evidence",
    )


def _decision_input() -> StrategyDecisionInput:
    return create_strategy_decision_input(
        input_id="decision-input-1",
        evidence_references=[_evidence_reference()],
        decision_purpose="Review whether strategy should continue paper review.",
        strategy_id="strategy-1",
    )


def _decision_summary() -> StrategyDecisionSummary:
    return create_strategy_decision_summary(
        summary_id="decision-summary-1",
        decision_input=_decision_input(),
        decision_facts=["Paper review evidence was manually inspected."],
    )


def test_valid_strategy_decision_record_creation() -> None:
    decision_summary = _decision_summary()

    decision_record = create_strategy_decision_record(
        decision_id="decision-record-1",
        decision_summary=decision_summary,
        decision_status="needs_more_evidence",
        rationale="The reviewer needs another paper review cycle.",
    )

    assert isinstance(decision_record, StrategyDecisionRecord)
    assert decision_record.decision_id == "decision-record-1"
    assert decision_record.decision_summary is decision_summary
    assert decision_record.decision_status == "needs_more_evidence"
    assert decision_record.rationale == (
        "The reviewer needs another paper review cycle."
    )
    assert decision_record.reviewed_by is None
    assert decision_record.reviewed_timestamp is None
    assert decision_record.notes == ()
    assert decision_record.warnings == ()


def test_supported_strategy_decision_record_statuses_are_deterministic() -> None:
    assert SUPPORTED_STRATEGY_DECISION_RECORD_STATUSES == (
        "needs_more_evidence",
        "approved_for_continued_paper_review",
        "rejected_for_now",
        "put_on_hold",
    )
    json.dumps(
        {"statuses": SUPPORTED_STRATEGY_DECISION_RECORD_STATUSES},
        allow_nan=False,
    )


def test_strategy_decision_record_normalizes_fields() -> None:
    decision_record = create_strategy_decision_record(
        decision_id=" decision-record-1 ",
        decision_summary=_decision_summary(),
        decision_status=" needs_more_evidence ",
        rationale=" needs another review cycle ",
        reviewed_by=" reviewer-1 ",
        notes=[" first note ", " second note "],
        warnings=[" no live readiness claim "],
    )

    assert decision_record.decision_id == "decision-record-1"
    assert decision_record.decision_status == "needs_more_evidence"
    assert decision_record.rationale == "needs another review cycle"
    assert decision_record.reviewed_by == "reviewer-1"
    assert decision_record.notes == ("first note", "second note")
    assert decision_record.warnings == ("no live readiness claim",)


def test_optional_reviewed_by_blank_normalizes_to_none() -> None:
    decision_record = create_strategy_decision_record(
        decision_id="decision-record-1",
        decision_summary=_decision_summary(),
        decision_status="needs_more_evidence",
        rationale="Needs more evidence.",
        reviewed_by="   ",
    )

    assert decision_record.reviewed_by is None


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("decision_id", {"decision_id": ""}),
        ("decision_id", {"decision_id": "   "}),
        ("rationale", {"rationale": ""}),
        ("rationale", {"rationale": "   "}),
    ],
)
def test_empty_required_strings_raise_value_error(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "decision_id": "decision-record-1",
        "decision_summary": _decision_summary(),
        "decision_status": "needs_more_evidence",
        "rationale": "Needs more evidence.",
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_strategy_decision_record(**arguments)  # type: ignore[arg-type]


def test_decision_summary_must_be_strategy_decision_summary() -> None:
    with pytest.raises(ValueError, match="decision_summary"):
        create_strategy_decision_record(
            decision_id="decision-record-1",
            decision_summary=object(),  # type: ignore[arg-type]
            decision_status="needs_more_evidence",
            rationale="Needs more evidence.",
        )


def test_unsupported_decision_status_raises_value_error() -> None:
    with pytest.raises(ValueError, match="unsupported decision_status"):
        create_strategy_decision_record(
            decision_id="decision-record-1",
            decision_summary=_decision_summary(),
            decision_status="approved",
            rationale="Needs more evidence.",
        )


def test_unsupported_decision_status_error_includes_supported_status() -> None:
    with pytest.raises(
        ValueError,
        match="approved_for_continued_paper_review",
    ):
        create_strategy_decision_record(
            decision_id="decision-record-1",
            decision_summary=_decision_summary(),
            decision_status="approved",
            rationale="Needs more evidence.",
        )


def test_invalid_reviewed_by_type_raises_value_error() -> None:
    with pytest.raises(ValueError, match="reviewed_by"):
        create_strategy_decision_record(
            decision_id="decision-record-1",
            decision_summary=_decision_summary(),
            decision_status="needs_more_evidence",
            rationale="Needs more evidence.",
            reviewed_by=object(),  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("field_name", ["notes", "warnings"])
def test_sequence_fields_reject_string_input(field_name: str) -> None:
    arguments: dict[str, object] = {
        "decision_id": "decision-record-1",
        "decision_summary": _decision_summary(),
        "decision_status": "needs_more_evidence",
        "rationale": "Needs more evidence.",
    }
    arguments[field_name] = "not-a-sequence"

    with pytest.raises(ValueError, match=field_name):
        create_strategy_decision_record(**arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize("field_name", ["notes", "warnings"])
def test_sequence_fields_reject_blank_items(field_name: str) -> None:
    arguments: dict[str, object] = {
        "decision_id": "decision-record-1",
        "decision_summary": _decision_summary(),
        "decision_status": "needs_more_evidence",
        "rationale": "Needs more evidence.",
    }
    arguments[field_name] = ["   "]

    with pytest.raises(ValueError, match=field_name):
        create_strategy_decision_record(**arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize("field_name", ["notes", "warnings"])
def test_sequence_fields_reject_non_string_items(field_name: str) -> None:
    arguments: dict[str, object] = {
        "decision_id": "decision-record-1",
        "decision_summary": _decision_summary(),
        "decision_status": "needs_more_evidence",
        "rationale": "Needs more evidence.",
    }
    arguments[field_name] = [object()]

    with pytest.raises(ValueError, match=field_name):
        create_strategy_decision_record(**arguments)  # type: ignore[arg-type]


def test_optional_sequence_fields_allow_empty_sequences() -> None:
    decision_record = create_strategy_decision_record(
        decision_id="decision-record-1",
        decision_summary=_decision_summary(),
        decision_status="needs_more_evidence",
        rationale="Needs more evidence.",
        notes=[],
        warnings=[],
    )

    assert decision_record.notes == ()
    assert decision_record.warnings == ()


def test_sequence_inputs_are_copied_to_immutable_tuples() -> None:
    notes = ["note"]
    warnings = ["warning"]

    decision_record = create_strategy_decision_record(
        decision_id="decision-record-1",
        decision_summary=_decision_summary(),
        decision_status="needs_more_evidence",
        rationale="Needs more evidence.",
        notes=notes,
        warnings=warnings,
    )
    notes.append("new note")
    warnings.append("new warning")

    assert decision_record.notes == ("note",)
    assert decision_record.warnings == ("warning",)


def test_timestamp_normalizes_to_deterministic_export() -> None:
    decision_record = create_strategy_decision_record(
        decision_id="decision-record-1",
        decision_summary=_decision_summary(),
        decision_status="needs_more_evidence",
        rationale="Needs more evidence.",
        reviewed_timestamp="2026-01-02T03:04:05",
    )

    assert (
        decision_record.to_dict()["reviewed_timestamp"]
        == "2026-01-02T03:04:05"
    )


def test_invalid_timestamp_raises_value_error() -> None:
    with pytest.raises(ValueError, match="reviewed_timestamp"):
        create_strategy_decision_record(
            decision_id="decision-record-1",
            decision_summary=_decision_summary(),
            decision_status="needs_more_evidence",
            rationale="Needs more evidence.",
            reviewed_timestamp="not-a-timestamp",
        )


def test_to_dict_is_deterministic_and_json_compatible() -> None:
    decision_summary = _decision_summary()
    decision_record = create_strategy_decision_record(
        decision_id="decision-record-1",
        decision_summary=decision_summary,
        decision_status="approved_for_continued_paper_review",
        rationale="Continue paper review under explicit human oversight.",
        reviewed_by="reviewer-1",
        reviewed_timestamp="2026-01-02T03:04:05",
        notes=["note 1", "note 2"],
        warnings=["warning"],
    )

    expected = {
        "schema_version": STRATEGY_DECISION_RECORD_SCHEMA_VERSION,
        "decision_id": "decision-record-1",
        "decision_summary": decision_summary.to_dict(),
        "decision_status": "approved_for_continued_paper_review",
        "rationale": "Continue paper review under explicit human oversight.",
        "reviewed_by": "reviewer-1",
        "reviewed_timestamp": "2026-01-02T03:04:05",
        "notes": ["note 1", "note 2"],
        "warnings": ["warning"],
    }

    assert decision_record.to_dict() == expected
    assert decision_record.to_dict() == expected
    json.dumps(decision_record.to_dict(), allow_nan=False)


def test_schema_version_is_json_compatible() -> None:
    assert STRATEGY_DECISION_RECORD_SCHEMA_VERSION == 1
    json.dumps(
        {"schema_version": STRATEGY_DECISION_RECORD_SCHEMA_VERSION},
        allow_nan=False,
    )


def test_strategy_decision_record_is_immutable() -> None:
    decision_record = create_strategy_decision_record(
        decision_id="decision-record-1",
        decision_summary=_decision_summary(),
        decision_status="needs_more_evidence",
        rationale="Needs more evidence.",
    )

    with pytest.raises(FrozenInstanceError):
        decision_record.decision_id = "other"  # type: ignore[misc]


def test_decision_governance_package_exports_record_public_api() -> None:
    from el_psy_quant import decision_governance

    assert (
        decision_governance.STRATEGY_DECISION_RECORD_SCHEMA_VERSION
        == STRATEGY_DECISION_RECORD_SCHEMA_VERSION
    )
    assert (
        decision_governance.SUPPORTED_STRATEGY_DECISION_RECORD_STATUSES
        == SUPPORTED_STRATEGY_DECISION_RECORD_STATUSES
    )
    assert decision_governance.StrategyDecisionRecord is StrategyDecisionRecord
    assert (
        decision_governance.create_strategy_decision_record
        is create_strategy_decision_record
    )


def test_decision_governance_package_does_not_expose_forbidden_behavior() -> None:
    from el_psy_quant import decision_governance

    forbidden_names = {
        "create_decision_manifest",
        "recommend_strategy_decision",
        "approve_strategy",
        "reject_strategy",
        "automatically_promote_strategy",
        "score_decision_evidence",
        "rank_decision_evidence",
        "discover_decision_evidence",
        "load_decision_evidence",
        "evaluate_rationale",
        "run_decision_workflow",
        "write_strategy_decision_record",
        "read_strategy_decision_record",
        "create_dashboard",
        "render_decision_report",
        "approve_live_trading",
        "allocate_capital",
        "route_orders",
        "mark_live_ready",
        "mark_real_money_ready",
    }

    for forbidden_name in forbidden_names:
        assert not hasattr(decision_governance, forbidden_name)
