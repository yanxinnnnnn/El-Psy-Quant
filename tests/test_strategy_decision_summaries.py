"""Tests for strategy decision summaries."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.decision_governance import (
    STRATEGY_DECISION_SUMMARY_SCHEMA_VERSION,
    DecisionEvidenceReference,
    StrategyDecisionInput,
    StrategyDecisionSummary,
    create_decision_evidence_reference,
    create_strategy_decision_input,
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


def test_valid_strategy_decision_summary_creation() -> None:
    decision_input = _decision_input()

    summary = create_strategy_decision_summary(
        summary_id="decision-summary-1",
        decision_input=decision_input,
        decision_facts=["Paper review decision remained human-controlled."],
    )

    assert isinstance(summary, StrategyDecisionSummary)
    assert summary.summary_id == "decision-summary-1"
    assert summary.decision_input is decision_input
    assert summary.decision_facts == (
        "Paper review decision remained human-controlled.",
    )
    assert summary.assumptions == ()
    assert summary.warnings == ()
    assert summary.missing_evidence == ()
    assert summary.created_by is None
    assert summary.created_timestamp is None


def test_strategy_decision_summary_normalizes_fields() -> None:
    summary = create_strategy_decision_summary(
        summary_id=" decision-summary-1 ",
        decision_input=_decision_input(),
        decision_facts=[" first fact ", " second fact "],
        assumptions=[" explicit human review "],
        warnings=[" no broker readiness claim "],
        missing_evidence=[" no live data evidence "],
        created_by=" reviewer-1 ",
    )

    assert summary.summary_id == "decision-summary-1"
    assert summary.decision_facts == ("first fact", "second fact")
    assert summary.assumptions == ("explicit human review",)
    assert summary.warnings == ("no broker readiness claim",)
    assert summary.missing_evidence == ("no live data evidence",)
    assert summary.created_by == "reviewer-1"


def test_optional_created_by_blank_normalizes_to_none() -> None:
    summary = create_strategy_decision_summary(
        summary_id="decision-summary-1",
        decision_input=_decision_input(),
        decision_facts=["fact"],
        created_by="   ",
    )

    assert summary.created_by is None


def test_empty_summary_id_raises_value_error() -> None:
    with pytest.raises(ValueError, match="summary_id"):
        create_strategy_decision_summary(
            summary_id="   ",
            decision_input=_decision_input(),
            decision_facts=["fact"],
        )


def test_decision_input_must_be_strategy_decision_input() -> None:
    with pytest.raises(ValueError, match="decision_input"):
        create_strategy_decision_summary(
            summary_id="decision-summary-1",
            decision_input=object(),  # type: ignore[arg-type]
            decision_facts=["fact"],
        )


def test_decision_facts_must_not_be_empty() -> None:
    with pytest.raises(ValueError, match="decision_facts"):
        create_strategy_decision_summary(
            summary_id="decision-summary-1",
            decision_input=_decision_input(),
            decision_facts=[],
        )


@pytest.mark.parametrize(
    "field_name",
    ["decision_facts", "assumptions", "warnings", "missing_evidence"],
)
def test_sequence_fields_reject_string_input(field_name: str) -> None:
    arguments: dict[str, object] = {
        "summary_id": "decision-summary-1",
        "decision_input": _decision_input(),
        "decision_facts": ["fact"],
    }
    arguments[field_name] = "not-a-sequence"

    with pytest.raises(ValueError, match=field_name):
        create_strategy_decision_summary(**arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field_name",
    ["decision_facts", "assumptions", "warnings", "missing_evidence"],
)
def test_sequence_fields_reject_blank_items(field_name: str) -> None:
    arguments: dict[str, object] = {
        "summary_id": "decision-summary-1",
        "decision_input": _decision_input(),
        "decision_facts": ["fact"],
    }
    arguments[field_name] = ["   "]

    with pytest.raises(ValueError, match=field_name):
        create_strategy_decision_summary(**arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field_name",
    ["decision_facts", "assumptions", "warnings", "missing_evidence"],
)
def test_sequence_fields_reject_non_string_items(field_name: str) -> None:
    arguments: dict[str, object] = {
        "summary_id": "decision-summary-1",
        "decision_input": _decision_input(),
        "decision_facts": ["fact"],
    }
    arguments[field_name] = [object()]

    with pytest.raises(ValueError, match=field_name):
        create_strategy_decision_summary(**arguments)  # type: ignore[arg-type]


def test_optional_sequence_fields_allow_empty_sequences() -> None:
    summary = create_strategy_decision_summary(
        summary_id="decision-summary-1",
        decision_input=_decision_input(),
        decision_facts=["fact"],
        assumptions=[],
        warnings=[],
        missing_evidence=[],
    )

    assert summary.assumptions == ()
    assert summary.warnings == ()
    assert summary.missing_evidence == ()


def test_sequence_inputs_are_copied_to_immutable_tuples() -> None:
    decision_facts = ["fact"]
    assumptions = ["assumption"]
    warnings = ["warning"]
    missing_evidence = ["missing evidence"]

    summary = create_strategy_decision_summary(
        summary_id="decision-summary-1",
        decision_input=_decision_input(),
        decision_facts=decision_facts,
        assumptions=assumptions,
        warnings=warnings,
        missing_evidence=missing_evidence,
    )
    decision_facts.append("new fact")
    assumptions.append("new assumption")
    warnings.append("new warning")
    missing_evidence.append("new missing evidence")

    assert summary.decision_facts == ("fact",)
    assert summary.assumptions == ("assumption",)
    assert summary.warnings == ("warning",)
    assert summary.missing_evidence == ("missing evidence",)


def test_invalid_created_by_type_raises_value_error() -> None:
    with pytest.raises(ValueError, match="created_by"):
        create_strategy_decision_summary(
            summary_id="decision-summary-1",
            decision_input=_decision_input(),
            decision_facts=["fact"],
            created_by=object(),  # type: ignore[arg-type]
        )


def test_timestamp_normalizes_to_deterministic_export() -> None:
    summary = create_strategy_decision_summary(
        summary_id="decision-summary-1",
        decision_input=_decision_input(),
        decision_facts=["fact"],
        created_timestamp="2026-01-02T03:04:05",
    )

    assert summary.to_dict()["created_timestamp"] == "2026-01-02T03:04:05"


def test_invalid_timestamp_raises_value_error() -> None:
    with pytest.raises(ValueError, match="created_timestamp"):
        create_strategy_decision_summary(
            summary_id="decision-summary-1",
            decision_input=_decision_input(),
            decision_facts=["fact"],
            created_timestamp="not-a-timestamp",
        )


def test_to_dict_is_deterministic_and_json_compatible() -> None:
    decision_input = _decision_input()
    summary = create_strategy_decision_summary(
        summary_id="decision-summary-1",
        decision_input=decision_input,
        decision_facts=["fact 1", "fact 2"],
        assumptions=["assumption"],
        warnings=["warning"],
        missing_evidence=["missing evidence"],
        created_by="reviewer-1",
        created_timestamp="2026-01-02T03:04:05",
    )

    expected = {
        "schema_version": STRATEGY_DECISION_SUMMARY_SCHEMA_VERSION,
        "summary_id": "decision-summary-1",
        "decision_input": decision_input.to_dict(),
        "decision_facts": ["fact 1", "fact 2"],
        "assumptions": ["assumption"],
        "warnings": ["warning"],
        "missing_evidence": ["missing evidence"],
        "created_by": "reviewer-1",
        "created_timestamp": "2026-01-02T03:04:05",
    }

    assert summary.to_dict() == expected
    assert summary.to_dict() == expected
    json.dumps(summary.to_dict(), allow_nan=False)


def test_schema_version_is_json_compatible() -> None:
    assert STRATEGY_DECISION_SUMMARY_SCHEMA_VERSION == 1
    json.dumps(
        {"schema_version": STRATEGY_DECISION_SUMMARY_SCHEMA_VERSION},
        allow_nan=False,
    )


def test_strategy_decision_summary_is_immutable() -> None:
    summary = create_strategy_decision_summary(
        summary_id="decision-summary-1",
        decision_input=_decision_input(),
        decision_facts=["fact"],
    )

    with pytest.raises(FrozenInstanceError):
        summary.summary_id = "other"  # type: ignore[misc]


def test_decision_governance_package_exports_summary_public_api() -> None:
    from el_psy_quant import decision_governance

    assert (
        decision_governance.STRATEGY_DECISION_SUMMARY_SCHEMA_VERSION
        == STRATEGY_DECISION_SUMMARY_SCHEMA_VERSION
    )
    assert decision_governance.StrategyDecisionSummary is StrategyDecisionSummary
    assert (
        decision_governance.create_strategy_decision_summary
        is create_strategy_decision_summary
    )


def test_decision_governance_package_does_not_expose_forbidden_behavior() -> None:
    from el_psy_quant import decision_governance

    forbidden_names = {
        "create_strategy_decision_record",
        "create_decision_manifest",
        "recommend_strategy_decision",
        "approve_strategy",
        "reject_strategy",
        "score_decision_evidence",
        "rank_decision_evidence",
        "discover_decision_evidence",
        "load_decision_evidence",
        "run_decision_workflow",
        "write_strategy_decision_summary",
        "read_strategy_decision_summary",
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
