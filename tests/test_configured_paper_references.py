"""Tests for configured paper result references."""

import json
from pathlib import Path

import pytest

from el_psy_quant.configured_paper_references import (
    ConfiguredPaperResultReferences,
    create_configured_paper_result_references,
    record_configured_paper_result_references,
)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def make_run_dir(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run-1"
    paper_dir = run_dir / "paper"
    paper_dir.mkdir(parents=True)
    (paper_dir / "paper_run_artifact.json").write_text("{}\n", encoding="utf-8")
    (paper_dir / "paper_run_result_summary.json").write_text(
        "{}\n",
        encoding="utf-8",
    )
    write_json(
        run_dir / "metadata.json",
        {
            "experiment_name": "test",
            "run_id": "run-1",
            "paper_run": {"existing": "kept"},
        },
    )
    write_json(
        run_dir / "manifest.json",
        {
            "schema_version": 1,
            "artifacts": {
                "config": "config.yaml",
                "metadata": "metadata.json",
            },
        },
    )
    return run_dir


def read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_creates_relative_posix_paper_references(tmp_path: Path) -> None:
    run_dir = make_run_dir(tmp_path)

    references = create_configured_paper_result_references(
        run_dir=run_dir,
        paper_run_artifact_path=run_dir / "paper" / "paper_run_artifact.json",
        paper_run_result_summary_path=(
            run_dir / "paper" / "paper_run_result_summary.json"
        ),
    )

    assert references == ConfiguredPaperResultReferences(
        paper_run_artifact_path="paper/paper_run_artifact.json",
        paper_run_result_summary_path="paper/paper_run_result_summary.json",
    )


def test_accepts_relative_paper_paths(tmp_path: Path) -> None:
    run_dir = make_run_dir(tmp_path)

    references = create_configured_paper_result_references(
        run_dir=run_dir,
        paper_run_artifact_path="paper/paper_run_artifact.json",
        paper_run_result_summary_path="paper/paper_run_result_summary.json",
    )

    assert references.paper_run_artifact_path == "paper/paper_run_artifact.json"
    assert (
        references.paper_run_result_summary_path
        == "paper/paper_run_result_summary.json"
    )


def test_records_paper_references_in_metadata_and_manifest(tmp_path: Path) -> None:
    run_dir = make_run_dir(tmp_path)

    references = record_configured_paper_result_references(
        run_dir=run_dir,
        paper_run_artifact_path=run_dir / "paper" / "paper_run_artifact.json",
        paper_run_result_summary_path=(
            run_dir / "paper" / "paper_run_result_summary.json"
        ),
    )

    metadata = read_json(run_dir / "metadata.json")
    manifest = read_json(run_dir / "manifest.json")
    assert references == ConfiguredPaperResultReferences(
        paper_run_artifact_path="paper/paper_run_artifact.json",
        paper_run_result_summary_path="paper/paper_run_result_summary.json",
    )
    assert metadata["paper_run"] == {
        "existing": "kept",
        "artifact_path": "paper/paper_run_artifact.json",
        "result_summary_path": "paper/paper_run_result_summary.json",
    }
    assert manifest["artifacts"] == {
        "config": "config.yaml",
        "metadata": "metadata.json",
        "paper_run_artifact": "paper/paper_run_artifact.json",
        "paper_run_result_summary": "paper/paper_run_result_summary.json",
    }


def test_preserves_existing_metadata_and_manifest_fields(tmp_path: Path) -> None:
    run_dir = make_run_dir(tmp_path)

    record_configured_paper_result_references(
        run_dir=run_dir,
        paper_run_artifact_path=run_dir / "paper" / "paper_run_artifact.json",
        paper_run_result_summary_path=(
            run_dir / "paper" / "paper_run_result_summary.json"
        ),
    )

    assert read_json(run_dir / "metadata.json")["experiment_name"] == "test"
    assert read_json(run_dir / "metadata.json")["run_id"] == "run-1"
    assert read_json(run_dir / "manifest.json")["schema_version"] == 1


def test_recording_is_idempotent(tmp_path: Path) -> None:
    run_dir = make_run_dir(tmp_path)

    record_configured_paper_result_references(
        run_dir=run_dir,
        paper_run_artifact_path=run_dir / "paper" / "paper_run_artifact.json",
        paper_run_result_summary_path=(
            run_dir / "paper" / "paper_run_result_summary.json"
        ),
    )
    first_metadata = (run_dir / "metadata.json").read_text(encoding="utf-8")
    first_manifest = (run_dir / "manifest.json").read_text(encoding="utf-8")
    record_configured_paper_result_references(
        run_dir=run_dir,
        paper_run_artifact_path=run_dir / "paper" / "paper_run_artifact.json",
        paper_run_result_summary_path=(
            run_dir / "paper" / "paper_run_result_summary.json"
        ),
    )

    assert (run_dir / "metadata.json").read_text(encoding="utf-8") == first_metadata
    assert (run_dir / "manifest.json").read_text(encoding="utf-8") == first_manifest


def test_recording_writes_deterministic_json_with_trailing_newline(
    tmp_path: Path,
) -> None:
    run_dir = make_run_dir(tmp_path)

    record_configured_paper_result_references(
        run_dir=run_dir,
        paper_run_artifact_path=run_dir / "paper" / "paper_run_artifact.json",
        paper_run_result_summary_path=(
            run_dir / "paper" / "paper_run_result_summary.json"
        ),
    )

    for path in (run_dir / "metadata.json", run_dir / "manifest.json"):
        text = path.read_text(encoding="utf-8")
        assert text.endswith("\n")
        json.dumps(json.loads(text), allow_nan=False)


@pytest.mark.parametrize("missing_file", ["metadata.json", "manifest.json"])
def test_missing_existing_configured_run_outputs_raise_value_error(
    tmp_path: Path,
    missing_file: str,
) -> None:
    run_dir = make_run_dir(tmp_path)
    (run_dir / missing_file).unlink()

    with pytest.raises(ValueError, match=missing_file):
        record_configured_paper_result_references(
            run_dir=run_dir,
            paper_run_artifact_path=run_dir / "paper" / "paper_run_artifact.json",
            paper_run_result_summary_path=(
                run_dir / "paper" / "paper_run_result_summary.json"
            ),
        )


@pytest.mark.parametrize(
    "missing_reference",
    ["paper_run_artifact.json", "paper_run_result_summary.json"],
)
def test_missing_paper_outputs_raise_value_error(
    tmp_path: Path,
    missing_reference: str,
) -> None:
    run_dir = make_run_dir(tmp_path)
    (run_dir / "paper" / missing_reference).unlink()

    with pytest.raises(ValueError, match="existing file"):
        record_configured_paper_result_references(
            run_dir=run_dir,
            paper_run_artifact_path=run_dir / "paper" / "paper_run_artifact.json",
            paper_run_result_summary_path=(
                run_dir / "paper" / "paper_run_result_summary.json"
            ),
        )


def test_paper_paths_outside_run_dir_raise_value_error(tmp_path: Path) -> None:
    run_dir = make_run_dir(tmp_path)
    outside_artifact = tmp_path / "paper_run_artifact.json"
    outside_artifact.write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="under run_dir"):
        create_configured_paper_result_references(
            run_dir=run_dir,
            paper_run_artifact_path=outside_artifact,
            paper_run_result_summary_path=(
                run_dir / "paper" / "paper_run_result_summary.json"
            ),
        )


