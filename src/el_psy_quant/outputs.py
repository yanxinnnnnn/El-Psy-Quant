"""Deterministic local output paths for future experiment artifacts."""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class ExperimentOutputLayout:
    """Paths reserved for one local experiment run."""

    root_dir: Path
    experiment_dir: Path
    run_dir: Path
    config_path: Path
    metadata_path: Path
    results_dir: Path
    logs_dir: Path


def _slugify_experiment_name(experiment_name: str) -> str:
    if not isinstance(experiment_name, str) or not experiment_name.strip():
        raise ValueError("experiment_name must be a non-empty string")
    slug = re.sub(r"[\W_]+", "-", experiment_name.strip().lower()).strip("-")
    if not slug:
        raise ValueError("experiment_name must contain an alphanumeric character")
    return slug


def _validate_run_id(run_id: str) -> str:
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("run_id must be a non-empty string")
    if re.fullmatch(r"[A-Za-z0-9_-]+", run_id) is None:
        raise ValueError(
            "run_id may contain only ASCII letters, digits, underscores, and hyphens"
        )
    return run_id


def create_experiment_output_layout(
    output_root: str | Path,
    experiment_name: str,
    run_id: str | None = None,
) -> ExperimentOutputLayout:
    """Create local output directories and return their reserved paths."""
    root_dir = Path(output_root)
    experiment_dir = root_dir / _slugify_experiment_name(experiment_name)
    validated_run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        if run_id is None
        else _validate_run_id(run_id)
    )
    run_dir = experiment_dir / validated_run_id
    results_dir = run_dir / "results"
    logs_dir = run_dir / "logs"

    results_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    return ExperimentOutputLayout(
        root_dir=root_dir,
        experiment_dir=experiment_dir,
        run_dir=run_dir,
        config_path=run_dir / "config.yaml",
        metadata_path=run_dir / "metadata.json",
        results_dir=results_dir,
        logs_dir=logs_dir,
    )
