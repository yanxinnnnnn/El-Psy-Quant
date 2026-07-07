"""Local writer for paper trading artifact files."""

import json
from pathlib import Path

from el_psy_quant.paper.artifact import PaperTradingArtifact
from el_psy_quant.paper.file_contract import (
    PAPER_TRADING_ARTIFACT_FILE_ENCODING,
    create_paper_trading_artifact_file_payload,
)


def _normalize_destination_path(destination_path: str | Path) -> Path:
    if not isinstance(destination_path, str | Path):
        raise ValueError("destination_path must be a str or pathlib.Path")
    if isinstance(destination_path, str) and not destination_path.strip():
        raise ValueError("destination_path must not be empty")

    path = Path(destination_path)
    if path.parent != Path(".") and not path.parent.exists():
        raise ValueError("destination parent directory must already exist")
    if path.exists() and path.is_dir():
        raise ValueError("destination_path must be a file path, not a directory")
    return path


def write_paper_trading_artifact_file(
    artifact: PaperTradingArtifact,
    destination_path: str | Path,
) -> Path:
    """Write a paper trading artifact JSON file to an explicit local path."""
    if not isinstance(artifact, PaperTradingArtifact):
        raise ValueError("artifact must be a PaperTradingArtifact")

    path = _normalize_destination_path(destination_path)
    payload = create_paper_trading_artifact_file_payload(artifact)
    document = json.dumps(payload, indent=2, allow_nan=False) + "\n"
    path.write_bytes(document.encode(PAPER_TRADING_ARTIFACT_FILE_ENCODING))
    return path
