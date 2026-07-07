"""File contract for saved paper trading artifacts."""

from el_psy_quant.paper.artifact import (
    PAPER_TRADING_ARTIFACT_SCHEMA_VERSION,
    PaperTradingArtifact,
)

PAPER_TRADING_ARTIFACT_FILE_NAME = "paper_trading_artifact.json"
PAPER_TRADING_ARTIFACT_FILE_ENCODING = "utf-8"
PAPER_TRADING_ARTIFACT_FILE_TOP_LEVEL_KEYS = (
    "schema_version",
    "created_timestamp",
    "starting_account_state",
    "ending_account_state",
    "orders",
    "fills",
    "session_summary",
)


def create_paper_trading_artifact_file_payload(
    artifact: PaperTradingArtifact,
) -> dict[str, object]:
    """Return the deterministic JSON-compatible paper artifact file payload."""
    if not isinstance(artifact, PaperTradingArtifact):
        raise ValueError("artifact must be a PaperTradingArtifact")

    payload = artifact.to_dict()
    if payload["schema_version"] != PAPER_TRADING_ARTIFACT_SCHEMA_VERSION:
        raise ValueError("artifact schema_version is unsupported")
    return payload
