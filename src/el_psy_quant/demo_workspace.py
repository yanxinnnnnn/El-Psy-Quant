"""Validated, isolated Founder Demo Workspace installation and discovery."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timezone
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
from el_psy_quant.application.paper_accounts import (
    PaperAccountApplicationService,
)
from el_psy_quant.application.paper_execution import (
    PaperExecutionApplicationService,
)
from el_psy_quant.application.strategy_order import (
    StrategyOrderApplicationService,
)
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
from el_psy_quant.paper_account import (
    PaperMoney,
    PaperQuantity,
    rebuild_paper_account_projection,
    replay_paper_account_ledger,
)
from el_psy_quant.paper_execution import (
    PaperExecutionBasisPoints,
    create_paper_execution_policy_reference,
)
from el_psy_quant.market_time import (
    MarketDataReplayEngine,
    ReplaySession,
    TradingCalendar,
    TradingSession,
    create_market_data_event,
    create_trading_calendar,
    create_trading_session,
    sort_and_validate_trading_sessions,
)
from el_psy_quant.persistence import (
    MarketDataReplayRecord,
    SqlAlchemyMarketTimeRepository,
    SqlAlchemyPaperJobAttemptRepository,
    SqlAlchemyPaperJobRepository,
    SqlAlchemyPaperJobResultReferenceRepository,
    SqlAlchemyStrategyOrderCommandReceiptRepository,
    create_product_database_engine,
    create_product_session_factory,
    create_market_data_replay_record,
    create_queued_paper_job_record,
    create_running_paper_job_attempt,
    create_paper_job_result_reference,
    prepare_paper_run_request_for_persistence,
    resolve_product_database_config,
)
from el_psy_quant.persistence.strategy_order_records import (
    COMMAND_NAMESPACE_DERIVE_INTENT,
    COMMAND_NAMESPACE_EVALUATE_RISK,
    COMMAND_NAMESPACE_EVALUATE_SIGNAL,
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
from el_psy_quant.strategy_order import (
    OrderIntent,
    create_long_only_cash_risk_policy_reference,
    create_moving_average_crossover_runtime_reference,
)

if TYPE_CHECKING:
    from el_psy_quant.api.portfolio_review_schemas import PortfolioReviewCreateRequest

DEMO_WORKSPACE_SOURCE_SCHEMA_VERSION = 6
DEMO_WORKSPACE_DESCRIPTOR_SCHEMA_VERSION = 6
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
    "paper_accounts",
    "market_time",
    "strategy_order",
    "paper_execution",
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


class _PaperAccountExampleSource(_StrictSourceModel):
    request_relative_path: str


class _MarketTimeExampleSource(_StrictSourceModel):
    request_relative_path: str


class _StrategyOrderExampleSource(_StrictSourceModel):
    request_relative_path: str


class _PaperExecutionExampleSource(_StrictSourceModel):
    request_relative_path: str


class _DemoTradingCalendar(_StrictSourceModel):
    schema_version: Literal[1]
    id: str
    market: str
    timezone: str
    calendar_version: int
    created_at: str


class _DemoTradingSession(_StrictSourceModel):
    schema_version: Literal[1]
    id: str
    calendar_id: str
    trading_date: str
    open_time: str
    close_time: str
    session_type: str


class _DemoMarketDataEvent(_StrictSourceModel):
    schema_version: Literal[1]
    event_id: str
    instrument_id: str
    event_time: str
    event_type: str
    payload: dict[str, Any]
    source: str


class _DemoMarketTimeExpected(_StrictSourceModel):
    event_stream_digest: str
    checkpoint_status: Literal["paused"]
    checkpoint_position: int
    checkpoint_last_event_id: str
    checkpoint_current_time: str
    recovery_remaining_event_ids: tuple[str, ...]
    recovery_final_status: Literal["completed"]
    recovery_final_position: int
    recovery_last_event_id: str
    recovery_current_time: str


class _DemoMarketTimeJourney(_StrictSourceModel):
    schema_version: Literal[1]
    calendar: _DemoTradingCalendar
    sessions: tuple[_DemoTradingSession, ...]
    replay_id: str
    events: tuple[_DemoMarketDataEvent, ...]
    checkpoint_after_event_count: int
    expected: _DemoMarketTimeExpected


class _DemoStrategyRuntime(_StrictSourceModel):
    fast_window: int
    slow_window: int
    target_position_quantity: str


class _DemoStrategyCommand(_StrictSourceModel):
    idempotency_key: str
    actor: str
    created_at: str


class _DemoRiskCommand(_DemoStrategyCommand):
    maximum_order_quantity: str | None = None


class _DemoStrategyExpectedAuthority(_StrictSourceModel):
    id: str
    digest: str


class _DemoStrategyExpectedDecision(_DemoStrategyExpectedAuthority):
    outcome: Literal["allow", "reject"]
    reason_codes: tuple[str, ...]


class _DemoStrategyOrderExpected(_StrictSourceModel):
    signal: _DemoStrategyExpectedAuthority
    intent: _DemoStrategyExpectedAuthority
    allow_decision: _DemoStrategyExpectedDecision
    reject_decision: _DemoStrategyExpectedDecision


class _DemoStrategyOrderJourney(_StrictSourceModel):
    schema_version: Literal[1]
    account_id: str
    trading_session_id: str
    instrument_id: str
    runtime: _DemoStrategyRuntime
    signal: _DemoStrategyCommand
    intent: _DemoStrategyCommand
    allow_risk: _DemoRiskCommand
    reject_risk: _DemoRiskCommand
    expected: _DemoStrategyOrderExpected


class _DemoExecutionAccount(_StrictSourceModel):
    account_id: str
    display_name: str
    initial_cash: str
    idempotency_key: str
    actor: str
    created_at: str


class _DemoExecutionMarket(_StrictSourceModel):
    calendar: _DemoTradingCalendar
    session: _DemoTradingSession
    replay_id: str
    events: tuple[_DemoMarketDataEvent, ...]
    handoff_event_count: int


class _DemoExecutionRiskCommand(_DemoStrategyCommand):
    maximum_order_quantity: str | None = None
    maximum_order_notional: str | None = None


class _DemoExecutionPolicy(_StrictSourceModel):
    max_fill_quantity_per_trade_event: str | None
    slippage_bps: str
    commission_bps: str
    fee_bps: str
    buy_tax_bps: str
    sell_tax_bps: str


class _DemoExecutionCreateCommand(_DemoStrategyCommand):
    pass


class _DemoExecutionStepCommand(_DemoStrategyCommand):
    expected_execution_version: int


class _DemoExecutionExpectedAttempt(_DemoStrategyExpectedAuthority):
    result: Literal["no_fill", "fill", "risk_rejected", "boundary_rejected"]
    consumed_event_id: str | None


class _DemoExecutionExpectedFill(_DemoStrategyExpectedAuthority):
    quantity: str
    execution_price: str
    total_charges: str


class _DemoExecutionExpected(_StrictSourceModel):
    intent: _DemoStrategyExpectedAuthority
    allow_decision: _DemoStrategyExpectedAuthority
    order: _DemoStrategyExpectedAuthority | None
    status: Literal[
        "fresh_manual_candidate",
        "filled",
        "rejected",
        "partially_filled_rejected",
    ]
    attempts: tuple[_DemoExecutionExpectedAttempt, ...]
    fills: tuple[_DemoExecutionExpectedFill, ...]
    settlement_links: tuple[_DemoStrategyExpectedAuthority, ...]
    account_head_version: int
    cash_balance: str
    position_quantity: str
    aggregate_cost_basis: str
    replay_position: int
    replay_last_event_id: str


class _DemoExecutionScenario(_StrictSourceModel):
    scenario_id: str
    kind: Literal["manual", "completed", "risk_rejection", "exhaustion"]
    account: _DemoExecutionAccount
    market: _DemoExecutionMarket
    runtime: _DemoStrategyRuntime
    signal: _DemoStrategyCommand
    intent: _DemoStrategyCommand
    allow_risk: _DemoExecutionRiskCommand
    execution_policy: _DemoExecutionPolicy
    create: _DemoExecutionCreateCommand | None
    steps: tuple[_DemoExecutionStepCommand, ...]
    expected: _DemoExecutionExpected


class _DemoPaperExecutionJourney(_StrictSourceModel):
    schema_version: Literal[1]
    scenarios: tuple[_DemoExecutionScenario, ...]


class _DemoPaperAccountCreation(_StrictSourceModel):
    idempotency_key: str
    display_name: str
    base_currency: str
    initial_cash: str
    actor: str


class _DemoPaperAccountCashMovement(_StrictSourceModel):
    idempotency_key: str
    expected_account_version: int
    actor: str
    reason: str
    movement_type: str
    requested_amount: str
    effective_timestamp_utc: str


class _DemoPaperAccountPositionAdjustment(_StrictSourceModel):
    idempotency_key: str
    expected_account_version: int
    actor: str
    reason: str
    symbol: str
    adjustment_category: str
    signed_quantity_delta: str
    signed_cost_basis_delta: str
    effective_timestamp_utc: str


class _DemoPaperAccountLifecycleCommand(_StrictSourceModel):
    idempotency_key: str
    expected_account_version: int
    actor: str
    reason: str
    action: Literal["freeze", "reactivate"]


class _DemoPaperAccountEvidenceOperation(_StrictSourceModel):
    idempotency_key: str
    actor: str
    reason: str


class _DemoPaperAccountAuthorityId(_StrictSourceModel):
    kind: str
    value: str


class _DemoPaperAccountExpectedPosition(_StrictSourceModel):
    symbol: str
    quantity: str
    aggregate_cost_basis: str


class _DemoPaperAccountExpected(_StrictSourceModel):
    head_version: int
    lifecycle_status: Literal["active"]
    cash_balance: str
    event_types: tuple[str, ...]
    positions: tuple[_DemoPaperAccountExpectedPosition, ...]
    snapshot_id: str
    reconciliation_id: str


class _DemoPaperAccountJourney(_StrictSourceModel):
    schema_version: Literal[1]
    account_id: str
    creation: _DemoPaperAccountCreation
    cash_movement: _DemoPaperAccountCashMovement
    position_adjustment: _DemoPaperAccountPositionAdjustment
    lifecycle_commands: tuple[_DemoPaperAccountLifecycleCommand, ...]
    snapshot: _DemoPaperAccountEvidenceOperation
    reconciliation: _DemoPaperAccountEvidenceOperation
    authority_ids: tuple[_DemoPaperAccountAuthorityId, ...]
    recorded_timestamps: tuple[str, ...]
    expected: _DemoPaperAccountExpected


class _DemoWorkspaceSourceManifest(_StrictSourceModel):
    schema_version: Literal[6]
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
    paper_account_example: _PaperAccountExampleSource
    market_time_example: _MarketTimeExampleSource
    strategy_order_example: _StrategyOrderExampleSource
    paper_execution_example: _PaperExecutionExampleSource

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
        if self.dataset_version != 6:
            raise ValueError("demo dataset version must be 6")
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
class _ValidatedDemoMarketTime:
    journey: _DemoMarketTimeJourney
    calendar: TradingCalendar
    sessions: tuple[TradingSession, ...]
    replay: MarketDataReplayRecord
    recovered_session: ReplaySession


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
    paper_account_journey: _DemoPaperAccountJourney
    market_time: _ValidatedDemoMarketTime
    strategy_order_journey: _DemoStrategyOrderJourney
    paper_execution_journey: _DemoPaperExecutionJourney
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


def _digest(value: object) -> str:
    text = _normalized_text(value)
    if len(text) != 64 or any(
        character not in "0123456789abcdef" for character in text
    ):
        raise DemoWorkspaceSourceInvalidError("demo source digest is invalid")
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


def _validate_paper_account_journey(
    payload: dict[str, Any],
) -> _DemoPaperAccountJourney:
    try:
        journey = _DemoPaperAccountJourney.model_validate(payload)
        creation_cash = PaperMoney.parse(journey.creation.initial_cash)
        movement_amount = PaperMoney.parse(
            journey.cash_movement.requested_amount
        )
        quantity = PaperQuantity.parse(
            journey.position_adjustment.signed_quantity_delta
        )
        cost_basis = PaperMoney.parse(
            journey.position_adjustment.signed_cost_basis_delta
        )
        expected_cash = PaperMoney.parse(journey.expected.cash_balance)
        expected_positions = tuple(
            (
                item.symbol,
                PaperQuantity.parse(item.quantity).canonical,
                PaperMoney.parse(item.aggregate_cost_basis).canonical,
            )
            for item in journey.expected.positions
        )
        timestamps = tuple(
            _utc_timestamp(value) for value in journey.recorded_timestamps
        )
        _utc_timestamp(journey.cash_movement.effective_timestamp_utc)
        _utc_timestamp(
            journey.position_adjustment.effective_timestamp_utc
        )
    except (TypeError, ValueError) as exc:
        raise DemoWorkspaceSourceInvalidError(
            "demo paper account journey is invalid"
        ) from exc
    expected_kinds = (
        "paper_account",
        "paper_account_event",
        "paper_cash_entry",
        "paper_account_event",
        "paper_cash_entry",
        "paper_account_event",
        "paper_position_entry",
        "paper_account_event",
        "paper_account_event",
        "paper_account_snapshot",
        "paper_account_reconciliation",
    )
    ids = tuple((item.kind, item.value) for item in journey.authority_ids)
    expected_events = (
        "account_created",
        "cash_movement_posted",
        "position_adjustment_posted",
        "account_frozen",
        "account_reactivated",
    )
    lifecycle = journey.lifecycle_commands
    if (
        creation_cash.decimal_value < 0
        or movement_amount.decimal_value <= 0
        or quantity.decimal_value <= 0
        or cost_basis.decimal_value <= 0
        or journey.creation.base_currency.upper()
        != journey.creation.base_currency
        or journey.cash_movement.movement_type != "deposit"
        or journey.position_adjustment.adjustment_category
        != "opening_balance"
        or journey.cash_movement.expected_account_version != 1
        or journey.position_adjustment.expected_account_version != 2
        or len(lifecycle) != 2
        or (lifecycle[0].action, lifecycle[0].expected_account_version)
        != ("freeze", 3)
        or (lifecycle[1].action, lifecycle[1].expected_account_version)
        != ("reactivate", 4)
        or journey.expected.head_version != 5
        or journey.expected.event_types != expected_events
        or len(expected_positions) != 1
        or expected_cash.decimal_value
        != creation_cash.decimal_value + movement_amount.decimal_value
        or tuple(item[0] for item in ids) != expected_kinds
        or ids[0][1] != journey.account_id
        or len({item[1] for item in ids}) != len(ids)
        or ids[-2][1] != journey.expected.snapshot_id
        or ids[-1][1] != journey.expected.reconciliation_id
        or len(timestamps) != 7
        or tuple(sorted(timestamps)) != timestamps
    ):
        raise DemoWorkspaceSourceInvalidError(
            "demo paper account journey is inconsistent"
        )
    for value in (
        journey.account_id,
        journey.creation.idempotency_key,
        journey.creation.display_name,
        journey.creation.actor,
        journey.cash_movement.idempotency_key,
        journey.position_adjustment.idempotency_key,
        journey.snapshot.idempotency_key,
        journey.reconciliation.idempotency_key,
        *(item.value for item in journey.authority_ids),
    ):
        _normalized_text(value)
    return journey


def _validate_market_time_journey(
    payload: dict[str, Any],
) -> _ValidatedDemoMarketTime:
    try:
        journey = _DemoMarketTimeJourney.model_validate(payload)
        calendar_source = journey.calendar
        calendar = create_trading_calendar(
            id=calendar_source.id,
            market=calendar_source.market,
            timezone=calendar_source.timezone,
            calendar_version=calendar_source.calendar_version,
            created_at=_utc_timestamp(calendar_source.created_at),
        )
        sessions = sort_and_validate_trading_sessions(
            calendar=calendar,
            sessions=[
                create_trading_session(
                    id=item.id,
                    calendar_id=item.calendar_id,
                    trading_date=date.fromisoformat(item.trading_date),
                    open_time=_utc_timestamp(item.open_time),
                    close_time=_utc_timestamp(item.close_time),
                    session_type=item.session_type,
                )
                for item in journey.sessions
            ],
        )
        events = tuple(
            create_market_data_event(
                event_id=item.event_id,
                instrument_id=item.instrument_id,
                event_time=_utc_timestamp(item.event_time),
                event_type=item.event_type,
                payload=item.payload,
                schema_version=item.schema_version,
                source=item.source,
            )
            for item in journey.events
        )
        replay_engine = MarketDataReplayEngine(
            replay_id=journey.replay_id,
            events=events,
        )
        if tuple(event.event_id for event in replay_engine.events) != tuple(
            event.event_id for event in events
        ):
            raise ValueError("demo market-data events must use canonical order")
        if not 1 <= journey.checkpoint_after_event_count < len(events):
            raise ValueError("demo replay checkpoint must be an intermediate state")
        replay_engine.start()
        for _ in range(journey.checkpoint_after_event_count):
            replay_engine.next_event()
        replay_engine.pause()
        replay = create_market_data_replay_record(
            session=replay_engine.session,
            events=replay_engine.events,
        )
        recovery_engine = MarketDataReplayEngine(
            replay_id=replay.session.replay_id,
            events=replay.events,
            cursor=replay.session.cursor,
        )
        recovery_engine.resume()
        remaining_event_ids = tuple(
            event.event_id for event in recovery_engine.iter_remaining()
        )
    except (TypeError, ValueError) as exc:
        raise DemoWorkspaceSourceInvalidError(
            "demo market-time journey is invalid"
        ) from exc

    expected = journey.expected
    checkpoint = replay.session.cursor
    recovered = recovery_engine.session
    session_ids = tuple(item.id for item in sessions)
    if (
        len(sessions) < 2
        or len(events) < 3
        or tuple(item.id for item in journey.sessions) != session_ids
        or any(
            not any(
                session.open_time <= event.event_time < session.close_time
                for session in sessions
            )
            for event in events
        )
        or checkpoint.event_stream_digest != expected.event_stream_digest
        or checkpoint.status != expected.checkpoint_status
        or checkpoint.position != expected.checkpoint_position
        or checkpoint.last_event_id != expected.checkpoint_last_event_id
        or checkpoint.current_event_time
        != _utc_timestamp(expected.checkpoint_current_time)
        or remaining_event_ids != expected.recovery_remaining_event_ids
        or recovered.status != expected.recovery_final_status
        or recovered.cursor.position != expected.recovery_final_position
        or recovered.cursor.last_event_id != expected.recovery_last_event_id
        or recovered.current_time != _utc_timestamp(expected.recovery_current_time)
    ):
        raise DemoWorkspaceSourceInvalidError(
            "demo market-time journey is inconsistent"
        )
    return _ValidatedDemoMarketTime(
        journey=journey,
        calendar=calendar,
        sessions=sessions,
        replay=replay,
        recovered_session=recovered,
    )


def _validate_strategy_order_journey(
    payload: dict[str, Any],
    *,
    account_journey: _DemoPaperAccountJourney,
    market_time: _ValidatedDemoMarketTime,
) -> _DemoStrategyOrderJourney:
    try:
        journey = _DemoStrategyOrderJourney.model_validate(payload)
        create_moving_average_crossover_runtime_reference(
            fast_window=journey.runtime.fast_window,
            slow_window=journey.runtime.slow_window,
            target_position_quantity=PaperQuantity.parse(
                journey.runtime.target_position_quantity
            ),
        )
        command_times = tuple(
            _utc_timestamp(item.created_at)
            for item in (
                journey.signal,
                journey.intent,
                journey.allow_risk,
                journey.reject_risk,
            )
        )
        reject_limit = PaperQuantity.parse(
            cast(str, journey.reject_risk.maximum_order_quantity)
        )
    except (TypeError, ValueError) as exc:
        raise DemoWorkspaceSourceInvalidError(
            "demo strategy-to-risk journey is invalid"
        ) from exc
    expected = journey.expected
    authorities = (
        expected.signal,
        expected.intent,
        expected.allow_decision,
        expected.reject_decision,
    )
    checkpoint = market_time.replay.session.cursor
    if (
        journey.account_id != account_journey.account_id
        or journey.trading_session_id not in {
            item.id for item in market_time.sessions
        }
        or checkpoint.position < journey.runtime.slow_window
        or checkpoint.last_event_id is None
        or market_time.replay.events[checkpoint.position - 1].instrument_id
        != journey.instrument_id
        or tuple(sorted(command_times)) != command_times
        or journey.allow_risk.maximum_order_quantity is not None
        or reject_limit.decimal_value
        >= PaperQuantity.parse(
            journey.runtime.target_position_quantity
        ).decimal_value
        or expected.allow_decision.outcome != "allow"
        or expected.allow_decision.reason_codes
        or expected.reject_decision.outcome != "reject"
        or expected.reject_decision.reason_codes
        != ("maximum_order_quantity_exceeded",)
        or any(
            not item.id or len(item.digest) != 64
            for item in authorities
        )
        or len({item.id for item in authorities}) != len(authorities)
    ):
        raise DemoWorkspaceSourceInvalidError(
            "demo strategy-to-risk journey is inconsistent"
        )
    for value in (
        journey.account_id,
        journey.trading_session_id,
        journey.instrument_id,
        journey.signal.idempotency_key,
        journey.intent.idempotency_key,
        journey.allow_risk.idempotency_key,
        journey.reject_risk.idempotency_key,
        *(item.actor for item in (
            journey.signal,
            journey.intent,
            journey.allow_risk,
            journey.reject_risk,
        )),
    ):
        _normalized_text(value)
    return journey


def _execution_policy(source: _DemoExecutionPolicy):
    return create_paper_execution_policy_reference(
        max_fill_quantity_per_trade_event=(
            None
            if source.max_fill_quantity_per_trade_event is None
            else PaperQuantity.parse(source.max_fill_quantity_per_trade_event)
        ),
        slippage_bps=PaperExecutionBasisPoints.parse(source.slippage_bps),
        commission_bps=PaperExecutionBasisPoints.parse(source.commission_bps),
        fee_bps=PaperExecutionBasisPoints.parse(source.fee_bps),
        buy_tax_bps=PaperExecutionBasisPoints.parse(source.buy_tax_bps),
        sell_tax_bps=PaperExecutionBasisPoints.parse(source.sell_tax_bps),
    )


def _execution_risk_policy(source: _DemoExecutionRiskCommand):
    return create_long_only_cash_risk_policy_reference(
        maximum_order_quantity=(
            None
            if source.maximum_order_quantity is None
            else PaperQuantity.parse(source.maximum_order_quantity)
        ),
        maximum_order_notional=(
            None
            if source.maximum_order_notional is None
            else PaperMoney.parse(source.maximum_order_notional)
        ),
    )


def _validate_paper_execution_journey(
    payload: dict[str, Any],
) -> _DemoPaperExecutionJourney:
    try:
        journey = _DemoPaperExecutionJourney.model_validate(payload)
        if tuple(item.kind for item in journey.scenarios) != (
            "manual",
            "completed",
            "risk_rejection",
            "exhaustion",
        ):
            raise ValueError("the four Demo execution scenarios are required in order")
        identities = tuple(item.scenario_id for item in journey.scenarios)
        account_ids = tuple(item.account.account_id for item in journey.scenarios)
        replay_ids = tuple(item.market.replay_id for item in journey.scenarios)
        session_ids = tuple(item.market.session.id for item in journey.scenarios)
        if any(len(set(values)) != len(values) for values in (
            identities, account_ids, replay_ids, session_ids
        )):
            raise ValueError("Demo execution scenario identities must be isolated")
        command_keys: list[str] = []
        expected_ids: list[str] = []
        for scenario in journey.scenarios:
            _normalized_text(scenario.scenario_id)
            _normalized_text(scenario.account.account_id)
            PaperMoney.parse(scenario.account.initial_cash)
            _utc_timestamp(scenario.account.created_at)
            runtime_quantity = PaperQuantity.parse(
                scenario.runtime.target_position_quantity
            )
            if runtime_quantity.decimal_value <= 0:
                raise ValueError("Demo execution target quantity must be positive")
            _execution_policy(scenario.execution_policy)
            _execution_risk_policy(scenario.allow_risk)
            command_times = [
                _utc_timestamp(scenario.signal.created_at),
                _utc_timestamp(scenario.intent.created_at),
                _utc_timestamp(scenario.allow_risk.created_at),
            ]
            if scenario.create is not None:
                command_times.append(_utc_timestamp(scenario.create.created_at))
            command_times.extend(_utc_timestamp(item.created_at) for item in scenario.steps)
            if command_times != sorted(command_times):
                raise ValueError("Demo execution command timestamps must be ordered")
            if scenario.market.session.calendar_id != scenario.market.calendar.id:
                raise ValueError("Demo execution calendar/session reference mismatch")
            if not 3 <= scenario.market.handoff_event_count < len(scenario.market.events):
                raise ValueError("Demo execution handoff must leave a future event")
            event_ids = tuple(item.event_id for item in scenario.market.events)
            if len(set(event_ids)) != len(event_ids):
                raise ValueError("Demo execution event IDs must be distinct")
            if (
                scenario.expected.replay_last_event_id not in event_ids
                or any(
                    item.consumed_event_id is not None
                    and item.consumed_event_id not in event_ids
                    for item in scenario.expected.attempts
                )
                or tuple(
                    item.expected_execution_version for item in scenario.steps
                )
                != tuple(range(len(scenario.steps)))
            ):
                raise ValueError("Demo execution expected references are inconsistent")
            if scenario.kind == "manual":
                if scenario.create is not None or scenario.steps or scenario.expected.order is not None:
                    raise ValueError("manual Demo scenario must remain M34-fresh")
                if scenario.expected.status != "fresh_manual_candidate":
                    raise ValueError("manual Demo status is invalid")
            elif scenario.create is None or not scenario.steps or scenario.expected.order is None:
                raise ValueError("prebuilt Demo scenario is incomplete")
            if len(scenario.expected.attempts) != len(scenario.steps):
                raise ValueError("Demo execution Attempt expectations are incomplete")
            if len(scenario.expected.fills) != len(scenario.expected.settlement_links):
                raise ValueError("Demo execution Fill/settlement expectations diverge")
            for decimal_value in (
                scenario.expected.cash_balance,
                scenario.expected.position_quantity,
                scenario.expected.aggregate_cost_basis,
                *(item.quantity for item in scenario.expected.fills),
                *(item.execution_price for item in scenario.expected.fills),
                *(item.total_charges for item in scenario.expected.fills),
            ):
                PaperMoney.parse(decimal_value)
            for authority in (
                scenario.expected.intent,
                scenario.expected.allow_decision,
                *(() if scenario.expected.order is None else (scenario.expected.order,)),
                *scenario.expected.attempts,
                *scenario.expected.fills,
                *scenario.expected.settlement_links,
            ):
                _normalized_text(authority.id)
                _digest(authority.digest)
                if not authority.id.endswith(authority.digest):
                    raise ValueError(
                        "Demo execution authority ID/digest mismatch"
                    )
                expected_ids.append(authority.id)
            command_keys.extend((
                scenario.account.idempotency_key,
                scenario.signal.idempotency_key,
                scenario.intent.idempotency_key,
                scenario.allow_risk.idempotency_key,
                *(() if scenario.create is None else (scenario.create.idempotency_key,)),
                *(item.idempotency_key for item in scenario.steps),
            ))
        if len(set(command_keys)) != len(command_keys):
            raise ValueError("Demo execution command identities must be distinct")
        if len(set(expected_ids)) != len(expected_ids):
            raise ValueError("Demo execution expected identities must be distinct")
    except (DemoWorkspaceSourceInvalidError, TypeError, ValueError) as exc:
        raise DemoWorkspaceSourceInvalidError(
            "demo paper-execution journey is invalid"
        ) from exc
    return journey


def _descriptor_payload(
    *,
    manifest: _DemoWorkspaceSourceManifest,
    proposal_payload: dict[str, Any],
    review_payload: dict[str, Any],
    submission_payload: dict[str, Any],
    portfolio_review_payload: dict[str, Any],
    paper_account_journey: _DemoPaperAccountJourney,
    market_time: _ValidatedDemoMarketTime,
    strategy_order_journey: _DemoStrategyOrderJourney,
    paper_execution_journey: _DemoPaperExecutionJourney,
) -> dict[str, Any]:
    checkpoint = market_time.replay.session.cursor
    recovered = market_time.recovered_session.cursor
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
        "paper_account": {
            "account_id": paper_account_journey.account_id,
            "head_version": paper_account_journey.expected.head_version,
            "event_types": list(
                paper_account_journey.expected.event_types
            ),
            "snapshot_id": paper_account_journey.expected.snapshot_id,
            "reconciliation_id": (
                paper_account_journey.expected.reconciliation_id
            ),
        },
        "market_time": {
            "calendar_id": market_time.calendar.id,
            "session_ids": [item.id for item in market_time.sessions],
            "replay_id": market_time.replay.session.replay_id,
            "event_count": len(market_time.replay.events),
            "event_stream_digest": checkpoint.event_stream_digest,
            "checkpoint": {
                "status": checkpoint.status,
                "position": checkpoint.position,
                "last_event_id": checkpoint.last_event_id,
                "current_time": checkpoint.current_event_time.isoformat()
                if checkpoint.current_event_time is not None
                else None,
            },
            "recovery": {
                "remaining_event_ids": list(
                    market_time.journey.expected.recovery_remaining_event_ids
                ),
                "final_status": recovered.status,
                "final_position": recovered.position,
                "last_event_id": recovered.last_event_id,
                "current_time": recovered.current_event_time.isoformat()
                if recovered.current_event_time is not None
                else None,
            },
        },
        "strategy_order": {
            "workspace_path": "/strategy-to-risk",
            "account_id": strategy_order_journey.account_id,
            "trading_session_id": strategy_order_journey.trading_session_id,
            "instrument_id": strategy_order_journey.instrument_id,
            "runtime": strategy_order_journey.runtime.model_dump(),
            "signal": {
                **strategy_order_journey.expected.signal.model_dump(),
                "receipt": {
                    "namespace": COMMAND_NAMESPACE_EVALUATE_SIGNAL,
                    "idempotency_key": strategy_order_journey.signal.idempotency_key,
                },
            },
            "intent": {
                **strategy_order_journey.expected.intent.model_dump(),
                "receipt": {
                    "namespace": COMMAND_NAMESPACE_DERIVE_INTENT,
                    "idempotency_key": strategy_order_journey.intent.idempotency_key,
                },
            },
            "allow_decision": (
                {
                    **strategy_order_journey.expected.allow_decision.model_dump(),
                    "receipt": {
                        "namespace": COMMAND_NAMESPACE_EVALUATE_RISK,
                        "idempotency_key": (
                            strategy_order_journey.allow_risk.idempotency_key
                        ),
                    },
                }
            ),
            "reject_decision": (
                {
                    **strategy_order_journey.expected.reject_decision.model_dump(),
                    "receipt": {
                        "namespace": COMMAND_NAMESPACE_EVALUATE_RISK,
                        "idempotency_key": (
                            strategy_order_journey.reject_risk.idempotency_key
                        ),
                    },
                }
            ),
        },
        "paper_execution": _paper_execution_descriptor(paper_execution_journey),
    }


def _paper_execution_descriptor(
    journey: _DemoPaperExecutionJourney,
) -> dict[str, object]:
    by_kind = {item.kind: item for item in journey.scenarios}
    manual = by_kind["manual"]

    def order_reference(kind: str) -> dict[str, str]:
        expected = by_kind[kind].expected.order
        if expected is None:
            raise DemoWorkspaceSourceInvalidError("Demo execution Order is missing")
        return {"id": expected.id, "digest": expected.digest}

    return {
        "workspace_path": "/paper-execution",
        "manual_candidate": {
            "intent_id": manual.expected.intent.id,
            "intent_digest": manual.expected.intent.digest,
            "decision_id": manual.expected.allow_decision.id,
            "decision_digest": manual.expected.allow_decision.digest,
        },
        "policy_draft": manual.execution_policy.model_dump(),
        "completed_order": order_reference("completed"),
        "risk_rejection_order": order_reference("risk_rejection"),
        "exhaustion_order": order_reference("exhaustion"),
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
        paper_account_journey = _validate_paper_account_journey(
            _read_json_object(
                _relative_source_path(
                    root,
                    manifest.paper_account_example.request_relative_path,
                )
            )
        )
        market_time = _validate_market_time_journey(
            _read_json_object(
                _relative_source_path(
                    root,
                    manifest.market_time_example.request_relative_path,
                )
            )
        )
        strategy_order_journey = _validate_strategy_order_journey(
            _read_json_object(
                _relative_source_path(
                    root,
                    manifest.strategy_order_example.request_relative_path,
                )
            ),
            account_journey=paper_account_journey,
            market_time=market_time,
        )
        paper_execution_journey = _validate_paper_execution_journey(
            _read_json_object(
                _relative_source_path(
                    root,
                    manifest.paper_execution_example.request_relative_path,
                )
            )
        )
        descriptor = DemoWorkspaceDescriptor(
            payload=_descriptor_payload(
                manifest=manifest,
                proposal_payload=proposal_payload,
                review_payload=review_payload,
                submission_payload=submission_payload,
                portfolio_review_payload=portfolio_review_payload,
                paper_account_journey=paper_account_journey,
                market_time=market_time,
                strategy_order_journey=strategy_order_journey,
                paper_execution_journey=paper_execution_journey,
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
            paper_account_journey=paper_account_journey,
            market_time=market_time,
            strategy_order_journey=strategy_order_journey,
            paper_execution_journey=paper_execution_journey,
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
            "paper_account",
            "market_time",
            "strategy_order",
            "paper_execution",
        },
    )
    if root["schema_version"] != DEMO_WORKSPACE_DESCRIPTOR_SCHEMA_VERSION:
        raise DemoWorkspaceSourceInvalidError("demo descriptor version is invalid")
    _normalized_text(root["dataset_id"])
    if type(root["dataset_version"]) is not int or root["dataset_version"] != 6:
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
    paper_account = _exact_object(
        root["paper_account"],
        {
            "account_id",
            "head_version",
            "event_types",
            "snapshot_id",
            "reconciliation_id",
        },
    )
    _normalized_text(paper_account["account_id"])
    _normalized_text(paper_account["snapshot_id"])
    _normalized_text(paper_account["reconciliation_id"])
    if (
        type(paper_account["head_version"]) is not int
        or paper_account["head_version"] != 5
        or paper_account["event_types"]
        != [
            "account_created",
            "cash_movement_posted",
            "position_adjustment_posted",
            "account_frozen",
            "account_reactivated",
        ]
    ):
        raise DemoWorkspaceSourceInvalidError(
            "demo descriptor paper account is invalid"
        )
    market_time = _exact_object(
        root["market_time"],
        {
            "calendar_id",
            "session_ids",
            "replay_id",
            "event_count",
            "event_stream_digest",
            "checkpoint",
            "recovery",
        },
    )
    _normalized_text(market_time["calendar_id"])
    _normalized_text(market_time["replay_id"])
    session_ids = market_time["session_ids"]
    digest = market_time["event_stream_digest"]
    checkpoint = _exact_object(
        market_time["checkpoint"],
        {"status", "position", "last_event_id", "current_time"},
    )
    recovery = _exact_object(
        market_time["recovery"],
        {
            "remaining_event_ids",
            "final_status",
            "final_position",
            "last_event_id",
            "current_time",
        },
    )
    if (
        type(session_ids) is not list
        or len(session_ids) < 2
        or len(set(session_ids)) != len(session_ids)
        or any(_normalized_text(item) != item for item in session_ids)
        or type(market_time["event_count"]) is not int
        or market_time["event_count"] < 3
        or not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
        or checkpoint["status"] != "paused"
        or type(checkpoint["position"]) is not int
        or not 1 <= checkpoint["position"] < market_time["event_count"]
        or recovery["final_status"] != "completed"
        or recovery["final_position"] != market_time["event_count"]
        or type(recovery["remaining_event_ids"]) is not list
        or len(recovery["remaining_event_ids"])
        != market_time["event_count"] - checkpoint["position"]
    ):
        raise DemoWorkspaceSourceInvalidError(
            "demo descriptor market time is invalid"
        )
    for value in (
        checkpoint["last_event_id"],
        recovery["last_event_id"],
        *recovery["remaining_event_ids"],
    ):
        _normalized_text(value)
    _utc_timestamp(checkpoint["current_time"])
    _utc_timestamp(recovery["current_time"])
    strategy_order = _exact_object(
        root["strategy_order"],
        {
            "workspace_path",
            "account_id",
            "trading_session_id",
            "instrument_id",
            "runtime",
            "signal",
            "intent",
            "allow_decision",
            "reject_decision",
        },
    )
    if strategy_order["workspace_path"] != "/strategy-to-risk":
        raise DemoWorkspaceSourceInvalidError(
            "demo descriptor strategy-to-risk journey is invalid"
        )
    runtime = _exact_object(
        strategy_order["runtime"],
        {"fast_window", "slow_window", "target_position_quantity"},
    )
    try:
        create_moving_average_crossover_runtime_reference(
            fast_window=runtime["fast_window"],
            slow_window=runtime["slow_window"],
            target_position_quantity=PaperQuantity.parse(
                runtime["target_position_quantity"]
            ),
        )
    except (TypeError, ValueError) as exc:
        raise DemoWorkspaceSourceInvalidError(
            "demo descriptor strategy-to-risk journey is invalid"
        ) from exc
    for value in (
        strategy_order["account_id"],
        strategy_order["trading_session_id"],
        strategy_order["instrument_id"],
    ):
        _normalized_text(value)
    for name, outcome, reasons in (
        ("allow_decision", "allow", []),
        (
            "reject_decision",
            "reject",
            ["maximum_order_quantity_exceeded"],
        ),
    ):
        authority = _exact_object(
            strategy_order[name],
            {"id", "digest", "outcome", "reason_codes", "receipt"},
        )
        if authority["outcome"] != outcome or authority["reason_codes"] != reasons:
            raise DemoWorkspaceSourceInvalidError(
                "demo descriptor strategy-to-risk journey is invalid"
            )
        _normalized_text(authority["id"])
        _digest(authority["digest"])
    for name in ("signal", "intent"):
        authority = _exact_object(
            strategy_order[name], {"id", "digest", "receipt"}
        )
        _normalized_text(authority["id"])
        _digest(authority["digest"])
    expected_namespaces = {
        "signal": COMMAND_NAMESPACE_EVALUATE_SIGNAL,
        "intent": COMMAND_NAMESPACE_DERIVE_INTENT,
        "allow_decision": COMMAND_NAMESPACE_EVALUATE_RISK,
        "reject_decision": COMMAND_NAMESPACE_EVALUATE_RISK,
    }
    receipt_keys: set[tuple[str, str]] = set()
    for name, namespace in expected_namespaces.items():
        receipt = _exact_object(
            strategy_order[name]["receipt"],
            {"namespace", "idempotency_key"},
        )
        if receipt["namespace"] != namespace:
            raise DemoWorkspaceSourceInvalidError(
                "demo descriptor strategy-to-risk receipt is invalid"
            )
        key = _normalized_text(receipt["idempotency_key"])
        identity = (namespace, key)
        if identity in receipt_keys:
            raise DemoWorkspaceSourceInvalidError(
                "demo descriptor strategy-to-risk receipt is invalid"
            )
        receipt_keys.add(identity)
    execution = _exact_object(
        root["paper_execution"],
        {
            "workspace_path",
            "manual_candidate",
            "policy_draft",
            "completed_order",
            "risk_rejection_order",
            "exhaustion_order",
        },
    )
    if execution["workspace_path"] != "/paper-execution":
        raise DemoWorkspaceSourceInvalidError(
            "demo descriptor paper execution path is invalid"
        )
    manual = _exact_object(
        execution["manual_candidate"],
        {"intent_id", "intent_digest", "decision_id", "decision_digest"},
    )
    for field in ("intent_id", "decision_id"):
        _normalized_text(manual[field])
    for field in ("intent_digest", "decision_digest"):
        _digest(manual[field])
    policy = _DemoExecutionPolicy.model_validate(execution["policy_draft"])
    _execution_policy(policy)
    order_ids: set[str] = set()
    for name in (
        "completed_order",
        "risk_rejection_order",
        "exhaustion_order",
    ):
        reference = _exact_object(execution[name], {"id", "digest"})
        identity = _normalized_text(reference["id"])
        _digest(reference["digest"])
        if identity in order_ids:
            raise DemoWorkspaceSourceInvalidError(
                "demo descriptor paper execution Orders are invalid"
            )
        order_ids.add(identity)


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


class _DemoPaperAccountAuthority:
    def __init__(self, journey: _DemoPaperAccountJourney) -> None:
        self._ids = deque(
            (item.kind, item.value) for item in journey.authority_ids
        )
        self._timestamps = deque(
            _utc_timestamp(value) for value in journey.recorded_timestamps
        )

    def id(self, kind: str) -> str:
        if not self._ids:
            raise DemoWorkspaceUnavailableError(
                "demo paper account identity authority is exhausted"
            )
        expected_kind, value = self._ids.popleft()
        if kind != expected_kind:
            raise DemoWorkspaceUnavailableError(
                "demo paper account identity authority is inconsistent"
            )
        return value

    def clock(self) -> datetime:
        if not self._timestamps:
            raise DemoWorkspaceUnavailableError(
                "demo paper account clock authority is exhausted"
            )
        return self._timestamps.popleft()

    def require_exhausted(self) -> None:
        if self._ids or self._timestamps:
            raise DemoWorkspaceUnavailableError(
                "demo paper account authority was not fully consumed"
            )


def _apply_demo_paper_account_journey(
    *,
    service: PaperAccountApplicationService,
    journey: _DemoPaperAccountJourney,
    expect_replayed: bool,
) -> None:
    creation = journey.creation
    result = service.create_account(
        display_name=creation.display_name,
        base_currency=creation.base_currency,
        initial_cash=PaperMoney.parse(creation.initial_cash),
        creation_idempotency_key=creation.idempotency_key,
        actor=creation.actor,
    )
    if (
        result.replayed is not expect_replayed
        or result.account.account_identity.account_id != journey.account_id
    ):
        raise DemoWorkspaceUnavailableError(
            "demo paper account creation is inconsistent"
        )

    cash = journey.cash_movement
    result = service.post_cash_movement(
        account_id=journey.account_id,
        expected_account_version=cash.expected_account_version,
        command_idempotency_key=cash.idempotency_key,
        actor=cash.actor,
        reason=cash.reason,
        movement_type=cast(Any, cash.movement_type),
        requested_amount=PaperMoney.parse(cash.requested_amount),
        effective_timestamp_utc=_utc_timestamp(
            cash.effective_timestamp_utc
        ),
    )
    if result.replayed is not expect_replayed:
        raise DemoWorkspaceUnavailableError(
            "demo paper account cash movement is inconsistent"
        )

    position = journey.position_adjustment
    result = service.post_position_adjustment(
        account_id=journey.account_id,
        expected_account_version=position.expected_account_version,
        command_idempotency_key=position.idempotency_key,
        actor=position.actor,
        reason=position.reason,
        symbol=position.symbol,
        adjustment_category=position.adjustment_category,
        signed_quantity_delta=PaperQuantity.parse(
            position.signed_quantity_delta
        ),
        signed_cost_basis_delta=PaperMoney.parse(
            position.signed_cost_basis_delta
        ),
        effective_timestamp_utc=_utc_timestamp(
            position.effective_timestamp_utc
        ),
    )
    if result.replayed is not expect_replayed:
        raise DemoWorkspaceUnavailableError(
            "demo paper account position adjustment is inconsistent"
        )

    for command in journey.lifecycle_commands:
        operation = (
            service.freeze_account
            if command.action == "freeze"
            else service.reactivate_account
        )
        result = operation(
            account_id=journey.account_id,
            expected_account_version=command.expected_account_version,
            command_idempotency_key=command.idempotency_key,
            actor=command.actor,
            reason=command.reason,
        )
        if result.replayed is not expect_replayed:
            raise DemoWorkspaceUnavailableError(
                "demo paper account lifecycle is inconsistent"
            )

    detail = service.get_account_detail(account_id=journey.account_id)
    history = service.get_account_history(account_id=journey.account_id)
    replayed_state = replay_paper_account_ledger(history)
    rebuilt_projection = rebuild_paper_account_projection(history)
    expected = journey.expected
    actual_positions = tuple(
        (
            item.symbol,
            item.quantity.canonical,
            item.aggregate_cost_basis.canonical,
        )
        for item in rebuilt_projection.positions
    )
    expected_positions = tuple(
        (item.symbol, item.quantity, item.aggregate_cost_basis)
        for item in expected.positions
    )
    if (
        tuple(bundle.event.event_type for bundle in history)
        != expected.event_types
        or replayed_state.head_version != expected.head_version
        or replayed_state.lifecycle_status != expected.lifecycle_status
        or replayed_state.cash_balance.canonical != expected.cash_balance
        or actual_positions != expected_positions
        or detail.account.head_version != expected.head_version
        or detail.account.projection_status != "current"
        or detail.projection.to_dict() != rebuilt_projection.to_dict()
    ):
        raise DemoWorkspaceUnavailableError(
            "demo paper account replay or projection is inconsistent"
        )

    snapshot = service.create_snapshot(
        account_id=journey.account_id,
        expected_account_version=expected.head_version,
        expected_head_event_id=replayed_state.head_event_id,
        expected_head_chain_digest=replayed_state.head_chain_digest,
        operation_idempotency_key=journey.snapshot.idempotency_key,
        actor=journey.snapshot.actor,
        reason=journey.snapshot.reason,
    )
    if (
        snapshot.replayed is not expect_replayed
        or snapshot.snapshot.snapshot_id != expected.snapshot_id
        or snapshot.snapshot.projection.to_dict()
        != rebuilt_projection.to_dict()
    ):
        raise DemoWorkspaceUnavailableError(
            "demo paper account snapshot is inconsistent"
        )

    reconciliation = service.reconcile_projection(
        account_id=journey.account_id,
        expected_account_version=expected.head_version,
        expected_head_event_id=replayed_state.head_event_id,
        expected_head_chain_digest=replayed_state.head_chain_digest,
        operation_idempotency_key=journey.reconciliation.idempotency_key,
        actor=journey.reconciliation.actor,
        reason=journey.reconciliation.reason,
    )
    evidence = reconciliation.reconciliation
    if (
        reconciliation.replayed is not expect_replayed
        or evidence.reconciliation_id != expected.reconciliation_id
        or evidence.outcome != "matched"
        or evidence.mismatch_codes
        or evidence.authoritative_projection_digest
        != rebuilt_projection.projection_digest
        or evidence.candidate_projection_digest
        != rebuilt_projection.projection_digest
    ):
        raise DemoWorkspaceUnavailableError(
            "demo paper account reconciliation is inconsistent"
        )


def _seed_demo_paper_account(
    *,
    paths: DemoWorkspacePaths,
    source: _ValidatedDemoSource,
) -> None:
    engine = create_product_database_engine(
        config=resolve_product_database_config(
            database_path=paths.database_path
        )
    )
    authority = _DemoPaperAccountAuthority(source.paper_account_journey)
    service = PaperAccountApplicationService(
        session_factory=create_product_session_factory(engine=engine),
        id_factory=authority.id,
        clock=authority.clock,
    )
    try:
        _apply_demo_paper_account_journey(
            service=service,
            journey=source.paper_account_journey,
            expect_replayed=False,
        )
        authority.require_exhausted()
    finally:
        engine.dispose()


def _validate_seeded_demo_paper_account(
    *,
    paths: DemoWorkspacePaths,
    source: _ValidatedDemoSource,
) -> None:
    engine = create_product_database_engine(
        config=resolve_product_database_config(
            database_path=paths.database_path
        )
    )
    authority = _DemoPaperAccountAuthority(source.paper_account_journey)
    service = PaperAccountApplicationService(
        session_factory=create_product_session_factory(engine=engine),
        id_factory=authority.id,
        clock=authority.clock,
    )
    try:
        _apply_demo_paper_account_journey(
            service=service,
            journey=source.paper_account_journey,
            expect_replayed=True,
        )
        snapshot = service.get_snapshot(
            snapshot_id=source.paper_account_journey.expected.snapshot_id
        )
        reconciliation = service.get_reconciliation(
            reconciliation_id=(
                source.paper_account_journey.expected.reconciliation_id
            )
        )
        if (
            snapshot.account_id != source.paper_account_journey.account_id
            or reconciliation.account_id
            != source.paper_account_journey.account_id
        ):
            raise DemoWorkspaceUnavailableError(
                "demo paper account evidence is inconsistent"
            )
    finally:
        engine.dispose()


def _seed_demo_market_time(
    *,
    paths: DemoWorkspacePaths,
    source: _ValidatedDemoSource,
) -> None:
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    factory = create_product_session_factory(engine=engine)
    fixture = source.market_time
    try:
        with factory.begin() as session:
            repository = SqlAlchemyMarketTimeRepository(session=session)
            repository.add_calendar(calendar=fixture.calendar)
            repository.add_sessions(sessions=fixture.sessions)
            repository.add_replay(replay=fixture.replay)
    finally:
        engine.dispose()


def _validate_seeded_demo_market_time(
    *,
    paths: DemoWorkspacePaths,
    source: _ValidatedDemoSource,
) -> None:
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    factory = create_product_session_factory(engine=engine)
    fixture = source.market_time
    try:
        with factory() as session:
            repository = SqlAlchemyMarketTimeRepository(session=session)
            calendar = repository.get_calendar(
                calendar_id=fixture.calendar.id
            )
            sessions = repository.list_sessions(
                calendar_id=fixture.calendar.id
            )
            replay = repository.get_replay(
                replay_id=fixture.replay.session.replay_id
            )
        if replay is None:
            raise DemoWorkspaceUnavailableError(
                "demo market-time authority is unavailable"
            )
        if (
            calendar != fixture.calendar
            or sessions != fixture.sessions
            or replay != fixture.replay
        ):
            raise DemoWorkspaceUnavailableError(
                "demo market-time authority is inconsistent"
            )
        recovery_engine = MarketDataReplayEngine(
            replay_id=replay.session.replay_id,
            events=replay.events,
            cursor=replay.session.cursor,
        )
        recovery_engine.resume()
        remaining = tuple(
            event.event_id for event in recovery_engine.iter_remaining()
        )
        if (
            remaining
            != fixture.journey.expected.recovery_remaining_event_ids
            or recovery_engine.session != fixture.recovered_session
        ):
            raise DemoWorkspaceUnavailableError(
                "demo market-time recovery is inconsistent"
            )
        with factory() as session:
            persisted = SqlAlchemyMarketTimeRepository(
                session=session
            ).get_replay(replay_id=fixture.replay.session.replay_id)
        if persisted != fixture.replay:
            raise DemoWorkspaceUnavailableError(
                "demo market-time verification changed the checkpoint"
            )
    finally:
        engine.dispose()


def _strategy_order_policy(command: _DemoRiskCommand):
    return create_long_only_cash_risk_policy_reference(
        maximum_order_quantity=(
            None
            if command.maximum_order_quantity is None
            else PaperQuantity.parse(command.maximum_order_quantity)
        )
    )


def _seed_demo_strategy_order(
    *,
    paths: DemoWorkspacePaths,
    source: _ValidatedDemoSource,
) -> None:
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    factory = create_product_session_factory(engine=engine)
    journey = source.strategy_order_journey
    account_service = PaperAccountApplicationService(session_factory=factory)
    service = StrategyOrderApplicationService(session_factory=factory)
    checkpoint = source.market_time.replay.session.cursor
    current_event = source.market_time.replay.events[checkpoint.position - 1]
    try:
        account = account_service.get_account_detail(
            account_id=journey.account_id
        ).account
        runtime = create_moving_average_crossover_runtime_reference(
            fast_window=journey.runtime.fast_window,
            slow_window=journey.runtime.slow_window,
            target_position_quantity=PaperQuantity.parse(
                journey.runtime.target_position_quantity
            ),
        )
        signal = service.evaluate_and_store_strategy_signal(
            strategy_runtime_reference=runtime,
            calendar_id=source.market_time.calendar.id,
            expected_calendar_version=source.market_time.calendar.calendar_version,
            trading_session_id=journey.trading_session_id,
            replay_id=source.market_time.replay.session.replay_id,
            expected_event_stream_digest=checkpoint.event_stream_digest,
            expected_cursor_position=checkpoint.position,
            expected_signal_event_id=cast(str, checkpoint.last_event_id),
            expected_signal_time=current_event.event_time,
            instrument_id=journey.instrument_id,
            command_idempotency_key=journey.signal.idempotency_key,
            actor=journey.signal.actor,
            created_at=_utc_timestamp(journey.signal.created_at),
        )
        intent = service.derive_and_store_order_intent(
            signal_id=signal.result.signal_id,
            account_id=journey.account_id,
            expected_account_head_version=account.head_version,
            expected_account_head_event_id=account.head_event_id,
            expected_account_head_chain_digest=account.head_chain_digest,
            command_idempotency_key=journey.intent.idempotency_key,
            actor=journey.intent.actor,
            created_at=_utc_timestamp(journey.intent.created_at),
        )
        if type(intent.result) is not OrderIntent:
            raise DemoWorkspaceUnavailableError(
                "demo strategy-to-risk intent is not executable"
            )
        decisions = []
        for command in (journey.allow_risk, journey.reject_risk):
            decisions.append(
                service.evaluate_and_store_pre_trade_risk(
                    intent_id=intent.result.intent_id,
                    risk_policy_reference=_strategy_order_policy(command),
                    expected_account_head_version=account.head_version,
                    expected_account_head_event_id=account.head_event_id,
                    expected_account_head_chain_digest=account.head_chain_digest,
                    expected_calendar_id=source.market_time.calendar.id,
                    expected_calendar_version=(
                        source.market_time.calendar.calendar_version
                    ),
                    expected_trading_session_id=journey.trading_session_id,
                    expected_replay_id=source.market_time.replay.session.replay_id,
                    expected_event_stream_digest=checkpoint.event_stream_digest,
                    expected_cursor_position=checkpoint.position,
                    expected_current_event_id=cast(str, checkpoint.last_event_id),
                    expected_current_event_time=current_event.event_time,
                    expected_instrument_id=journey.instrument_id,
                    command_idempotency_key=command.idempotency_key,
                    actor=command.actor,
                    created_at=_utc_timestamp(command.created_at),
                )
            )
        actual = (
            (signal.result.signal_id, signal.result.signal_digest),
            (intent.result.intent_id, intent.result.intent_digest),
            (
                decisions[0].result.decision_id,
                decisions[0].result.decision_digest,
                decisions[0].result.outcome,
                decisions[0].result.reason_codes,
            ),
            (
                decisions[1].result.decision_id,
                decisions[1].result.decision_digest,
                decisions[1].result.outcome,
                decisions[1].result.reason_codes,
            ),
        )
        expected = journey.expected
        if actual != (
            (expected.signal.id, expected.signal.digest),
            (expected.intent.id, expected.intent.digest),
            (
                expected.allow_decision.id,
                expected.allow_decision.digest,
                expected.allow_decision.outcome,
                expected.allow_decision.reason_codes,
            ),
            (
                expected.reject_decision.id,
                expected.reject_decision.digest,
                expected.reject_decision.outcome,
                expected.reject_decision.reason_codes,
            ),
        ):
            raise DemoWorkspaceUnavailableError(
                "demo strategy-to-risk authority is inconsistent: "
                + repr(actual)
            )
    finally:
        engine.dispose()


def _validate_descriptor_strategy_order(
    *,
    paths: DemoWorkspacePaths,
    strategy_order: dict[str, Any],
) -> None:
    """Strictly reconstruct descriptor-owned M33 authority without writes."""
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    factory = create_product_session_factory(engine=engine)
    service = StrategyOrderApplicationService(session_factory=factory)
    try:
        signal_metadata = strategy_order["signal"]
        intent_metadata = strategy_order["intent"]
        allow_metadata = strategy_order["allow_decision"]
        reject_metadata = strategy_order["reject_decision"]
        signal = service.get_strategy_signal(signal_id=signal_metadata["id"])
        intent = service.get_order_intent(intent_id=intent_metadata["id"])
        allow = service.get_pre_trade_risk_decision(
            decision_id=allow_metadata["id"]
        )
        reject = service.get_pre_trade_risk_decision(
            decision_id=reject_metadata["id"]
        )
        if (
            signal.signal_digest != signal_metadata["digest"]
            or intent.intent_digest != intent_metadata["digest"]
            or intent.signal_reference.signal_id != signal.signal_id
            or intent.signal_reference.signal_digest != signal.signal_digest
            or allow.decision_digest != allow_metadata["digest"]
            or allow.outcome != allow_metadata["outcome"]
            or list(allow.reason_codes) != allow_metadata["reason_codes"]
            or allow.input_snapshot.intent_reference.intent_id != intent.intent_id
            or allow.input_snapshot.intent_reference.intent_digest
            != intent.intent_digest
            or reject.decision_digest != reject_metadata["digest"]
            or reject.outcome != reject_metadata["outcome"]
            or list(reject.reason_codes) != reject_metadata["reason_codes"]
            or reject.input_snapshot.intent_reference.intent_id
            != intent.intent_id
            or reject.input_snapshot.intent_reference.intent_digest
            != intent.intent_digest
            or signal not in service.list_strategy_signals(limit=200).items
            or intent not in service.list_order_intents(limit=200).items
            or allow
            not in service.list_pre_trade_risk_decisions(limit=200).items
            or reject
            not in service.list_pre_trade_risk_decisions(limit=200).items
        ):
            raise DemoWorkspaceUnavailableError(
                "demo strategy-to-risk authority is inconsistent"
            )
        receipts = (
            (signal_metadata["receipt"], signal),
            (intent_metadata["receipt"], intent),
            (allow_metadata["receipt"], allow),
            (reject_metadata["receipt"], reject),
        )
        with factory() as session:
            repository = SqlAlchemyStrategyOrderCommandReceiptRepository(
                session=session
            )
            for metadata, result in receipts:
                receipt = repository.get(
                    namespace=metadata["namespace"],
                    command_idempotency_key=metadata["idempotency_key"],
                )
                if receipt is None or repository.resolve(receipt=receipt) != result:
                    raise DemoWorkspaceUnavailableError(
                        "demo strategy-to-risk receipt is inconsistent"
                    )
    finally:
        engine.dispose()


def _validate_seeded_demo_strategy_order(
    *,
    paths: DemoWorkspacePaths,
    source: _ValidatedDemoSource,
) -> None:
    _validate_descriptor_strategy_order(
        paths=paths,
        strategy_order=source.descriptor.to_dict()["strategy_order"],
    )


class _DemoExecutionClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value


def _demo_execution_id_factory(scenario: _DemoExecutionScenario):
    counts: dict[str, int] = {}

    def identifier(kind: str) -> str:
        counts[kind] = counts.get(kind, 0) + 1
        if kind == "paper_account":
            return scenario.account.account_id
        return f"demo-{scenario.scenario_id}-{kind}-{counts[kind]}"

    return identifier


def _build_demo_execution_scenario(
    *,
    factory,
    scenario: _DemoExecutionScenario,
) -> dict[str, object]:
    account_clock = _DemoExecutionClock(_utc_timestamp(scenario.account.created_at))
    account_service = PaperAccountApplicationService(
        session_factory=factory,
        clock=account_clock,
        id_factory=_demo_execution_id_factory(scenario),
    )
    account = account_service.create_account(
        display_name=scenario.account.display_name,
        base_currency="USD",
        initial_cash=PaperMoney.parse(scenario.account.initial_cash),
        creation_idempotency_key=scenario.account.idempotency_key,
        actor=scenario.account.actor,
    ).account
    if account.account_id != scenario.account.account_id:
        raise DemoWorkspaceUnavailableError("Demo execution account ID diverged")

    market = scenario.market
    calendar = create_trading_calendar(
        id=market.calendar.id,
        market=market.calendar.market,
        timezone=market.calendar.timezone,
        calendar_version=market.calendar.calendar_version,
        created_at=_utc_timestamp(market.calendar.created_at),
    )
    trading_session = create_trading_session(
        id=market.session.id,
        calendar_id=market.session.calendar_id,
        trading_date=date.fromisoformat(market.session.trading_date),
        open_time=_utc_timestamp(market.session.open_time),
        close_time=_utc_timestamp(market.session.close_time),
        session_type=market.session.session_type,
    )
    events = tuple(
        create_market_data_event(
            event_id=item.event_id,
            instrument_id=item.instrument_id,
            event_time=_utc_timestamp(item.event_time),
            event_type=item.event_type,
            payload=item.payload,
            schema_version=item.schema_version,
            source=item.source,
        )
        for item in market.events
    )
    replay = MarketDataReplayEngine(replay_id=market.replay_id, events=events)
    replay.start()
    for _ in range(market.handoff_event_count):
        if replay.next_event() is None:
            raise DemoWorkspaceUnavailableError("Demo execution handoff exhausted")
    with factory.begin() as session:
        repository = SqlAlchemyMarketTimeRepository(session=session)
        repository.add_calendar(calendar=calendar)
        repository.add_session(session=trading_session)
        repository.add_replay(
            replay=create_market_data_replay_record(
                session=replay.session,
                events=replay.events,
            )
        )

    strategy = StrategyOrderApplicationService(session_factory=factory)
    current_event = replay.events[replay.cursor.position - 1]
    signal = strategy.evaluate_and_store_strategy_signal(
        strategy_runtime_reference=create_moving_average_crossover_runtime_reference(
            fast_window=scenario.runtime.fast_window,
            slow_window=scenario.runtime.slow_window,
            target_position_quantity=PaperQuantity.parse(
                scenario.runtime.target_position_quantity
            ),
        ),
        calendar_id=calendar.id,
        expected_calendar_version=calendar.calendar_version,
        trading_session_id=trading_session.id,
        replay_id=replay.session.replay_id,
        expected_event_stream_digest=replay.cursor.event_stream_digest,
        expected_cursor_position=replay.cursor.position,
        expected_signal_event_id=cast(str, replay.cursor.last_event_id),
        expected_signal_time=current_event.event_time,
        instrument_id=current_event.instrument_id,
        command_idempotency_key=scenario.signal.idempotency_key,
        actor=scenario.signal.actor,
        created_at=_utc_timestamp(scenario.signal.created_at),
    )
    intent = strategy.derive_and_store_order_intent(
        signal_id=signal.result.signal_id,
        account_id=account.account_id,
        expected_account_head_version=account.head_version,
        expected_account_head_event_id=account.head_event_id,
        expected_account_head_chain_digest=account.head_chain_digest,
        command_idempotency_key=scenario.intent.idempotency_key,
        actor=scenario.intent.actor,
        created_at=_utc_timestamp(scenario.intent.created_at),
    )
    if type(intent.result) is not OrderIntent:
        raise DemoWorkspaceUnavailableError("Demo execution Intent is not executable")
    decision = strategy.evaluate_and_store_pre_trade_risk(
        intent_id=intent.result.intent_id,
        risk_policy_reference=_execution_risk_policy(scenario.allow_risk),
        expected_account_head_version=account.head_version,
        expected_account_head_event_id=account.head_event_id,
        expected_account_head_chain_digest=account.head_chain_digest,
        expected_calendar_id=calendar.id,
        expected_calendar_version=calendar.calendar_version,
        expected_trading_session_id=trading_session.id,
        expected_replay_id=replay.session.replay_id,
        expected_event_stream_digest=replay.cursor.event_stream_digest,
        expected_cursor_position=replay.cursor.position,
        expected_current_event_id=cast(str, replay.cursor.last_event_id),
        expected_current_event_time=current_event.event_time,
        expected_instrument_id=current_event.instrument_id,
        command_idempotency_key=scenario.allow_risk.idempotency_key,
        actor=scenario.allow_risk.actor,
        created_at=_utc_timestamp(scenario.allow_risk.created_at),
    )
    if decision.result.outcome != "allow":
        raise DemoWorkspaceUnavailableError("Demo execution M33 handoff was rejected")

    order = None
    history = None
    create_replayed = False
    step_replayed = False
    if scenario.create is not None:
        execution_clock = _DemoExecutionClock(_utc_timestamp(scenario.create.created_at))
        execution = PaperExecutionApplicationService(
            session_factory=factory,
            clock=execution_clock,
        )

        def create_order():
            return execution.create_order_from_references(
                intent_id=intent.result.intent_id,
                intent_digest=intent.result.intent_digest,
                decision_id=decision.result.decision_id,
                decision_digest=decision.result.decision_digest,
                execution_policy_reference=_execution_policy(
                    scenario.execution_policy
                ),
                command_idempotency_key=scenario.create.idempotency_key,
                actor=scenario.create.actor,
            )

        created = create_order()
        replayed_create = create_order()
        order = created.result.order
        create_replayed = (
            not created.replayed
            and replayed_create.replayed
            and replayed_create.result.order == order
        )
        for index, step in enumerate(scenario.steps):
            execution_clock.value = _utc_timestamp(step.created_at)
            committed = execution.step_order_from_reference(
                execution_order_id=order.execution_order_id,
                execution_order_digest=order.execution_order_digest,
                expected_execution_version=step.expected_execution_version,
                command_idempotency_key=step.idempotency_key,
                actor=step.actor,
            )
            if index == 0:
                replayed_step = execution.step_order_from_reference(
                    execution_order_id=order.execution_order_id,
                    execution_order_digest=order.execution_order_digest,
                    expected_execution_version=step.expected_execution_version,
                    command_idempotency_key=step.idempotency_key,
                    actor=step.actor,
                )
                step_replayed = (
                    not committed.replayed
                    and replayed_step.replayed
                    and replayed_step.result == committed.result
                )
        execution = PaperExecutionApplicationService(
            session_factory=factory,
            clock=execution_clock,
        )
        history = execution.reconcile_order(
            execution_order_id=order.execution_order_id
        )

    detail = account_service.get_account_detail(account_id=account.account_id)
    projection = detail.projection.to_dict()
    positions = cast(list[dict[str, object]], projection["positions"])
    position = positions[0] if positions else None
    with factory() as session:
        persisted_replay = SqlAlchemyMarketTimeRepository(session=session).get_replay(
            replay_id=market.replay_id
        )
    if persisted_replay is None:
        raise DemoWorkspaceUnavailableError("Demo execution replay is unavailable")
    return {
        "intent": (intent.result.intent_id, intent.result.intent_digest),
        "allow_decision": (
            decision.result.decision_id,
            decision.result.decision_digest,
        ),
        "order": None if order is None else (
            order.execution_order_id,
            order.execution_order_digest,
        ),
        "status": "fresh_manual_candidate" if history is None else history.state.status,
        "attempts": () if history is None else tuple(
            (
                item.attempt_id,
                item.attempt_digest,
                item.attempt_result,
                None if item.consumed_event_reference is None else item.consumed_event_reference.event_id,
            )
            for item in history.attempts
        ),
        "fills": () if history is None else tuple(
            (
                item.fill_id,
                item.fill_digest,
                item.fill_quantity.to_json_value(),
                item.execution_price_evidence.execution_price.to_json_value(),
                item.cost_evidence.total_charges.to_json_value(),
            )
            for item in history.fills
        ),
        "settlement_links": () if history is None else tuple(
            (item.settlement_link_id, item.settlement_link_digest)
            for item in history.settlement_links
        ),
        "account_head_version": detail.account.head_version,
        "cash_balance": projection["cash_balance"],
        "position_quantity": "0" if position is None else position["quantity"],
        "aggregate_cost_basis": "0" if position is None else position["aggregate_cost_basis"],
        "replay_position": persisted_replay.session.cursor.position,
        "replay_last_event_id": persisted_replay.session.cursor.last_event_id,
        "create_replayed": create_replayed,
        "step_replayed": step_replayed,
    }


def _expected_demo_execution_scenario(
    scenario: _DemoExecutionScenario,
) -> dict[str, object]:
    expected = scenario.expected
    return {
        "intent": (expected.intent.id, expected.intent.digest),
        "allow_decision": (
            expected.allow_decision.id,
            expected.allow_decision.digest,
        ),
        "order": None if expected.order is None else (
            expected.order.id,
            expected.order.digest,
        ),
        "status": expected.status,
        "attempts": tuple(
            (item.id, item.digest, item.result, item.consumed_event_id)
            for item in expected.attempts
        ),
        "fills": tuple(
            (
                item.id,
                item.digest,
                item.quantity,
                item.execution_price,
                item.total_charges,
            )
            for item in expected.fills
        ),
        "settlement_links": tuple(
            (item.id, item.digest) for item in expected.settlement_links
        ),
        "account_head_version": expected.account_head_version,
        "cash_balance": expected.cash_balance,
        "position_quantity": expected.position_quantity,
        "aggregate_cost_basis": expected.aggregate_cost_basis,
        "replay_position": expected.replay_position,
        "replay_last_event_id": expected.replay_last_event_id,
        "create_replayed": scenario.kind != "manual",
        "step_replayed": scenario.kind != "manual",
    }


def _seed_demo_paper_execution(
    *, paths: DemoWorkspacePaths, source: _ValidatedDemoSource
) -> None:
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    factory = create_product_session_factory(engine=engine)
    try:
        for scenario in source.paper_execution_journey.scenarios:
            actual = _build_demo_execution_scenario(
                factory=factory,
                scenario=scenario,
            )
            expected = _expected_demo_execution_scenario(scenario)
            if actual != expected:
                raise DemoWorkspaceUnavailableError(
                    "Demo execution authority diverged: " + repr((scenario.kind, actual))
                )
    finally:
        engine.dispose()


def _validate_seeded_demo_paper_execution(
    *, paths: DemoWorkspacePaths, source: _ValidatedDemoSource
) -> None:
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    factory = create_product_session_factory(engine=engine)
    try:
        service = PaperExecutionApplicationService(session_factory=factory)
        descriptor = source.descriptor.to_dict()["paper_execution"]
        manual = descriptor["manual_candidate"]
        strategy = StrategyOrderApplicationService(session_factory=factory)
        intent = strategy.get_order_intent(intent_id=manual["intent_id"])
        decision = strategy.get_pre_trade_risk_decision(
            decision_id=manual["decision_id"]
        )
        if (
            intent.intent_digest != manual["intent_digest"]
            or decision.decision_digest != manual["decision_digest"]
            or decision.outcome != "allow"
            or any(
                item.order.order_intent_reference.intent_id == intent.intent_id
                for item in service.list_order_histories(limit=200).items
            )
        ):
            raise DemoWorkspaceUnavailableError(
                "Demo manual execution candidate is inconsistent"
            )
        for name in (
            "completed_order",
            "risk_rejection_order",
            "exhaustion_order",
        ):
            reference = descriptor[name]
            history = service.reconcile_order(execution_order_id=reference["id"])
            if history.order.execution_order_digest != reference["digest"]:
                raise DemoWorkspaceUnavailableError(
                    "Demo execution descriptor is inconsistent"
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
    try:
        _validate_seeded_demo_paper_account(paths=paths, source=source)
    except DemoWorkspaceUnavailableError:
        raise
    except Exception as exc:
        raise DemoWorkspaceUnavailableError(
            "demo paper account is unavailable"
        ) from exc
    try:
        _validate_seeded_demo_market_time(paths=paths, source=source)
    except DemoWorkspaceUnavailableError:
        raise
    except Exception as exc:
        raise DemoWorkspaceUnavailableError(
            "demo market time is unavailable"
        ) from exc
    try:
        _validate_seeded_demo_strategy_order(paths=paths, source=source)
    except DemoWorkspaceUnavailableError:
        raise
    except Exception as exc:
        raise DemoWorkspaceUnavailableError(
            "demo strategy-to-risk authority is unavailable"
        ) from exc
    try:
        _validate_seeded_demo_paper_execution(paths=paths, source=source)
    except DemoWorkspaceUnavailableError:
        raise
    except Exception as exc:
        raise DemoWorkspaceUnavailableError(
            "demo paper execution authority is unavailable"
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
        if prior_revision == "0009_market_time_runtime":
            _seed_demo_strategy_order(paths=paths, source=source)
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
        _seed_demo_paper_account(paths=staging, source=source)
        _seed_demo_market_time(paths=staging, source=source)
        _seed_demo_strategy_order(paths=staging, source=source)
        _seed_demo_paper_execution(paths=staging, source=source)
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
            paper_account = payload["paper_account"]
            service = PaperAccountApplicationService(
                session_factory=factory
            )
            detail = service.get_account_detail(
                account_id=paper_account["account_id"]
            )
            history = service.get_account_history(
                account_id=paper_account["account_id"]
            )
            replayed_state = replay_paper_account_ledger(history)
            rebuilt = rebuild_paper_account_projection(history)
            snapshot = service.get_snapshot(
                snapshot_id=paper_account["snapshot_id"]
            )
            reconciliation = service.get_reconciliation(
                reconciliation_id=paper_account["reconciliation_id"]
            )
            if (
                detail.account.head_version
                != paper_account["head_version"]
                or tuple(
                    bundle.event.event_type for bundle in history
                )
                != tuple(paper_account["event_types"])
                or replayed_state.head_version
                != paper_account["head_version"]
                or detail.projection.to_dict() != rebuilt.to_dict()
                or snapshot.account_id != paper_account["account_id"]
                or snapshot.projection.to_dict() != rebuilt.to_dict()
                or reconciliation.account_id
                != paper_account["account_id"]
                or reconciliation.outcome != "matched"
                or reconciliation.authoritative_projection_digest
                != rebuilt.projection_digest
                or reconciliation.candidate_projection_digest
                != rebuilt.projection_digest
            ):
                raise DemoWorkspaceUnavailableError(
                    "demo paper account is inconsistent"
                )
            market_time = payload["market_time"]
            with factory() as market_session:
                market_repository = SqlAlchemyMarketTimeRepository(
                    session=market_session
                )
                calendar = market_repository.get_calendar(
                    calendar_id=market_time["calendar_id"]
                )
                sessions = market_repository.list_sessions(
                    calendar_id=market_time["calendar_id"]
                )
                replay = market_repository.get_replay(
                    replay_id=market_time["replay_id"]
                )
            if calendar is None or replay is None:
                raise DemoWorkspaceUnavailableError(
                    "demo market time is inconsistent"
                )
            checkpoint = market_time["checkpoint"]
            cursor = replay.session.cursor
            if (
                tuple(item.id for item in sessions)
                != tuple(market_time["session_ids"])
                or len(replay.events) != market_time["event_count"]
                or cursor.event_stream_digest
                != market_time["event_stream_digest"]
                or cursor.status != checkpoint["status"]
                or cursor.position != checkpoint["position"]
                or cursor.last_event_id != checkpoint["last_event_id"]
                or cursor.current_event_time
                != _utc_timestamp(checkpoint["current_time"])
            ):
                raise DemoWorkspaceUnavailableError(
                    "demo market time is inconsistent"
                )
            recovered = MarketDataReplayEngine(
                replay_id=replay.session.replay_id,
                events=replay.events,
                cursor=replay.session.cursor,
            )
            recovered.resume()
            remaining = tuple(
                event.event_id for event in recovered.iter_remaining()
            )
            recovery = market_time["recovery"]
            if (
                remaining != tuple(recovery["remaining_event_ids"])
                or recovered.session.status != recovery["final_status"]
                or recovered.session.cursor.position
                != recovery["final_position"]
                or recovered.session.cursor.last_event_id
                != recovery["last_event_id"]
                or recovered.session.current_time
                != _utc_timestamp(recovery["current_time"])
            ):
                raise DemoWorkspaceUnavailableError(
                    "demo market time recovery is inconsistent"
                )
            _validate_descriptor_strategy_order(
                paths=paths,
                strategy_order=payload["strategy_order"],
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
