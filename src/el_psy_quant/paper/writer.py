"""Local writer for paper trading artifact files."""

import json
from pathlib import Path
from typing import Literal, TypeAlias

from el_psy_quant.paper.artifact import PaperTradingArtifact
from el_psy_quant.paper.file_contract import (
    PAPER_TRADING_ARTIFACT_FILE_ENCODING,
    create_paper_trading_artifact_file_payload,
)

PaperArtifactWriteMode: TypeAlias = Literal["overwrite", "exclusive"]


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


def _validate_write_mode(write_mode: PaperArtifactWriteMode) -> PaperArtifactWriteMode:
    if write_mode not in ("overwrite", "exclusive"):
        raise ValueError("write_mode must be overwrite or exclusive")
    return write_mode


def _write_document(
    *,
    path: Path,
    document: bytes,
    write_mode: PaperArtifactWriteMode,
) -> None:
    if write_mode == "overwrite":
        path.write_bytes(document)
        return
    with path.open("xb") as destination:
        destination.write(document)


def write_paper_trading_artifact_file(
    artifact: PaperTradingArtifact,
    destination_path: str | Path,
    *,
    write_mode: PaperArtifactWriteMode = "overwrite",
) -> Path:
    """Write a paper trading artifact JSON file to an explicit local path."""
    if not isinstance(artifact, PaperTradingArtifact):
        raise ValueError("artifact must be a PaperTradingArtifact")

    validated_write_mode = _validate_write_mode(write_mode)
    path = _normalize_destination_path(destination_path)
    payload = create_paper_trading_artifact_file_payload(artifact)
    document = json.dumps(payload, indent=2, allow_nan=False) + "\n"
    _write_document(
        path=path,
        document=document.encode(PAPER_TRADING_ARTIFACT_FILE_ENCODING),
        write_mode=validated_write_mode,
    )
    return path
