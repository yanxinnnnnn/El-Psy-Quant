"""Bounded read-only inspection of configured research-run artifacts."""

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Literal

DataSource = Literal["csv", "cache"]

_EXPERIMENT_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_RUN_ID = re.compile(r"[A-Za-z0-9_-]+\Z")


class ResearchArtifactRootUnavailableError(Exception):
    """Raised when the configured research artifact root cannot be used."""


class ResearchRunNotFoundError(Exception):
    """Raised when an exact research run cannot be selected."""


class ResearchArtifactInvalidError(Exception):
    """Raised when a selected or discovered artifact is unsafe or invalid."""


@dataclass(frozen=True)
class ResearchRunSummary:
    experiment_slug: str
    run_id: str
    experiment_name: str
    strategy: str
    data_source: DataSource
    symbols: tuple[str, ...]


@dataclass(frozen=True)
class ResearchRunData:
    source: DataSource
    symbols: tuple[str, ...]


@dataclass(frozen=True)
class ResearchRunParameters:
    fast_window: int
    slow_window: int
    initial_capital: float
    transaction_cost_rate: float
    slippage_rate: float


@dataclass(frozen=True)
class ResearchRunEvaluation:
    periods_per_year: float | None
    annual_risk_free_rate: float


@dataclass(frozen=True)
class ResearchArtifactReferences:
    config: str
    metadata: str
    summary: str
    metrics: str
    logs_dir: str


@dataclass(frozen=True)
class ResearchMetricRecord:
    symbol: str
    initial_equity: float
    final_equity: float
    total_return: float
    max_drawdown: float
    periods: float
    cagr: float | None
    annualized_volatility: float | None
    sharpe_ratio: float | None


@dataclass(frozen=True)
class ResearchRunDetail:
    manifest_schema_version: Literal[1]
    metrics_schema_version: Literal[1]
    experiment_slug: str
    run_id: str
    experiment_name: str
    strategy: str
    data: ResearchRunData
    parameters: ResearchRunParameters
    evaluation: ResearchRunEvaluation
    artifacts: ResearchArtifactReferences
    metrics: tuple[ResearchMetricRecord, ...]


@dataclass(frozen=True)
class _ParsedManifest:
    summary: ResearchRunSummary
    data: ResearchRunData
    parameters: ResearchRunParameters
    evaluation: ResearchRunEvaluation
    artifacts: ResearchArtifactReferences


def _invalid() -> ResearchArtifactInvalidError:
    return ResearchArtifactInvalidError("research artifact is invalid")


def _canonical_root(artifact_root: str | Path) -> Path:
    if not isinstance(artifact_root, (str, Path)):
        raise ResearchArtifactRootUnavailableError("research artifact root unavailable")
    if isinstance(artifact_root, str) and not artifact_root.strip():
        raise ResearchArtifactRootUnavailableError("research artifact root unavailable")
    try:
        root = Path(artifact_root).resolve(strict=True)
        if not root.is_dir():
            raise ResearchArtifactRootUnavailableError(
                "research artifact root unavailable"
            )
    except (OSError, RuntimeError, ValueError) as exc:
        raise ResearchArtifactRootUnavailableError(
            "research artifact root unavailable"
        ) from exc
    return root


def _valid_experiment_slug(value: object) -> bool:
    return isinstance(value, str) and _EXPERIMENT_SLUG.fullmatch(value) is not None


def _valid_run_id(value: object) -> bool:
    return isinstance(value, str) and _RUN_ID.fullmatch(value) is not None


def _json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _invalid() from exc
    if not isinstance(value, dict):
        raise _invalid()
    return value


