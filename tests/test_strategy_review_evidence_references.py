"""Tests for strategy review evidence references."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.strategy_review import (
    STRATEGY_REVIEW_EVIDENCE_REFERENCE_SCHEMA_VERSION,
    SUPPORTED_STRATEGY_REVIEW_EVIDENCE_REFERENCE_TYPES,
    StrategyReviewEvidenceReference,
    create_strategy_review_evidence_reference,
)


def test_supported_reference_types_are_exact_and_deterministic() -> None:
    assert SUPPORTED_STRATEGY_REVIEW_EVIDENCE_REFERENCE_TYPES == (
        "promotion_record",
        "promotion_manifest",
        "paper_comparison_summary",
        "paper_review_decision",
        "paper_review_manifest",
        "strategy_decision_summary",
        "strategy_decision_record",
        "strategy_decision_manifest",
        "report_artifact_summary",
        "report_artifact_manifest",
    )
    json.dumps(
        {"reference_types": SUPPORTED_STRATEGY_REVIEW_EVIDENCE_REFERENCE_TYPES},
        allow_nan=False,
    )


@pytest.mark.parametrize(
    "reference_type",
    SUPPORTED_STRATEGY_REVIEW_EVIDENCE_REFERENCE_TYPES,
)
def test_all_supported_reference_types_can_be_created(reference_type: str) -> None:
    reference = create_strategy_review_evidence_reference(
        reference_type=reference_type,
        reference_id=f"{reference_type}-1",
    )

    assert isinstance(reference, StrategyReviewEvidenceReference)
    assert reference.reference_type == reference_type
    assert reference.reference_id == f"{reference_type}-1"


def test_reference_normalizes_whitespace() -> None:
    reference = create_strategy_review_evidence_reference(
        reference_type=" strategy_decision_record ",
        reference_id=" decision-record-1 ",
    )

    assert reference.reference_type == "strategy_decision_record"
    assert reference.reference_id == "decision-record-1"


def test_optional_fields_normalize() -> None:
    reference = create_strategy_review_evidence_reference(
        reference_type="promotion_record",
        reference_id="promotion-record-1",
        label=" Review evidence ",
        description="  ",
    )

    assert reference.label == "Review evidence"
    assert reference.description is None


def test_unsupported_reference_type_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported reference_type"):
        create_strategy_review_evidence_reference(
            reference_type="promotion_candidate",
            reference_id="promotion-candidate-1",
        )


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("reference_type", {"reference_type": ""}),
        ("reference_type", {"reference_type": "   "}),
        ("reference_id", {"reference_id": ""}),
        ("reference_id", {"reference_id": "   "}),
    ],
)
def test_empty_required_fields_are_rejected(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "reference_type": "promotion_record",
        "reference_id": "promotion-record-1",
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_strategy_review_evidence_reference(**arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("reference_type", {"reference_type": object()}),
        ("reference_id", {"reference_id": object()}),
        ("label", {"label": object()}),
        ("description", {"description": object()}),
    ],
)
def test_invalid_field_types_are_rejected(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "reference_type": "promotion_record",
        "reference_id": "promotion-record-1",
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_strategy_review_evidence_reference(**arguments)  # type: ignore[arg-type]


def test_to_dict_is_deterministic_and_json_compatible() -> None:
    reference = create_strategy_review_evidence_reference(
        reference_type="report_artifact_manifest",
        reference_id="report-manifest-1",
        label="Review package",
        description="Caller-supplied review context.",
    )
    expected = {
        "schema_version": STRATEGY_REVIEW_EVIDENCE_REFERENCE_SCHEMA_VERSION,
        "reference_type": "report_artifact_manifest",
        "reference_id": "report-manifest-1",
        "label": "Review package",
        "description": "Caller-supplied review context.",
    }

    assert reference.to_dict() == expected
    assert reference.to_dict() == expected
    json.dumps(reference.to_dict(), allow_nan=False)


def test_schema_version_is_json_compatible() -> None:
    assert STRATEGY_REVIEW_EVIDENCE_REFERENCE_SCHEMA_VERSION == 1
    json.dumps(
        {"schema_version": STRATEGY_REVIEW_EVIDENCE_REFERENCE_SCHEMA_VERSION},
        allow_nan=False,
    )


def test_evidence_reference_is_immutable() -> None:
    reference = create_strategy_review_evidence_reference(
        reference_type="promotion_record",
        reference_id="promotion-record-1",
    )

    with pytest.raises(FrozenInstanceError):
        reference.reference_id = "other"  # type: ignore[misc]


def test_strategy_review_package_exports_public_api() -> None:
    from el_psy_quant import strategy_review

    assert (
        strategy_review.STRATEGY_REVIEW_EVIDENCE_REFERENCE_SCHEMA_VERSION
        == STRATEGY_REVIEW_EVIDENCE_REFERENCE_SCHEMA_VERSION
    )
    assert (
        strategy_review.SUPPORTED_STRATEGY_REVIEW_EVIDENCE_REFERENCE_TYPES
        == SUPPORTED_STRATEGY_REVIEW_EVIDENCE_REFERENCE_TYPES
    )
    assert strategy_review.StrategyReviewEvidenceReference is StrategyReviewEvidenceReference
    assert (
        strategy_review.create_strategy_review_evidence_reference
        is create_strategy_review_evidence_reference
    )


def test_strategy_review_package_does_not_expose_forbidden_behavior() -> None:
    from el_psy_quant import strategy_review

    forbidden_names = {
        "StrategyLifecycleStateSnapshot",
        "create_strategy_lifecycle_state_snapshot",
        "create_lifecycle_transition_proposal",
        "create_lifecycle_transition_record",
        "create_strategy_review_manifest",
        "discover_strategy_review_evidence",
        "load_strategy_review_evidence",
        "score_strategy_review_evidence",
        "rank_strategy_review_evidence",
        "run_strategy_review_workflow",
        "write_strategy_review_evidence",
        "read_strategy_review_evidence",
        "mark_live_ready",
        "allocate_capital",
    }

    for forbidden_name in forbidden_names:
        assert not hasattr(strategy_review, forbidden_name)
