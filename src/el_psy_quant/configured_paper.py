"""Configured local paper workflow runner."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias

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

PaperWorkflowOutputWriteMode: TypeAlias = Literal["overwrite", "exclusive"]


@dataclass(frozen=True)
class PaperWorkflowRunResult:
    """Result objects and paths from one request-driven paper workflow run."""

    request: PaperRunRequest
    artifact: PaperTradingArtifact
    result_summary: PaperRunResultSummary
    paper_run_artifact_path: Path
    paper_run_result_summary_path: Path


@dataclass(frozen=True)
class ConfiguredPaperWorkflowRunResult(PaperWorkflowRunResult):
    """Backward-compatible result from one configured paper workflow run."""


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
    *,
    output_write_mode: PaperWorkflowOutputWriteMode,
) -> Path:
    document = json.dumps(summary.to_dict(), indent=2, allow_nan=False) + "\n"
    encoded_document = document.encode(PAPER_TRADING_ARTIFACT_FILE_ENCODING)
    if output_write_mode == "overwrite":
        destination_path.write_bytes(encoded_document)
    else:
        with destination_path.open("xb") as destination:
            destination.write(encoded_document)
    return destination_path


def _validate_output_write_mode(
    output_write_mode: PaperWorkflowOutputWriteMode,
) -> PaperWorkflowOutputWriteMode:
    if output_write_mode not in ("overwrite", "exclusive"):
        raise ValueError("output_write_mode must be overwrite or exclusive")
    return output_write_mode


def run_paper_workflow_request(
    *,
    request: PaperRunRequest,
    run_dir: str | Path,
    output_write_mode: PaperWorkflowOutputWriteMode = "overwrite",
) -> PaperWorkflowRunResult:
    """Execute and persist one explicit request-driven paper workflow."""
    if type(request) is not PaperRunRequest:
        raise ValueError("request must be a PaperRunRequest")
    validated_write_mode = _validate_output_write_mode(output_write_mode)
    validated_run_dir = _validate_existing_run_dir(run_dir)
    paths = create_configured_paper_run_output_paths(run_dir=validated_run_dir)

    paper_dir = paths.paper_run_artifact_path.parent
    paper_dir.mkdir(exist_ok=True)

    artifact = run_paper_trading_request(request)
    artifact_path = persist_paper_run_artifact(
        artifact,
        paths.paper_run_artifact_path,
        write_mode=validated_write_mode,
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
        output_write_mode=validated_write_mode,
    )

    return PaperWorkflowRunResult(
        request=request,
        artifact=artifact,
        result_summary=result_summary,
        paper_run_artifact_path=artifact_path,
        paper_run_result_summary_path=result_summary_path,
    )


def run_configured_paper_workflow(
    *,
    config: ExperimentConfig,
    run_dir: str | Path,
) -> ConfiguredPaperWorkflowRunResult:
    """Execute and persist one configured local paper workflow."""
    validated_config = _validate_config(config)
    validated_run_dir = _validate_existing_run_dir(run_dir)
    request = create_paper_run_request_from_config(validated_config.paper_run)
    workflow = run_paper_workflow_request(
        request=request,
        run_dir=validated_run_dir,
    )

    return ConfiguredPaperWorkflowRunResult(
        request=workflow.request,
        artifact=workflow.artifact,
        result_summary=workflow.result_summary,
        paper_run_artifact_path=workflow.paper_run_artifact_path,
        paper_run_result_summary_path=workflow.paper_run_result_summary_path,
    )