def _object(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _invalid()
    return value


def _string(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _invalid()
    return value


def _integer(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise _invalid()
    return value


def _number(value: object) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise _invalid()
    result = float(value)
    if not math.isfinite(result):
        raise _invalid()
    return result


def _schema_version(value: object) -> Literal[1]:
    if not isinstance(value, int) or isinstance(value, bool) or value != 1:
        raise _invalid()
    return 1


def _symbols(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise _invalid()
    return tuple(_string(symbol) for symbol in value)


def _contains_symlink(run_dir: Path, relative_path: Path) -> bool:
    current = run_dir
    for part in relative_path.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _artifact_reference(value: object, run_dir: Path) -> str:
    reference = _string(value)
    try:
        relative = Path(reference)
        posix = PurePosixPath(reference)
        windows = PureWindowsPath(reference)
        if (
            "\\" in reference
            or posix.is_absolute()
            or windows.is_absolute()
            or bool(windows.drive)
            or ".." in posix.parts
            or ".." in windows.parts
            or not relative.parts
        ):
            raise _invalid()
        if _contains_symlink(run_dir, relative):
            raise _invalid()
        resolved = (run_dir / relative).resolve(strict=False)
        if not resolved.is_relative_to(run_dir):
            raise _invalid()
    except ResearchArtifactInvalidError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise _invalid() from exc
    return reference


def _read_manifest(
    manifest_path: Path,
    *,
    experiment_slug: str,
    selected_run_id: str,
    run_dir: Path,
) -> _ParsedManifest:
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise _invalid()
    manifest = _json_object(manifest_path)
    _schema_version(manifest.get("schema_version"))
    experiment_name = _string(manifest.get("experiment_name"))
    strategy = _string(manifest.get("strategy"))
    run_id = _string(manifest.get("run_id"))
    if run_id != selected_run_id:
        raise _invalid()

    data_value = _object(manifest.get("data"))
    source = _string(data_value.get("source"))
    if source not in ("csv", "cache"):
        raise _invalid()
    symbols = _symbols(data_value.get("symbols"))

    parameter_value = _object(manifest.get("parameters"))
    parameters = ResearchRunParameters(
        fast_window=_integer(parameter_value.get("fast_window")),
        slow_window=_integer(parameter_value.get("slow_window")),
        initial_capital=_number(parameter_value.get("initial_capital")),
        transaction_cost_rate=_number(parameter_value.get("transaction_cost_rate")),
        slippage_rate=_number(parameter_value.get("slippage_rate")),
    )

    evaluation_value = _object(manifest.get("evaluation"))
    raw_periods_per_year = evaluation_value.get("periods_per_year")
    periods_per_year = (
        None if raw_periods_per_year is None else _number(raw_periods_per_year)
    )
    if periods_per_year is not None and periods_per_year <= 0:
        raise _invalid()
    evaluation = ResearchRunEvaluation(
        periods_per_year=periods_per_year,
        annual_risk_free_rate=_number(evaluation_value.get("annual_risk_free_rate")),
    )

    artifact_value = _object(manifest.get("artifacts"))
    artifacts = ResearchArtifactReferences(
        config=_artifact_reference(artifact_value.get("config"), run_dir),
        metadata=_artifact_reference(artifact_value.get("metadata"), run_dir),
        summary=_artifact_reference(artifact_value.get("summary"), run_dir),
        metrics=_artifact_reference(artifact_value.get("metrics"), run_dir),
        logs_dir=_artifact_reference(artifact_value.get("logs_dir"), run_dir),
    )
    data = ResearchRunData(source=source, symbols=symbols)
    summary = ResearchRunSummary(
        experiment_slug=experiment_slug,
        run_id=run_id,
        experiment_name=experiment_name,
        strategy=strategy,
        data_source=source,
        symbols=symbols,
    )
    return _ParsedManifest(
        summary=summary,
        data=data,
        parameters=parameters,
        evaluation=evaluation,
        artifacts=artifacts,
    )


def _metric_optional(record: dict[str, Any], name: str) -> float | None:
    if name not in record:
        return None
    return _number(record[name])


def _read_metrics(
    metrics_path: Path,
    *,
    run_dir: Path,
    run_id: str,
    manifest: _ParsedManifest,
) -> tuple[Literal[1], tuple[ResearchMetricRecord, ...]]:
    relative = Path(manifest.artifacts.metrics)
    if metrics_path.is_symlink() or _contains_symlink(run_dir, relative):
        raise _invalid()
    try:
        resolved = metrics_path.resolve(strict=True)
        if not resolved.is_relative_to(run_dir) or not resolved.is_file():
            raise _invalid()
    except (OSError, RuntimeError) as exc:
        raise _invalid() from exc
    payload = _json_object(resolved)
    schema_version = _schema_version(payload.get("schema_version"))
    if _string(payload.get("run_id")) != run_id:
        raise _invalid()
    source_artifact = _artifact_reference(payload.get("source_artifact"), run_dir)
    if source_artifact != manifest.artifacts.summary:
        raise _invalid()
    records_value = payload.get("metrics")
    if not isinstance(records_value, list) or not records_value:
        raise _invalid()

    records = []
    annualized_names = ("cagr", "annualized_volatility", "sharpe_ratio")
    for raw_record in records_value:
        record = _object(raw_record)
        if manifest.evaluation.periods_per_year is not None and any(
            name not in record for name in annualized_names
        ):
            raise _invalid()
        periods = _number(record.get("periods"))
        if periods <= 0:
            raise _invalid()
        records.append(
            ResearchMetricRecord(
                symbol=_string(record.get("symbol")),
                initial_equity=_number(record.get("initial_equity")),
                final_equity=_number(record.get("final_equity")),
                total_return=_number(record.get("total_return")),
                max_drawdown=_number(record.get("max_drawdown")),
                periods=periods,
                cagr=_metric_optional(record, "cagr"),
                annualized_volatility=_metric_optional(record, "annualized_volatility"),
                sharpe_ratio=_metric_optional(record, "sharpe_ratio"),
            )
        )
    return schema_version, tuple(records)


def list_research_runs(
    *,
    artifact_root: str | Path,
) -> tuple[ResearchRunSummary, ...]:
    """List direct configured research runs by reading manifests only."""
    root = _canonical_root(artifact_root)
    summaries = []
    try:
        experiment_dirs = sorted(root.iterdir(), key=lambda path: path.name)
        for experiment_dir in experiment_dirs:
            if (
                experiment_dir.is_symlink()
                or not experiment_dir.is_dir()
                or not _valid_experiment_slug(experiment_dir.name)
            ):
                continue
            run_dirs = sorted(experiment_dir.iterdir(), key=lambda path: path.name)
            for run_dir in run_dirs:
                if (
                    run_dir.is_symlink()
                    or not run_dir.is_dir()
                    or not _valid_run_id(run_dir.name)
                ):
                    continue
                canonical_run = run_dir.resolve(strict=True)
                if not canonical_run.is_relative_to(root):
                    raise _invalid()
                manifest_path = run_dir / "manifest.json"
                if not manifest_path.exists() and not manifest_path.is_symlink():
                    continue
                parsed = _read_manifest(
                    manifest_path,
                    experiment_slug=experiment_dir.name,
                    selected_run_id=run_dir.name,
                    run_dir=canonical_run,
                )
                summaries.append(parsed.summary)
    except ResearchArtifactInvalidError:
        raise
    except OSError as exc:
        raise ResearchArtifactRootUnavailableError(
            "research artifact root unavailable"
        ) from exc
    return tuple(summaries)


def get_research_run_detail(
    *,
    artifact_root: str | Path,
    experiment_slug: str,
    run_id: str,
) -> ResearchRunDetail:
    """Read one fixed manifest and its single safe metrics artifact."""
    if not _valid_experiment_slug(experiment_slug) or not _valid_run_id(run_id):
        raise ResearchRunNotFoundError("research run not found")
    root = _canonical_root(artifact_root)
    experiment_dir = root / experiment_slug
    run_dir = experiment_dir / run_id
    if experiment_dir.is_symlink() or run_dir.is_symlink():
        raise _invalid()
    try:
        canonical_run = run_dir.resolve(strict=True)
        if not canonical_run.is_dir():
            raise ResearchRunNotFoundError("research run not found")
        if not canonical_run.is_relative_to(root):
            raise _invalid()
    except (OSError, RuntimeError) as exc:
        raise ResearchRunNotFoundError("research run not found") from exc
    manifest_path = canonical_run / "manifest.json"
    if not manifest_path.exists() and not manifest_path.is_symlink():
        raise ResearchRunNotFoundError("research run not found")
    parsed = _read_manifest(
        manifest_path,
        experiment_slug=experiment_slug,
        selected_run_id=run_id,
        run_dir=canonical_run,
    )
    metrics_path = canonical_run / parsed.artifacts.metrics
    metrics_schema_version, metrics = _read_metrics(
        metrics_path,
        run_dir=canonical_run,
        run_id=run_id,
        manifest=parsed,
    )
    return ResearchRunDetail(
        manifest_schema_version=1,
        metrics_schema_version=metrics_schema_version,
        experiment_slug=experiment_slug,
        run_id=run_id,
        experiment_name=parsed.summary.experiment_name,
        strategy=parsed.summary.strategy,
        data=parsed.data,
        parameters=parsed.parameters,
        evaluation=parsed.evaluation,
        artifacts=parsed.artifacts,
        metrics=metrics,
    )
