"""Tests for the compact immutable artifact-index value contract."""

from dataclasses import FrozenInstanceError, fields

import pytest

from el_psy_quant.persistence import (
    ArtifactIndexEntry,
    create_artifact_index_entry,
)


@pytest.mark.parametrize(
    ("artifact_type", "artifact_key", "source_id", "root_type", "path"),
    (
        (
            "research_run_manifest",
            "daily-research/run_1",
            "run_1",
            "research",
            "daily-research/run_1/manifest.json",
        ),
        (
            "strategy_decision_manifest",
            "decision_file",
            "decision manifest id",
            "evidence",
            "strategy-decisions/decision_file.json",
        ),
        (
            "report_artifact_manifest",
            "report-1",
            "report manifest id",
            "evidence",
            "report-artifacts/report-1.json",
        ),
        (
            "strategy_review_workflow_manifest",
            "review_1",
            "review manifest id",
            "evidence",
            "strategy-review/review_1.json",
        ),
    ),
)
def test_factory_derives_exact_supported_locator(
    artifact_type: str,
    artifact_key: str,
    source_id: str,
    root_type: str,
    path: str,
) -> None:
    entry = create_artifact_index_entry(
        artifact_type=artifact_type,
        artifact_key=artifact_key,
        source_id=source_id,
    )

    assert entry.record_schema_version == 1
    assert entry.root_type == root_type
    assert entry.relative_path == path
    assert entry.source_id == source_id
    assert tuple(field.name for field in fields(entry)) == (
        "record_schema_version",
        "artifact_type",
        "artifact_key",
        "root_type",
        "relative_path",
        "source_id",
    )
    assert not hasattr(entry, "payload")
    assert not hasattr(entry, "status")
    with pytest.raises(FrozenInstanceError):
        entry.source_id = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("record_schema_version", 2),
        ("artifact_type", "paper_run_manifest"),
        ("root_type", "evidence"),
        ("relative_path", "/daily-research/run_1/manifest.json"),
        ("relative_path", "C:/daily-research/run_1/manifest.json"),
        ("relative_path", "daily-research/../run_1/manifest.json"),
        ("relative_path", "daily-research\\run_1\\manifest.json"),
        ("relative_path", "daily-research/run_1/other.json"),
        ("source_id", "other-run"),
    ),
)
def test_entry_rejects_invalid_or_mismatched_fields(field: str, value: object) -> None:
    values: dict[str, object] = {
        "record_schema_version": 1,
        "artifact_type": "research_run_manifest",
        "artifact_key": "daily-research/run_1",
        "root_type": "research",
        "relative_path": "daily-research/run_1/manifest.json",
        "source_id": "run_1",
    }
    values[field] = value

    with pytest.raises(ValueError):
        ArtifactIndexEntry(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "artifact_key",
    ("", "experiment", "Experiment/run", "experiment/run/id", "experiment/.."),
)
def test_research_keys_are_exact_slug_and_run_pairs(artifact_key: str) -> None:
    with pytest.raises(ValueError):
        create_artifact_index_entry(
            artifact_type="research_run_manifest",
            artifact_key=artifact_key,
            source_id="run",
        )


@pytest.mark.parametrize("artifact_key", ("", ".", "..", "a/b", "a\\b", "a.json"))
def test_evidence_keys_remain_safe_file_selectors(artifact_key: str) -> None:
    with pytest.raises(ValueError):
        create_artifact_index_entry(
            artifact_type="report_artifact_manifest",
            artifact_key=artifact_key,
            source_id="manifest-id",
        )
