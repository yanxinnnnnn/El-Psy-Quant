"""Tests for report sections."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.report_artifacts import (
    REPORT_SECTION_SCHEMA_VERSION,
    ReportSection,
    ReportSourceReference,
    create_report_section,
    create_report_source_reference,
)


def _source_reference() -> ReportSourceReference:
    return create_report_source_reference(
        reference_type="strategy_decision_record",
        reference_id="strategy-decision-record-1",
        label="Strategy decision record",
    )


def test_valid_report_section_creation_without_source_references() -> None:
    section = create_report_section(
        section_id="section-1",
        title="Executive context",
        content="Caller-supplied report section content.",
    )

    assert isinstance(section, ReportSection)
    assert section.section_id == "section-1"
    assert section.title == "Executive context"
    assert section.content == "Caller-supplied report section content."
    assert section.source_references == ()
    assert section.section_type is None
    assert section.notes is None


def test_valid_report_section_creation_with_explicit_source_references() -> None:
    source_reference = _source_reference()

    section = create_report_section(
        section_id="section-1",
        title="Decision context",
        content="This section references an existing decision record.",
        source_references=[source_reference],
    )

    assert section.source_references == (source_reference,)


def test_report_section_normalizes_fields() -> None:
    source_reference = _source_reference()

    section = create_report_section(
        section_id=" section-1 ",
        title=" Decision context ",
        content=" Caller-supplied content. ",
        source_references=[source_reference],
        section_type=" narrative ",
        notes="  ",
    )

    assert section.section_id == "section-1"
    assert section.title == "Decision context"
    assert section.content == "Caller-supplied content."
    assert section.source_references == (source_reference,)
    assert section.section_type == "narrative"
    assert section.notes is None


def test_optional_section_type_and_notes_normalize() -> None:
    section = create_report_section(
        section_id="section-1",
        title="Decision context",
        content="Caller-supplied content.",
        section_type=" summary ",
        notes=" reviewer note ",
    )

    assert section.section_type == "summary"
    assert section.notes == "reviewer note"


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("section_id", {"section_id": ""}),
        ("section_id", {"section_id": "   "}),
        ("title", {"title": ""}),
        ("title", {"title": "   "}),
        ("content", {"content": ""}),
        ("content", {"content": "   "}),
    ],
)
def test_empty_required_fields_raise_value_error(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "section_id": "section-1",
        "title": "Decision context",
        "content": "Caller-supplied content.",
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_report_section(**arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("section_id", {"section_id": object()}),
        ("title", {"title": object()}),
        ("content", {"content": object()}),
        ("section_type", {"section_type": object()}),
        ("notes", {"notes": object()}),
    ],
)
def test_invalid_string_field_types_raise_value_error(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "section_id": "section-1",
        "title": "Decision context",
        "content": "Caller-supplied content.",
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_report_section(**arguments)  # type: ignore[arg-type]


def test_source_references_reject_string_input() -> None:
    with pytest.raises(ValueError, match="source_references"):
        create_report_section(
            section_id="section-1",
            title="Decision context",
            content="Caller-supplied content.",
            source_references="not-a-sequence",  # type: ignore[arg-type]
        )


def test_source_references_reject_single_reference_instead_of_sequence() -> None:
    with pytest.raises(ValueError, match="source_references"):
        create_report_section(
            section_id="section-1",
            title="Decision context",
            content="Caller-supplied content.",
            source_references=_source_reference(),  # type: ignore[arg-type]
        )


def test_source_references_reject_invalid_items() -> None:
    with pytest.raises(ValueError, match="ReportSourceReference"):
        create_report_section(
            section_id="section-1",
            title="Decision context",
            content="Caller-supplied content.",
            source_references=[object()],  # type: ignore[list-item]
        )


def test_source_references_are_copied_to_immutable_tuple() -> None:
    source_references = [_source_reference()]

    section = create_report_section(
        section_id="section-1",
        title="Decision context",
        content="Caller-supplied content.",
        source_references=source_references,
    )
    source_references.append(_source_reference())

    assert len(section.source_references) == 1


def test_to_dict_is_deterministic_and_json_compatible() -> None:
    source_reference = _source_reference()
    section = create_report_section(
        section_id="section-1",
        title="Decision context",
        content="Caller-supplied content.",
        source_references=[source_reference],
        section_type="summary",
        notes="Manual reviewer context.",
    )

    expected = {
        "schema_version": REPORT_SECTION_SCHEMA_VERSION,
        "section_id": "section-1",
        "title": "Decision context",
        "content": "Caller-supplied content.",
        "source_references": [source_reference.to_dict()],
        "section_type": "summary",
        "notes": "Manual reviewer context.",
    }

    assert section.to_dict() == expected
    assert section.to_dict() == expected
    json.dumps(section.to_dict(), allow_nan=False)


def test_source_reference_to_dict_is_included_in_section_export() -> None:
    source_reference = _source_reference()

    section = create_report_section(
        section_id="section-1",
        title="Decision context",
        content="Caller-supplied content.",
        source_references=[source_reference],
    )

    assert section.to_dict()["source_references"] == [source_reference.to_dict()]


def test_schema_version_is_json_compatible() -> None:
    assert REPORT_SECTION_SCHEMA_VERSION == 1
    json.dumps(
        {"schema_version": REPORT_SECTION_SCHEMA_VERSION},
        allow_nan=False,
    )


def test_report_section_is_immutable() -> None:
    section = create_report_section(
        section_id="section-1",
        title="Decision context",
        content="Caller-supplied content.",
    )

    with pytest.raises(FrozenInstanceError):
        section.section_id = "other"  # type: ignore[misc]


def test_report_artifacts_package_exports_section_public_api() -> None:
    from el_psy_quant import report_artifacts

    assert (
        report_artifacts.REPORT_SECTION_SCHEMA_VERSION
        == REPORT_SECTION_SCHEMA_VERSION
    )
    assert report_artifacts.ReportSection is ReportSection
    assert report_artifacts.create_report_section is create_report_section


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
