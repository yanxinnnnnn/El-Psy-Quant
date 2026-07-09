"""Tests for report artifact summaries."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.report_artifacts import (
    REPORT_ARTIFACT_SUMMARY_SCHEMA_VERSION,
    ReportArtifactSummary,
    ReportSection,
    create_report_artifact_summary,
    create_report_section,
    create_report_source_reference,
)


def _section(section_id: str = "section-1") -> ReportSection:
    source_reference = create_report_source_reference(
        reference_type="strategy_decision_record",
        reference_id="strategy-decision-record-1",
    )
    return create_report_section(
        section_id=section_id,
        title=f"Section {section_id}",
        content="Caller-supplied section content.",
        source_references=[source_reference],
    )


def test_valid_report_artifact_summary_creation_with_one_section() -> None:
    section = _section()

    report_summary = create_report_artifact_summary(
        report_id="report-1",
        title="Strategy decision report",
        sections=[section],
    )

    assert isinstance(report_summary, ReportArtifactSummary)
    assert report_summary.report_id == "report-1"
    assert report_summary.title == "Strategy decision report"
    assert report_summary.sections == (section,)
    assert report_summary.summary is None
    assert report_summary.purpose is None
    assert report_summary.created_by is None
    assert report_summary.created_timestamp is None
    assert report_summary.notes is None


def test_valid_report_artifact_summary_creation_with_multiple_sections() -> None:
    first_section = _section("section-1")
    second_section = _section("section-2")

    report_summary = create_report_artifact_summary(
        report_id="report-1",
        title="Strategy decision report",
        sections=[first_section, second_section],
    )

    assert report_summary.sections == (first_section, second_section)


def test_report_artifact_summary_normalizes_fields() -> None:
    section = _section()

    report_summary = create_report_artifact_summary(
        report_id=" report-1 ",
        title=" Strategy decision report ",
        sections=[section],
        summary=" Caller-supplied summary. ",
        purpose=" Manual governance review. ",
        created_by=" reviewer-1 ",
        created_timestamp=" 2026-01-02T03:04:05 ",
        notes="  ",
    )

    assert report_summary.report_id == "report-1"
    assert report_summary.title == "Strategy decision report"
    assert report_summary.summary == "Caller-supplied summary."
    assert report_summary.purpose == "Manual governance review."
    assert report_summary.created_by == "reviewer-1"
    assert report_summary.created_timestamp == "2026-01-02T03:04:05"
    assert report_summary.notes is None


def test_optional_metadata_normalizes() -> None:
    report_summary = create_report_artifact_summary(
        report_id="report-1",
        title="Strategy decision report",
        sections=[_section()],
        summary=" Summary ",
        purpose=" Purpose ",
        created_by=" Reviewer ",
        created_timestamp=" Timestamp ",
        notes=" Notes ",
    )

    assert report_summary.summary == "Summary"
    assert report_summary.purpose == "Purpose"
    assert report_summary.created_by == "Reviewer"
    assert report_summary.created_timestamp == "Timestamp"
    assert report_summary.notes == "Notes"


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("report_id", {"report_id": ""}),
        ("report_id", {"report_id": "   "}),
        ("title", {"title": ""}),
        ("title", {"title": "   "}),
    ],
)
def test_empty_required_fields_raise_value_error(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "report_id": "report-1",
        "title": "Strategy decision report",
        "sections": [_section()],
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_report_artifact_summary(**arguments)  # type: ignore[arg-type]


def test_empty_sections_raise_value_error() -> None:
    with pytest.raises(ValueError, match="sections"):
        create_report_artifact_summary(
            report_id="report-1",
            title="Strategy decision report",
            sections=[],
        )


def test_sections_reject_string_input() -> None:
    with pytest.raises(ValueError, match="sections"):
        create_report_artifact_summary(
            report_id="report-1",
            title="Strategy decision report",
            sections="not-a-sequence",  # type: ignore[arg-type]
        )


def test_sections_reject_single_section_instead_of_sequence() -> None:
    with pytest.raises(ValueError, match="sections"):
        create_report_artifact_summary(
            report_id="report-1",
            title="Strategy decision report",
            sections=_section(),  # type: ignore[arg-type]
        )


def test_sections_reject_invalid_items() -> None:
    with pytest.raises(ValueError, match="ReportSection"):
        create_report_artifact_summary(
            report_id="report-1",
            title="Strategy decision report",
            sections=[object()],  # type: ignore[list-item]
        )


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("report_id", {"report_id": object()}),
        ("title", {"title": object()}),
        ("summary", {"summary": object()}),
        ("purpose", {"purpose": object()}),
        ("created_by", {"created_by": object()}),
        ("created_timestamp", {"created_timestamp": object()}),
        ("notes", {"notes": object()}),
    ],
)
def test_invalid_string_field_types_raise_value_error(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "report_id": "report-1",
        "title": "Strategy decision report",
        "sections": [_section()],
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_report_artifact_summary(**arguments)  # type: ignore[arg-type]


def test_sections_are_copied_to_immutable_tuple() -> None:
    sections = [_section()]

    report_summary = create_report_artifact_summary(
        report_id="report-1",
        title="Strategy decision report",
        sections=sections,
    )
    sections.append(_section("section-2"))

    assert len(report_summary.sections) == 1


def test_to_dict_is_deterministic_and_json_compatible() -> None:
    section = _section()
    report_summary = create_report_artifact_summary(
        report_id="report-1",
        title="Strategy decision report",
        sections=[section],
        summary="Caller-supplied report summary.",
        purpose="Manual governance review.",
        created_by="reviewer-1",
        created_timestamp="2026-01-02T03:04:05",
        notes="Manual reviewer context.",
    )

    expected = {
        "schema_version": REPORT_ARTIFACT_SUMMARY_SCHEMA_VERSION,
        "report_id": "report-1",
        "title": "Strategy decision report",
        "sections": [section.to_dict()],
        "summary": "Caller-supplied report summary.",
        "purpose": "Manual governance review.",
        "created_by": "reviewer-1",
        "created_timestamp": "2026-01-02T03:04:05",
        "notes": "Manual reviewer context.",
    }

    assert report_summary.to_dict() == expected
    assert report_summary.to_dict() == expected
    json.dumps(report_summary.to_dict(), allow_nan=False)


def test_section_to_dict_is_included_in_summary_export() -> None:
    section = _section()

    report_summary = create_report_artifact_summary(
        report_id="report-1",
        title="Strategy decision report",
        sections=[section],
    )

    assert report_summary.to_dict()["sections"] == [section.to_dict()]


def test_schema_version_is_json_compatible() -> None:
    assert REPORT_ARTIFACT_SUMMARY_SCHEMA_VERSION == 1
    json.dumps(
        {"schema_version": REPORT_ARTIFACT_SUMMARY_SCHEMA_VERSION},
        allow_nan=False,
    )


def test_report_artifact_summary_is_immutable() -> None:
    report_summary = create_report_artifact_summary(
        report_id="report-1",
        title="Strategy decision report",
        sections=[_section()],
    )

    with pytest.raises(FrozenInstanceError):
        report_summary.report_id = "other"  # type: ignore[misc]


def test_report_artifacts_package_exports_summary_public_api() -> None:
    from el_psy_quant import report_artifacts

    assert (
        report_artifacts.REPORT_ARTIFACT_SUMMARY_SCHEMA_VERSION
        == REPORT_ARTIFACT_SUMMARY_SCHEMA_VERSION
    )
    assert report_artifacts.ReportArtifactSummary is ReportArtifactSummary
    assert (
        report_artifacts.create_report_artifact_summary
        is create_report_artifact_summary
    )


def test_report_artifacts_package_does_not_expose_forbidden_behavior() -> None:
    from el_psy_quant import report_artifacts

    forbidden_names = {
        "ReportManifest",
        "create_report_manifest",
        "render_report",
        "render_dashboard",
        "generate_report",
        "discover_report_sources",
        "load_report_source",
        "calculate_report_metrics",
        "score_report_source",
        "rank_report_sources",
        "recommend_report_action",
        "run_report_workflow",
        "write_report_artifact",
        "read_report_artifact",
        "approve_live_trading",
        "mark_live_ready",
        "mark_real_money_ready",
    }

    for forbidden_name in forbidden_names:
        assert not hasattr(report_artifacts, forbidden_name)
