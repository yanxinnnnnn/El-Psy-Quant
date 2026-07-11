import inspect
import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.strategy_review import (
    STRATEGY_REVIEW_WORKFLOW_MANIFEST_SCHEMA_VERSION,
    STRATEGY_REVIEW_WORKFLOW_REFERENCE_SCHEMA_VERSION,
    SUPPORTED_STRATEGY_REVIEW_WORKFLOW_REFERENCE_TYPES,
    StrategyReviewWorkflowManifest,
    StrategyReviewWorkflowReference,
    create_strategy_lifecycle_state_snapshot,
    create_strategy_lifecycle_transition_proposal,
    create_strategy_lifecycle_transition_record,
    create_strategy_review_evidence_reference,
    create_strategy_review_workflow_manifest,
    create_strategy_review_workflow_reference,
    create_strategy_review_workflow_reference_from_state_snapshot,
    create_strategy_review_workflow_reference_from_transition_proposal,
    create_strategy_review_workflow_reference_from_transition_record,
)

SNAPSHOT_TYPE = "strategy_lifecycle_state_snapshot"
PROPOSAL_TYPE = "strategy_lifecycle_transition_proposal"
RECORD_TYPE = "strategy_lifecycle_transition_record"


def _snapshot(state: str = "research_review", snapshot_id: str = "snapshot-1"):
    return create_strategy_lifecycle_state_snapshot(
        snapshot_id=snapshot_id,
        strategy_id="strategy-1",
        lifecycle_state=state,
        rationale="Caller-supplied state.",
    )


def _proposal():
    return create_strategy_lifecycle_transition_proposal(
        proposal_id="proposal-1",
        source_snapshot=_snapshot(),
        target_state="watchlist",
        rationale="Request review.",
        evidence_references=[
            create_strategy_review_evidence_reference(
                reference_type="strategy_decision_record",
                reference_id="decision-1",
            )
        ],
    )


def _record():
    return create_strategy_lifecycle_transition_record(
        transition_record_id="record-1",
        proposal=_proposal(),
        review_outcome="approved",
        rationale="Approved as governance evidence.",
        resulting_snapshot=_snapshot("watchlist", "snapshot-2"),
    )


def _reference(reference_type: str, reference_id: str = "reference-1"):
    return create_strategy_review_workflow_reference(
        reference_type=reference_type,
        reference_id=reference_id,
    )


def test_public_constants_are_exact_and_deterministic():
    assert STRATEGY_REVIEW_WORKFLOW_REFERENCE_SCHEMA_VERSION == 1
    assert STRATEGY_REVIEW_WORKFLOW_MANIFEST_SCHEMA_VERSION == 1
    assert SUPPORTED_STRATEGY_REVIEW_WORKFLOW_REFERENCE_TYPES == (
        SNAPSHOT_TYPE,
        PROPOSAL_TYPE,
        RECORD_TYPE,
    )
    json.dumps(SUPPORTED_STRATEGY_REVIEW_WORKFLOW_REFERENCE_TYPES, allow_nan=False)


@pytest.mark.parametrize("reference_type", (SNAPSHOT_TYPE, PROPOSAL_TYPE, RECORD_TYPE))
def test_all_supported_reference_types_create(reference_type: str):
    reference = _reference(reference_type)
    assert isinstance(reference, StrategyReviewWorkflowReference)
    assert reference.reference_type == reference_type


def test_reference_fields_normalize():
    reference = create_strategy_review_workflow_reference(
        reference_type=f" {SNAPSHOT_TYPE} ",
        reference_id=" snapshot-1 ",
        label=" Snapshot ",
        description="  ",
    )
    assert reference.reference_type == SNAPSHOT_TYPE
    assert reference.reference_id == "snapshot-1"
    assert reference.label == "Snapshot"
    assert reference.description is None


