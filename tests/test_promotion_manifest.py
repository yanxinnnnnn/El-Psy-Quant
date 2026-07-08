"""Tests for promotion candidate references and manifests."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.promotion import (
    PROMOTION_CANDIDATE_REFERENCE_SCHEMA_VERSION,
    PROMOTION_MANIFEST_SCHEMA_VERSION,
    PROMOTION_RECORD_STATUSES,
    PromotionCandidateReference,
    PromotionManifest,
    PromotionRecord,
    create_paper_promotion_candidate,
    create_promotion_candidate_reference,
    create_promotion_evidence_summary,
    create_promotion_manifest,
    create_promotion_record,
    create_promotion_source_reference,
)


def _promotion_record(
    record_id: str = "record-1",
    candidate_id: str = "candidate-1",
    status: str = "proposed",
) -> PromotionRecord:
    source_reference = create_promotion_source_reference(
        source_type="configured_run",
        reference=f"outputs/{candidate_id}",
        run_id=candidate_id,
        artifact_id="manifest",
        label="Configured run",
    )
    candidate = create_paper_promotion_candidate(
        candidate_id=candidate_id,
        source_references=[source_reference],
        title=f"Review {candidate_id}",
    )
    evidence_summary = create_promotion_evidence_summary(
        candidate=candidate,
        source_facts=["Summary row exists"],
        warnings=["Manual review only"],
    )
    return create_promotion_record(
        record_id=record_id,
        evidence_summary=evidence_summary,
        status=status,
        rationale="Manual promotion review rationale.",
    )


def _candidate_reference(
    record_id: str = "record-1",
    candidate_id: str = "candidate-1",
    status: str = "proposed",
) -> PromotionCandidateReference:
    return create_promotion_candidate_reference(
        record_id=record_id,
        candidate_id=candidate_id,
        status=status,
        reference=f"promotion/{record_id}.json",
        label="Candidate reference",
        description="Local logical reference only.",
    )


def test_valid_candidate_reference_creation() -> None:
    reference = create_promotion_candidate_reference(
        record_id="record-1",
        candidate_id="candidate-1",
        status="approved_for_paper",
        reference="promotion/record-1.json",
        label="Paper candidate",
        description="Ready for manual paper review.",
    )

    assert isinstance(reference, PromotionCandidateReference)
    assert reference.record_id == "record-1"
    assert reference.candidate_id == "candidate-1"
    assert reference.status == "approved_for_paper"
    assert reference.reference == "promotion/record-1.json"
    assert reference.label == "Paper candidate"
    assert reference.description == "Ready for manual paper review."


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("record_id", {"record_id": ""}),
        ("record_id", {"record_id": "  "}),
        ("candidate_id", {"candidate_id": ""}),
        ("candidate_id", {"candidate_id": "  "}),
    ],
)
def test_candidate_reference_required_field_validation(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "record_id": "record-1",
        "candidate_id": "candidate-1",
        "status": "proposed",
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_promotion_candidate_reference(**arguments)  # type: ignore[arg-type]


def test_candidate_reference_status_validation() -> None:
    with pytest.raises(ValueError, match="unsupported promotion status"):
        create_promotion_candidate_reference(
            record_id="record-1",
            candidate_id="candidate-1",
            status="approved_for_live",
        )


def test_candidate_reference_status_message_includes_supported_status() -> None:
    with pytest.raises(ValueError, match="approved_for_paper"):
        create_promotion_candidate_reference(
            record_id="record-1",
            candidate_id="candidate-1",
            status="unknown",
        )


def test_candidate_reference_optional_field_normalization() -> None:
    reference = create_promotion_candidate_reference(
        record_id=" record-1 ",
        candidate_id=" candidate-1 ",
        status=" proposed ",
        reference="  ",
        label=" Candidate ",
        description=" Local reference only. ",
    )

    assert reference.record_id == "record-1"
    assert reference.candidate_id == "candidate-1"
    assert reference.status == "proposed"
    assert reference.reference is None
    assert reference.label == "Candidate"
    assert reference.description == "Local reference only."


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("reference", {"reference": object()}),
        ("label", {"label": object()}),
        ("description", {"description": object()}),
    ],
)
def test_candidate_reference_invalid_optional_field_types_raise_value_error(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "record_id": "record-1",
        "candidate_id": "candidate-1",
        "status": "proposed",
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_promotion_candidate_reference(**arguments)  # type: ignore[arg-type]


def test_candidate_reference_to_dict_is_deterministic_and_json_compatible() -> None:
    reference = _candidate_reference()

    expected = {
        "schema_version": PROMOTION_CANDIDATE_REFERENCE_SCHEMA_VERSION,
        "record_id": "record-1",
        "candidate_id": "candidate-1",
        "status": "proposed",
        "reference": "promotion/record-1.json",
        "label": "Candidate reference",
        "description": "Local logical reference only.",
    }

    assert reference.to_dict() == expected
    assert reference.to_dict() == expected
    json.dumps(reference.to_dict(), allow_nan=False)


def test_valid_manifest_creation_with_one_record_and_reference() -> None:
    record = _promotion_record()
    reference = _candidate_reference()

    manifest = create_promotion_manifest(
        manifest_id="manifest-1",
        promotion_records=[record],
        candidate_references=[reference],
    )

    assert isinstance(manifest, PromotionManifest)
    assert manifest.manifest_id == "manifest-1"
    assert manifest.promotion_records == (record,)
    assert manifest.candidate_references == (reference,)
    assert manifest.created_timestamp is None
    assert manifest.description is None


def test_valid_manifest_creation_with_multiple_records_and_references() -> None:
    first_record = _promotion_record("record-1", "candidate-1", "proposed")
    second_record = _promotion_record("record-2", "candidate-2", "deferred")
    first_reference = _candidate_reference("record-1", "candidate-1", "proposed")
    second_reference = _candidate_reference("record-2", "candidate-2", "deferred")

    manifest = create_promotion_manifest(
        manifest_id="manifest-1",
        promotion_records=(first_record, second_record),
        candidate_references=(first_reference, second_reference),
        description="Manual inspection manifest.",
    )

    assert manifest.promotion_records == (first_record, second_record)
    assert manifest.candidate_references == (first_reference, second_reference)
    assert manifest.description == "Manual inspection manifest."


@pytest.mark.parametrize("manifest_id", ["", "   "])
def test_manifest_id_validation(manifest_id: str) -> None:
    with pytest.raises(ValueError, match="manifest_id"):
        create_promotion_manifest(
            manifest_id=manifest_id,
            promotion_records=[_promotion_record()],
            candidate_references=[_candidate_reference()],
        )


@pytest.mark.parametrize(
    "promotion_records",
    [
        [],
        "records",
        object(),
    ],
)
def test_promotion_record_sequence_validation(promotion_records: object) -> None:
    with pytest.raises(ValueError, match="promotion_records"):
        create_promotion_manifest(
            manifest_id="manifest-1",
            promotion_records=promotion_records,  # type: ignore[arg-type]
            candidate_references=[_candidate_reference()],
        )


def test_invalid_promotion_record_sequence_item_validation() -> None:
    with pytest.raises(ValueError, match="PromotionRecord"):
        create_promotion_manifest(
            manifest_id="manifest-1",
            promotion_records=[_promotion_record(), object()],  # type: ignore[list-item]
            candidate_references=[_candidate_reference()],
        )


@pytest.mark.parametrize(
    "candidate_references",
    [
        [],
        "references",
        object(),
    ],
)
def test_candidate_reference_sequence_validation(
    candidate_references: object,
) -> None:
    with pytest.raises(ValueError, match="candidate_references"):
        create_promotion_manifest(
            manifest_id="manifest-1",
            promotion_records=[_promotion_record()],
            candidate_references=candidate_references,  # type: ignore[arg-type]
        )


def test_invalid_candidate_reference_sequence_item_validation() -> None:
    with pytest.raises(ValueError, match="PromotionCandidateReference"):
        create_promotion_manifest(
            manifest_id="manifest-1",
            promotion_records=[_promotion_record()],
            candidate_references=[_candidate_reference(), object()],  # type: ignore[list-item]
        )


def test_manifest_optional_fields_normalize() -> None:
    manifest = create_promotion_manifest(
        manifest_id=" manifest-1 ",
        promotion_records=[_promotion_record()],
        candidate_references=[_candidate_reference()],
        description="  ",
    )
    described_manifest = create_promotion_manifest(
        manifest_id="manifest-2",
        promotion_records=[_promotion_record()],
        candidate_references=[_candidate_reference()],
        description=" Local inspection only. ",
    )

    assert manifest.manifest_id == "manifest-1"
    assert manifest.description is None
    assert described_manifest.description == "Local inspection only."


def test_manifest_timestamp_normalizes_to_deterministic_export() -> None:
    manifest = create_promotion_manifest(
        manifest_id="manifest-1",
        promotion_records=[_promotion_record()],
        candidate_references=[_candidate_reference()],
        created_timestamp="2026-01-02T03:04:05",
    )

    assert manifest.to_dict()["created_timestamp"] == "2026-01-02T03:04:05"


def test_manifest_invalid_timestamp_raises_value_error() -> None:
    with pytest.raises(ValueError, match="created_timestamp"):
        create_promotion_manifest(
            manifest_id="manifest-1",
            promotion_records=[_promotion_record()],
            candidate_references=[_candidate_reference()],
            created_timestamp="not-a-timestamp",
        )


def test_manifest_to_dict_is_deterministic_and_json_compatible() -> None:
    record = _promotion_record()
    reference = _candidate_reference()
    manifest = create_promotion_manifest(
        manifest_id="manifest-1",
        promotion_records=[record],
        candidate_references=[reference],
        created_timestamp="2026-01-02T03:04:05",
        description="Local inspection manifest.",
    )

    expected = {
        "schema_version": PROMOTION_MANIFEST_SCHEMA_VERSION,
        "manifest_id": "manifest-1",
        "promotion_records": [record.to_dict()],
        "candidate_references": [reference.to_dict()],
        "created_timestamp": "2026-01-02T03:04:05",
        "description": "Local inspection manifest.",
    }

    assert manifest.to_dict() == expected
    assert manifest.to_dict() == expected
    json.dumps(manifest.to_dict(), allow_nan=False)


def test_manifest_input_sequences_are_not_mutated() -> None:
    record = _promotion_record()
    reference = _candidate_reference()
    promotion_records = [record]
    candidate_references = [reference]

    manifest = create_promotion_manifest(
        manifest_id="manifest-1",
        promotion_records=promotion_records,
        candidate_references=candidate_references,
    )
    promotion_records.append(_promotion_record("record-2", "candidate-2"))
    candidate_references.append(_candidate_reference("record-2", "candidate-2"))

    assert manifest.promotion_records == (record,)
    assert manifest.candidate_references == (reference,)


def test_schema_versions_are_json_compatible() -> None:
    assert PROMOTION_CANDIDATE_REFERENCE_SCHEMA_VERSION == 1
    assert PROMOTION_MANIFEST_SCHEMA_VERSION == 1
    json.dumps(
        {
            "candidate_reference_schema_version": (
                PROMOTION_CANDIDATE_REFERENCE_SCHEMA_VERSION
            ),
            "manifest_schema_version": PROMOTION_MANIFEST_SCHEMA_VERSION,
        },
        allow_nan=False,
    )


def test_candidate_reference_and_manifest_are_immutable() -> None:
    reference = _candidate_reference()
    manifest = create_promotion_manifest(
        manifest_id="manifest-1",
        promotion_records=[_promotion_record()],
        candidate_references=[reference],
    )

    with pytest.raises(FrozenInstanceError):
        reference.status = "rejected"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        manifest.manifest_id = "other"  # type: ignore[misc]


def test_promotion_package_exports_manifest_public_api() -> None:
    from el_psy_quant import promotion

    assert (
        promotion.PROMOTION_CANDIDATE_REFERENCE_SCHEMA_VERSION
        == PROMOTION_CANDIDATE_REFERENCE_SCHEMA_VERSION
    )
    assert promotion.PROMOTION_MANIFEST_SCHEMA_VERSION == PROMOTION_MANIFEST_SCHEMA_VERSION
    assert promotion.PromotionCandidateReference is PromotionCandidateReference
    assert promotion.PromotionManifest is PromotionManifest
    assert (
        promotion.create_promotion_candidate_reference
        is create_promotion_candidate_reference
    )
    assert promotion.create_promotion_manifest is create_promotion_manifest
    assert promotion.PROMOTION_RECORD_STATUSES is PROMOTION_RECORD_STATUSES
