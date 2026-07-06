"""Comparison helpers for saved local experiment artifacts."""

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import pandas as pd


def _read_json_object(path: Path, artifact_name: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"unable to read {artifact_name}: {path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{artifact_name} must contain a JSON object: {path}")
    return value


def compare_experiment_runs(
    run_dirs: Iterable[str | Path],
) -> pd.DataFrame:
    """Combine existing per-symbol metrics from saved experiment runs."""
    run_paths = [Path(run_dir) for run_dir in run_dirs]
    if len(run_paths) < 2:
        raise ValueError("at least two run directories are required")

    rows: list[dict[str, Any]] = []
    for run_dir in run_paths:
        manifest_path = run_dir / "manifest.json"
        if not manifest_path.is_file():
            raise ValueError(f"manifest.json is missing: {manifest_path}")
        manifest = _read_json_object(manifest_path, "manifest.json")
        if manifest.get("schema_version") != 1:
            raise ValueError(f"unsupported manifest schema_version: {manifest_path}")

        artifacts = manifest.get("artifacts")
        metrics_artifact = (
            artifacts.get("metrics") if isinstance(artifacts, Mapping) else None
        )
        if not isinstance(metrics_artifact, str) or not metrics_artifact:
            raise ValueError(f"manifest artifacts.metrics is missing: {manifest_path}")

        metrics_relative_path = Path(metrics_artifact)
        if metrics_relative_path.is_absolute():
            raise ValueError("manifest artifacts.metrics must be a relative path")
        if ".." in metrics_relative_path.parts:
            raise ValueError("manifest artifacts.metrics must not contain '..'")

        metrics_path = run_dir / metrics_relative_path
        if not metrics_path.is_file():
            raise ValueError(f"metrics artifact is missing: {metrics_path}")
        metrics_artifact_data = _read_json_object(metrics_path, "metrics artifact")
        if metrics_artifact_data.get("schema_version") != 1:
            raise ValueError(f"unsupported metrics schema_version: {metrics_path}")

        metric_records = metrics_artifact_data.get("metrics")
        if not isinstance(metric_records, list) or not metric_records:
            raise ValueError(f"metrics records must not be empty: {metrics_path}")

        identity = {
            "run_id": manifest.get("run_id"),
            "experiment_name": manifest.get("experiment_name"),
            "strategy": manifest.get("strategy"),
        }
        for record in metric_records:
            if not isinstance(record, Mapping):
                raise ValueError(f"metrics records must be JSON objects: {metrics_path}")
            rows.append({**identity, **record})

    return pd.DataFrame(rows)
