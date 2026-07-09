"""Tests for strategy decision inputs."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.decision_governance import (
    STRATEGY_DECISION_INPUT_SCHEMA_VERSION,
    DecisionEvidenceReference,
    StrategyDecisionInput,
    create_decision_evidence_reference,
    create_strategy_decision_input,
)


def _evidence_reference(
    reference_type: str = "promotion_record",
    reference_id: str = "promotion-record-1",
) -> DecisionEvidenceReference:
    return create_decision_evidence_reference(
        reference_type=reference_type,
        reference_id=reference_id,
        label="Evidence",
    )


def test_valid_strategy_decision_input_creation() -> None:
    evidence_reference = _evidence_reference()

    decision_input = create_strategy_decision_input(
        input_id="decision-input-1",
        evidence_references=[evidence_reference],
        decision_purpose="Review whether strategy should continue paper review.",
    )

    assert isinstance(decision_input, StrategyDecisionInput)
    assert decision_input.input_id == "decision-input-1"
    assert decision_input.evidence_references == (evidence_reference,)
    assert (
        decision_input.decision_purpose
        == "Review whether strategy should continue paper review."
    )
    assert decision_input.strategy_id is None
    assert decision_input.review_context is None
    assert decision_input.created_by is None
    assert decision_input.created_timestamp is None


def test_required_strings_trim_whitespace() -> None:
    decision_input = create_strategy_decision_input(
        input_id=" decision-input-1 ",
        evidence_references=[_evidence_reference()],
        decision_purpose=" continue paper review ",
    )

    assert decision_input.input_id == "decision-input-1"
    assert decision_input.decision_purpose == "continue paper review"


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("input_id", {"input_id": ""}),
        ("input_id", {"input_id": "   "}),
        ("decision_purpose", {"decision_purpose": ""}),
        ("decision_purpose", {"decision_purpose": "   "}),
    ],
)
def test_empty_required_strings_raise_value_error(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "input_id": "decision-input-1",
        "evidence_references": [_evidence_reference()],
        "decision_purpose": "continue paper review",
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_strategy_decision_input(**arguments)  # type: ignore[arg-type]


def test_optional_strings_normalize() -> None:
    decision_input = create_strategy_decision_input(
        input_id="decision-input-1",
        evidence_references=[_evidence_reference()],
        decision_purpose="continue paper review",
        strategy_id=" strategy-1 ",
        review_context="  ",
        created_by=" reviewer-1 ",
    )

    assert decision_input.strategy_id == "strategy-1"
    assert decision_input.review_context is None
    assert decision_input.created_by == "reviewer-1"


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("strategy_id", {"strategy_id": object()}),
        ("review_context", {"review_context": object()}),
        ("created_by", {"created_by": object()}),
    ],
)
def test_invalid_optional_field_types_raise_value_error(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "input_id": "decision-input-1",
        "evidence_references": [_evidence_reference()],
        "decision_purpose": "continue paper review",
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_strategy_decision_input(**arguments)  # type: ignore[arg-type]


def test_evidence_references_must_not_be_empty() -> None:
    with pytest.raises(ValueError, match="evidence_references"):
        create_strategy_decision_input(
            input_id="decision-input-1",
            evidence_references=[],
            decision_purpose="continue paper review",
        )


def test_evidence_references_reject_single_reference_instead_of_sequence() -> None:
    with pytest.raises(ValueError, match="evidence_references"):
        create_strategy_decision_input(
            input_id="decision-input-1",
            evidence_references=_evidence_reference(),  # type: ignore[arg-type]
            decision_purpose="continue paper review",
        )


def test_evidence_references_reject_string_input() -> None:
    with pytest.raises(ValueError, match="evidence_references"):
        create_strategy_decision_input(
            input_id="decision-input-1",
            evidence_references="promotion-record-1",  # type: ignore[arg-type]
            decision_purpose="continue paper review",
        )


def test_evidence_references_reject_invalid_items() -> None:
    with pytest.raises(ValueError, match="DecisionEvidenceReference"):
        create_strategy_decision_input(
            input_id="decision-input-1",
            evidence_references=[object()],  # type: ignore[list-item]
            decision_purpose="continue paper review",
        )


def test_evidence_references_normalize_to_immutable_tuple() -> None:
    evidence_references = [_evidence_reference()]

    decision_input = create_strategy_decision_input(
        input_id="decision-input-1",
        evidence_references=evidence_references,
        decision_purpose="continue paper review",
    )
    evidence_references.append(
        _evidence_reference(
            reference_type="paper_review_decision",
            reference_id="decision-1",
        )
    )

    assert len(decision_input.evidence_references) == 1


def test_timestamp_normalizes_to_deterministic_export() -> None:
    decision_input = create_strategy_decision_input(
        input_id="decision-input-1",
        evidence_references=[_evidence_reference()],
        decision_purpose="continue paper review",
        created_timestamp="2026-01-02T03:04:05",
    )

    assert decision_input.to_dict()["created_timestamp"] == "2026-01-02T03:04:05"


def test_invalid_timestamp_raises_value_error() -> None:
    with pytest.raises(ValueError, match="created_timestamp"):
        create_strategy_decision_input(
            input_id="decision-input-1",
            evidence_references=[_evidence_reference()],
            decision_purpose="continue paper review",
            created_timestamp="not-a-timestamp",
        )


def test_to_dict_is_deterministic_and_json_compatible() -> None:
    evidence_reference = _evidence_reference()
    decision_input = create_strategy_decision_input(
        input_id="decision-input-1",
        evidence_references=[evidence_reference],
        decision_purpose="continue paper review",
        strategy_id="strategy-1",
        review_context="Manual strategy-level review.",
        created_by="reviewer-1",
        created_timestamp="2026-01-02T03:04:05",
    )

    expected = {
        "schema_version": STRATEGY_DECISION_INPUT_SCHEMA_VERSION,
        "input_id": "decision-input-1",
        "evidence_references": [evidence_reference.to_dict()],
        "decision_purpose": "continue paper review",
        "strategy_id": "strategy-1",
        "review_context": "Manual strategy-level review.",
        "created_by": "reviewer-1",
        "created_timestamp": "2026-01-02T03:04:05",
    }

    assert decision_input.to_dict() == expected
    assert decision_input.to_dict() == expected
    json.dumps(decision_input.to_dict(), allow_nan=False)


def test_schema_version_is_json_compatible() -> None:
    assert STRATEGY_DECISION_INPUT_SCHEMA_VERSION == 1
    json.dumps(
        {"schema_version": STRATEGY_DECISION_INPUT_SCHEMA_VERSION},
        allow_nan=False,
    )


def test_strategy_decision_input_is_immutable() -> None:
    decision_input = create_strategy_decision_input(
        input_id="decision-input-1",
        evidence_references=[_evidence_reference()],
        decision_purpose="continue paper review",
    )

    with pytest.raises(FrozenInstanceError):
        decision_input.input_id = "other"  # type: ignore[misc]


def test_decision_governance_package_exports_input_public_api() -> None:
    from el_psy_quant import decision_governance

    assert (
        decision_governance.STRATEGY_DECISION_INPUT_SCHEMA_VERSION
        == STRATEGY_DECISION_INPUT_SCHEMA_VERSION
    )
    assert decision_governance.StrategyDecisionInput is StrategyDecisionInput
    assert (
        decision_governance.create_strategy_decision_input
        is create_strategy_decision_input
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
        "write_strategy_decision_input",
        "read_strategy_decision_input",
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
