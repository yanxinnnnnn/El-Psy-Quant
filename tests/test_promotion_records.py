"""Tests for explicit promotion records."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.promotion import (
    PROMOTION_RECORD_SCHEMA_VERSION,
    PROMOTION_RECORD_STATUSES,
    PromotionEvidenceSummary,
    PromotionRecord,
    create_paper_promotion_candidate,
    create_promotion_evidence_summary,
    create_promotion_record,
    create_promotion_source_reference,
)


def _evidence_summary() -> PromotionEvidenceSummary:
    source_reference = create_promotion_source_reference(
        source_type="configured_run",
        reference="outputs/run-1",
        run_id="run-1",
        artifact_id="manifest",
        label="Configured run",
    )
    candidate = create_paper_promotion_candidate(
        candidate_id="candidate-1",
        source_references=[source_reference],
        title="Review moving-average candidate",
    )
    return create_promotion_evidence_summary(
        candidate=candidate,
        source_facts=["Summary row exists"],
        assumptions=["Manual review is required"],
        warnings=["Not a live-readiness claim"],
    )


@pytest.mark.parametrize("status", PROMOTION_RECORD_STATUSES)
def test_valid_promotion_record_creation_for_each_status(status: str) -> None:
    evidence_summary = _evidence_summary()

    record = create_promotion_record(
        record_id="record-1",
        evidence_summary=evidence_summary,
        status=status,
        rationale="Reviewed for paper-trading consideration only.",
    )

    assert isinstance(record, PromotionRecord)
    assert record.record_id == "record-1"
    assert record.evidence_summary is evidence_summary
    assert record.status == status
    assert record.rationale == "Reviewed for paper-trading consideration only."
    assert record.reviewer is None
    assert record.created_timestamp is None


def test_allowed_statuses_are_explicit_and_deterministic() -> None:
    assert PROMOTION_RECORD_STATUSES == (
        "proposed",
        "approved_for_paper",
        "rejected",
        "deferred",
    )


@pytest.mark.parametrize("record_id", ["", "   "])
def test_record_id_validation(record_id: str) -> None:
    with pytest.raises(ValueError, match="record_id"):
        create_promotion_record(
            record_id=record_id,
            evidence_summary=_evidence_summary(),
            status="proposed",
            rationale="Manual review rationale.",
        )


def test_evidence_summary_validation() -> None:
    with pytest.raises(ValueError, match="PromotionEvidenceSummary"):
        create_promotion_record(
            record_id="record-1",
            evidence_summary=object(),  # type: ignore[arg-type]
            status="proposed",
            rationale="Manual review rationale.",
        )


def test_status_validation() -> None:
    with pytest.raises(ValueError, match="unsupported promotion status"):
        create_promotion_record(
            record_id="record-1",
            evidence_summary=_evidence_summary(),
            status="approved_for_live",
            rationale="Manual review rationale.",
        )


def test_status_validation_message_includes_supported_status() -> None:
    with pytest.raises(ValueError, match="approved_for_paper"):
        create_promotion_record(
            record_id="record-1",
            evidence_summary=_evidence_summary(),
            status="unknown",
            rationale="Manual review rationale.",
        )


@pytest.mark.parametrize("rationale", ["", "   "])
def test_rationale_validation(rationale: str) -> None:
    with pytest.raises(ValueError, match="rationale"):
        create_promotion_record(
            record_id="record-1",
            evidence_summary=_evidence_summary(),
            status="proposed",
            rationale=rationale,
        )


def test_required_string_fields_strip_whitespace() -> None:
    record = create_promotion_record(
        record_id=" record-1 ",
        evidence_summary=_evidence_summary(),
        status=" proposed ",
        rationale=" Manual review rationale. ",
    )

    assert record.record_id == "record-1"
    assert record.status == "proposed"
    assert record.rationale == "Manual review rationale."


def test_optional_reviewer_normalization() -> None:
    record = create_promotion_record(
        record_id="record-1",
        evidence_summary=_evidence_summary(),
        status="deferred",
        rationale="Needs another review.",
        reviewer="  ",
    )
    reviewed_record = create_promotion_record(
        record_id="record-2",
        evidence_summary=_evidence_summary(),
        status="approved_for_paper",
        rationale="Approved for paper review only.",
        reviewer=" reviewer-1 ",
    )

    assert record.reviewer is None
    assert reviewed_record.reviewer == "reviewer-1"


def test_invalid_reviewer_type_raises_value_error() -> None:
    with pytest.raises(ValueError, match="reviewer"):
        create_promotion_record(
            record_id="record-1",
            evidence_summary=_evidence_summary(),
            status="proposed",
            rationale="Manual review rationale.",
            reviewer=object(),  # type: ignore[arg-type]
        )


def test_timestamp_normalizes_to_deterministic_export() -> None:
    record = create_promotion_record(
        record_id="record-1",
        evidence_summary=_evidence_summary(),
        status="proposed",
        rationale="Manual review rationale.",
        created_timestamp="2026-01-02T03:04:05",
    )

    assert record.to_dict()["created_timestamp"] == "2026-01-02T03:04:05"


def test_invalid_timestamp_raises_value_error() -> None:
    with pytest.raises(ValueError, match="created_timestamp"):
        create_promotion_record(
            record_id="record-1",
            evidence_summary=_evidence_summary(),
            status="proposed",
            rationale="Manual review rationale.",
            created_timestamp="not-a-timestamp",
        )


def test_to_dict_is_deterministic_and_json_compatible() -> None:
    evidence_summary = _evidence_summary()
    record = create_promotion_record(
        record_id="record-1",
        evidence_summary=evidence_summary,
        status="approved_for_paper",
        rationale="Approved for paper-trading review only.",
        reviewer="reviewer-1",
        created_timestamp="2026-01-02T03:04:05",
    )

    expected = {
        "schema_version": PROMOTION_RECORD_SCHEMA_VERSION,
        "record_id": "record-1",
        "evidence_summary": evidence_summary.to_dict(),
        "status": "approved_for_paper",
        "rationale": "Approved for paper-trading review only.",
        "reviewer": "reviewer-1",
        "created_timestamp": "2026-01-02T03:04:05",
    }

    assert record.to_dict() == expected
    assert record.to_dict() == expected
    json.dumps(record.to_dict(), allow_nan=False)


def test_schema_version_is_json_compatible() -> None:
    assert PROMOTION_RECORD_SCHEMA_VERSION == 1
    json.dumps(
        {"schema_version": PROMOTION_RECORD_SCHEMA_VERSION},
        allow_nan=False,
    )


def test_promotion_record_is_immutable() -> None:
    record = create_promotion_record(
        record_id="record-1",
        evidence_summary=_evidence_summary(),
        status="proposed",
        rationale="Manual review rationale.",
    )

    with pytest.raises(FrozenInstanceError):
        record.status = "rejected"  # type: ignore[misc]


def test_promotion_package_exports_record_public_api() -> None:
    from el_psy_quant import promotion

    assert promotion.PROMOTION_RECORD_SCHEMA_VERSION == PROMOTION_RECORD_SCHEMA_VERSION
    assert promotion.PROMOTION_RECORD_STATUSES is PROMOTION_RECORD_STATUSES
    assert promotion.PromotionRecord is PromotionRecord
    assert promotion.create_promotion_record is create_promotion_record
