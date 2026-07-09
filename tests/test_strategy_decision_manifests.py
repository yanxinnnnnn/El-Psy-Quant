"""Tests for strategy decision manifests and references."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.decision_governance import (
    STRATEGY_DECISION_MANIFEST_SCHEMA_VERSION,
    STRATEGY_DECISION_REFERENCE_SCHEMA_VERSION,
    SUPPORTED_STRATEGY_DECISION_REFERENCE_TYPES,
    DecisionEvidenceReference,
    StrategyDecisionInput,
    StrategyDecisionManifest,
    StrategyDecisionRecord,
    StrategyDecisionReference,
    StrategyDecisionSummary,
    create_decision_evidence_reference,
    create_strategy_decision_input,
    create_strategy_decision_manifest,
    create_strategy_decision_record,
    create_strategy_decision_reference,
    create_strategy_decision_reference_from_record,
    create_strategy_decision_reference_from_summary,
    create_strategy_decision_summary,
)


def _evidence_reference() -> DecisionEvidenceReference:
    return create_decision_evidence_reference(
        reference_type="promotion_record",
        reference_id="promotion-record-1",
        label="Evidence",
    )


def _decision_input() -> StrategyDecisionInput:
    return create_strategy_decision_input(
        input_id="decision-input-1",
        evidence_references=[_evidence_reference()],
        decision_purpose="Review whether strategy should continue paper review.",
        strategy_id="strategy-1",
    )


def _decision_summary() -> StrategyDecisionSummary:
    return create_strategy_decision_summary(
        summary_id="decision-summary-1",
        decision_input=_decision_input(),
        decision_facts=["Paper review evidence was manually inspected."],
    )


def _decision_record() -> StrategyDecisionRecord:
    return create_strategy_decision_record(
        decision_id="decision-record-1",
        decision_summary=_decision_summary(),
        decision_status="needs_more_evidence",
        rationale="The reviewer needs another paper review cycle.",
    )


def _summary_reference() -> StrategyDecisionReference:
    return create_strategy_decision_reference(
        reference_type="strategy_decision_summary",
        reference_id="decision-summary-1",
        label="Summary",
    )


def _record_reference() -> StrategyDecisionReference:
    return create_strategy_decision_reference(
        reference_type="strategy_decision_record",
        reference_id="decision-record-1",
        label="Record",
    )


def test_valid_strategy_decision_reference_creation() -> None:
    reference = create_strategy_decision_reference(
        reference_type="strategy_decision_summary",
        reference_id="decision-summary-1",
        label="Summary",
        description="Summary reference.",
    )

    assert isinstance(reference, StrategyDecisionReference)
    assert reference.reference_type == "strategy_decision_summary"
    assert reference.reference_id == "decision-summary-1"
    assert reference.label == "Summary"
    assert reference.description == "Summary reference."


def test_supported_strategy_decision_reference_types_are_deterministic() -> None:
    assert SUPPORTED_STRATEGY_DECISION_REFERENCE_TYPES == (
        "strategy_decision_summary",
        "strategy_decision_record",
    )
    json.dumps(
        {"reference_types": SUPPORTED_STRATEGY_DECISION_REFERENCE_TYPES},
        allow_nan=False,
    )


def test_strategy_decision_reference_normalizes_fields() -> None:
    reference = create_strategy_decision_reference(
        reference_type=" strategy_decision_record ",
        reference_id=" decision-record-1 ",
        label=" Record ",
        description="  ",
    )

    assert reference.reference_type == "strategy_decision_record"
    assert reference.reference_id == "decision-record-1"
    assert reference.label == "Record"
    assert reference.description is None


def test_unsupported_reference_type_raises_value_error() -> None:
    with pytest.raises(ValueError, match="unsupported reference_type"):
        create_strategy_decision_reference(
            reference_type="promotion_record",
            reference_id="decision-summary-1",
        )


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("reference_type", {"reference_type": ""}),
        ("reference_type", {"reference_type": "   "}),
        ("reference_id", {"reference_id": ""}),
        ("reference_id", {"reference_id": "   "}),
    ],
)
def test_empty_reference_required_strings_raise_value_error(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "reference_type": "strategy_decision_summary",
        "reference_id": "decision-summary-1",
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_strategy_decision_reference(**arguments)  # type: ignore[arg-type]


def test_valid_manifest_with_summary_references_only() -> None:
    summary_reference = _summary_reference()

    manifest = create_strategy_decision_manifest(
        manifest_id="decision-manifest-1",
        summary_references=[summary_reference],
    )

    assert isinstance(manifest, StrategyDecisionManifest)
    assert manifest.manifest_id == "decision-manifest-1"
    assert manifest.summary_references == (summary_reference,)
    assert manifest.record_references == ()


def test_valid_manifest_with_record_references_only() -> None:
    record_reference = _record_reference()

    manifest = create_strategy_decision_manifest(
        manifest_id="decision-manifest-1",
        record_references=[record_reference],
    )

    assert manifest.summary_references == ()
    assert manifest.record_references == (record_reference,)


def test_valid_manifest_with_summary_and_record_references() -> None:
    summary_reference = _summary_reference()
    record_reference = _record_reference()

    manifest = create_strategy_decision_manifest(
        manifest_id=" decision-manifest-1 ",
        summary_references=[summary_reference],
        record_references=[record_reference],
        created_by=" reviewer-1 ",
        created_timestamp="2026-01-02T03:04:05",
        description="  ",
    )

    assert manifest.manifest_id == "decision-manifest-1"
    assert manifest.summary_references == (summary_reference,)
    assert manifest.record_references == (record_reference,)
    assert manifest.created_by == "reviewer-1"
    assert manifest.to_dict()["created_timestamp"] == "2026-01-02T03:04:05"
    assert manifest.description is None


def test_empty_manifest_raises_value_error() -> None:
    with pytest.raises(ValueError, match="at least one"):
        create_strategy_decision_manifest(manifest_id="decision-manifest-1")


def test_empty_manifest_id_raises_value_error() -> None:
    with pytest.raises(ValueError, match="manifest_id"):
        create_strategy_decision_manifest(
            manifest_id="   ",
            summary_references=[_summary_reference()],
        )


@pytest.mark.parametrize(
    ("field_name", "reference"),
    [
        ("summary_references", _record_reference()),
        ("record_references", _summary_reference()),
    ],
)
def test_manifest_rejects_wrong_bucket_reference_type(
    field_name: str,
    reference: StrategyDecisionReference,
) -> None:
    arguments: dict[str, object] = {"manifest_id": "decision-manifest-1"}
    arguments[field_name] = [reference]

    with pytest.raises(ValueError, match=field_name):
        create_strategy_decision_manifest(**arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize("field_name", ["summary_references", "record_references"])
def test_manifest_rejects_string_reference_sequence(field_name: str) -> None:
    arguments: dict[str, object] = {"manifest_id": "decision-manifest-1"}
    arguments[field_name] = "not-a-sequence"

    with pytest.raises(ValueError, match=field_name):
        create_strategy_decision_manifest(**arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "reference"),
    [
        ("summary_references", _summary_reference()),
        ("record_references", _record_reference()),
    ],
)
def test_manifest_rejects_single_reference_instead_of_sequence(
    field_name: str,
    reference: StrategyDecisionReference,
) -> None:
    arguments: dict[str, object] = {"manifest_id": "decision-manifest-1"}
    arguments[field_name] = reference

    with pytest.raises(ValueError, match=field_name):
        create_strategy_decision_manifest(**arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize("field_name", ["summary_references", "record_references"])
def test_manifest_rejects_invalid_reference_items(field_name: str) -> None:
    arguments: dict[str, object] = {"manifest_id": "decision-manifest-1"}
    arguments[field_name] = [object()]

    with pytest.raises(ValueError, match="StrategyDecisionReference"):
        create_strategy_decision_manifest(**arguments)  # type: ignore[arg-type]


def test_manifest_reference_sequences_are_copied_to_immutable_tuples() -> None:
    summary_references = [_summary_reference()]
    record_references = [_record_reference()]

    manifest = create_strategy_decision_manifest(
        manifest_id="decision-manifest-1",
        summary_references=summary_references,
        record_references=record_references,
    )
    summary_references.append(_summary_reference())
    record_references.append(_record_reference())

    assert len(manifest.summary_references) == 1
    assert len(manifest.record_references) == 1


def test_reference_helper_from_summary_uses_summary_id() -> None:
    summary = _decision_summary()

    reference = create_strategy_decision_reference_from_summary(
        summary,
        label="Summary",
    )

    assert reference.reference_type == "strategy_decision_summary"
    assert reference.reference_id == summary.summary_id
    assert reference.label == "Summary"


def test_reference_helper_from_summary_rejects_invalid_input() -> None:
    with pytest.raises(ValueError, match="StrategyDecisionSummary"):
        create_strategy_decision_reference_from_summary(
            object(),  # type: ignore[arg-type]
        )


def test_reference_helper_from_record_uses_decision_id() -> None:
    record = _decision_record()

    reference = create_strategy_decision_reference_from_record(
        record,
        label="Record",
    )

    assert reference.reference_type == "strategy_decision_record"
    assert reference.reference_id == record.decision_id
    assert reference.label == "Record"


def test_reference_helper_from_record_rejects_invalid_input() -> None:
    with pytest.raises(ValueError, match="StrategyDecisionRecord"):
        create_strategy_decision_reference_from_record(
            object(),  # type: ignore[arg-type]
        )


def test_invalid_optional_field_types_raise_value_error() -> None:
    with pytest.raises(ValueError, match="created_by"):
        create_strategy_decision_manifest(
            manifest_id="decision-manifest-1",
            summary_references=[_summary_reference()],
            created_by=object(),  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="description"):
        create_strategy_decision_manifest(
            manifest_id="decision-manifest-1",
            summary_references=[_summary_reference()],
            description=object(),  # type: ignore[arg-type]
        )


def test_invalid_timestamp_raises_value_error() -> None:
    with pytest.raises(ValueError, match="created_timestamp"):
        create_strategy_decision_manifest(
            manifest_id="decision-manifest-1",
            summary_references=[_summary_reference()],
            created_timestamp="not-a-timestamp",
        )


def test_reference_to_dict_is_deterministic_and_json_compatible() -> None:
    reference = create_strategy_decision_reference(
        reference_type="strategy_decision_summary",
        reference_id="decision-summary-1",
        label="Summary",
        description="Summary reference.",
    )

    expected = {
        "schema_version": STRATEGY_DECISION_REFERENCE_SCHEMA_VERSION,
        "reference_type": "strategy_decision_summary",
        "reference_id": "decision-summary-1",
        "label": "Summary",
        "description": "Summary reference.",
    }

    assert reference.to_dict() == expected
    assert reference.to_dict() == expected
    json.dumps(reference.to_dict(), allow_nan=False)


def test_manifest_to_dict_is_deterministic_and_json_compatible() -> None:
    summary_reference = _summary_reference()
    record_reference = _record_reference()
    manifest = create_strategy_decision_manifest(
        manifest_id="decision-manifest-1",
        summary_references=[summary_reference],
        record_references=[record_reference],
        created_by="reviewer-1",
        created_timestamp="2026-01-02T03:04:05",
        description="Manual decision manifest.",
    )

    expected = {
        "schema_version": STRATEGY_DECISION_MANIFEST_SCHEMA_VERSION,
        "manifest_id": "decision-manifest-1",
        "summary_references": [summary_reference.to_dict()],
        "record_references": [record_reference.to_dict()],
        "created_by": "reviewer-1",
        "created_timestamp": "2026-01-02T03:04:05",
        "description": "Manual decision manifest.",
    }

    assert manifest.to_dict() == expected
    assert manifest.to_dict() == expected
    json.dumps(manifest.to_dict(), allow_nan=False)


def test_schema_versions_are_json_compatible() -> None:
    assert STRATEGY_DECISION_REFERENCE_SCHEMA_VERSION == 1
    assert STRATEGY_DECISION_MANIFEST_SCHEMA_VERSION == 1
    json.dumps(
        {
            "reference_schema": STRATEGY_DECISION_REFERENCE_SCHEMA_VERSION,
            "manifest_schema": STRATEGY_DECISION_MANIFEST_SCHEMA_VERSION,
        },
        allow_nan=False,
    )


def test_reference_and_manifest_are_immutable() -> None:
    reference = _summary_reference()
    manifest = create_strategy_decision_manifest(
        manifest_id="decision-manifest-1",
        summary_references=[reference],
    )

    with pytest.raises(FrozenInstanceError):
        reference.reference_id = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        manifest.manifest_id = "other"  # type: ignore[misc]


def test_decision_governance_package_exports_manifest_public_api() -> None:
    from el_psy_quant import decision_governance

    assert (
        decision_governance.STRATEGY_DECISION_REFERENCE_SCHEMA_VERSION
        == STRATEGY_DECISION_REFERENCE_SCHEMA_VERSION
    )
    assert (
        decision_governance.STRATEGY_DECISION_MANIFEST_SCHEMA_VERSION
        == STRATEGY_DECISION_MANIFEST_SCHEMA_VERSION
    )
    assert (
        decision_governance.SUPPORTED_STRATEGY_DECISION_REFERENCE_TYPES
        == SUPPORTED_STRATEGY_DECISION_REFERENCE_TYPES
    )
    assert decision_governance.StrategyDecisionReference is StrategyDecisionReference
    assert decision_governance.StrategyDecisionManifest is StrategyDecisionManifest
    assert (
        decision_governance.create_strategy_decision_reference
        is create_strategy_decision_reference
    )
    assert (
        decision_governance.create_strategy_decision_manifest
        is create_strategy_decision_manifest
    )
    assert (
        decision_governance.create_strategy_decision_reference_from_summary
        is create_strategy_decision_reference_from_summary
    )
    assert (
        decision_governance.create_strategy_decision_reference_from_record
        is create_strategy_decision_reference_from_record
    )


def test_decision_governance_package_does_not_expose_forbidden_behavior() -> None:
    from el_psy_quant import decision_governance

    forbidden_names = {
        "write_decision_manifest",
        "read_decision_manifest",
        "save_strategy_decision_manifest",
        "load_strategy_decision_manifest",
        "persist_strategy_decision_manifest",
        "discover_decision_evidence",
        "load_decision_evidence",
        "recommend_strategy_decision",
        "approve_strategy",
        "reject_strategy",
        "automatically_promote_strategy",
        "score_decision_evidence",
        "rank_decision_evidence",
        "run_decision_workflow",
        "create_dashboard",
        "render_decision_report",
        "approve_live_trading",
        "allocate_capital",
        "route_orders",
        "mark_live_ready",
        "mark_real_money_ready",
    }

    for forbidden_name in forbidden_names:
        assert not hasattr(decision_governance, forbidden_name)