def test_unexpected_paper_paths_raise_value_error(tmp_path: Path) -> None:
    run_dir = make_run_dir(tmp_path)
    other_artifact = run_dir / "paper" / "other.json"
    other_artifact.write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="paper/paper_run_artifact.json"):
        create_configured_paper_result_references(
            run_dir=run_dir,
            paper_run_artifact_path=other_artifact,
            paper_run_result_summary_path=(
                run_dir / "paper" / "paper_run_result_summary.json"
            ),
        )


def test_no_extra_files_are_written(tmp_path: Path) -> None:
    run_dir = make_run_dir(tmp_path)
    before_files = sorted(path.relative_to(run_dir).as_posix() for path in run_dir.rglob("*"))

    record_configured_paper_result_references(
        run_dir=run_dir,
        paper_run_artifact_path=run_dir / "paper" / "paper_run_artifact.json",
        paper_run_result_summary_path=(
            run_dir / "paper" / "paper_run_result_summary.json"
        ),
    )

    after_files = sorted(path.relative_to(run_dir).as_posix() for path in run_dir.rglob("*"))
    assert after_files == before_files


def test_configured_paper_references_api_is_importable() -> None:
    from el_psy_quant import configured_paper_references

    assert (
        configured_paper_references.ConfiguredPaperResultReferences
        is ConfiguredPaperResultReferences
    )
    assert (
        configured_paper_references.create_configured_paper_result_references
        is create_configured_paper_result_references
    )
    assert (
        configured_paper_references.record_configured_paper_result_references
        is record_configured_paper_result_references
    )
