"""Tests for promotion evidence summaries."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.promotion import (
    PROMOTION_EVIDENCE_SUMMARY_SCHEMA_VERSION,
    PaperPromotionCandidate,
    PromotionEvidenceSummary,
    create_paper_promotion_candidate,
    create_promotion_evidence_summary,
    create_promotion_source_reference,
)


def _candidate() -> PaperPromotionCandidate:
    source_reference = create_promotion_source_reference(
        source_type="configured_run",
        reference="outputs/run-1",
        run_id="run-1",
        artifact_id="manifest",
        label="Configured run",
    )
    return create_paper_promotion_candidate(
        candidate_id="candidate-1",
        source_references=[source_reference],
        title="Review moving-average candidate",
    )


def test_valid_evidence_summary_creation() -> None:
    candidate = _candidate()

    summary = create_promotion_evidence_summary(
        candidate=candidate,
        source_facts=["Summary row exists", "Paper artifact is present"],
    )

    assert isinstance(summary, PromotionEvidenceSummary)
    assert summary.candidate is candidate
    assert summary.source_facts == (
        "Summary row exists",
        "Paper artifact is present",
    )
    assert summary.assumptions == ()
    assert summary.warnings == ()
    assert summary.missing_evidence == ()
    assert summary.created_timestamp is None


def test_optional_sequence_fields_normalize_to_tuples() -> None:
    summary = create_promotion_evidence_summary(
        candidate=_candidate(),
        source_facts=[" fact "],
        assumptions=[" assumption "],
        warnings=[" warning "],
        missing_evidence=[" missing evidence "],
    )

    assert summary.source_facts == ("fact",)
    assert summary.assumptions == ("assumption",)
    assert summary.warnings == ("warning",)
    assert summary.missing_evidence == ("missing evidence",)


def test_empty_optional_sequence_fields_normalize_to_empty_tuples() -> None:
    summary = create_promotion_evidence_summary(
        candidate=_candidate(),
        source_facts=["fact"],
        assumptions=[],
        warnings=[],
        missing_evidence=[],
    )

    assert summary.assumptions == ()
    assert summary.warnings == ()
    assert summary.missing_evidence == ()


def test_candidate_validation() -> None:
    with pytest.raises(ValueError, match="PaperPromotionCandidate"):
        create_promotion_evidence_summary(
            candidate=object(),  # type: ignore[arg-type]
            source_facts=["fact"],
        )


def test_source_facts_must_not_be_empty() -> None:
    with pytest.raises(ValueError, match="source_facts"):
        create_promotion_evidence_summary(
            candidate=_candidate(),
            source_facts=[],
        )


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("source_facts", {"source_facts": "fact"}),
        ("assumptions", {"assumptions": "assumption"}),
        ("warnings", {"warnings": "warning"}),
        ("missing_evidence", {"missing_evidence": "missing"}),
    ],
)
def test_raw_string_sequence_fields_raise_value_error(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "candidate": _candidate(),
        "source_facts": ["fact"],
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_promotion_evidence_summary(**arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("source_facts", {"source_facts": object()}),
        ("assumptions", {"assumptions": object()}),
        ("warnings", {"warnings": object()}),
        ("missing_evidence", {"missing_evidence": object()}),
    ],
)
def test_non_sequence_fields_raise_value_error(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "candidate": _candidate(),
        "source_facts": ["fact"],
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_promotion_evidence_summary(**arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("source_facts", {"source_facts": [""]}),
        ("source_facts", {"source_facts": ["  "]}),
        ("source_facts", {"source_facts": [object()]}),
        ("assumptions", {"assumptions": [""]}),
        ("warnings", {"warnings": ["  "]}),
        ("missing_evidence", {"missing_evidence": [object()]}),
    ],
)
def test_invalid_sequence_items_raise_value_error(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "candidate": _candidate(),
        "source_facts": ["fact"],
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_promotion_evidence_summary(**arguments)  # type: ignore[arg-type]


def test_timestamp_normalizes_to_deterministic_export() -> None:
    summary = create_promotion_evidence_summary(
        candidate=_candidate(),
        source_facts=["fact"],
        created_timestamp="2026-01-02T03:04:05",
    )

    assert summary.to_dict()["created_timestamp"] == "2026-01-02T03:04:05"


def test_invalid_timestamp_raises_value_error() -> None:
    with pytest.raises(ValueError, match="created_timestamp"):
        create_promotion_evidence_summary(
            candidate=_candidate(),
            source_facts=["fact"],
            created_timestamp="not-a-timestamp",
        )


def test_to_dict_is_deterministic_and_json_compatible() -> None:
    candidate = _candidate()
    summary = create_promotion_evidence_summary(
        candidate=candidate,
        source_facts=["Summary row exists", "Paper artifact is present"],
        assumptions=["Costs are already represented in source results"],
        warnings=["Manual review still required"],
        missing_evidence=["No live-readiness review"],
        created_timestamp="2026-01-02T03:04:05",
    )

    expected = {
        "schema_version": PROMOTION_EVIDENCE_SUMMARY_SCHEMA_VERSION,
        "candidate": candidate.to_dict(),
        "source_facts": [
            "Summary row exists",
            "Paper artifact is present",
        ],
        "assumptions": ["Costs are already represented in source results"],
        "warnings": ["Manual review still required"],
        "missing_evidence": ["No live-readiness review"],
        "created_timestamp": "2026-01-02T03:04:05",
    }

    assert summary.to_dict() == expected
    assert summary.to_dict() == expected
    json.dumps(summary.to_dict(), allow_nan=False)


def test_schema_version_is_json_compatible() -> None:
    assert PROMOTION_EVIDENCE_SUMMARY_SCHEMA_VERSION == 1
    json.dumps(
        {"schema_version": PROMOTION_EVIDENCE_SUMMARY_SCHEMA_VERSION},
        allow_nan=False,
    )


def test_evidence_summary_is_immutable() -> None:
    summary = create_promotion_evidence_summary(
        candidate=_candidate(),
        source_facts=["fact"],
    )

    with pytest.raises(FrozenInstanceError):
        summary.source_facts = ("other",)  # type: ignore[misc]


def test_evidence_summary_does_not_mutate_input_sequences() -> None:
    source_facts = ["fact"]
    assumptions = ["assumption"]

    summary = create_promotion_evidence_summary(
        candidate=_candidate(),
        source_facts=source_facts,
        assumptions=assumptions,
    )
    source_facts.append("new fact")
    assumptions.append("new assumption")

    assert summary.source_facts == ("fact",)
    assert summary.assumptions == ("assumption",)


def test_promotion_package_exports_evidence_public_api() -> None:
    from el_psy_quant import promotion

    assert (
        promotion.PROMOTION_EVIDENCE_SUMMARY_SCHEMA_VERSION
        == PROMOTION_EVIDENCE_SUMMARY_SCHEMA_VERSION
    )
    assert promotion.PromotionEvidenceSummary is PromotionEvidenceSummary
    assert (
        promotion.create_promotion_evidence_summary
        is create_promotion_evidence_summary
    )
