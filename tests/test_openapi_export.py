"""Focused tests for the deterministic Web OpenAPI export boundary."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SERVER_LOCAL_ENVIRONMENT_NAMES = (
    "EL_PSY_QUANT_RESEARCH_ARTIFACT_ROOT",
    "EL_PSY_QUANT_EVIDENCE_ARTIFACT_ROOT",
    "EL_PSY_QUANT_PRODUCT_DATABASE_PATH",
    "EL_PSY_QUANT_PAPER_ARTIFACT_ROOT",
)


def test_canonical_openapi_matches_checked_in_snapshot() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/export_openapi.py", "--check"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_export_neutralizes_local_resources_and_has_no_filesystem_side_effects(
    tmp_path: Path,
) -> None:
    configured_paths = {
        name: tmp_path / name.lower() for name in SERVER_LOCAL_ENVIRONMENT_NAMES
    }
    environment = os.environ.copy()
    environment.update({name: str(path) for name, path in configured_paths.items()})

    result = subprocess.run(
        [sys.executable, "scripts/export_openapi.py", "--check"],
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert all(not path.exists() for path in configured_paths.values())
