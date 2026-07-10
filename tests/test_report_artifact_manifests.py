"""Tests for report artifact manifests and references."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.report_artifacts import (
    REPORT_ARTIFACT_MANIFEST_SCHEMA_VERSION,
    REPORT_ARTIFACT_REFERENCE_SCHEMA_VERSION,
    SUPPORTED_REPORT_ARTIFACT_REFERENCE_TYPES,
    ReportArtifactManifest,
    ReportArtifactReference,
    ReportArtifactSummary,
    create_report_artifact_manifest,
    create_report_artifact_reference,
    create_report_artifact_reference_from_summary,
    create_report_artifact_summary,
    create_report_section,
    create_report_source_reference,
)


def _reference(reference_id: str = "report-1") -> ReportArtifactReference:
    return create_report_artifact_reference(
        reference_type="report_artifact_summary",
        reference_id=reference_id,
    )


def _summary() -> ReportArtifactSummary:
    source_reference = create_report_source_reference(
        reference_type="strategy_decision_record",
        reference_id="decision-record-1",
    )
    section = create_report_section(
        section_id="section-1",
        title="Decision context",
        content="Caller-supplied report content.",
        source_references=[source_reference],
    )
    return create_report_artifact_summary(
        report_id="report-1",
        title="Strategy decision report",
        sections=[section],
        summary="Caller-supplied summary metadata.",
    )


def test_valid_report_artifact_reference_creation() -> None:
    reference = create_report_artifact_reference(
        reference_type="report_artifact_summary",
        reference_id="report-1",
        label="Decision report",
        description="Completed report artifact summary.",
    )

    assert isinstance(reference, ReportArtifactReference)
    assert reference.reference_type == "report_artifact_summary"
    assert reference.reference_id == "report-1"
    assert reference.label == "Decision report"
    assert reference.description == "Completed report artifact summary."


def test_supported_reference_types_are_intentionally_narrow() -> None:
    assert SUPPORTED_REPORT_ARTIFACT_REFERENCE_TYPES == (
        "report_artifact_summary",
    )


def test_reference_normalizes_whitespace_and_optional_metadata() -> None:
    reference = create_report_artifact_reference(
        reference_type=" report_artifact_summary ",
        reference_id=" report-1 ",
        label=" Decision report ",
        description="  ",
    )

    assert reference.reference_type == "report_artifact_summary"
    assert reference.reference_id == "report-1"
    assert reference.label == "Decision report"
    assert reference.description is None


def test_unsupported_reference_type_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported reference_type"):
        create_report_artifact_reference(
            reference_type="report_section",
            reference_id="report-1",
        )


@pytest.mark.parametrize("reference_id", ["", "   "])
def test_empty_reference_id_is_rejected(reference_id: str) -> None:
    with pytest.raises(ValueError, match="reference_id"):
        create_report_artifact_reference(
            reference_type="report_artifact_summary",
            reference_id=reference_id,
        )


def test_reference_to_dict_is_deterministic_and_json_compatible() -> None:
    reference = create_report_artifact_reference(
        reference_type="report_artifact_summary",
        reference_id="report-1",
        label="Decision report",
        description="Completed report artifact summary.",
    )
    expected = {
        "schema_version": REPORT_ARTIFACT_REFERENCE_SCHEMA_VERSION,
        "reference_type": "report_artifact_summary",
        "reference_id": "report-1",
        "label": "Decision report",
        "description": "Completed report artifact summary.",
    }

    assert reference.to_dict() == expected
    assert reference.to_dict() == expected
    json.dumps(reference.to_dict(), allow_nan=False)


def test_valid_manifest_with_one_reference() -> None:
    reference = _reference()
    manifest = create_report_artifact_manifest(
        manifest_id="manifest-1",
        references=[reference],
    )

    assert isinstance(manifest, ReportArtifactManifest)
    assert manifest.manifest_id == "manifest-1"
    assert manifest.references == (reference,)


def test_valid_manifest_with_multiple_references() -> None:
    first_reference = _reference("report-1")
    second_reference = _reference("report-2")
    manifest = create_report_artifact_manifest(
        manifest_id="manifest-1",
        references=[first_reference, second_reference],
    )

    assert manifest.references == (first_reference, second_reference)


def test_manifest_normalizes_whitespace_and_optional_metadata() -> None:
    manifest = create_report_artifact_manifest(
        manifest_id=" manifest-1 ",
        references=[_reference()],
        label=" Review package ",
        description=" Explicit report references. ",
        created_by=" reviewer-1 ",
        created_timestamp=" 2026-07-10T12:00:00Z ",
        notes="  ",
    )

    assert manifest.manifest_id == "manifest-1"
    assert manifest.label == "Review package"
    assert manifest.description == "Explicit report references."
    assert manifest.created_by == "reviewer-1"
    assert manifest.created_timestamp == "2026-07-10T12:00:00Z"
    assert manifest.notes is None


def test_empty_manifest_references_are_rejected() -> None:
    with pytest.raises(ValueError, match="references"):
        create_report_artifact_manifest(
            manifest_id="manifest-1",
            references=[],
        )


@pytest.mark.parametrize("references", ["not-references", [object()]])
def test_invalid_manifest_references_are_rejected(references: object) -> None:
    with pytest.raises(ValueError, match="references"):
        create_report_artifact_manifest(
            manifest_id="manifest-1",
            references=references,  # type: ignore[arg-type]
        )


def test_manifest_references_are_copied_to_immutable_tuple() -> None:
    references = [_reference()]
    manifest = create_report_artifact_manifest(
        manifest_id="manifest-1",
        references=references,
    )
    references.append(_reference("report-2"))

    assert len(manifest.references) == 1


def test_manifest_to_dict_is_deterministic_and_nested() -> None:
    reference = _reference()
    manifest = create_report_artifact_manifest(
        manifest_id="manifest-1",
        references=[reference],
        label="Review package",
        description="Explicit report references.",
        created_by="reviewer-1",
        created_timestamp="2026-07-10T12:00:00Z",
        notes="Manual context.",
    )
    expected = {
        "schema_version": REPORT_ARTIFACT_MANIFEST_SCHEMA_VERSION,
        "manifest_id": "manifest-1",
        "references": [reference.to_dict()],
        "label": "Review package",
        "description": "Explicit report references.",
        "created_by": "reviewer-1",
        "created_timestamp": "2026-07-10T12:00:00Z",
        "notes": "Manual context.",
    }

    assert manifest.to_dict() == expected
    assert manifest.to_dict() == expected
    json.dumps(manifest.to_dict(), allow_nan=False)


def test_reference_from_summary_extracts_only_stable_report_id() -> None:
    summary = _summary()
    reference = create_report_artifact_reference_from_summary(summary)

    assert reference.reference_type == "report_artifact_summary"
    assert reference.reference_id == summary.report_id
    assert reference.label is None
    assert reference.description is None


def test_reference_from_summary_preserves_caller_metadata() -> None:
    reference = create_report_artifact_reference_from_summary(
        _summary(),
        label="Decision report",
        description="Manually selected summary.",
    )

    assert reference.label == "Decision report"
    assert reference.description == "Manually selected summary."


def test_reference_from_summary_rejects_invalid_input() -> None:
    with pytest.raises(ValueError, match="ReportArtifactSummary"):
        create_report_artifact_reference_from_summary(object())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("label", {"label": object()}),
        ("description", {"description": object()}),
        ("created_by", {"created_by": object()}),
        ("created_timestamp", {"created_timestamp": object()}),
        ("notes", {"notes": object()}),
    ],
)
def test_invalid_optional_manifest_strings_are_rejected(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "manifest_id": "manifest-1",
        "references": [_reference()],
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_report_artifact_manifest(**arguments)  # type: ignore[arg-type]


def test_reference_and_manifest_are_immutable() -> None:
    reference = _reference()
    manifest = create_report_artifact_manifest(
        manifest_id="manifest-1",
        references=[reference],
    )

    with pytest.raises(FrozenInstanceError):
        reference.reference_id = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        manifest.manifest_id = "other"  # type: ignore[misc]


def test_report_artifacts_package_exports_manifest_public_api() -> None:
    from el_psy_quant import report_artifacts

    assert (
        report_artifacts.REPORT_ARTIFACT_REFERENCE_SCHEMA_VERSION
        == REPORT_ARTIFACT_REFERENCE_SCHEMA_VERSION
    )
    assert (
        report_artifacts.REPORT_ARTIFACT_MANIFEST_SCHEMA_VERSION
        == REPORT_ARTIFACT_MANIFEST_SCHEMA_VERSION
    )
    assert (
        report_artifacts.SUPPORTED_REPORT_ARTIFACT_REFERENCE_TYPES
        == SUPPORTED_REPORT_ARTIFACT_REFERENCE_TYPES
    )
    assert report_artifacts.ReportArtifactReference is ReportArtifactReference
    assert report_artifacts.ReportArtifactManifest is ReportArtifactManifest
    assert (
        report_artifacts.create_report_artifact_reference
        is create_report_artifact_reference
    )
    assert (
        report_artifacts.create_report_artifact_manifest
        is create_report_artifact_manifest
    )
    assert (
        report_artifacts.create_report_artifact_reference_from_summary
        is create_report_artifact_reference_from_summary
    )


def test_report_artifacts_package_does_not_expose_forbidden_behavior() -> None:
    from el_psy_quant import report_artifacts

    forbidden_names = {
        "write_report_artifact_manifest",
        "read_report_artifact_manifest",
        "load_report_artifact",
        "discover_report_artifacts",
        "render_report",
        "render_dashboard",
        "generate_report",
        "score_report_artifacts",
        "rank_report_artifacts",
        "run_report_workflow",
        "mark_live_ready",
    }

    for forbidden_name in forbidden_names:
        assert not hasattr(report_artifacts, forbidden_name)
