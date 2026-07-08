"""Tests for paper run references."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.paper_review import (
    PAPER_RUN_REFERENCE_SCHEMA_VERSION,
    SUPPORTED_PAPER_RUN_REFERENCE_TYPES,
    PaperRunReference,
    create_paper_run_reference,
)


def test_valid_paper_run_reference_creation() -> None:
    reference = create_paper_run_reference(
        reference_type="paper_result_summary",
        reference="outputs/run-1/paper/paper_run_result_summary.json",
        run_id="run-1",
        artifact_id="paper-result-summary",
        label="Paper result summary",
        description="Existing paper run result summary for review.",
    )

    assert isinstance(reference, PaperRunReference)
    assert reference.reference_type == "paper_result_summary"
    assert reference.reference == "outputs/run-1/paper/paper_run_result_summary.json"
    assert reference.run_id == "run-1"
    assert reference.artifact_id == "paper-result-summary"
    assert reference.label == "Paper result summary"
    assert reference.description == "Existing paper run result summary for review."


def test_supported_reference_types_are_explicit_and_deterministic() -> None:
    assert SUPPORTED_PAPER_RUN_REFERENCE_TYPES == (
        "paper_artifact",
        "paper_result_summary",
    )


def test_invalid_reference_type_raises_value_error() -> None:
    with pytest.raises(ValueError, match="unsupported reference_type"):
        create_paper_run_reference(
            reference_type="metrics",
            reference="outputs/run-1/paper/metrics.json",
        )


def test_invalid_reference_type_message_includes_supported_type() -> None:
    with pytest.raises(ValueError, match="paper_result_summary"):
        create_paper_run_reference(
            reference_type="unknown",
            reference="outputs/run-1/paper/paper_run_result_summary.json",
        )


@pytest.mark.parametrize("reference", ["", "   "])
def test_blank_required_reference_raises_value_error(reference: str) -> None:
    with pytest.raises(ValueError, match="reference"):
        create_paper_run_reference(
            reference_type="paper_artifact",
            reference=reference,
        )


def test_required_fields_strip_whitespace() -> None:
    reference = create_paper_run_reference(
        reference_type=" paper_artifact ",
        reference=" outputs/run-1/paper/paper_run_artifact.json ",
    )

    assert reference.reference_type == "paper_artifact"
    assert reference.reference == "outputs/run-1/paper/paper_run_artifact.json"


def test_optional_field_normalization() -> None:
    reference = create_paper_run_reference(
        reference_type="paper_artifact",
        reference="paper/paper_run_artifact.json",
        run_id=" run-1 ",
        artifact_id=" paper-artifact ",
        label="  ",
        description=" Existing paper artifact. ",
    )

    assert reference.run_id == "run-1"
    assert reference.artifact_id == "paper-artifact"
    assert reference.label is None
    assert reference.description == "Existing paper artifact."


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("run_id", {"run_id": object()}),
        ("artifact_id", {"artifact_id": object()}),
        ("label", {"label": object()}),
        ("description", {"description": object()}),
    ],
)
def test_invalid_optional_field_types_raise_value_error(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match=field_name):
        create_paper_run_reference(
            reference_type="paper_artifact",
            reference="paper/paper_run_artifact.json",
            **kwargs,  # type: ignore[arg-type]
        )


def test_to_dict_is_deterministic_and_json_compatible() -> None:
    reference = create_paper_run_reference(
        reference_type="paper_result_summary",
        reference="outputs/run-1/paper/paper_run_result_summary.json",
        run_id="run-1",
        artifact_id="paper-result-summary",
        label="Paper result summary",
        description=None,
    )

    expected = {
        "schema_version": PAPER_RUN_REFERENCE_SCHEMA_VERSION,
        "reference_type": "paper_result_summary",
        "reference": "outputs/run-1/paper/paper_run_result_summary.json",
        "run_id": "run-1",
        "artifact_id": "paper-result-summary",
        "label": "Paper result summary",
        "description": None,
    }
    assert reference.to_dict() == expected
    assert reference.to_dict() == expected
    json.dumps(reference.to_dict(), allow_nan=False)


def test_schema_version_is_json_compatible() -> None:
    assert PAPER_RUN_REFERENCE_SCHEMA_VERSION == 1
    json.dumps(
        {"schema_version": PAPER_RUN_REFERENCE_SCHEMA_VERSION},
        allow_nan=False,
    )


def test_paper_run_reference_is_immutable() -> None:
    reference = create_paper_run_reference(
        reference_type="paper_artifact",
        reference="paper/paper_run_artifact.json",
    )

    with pytest.raises(FrozenInstanceError):
        reference.reference = "other"  # type: ignore[misc]


def test_paper_review_package_exports_public_api() -> None:
    from el_psy_quant import paper_review

    assert (
        paper_review.PAPER_RUN_REFERENCE_SCHEMA_VERSION
        == PAPER_RUN_REFERENCE_SCHEMA_VERSION
    )
    assert (
        paper_review.SUPPORTED_PAPER_RUN_REFERENCE_TYPES
        is SUPPORTED_PAPER_RUN_REFERENCE_TYPES
    )
    assert paper_review.PaperRunReference is PaperRunReference
    assert paper_review.create_paper_run_reference is create_paper_run_reference


def test_reference_module_does_not_expose_forbidden_runtime_behavior() -> None:
    from el_psy_quant import paper_review

    forbidden_names = {
        "load_paper_run_artifact",
        "read_paper_run_artifact",
        "write_paper_run_artifact",
        "run_paper_workflow",
        "persist_paper_run",
        "compare_paper_run_metrics",
        "render_paper_run_report",
        "create_dashboard",
    }

    for forbidden_name in forbidden_names:
        assert not hasattr(paper_review, forbidden_name)