@pytest.mark.parametrize("value", ("unknown", "", "   ", object()))
def test_invalid_reference_types_are_rejected(value):
    with pytest.raises(ValueError, match="reference_type"):
        create_strategy_review_workflow_reference(
            reference_type=value,
            reference_id="reference-1",
        )


@pytest.mark.parametrize("value", ("", "   ", object()))
def test_invalid_reference_ids_are_rejected(value):
    with pytest.raises(ValueError, match="reference_id"):
        create_strategy_review_workflow_reference(
            reference_type=SNAPSHOT_TYPE,
            reference_id=value,
        )


@pytest.mark.parametrize("field", ("label", "description"))
def test_invalid_optional_reference_strings_are_rejected(field: str):
    with pytest.raises(ValueError, match=field):
        create_strategy_review_workflow_reference(
            reference_type=SNAPSHOT_TYPE,
            reference_id="snapshot-1",
            **{field: object()},
        )


def test_reference_is_frozen_and_serializes_deterministically():
    reference = create_strategy_review_workflow_reference(
        reference_type=SNAPSHOT_TYPE,
        reference_id="snapshot-1",
        label="Snapshot",
        description="Compact pointer.",
    )
    expected = {
        "schema_version": STRATEGY_REVIEW_WORKFLOW_REFERENCE_SCHEMA_VERSION,
        "reference_type": SNAPSHOT_TYPE,
        "reference_id": "snapshot-1",
        "label": "Snapshot",
        "description": "Compact pointer.",
    }
    assert reference.to_dict() == expected == reference.to_dict()
    json.dumps(reference.to_dict(), allow_nan=False)
    with pytest.raises(FrozenInstanceError):
        reference.reference_id = "other"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("factory", "argument", "source", "reference_type", "reference_id"),
    (
        (
            create_strategy_review_workflow_reference_from_state_snapshot,
            "snapshot",
            _snapshot,
            SNAPSHOT_TYPE,
            "snapshot-1",
        ),
        (
            create_strategy_review_workflow_reference_from_transition_proposal,
            "proposal",
            _proposal,
            PROPOSAL_TYPE,
            "proposal-1",
        ),
        (
            create_strategy_review_workflow_reference_from_transition_record,
            "record",
            _record,
            RECORD_TYPE,
            "record-1",
        ),
    ),
)
def test_helpers_derive_only_stable_ids_and_preserve_sources(
    factory, argument: str, source, reference_type: str, reference_id: str
):
    artifact = source()
    before = artifact.to_dict()
    reference = factory(**{argument: artifact}, label=" Label ")
    assert reference.reference_type == reference_type
    assert reference.reference_id == reference_id
    assert reference.label == "Label"
    assert set(reference.to_dict()) == {
        "schema_version",
        "reference_type",
        "reference_id",
        "label",
        "description",
    }
    assert artifact.to_dict() == before


@pytest.mark.parametrize(
    ("factory", "argument", "message"),
    (
        (
            create_strategy_review_workflow_reference_from_state_snapshot,
            "snapshot",
            "StrategyLifecycleStateSnapshot",
        ),
        (
            create_strategy_review_workflow_reference_from_transition_proposal,
            "proposal",
            "StrategyLifecycleTransitionProposal",
        ),
        (
            create_strategy_review_workflow_reference_from_transition_record,
            "record",
            "StrategyLifecycleTransitionRecord",
        ),
    ),
)
def test_helpers_reject_invalid_objects(factory, argument: str, message: str):
    with pytest.raises(ValueError, match=message):
        factory(**{argument: object()})


@pytest.mark.parametrize(
    ("field", "reference_type"),
    (
        ("state_snapshot_references", SNAPSHOT_TYPE),
        ("transition_proposal_references", PROPOSAL_TYPE),
        ("transition_record_references", RECORD_TYPE),
    ),
)
def test_partial_manifests_accept_each_group(field: str, reference_type: str):
    reference = _reference(reference_type)
    manifest = create_strategy_review_workflow_manifest(
        manifest_id="manifest-1", **{field: [reference]}
    )
    assert isinstance(manifest, StrategyReviewWorkflowManifest)
    assert getattr(manifest, field) == (reference,)


