"""Tests for paper review references and manifests."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.paper_review import (
    PAPER_REVIEW_MANIFEST_SCHEMA_VERSION,
    PAPER_REVIEW_REFERENCE_SCHEMA_VERSION,
    SUPPORTED_PAPER_REVIEW_REFERENCE_TYPES,
    PaperReviewManifest,
    PaperReviewReference,
    PaperRunComparisonSummary,
    PaperRunReviewDecision,
    create_paper_review_manifest,
    create_paper_review_reference,
    create_paper_review_reference_from_decision,
    create_paper_review_reference_from_summary,
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


def _review_decision() -> PaperRunReviewDecision:
    return create_paper_run_review_decision(
        decision_id="decision-1",
        comparison_summary=_comparison_summary(),
        decision_status="needs_more_evidence",
        rationale="Need more paper review before any later decision.",
    )


def _comparison_reference() -> PaperReviewReference:
    return create_paper_review_reference(
        reference_type="comparison_summary",
        reference_id="summary-1",
        label="Summary 1",
    )


def _decision_reference() -> PaperReviewReference:
    return create_paper_review_reference(
        reference_type="review_decision",
        reference_id="decision-1",
        label="Decision 1",
    )


def test_valid_paper_review_reference_creation() -> None:
    reference = create_paper_review_reference(
        reference_type="comparison_summary",
        reference_id="summary-1",
        label="Summary 1",
        description="Caller supplied comparison summary.",
    )

    assert isinstance(reference, PaperReviewReference)
    assert reference.reference_type == "comparison_summary"
    assert reference.reference_id == "summary-1"
    assert reference.label == "Summary 1"
    assert reference.description == "Caller supplied comparison summary."


def test_supported_reference_types_are_explicit_and_deterministic() -> None:
    assert SUPPORTED_PAPER_REVIEW_REFERENCE_TYPES == (
        "comparison_summary",
        "review_decision",
    )


def test_invalid_reference_type_raises_value_error() -> None:
    with pytest.raises(ValueError, match="comparison_summary"):
        create_paper_review_reference(
            reference_type="paper_artifact",
            reference_id="summary-1",
        )


@pytest.mark.parametrize("reference_id", ["", "   "])
def test_blank_required_reference_id_raises_value_error(reference_id: str) -> None:
    with pytest.raises(ValueError, match="reference_id"):
        create_paper_review_reference(
            reference_type="comparison_summary",
            reference_id=reference_id,
        )


def test_required_reference_fields_trim() -> None:
    reference = create_paper_review_reference(
        reference_type=" comparison_summary ",
        reference_id=" summary-1 ",
    )

    assert reference.reference_type == "comparison_summary"
    assert reference.reference_id == "summary-1"


def test_optional_reference_fields_normalize() -> None:
    reference = create_paper_review_reference(
        reference_type="comparison_summary",
        reference_id="summary-1",
        label="  ",
        description=" description ",
    )

    assert reference.label is None
    assert reference.description == "description"


def test_invalid_reference_optional_field_types_raise_value_error() -> None:
    with pytest.raises(ValueError, match="label"):
        create_paper_review_reference(
            reference_type="comparison_summary",
            reference_id="summary-1",
            label=object(),  # type: ignore[arg-type]
        )


def test_reference_to_dict_is_deterministic_and_json_compatible() -> None:
    reference = create_paper_review_reference(
        reference_type="comparison_summary",
        reference_id="summary-1",
        label="Summary 1",
        description="Caller supplied comparison summary.",
    )

    expected = {
        "schema_version": PAPER_REVIEW_REFERENCE_SCHEMA_VERSION,
        "reference_type": "comparison_summary",
        "reference_id": "summary-1",
        "label": "Summary 1",
        "description": "Caller supplied comparison summary.",
    }
    assert reference.to_dict() == expected
    assert reference.to_dict() == expected
    json.dumps(reference.to_dict(), allow_nan=False)


def test_reference_from_summary_uses_existing_summary_id_only() -> None:
    summary = _comparison_summary()

    reference = create_paper_review_reference_from_summary(
        summary,
        label=" Summary ",
    )

    assert reference.reference_type == "comparison_summary"
    assert reference.reference_id == "summary-1"
    assert reference.label == "Summary"


def test_reference_from_decision_uses_existing_decision_id_only() -> None:
    decision = _review_decision()

    reference = create_paper_review_reference_from_decision(
        decision,
        description=" Decision ",
    )

    assert reference.reference_type == "review_decision"
    assert reference.reference_id == "decision-1"
    assert reference.description == "Decision"


def test_reference_helpers_reject_invalid_objects() -> None:
    with pytest.raises(ValueError, match="PaperRunComparisonSummary"):
        create_paper_review_reference_from_summary(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="PaperRunReviewDecision"):
        create_paper_review_reference_from_decision(object())  # type: ignore[arg-type]


def test_valid_manifest_creation_with_comparison_references_only() -> None:
    reference = _comparison_reference()

    manifest = create_paper_review_manifest(
        manifest_id="manifest-1",
        comparison_references=[reference],
    )

    assert isinstance(manifest, PaperReviewManifest)
    assert manifest.manifest_id == "manifest-1"
    assert manifest.comparison_references == (reference,)
    assert manifest.decision_references == ()


def test_valid_manifest_creation_with_decision_references_only() -> None:
    reference = _decision_reference()

    manifest = create_paper_review_manifest(
        manifest_id="manifest-1",
        decision_references=[reference],
    )

    assert manifest.comparison_references == ()
    assert manifest.decision_references == (reference,)


def test_valid_manifest_creation_with_both_reference_groups() -> None:
    comparison_reference = _comparison_reference()
    decision_reference = _decision_reference()

    manifest = create_paper_review_manifest(
        manifest_id="manifest-1",
        comparison_references=[comparison_reference],
        decision_references=[decision_reference],
    )

    assert manifest.comparison_references == (comparison_reference,)
    assert manifest.decision_references == (decision_reference,)


@pytest.mark.parametrize("manifest_id", ["", "   "])
def test_manifest_id_validation(manifest_id: str) -> None:
    with pytest.raises(ValueError, match="manifest_id"):
        create_paper_review_manifest(
            manifest_id=manifest_id,
            comparison_references=[_comparison_reference()],
        )


def test_manifest_id_trimming() -> None:
    manifest = create_paper_review_manifest(
        manifest_id=" manifest-1 ",
        comparison_references=[_comparison_reference()],
    )

    assert manifest.manifest_id == "manifest-1"


def test_manifest_rejects_both_reference_groups_empty() -> None:
    with pytest.raises(ValueError, match="at least one"):
        create_paper_review_manifest(manifest_id="manifest-1")


def test_manifest_rejects_bare_reference_instead_of_sequence() -> None:
    with pytest.raises(ValueError, match="comparison_references"):
        create_paper_review_manifest(
            manifest_id="manifest-1",
            comparison_references=_comparison_reference(),  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("comparison_references", {"comparison_references": "summary-1"}),
        ("decision_references", {"decision_references": "decision-1"}),
    ],
)
def test_manifest_rejects_bare_string_sequence_fields(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {"manifest_id": "manifest-1"}
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_paper_review_manifest(**arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("comparison_references", {"comparison_references": [object()]}),
        ("decision_references", {"decision_references": [object()]}),
    ],
)
def test_manifest_rejects_invalid_sequence_elements(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {"manifest_id": "manifest-1"}
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_paper_review_manifest(**arguments)  # type: ignore[arg-type]


def test_manifest_rejects_wrong_reference_type_in_each_group() -> None:
    with pytest.raises(ValueError, match="comparison_references"):
        create_paper_review_manifest(
            manifest_id="manifest-1",
            comparison_references=[_decision_reference()],
        )
    with pytest.raises(ValueError, match="decision_references"):
        create_paper_review_manifest(
            manifest_id="manifest-2",
            decision_references=[_comparison_reference()],
        )


def test_manifest_normalizes_reference_sequences_to_immutable_tuples() -> None:
    comparison_references = [_comparison_reference()]
    decision_references = [_decision_reference()]

    manifest = create_paper_review_manifest(
        manifest_id="manifest-1",
        comparison_references=comparison_references,
        decision_references=decision_references,
    )
    comparison_references.append(_comparison_reference())
    decision_references.append(_decision_reference())

    assert len(manifest.comparison_references) == 1
    assert len(manifest.decision_references) == 1


def test_manifest_optional_fields_normalize() -> None:
    manifest = create_paper_review_manifest(
        manifest_id="manifest-1",
        comparison_references=[_comparison_reference()],
        created_by="  ",
        description=" description ",
    )

    assert manifest.created_by is None
    assert manifest.description == "description"


def test_invalid_manifest_optional_field_types_raise_value_error() -> None:
    with pytest.raises(ValueError, match="created_by"):
        create_paper_review_manifest(
            manifest_id="manifest-1",
            comparison_references=[_comparison_reference()],
            created_by=object(),  # type: ignore[arg-type]
        )


def test_manifest_timestamp_normalizes_to_deterministic_export() -> None:
    manifest = create_paper_review_manifest(
        manifest_id="manifest-1",
        comparison_references=[_comparison_reference()],
        created_timestamp="2026-01-02T03:04:05",
    )

    assert manifest.to_dict()["created_timestamp"] == "2026-01-02T03:04:05"


def test_invalid_manifest_timestamp_raises_value_error() -> None:
    with pytest.raises(ValueError, match="created_timestamp"):
        create_paper_review_manifest(
            manifest_id="manifest-1",
            comparison_references=[_comparison_reference()],
            created_timestamp="not-a-timestamp",
        )


def test_manifest_to_dict_is_deterministic_and_json_compatible() -> None:
    comparison_reference = _comparison_reference()
    decision_reference = _decision_reference()
    manifest = create_paper_review_manifest(
        manifest_id="manifest-1",
        comparison_references=[comparison_reference],
        decision_references=[decision_reference],
        created_by="reviewer-1",
        created_timestamp="2026-01-02T03:04:05",
        description="Manual paper review manifest.",
    )

    expected = {
        "schema_version": PAPER_REVIEW_MANIFEST_SCHEMA_VERSION,
        "manifest_id": "manifest-1",
        "comparison_references": [comparison_reference.to_dict()],
        "decision_references": [decision_reference.to_dict()],
        "created_by": "reviewer-1",
        "created_timestamp": "2026-01-02T03:04:05",
        "description": "Manual paper review manifest.",
    }

    assert manifest.to_dict() == expected
    assert manifest.to_dict() == expected
    json.dumps(manifest.to_dict(), allow_nan=False)


def test_schema_versions_are_json_compatible() -> None:
    assert PAPER_REVIEW_REFERENCE_SCHEMA_VERSION == 1
    assert PAPER_REVIEW_MANIFEST_SCHEMA_VERSION == 1
    json.dumps(
        {
            "reference": PAPER_REVIEW_REFERENCE_SCHEMA_VERSION,
            "manifest": PAPER_REVIEW_MANIFEST_SCHEMA_VERSION,
        },
        allow_nan=False,
    )


def test_review_reference_and_manifest_are_immutable() -> None:
    reference = _comparison_reference()
    manifest = create_paper_review_manifest(
        manifest_id="manifest-1",
        comparison_references=[reference],
    )

    with pytest.raises(FrozenInstanceError):
        reference.reference_id = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        manifest.manifest_id = "other"  # type: ignore[misc]


def test_paper_review_package_exports_manifest_public_api() -> None:
    from el_psy_quant import paper_review

    assert (
        paper_review.PAPER_REVIEW_REFERENCE_SCHEMA_VERSION
        == PAPER_REVIEW_REFERENCE_SCHEMA_VERSION
    )
    assert (
        paper_review.PAPER_REVIEW_MANIFEST_SCHEMA_VERSION
        == PAPER_REVIEW_MANIFEST_SCHEMA_VERSION
    )
    assert (
        paper_review.SUPPORTED_PAPER_REVIEW_REFERENCE_TYPES
        == SUPPORTED_PAPER_REVIEW_REFERENCE_TYPES
    )
    assert paper_review.PaperReviewReference is PaperReviewReference
    assert paper_review.PaperReviewManifest is PaperReviewManifest
    assert paper_review.create_paper_review_reference is create_paper_review_reference
    assert paper_review.create_paper_review_manifest is create_paper_review_manifest
    assert (
        paper_review.create_paper_review_reference_from_summary
        is create_paper_review_reference_from_summary
    )
    assert (
        paper_review.create_paper_review_reference_from_decision
        is create_paper_review_reference_from_decision
    )


def test_paper_review_package_does_not_expose_forbidden_runtime_behavior() -> None:
    from el_psy_quant import paper_review

    forbidden_names = {
        "write_paper_review_manifest",
        "read_paper_review_manifest",
        "scan_paper_review_directories",
        "load_paper_artifact",
        "save_paper_review_manifest",
        "insert_paper_review_database_row",
        "run_paper_workflow",
        "create_dashboard",
        "render_paper_review_report",
        "approve_live_trading",
        "allocate_capital",
        "route_orders",
        "mark_live_ready",
        "mark_real_money_ready",
    }

    for forbidden_name in forbidden_names:
        assert not hasattr(paper_review, forbidden_name)
