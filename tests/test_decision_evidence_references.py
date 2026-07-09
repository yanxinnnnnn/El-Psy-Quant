"""Tests for decision evidence references."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.decision_governance import (
    DECISION_EVIDENCE_REFERENCE_SCHEMA_VERSION,
    SUPPORTED_DECISION_EVIDENCE_REFERENCE_TYPES,
    DecisionEvidenceReference,
    create_decision_evidence_reference,
)


def test_valid_decision_evidence_reference_creation() -> None:
    reference = create_decision_evidence_reference(
        reference_type="promotion_record",
        reference_id="promotion-record-1",
        label="Promotion Record 1",
        description="Human-controlled promotion record.",
    )

    assert isinstance(reference, DecisionEvidenceReference)
    assert reference.reference_type == "promotion_record"
    assert reference.reference_id == "promotion-record-1"
    assert reference.label == "Promotion Record 1"
    assert reference.description == "Human-controlled promotion record."


def test_supported_reference_types_are_explicit_and_deterministic() -> None:
    assert SUPPORTED_DECISION_EVIDENCE_REFERENCE_TYPES == (
        "promotion_record",
        "promotion_candidate_reference",
        "promotion_manifest",
        "paper_comparison_summary",
        "paper_review_decision",
        "paper_review_manifest",
    )


def test_reference_required_fields_trim_whitespace() -> None:
    reference = create_decision_evidence_reference(
        reference_type=" promotion_record ",
        reference_id=" promotion-record-1 ",
    )

    assert reference.reference_type == "promotion_record"
    assert reference.reference_id == "promotion-record-1"


def test_optional_label_and_description_normalize() -> None:
    reference = create_decision_evidence_reference(
        reference_type="promotion_record",
        reference_id="promotion-record-1",
        label="  ",
        description=" description ",
    )

    assert reference.label is None
    assert reference.description == "description"


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("reference_type", {"reference_type": ""}),
        ("reference_type", {"reference_type": "   "}),
        ("reference_id", {"reference_id": ""}),
        ("reference_id", {"reference_id": "   "}),
    ],
)
def test_empty_required_fields_raise_value_error(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "reference_type": "promotion_record",
        "reference_id": "promotion-record-1",
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_decision_evidence_reference(**arguments)  # type: ignore[arg-type]


def test_unsupported_reference_type_raises_value_error() -> None:
    with pytest.raises(ValueError, match="promotion_record"):
        create_decision_evidence_reference(
            reference_type="research_backtest",
            reference_id="backtest-1",
        )


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("reference_type", {"reference_type": object()}),
        ("reference_id", {"reference_id": object()}),
        ("label", {"label": object()}),
        ("description", {"description": object()}),
    ],
)
def test_invalid_field_types_raise_value_error(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "reference_type": "promotion_record",
        "reference_id": "promotion-record-1",
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_decision_evidence_reference(**arguments)  # type: ignore[arg-type]


def test_to_dict_is_deterministic_and_json_compatible() -> None:
    reference = create_decision_evidence_reference(
        reference_type="paper_review_manifest",
        reference_id="review-manifest-1",
        label="Review Manifest",
        description="Local paper review manifest.",
    )

    expected = {
        "schema_version": DECISION_EVIDENCE_REFERENCE_SCHEMA_VERSION,
        "reference_type": "paper_review_manifest",
        "reference_id": "review-manifest-1",
        "label": "Review Manifest",
        "description": "Local paper review manifest.",
    }

    assert reference.to_dict() == expected
    assert reference.to_dict() == expected
    json.dumps(reference.to_dict(), allow_nan=False)


def test_schema_version_is_json_compatible() -> None:
    assert DECISION_EVIDENCE_REFERENCE_SCHEMA_VERSION == 1
    json.dumps(
        {"schema_version": DECISION_EVIDENCE_REFERENCE_SCHEMA_VERSION},
        allow_nan=False,
    )


def test_decision_evidence_reference_is_immutable() -> None:
    reference = create_decision_evidence_reference(
        reference_type="promotion_record",
        reference_id="promotion-record-1",
    )

    with pytest.raises(FrozenInstanceError):
        reference.reference_id = "other"  # type: ignore[misc]


def test_decision_governance_package_exports_public_api() -> None:
    from el_psy_quant import decision_governance

    assert (
        decision_governance.DECISION_EVIDENCE_REFERENCE_SCHEMA_VERSION
        == DECISION_EVIDENCE_REFERENCE_SCHEMA_VERSION
    )
    assert (
        decision_governance.SUPPORTED_DECISION_EVIDENCE_REFERENCE_TYPES
        == SUPPORTED_DECISION_EVIDENCE_REFERENCE_TYPES
    )
    assert decision_governance.DecisionEvidenceReference is DecisionEvidenceReference
    assert (
        decision_governance.create_decision_evidence_reference
        is create_decision_evidence_reference
    )


def test_decision_governance_package_does_not_expose_forbidden_behavior() -> None:
    from el_psy_quant import decision_governance

    forbidden_names = {
        "create_decision_manifest",
        "load_decision_evidence",
        "score_decision_evidence",
        "rank_decision_evidence",
        "discover_decision_evidence",
        "run_decision_workflow",
        "write_decision_evidence_reference",
        "read_decision_evidence_reference",
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
