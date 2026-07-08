"""Tests for paper promotion candidates."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.promotion import (
    PAPER_PROMOTION_CANDIDATE_SCHEMA_VERSION,
    PaperPromotionCandidate,
    PromotionSourceReference,
    create_paper_promotion_candidate,
    create_promotion_source_reference,
)


def _source_reference(reference: str = "outputs/run-1") -> PromotionSourceReference:
    return create_promotion_source_reference(
        source_type="configured_run",
        reference=reference,
        run_id="run-1",
        artifact_id="manifest",
        label="Configured run",
    )


def test_valid_candidate_creation_with_one_source_reference() -> None:
    source_reference = _source_reference()

    candidate = create_paper_promotion_candidate(
        candidate_id="candidate-1",
        source_references=[source_reference],
        title="Review moving-average candidate",
    )

    assert isinstance(candidate, PaperPromotionCandidate)
    assert candidate.candidate_id == "candidate-1"
    assert candidate.title == "Review moving-average candidate"
    assert candidate.source_references == (source_reference,)
    assert candidate.rationale is None
    assert candidate.proposed_by is None
    assert candidate.created_timestamp is None


def test_valid_candidate_creation_with_multiple_source_references() -> None:
    first = _source_reference("outputs/run-1")
    second = create_promotion_source_reference(
        source_type="paper_result_summary",
        reference="outputs/run-1/paper/paper_run_result_summary.json",
        run_id="run-1",
    )

    candidate = create_paper_promotion_candidate(
        candidate_id="candidate-1",
        source_references=(first, second),
        title="Review paired evidence",
    )

    assert candidate.source_references == (first, second)


@pytest.mark.parametrize("candidate_id", ["", "   "])
def test_candidate_id_validation(candidate_id: str) -> None:
    with pytest.raises(ValueError, match="candidate_id"):
        create_paper_promotion_candidate(
            candidate_id=candidate_id,
            source_references=[_source_reference()],
            title="Candidate",
        )


@pytest.mark.parametrize("title", ["", "   "])
def test_title_validation(title: str) -> None:
    with pytest.raises(ValueError, match="title"):
        create_paper_promotion_candidate(
            candidate_id="candidate-1",
            source_references=[_source_reference()],
            title=title,
        )


def test_source_references_must_be_non_empty_sequence() -> None:
    with pytest.raises(ValueError, match="source_references"):
        create_paper_promotion_candidate(
            candidate_id="candidate-1",
            source_references=[],
            title="Candidate",
        )


def test_single_source_reference_object_is_rejected_as_sequence() -> None:
    with pytest.raises(ValueError, match="source_references"):
        create_paper_promotion_candidate(
            candidate_id="candidate-1",
            source_references=_source_reference(),  # type: ignore[arg-type]
            title="Candidate",
        )


def test_non_sequence_source_references_raise_value_error() -> None:
    with pytest.raises(ValueError, match="source_references"):
        create_paper_promotion_candidate(
            candidate_id="candidate-1",
            source_references=object(),  # type: ignore[arg-type]
            title="Candidate",
        )


def test_invalid_source_reference_item_raises_value_error() -> None:
    with pytest.raises(ValueError, match="PromotionSourceReference"):
        create_paper_promotion_candidate(
            candidate_id="candidate-1",
            source_references=[_source_reference(), object()],  # type: ignore[list-item]
            title="Candidate",
        )


def test_optional_field_normalization() -> None:
    candidate = create_paper_promotion_candidate(
        candidate_id=" candidate-1 ",
        source_references=[_source_reference()],
        title=" Candidate title ",
        rationale="  ",
        proposed_by=" research-reviewer ",
    )

    assert candidate.candidate_id == "candidate-1"
    assert candidate.title == "Candidate title"
    assert candidate.rationale is None
    assert candidate.proposed_by == "research-reviewer"


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("rationale", {"rationale": object()}),
        ("proposed_by", {"proposed_by": object()}),
    ],
)
def test_invalid_optional_string_fields_raise_value_error(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match=field_name):
        create_paper_promotion_candidate(
            candidate_id="candidate-1",
            source_references=[_source_reference()],
            title="Candidate",
            **kwargs,  # type: ignore[arg-type]
        )


def test_timestamp_normalizes_to_deterministic_export() -> None:
    candidate = create_paper_promotion_candidate(
        candidate_id="candidate-1",
        source_references=[_source_reference()],
        title="Candidate",
        created_timestamp="2026-01-02T03:04:05",
    )

    assert candidate.to_dict()["created_timestamp"] == "2026-01-02T03:04:05"


def test_invalid_timestamp_raises_value_error() -> None:
    with pytest.raises(ValueError, match="created_timestamp"):
        create_paper_promotion_candidate(
            candidate_id="candidate-1",
            source_references=[_source_reference()],
            title="Candidate",
            created_timestamp="not-a-timestamp",
        )


def test_to_dict_is_deterministic_and_json_compatible() -> None:
    source_reference = _source_reference()
    candidate = create_paper_promotion_candidate(
        candidate_id="candidate-1",
        source_references=[source_reference],
        title="Review moving-average candidate",
        rationale="Stable research and paper evidence.",
        proposed_by="analyst",
        created_timestamp="2026-01-02T03:04:05",
    )

    expected = {
        "schema_version": PAPER_PROMOTION_CANDIDATE_SCHEMA_VERSION,
        "candidate_id": "candidate-1",
        "title": "Review moving-average candidate",
        "rationale": "Stable research and paper evidence.",
        "proposed_by": "analyst",
        "created_timestamp": "2026-01-02T03:04:05",
        "source_references": [source_reference.to_dict()],
    }

    assert candidate.to_dict() == expected
    assert candidate.to_dict() == expected
    json.dumps(candidate.to_dict(), allow_nan=False)


def test_schema_version_is_json_compatible() -> None:
    assert PAPER_PROMOTION_CANDIDATE_SCHEMA_VERSION == 1
    json.dumps(
        {"schema_version": PAPER_PROMOTION_CANDIDATE_SCHEMA_VERSION},
        allow_nan=False,
    )


def test_candidate_is_immutable() -> None:
    candidate = create_paper_promotion_candidate(
        candidate_id="candidate-1",
        source_references=[_source_reference()],
        title="Candidate",
    )

    with pytest.raises(FrozenInstanceError):
        candidate.title = "Other"  # type: ignore[misc]


def test_candidate_does_not_mutate_source_reference_sequence() -> None:
    source_reference = _source_reference()
    source_references = [source_reference]

    candidate = create_paper_promotion_candidate(
        candidate_id="candidate-1",
        source_references=source_references,
        title="Candidate",
    )
    source_references.append(_source_reference("outputs/run-2"))

    assert candidate.source_references == (source_reference,)


def test_promotion_package_exports_candidate_public_api() -> None:
    from el_psy_quant import promotion

    assert (
        promotion.PAPER_PROMOTION_CANDIDATE_SCHEMA_VERSION
        == PAPER_PROMOTION_CANDIDATE_SCHEMA_VERSION
    )
    assert promotion.PaperPromotionCandidate is PaperPromotionCandidate
    assert (
        promotion.create_paper_promotion_candidate
        is create_paper_promotion_candidate
    )
