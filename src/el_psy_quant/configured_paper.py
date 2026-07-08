"""Configured local paper workflow runner."""

import json
from dataclasses import dataclass
from pathlib import Path

from el_psy_quant.config import (
    ExperimentConfig,
    create_paper_run_request_from_config,
)
from el_psy_quant.outputs import create_configured_paper_run_output_paths
from el_psy_quant.paper import (
    PaperRunRequest,
    PaperRunResultSummary,
    PaperTradingArtifact,
    create_paper_run_result_summary,
    create_paper_trading_artifact_audit_summary,
    create_paper_trading_artifact_file_payload,
    persist_paper_run_artifact,
    run_paper_trading_request,
)
from el_psy_quant.paper.file_contract import PAPER_TRADING_ARTIFACT_FILE_ENCODING


@dataclass(frozen=True)
class ConfiguredPaperWorkflowRunResult:
    """Result objects and paths from one configured paper workflow run."""

    request: PaperRunRequest
    artifact: PaperTradingArtifact
    result_summary: PaperRunResultSummary
    paper_run_artifact_path: Path
    paper_run_result_summary_path: Path


def _validate_config(config: ExperimentConfig) -> ExperimentConfig:
    if not isinstance(config, ExperimentConfig):
        raise ValueError("config must be an ExperimentConfig")
    if config.paper_run is None:
        raise ValueError("config.paper_run is required")
    return config


def _validate_existing_run_dir(run_dir: str | Path) -> Path:
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


def _write_result_summary_file(
    summary: PaperRunResultSummary,
    destination_path: Path,
) -> Path:
    document = json.dumps(summary.to_dict(), indent=2, allow_nan=False) + "\n"
    destination_path.write_bytes(
        document.encode(PAPER_TRADING_ARTIFACT_FILE_ENCODING)
    )
    return destination_path


def run_configured_paper_workflow(
    *,
    config: ExperimentConfig,
    run_dir: str | Path,
) -> ConfiguredPaperWorkflowRunResult:
    """Execute and persist one configured local paper workflow."""
    validated_config = _validate_config(config)
    validated_run_dir = _validate_existing_run_dir(run_dir)
    paths = create_configured_paper_run_output_paths(run_dir=validated_run_dir)

    paper_dir = paths.paper_run_artifact_path.parent
    paper_dir.mkdir(exist_ok=True)

    request = create_paper_run_request_from_config(validated_config.paper_run)
    artifact = run_paper_trading_request(request)
    artifact_path = persist_paper_run_artifact(
        artifact,
        paths.paper_run_artifact_path,
    )
    artifact_payload = create_paper_trading_artifact_file_payload(artifact)
    audit_summary = create_paper_trading_artifact_audit_summary(artifact_payload)
    result_summary = create_paper_run_result_summary(
        request=request,
        artifact=artifact,
        artifact_path=artifact_path,
        audit_summary=audit_summary,
    )
    result_summary_path = _write_result_summary_file(
        result_summary,
        paths.paper_run_result_summary_path,
    )

    return ConfiguredPaperWorkflowRunResult(
        request=request,
        artifact=artifact,
        result_summary=result_summary,
        paper_run_artifact_path=artifact_path,
        paper_run_result_summary_path=result_summary_path,
    )