def test_valid_mixed_manifest():
    snapshot = _reference(SNAPSHOT_TYPE, "snapshot-1")
    proposal = _reference(PROPOSAL_TYPE, "proposal-1")
    record = _reference(RECORD_TYPE, "record-1")
    manifest = create_strategy_review_workflow_manifest(
        manifest_id="manifest-1",
        state_snapshot_references=[snapshot],
        transition_proposal_references=[proposal],
        transition_record_references=[record],
    )
    assert manifest.state_snapshot_references == (snapshot,)
    assert manifest.transition_proposal_references == (proposal,)
    assert manifest.transition_record_references == (record,)


def test_empty_manifest_is_rejected():
    with pytest.raises(ValueError, match="at least one"):
        create_strategy_review_workflow_manifest(manifest_id="manifest-1")


@pytest.mark.parametrize(
    "field",
    (
        "state_snapshot_references",
        "transition_proposal_references",
        "transition_record_references",
    ),
)
@pytest.mark.parametrize("value", ("bare", object()))
def test_manifest_rejects_strings_and_non_sequences(field: str, value):
    with pytest.raises(ValueError, match=field):
        create_strategy_review_workflow_manifest(
            manifest_id="manifest-1", **{field: value}
        )


@pytest.mark.parametrize(
    ("field", "reference_type"),
    (
        ("state_snapshot_references", SNAPSHOT_TYPE),
        ("transition_proposal_references", PROPOSAL_TYPE),
        ("transition_record_references", RECORD_TYPE),
    ),
)
def test_manifest_rejects_bare_reference_and_invalid_items(
    field: str, reference_type: str
):
    reference = _reference(reference_type)
    with pytest.raises(ValueError, match=field):
        create_strategy_review_workflow_manifest(
            manifest_id="manifest-1", **{field: reference}
        )
    with pytest.raises(ValueError, match=field):
        create_strategy_review_workflow_manifest(
            manifest_id="manifest-1", **{field: [object()]}
        )


@pytest.mark.parametrize(
    ("field", "wrong_type"),
    (
        ("state_snapshot_references", PROPOSAL_TYPE),
        ("transition_proposal_references", RECORD_TYPE),
        ("transition_record_references", SNAPSHOT_TYPE),
    ),
)
def test_manifest_rejects_wrong_reference_type(field: str, wrong_type: str):
    with pytest.raises(ValueError, match=field):
        create_strategy_review_workflow_manifest(
            manifest_id="manifest-1", **{field: [_reference(wrong_type)]}
        )


def test_manifest_preserves_order_duplicates_and_immutable_tuple():
    first = _reference(SNAPSHOT_TYPE, "snapshot-2")
    second = _reference(SNAPSHOT_TYPE, "snapshot-1")
    values = [first, second, first]
    manifest = create_strategy_review_workflow_manifest(
        manifest_id="manifest-1", state_snapshot_references=values
    )
    values.append(second)
    assert manifest.state_snapshot_references == (first, second, first)


def test_manifest_metadata_normalizes():
    manifest = create_strategy_review_workflow_manifest(
        manifest_id=" manifest-1 ",
        state_snapshot_references=[_reference(SNAPSHOT_TYPE)],
        created_by=" reviewer ",
        created_timestamp="2026-01-02T03:04:05",
        description="  ",
    )
    assert manifest.manifest_id == "manifest-1"
    assert manifest.created_by == "reviewer"
    assert manifest.description is None
    assert manifest.to_dict()["created_timestamp"] == "2026-01-02T03:04:05"


@pytest.mark.parametrize("value", ("", "   ", object()))
def test_invalid_manifest_ids_are_rejected(value):
    with pytest.raises(ValueError, match="manifest_id"):
        create_strategy_review_workflow_manifest(
            manifest_id=value,
            state_snapshot_references=[_reference(SNAPSHOT_TYPE)],
        )


