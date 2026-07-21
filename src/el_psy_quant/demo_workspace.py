"""Validated, isolated Founder Demo Workspace installation and discovery."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Literal, cast
from uuid import UUID

import pandas as pd
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from el_psy_quant.application.artifact_index import refresh_artifact_index
from el_psy_quant.application.evidence_manifests import (
    SUPPORTED_EVIDENCE_MANIFEST_TYPES,
    get_evidence_manifest_detail,
    list_evidence_manifests,
)
from el_psy_quant.application.lifecycle_commands import (
    LifecycleTransitionProposalCommand,
    LifecycleTransitionReviewCommand,
    StrategyLifecycleStateSnapshotCommandInput,
    StrategyReviewEvidenceReferenceCommandInput,
    create_lifecycle_transition_proposal,
    record_lifecycle_transition_review,
)
from el_psy_quant.application.paper_jobs import read_paper_job_result
from el_psy_quant.application.paper_runs import (
    PaperAccountStateCommandInput,
    PaperFillCommandInput,
    PaperOrderCommandInput,
    PaperRunCommand,
    create_paper_run_request_from_command,
)
from el_psy_quant.application.portfolio_reviews import (
    create_portfolio_review_with_outcome,
    get_portfolio_review_detail,
)
from el_psy_quant.application.research_artifacts import (
    get_research_run_detail,
    list_research_runs,
)
from el_psy_quant.configured_paper import run_paper_workflow_request
from el_psy_quant.paper import (
    create_paper_run_result_summary,
    create_paper_trading_artifact_audit_summary,
    read_paper_run_result_summary_file,
    read_paper_trading_artifact_file,
    run_paper_trading_request,
    validate_paper_run_recovery_consistency,
)
from el_psy_quant.persistence import (
    SqlAlchemyPaperJobAttemptRepository,
    SqlAlchemyPaperJobRepository,
    SqlAlchemyPaperJobResultReferenceRepository,
    create_product_database_engine,
    create_product_session_factory,
    create_queued_paper_job_record,
    create_running_paper_job_attempt,
    create_paper_job_result_reference,
    prepare_paper_run_request_for_persistence,
    resolve_product_database_config,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV
from el_psy_quant.persistence.schema import (
    CURRENT_PRODUCT_SCHEMA_REVISION,
    verify_product_schema,
)
from el_psy_quant.strategies import resolve_strategy
from el_psy_quant.portfolio_review import (
    PortfolioReviewScenarioPair,
    PortfolioReviewSource,
    create_portfolio_review_analysis_artifact,
    create_portfolio_review_baseline_scenario,
    create_portfolio_review_component,
    create_portfolio_review_evidence_reference,
    create_portfolio_review_proposed_scenario,
    create_portfolio_review_scenario_pair,
    create_portfolio_review_source,
)

if TYPE_CHECKING:
    from el_psy_quant.api.portfolio_review_schemas import PortfolioReviewCreateRequest

DEMO_WORKSPACE_SOURCE_SCHEMA_VERSION = 2
DEMO_WORKSPACE_DESCRIPTOR_SCHEMA_VERSION = 2
DEMO_WORKSPACE_INSTALL_SCHEMA_VERSION = 1
DEMO_WORKSPACE_MODE = "demo"
STANDARD_WORKSPACE_MODE = "standard"
WORKSPACE_MODE_ENV = "EL_PSY_QUANT_WORKSPACE_MODE"
DEMO_WORKSPACE_ROOT_ENV = "EL_PSY_QUANT_DEMO_WORKSPACE_ROOT"
WORKSPACE_MANIFEST_FILE_NAME = "workspace-manifest.json"
WORKSPACE_DESCRIPTOR_FILE_NAME = "workspace-descriptor.json"
INSTALL_MARKER_FILE_NAME = ".demo-workspace-install.json"
DEMO_PORTFOLIO_REVIEW_REQUEST_DIGEST = (
    "3984a311d9d623c91424b2dea428f2d1d227fe2c74b85bfb69aa9e048374c4c2"
)

_SOURCE_ROOT_DIRECTORIES = (
    "strategies",
    "research_artifacts",
    "evidence_manifests",
    "paper_artifacts",
    "lifecycle_records",
    "portfolio_reviews",
)
_SOURCE_ROOT_FILES = ("README.md", WORKSPACE_MANIFEST_FILE_NAME)
_INSTALLED_CHILDREN = (
    "research",
    "evidence",
    "paper",
    "product.sqlite3",
    WORKSPACE_DESCRIPTOR_FILE_NAME,
    INSTALL_MARKER_FILE_NAME,
)


class DemoWorkspaceError(Exception):
    """Base class for bounded demo workspace failures."""


class DemoWorkspaceSourceInvalidError(DemoWorkspaceError):
    """Raised when the versioned source dataset is invalid."""


class DemoWorkspaceTargetRefusedError(DemoWorkspaceError):
    """Raised before a non-demo or non-empty target could be changed."""


class DemoWorkspaceConflictError(DemoWorkspaceError):
    """Raised when an installed dataset conflicts with the requested source."""


class DemoWorkspaceUnavailableError(DemoWorkspaceError):
    """Raised when an installed demo workspace cannot be validated."""


class _StrictSourceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class _ResearchReferenceSource(_StrictSourceModel):
    experiment_slug: str
    run_id: str


class _EvidenceReferenceSource(_StrictSourceModel):
    manifest_type: str
    artifact_key: str


class _PaperJobSource(_StrictSourceModel):
    job_id: str
    attempt_id: str
    run_id: str
    request_relative_path: str
    submitted_timestamp: str
    started_timestamp: str
    completed_timestamp: str


class _PaperSubmissionSource(_StrictSourceModel):
    idempotency_key: str
    request_relative_path: str


class _PortfolioReviewExampleSource(_StrictSourceModel):
    create_idempotency_key: str
    request_relative_path: str


class _DemoWorkspaceSourceManifest(_StrictSourceModel):
    schema_version: Literal[2]
    dataset_id: str
    dataset_version: int
    display_name: str
    warning: str
    canonical_strategy_name: str
    research_run: _ResearchReferenceSource
    evidence_manifests: tuple[_EvidenceReferenceSource, ...]
    paper_jobs: tuple[_PaperJobSource, ...]
    comparison_candidate_job_ids: tuple[str, ...]
    lifecycle_proposal_relative_path: str
    lifecycle_review_relative_path: str
    paper_submission_example: _PaperSubmissionSource
    portfolio_review_example: _PortfolioReviewExampleSource

    @field_validator(
        "dataset_id",
        "display_name",
        "warning",
        "canonical_strategy_name",
        "lifecycle_proposal_relative_path",
        "lifecycle_review_relative_path",
    )
    @classmethod
    def require_normalized_text(cls, value: str) -> str:
        if not value or value != value.strip():
            raise ValueError("demo manifest text must be normalized")
        return value

    @field_validator("dataset_version")
    @classmethod
    def require_positive_version(cls, value: int) -> int:
        if type(value) is not int or value < 1:
            raise ValueError("dataset_version must be positive")
        return value

    @model_validator(mode="after")
    def require_coherent_journey(self) -> _DemoWorkspaceSourceManifest:
        if "DEMO" not in self.warning.upper():
            raise ValueError("demo warning must identify demo data")
        if self.dataset_version != 2:
            raise ValueError("demo dataset version must be 2")
        if len(self.paper_jobs) < 2:
            raise ValueError("at least two paper jobs are required")
        job_ids = tuple(job.job_id for job in self.paper_jobs)
        run_ids = tuple(job.run_id for job in self.paper_jobs)
        attempt_ids = tuple(job.attempt_id for job in self.paper_jobs)
        if len(set(job_ids)) != len(job_ids):
            raise ValueError("paper job IDs must be distinct")
        if len(set(run_ids)) != len(run_ids):
            raise ValueError("paper run IDs must be distinct")
        if len(set(attempt_ids)) != len(attempt_ids):
            raise ValueError("paper attempt IDs must be distinct")
        candidates = self.comparison_candidate_job_ids
        if not 2 <= len(candidates) <= 4 or len(set(candidates)) != len(candidates):
            raise ValueError("comparison candidates must contain two to four distinct IDs")
        if any(candidate not in job_ids for candidate in candidates):
            raise ValueError("comparison candidates must reference demo jobs")
        return self


@dataclass(frozen=True)
class DemoWorkspacePaths:
    """Fixed children owned by one isolated demo workspace root."""

    root: Path
    research_root: Path
    evidence_root: Path
    paper_root: Path
    database_path: Path
    descriptor_path: Path
    marker_path: Path

    @classmethod
    def from_root(cls, workspace_root: str | Path) -> DemoWorkspacePaths:
        root = _local_path(workspace_root, field_name="demo workspace root")
        return cls(
            root=root,
            research_root=root / "research",
            evidence_root=root / "evidence",
            paper_root=root / "paper",
            database_path=root / "product.sqlite3",
            descriptor_path=root / WORKSPACE_DESCRIPTOR_FILE_NAME,
            marker_path=root / INSTALL_MARKER_FILE_NAME,
        )


@dataclass(frozen=True)
class DemoWorkspaceDescriptor:
    """Path-free product navigation metadata for the guided demo."""

    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(_canonical_json(self.payload)))


@dataclass(frozen=True)
class _ValidatedDemoSource:
    root: Path
    digest: str
    manifest: _DemoWorkspaceSourceManifest
    paper_requests: tuple[object, ...]
    paper_request_payloads: tuple[dict[str, Any], ...]
    lifecycle_proposal_payload: dict[str, Any]
    lifecycle_review_payload: dict[str, Any]
    paper_submission_payload: dict[str, Any]
    portfolio_review_request: PortfolioReviewCreateRequest
    portfolio_review_source: PortfolioReviewSource
    portfolio_review_scenario_pair: PortfolioReviewScenarioPair
    descriptor: DemoWorkspaceDescriptor


@dataclass(frozen=True)
class DemoWorkspaceInstallResult:
    dataset_id: str
    dataset_version: int
    workspace_root: Path
    already_installed: bool


def resolve_workspace_mode(value: str | None = None) -> Literal["standard", "demo"]:
    """Resolve one explicit workspace mode without filesystem access."""
    configured = os.getenv(WORKSPACE_MODE_ENV) if value is None else value
    if configured is None or not configured.strip():
        return STANDARD_WORKSPACE_MODE
    normalized = configured.strip().lower()
    if normalized not in (STANDARD_WORKSPACE_MODE, DEMO_WORKSPACE_MODE):
        raise ValueError("workspace mode must be standard or demo")
    return cast(Literal["standard", "demo"], normalized)


def resolve_demo_workspace_root(
    value: str | Path | None = None,
) -> Path | None:
    """Resolve the optional demo root without touching it."""
    configured: str | Path | None = (
        os.getenv(DEMO_WORKSPACE_ROOT_ENV) if value is None else value
    )
    if configured is None or (isinstance(configured, str) and not configured.strip()):
        return None
    return _local_path(configured, field_name="demo workspace root")


def _local_path(value: str | Path, *, field_name: str) -> Path:
    if not isinstance(value, (str, Path)):
        raise ValueError(f"{field_name} must be a local path")
    text = str(value).strip()
    if not text or "://" in text:
        raise ValueError(f"{field_name} must be a local path")
    return Path(text).resolve(strict=False)


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_json_constant(_value: str) -> None:
    raise ValueError("non-standard JSON number")


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise DemoWorkspaceSourceInvalidError("demo source JSON is invalid") from exc
    if type(payload) is not dict:
        raise DemoWorkspaceSourceInvalidError("demo source JSON is invalid")
    return cast(dict[str, Any], payload)


def _exact_object(value: object, fields: set[str]) -> dict[str, Any]:
    if type(value) is not dict or set(value) != fields:
        raise DemoWorkspaceSourceInvalidError("demo source payload is invalid")
    return cast(dict[str, Any], value)


def _normalized_text(value: object) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise DemoWorkspaceSourceInvalidError("demo source text is invalid")
    return value


def _uuid(value: object) -> str:
    text = _normalized_text(value)
    try:
        parsed = UUID(text)
    except ValueError as exc:
        raise DemoWorkspaceSourceInvalidError("demo source UUID is invalid") from exc
    if str(parsed) != text:
        raise DemoWorkspaceSourceInvalidError("demo source UUID is invalid")
    return text


def _utc_timestamp(value: object) -> datetime:
    text = _normalized_text(value)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DemoWorkspaceSourceInvalidError("demo timestamp is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise DemoWorkspaceSourceInvalidError("demo timestamp must be UTC")
    return parsed.astimezone(timezone.utc)


def _relative_source_path(root: Path, relative_path: str) -> Path:
    text = _normalized_text(relative_path)
    if "\\" in text or ":" in text:
        raise DemoWorkspaceSourceInvalidError("demo source path is invalid")
    pure = PurePosixPath(text)
    if pure.is_absolute() or any(part in ("", ".", "..") for part in pure.parts):
        raise DemoWorkspaceSourceInvalidError("demo source path is invalid")
    candidate = root.joinpath(*pure.parts)
    try:
        if candidate.is_symlink():
            raise DemoWorkspaceSourceInvalidError("demo source path is invalid")
        resolved = candidate.resolve(strict=True)
        if not resolved.is_file() or not resolved.is_relative_to(root):
            raise DemoWorkspaceSourceInvalidError("demo source path is invalid")
    except DemoWorkspaceSourceInvalidError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise DemoWorkspaceSourceInvalidError("demo source path is invalid") from exc
    return resolved


def _source_digest(root: Path) -> str:
    digest = hashlib.sha256()
    try:
        entries = tuple(root.rglob("*"))
        if any(path.is_symlink() for path in entries):
            raise DemoWorkspaceSourceInvalidError("demo source may not use symlinks")
        files = sorted(
            (path for path in entries if path.is_file()),
            key=lambda path: path.relative_to(root).as_posix(),
        )
        for path in files:
            relative = path.relative_to(root).as_posix().encode("utf-8")
            digest.update(relative)
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    except DemoWorkspaceSourceInvalidError:
        raise
    except OSError as exc:
        raise DemoWorkspaceSourceInvalidError("demo source cannot be read") from exc
    return digest.hexdigest()


def _paper_command(payload: object) -> PaperRunCommand:
    root = _exact_object(
        payload,
        {
            "run_id",
            "created_timestamp",
            "starting_account_state",
            "ending_account_state",
            "orders",
            "fills",
        },
    )

    def account(value: object) -> PaperAccountStateCommandInput:
        item = _exact_object(
            value,
            {"timestamp", "starting_cash", "current_cash", "positions"},
        )
        if type(item["positions"]) is not dict:
            raise DemoWorkspaceSourceInvalidError("demo account positions are invalid")
        return PaperAccountStateCommandInput(
            timestamp=item["timestamp"],
            starting_cash=item["starting_cash"],
            current_cash=item["current_cash"],
            positions=cast(dict[str, object], item["positions"]),
        )

    if type(root["orders"]) is not list or type(root["fills"]) is not list:
        raise DemoWorkspaceSourceInvalidError("demo paper rows are invalid")
    orders = tuple(
        PaperOrderCommandInput(**_exact_object(
            item,
            {"order_id", "timestamp", "symbol", "side", "quantity", "status"},
        ))
        for item in root["orders"]
    )
    fills: list[PaperFillCommandInput] = []
    for item in root["fills"]:
        if type(item) is not dict or set(item) not in (
            {"timestamp", "symbol", "side", "quantity", "price"},
            {"timestamp", "symbol", "side", "quantity", "price", "order_id"},
        ):
            raise DemoWorkspaceSourceInvalidError("demo fill row is invalid")
        fills.append(PaperFillCommandInput(**cast(dict[str, object], item)))
    return PaperRunCommand(
        run_id=root["run_id"],
        created_timestamp=root["created_timestamp"],
        starting_account_state=account(root["starting_account_state"]),
        ending_account_state=account(root["ending_account_state"]),
        orders=orders,
        fills=tuple(fills),
    )


def _snapshot_command(value: object) -> StrategyLifecycleStateSnapshotCommandInput:
    item = _exact_object(
        value,
        {
            "snapshot_id",
            "strategy_id",
            "lifecycle_state",
            "rationale",
            "declared_by",
            "declared_timestamp",
            "notes",
            "warnings",
        },
    )
    return StrategyLifecycleStateSnapshotCommandInput(**item)


def _proposal_command(value: object) -> LifecycleTransitionProposalCommand:
    item = _exact_object(
        value,
        {
            "proposal_id",
            "source_snapshot",
            "target_state",
            "rationale",
            "evidence_references",
            "requested_by",
            "requested_timestamp",
            "notes",
            "warnings",
        },
    )
    if type(item["evidence_references"]) is not list:
        raise DemoWorkspaceSourceInvalidError("demo lifecycle evidence is invalid")
    evidence = tuple(
        StrategyReviewEvidenceReferenceCommandInput(
            **_exact_object(
                reference,
                {"reference_type", "reference_id", "label", "description"},
            )
        )
        for reference in item["evidence_references"]
    )
    return LifecycleTransitionProposalCommand(
        proposal_id=item["proposal_id"],
        source_snapshot=_snapshot_command(item["source_snapshot"]),
        target_state=item["target_state"],
        rationale=item["rationale"],
        evidence_references=evidence,
        requested_by=item["requested_by"],
        requested_timestamp=item["requested_timestamp"],
        notes=item["notes"],
        warnings=item["warnings"],
    )


def _review_command(value: object) -> LifecycleTransitionReviewCommand:
    item = _exact_object(
        value,
        {
            "transition_record_id",
            "proposal",
            "review_outcome",
            "rationale",
            "resulting_snapshot",
            "reviewed_by",
            "reviewed_timestamp",
            "notes",
            "warnings",
        },
    )
    return LifecycleTransitionReviewCommand(
        transition_record_id=item["transition_record_id"],
        proposal=_proposal_command(item["proposal"]),
        review_outcome=item["review_outcome"],
        rationale=item["rationale"],
        resulting_snapshot=(
            None
            if item["resulting_snapshot"] is None
            else _snapshot_command(item["resulting_snapshot"])
        ),
        reviewed_by=item["reviewed_by"],
        reviewed_timestamp=item["reviewed_timestamp"],
        notes=item["notes"],
        warnings=item["warnings"],
    )


def _portfolio_review_domain_inputs(
    command: PortfolioReviewCreateRequest,
) -> tuple[PortfolioReviewSource, PortfolioReviewScenarioPair]:
    components = tuple(
        create_portfolio_review_component(
            component_id=component.component_id,
            strategy_id=component.strategy_id,
            evidence_references=tuple(
                create_portfolio_review_evidence_reference(
                    reference_type=reference.reference_type,
                    reference_id=reference.reference_id,
                    label=reference.label,
                    description=reference.description,
                )
                for reference in component.evidence_references
            ),
            symbols=component.symbols,
            label=component.label,
            description=component.description,
        )
        for component in command.source.components
    )
    component_ids = tuple(component.component_id for component in components)
    source = create_portfolio_review_source(
        source_id=command.source.source_id,
        components=components,
        aligned_returns=pd.DataFrame(
            [
                observation.component_returns
                for observation in command.source.return_observations
            ],
            index=pd.DatetimeIndex(
                [
                    observation.timestamp
                    for observation in command.source.return_observations
                ]
            ),
            columns=component_ids,
        ),
        evaluation_frequency=command.source.evaluation_frequency,
        periods_per_year=command.source.periods_per_year,
        created_by=command.source.created_by,
        created_timestamp=command.source.created_timestamp,
        assumptions=command.source.assumptions,
        warnings=command.source.warnings,
        missing_evidence=command.source.missing_evidence,
    )
    baseline = create_portfolio_review_baseline_scenario(
        scenario_id=command.baseline_scenario.scenario_id,
        source=source,
        weights=command.baseline_scenario.weights,
        rationale=command.baseline_scenario.rationale,
        assumptions=command.baseline_scenario.assumptions,
        warnings=command.baseline_scenario.warnings,
    )
    proposed = create_portfolio_review_proposed_scenario(
        scenario_id=command.proposed_scenario.scenario_id,
        source=source,
        weights=command.proposed_scenario.weights,
        proposed_component_id=command.proposed_scenario.proposed_component_id,
        rationale=command.proposed_scenario.rationale,
        assumptions=command.proposed_scenario.assumptions,
        warnings=command.proposed_scenario.warnings,
    )
    return source, create_portfolio_review_scenario_pair(
        source=source,
        baseline=baseline,
        proposed=proposed,
    )


def _portfolio_review_reference_identities(detail: object) -> set[tuple[str, str]]:
    identities: set[tuple[str, str]] = set()
    for field_name in (
        "summary_references",
        "record_references",
        "references",
        "state_snapshot_references",
        "transition_proposal_references",
        "transition_record_references",
    ):
        for reference in getattr(detail, field_name, ()):
            identities.add((reference.reference_type, reference.reference_id))
    return identities


def _validate_portfolio_review_example(
    *,
    payload: dict[str, Any],
    manifest: _DemoWorkspaceSourceManifest,
    evidence_reference_identities: set[tuple[str, str]],
) -> tuple[PortfolioReviewCreateRequest, PortfolioReviewSource, PortfolioReviewScenarioPair]:
    from el_psy_quant.api.portfolio_review_schemas import PortfolioReviewCreateRequest

    if hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest() != (
        DEMO_PORTFOLIO_REVIEW_REQUEST_DIGEST
    ):
        raise DemoWorkspaceSourceInvalidError(
            "demo portfolio review example is invalid"
        )
    try:
        command = PortfolioReviewCreateRequest.model_validate(payload)
        source, pair = _portfolio_review_domain_inputs(command)
        analysis = create_portfolio_review_analysis_artifact(
            review_id=command.review_id,
            source=source,
            scenario_pair=pair,
            created_by=command.analysis.created_by,
            created_timestamp=command.analysis.created_timestamp,
            assumptions=command.analysis.assumptions,
            warnings=command.analysis.warnings,
            missing_evidence=command.analysis.missing_evidence,
        )
    except (TypeError, ValueError) as exc:
        raise DemoWorkspaceSourceInvalidError(
            "demo portfolio review example is invalid"
        ) from exc
    research_identity = (
        f"{manifest.research_run.experiment_slug}/{manifest.research_run.run_id}"
    )
    for component in command.source.components:
        if component.strategy_id != manifest.canonical_strategy_name:
            raise DemoWorkspaceSourceInvalidError(
                "demo portfolio review strategy is invalid"
            )
        for reference in component.evidence_references:
            identity = (reference.reference_type, reference.reference_id)
            if reference.reference_type == "research_run":
                if reference.reference_id != research_identity:
                    raise DemoWorkspaceSourceInvalidError(
                        "demo portfolio review research reference is invalid"
                    )
            elif identity not in evidence_reference_identities:
                raise DemoWorkspaceSourceInvalidError(
                    "demo portfolio review evidence reference is invalid"
                )
    if (
        command.review_id != "demo-portfolio-review-001"
        or command.source.source_id != "demo-portfolio-review-source-001"
        or command.proposed_scenario.proposed_component_id
        != "demo-msft-sleeve"
        or analysis.review_id != command.review_id
        or not any("DEMO" in warning.upper() for warning in command.source.warnings)
        or not any("DEMO" in warning.upper() for warning in command.analysis.warnings)
    ):
        raise DemoWorkspaceSourceInvalidError(
            "demo portfolio review identity is invalid"
        )
    return command, source, pair


def _descriptor_payload(
    *,
    manifest: _DemoWorkspaceSourceManifest,
    proposal_payload: dict[str, Any],
    review_payload: dict[str, Any],
    submission_payload: dict[str, Any],
    portfolio_review_payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": DEMO_WORKSPACE_DESCRIPTOR_SCHEMA_VERSION,
        "dataset_id": manifest.dataset_id,
        "dataset_version": manifest.dataset_version,
        "display_name": manifest.display_name,
        "warning": manifest.warning,
        "canonical_strategy_name": manifest.canonical_strategy_name,
        "research_run": manifest.research_run.model_dump(),
        "evidence_manifests": [item.model_dump() for item in manifest.evidence_manifests],
        "paper_jobs": [
            {"job_id": item.job_id, "run_id": item.run_id}
            for item in manifest.paper_jobs
        ],
        "comparison_candidate_job_ids": list(
            manifest.comparison_candidate_job_ids
        ),
        "lifecycle_proposal_example": proposal_payload,
        "lifecycle_review_example": review_payload,
        "paper_job_submission_example": {
            "idempotency_key": manifest.paper_submission_example.idempotency_key,
            "request": submission_payload,
        },
        "portfolio_review_example": {
            "create_idempotency_key": (
                manifest.portfolio_review_example.create_idempotency_key
            ),
            "request": portfolio_review_payload,
        },
    }


def validate_demo_workspace_source(
    source_root: str | Path,
) -> _ValidatedDemoSource:
    """Validate every source record before any target is inspected or changed."""
    root = _local_path(source_root, field_name="demo source root")
    try:
        if root.is_symlink() or not root.resolve(strict=True).is_dir():
            raise DemoWorkspaceSourceInvalidError("demo source root is invalid")
        root = root.resolve(strict=True)
        if tuple(sorted(item.name for item in root.iterdir())) != tuple(
            sorted((*_SOURCE_ROOT_DIRECTORIES, *_SOURCE_ROOT_FILES))
        ):
            raise DemoWorkspaceSourceInvalidError(
                "demo source root children are invalid"
            )
        for directory in _SOURCE_ROOT_DIRECTORIES:
            candidate = root / directory
            if candidate.is_symlink() or not candidate.is_dir():
                raise DemoWorkspaceSourceInvalidError("demo source layout is incomplete")
        manifest = _DemoWorkspaceSourceManifest.model_validate(
            _read_json_object(root / WORKSPACE_MANIFEST_FILE_NAME)
        )
        resolve_strategy(manifest.canonical_strategy_name)

        research_summaries = list_research_runs(
            artifact_root=root / "research_artifacts"
        )
        research = manifest.research_run
        if not any(
            item.experiment_slug == research.experiment_slug
            and item.run_id == research.run_id
            and item.strategy == manifest.canonical_strategy_name
            for item in research_summaries
        ):
            raise DemoWorkspaceSourceInvalidError("demo research reference is invalid")
        get_research_run_detail(
            artifact_root=root / "research_artifacts",
            experiment_slug=research.experiment_slug,
            run_id=research.run_id,
        )

        evidence_summaries = list_evidence_manifests(
            artifact_root=root / "evidence_manifests"
        )
        evidence_identities = {
            (item.manifest_type, item.artifact_key) for item in evidence_summaries
        }
        evidence_reference_identities: set[tuple[str, str]] = set()
        for reference in manifest.evidence_manifests:
            if reference.manifest_type not in SUPPORTED_EVIDENCE_MANIFEST_TYPES:
                raise DemoWorkspaceSourceInvalidError("demo evidence type is invalid")
            if (reference.manifest_type, reference.artifact_key) not in evidence_identities:
                raise DemoWorkspaceSourceInvalidError("demo evidence reference is invalid")
            evidence_detail = get_evidence_manifest_detail(
                artifact_root=root / "evidence_manifests",
                manifest_type=reference.manifest_type,
                artifact_key=reference.artifact_key,
            )
            evidence_reference_identities.update(
                _portfolio_review_reference_identities(evidence_detail)
            )

        paper_requests: list[object] = []
        paper_request_payloads: list[dict[str, Any]] = []
        for job in manifest.paper_jobs:
            _uuid(job.job_id)
            _uuid(job.attempt_id)
            submitted = _utc_timestamp(job.submitted_timestamp)
            started = _utc_timestamp(job.started_timestamp)
            completed = _utc_timestamp(job.completed_timestamp)
            if not submitted <= started <= completed:
                raise DemoWorkspaceSourceInvalidError("demo job timestamps are invalid")
            request_payload = _read_json_object(
                _relative_source_path(root, job.request_relative_path)
            )
            request = create_paper_run_request_from_command(
                command=_paper_command(request_payload)
            )
            if request.run_id != job.run_id:
                raise DemoWorkspaceSourceInvalidError("demo job run ID is invalid")
            source_paper = (
                root / "paper_artifacts" / "jobs" / job.job_id / "paper"
            )
            artifact_payload = read_paper_trading_artifact_file(
                source_paper / "paper_run_artifact.json"
            )
            summary = read_paper_run_result_summary_file(
                source_paper / "paper_run_result_summary.json"
            )
            generated = run_paper_trading_request(request).to_dict()
            generated_audit = create_paper_trading_artifact_audit_summary(generated)
            if (
                artifact_payload != generated
                or summary.run_id != request.run_id
                or summary.request_created_timestamp
                != request.created_timestamp.isoformat()
                or summary.artifact_created_timestamp != generated["created_timestamp"]
                or summary.audit_summary.to_dict() != generated_audit.to_dict()
                or Path(summary.artifact_path).name != "paper_run_artifact.json"
            ):
                raise DemoWorkspaceSourceInvalidError("demo paper output is invalid")
            paper_requests.append(request)
            paper_request_payloads.append(request_payload)

        proposal_payload = _read_json_object(
            _relative_source_path(root, manifest.lifecycle_proposal_relative_path)
        )
        review_payload = _read_json_object(
            _relative_source_path(root, manifest.lifecycle_review_relative_path)
        )
        proposal_result = create_lifecycle_transition_proposal(
            command=_proposal_command(proposal_payload)
        )
        review_result = record_lifecycle_transition_review(
            command=_review_command(review_payload)
        )
        if review_result.transition_record.proposal != proposal_result.proposal:
            raise DemoWorkspaceSourceInvalidError("demo lifecycle examples diverge")

        submission_payload = _read_json_object(
            _relative_source_path(
                root,
                manifest.paper_submission_example.request_relative_path,
            )
        )
        create_paper_run_request_from_command(command=_paper_command(submission_payload))
        if not manifest.paper_submission_example.idempotency_key.strip():
            raise DemoWorkspaceSourceInvalidError("demo idempotency example is invalid")
        portfolio_review_payload = _read_json_object(
            _relative_source_path(
                root,
                manifest.portfolio_review_example.request_relative_path,
            )
        )
        if (
            manifest.portfolio_review_example.create_idempotency_key
            != "demo-portfolio-review-create-v1"
        ):
            raise DemoWorkspaceSourceInvalidError(
                "demo portfolio review idempotency example is invalid"
            )
        (
            portfolio_review_request,
            portfolio_review_source,
            portfolio_review_scenario_pair,
        ) = _validate_portfolio_review_example(
            payload=portfolio_review_payload,
            manifest=manifest,
            evidence_reference_identities=evidence_reference_identities,
        )
        descriptor = DemoWorkspaceDescriptor(
            payload=_descriptor_payload(
                manifest=manifest,
                proposal_payload=proposal_payload,
                review_payload=review_payload,
                submission_payload=submission_payload,
                portfolio_review_payload=portfolio_review_payload,
            )
        )
        _validate_descriptor_payload(descriptor.to_dict())
        return _ValidatedDemoSource(
            root=root,
            digest=_source_digest(root),
            manifest=manifest,
            paper_requests=tuple(paper_requests),
            paper_request_payloads=tuple(paper_request_payloads),
            lifecycle_proposal_payload=proposal_payload,
            lifecycle_review_payload=review_payload,
            paper_submission_payload=submission_payload,
            portfolio_review_request=portfolio_review_request,
            portfolio_review_source=portfolio_review_source,
            portfolio_review_scenario_pair=portfolio_review_scenario_pair,
            descriptor=descriptor,
        )
    except DemoWorkspaceSourceInvalidError:
        raise
    except Exception as exc:
        raise DemoWorkspaceSourceInvalidError("demo source dataset is invalid") from exc


def _validate_descriptor_payload(payload: object) -> None:
    root = _exact_object(
        payload,
        {
            "schema_version",
            "dataset_id",
            "dataset_version",
            "display_name",
            "warning",
            "canonical_strategy_name",
            "research_run",
            "evidence_manifests",
            "paper_jobs",
            "comparison_candidate_job_ids",
            "lifecycle_proposal_example",
            "lifecycle_review_example",
            "paper_job_submission_example",
            "portfolio_review_example",
        },
    )
    if root["schema_version"] != DEMO_WORKSPACE_DESCRIPTOR_SCHEMA_VERSION:
        raise DemoWorkspaceSourceInvalidError("demo descriptor version is invalid")
    _normalized_text(root["dataset_id"])
    if type(root["dataset_version"]) is not int or root["dataset_version"] != 2:
        raise DemoWorkspaceSourceInvalidError("demo descriptor version is invalid")
    _normalized_text(root["display_name"])
    if "DEMO" not in _normalized_text(root["warning"]).upper():
        raise DemoWorkspaceSourceInvalidError("demo descriptor warning is invalid")
    resolve_strategy(_normalized_text(root["canonical_strategy_name"]))
    research = _exact_object(root["research_run"], {"experiment_slug", "run_id"})
    _normalized_text(research["experiment_slug"])
    _normalized_text(research["run_id"])
    if type(root["evidence_manifests"]) is not list or type(root["paper_jobs"]) is not list:
        raise DemoWorkspaceSourceInvalidError("demo descriptor references are invalid")
    for value in root["evidence_manifests"]:
        reference = _exact_object(value, {"manifest_type", "artifact_key"})
        if reference["manifest_type"] not in SUPPORTED_EVIDENCE_MANIFEST_TYPES:
            raise DemoWorkspaceSourceInvalidError(
                "demo descriptor evidence type is invalid"
            )
        _normalized_text(reference["artifact_key"])
    job_ids: list[str] = []
    for value in root["paper_jobs"]:
        job = _exact_object(value, {"job_id", "run_id"})
        job_ids.append(_uuid(job["job_id"]))
        _normalized_text(job["run_id"])
    if len(job_ids) < 2 or len(set(job_ids)) != len(job_ids):
        raise DemoWorkspaceSourceInvalidError("demo descriptor jobs are invalid")
    if type(root["comparison_candidate_job_ids"]) is not list:
        raise DemoWorkspaceSourceInvalidError("demo descriptor comparison is invalid")
    candidates = root["comparison_candidate_job_ids"]
    if (
        not 2 <= len(candidates) <= 4
        or len(set(candidates)) != len(candidates)
        or any(candidate not in job_ids for candidate in candidates)
    ):
        raise DemoWorkspaceSourceInvalidError("demo descriptor comparison is invalid")
    proposal = create_lifecycle_transition_proposal(
        command=_proposal_command(root["lifecycle_proposal_example"])
    )
    review = record_lifecycle_transition_review(
        command=_review_command(root["lifecycle_review_example"])
    )
    if review.transition_record.proposal != proposal.proposal:
        raise DemoWorkspaceSourceInvalidError("demo descriptor lifecycle is invalid")
    submission = _exact_object(
        root["paper_job_submission_example"], {"idempotency_key", "request"}
    )
    _normalized_text(submission["idempotency_key"])
    create_paper_run_request_from_command(command=_paper_command(submission["request"]))
    portfolio_review = _exact_object(
        root["portfolio_review_example"],
        {"create_idempotency_key", "request"},
    )
    if (
        _normalized_text(portfolio_review["create_idempotency_key"])
        != "demo-portfolio-review-create-v1"
        or type(portfolio_review["request"]) is not dict
    ):
        raise DemoWorkspaceSourceInvalidError(
            "demo descriptor portfolio review is invalid"
        )
    request_payload = cast(dict[str, Any], portfolio_review["request"])
    if hashlib.sha256(_canonical_json(request_payload).encode("utf-8")).hexdigest() != (
        DEMO_PORTFOLIO_REVIEW_REQUEST_DIGEST
    ):
        raise DemoWorkspaceSourceInvalidError(
            "demo descriptor portfolio review is invalid"
        )
    try:
        from el_psy_quant.api.portfolio_review_schemas import PortfolioReviewCreateRequest

        command = PortfolioReviewCreateRequest.model_validate(request_payload)
        source, pair = _portfolio_review_domain_inputs(command)
        create_portfolio_review_analysis_artifact(
            review_id=command.review_id,
            source=source,
            scenario_pair=pair,
            created_by=command.analysis.created_by,
            created_timestamp=command.analysis.created_timestamp,
            assumptions=command.analysis.assumptions,
            warnings=command.analysis.warnings,
            missing_evidence=command.analysis.missing_evidence,
        )
    except (TypeError, ValueError) as exc:
        raise DemoWorkspaceSourceInvalidError(
            "demo descriptor portfolio review is invalid"
        ) from exc


@contextmanager
def _database_environment(database_path: Path):
    previous = os.environ.get(PRODUCT_DATABASE_PATH_ENV)
    os.environ[PRODUCT_DATABASE_PATH_ENV] = str(database_path)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(PRODUCT_DATABASE_PATH_ENV, None)
        else:
            os.environ[PRODUCT_DATABASE_PATH_ENV] = previous


def _upgrade_database(database_path: Path, alembic_config_path: Path) -> None:
    if not alembic_config_path.is_file():
        raise DemoWorkspaceUnavailableError("Alembic configuration is unavailable")
    with _database_environment(database_path):
        alembic_command.upgrade(AlembicConfig(str(alembic_config_path)), "head")


def _populate_database(
    *, paths: DemoWorkspacePaths, source: _ValidatedDemoSource
) -> None:
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    session_factory = create_product_session_factory(engine=engine)
    try:
        refresh_artifact_index(
            session_factory=session_factory,
            research_artifact_root=paths.research_root,
            evidence_artifact_root=paths.evidence_root,
        )
        with session_factory.begin() as session:
            jobs = SqlAlchemyPaperJobRepository(session=session)
            attempts = SqlAlchemyPaperJobAttemptRepository(session=session)
            references = SqlAlchemyPaperJobResultReferenceRepository(session=session)
            for source_job, request in zip(
                source.manifest.paper_jobs,
                source.paper_requests,
                strict=True,
            ):
                submitted = _utc_timestamp(source_job.submitted_timestamp)
                started = _utc_timestamp(source_job.started_timestamp)
                completed = _utc_timestamp(source_job.completed_timestamp)
                prepared = prepare_paper_run_request_for_persistence(request)  # type: ignore[arg-type]
                queued = create_queued_paper_job_record(
                    job_id=source_job.job_id,
                    request=request,  # type: ignore[arg-type]
                    submitted_timestamp=submitted,
                )
                jobs.add(job=queued, prepared_request=prepared)
                running = jobs.transition_status(
                    job_id=source_job.job_id,
                    expected_status="queued",
                    target_status="running",
                    updated_timestamp=started,
                )
                if running is None:
                    raise DemoWorkspaceUnavailableError("demo job claim failed")
                attempt = create_running_paper_job_attempt(
                    attempt_id=source_job.attempt_id,
                    job_id=source_job.job_id,
                    attempt_number=1,
                    started_timestamp=started,
                )
                attempts.start_attempt(attempt=attempt)
                succeeded = jobs.transition_status(
                    job_id=source_job.job_id,
                    expected_status="running",
                    target_status="succeeded",
                    updated_timestamp=completed,
                )
                completed_attempt = attempts.complete_attempt(
                    attempt_id=source_job.attempt_id,
                    status="succeeded",
                    completed_timestamp=completed,
                )
                if succeeded is None or completed_attempt is None:
                    raise DemoWorkspaceUnavailableError("demo job completion failed")
                references.add(
                    reference=create_paper_job_result_reference(
                        job_id=source_job.job_id,
                        created_timestamp=completed,
                    )
                )
    finally:
        engine.dispose()


def _seed_portfolio_review(
    *,
    paths: DemoWorkspacePaths,
    source: _ValidatedDemoSource,
) -> None:
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    session_factory = create_product_session_factory(engine=engine)
    command = source.portfolio_review_request
    try:
        result = create_portfolio_review_with_outcome(
            session_factory=session_factory,
            artifact_root=paths.evidence_root,
            idempotency_key=(
                source.manifest.portfolio_review_example.create_idempotency_key
            ),
            review_id=command.review_id,
            source=source.portfolio_review_source,
            scenario_pair=source.portfolio_review_scenario_pair,
            created_by=command.analysis.created_by,
            created_timestamp=command.analysis.created_timestamp,
            assumptions=tuple(command.analysis.assumptions),
            warnings=tuple(command.analysis.warnings),
            missing_evidence=tuple(command.analysis.missing_evidence),
        )
        if (
            result.outcome != "created"
            or result.review.record.status != "awaiting_decision"
            or result.review.decision is not None
        ):
            raise DemoWorkspaceUnavailableError(
                "demo portfolio review seed is inconsistent"
            )
    finally:
        engine.dispose()


def _validate_seeded_portfolio_review(
    *,
    paths: DemoWorkspacePaths,
    source: _ValidatedDemoSource,
) -> None:
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    session_factory = create_product_session_factory(engine=engine)
    command = source.portfolio_review_request
    try:
        detail = get_portfolio_review_detail(
            session_factory=session_factory,
            artifact_root=paths.evidence_root,
            review_id=command.review_id,
        )
        replay = create_portfolio_review_with_outcome(
            session_factory=session_factory,
            artifact_root=paths.evidence_root,
            idempotency_key=(
                source.manifest.portfolio_review_example.create_idempotency_key
            ),
            review_id=command.review_id,
            source=source.portfolio_review_source,
            scenario_pair=source.portfolio_review_scenario_pair,
            created_by=command.analysis.created_by,
            created_timestamp=command.analysis.created_timestamp,
            assumptions=tuple(command.analysis.assumptions),
            warnings=tuple(command.analysis.warnings),
            missing_evidence=tuple(command.analysis.missing_evidence),
        )
        if (
            replay.outcome != "replayed"
            or detail.source.to_dict() != source.portfolio_review_source.to_dict()
            or replay.review.analysis.to_dict() != detail.analysis.to_dict()
            or replay.review.record.status != detail.record.status
            or replay.review.decision != detail.decision
        ):
            raise DemoWorkspaceUnavailableError(
                "demo portfolio review is inconsistent"
            )
    finally:
        engine.dispose()


def _populate_upgraded_demo_result_references(
    *,
    paths: DemoWorkspacePaths,
    source: _ValidatedDemoSource,
) -> None:
    """Materialize deterministic Demo references introduced by revision 0005."""
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    session_factory = create_product_session_factory(engine=engine)
    try:
        with session_factory.begin() as session:
            jobs = SqlAlchemyPaperJobRepository(session=session)
            attempts = SqlAlchemyPaperJobAttemptRepository(session=session)
            references = SqlAlchemyPaperJobResultReferenceRepository(session=session)
            installed_jobs = jobs.list()
            if tuple(job.job_id for job in installed_jobs) != tuple(
                job.job_id for job in source.manifest.paper_jobs
            ):
                raise DemoWorkspaceUnavailableError(
                    "demo upgraded job identity is inconsistent"
                )
            for source_job, installed_job in zip(
                source.manifest.paper_jobs,
                installed_jobs,
                strict=True,
            ):
                installed_attempts = attempts.list_for_job(job_id=source_job.job_id)
                if (
                    installed_job.run_id != source_job.run_id
                    or installed_job.status != "succeeded"
                    or len(installed_attempts) != 1
                    or installed_attempts[0].attempt_id != source_job.attempt_id
                    or installed_attempts[0].status != "succeeded"
                ):
                    raise DemoWorkspaceUnavailableError(
                        "demo upgraded job audit is inconsistent"
                    )
                if references.get_by_job_id(job_id=source_job.job_id) is not None:
                    raise DemoWorkspaceUnavailableError(
                        "demo upgraded result reference is inconsistent"
                    )
                references.add(
                    reference=create_paper_job_result_reference(
                        job_id=source_job.job_id,
                        created_timestamp=_utc_timestamp(
                            source_job.completed_timestamp
                        ),
                    )
                )
    finally:
        engine.dispose()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, allow_nan=False, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _retarget_staged_result_summaries(
    *,
    staging: DemoWorkspacePaths,
    target: DemoWorkspacePaths,
    source: _ValidatedDemoSource,
) -> None:
    """Bind staged summaries to their deterministic post-install absolute paths."""
    for job, request in zip(
        source.manifest.paper_jobs,
        source.paper_requests,
        strict=True,
    ):
        staging_paper = staging.paper_root / "jobs" / job.job_id / "paper"
        target_artifact = (
            target.paper_root
            / "jobs"
            / job.job_id
            / "paper"
            / "paper_run_artifact.json"
        )
        artifact = run_paper_trading_request(request)  # type: ignore[arg-type]
        artifact_payload = read_paper_trading_artifact_file(
            staging_paper / "paper_run_artifact.json"
        )
        if artifact_payload != artifact.to_dict():
            raise DemoWorkspaceUnavailableError("staged paper artifact is invalid")
        audit = create_paper_trading_artifact_audit_summary(artifact_payload)
        summary = create_paper_run_result_summary(
            request=request,  # type: ignore[arg-type]
            artifact=artifact,
            artifact_path=target_artifact,
            audit_summary=audit,
        )
        summary_path = staging_paper / "paper_run_result_summary.json"
        _write_json(summary_path, summary.to_dict())
        validate_paper_run_recovery_consistency(
            request=request,  # type: ignore[arg-type]
            artifact_payload=artifact_payload,
            summary=read_paper_run_result_summary_file(summary_path),
            expected_artifact_path=target_artifact,
        )


def _install_marker(source: _ValidatedDemoSource) -> dict[str, object]:
    return {
        "schema_version": DEMO_WORKSPACE_INSTALL_SCHEMA_VERSION,
        "dataset_id": source.manifest.dataset_id,
        "dataset_version": source.manifest.dataset_version,
        "source_digest": source.digest,
        "workspace_mode": DEMO_WORKSPACE_MODE,
    }


def _database_revision(database_path: Path) -> str:
    connection: sqlite3.Connection | None = None
    try:
        resolved = database_path.resolve(strict=True)
        if database_path.is_symlink() or not resolved.is_file():
            raise DemoWorkspaceUnavailableError("demo database is unavailable")
        connection = sqlite3.connect(
            f"{resolved.as_uri()}?mode=ro",
            uri=True,
            timeout=1.0,
        )
        revisions = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchall()
        if (
            len(revisions) != 1
            or len(revisions[0]) != 1
            or not isinstance(revisions[0][0], str)
        ):
            raise DemoWorkspaceUnavailableError(
                "demo database revision is invalid"
            )
        return revisions[0][0]
    except DemoWorkspaceUnavailableError:
        raise
    except (OSError, RuntimeError, sqlite3.Error, ValueError) as exc:
        raise DemoWorkspaceUnavailableError("demo database is unavailable") from exc
    finally:
        if connection is not None:
            try:
                connection.close()
            except sqlite3.Error as exc:
                raise DemoWorkspaceUnavailableError(
                    "demo database is unavailable"
                ) from exc


def _validate_installed_workspace(
    *, paths: DemoWorkspacePaths, source: _ValidatedDemoSource
) -> None:
    if _database_revision(paths.database_path) != CURRENT_PRODUCT_SCHEMA_REVISION:
        raise DemoWorkspaceUnavailableError("demo database schema is unavailable")
    try:
        verify_product_schema(paths.database_path)
    except Exception as exc:
        raise DemoWorkspaceUnavailableError(
            "demo database schema is unavailable"
        ) from exc
    get_research_run_detail(
        artifact_root=paths.research_root,
        experiment_slug=source.manifest.research_run.experiment_slug,
        run_id=source.manifest.research_run.run_id,
    )
    for reference in source.manifest.evidence_manifests:
        get_evidence_manifest_detail(
            artifact_root=paths.evidence_root,
            manifest_type=reference.manifest_type,
            artifact_key=reference.artifact_key,
        )
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    session_factory = create_product_session_factory(engine=engine)
    try:
        for job in source.manifest.paper_jobs:
            result = read_paper_job_result(
                session_factory=session_factory,
                job_id=job.job_id,
                paper_artifact_root=paths.paper_root,
            )
            if result.run_id != job.run_id:
                raise DemoWorkspaceUnavailableError("demo paper result is inconsistent")
    finally:
        engine.dispose()
    try:
        _validate_seeded_portfolio_review(paths=paths, source=source)
    except DemoWorkspaceUnavailableError:
        raise
    except Exception as exc:
        raise DemoWorkspaceUnavailableError(
            "demo portfolio review is unavailable"
        ) from exc
    installed_descriptor = _read_json_object(paths.descriptor_path)
    if _canonical_json(installed_descriptor) != _canonical_json(
        source.descriptor.to_dict()
    ):
        raise DemoWorkspaceUnavailableError("demo descriptor is inconsistent")


def _read_marker(path: Path) -> dict[str, Any]:
    try:
        marker = _read_json_object(path)
    except DemoWorkspaceSourceInvalidError as exc:
        raise DemoWorkspaceUnavailableError("demo install marker is invalid") from exc
    expected = {
        "schema_version",
        "dataset_id",
        "dataset_version",
        "source_digest",
        "workspace_mode",
    }
    if set(marker) != expected:
        raise DemoWorkspaceUnavailableError("demo install marker is invalid")
    if (
        marker["schema_version"] != DEMO_WORKSPACE_INSTALL_SCHEMA_VERSION
        or marker["workspace_mode"] != DEMO_WORKSPACE_MODE
        or type(marker["dataset_version"]) is not int
        or marker["dataset_version"] < 1
    ):
        raise DemoWorkspaceUnavailableError("demo install marker is invalid")
    try:
        _normalized_text(marker["dataset_id"])
    except DemoWorkspaceSourceInvalidError as exc:
        raise DemoWorkspaceUnavailableError(
            "demo install marker is invalid"
        ) from exc
    digest = marker["source_digest"]
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise DemoWorkspaceUnavailableError("demo install marker is invalid")
    return marker


def _existing_entries(root: Path) -> tuple[str, ...]:
    try:
        return tuple(sorted(item.name for item in root.iterdir()))
    except OSError as exc:
        raise DemoWorkspaceTargetRefusedError("demo target cannot be inspected") from exc


def install_demo_workspace(
    *,
    source_root: str | Path,
    workspace_root: str | Path,
    workspace_mode: str,
    alembic_config_path: str | Path,
) -> DemoWorkspaceInstallResult:
    """Install one fully validated dataset into one fixed isolated demo root."""
    if resolve_workspace_mode(workspace_mode) != DEMO_WORKSPACE_MODE:
        raise DemoWorkspaceTargetRefusedError("demo mode is required for installation")
    source = validate_demo_workspace_source(source_root)
    paths = DemoWorkspacePaths.from_root(workspace_root)
    config_path = _local_path(
        alembic_config_path, field_name="Alembic configuration path"
    )
    try:
        if paths.root.is_symlink():
            raise DemoWorkspaceTargetRefusedError("demo target may not be a symlink")
        if paths.root.exists() and not paths.root.is_dir():
            raise DemoWorkspaceTargetRefusedError("demo target must be a directory")
    except OSError as exc:
        raise DemoWorkspaceTargetRefusedError("demo target cannot be inspected") from exc

    if paths.root.exists() and _existing_entries(paths.root):
        if not paths.marker_path.is_file():
            raise DemoWorkspaceTargetRefusedError(
                "non-empty target is not an installed demo workspace"
            )
        marker = _read_marker(paths.marker_path)
        expected = _install_marker(source)
        if marker != expected:
            raise DemoWorkspaceConflictError("installed demo dataset conflicts")
        if set(_existing_entries(paths.root)) != set(_INSTALLED_CHILDREN):
            raise DemoWorkspaceTargetRefusedError(
                "installed demo workspace contains unrelated data"
            )
        prior_revision = _database_revision(paths.database_path)
        _upgrade_database(paths.database_path, config_path)
        if prior_revision == "0004_paper_job_recovery_audit":
            _populate_upgraded_demo_result_references(paths=paths, source=source)
        _validate_installed_workspace(paths=paths, source=source)
        return DemoWorkspaceInstallResult(
            dataset_id=source.manifest.dataset_id,
            dataset_version=source.manifest.dataset_version,
            workspace_root=paths.root,
            already_installed=True,
        )

    parent = paths.root.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DemoWorkspaceTargetRefusedError("demo target parent is unavailable") from exc
    staging_root = parent / f".{paths.root.name}.demo-install-staging"
    if staging_root.exists() or staging_root.is_symlink():
        raise DemoWorkspaceTargetRefusedError("demo installation staging path is occupied")
    staging = DemoWorkspacePaths.from_root(staging_root)
    created_staging = False
    removed_empty_target = False
    try:
        staging.root.mkdir()
        created_staging = True
        shutil.copytree(source.root / "research_artifacts", staging.research_root)
        shutil.copytree(source.root / "evidence_manifests", staging.evidence_root)
        staging.paper_root.mkdir()
        for job, request in zip(
            source.manifest.paper_jobs,
            source.paper_requests,
            strict=True,
        ):
            run_dir = staging.paper_root / "jobs" / job.job_id
            run_dir.mkdir(parents=True)
            run_paper_workflow_request(
                request=request,  # type: ignore[arg-type]
                run_dir=run_dir,
                output_write_mode="exclusive",
            )
        _upgrade_database(staging.database_path, config_path)
        _populate_database(paths=staging, source=source)
        _seed_portfolio_review(paths=staging, source=source)
        _write_json(staging.descriptor_path, source.descriptor.to_dict())
        _write_json(staging.marker_path, _install_marker(source))
        _validate_installed_workspace(paths=staging, source=source)
        _retarget_staged_result_summaries(
            staging=staging,
            target=paths,
            source=source,
        )

        if paths.root.exists():
            if _existing_entries(paths.root):
                raise DemoWorkspaceTargetRefusedError(
                    "demo target changed during installation"
                )
            paths.root.rmdir()
            removed_empty_target = True
        staging.root.replace(paths.root)
        created_staging = False
    except DemoWorkspaceError:
        raise
    except Exception as exc:
        raise DemoWorkspaceUnavailableError("demo installation failed") from exc
    finally:
        if created_staging and staging.root.exists():
            shutil.rmtree(staging.root, ignore_errors=True)
        if removed_empty_target and not paths.root.exists():
            paths.root.mkdir(exist_ok=True)

    return DemoWorkspaceInstallResult(
        dataset_id=source.manifest.dataset_id,
        dataset_version=source.manifest.dataset_version,
        workspace_root=paths.root,
        already_installed=False,
    )


def load_demo_workspace_descriptor(
    workspace_root: str | Path,
) -> DemoWorkspaceDescriptor:
    """Read one installed path-free descriptor only from a marked demo root."""
    paths = DemoWorkspacePaths.from_root(workspace_root)
    try:
        marker = _read_marker(paths.marker_path)
        if (
            marker.get("workspace_mode") != DEMO_WORKSPACE_MODE
            or marker.get("schema_version") != DEMO_WORKSPACE_INSTALL_SCHEMA_VERSION
        ):
            raise DemoWorkspaceUnavailableError("demo workspace is not installed")
        payload = _read_json_object(paths.descriptor_path)
        _validate_descriptor_payload(payload)
        if (
            payload.get("dataset_id") != marker.get("dataset_id")
            or payload.get("dataset_version") != marker.get("dataset_version")
        ):
            raise DemoWorkspaceUnavailableError("demo descriptor is inconsistent")
        return DemoWorkspaceDescriptor(payload=payload)
    except DemoWorkspaceUnavailableError:
        raise
    except Exception as exc:
        raise DemoWorkspaceUnavailableError("demo workspace is unavailable") from exc


def validate_installed_demo_workspace(
    workspace_root: str | Path,
) -> DemoWorkspaceDescriptor:
    """Read all descriptor-owned Demo references without changing the workspace."""
    paths = DemoWorkspacePaths.from_root(workspace_root)
    try:
        if (
            paths.root.is_symlink()
            or not paths.root.is_dir()
            or set(_existing_entries(paths.root)) != set(_INSTALLED_CHILDREN)
        ):
            raise DemoWorkspaceUnavailableError("demo workspace layout is invalid")
        root = paths.root.resolve(strict=True)
        for child in (
            paths.research_root,
            paths.evidence_root,
            paths.paper_root,
        ):
            resolved = child.resolve(strict=True)
            if child.is_symlink() or not resolved.is_dir() or not resolved.is_relative_to(root):
                raise DemoWorkspaceUnavailableError(
                    "demo workspace layout is invalid"
                )
        if paths.database_path.is_symlink():
            raise DemoWorkspaceUnavailableError("demo database schema is unavailable")
        verify_product_schema(paths.database_path)
        descriptor = load_demo_workspace_descriptor(paths.root)
        payload = descriptor.to_dict()
        research = payload["research_run"]
        get_research_run_detail(
            artifact_root=paths.research_root,
            experiment_slug=research["experiment_slug"],
            run_id=research["run_id"],
        )
        for reference in payload["evidence_manifests"]:
            get_evidence_manifest_detail(
                artifact_root=paths.evidence_root,
                manifest_type=reference["manifest_type"],
                artifact_key=reference["artifact_key"],
            )
        engine = create_product_database_engine(
            config=resolve_product_database_config(
                database_path=paths.database_path
            )
        )
        factory = create_product_session_factory(engine=engine)
        try:
            for job in payload["paper_jobs"]:
                result = read_paper_job_result(
                    session_factory=factory,
                    job_id=job["job_id"],
                    paper_artifact_root=paths.paper_root,
                )
                if result.run_id != job["run_id"]:
                    raise DemoWorkspaceUnavailableError(
                        "demo paper result is inconsistent"
                    )
            portfolio_review = payload["portfolio_review_example"]["request"]
            review = get_portfolio_review_detail(
                session_factory=factory,
                artifact_root=paths.evidence_root,
                review_id=portfolio_review["review_id"],
            )
            if (
                review.source.source_id != portfolio_review["source"]["source_id"]
                or review.analysis.proposed_component_id
                != portfolio_review["proposed_scenario"]["proposed_component_id"]
                or review.record.status
                not in ("awaiting_decision", "approved", "rejected", "deferred")
            ):
                raise DemoWorkspaceUnavailableError(
                    "demo portfolio review is inconsistent"
                )
        finally:
            engine.dispose()
        return descriptor
    except DemoWorkspaceUnavailableError:
        raise
    except Exception as exc:
        raise DemoWorkspaceUnavailableError(
            "demo workspace verification failed"
        ) from exc


__all__ = [
    "DEMO_WORKSPACE_ROOT_ENV",
    "WORKSPACE_MODE_ENV",
    "DemoWorkspaceConflictError",
    "DemoWorkspaceDescriptor",
    "DemoWorkspaceInstallResult",
    "DemoWorkspaceSourceInvalidError",
    "DemoWorkspaceTargetRefusedError",
    "DemoWorkspaceUnavailableError",
    "install_demo_workspace",
    "load_demo_workspace_descriptor",
    "resolve_demo_workspace_root",
    "resolve_workspace_mode",
    "validate_installed_demo_workspace",
    "validate_demo_workspace_source",
]
