"""Tests for paper run comparison summaries."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.paper_review import (
    PAPER_RUN_COMPARISON_SUMMARY_SCHEMA_VERSION,
    PaperRunComparisonInput,
    PaperRunComparisonSummary,
    create_paper_run_comparison_input,
    create_paper_run_comparison_summary,
    create_paper_run_reference,
)


def _comparison_input() -> PaperRunComparisonInput:
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
    return create_paper_run_comparison_input(
        comparison_id="comparison-1",
        paper_run_references=[first, second],
        purpose="Compare paper runs for manual review.",
    )


def test_valid_comparison_summary_creation() -> None:
    comparison_input = _comparison_input()

    summary = create_paper_run_comparison_summary(
        summary_id="summary-1",
        comparison_input=comparison_input,
        comparison_facts=[
            "Run 1 and Run 2 were supplied explicitly.",
            "Run 1 has result-summary reference metadata.",
        ],
    )

    assert isinstance(summary, PaperRunComparisonSummary)
    assert summary.summary_id == "summary-1"
    assert summary.comparison_input is comparison_input
    assert summary.comparison_facts == (
        "Run 1 and Run 2 were supplied explicitly.",
        "Run 1 has result-summary reference metadata.",
    )
    assert summary.assumptions == ()
    assert summary.warnings == ()
    assert summary.missing_evidence == ()
    assert summary.created_by is None
    assert summary.created_timestamp is None


@pytest.mark.parametrize("summary_id", ["", "   "])
def test_summary_id_validation(summary_id: str) -> None:
    with pytest.raises(ValueError, match="summary_id"):
        create_paper_run_comparison_summary(
            summary_id=summary_id,
            comparison_input=_comparison_input(),
            comparison_facts=["fact"],
        )


def test_summary_id_trimming() -> None:
    summary = create_paper_run_comparison_summary(
        summary_id=" summary-1 ",
        comparison_input=_comparison_input(),
        comparison_facts=["fact"],
    )

    assert summary.summary_id == "summary-1"


def test_comparison_input_type_validation() -> None:
    with pytest.raises(ValueError, match="PaperRunComparisonInput"):
        create_paper_run_comparison_summary(
            summary_id="summary-1",
            comparison_input=object(),  # type: ignore[arg-type]
            comparison_facts=["fact"],
        )


def test_comparison_facts_must_not_be_empty() -> None:
    with pytest.raises(ValueError, match="comparison_facts"):
        create_paper_run_comparison_summary(
            summary_id="summary-1",
            comparison_input=_comparison_input(),
            comparison_facts=[],
        )


def test_sequence_fields_normalize_to_immutable_tuples() -> None:
    comparison_facts = [" fact "]
    assumptions = [" assumption "]
    warnings = [" warning "]
    missing_evidence = [" missing evidence "]

    summary = create_paper_run_comparison_summary(
        summary_id="summary-1",
        comparison_input=_comparison_input(),
        comparison_facts=comparison_facts,
        assumptions=assumptions,
        warnings=warnings,
        missing_evidence=missing_evidence,
    )
    comparison_facts.append("new fact")
    assumptions.append("new assumption")
    warnings.append("new warning")
    missing_evidence.append("new missing evidence")

    assert summary.comparison_facts == ("fact",)
    assert summary.assumptions == ("assumption",)
    assert summary.warnings == ("warning",)
    assert summary.missing_evidence == ("missing evidence",)


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("comparison_facts", {"comparison_facts": "fact"}),
        ("assumptions", {"assumptions": "assumption"}),
        ("warnings", {"warnings": "warning"}),
        ("missing_evidence", {"missing_evidence": "missing"}),
    ],
)
def test_bare_strings_rejected_for_sequence_fields(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "summary_id": "summary-1",
        "comparison_input": _comparison_input(),
        "comparison_facts": ["fact"],
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_paper_run_comparison_summary(**arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("comparison_facts", {"comparison_facts": [""]}),
        ("comparison_facts", {"comparison_facts": ["  "]}),
        ("comparison_facts", {"comparison_facts": [object()]}),
        ("assumptions", {"assumptions": [""]}),
        ("warnings", {"warnings": ["  "]}),
        ("missing_evidence", {"missing_evidence": [object()]}),
    ],
)
def test_invalid_sequence_elements_rejected(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "summary_id": "summary-1",
        "comparison_input": _comparison_input(),
        "comparison_facts": ["fact"],
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_paper_run_comparison_summary(**arguments)  # type: ignore[arg-type]


def test_optional_empty_sequences_allowed() -> None:
    summary = create_paper_run_comparison_summary(
        summary_id="summary-1",
        comparison_input=_comparison_input(),
        comparison_facts=["fact"],
        assumptions=[],
        warnings=[],
        missing_evidence=[],
    )

    assert summary.assumptions == ()
    assert summary.warnings == ()
    assert summary.missing_evidence == ()


def test_optional_created_by_normalization() -> None:
    summary = create_paper_run_comparison_summary(
        summary_id="summary-1",
        comparison_input=_comparison_input(),
        comparison_facts=["fact"],
        created_by="  ",
    )
    reviewed_summary = create_paper_run_comparison_summary(
        summary_id="summary-2",
        comparison_input=_comparison_input(),
        comparison_facts=["fact"],
        created_by=" reviewer-1 ",
    )

    assert summary.created_by is None
    assert reviewed_summary.created_by == "reviewer-1"


def test_invalid_created_by_type_raises_value_error() -> None:
    with pytest.raises(ValueError, match="created_by"):
        create_paper_run_comparison_summary(
            summary_id="summary-1",
            comparison_input=_comparison_input(),
            comparison_facts=["fact"],
            created_by=object(),  # type: ignore[arg-type]
        )


def test_timestamp_normalizes_to_deterministic_export() -> None:
    summary = create_paper_run_comparison_summary(
        summary_id="summary-1",
        comparison_input=_comparison_input(),
        comparison_facts=["fact"],
        created_timestamp="2026-01-02T03:04:05",
    )

    assert summary.to_dict()["created_timestamp"] == "2026-01-02T03:04:05"


def test_invalid_timestamp_raises_value_error() -> None:
    with pytest.raises(ValueError, match="created_timestamp"):
        create_paper_run_comparison_summary(
            summary_id="summary-1",
            comparison_input=_comparison_input(),
            comparison_facts=["fact"],
            created_timestamp="not-a-timestamp",
        )


def test_to_dict_is_deterministic_and_json_compatible() -> None:
    comparison_input = _comparison_input()
    summary = create_paper_run_comparison_summary(
        summary_id="summary-1",
        comparison_input=comparison_input,
        comparison_facts=[
            "Run 1 and Run 2 were supplied explicitly.",
            "Run 2 is missing reviewer-provided slippage context.",
        ],
        assumptions=["Facts are caller supplied."],
        warnings=["No scoring or ranking was performed."],
        missing_evidence=["No artifact parsing was performed."],
        created_by="reviewer-1",
        created_timestamp="2026-01-02T03:04:05",
    )

    expected = {
        "schema_version": PAPER_RUN_COMPARISON_SUMMARY_SCHEMA_VERSION,
        "summary_id": "summary-1",
        "comparison_input": comparison_input.to_dict(),
        "comparison_facts": [
            "Run 1 and Run 2 were supplied explicitly.",
            "Run 2 is missing reviewer-provided slippage context.",
        ],
        "assumptions": ["Facts are caller supplied."],
        "warnings": ["No scoring or ranking was performed."],
        "missing_evidence": ["No artifact parsing was performed."],
        "created_by": "reviewer-1",
        "created_timestamp": "2026-01-02T03:04:05",
    }

    assert summary.to_dict() == expected
    assert summary.to_dict() == expected
    json.dumps(summary.to_dict(), allow_nan=False)


def test_schema_version_is_json_compatible() -> None:
    assert PAPER_RUN_COMPARISON_SUMMARY_SCHEMA_VERSION == 1
    json.dumps(
        {"schema_version": PAPER_RUN_COMPARISON_SUMMARY_SCHEMA_VERSION},
        allow_nan=False,
    )


def test_paper_run_comparison_summary_is_immutable() -> None:
    summary = create_paper_run_comparison_summary(
        summary_id="summary-1",
        comparison_input=_comparison_input(),
        comparison_facts=["fact"],
    )

    with pytest.raises(FrozenInstanceError):
        summary.summary_id = "other"  # type: ignore[misc]


def test_paper_review_package_exports_summary_public_api() -> None:
    from el_psy_quant import paper_review

    assert (
        paper_review.PAPER_RUN_COMPARISON_SUMMARY_SCHEMA_VERSION
        == PAPER_RUN_COMPARISON_SUMMARY_SCHEMA_VERSION
    )
    assert paper_review.PaperRunComparisonSummary is PaperRunComparisonSummary
    assert (
        paper_review.create_paper_run_comparison_summary
        is create_paper_run_comparison_summary
    )


def test_paper_review_package_does_not_expose_forbidden_runtime_behavior() -> None:
    from el_psy_quant import paper_review

    forbidden_names = {
        "discover_paper_runs",
        "load_paper_run_artifact",
        "read_paper_run_artifact",
        "write_paper_run_artifact",
        "calculate_paper_run_metrics",
        "compare_paper_run_metrics",
        "score_paper_runs",
        "rank_paper_runs",
        "choose_winning_run",
        "create_paper_run_review_decision",
        "render_paper_run_report",
        "create_dashboard",
        "run_paper_workflow",
    }

    for forbidden_name in forbidden_names:
        assert not hasattr(paper_review, forbidden_name)
