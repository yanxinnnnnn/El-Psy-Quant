"""Configured paper result references for existing run artifacts."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PAPER_RUN_ARTIFACT_REFERENCE = "paper/paper_run_artifact.json"
PAPER_RUN_RESULT_SUMMARY_REFERENCE = "paper/paper_run_result_summary.json"
_JSON_ENCODING = "utf-8"


@dataclass(frozen=True)
class ConfiguredPaperResultReferences:
    """Relative configured paper output references."""

    paper_run_artifact_path: str
    paper_run_result_summary_path: str


def _validate_run_dir(run_dir: str | Path) -> Path:
    if isinstance(run_dir, str) and not run_dir.strip():
        raise ValueError("run_dir must be a non-empty path")
    if not isinstance(run_dir, (str, Path)):
        raise ValueError("run_dir must be a string or Path")
    path = Path(run_dir)
    if not path.exists():
        raise ValueError("run_dir must already exist")
    if not path.is_dir():
        raise ValueError("run_dir must be a directory")
    return path


def _validate_existing_json_mapping(path: Path, *, field_name: str) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{field_name} must already exist")
    try:
        payload = json.loads(path.read_text(encoding=_JSON_ENCODING))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must contain valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{field_name} must contain a JSON object")
    return payload


def _relative_paper_file_reference(
    *,
    run_dir: Path,
    path: str | Path,
    expected_reference: str,
    field_name: str,
) -> str:
    if isinstance(path, str) and not path.strip():
        raise ValueError(f"{field_name} must be a non-empty path")
    if not isinstance(path, (str, Path)):
        raise ValueError(f"{field_name} must be a string or Path")

    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = run_dir / candidate
    if not candidate.is_file():
        raise ValueError(f"{field_name} must be an existing file")

    try:
        relative_path = candidate.resolve().relative_to(run_dir.resolve())
    except ValueError as exc:
        raise ValueError(f"{field_name} must be under run_dir") from exc

    reference = relative_path.as_posix()
    if reference != expected_reference:
        raise ValueError(f"{field_name} must be {expected_reference}")
    return reference


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    document = json.dumps(payload, indent=2, allow_nan=False) + "\n"
    path.write_text(document, encoding=_JSON_ENCODING)


def create_configured_paper_result_references(
    *,
    run_dir: str | Path,
    paper_run_artifact_path: str | Path,
    paper_run_result_summary_path: str | Path,
) -> ConfiguredPaperResultReferences:
    """Create validated relative configured paper result references."""
    validated_run_dir = _validate_run_dir(run_dir)
    return ConfiguredPaperResultReferences(
        paper_run_artifact_path=_relative_paper_file_reference(
            run_dir=validated_run_dir,
            path=paper_run_artifact_path,
            expected_reference=PAPER_RUN_ARTIFACT_REFERENCE,
            field_name="paper_run_artifact_path",
        ),
        paper_run_result_summary_path=_relative_paper_file_reference(
            run_dir=validated_run_dir,
            path=paper_run_result_summary_path,
            expected_reference=PAPER_RUN_RESULT_SUMMARY_REFERENCE,
            field_name="paper_run_result_summary_path",
        ),
    )


def record_configured_paper_result_references(
    *,
    run_dir: str | Path,
    paper_run_artifact_path: str | Path,
    paper_run_result_summary_path: str | Path,
) -> ConfiguredPaperResultReferences:
    """Record configured paper references in existing metadata and manifest files."""
    validated_run_dir = _validate_run_dir(run_dir)
    metadata_path = validated_run_dir / "metadata.json"
    manifest_path = validated_run_dir / "manifest.json"
    metadata = _validate_existing_json_mapping(
        metadata_path,
        field_name="metadata.json",
    )
    manifest = _validate_existing_json_mapping(
        manifest_path,
        field_name="manifest.json",
    )
    references = create_configured_paper_result_references(
        run_dir=validated_run_dir,
        paper_run_artifact_path=paper_run_artifact_path,
        paper_run_result_summary_path=paper_run_result_summary_path,
    )

    existing_paper_run = metadata.get("paper_run", {})
    if not isinstance(existing_paper_run, dict):
        raise ValueError("metadata.json paper_run must be an object when present")
    metadata["paper_run"] = {
        **existing_paper_run,
        "artifact_path": references.paper_run_artifact_path,
        "result_summary_path": references.paper_run_result_summary_path,
    }

    existing_artifacts = manifest.get("artifacts")
    if not isinstance(existing_artifacts, dict):
        raise ValueError("manifest.json artifacts must be an object")
    manifest["artifacts"] = {
        **existing_artifacts,
        "paper_run_artifact": references.paper_run_artifact_path,
        "paper_run_result_summary": references.paper_run_result_summary_path,
    }

    _write_json(metadata_path, metadata)
    _write_json(manifest_path, manifest)
    return references