@pytest.mark.parametrize("field", ("created_by", "description"))
def test_invalid_manifest_optional_strings_are_rejected(field: str):
    with pytest.raises(ValueError, match=field):
        create_strategy_review_workflow_manifest(
            manifest_id="manifest-1",
            state_snapshot_references=[_reference(SNAPSHOT_TYPE)],
            **{field: object()},
        )


@pytest.mark.parametrize("value", ("invalid", "NaT", object()))
def test_invalid_manifest_timestamps_are_rejected(value):
    with pytest.raises(ValueError, match="created_timestamp"):
        create_strategy_review_workflow_manifest(
            manifest_id="manifest-1",
            state_snapshot_references=[_reference(SNAPSHOT_TYPE)],
            created_timestamp=value,
        )


def test_complete_manifest_serialization_is_deterministic_and_json_compatible():
    snapshot = _reference(SNAPSHOT_TYPE, "snapshot-1")
    proposal = _reference(PROPOSAL_TYPE, "proposal-1")
    record = _reference(RECORD_TYPE, "record-1")
    manifest = create_strategy_review_workflow_manifest(
        manifest_id="manifest-1",
        state_snapshot_references=[snapshot],
        transition_proposal_references=[proposal],
        transition_record_references=[record],
        created_by="reviewer",
        created_timestamp="2026-01-02T03:04:05",
        description="Caller-supplied local index.",
    )
    expected = {
        "schema_version": STRATEGY_REVIEW_WORKFLOW_MANIFEST_SCHEMA_VERSION,
        "manifest_id": "manifest-1",
        "state_snapshot_references": [snapshot.to_dict()],
        "transition_proposal_references": [proposal.to_dict()],
        "transition_record_references": [record.to_dict()],
        "created_by": "reviewer",
        "created_timestamp": "2026-01-02T03:04:05",
        "description": "Caller-supplied local index.",
    }
    assert manifest.to_dict() == expected == manifest.to_dict()
    json.dumps(manifest.to_dict(), allow_nan=False)
    with pytest.raises(FrozenInstanceError):
        manifest.manifest_id = "other"  # type: ignore[misc]


def test_public_factories_are_explicit_keyword_only_and_exports_exist():
    factories = (
        create_strategy_review_workflow_reference,
        create_strategy_review_workflow_manifest,
        create_strategy_review_workflow_reference_from_state_snapshot,
        create_strategy_review_workflow_reference_from_transition_proposal,
        create_strategy_review_workflow_reference_from_transition_record,
    )
    for factory in factories:
        parameters = inspect.signature(factory).parameters
        assert "kwargs" not in parameters
        assert all(
            parameter.kind is inspect.Parameter.KEYWORD_ONLY
            for parameter in parameters.values()
        )
    from el_psy_quant import strategy_review

    assert (
        strategy_review.StrategyReviewWorkflowReference
        is StrategyReviewWorkflowReference
    )
    assert (
        strategy_review.StrategyReviewWorkflowManifest is StrategyReviewWorkflowManifest
    )
    assert (
        strategy_review.SUPPORTED_STRATEGY_REVIEW_WORKFLOW_REFERENCE_TYPES
        == SUPPORTED_STRATEGY_REVIEW_WORKFLOW_REFERENCE_TYPES
    )


def test_package_has_no_resolution_execution_persistence_or_live_behavior():
    from el_psy_quant import strategy_review

    forbidden = {
        "load_strategy_review_artifact",
        "resolve_strategy_review_reference",
        "validate_strategy_review_workflow_chain",
        "apply_lifecycle_transition",
        "get_current_lifecycle_state",
        "write_strategy_review_manifest",
        "save_strategy_review_manifest",
        "create_strategy_review_workflow",
        "run_strategy_review_workflow",
        "mark_broker_ready",
        "mark_live_ready",
        "allocate_capital",
    }
    assert all(not hasattr(strategy_review, name) for name in forbidden)
