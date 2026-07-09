"""Tests for report source references."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.report_artifacts import (
    REPORT_SOURCE_REFERENCE_SCHEMA_VERSION,
    SUPPORTED_REPORT_SOURCE_REFERENCE_TYPES,
    ReportSourceReference,
    create_report_source_reference,
)


def test_valid_report_source_reference_creation() -> None:
    reference = create_report_source_reference(
        reference_type="promotion_record",
        reference_id="promotion-record-1",
        label="Promotion record",
        description="Human-controlled promotion decision.",
    )

    assert isinstance(reference, ReportSourceReference)
    assert reference.reference_type == "promotion_record"
    assert reference.reference_id == "promotion-record-1"
    assert reference.label == "Promotion record"
    assert reference.description == "Human-controlled promotion decision."


def test_supported_report_source_reference_types_are_deterministic() -> None:
    assert SUPPORTED_REPORT_SOURCE_REFERENCE_TYPES == (
        "promotion_evidence_summary",
        "promotion_record",
        "promotion_manifest",
        "paper_comparison_summary",
        "paper_review_decision",
        "paper_review_manifest",
        "strategy_decision_summary",
        "strategy_decision_record",
        "strategy_decision_manifest",
    )
    json.dumps(
        {"reference_types": SUPPORTED_REPORT_SOURCE_REFERENCE_TYPES},
        allow_nan=False,
    )


def test_report_source_reference_normalizes_fields() -> None:
    reference = create_report_source_reference(
        reference_type=" strategy_decision_manifest ",
        reference_id=" decision-manifest-1 ",
        label=" Strategy decision manifest ",
        description="  ",
    )

    assert reference.reference_type == "strategy_decision_manifest"
    assert reference.reference_id == "decision-manifest-1"
    assert reference.label == "Strategy decision manifest"
    assert reference.description is None


@pytest.mark.parametrize(
    "reference_type",
    SUPPORTED_REPORT_SOURCE_REFERENCE_TYPES,
)
def test_all_supported_reference_types_can_be_created(reference_type: str) -> None:
    reference = create_report_source_reference(
        reference_type=reference_type,
        reference_id=f"{reference_type}-1",
    )

    assert reference.reference_type == reference_type
    assert reference.reference_id == f"{reference_type}-1"


def test_unsupported_reference_type_raises_value_error() -> None:
    with pytest.raises(ValueError, match="unsupported reference_type"):
        create_report_source_reference(
            reference_type="research_run",
            reference_id="run-1",
        )


def test_unsupported_reference_type_error_includes_supported_type() -> None:
    with pytest.raises(ValueError, match="strategy_decision_manifest"):
        create_report_source_reference(
            reference_type="research_run",
            reference_id="run-1",
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
        create_report_source_reference(**arguments)  # type: ignore[arg-type]


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
        create_report_source_reference(**arguments)  # type: ignore[arg-type]


def test_to_dict_is_deterministic_and_json_compatible() -> None:
    reference = create_report_source_reference(
        reference_type="paper_review_decision",
        reference_id="paper-review-decision-1",
        label="Paper review decision",
        description="Human-controlled paper review decision.",
    )

    expected = {
        "schema_version": REPORT_SOURCE_REFERENCE_SCHEMA_VERSION,
        "reference_type": "paper_review_decision",
        "reference_id": "paper-review-decision-1",
        "label": "Paper review decision",
        "description": "Human-controlled paper review decision.",
    }

    assert reference.to_dict() == expected
    assert reference.to_dict() == expected
    json.dumps(reference.to_dict(), allow_nan=False)


def test_schema_version_is_json_compatible() -> None:
    assert REPORT_SOURCE_REFERENCE_SCHEMA_VERSION == 1
    json.dumps(
        {"schema_version": REPORT_SOURCE_REFERENCE_SCHEMA_VERSION},
        allow_nan=False,
    )


def test_report_source_reference_is_immutable() -> None:
    reference = create_report_source_reference(
        reference_type="promotion_record",
        reference_id="promotion-record-1",
    )

    with pytest.raises(FrozenInstanceError):
        reference.reference_id = "other"  # type: ignore[misc]


def test_report_artifacts_package_exports_public_api() -> None:
    from el_psy_quant import report_artifacts

    assert (
        report_artifacts.REPORT_SOURCE_REFERENCE_SCHEMA_VERSION
        == REPORT_SOURCE_REFERENCE_SCHEMA_VERSION
    )
    assert (
        report_artifacts.SUPPORTED_REPORT_SOURCE_REFERENCE_TYPES
        == SUPPORTED_REPORT_SOURCE_REFERENCE_TYPES
    )
    assert report_artifacts.ReportSourceReference is ReportSourceReference
    assert (
        report_artifacts.create_report_source_reference
        is create_report_source_reference
    )


def test_report_artifacts_package_does_not_expose_forbidden_behavior() -> None:
    from el_psy_quant import report_artifacts

    forbidden_names = {
        "ReportSection",
        "ReportArtifactSummary",
        "ReportManifest",
        "create_report_section",
        "create_report_artifact_summary",
        "create_report_manifest",
        "render_report",
        "render_dashboard",
        "generate_report",
        "discover_report_sources",
        "load_report_source",
        "score_report_source",
        "rank_report_sources",
        "run_report_workflow",
        "write_report_artifact",
        "read_report_artifact",
        "approve_live_trading",
        "mark_live_ready",
        "mark_real_money_ready",
    }

    for forbidden_name in forbidden_names:
        assert not hasattr(report_artifacts, forbidden_name)
