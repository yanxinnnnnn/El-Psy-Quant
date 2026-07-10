"""Tests for strategy lifecycle state snapshots."""

import inspect
import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.strategy_review import (
    STRATEGY_LIFECYCLE_STATE_SNAPSHOT_SCHEMA_VERSION,
    SUPPORTED_STRATEGY_LIFECYCLE_STATES,
    StrategyLifecycleStateSnapshot,
    create_strategy_lifecycle_state_snapshot,
)


def _snapshot(
    lifecycle_state: str = "research_review",
) -> StrategyLifecycleStateSnapshot:
    return create_strategy_lifecycle_state_snapshot(
        snapshot_id="snapshot-1",
        strategy_id="strategy-1",
        lifecycle_state=lifecycle_state,
        rationale="Caller-supplied lifecycle declaration.",
    )


def test_supported_lifecycle_states_are_exact_and_deterministic() -> None:
    assert SUPPORTED_STRATEGY_LIFECYCLE_STATES == (
        "research_review",
        "paper_review",
        "watchlist",
        "on_hold",
        "rejected",
    )
    json.dumps({"states": SUPPORTED_STRATEGY_LIFECYCLE_STATES}, allow_nan=False)


@pytest.mark.parametrize("lifecycle_state", SUPPORTED_STRATEGY_LIFECYCLE_STATES)
def test_all_supported_lifecycle_states_can_be_created(
    lifecycle_state: str,
) -> None:
    snapshot = _snapshot(lifecycle_state)

    assert isinstance(snapshot, StrategyLifecycleStateSnapshot)
    assert snapshot.lifecycle_state == lifecycle_state
    assert snapshot.declared_by is None
    assert snapshot.declared_timestamp is None
    assert snapshot.notes == ()
    assert snapshot.warnings == ()


def test_required_strings_normalize_whitespace() -> None:
    snapshot = create_strategy_lifecycle_state_snapshot(
        snapshot_id=" snapshot-1 ",
        strategy_id=" strategy-1 ",
        lifecycle_state=" paper_review ",
        rationale=" Caller-supplied declaration. ",
    )

    assert snapshot.snapshot_id == "snapshot-1"
    assert snapshot.strategy_id == "strategy-1"
    assert snapshot.lifecycle_state == "paper_review"
    assert snapshot.rationale == "Caller-supplied declaration."


def test_optional_declared_by_normalizes() -> None:
    snapshot = create_strategy_lifecycle_state_snapshot(
        snapshot_id="snapshot-1",
        strategy_id="strategy-1",
        lifecycle_state="research_review",
        rationale="Caller-supplied declaration.",
        declared_by="  ",
    )

    assert snapshot.declared_by is None


def test_timestamp_normalizes_and_exports_as_iso_string() -> None:
    snapshot = create_strategy_lifecycle_state_snapshot(
        snapshot_id="snapshot-1",
        strategy_id="strategy-1",
        lifecycle_state="paper_review",
        rationale="Caller-supplied declaration.",
        declared_timestamp="2026-01-02T03:04:05",
    )

    assert snapshot.to_dict()["declared_timestamp"] == "2026-01-02T03:04:05"


@pytest.mark.parametrize("declared_timestamp", ["not-a-timestamp", "NaT"])
def test_invalid_timestamp_is_rejected(declared_timestamp: object) -> None:
    with pytest.raises(ValueError, match="declared_timestamp"):
        create_strategy_lifecycle_state_snapshot(
            snapshot_id="snapshot-1",
            strategy_id="strategy-1",
            lifecycle_state="research_review",
            rationale="Caller-supplied declaration.",
            declared_timestamp=declared_timestamp,
        )


def test_notes_and_warnings_normalize_to_immutable_tuples() -> None:
    notes = [" first note "]
    warnings = [" first warning "]
    snapshot = create_strategy_lifecycle_state_snapshot(
        snapshot_id="snapshot-1",
        strategy_id="strategy-1",
        lifecycle_state="watchlist",
        rationale="Caller-supplied declaration.",
        notes=notes,
        warnings=warnings,
    )
    notes.append("new note")
    warnings.append("new warning")

    assert snapshot.notes == ("first note",)
    assert snapshot.warnings == ("first warning",)


@pytest.mark.parametrize("field_name", ["notes", "warnings"])
def test_sequence_fields_reject_invalid_values(field_name: str) -> None:
    arguments: dict[str, object] = {
        "snapshot_id": "snapshot-1",
        "strategy_id": "strategy-1",
        "lifecycle_state": "research_review",
        "rationale": "Caller-supplied declaration.",
    }

    for invalid_value in (object(), "not-a-sequence", ["   "], [object()]):
        arguments[field_name] = invalid_value
        with pytest.raises(ValueError, match=field_name):
            create_strategy_lifecycle_state_snapshot(**arguments)  # type: ignore[arg-type]


