"""Tests for paper run comparison inputs."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.paper_review import (
    PAPER_RUN_COMPARISON_INPUT_SCHEMA_VERSION,
    PaperRunComparisonInput,
    PaperRunReference,
    create_paper_run_comparison_input,
    create_paper_run_reference,
)


def _paper_run_reference(
    run_id: str = "run-1",
    reference_type: str = "paper_result_summary",
) -> PaperRunReference:
    suffix = (
        "paper_run_result_summary.json"
        if reference_type == "paper_result_summary"
        else "paper_run_artifact.json"
    )
    return create_paper_run_reference(
        reference_type=reference_type,
        reference=f"outputs/{run_id}/paper/{suffix}",
        run_id=run_id,
        artifact_id=reference_type,
        label=f"{run_id} {reference_type}",
    )


def test_valid_comparison_input_creation() -> None:
    reference = _paper_run_reference()

    comparison_input = create_paper_run_comparison_input(
        comparison_id="comparison-1",
        paper_run_references=[reference],
        purpose="Compare paper result summaries for manual review.",
    )

    assert isinstance(comparison_input, PaperRunComparisonInput)
    assert comparison_input.comparison_id == "comparison-1"
    assert comparison_input.paper_run_references == (reference,)
    assert comparison_input.purpose == "Compare paper result summaries for manual review."
    assert comparison_input.review_context is None
    assert comparison_input.requested_by is None
    assert comparison_input.created_timestamp is None


@pytest.mark.parametrize("comparison_id", ["", "   "])
def test_comparison_id_validation(comparison_id: str) -> None:
    with pytest.raises(ValueError, match="comparison_id"):
        create_paper_run_comparison_input(
            comparison_id=comparison_id,
            paper_run_references=[_paper_run_reference()],
            purpose="Manual comparison.",
        )


@pytest.mark.parametrize("purpose", ["", "   "])
def test_purpose_validation(purpose: str) -> None:
    with pytest.raises(ValueError, match="purpose"):
        create_paper_run_comparison_input(
            comparison_id="comparison-1",
            paper_run_references=[_paper_run_reference()],
            purpose=purpose,
        )


def test_required_fields_strip_whitespace() -> None:
    comparison_input = create_paper_run_comparison_input(
        comparison_id=" comparison-1 ",
        paper_run_references=[_paper_run_reference()],
        purpose=" Manual comparison. ",
    )

    assert comparison_input.comparison_id == "comparison-1"
    assert comparison_input.purpose == "Manual comparison."


def test_paper_run_references_normalize_to_immutable_tuple() -> None:
    first = _paper_run_reference("run-1")
    second = _paper_run_reference("run-2", "paper_artifact")
    references = [first, second]

    comparison_input = create_paper_run_comparison_input(
        comparison_id="comparison-1",
        paper_run_references=references,
        purpose="Manual comparison.",
    )
    references.append(_paper_run_reference("run-3"))

    assert comparison_input.paper_run_references == (first, second)


def test_empty_paper_run_reference_sequence_raises_value_error() -> None:
    with pytest.raises(ValueError, match="paper_run_references"):
        create_paper_run_comparison_input(
            comparison_id="comparison-1",
            paper_run_references=[],
            purpose="Manual comparison.",
        )


def test_bare_paper_run_reference_raises_value_error() -> None:
    with pytest.raises(ValueError, match="paper_run_references"):
        create_paper_run_comparison_input(
            comparison_id="comparison-1",
            paper_run_references=_paper_run_reference(),  # type: ignore[arg-type]
            purpose="Manual comparison.",
        )


@pytest.mark.parametrize("paper_run_references", ["references", object()])
def test_invalid_paper_run_reference_sequence_raises_value_error(
    paper_run_references: object,
) -> None:
    with pytest.raises(ValueError, match="paper_run_references"):
        create_paper_run_comparison_input(
            comparison_id="comparison-1",
            paper_run_references=paper_run_references,  # type: ignore[arg-type]
            purpose="Manual comparison.",
        )


def test_invalid_paper_run_reference_element_raises_value_error() -> None:
    with pytest.raises(ValueError, match="PaperRunReference"):
        create_paper_run_comparison_input(
            comparison_id="comparison-1",
            paper_run_references=[_paper_run_reference(), object()],  # type: ignore[list-item]
            purpose="Manual comparison.",
        )


def test_optional_field_normalization() -> None:
    comparison_input = create_paper_run_comparison_input(
        comparison_id="comparison-1",
        paper_run_references=[_paper_run_reference()],
        purpose="Manual comparison.",
        review_context="  ",
        requested_by=" reviewer-1 ",
    )

    assert comparison_input.review_context is None
    assert comparison_input.requested_by == "reviewer-1"


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("review_context", {"review_context": object()}),
        ("requested_by", {"requested_by": object()}),
    ],
)
def test_invalid_optional_field_types_raise_value_error(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match=field_name):
        create_paper_run_comparison_input(
            comparison_id="comparison-1",
            paper_run_references=[_paper_run_reference()],
            purpose="Manual comparison.",
            **kwargs,  # type: ignore[arg-type]
        )


def test_timestamp_normalizes_to_deterministic_export() -> None:
    comparison_input = create_paper_run_comparison_input(
        comparison_id="comparison-1",
        paper_run_references=[_paper_run_reference()],
        purpose="Manual comparison.",
        created_timestamp="2026-01-02T03:04:05",
    )

    assert comparison_input.to_dict()["created_timestamp"] == "2026-01-02T03:04:05"


def test_invalid_timestamp_raises_value_error() -> None:
    with pytest.raises(ValueError, match="created_timestamp"):
        create_paper_run_comparison_input(
            comparison_id="comparison-1",
            paper_run_references=[_paper_run_reference()],
            purpose="Manual comparison.",
            created_timestamp="not-a-timestamp",
        )


def test_to_dict_is_deterministic_and_json_compatible() -> None:
    first = _paper_run_reference("run-1")
    second = _paper_run_reference("run-2", "paper_artifact")
    comparison_input = create_paper_run_comparison_input(
        comparison_id="comparison-1",
        paper_run_references=[first, second],
        purpose="Compare completed paper runs for manual review.",
        review_context="Milestone 21 review",
        requested_by="reviewer-1",
        created_timestamp="2026-01-02T03:04:05",
    )

    expected = {
        "schema_version": PAPER_RUN_COMPARISON_INPUT_SCHEMA_VERSION,
        "comparison_id": "comparison-1",
        "paper_run_references": [first.to_dict(), second.to_dict()],
        "purpose": "Compare completed paper runs for manual review.",
        "review_context": "Milestone 21 review",
        "requested_by": "reviewer-1",
        "created_timestamp": "2026-01-02T03:04:05",
    }

    assert comparison_input.to_dict() == expected
    assert comparison_input.to_dict() == expected
    json.dumps(comparison_input.to_dict(), allow_nan=False)


def test_schema_version_is_json_compatible() -> None:
    assert PAPER_RUN_COMPARISON_INPUT_SCHEMA_VERSION == 1
    json.dumps(
        {"schema_version": PAPER_RUN_COMPARISON_INPUT_SCHEMA_VERSION},
        allow_nan=False,
    )


def test_paper_run_comparison_input_is_immutable() -> None:
    comparison_input = create_paper_run_comparison_input(
        comparison_id="comparison-1",
        paper_run_references=[_paper_run_reference()],
        purpose="Manual comparison.",
    )

    with pytest.raises(FrozenInstanceError):
        comparison_input.purpose = "Other"  # type: ignore[misc]


def test_paper_review_package_exports_comparison_input_public_api() -> None:
    from el_psy_quant import paper_review

    assert (
        paper_review.PAPER_RUN_COMPARISON_INPUT_SCHEMA_VERSION
        == PAPER_RUN_COMPARISON_INPUT_SCHEMA_VERSION
    )
    assert paper_review.PaperRunComparisonInput is PaperRunComparisonInput
    assert (
        paper_review.create_paper_run_comparison_input
        is create_paper_run_comparison_input
    )


def test_paper_review_package_does_not_expose_forbidden_runtime_behavior() -> None:
    from el_psy_quant import paper_review

    forbidden_names = {
        "discover_paper_runs",
        "load_paper_run_artifact",
        "read_paper_run_artifact",
        "write_paper_run_artifact",
        "compare_paper_run_metrics",
        "score_paper_runs",
        "create_paper_run_comparison_summary",
        "create_paper_run_review_decision",
        "render_paper_run_report",
        "create_dashboard",
        "run_paper_workflow",
    }

    for forbidden_name in forbidden_names:
        assert not hasattr(paper_review, forbidden_name)
