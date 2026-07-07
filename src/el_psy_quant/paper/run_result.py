"""Immutable paper run result summary boundary."""

from dataclasses import dataclass
from pathlib import Path

from el_psy_quant.paper.artifact import PaperTradingArtifact
from el_psy_quant.paper.audit import PaperTradingArtifactAuditSummary
from el_psy_quant.paper.run_request import (
    PAPER_RUN_REQUEST_SCHEMA_VERSION,
    PaperRunRequest,
)

PAPER_RUN_RESULT_SUMMARY_SCHEMA_VERSION = 1


def _validate_request(request: PaperRunRequest) -> PaperRunRequest:
    if not isinstance(request, PaperRunRequest):
        raise ValueError("request must be a PaperRunRequest")
    return request


def _validate_artifact(artifact: PaperTradingArtifact) -> PaperTradingArtifact:
    if not isinstance(artifact, PaperTradingArtifact):
        raise ValueError("artifact must be a PaperTradingArtifact")
    return artifact


def _normalize_artifact_path(artifact_path: str | Path) -> str:
    if not isinstance(artifact_path, str | Path):
        raise ValueError("artifact_path must be a str or pathlib.Path")
    if isinstance(artifact_path, str) and not artifact_path.strip():
        raise ValueError("artifact_path must not be empty")
    return str(Path(artifact_path))


def _validate_audit_summary(
    audit_summary: PaperTradingArtifactAuditSummary,
) -> PaperTradingArtifactAuditSummary:
    if not isinstance(audit_summary, PaperTradingArtifactAuditSummary):
        raise ValueError("audit_summary must be a PaperTradingArtifactAuditSummary")
    return audit_summary


def _validate_artifact_audit_identity(
    artifact: PaperTradingArtifact,
    audit_summary: PaperTradingArtifactAuditSummary,
) -> None:
    artifact_payload = artifact.to_dict()
    audit_payload = audit_summary.to_dict()

    if (
        artifact_payload["schema_version"] != audit_payload["schema_version"]
        or artifact_payload["created_timestamp"] != audit_payload["created_timestamp"]
    ):
        raise ValueError("audit_summary must match artifact identity")


@dataclass(frozen=True)
class PaperRunResultSummary:
    """Immutable compact summary for one local paper run result."""

    request: PaperRunRequest
    artifact: PaperTradingArtifact
    artifact_path: str | Path
    audit_summary: PaperTradingArtifactAuditSummary

    def __post_init__(self) -> None:
        object.__setattr__(self, "request", _validate_request(self.request))
        object.__setattr__(self, "artifact", _validate_artifact(self.artifact))
        object.__setattr__(
            self,
            "artifact_path",
            _normalize_artifact_path(self.artifact_path),
        )
        object.__setattr__(
            self,
            "audit_summary",
            _validate_audit_summary(self.audit_summary),
        )
        _validate_artifact_audit_identity(self.artifact, self.audit_summary)

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible paper run result summary."""
        artifact_payload = self.artifact.to_dict()
        audit_payload = self.audit_summary.to_dict()

        return {
            "schema_version": PAPER_RUN_RESULT_SUMMARY_SCHEMA_VERSION,
            "run_id": self.request.run_id,
            "request": {
                "schema_version": PAPER_RUN_REQUEST_SCHEMA_VERSION,
                "created_timestamp": self.request.created_timestamp.isoformat(),
            },
            "artifact": {
                "schema_version": artifact_payload["schema_version"],
                "created_timestamp": artifact_payload["created_timestamp"],
                "path": self.artifact_path,
            },
            "audit": audit_payload,
        }


def create_paper_run_result_summary(
    *,
    request: PaperRunRequest,
    artifact: PaperTradingArtifact,
    artifact_path: str | Path,
    audit_summary: PaperTradingArtifactAuditSummary,
) -> PaperRunResultSummary:
    """Create a compact summary for one explicit local paper run result."""
    return PaperRunResultSummary(
        request=request,
        artifact=artifact,
        artifact_path=artifact_path,
        audit_summary=audit_summary,
    )