def test_unsupported_lifecycle_state_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported lifecycle_state"):
        _snapshot("live_ready")


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("snapshot_id", {"snapshot_id": ""}),
        ("snapshot_id", {"snapshot_id": "   "}),
        ("strategy_id", {"strategy_id": ""}),
        ("strategy_id", {"strategy_id": "   "}),
        ("rationale", {"rationale": ""}),
        ("rationale", {"rationale": "   "}),
    ],
)
def test_empty_required_fields_are_rejected(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "snapshot_id": "snapshot-1",
        "strategy_id": "strategy-1",
        "lifecycle_state": "research_review",
        "rationale": "Caller-supplied declaration.",
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_strategy_lifecycle_state_snapshot(**arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("snapshot_id", {"snapshot_id": object()}),
        ("strategy_id", {"strategy_id": object()}),
        ("lifecycle_state", {"lifecycle_state": object()}),
        ("rationale", {"rationale": object()}),
        ("declared_by", {"declared_by": object()}),
        ("declared_timestamp", {"declared_timestamp": object()}),
    ],
)
def test_invalid_field_types_are_rejected(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "snapshot_id": "snapshot-1",
        "strategy_id": "strategy-1",
        "lifecycle_state": "research_review",
        "rationale": "Caller-supplied declaration.",
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=field_name):
        create_strategy_lifecycle_state_snapshot(**arguments)  # type: ignore[arg-type]


def test_to_dict_is_deterministic_and_json_compatible() -> None:
    snapshot = create_strategy_lifecycle_state_snapshot(
        snapshot_id="snapshot-1",
        strategy_id="strategy-1",
        lifecycle_state="on_hold",
        rationale="Caller-supplied declaration.",
        declared_by="reviewer-1",
        declared_timestamp="2026-01-02T03:04:05",
        notes=["note"],
        warnings=["warning"],
    )
    expected = {
        "schema_version": STRATEGY_LIFECYCLE_STATE_SNAPSHOT_SCHEMA_VERSION,
        "snapshot_id": "snapshot-1",
        "strategy_id": "strategy-1",
        "lifecycle_state": "on_hold",
        "rationale": "Caller-supplied declaration.",
        "declared_by": "reviewer-1",
        "declared_timestamp": "2026-01-02T03:04:05",
        "notes": ["note"],
        "warnings": ["warning"],
    }

    assert snapshot.to_dict() == expected
    assert snapshot.to_dict() == expected
    json.dumps(snapshot.to_dict(), allow_nan=False)


def test_schema_version_is_json_compatible() -> None:
    assert STRATEGY_LIFECYCLE_STATE_SNAPSHOT_SCHEMA_VERSION == 1
    json.dumps(
        {"schema_version": STRATEGY_LIFECYCLE_STATE_SNAPSHOT_SCHEMA_VERSION},
        allow_nan=False,
    )


def test_snapshot_is_immutable() -> None:
    snapshot = _snapshot()

    with pytest.raises(FrozenInstanceError):
        snapshot.snapshot_id = "other"  # type: ignore[misc]


def test_lifecycle_state_has_no_implicit_default() -> None:
    lifecycle_state = inspect.signature(
        StrategyLifecycleStateSnapshot
    ).parameters["lifecycle_state"]

    assert lifecycle_state.default is inspect.Parameter.empty


def test_strategy_review_package_exports_snapshot_public_api() -> None:
    from el_psy_quant import strategy_review

    assert (
        strategy_review.STRATEGY_LIFECYCLE_STATE_SNAPSHOT_SCHEMA_VERSION
        == STRATEGY_LIFECYCLE_STATE_SNAPSHOT_SCHEMA_VERSION
    )
    assert (
        strategy_review.SUPPORTED_STRATEGY_LIFECYCLE_STATES
        == SUPPORTED_STRATEGY_LIFECYCLE_STATES
    )
    assert strategy_review.StrategyLifecycleStateSnapshot is StrategyLifecycleStateSnapshot
    assert (
        strategy_review.create_strategy_lifecycle_state_snapshot
        is create_strategy_lifecycle_state_snapshot
    )


def test_strategy_review_package_does_not_expose_forbidden_behavior() -> None:
    from el_psy_quant import strategy_review

    forbidden_names = {
        "LifecycleTransitionProposal",
        "LifecycleTransitionRecord",
        "create_lifecycle_transition_proposal",
        "create_lifecycle_transition_record",
        "create_strategy_review_manifest",
        "get_current_lifecycle_state",
        "set_current_lifecycle_state",
        "derive_lifecycle_state",
        "apply_lifecycle_transition",
        "validate_lifecycle_transition",
        "discover_strategy_review_evidence",
        "load_strategy_review_evidence",
        "run_strategy_review_workflow",
        "mark_live_ready",
        "approve_for_live",
        "allocate_capital",
    }

    for forbidden_name in forbidden_names:
        assert not hasattr(strategy_review, forbidden_name)
