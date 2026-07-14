"""Local reader and top-level validation for paper trading artifact files."""

import json
from pathlib import Path
from typing import Any

from el_psy_quant.paper.artifact import PAPER_TRADING_ARTIFACT_SCHEMA_VERSION
from el_psy_quant.paper.file_contract import (
    PAPER_TRADING_ARTIFACT_FILE_ENCODING,
    PAPER_TRADING_ARTIFACT_FILE_TOP_LEVEL_KEYS,
)


def _normalize_source_path(source_path: str | Path) -> Path:
    if not isinstance(source_path, str | Path):
        raise ValueError("source_path must be a str or pathlib.Path")
    if isinstance(source_path, str) and not source_path.strip():
        raise ValueError("source_path must not be empty")

    path = Path(source_path)
    if not path.exists():
        raise ValueError("source_path file does not exist")
    if path.is_dir():
        raise ValueError("source_path must be a file path, not a directory")
    return path


def validate_paper_trading_artifact_file_payload(
    payload: object,
) -> dict[str, object]:
    """Validate the top-level paper artifact file contract."""
    if not isinstance(payload, dict):
        raise ValueError("paper artifact file payload must be a dict")

    expected_keys = set(PAPER_TRADING_ARTIFACT_FILE_TOP_LEVEL_KEYS)
    actual_keys = set(payload)
    missing_keys = expected_keys - actual_keys
    if missing_keys:
        missing = ", ".join(sorted(missing_keys))
        raise ValueError(f"paper artifact file payload missing keys: {missing}")

    extra_keys = actual_keys - expected_keys
    if extra_keys:
        extra = ", ".join(sorted(extra_keys))
        raise ValueError(f"paper artifact file payload has unexpected keys: {extra}")

    if payload["schema_version"] != PAPER_TRADING_ARTIFACT_SCHEMA_VERSION:
        raise ValueError("paper artifact file payload schema_version is unsupported")

    return {
        key: payload[key]
        for key in PAPER_TRADING_ARTIFACT_FILE_TOP_LEVEL_KEYS
    }


def read_paper_trading_artifact_file(
    source_path: str | Path,
) -> dict[str, object]:
    """Read and validate one local paper trading artifact JSON file."""
    path = _normalize_source_path(source_path)
    try:
        payload: Any = json.loads(
            path.read_text(encoding=PAPER_TRADING_ARTIFACT_FILE_ENCODING)
        )
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError("source_path must contain valid JSON") from exc

    return validate_paper_trading_artifact_file_payload(payload)
