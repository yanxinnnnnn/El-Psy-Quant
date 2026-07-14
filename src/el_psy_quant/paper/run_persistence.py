"""Explicit local persistence boundary for paper run artifacts."""

from pathlib import Path

from el_psy_quant.paper.artifact import PaperTradingArtifact
from el_psy_quant.paper.writer import (
    PaperArtifactWriteMode,
    write_paper_trading_artifact_file,
)


def persist_paper_run_artifact(
    artifact: PaperTradingArtifact,
    destination_path: str | Path,
    *,
    write_mode: PaperArtifactWriteMode = "overwrite",
) -> Path:
    """Persist a paper trading artifact to an explicit local path."""
    return write_paper_trading_artifact_file(
        artifact,
        destination_path,
        write_mode=write_mode,
    )
