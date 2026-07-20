"""Safe write-once files for durable portfolio-review authority."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable, Mapping
from pathlib import Path, PurePosixPath
from typing import TypeVar
from uuid import uuid4

import pandas as pd

from el_psy_quant.portfolio_review.analysis_artifacts import (
    PORTFOLIO_REVIEW_ANALYSIS_ARTIFACT_SCHEMA_VERSION,
    PortfolioReviewAnalysisArtifact,
    create_portfolio_review_analysis_artifact,
)
from el_psy_quant.portfolio_review.decision_artifacts import (
    PORTFOLIO_REVIEW_DECISION_ARTIFACT_SCHEMA_VERSION,
    PortfolioReviewDecisionArtifact,
    create_portfolio_review_decision_artifact,
)
from el_psy_quant.portfolio_review.evidence_references import (
    PORTFOLIO_REVIEW_COMPONENT_SCHEMA_VERSION,
    PORTFOLIO_REVIEW_EVIDENCE_REFERENCE_SCHEMA_VERSION,
    create_portfolio_review_component,
    create_portfolio_review_evidence_reference,
)
from el_psy_quant.portfolio_review.scenarios import (
    PORTFOLIO_REVIEW_BASELINE_SCENARIO_SCHEMA_VERSION,
    PORTFOLIO_REVIEW_PROPOSED_SCENARIO_SCHEMA_VERSION,
    create_portfolio_review_baseline_scenario,
    create_portfolio_review_proposed_scenario,
    create_portfolio_review_scenario_pair,
)
from el_psy_quant.portfolio_review.sources import (
    PORTFOLIO_REVIEW_RETURN_OBSERVATION_SCHEMA_VERSION,
    PORTFOLIO_REVIEW_SOURCE_SCHEMA_VERSION,
    PortfolioReviewSource,
    create_portfolio_review_source,
)

PORTFOLIO_REVIEW_ARTIFACT_DIRECTORY = "portfolio-reviews"
PORTFOLIO_REVIEW_SOURCE_FILENAME = "source.json"
PORTFOLIO_REVIEW_ANALYSIS_FILENAME = "analysis.json"
PORTFOLIO_REVIEW_DECISION_FILENAME = "decision.json"


class PortfolioReviewArtifactRootUnavailableError(Exception):
    """The configured evidence root is not one existing real directory."""

    def __init__(self) -> None:
        super().__init__("portfolio review artifact root is unavailable")


class PortfolioReviewArtifactConflictError(Exception):
    """A reserved immutable file contains different valid authority."""

    def __init__(self) -> None:
        super().__init__("portfolio review artifact conflicts with existing authority")


class PortfolioReviewArtifactInvalidError(Exception):
    """A selected artifact or fixed layout is unsafe or invalid."""

    def __init__(self) -> None:
        super().__init__("portfolio review artifact is invalid")


class PortfolioReviewArtifactUnavailableError(Exception):
    """A database-referenced artifact is absent or cannot be read."""

    def __init__(self) -> None:
        super().__init__("portfolio review artifact is unavailable")


ArtifactT = TypeVar(
    "ArtifactT",
    PortfolioReviewSource,
    PortfolioReviewAnalysisArtifact,
    PortfolioReviewDecisionArtifact,
)


def _normalized_id(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def portfolio_review_id_path_key(value: str) -> str:
    """Hash one normalized authority ID so raw IDs never become path fragments."""
    normalized = _normalized_id(value, "artifact_id")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def portfolio_review_source_relative_path(source_id: str) -> str:
    """Return the one fixed POSIX locator for a source authority."""
    return PurePosixPath(
        PORTFOLIO_REVIEW_ARTIFACT_DIRECTORY,
        "sources",
        portfolio_review_id_path_key(source_id),
        PORTFOLIO_REVIEW_SOURCE_FILENAME,
    ).as_posix()


def portfolio_review_analysis_relative_path(review_id: str) -> str:
    """Return the one fixed POSIX locator for an analysis authority."""
    return PurePosixPath(
        PORTFOLIO_REVIEW_ARTIFACT_DIRECTORY,
        "reviews",
        portfolio_review_id_path_key(review_id),
        PORTFOLIO_REVIEW_ANALYSIS_FILENAME,
    ).as_posix()


def portfolio_review_decision_relative_path(review_id: str) -> str:
    """Return the one fixed POSIX locator for a decision authority."""
    return PurePosixPath(
        PORTFOLIO_REVIEW_ARTIFACT_DIRECTORY,
        "reviews",
        portfolio_review_id_path_key(review_id),
        PORTFOLIO_REVIEW_DECISION_FILENAME,
    ).as_posix()


def validate_portfolio_review_artifact_root(root: str | Path) -> Path:
    """Validate the existing configured evidence root without creating it."""
    if isinstance(root, str) and not root.strip():
        raise PortfolioReviewArtifactRootUnavailableError()
    if not isinstance(root, (str, Path)):
        raise PortfolioReviewArtifactRootUnavailableError()
    try:
        path = Path(root)
        if path.is_symlink() or not path.exists() or not path.is_dir():
            raise PortfolioReviewArtifactRootUnavailableError()
        return path.resolve(strict=True)
    except PortfolioReviewArtifactRootUnavailableError:
        raise
    except (OSError, RuntimeError) as exc:
        raise PortfolioReviewArtifactRootUnavailableError() from exc


def _contained_directory(root: Path, parts: tuple[str, ...], *, create: bool) -> Path:
    current = root
    try:
        for part in parts:
            current = current / part
            if create:
                current.mkdir(exist_ok=True)
            if current.is_symlink() or not current.exists() or not current.is_dir():
                raise PortfolioReviewArtifactInvalidError()
            current.resolve(strict=True).relative_to(root)
        return current.resolve(strict=True)
    except PortfolioReviewArtifactInvalidError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise PortfolioReviewArtifactInvalidError() from exc


def _selected_file(
    *,
    root: Path,
    relative_path: str,
    create_parents: bool,
    required: bool,
) -> Path:
    relative = PurePosixPath(relative_path)
    parts = relative.parts
    if (
        relative.is_absolute()
        or ".." in parts
        or "\\" in relative_path
        or len(parts) != 4
        or parts[0] != PORTFOLIO_REVIEW_ARTIFACT_DIRECTORY
        or parts[1] not in {"sources", "reviews"}
        or len(parts[2]) != 64
        or any(character not in "0123456789abcdef" for character in parts[2])
        or parts[3]
        not in {
            PORTFOLIO_REVIEW_SOURCE_FILENAME,
            PORTFOLIO_REVIEW_ANALYSIS_FILENAME,
            PORTFOLIO_REVIEW_DECISION_FILENAME,
        }
    ):
        raise PortfolioReviewArtifactInvalidError()
    directory = _contained_directory(root, parts[:-1], create=create_parents)
    target = directory / parts[-1]
    try:
        if target.exists() or target.is_symlink():
            if target.is_symlink() or not target.is_file():
                raise PortfolioReviewArtifactInvalidError()
            resolved = target.resolve(strict=True)
            resolved.relative_to(directory)
            return resolved
        if required:
            raise PortfolioReviewArtifactUnavailableError()
        return target
    except (
        PortfolioReviewArtifactInvalidError,
        PortfolioReviewArtifactUnavailableError,
    ):
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        if required:
            raise PortfolioReviewArtifactUnavailableError() from exc
        raise PortfolioReviewArtifactInvalidError() from exc


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _read_payload(path: Path) -> dict[str, object]:
    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(
            raw,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError) as exc:
        raise PortfolioReviewArtifactUnavailableError() from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise PortfolioReviewArtifactInvalidError() from exc
    if type(payload) is not dict:
        raise PortfolioReviewArtifactInvalidError()
    return payload


def _dict(value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError("expected JSON object")
    return value


def _list(value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError("expected JSON array")
    return value


def _exact_keys(payload: Mapping[str, object], expected: tuple[str, ...]) -> None:
    if set(payload) != set(expected):
        raise ValueError("artifact fields do not match the approved schema")


def _require_schema(value: object, expected: int, name: str) -> None:
    if type(value) is not int or value != expected:
        raise ValueError(f"unsupported {name} schema")


def _source_from_payload(payload: dict[str, object]) -> PortfolioReviewSource:
    _exact_keys(
        payload,
        (
            "schema_version",
            "source_id",
            "components",
            "return_observations",
            "evaluation_frequency",
            "periods_per_year",
            "created_by",
            "created_timestamp",
            "assumptions",
            "warnings",
            "missing_evidence",
            "source_digest",
        ),
    )
    _require_schema(
        payload["schema_version"],
        PORTFOLIO_REVIEW_SOURCE_SCHEMA_VERSION,
        "source",
    )
    components = []
    for raw_component in _list(payload["components"]):
        component = _dict(raw_component)
        _exact_keys(
            component,
            (
                "schema_version",
                "component_id",
                "strategy_id",
                "evidence_references",
                "symbols",
                "label",
                "description",
            ),
        )
        _require_schema(
            component["schema_version"],
            PORTFOLIO_REVIEW_COMPONENT_SCHEMA_VERSION,
            "component",
        )
        references = []
        for raw_reference in _list(component["evidence_references"]):
            reference = _dict(raw_reference)
            _exact_keys(
                reference,
                (
                    "schema_version",
                    "reference_type",
                    "reference_id",
                    "label",
                    "description",
                ),
            )
            _require_schema(
                reference["schema_version"],
                PORTFOLIO_REVIEW_EVIDENCE_REFERENCE_SCHEMA_VERSION,
                "evidence",
            )
            references.append(
                create_portfolio_review_evidence_reference(
                    reference_type=reference["reference_type"],  # type: ignore[arg-type]
                    reference_id=reference["reference_id"],  # type: ignore[arg-type]
                    label=reference["label"],  # type: ignore[arg-type]
                    description=reference["description"],  # type: ignore[arg-type]
                )
            )
        symbols = component["symbols"]
        components.append(
            create_portfolio_review_component(
                component_id=component["component_id"],  # type: ignore[arg-type]
                strategy_id=component["strategy_id"],  # type: ignore[arg-type]
                evidence_references=references,
                symbols=None if symbols is None else _list(symbols),  # type: ignore[arg-type]
                label=component["label"],  # type: ignore[arg-type]
                description=component["description"],  # type: ignore[arg-type]
            )
        )

    observations = _list(payload["return_observations"])
    timestamps: list[object] = []
    rows: list[list[object]] = []
    for raw_observation in observations:
        observation = _dict(raw_observation)
        _exact_keys(
            observation,
            ("schema_version", "timestamp", "component_returns"),
        )
        _require_schema(
            observation["schema_version"],
            PORTFOLIO_REVIEW_RETURN_OBSERVATION_SCHEMA_VERSION,
            "observation",
        )
        timestamps.append(observation["timestamp"])
        rows.append(_list(observation["component_returns"]))
    aligned_returns = pd.DataFrame(
        rows,
        index=pd.DatetimeIndex(timestamps),
        columns=[component.component_id for component in components],
    )
    source = create_portfolio_review_source(
        source_id=payload["source_id"],  # type: ignore[arg-type]
        components=components,
        aligned_returns=aligned_returns,
        evaluation_frequency=payload["evaluation_frequency"],  # type: ignore[arg-type]
        periods_per_year=payload["periods_per_year"],  # type: ignore[arg-type]
        created_by=payload["created_by"],  # type: ignore[arg-type]
        created_timestamp=payload["created_timestamp"],
        assumptions=_list(payload["assumptions"]),  # type: ignore[arg-type]
        warnings=_list(payload["warnings"]),  # type: ignore[arg-type]
        missing_evidence=_list(payload["missing_evidence"]),  # type: ignore[arg-type]
    )
    if source.to_dict() != payload:
        raise ValueError("source payload does not reconstruct exactly")
    return source


def _weights(payload: dict[str, object]) -> dict[str, object]:
    weights: dict[str, object] = {}
    for raw_item in _list(payload["component_weights"]):
        item = _dict(raw_item)
        _exact_keys(item, ("component_id", "weight"))
        component_id = item["component_id"]
        if type(component_id) is not str or component_id in weights:
            raise ValueError("invalid component weight identity")
        weights[component_id] = item["weight"]
    return weights


def _analysis_from_payload(
    payload: dict[str, object],
    *,
    source: PortfolioReviewSource,
) -> PortfolioReviewAnalysisArtifact:
    _exact_keys(
        payload,
        (
            "schema_version",
            "review_id",
            "analysis_evidence_scope",
            "source_id",
            "source_digest",
            "component_ids",
            "baseline_scenario_id",
            "baseline_scenario_digest",
            "proposed_scenario_id",
            "proposed_scenario_digest",
            "proposed_component_id",
            "baseline_scenario",
            "proposed_scenario",
            "concentration_exposure_analysis",
            "interaction_impact_analysis",
            "assumptions",
            "warnings",
            "missing_evidence",
            "created_by",
            "created_timestamp",
            "analysis_digest",
        ),
    )
    _require_schema(
        payload["schema_version"],
        PORTFOLIO_REVIEW_ANALYSIS_ARTIFACT_SCHEMA_VERSION,
        "analysis",
    )
    baseline_payload = _dict(payload["baseline_scenario"])
    proposed_payload = _dict(payload["proposed_scenario"])
    _exact_keys(
        baseline_payload,
        (
            "schema_version",
            "scenario_id",
            "source_id",
            "source_digest",
            "component_weights",
            "rationale",
            "assumptions",
            "warnings",
            "scenario_digest",
        ),
    )
    _exact_keys(
        proposed_payload,
        (
            "schema_version",
            "scenario_id",
            "source_id",
            "source_digest",
            "component_weights",
            "proposed_component_id",
            "rationale",
            "assumptions",
            "warnings",
            "scenario_digest",
        ),
    )
    _require_schema(
        baseline_payload["schema_version"],
        PORTFOLIO_REVIEW_BASELINE_SCENARIO_SCHEMA_VERSION,
        "baseline scenario",
    )
    _require_schema(
        proposed_payload["schema_version"],
        PORTFOLIO_REVIEW_PROPOSED_SCENARIO_SCHEMA_VERSION,
        "proposed scenario",
    )
    baseline = create_portfolio_review_baseline_scenario(
        scenario_id=baseline_payload["scenario_id"],  # type: ignore[arg-type]
        source=source,
        weights=_weights(baseline_payload),  # type: ignore[arg-type]
        rationale=baseline_payload["rationale"],  # type: ignore[arg-type]
        assumptions=_list(baseline_payload["assumptions"]),  # type: ignore[arg-type]
        warnings=_list(baseline_payload["warnings"]),  # type: ignore[arg-type]
    )
    proposed = create_portfolio_review_proposed_scenario(
        scenario_id=proposed_payload["scenario_id"],  # type: ignore[arg-type]
        source=source,
        weights=_weights(proposed_payload),  # type: ignore[arg-type]
        proposed_component_id=proposed_payload["proposed_component_id"],  # type: ignore[arg-type]
        rationale=proposed_payload["rationale"],  # type: ignore[arg-type]
        assumptions=_list(proposed_payload["assumptions"]),  # type: ignore[arg-type]
        warnings=_list(proposed_payload["warnings"]),  # type: ignore[arg-type]
    )
    pair = create_portfolio_review_scenario_pair(
        source=source,
        baseline=baseline,
        proposed=proposed,
    )
    analysis = create_portfolio_review_analysis_artifact(
        review_id=payload["review_id"],  # type: ignore[arg-type]
        source=source,
        scenario_pair=pair,
        created_by=payload["created_by"],  # type: ignore[arg-type]
        created_timestamp=payload["created_timestamp"],
        assumptions=_list(payload["assumptions"]),  # type: ignore[arg-type]
        warnings=_list(payload["warnings"]),  # type: ignore[arg-type]
        missing_evidence=_list(payload["missing_evidence"]),  # type: ignore[arg-type]
    )
    if analysis.to_dict() != payload:
        raise ValueError("analysis payload does not reconstruct exactly")
    return analysis


def _decision_from_payload(
    payload: dict[str, object],
    *,
    analysis: PortfolioReviewAnalysisArtifact,
) -> PortfolioReviewDecisionArtifact:
    _exact_keys(
        payload,
        (
            "schema_version",
            "decision_id",
            "decision_scope",
            "review_id",
            "analysis_digest",
            "source_id",
            "source_digest",
            "baseline_scenario_id",
            "baseline_scenario_digest",
            "proposed_scenario_id",
            "proposed_scenario_digest",
            "outcome",
            "rationale",
            "reviewed_by",
            "reviewed_timestamp",
            "notes",
            "warnings",
            "decision_digest",
        ),
    )
    _require_schema(
        payload["schema_version"],
        PORTFOLIO_REVIEW_DECISION_ARTIFACT_SCHEMA_VERSION,
        "decision",
    )
    decision = create_portfolio_review_decision_artifact(
        decision_id=payload["decision_id"],  # type: ignore[arg-type]
        analysis=analysis,
        outcome=payload["outcome"],  # type: ignore[arg-type]
        rationale=payload["rationale"],  # type: ignore[arg-type]
        reviewed_by=payload["reviewed_by"],  # type: ignore[arg-type]
        reviewed_timestamp=payload["reviewed_timestamp"],
        notes=_list(payload["notes"]),  # type: ignore[arg-type]
        warnings=_list(payload["warnings"]),  # type: ignore[arg-type]
    )
    if decision.to_dict() != payload:
        raise ValueError("decision payload does not reconstruct exactly")
    return decision


def _read_and_reconstruct(
    *,
    root: str | Path,
    relative_path: str,
    reconstruct: Callable[[dict[str, object]], ArtifactT],
) -> ArtifactT:
    canonical_root = validate_portfolio_review_artifact_root(root)
    path = _selected_file(
        root=canonical_root,
        relative_path=relative_path,
        create_parents=False,
        required=True,
    )
    payload = _read_payload(path)
    try:
        return reconstruct(payload)
    except PortfolioReviewArtifactInvalidError:
        raise
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise PortfolioReviewArtifactInvalidError() from exc


def read_portfolio_review_source(
    *, root: str | Path, source_id: str
) -> PortfolioReviewSource:
    """Strictly reopen and reconstruct one exact source artifact."""
    normalized = _normalized_id(source_id, "source_id")
    source = _read_and_reconstruct(
        root=root,
        relative_path=portfolio_review_source_relative_path(normalized),
        reconstruct=_source_from_payload,
    )
    if source.source_id != normalized:
        raise PortfolioReviewArtifactInvalidError()
    return source


def read_portfolio_review_analysis(
    *,
    root: str | Path,
    review_id: str,
    source_id: str,
) -> PortfolioReviewAnalysisArtifact:
    """Recalculate S171/S172 authority while reopening an analysis."""
    normalized_review = _normalized_id(review_id, "review_id")
    source = read_portfolio_review_source(root=root, source_id=source_id)
    analysis = _read_and_reconstruct(
        root=root,
        relative_path=portfolio_review_analysis_relative_path(normalized_review),
        reconstruct=lambda payload: _analysis_from_payload(payload, source=source),
    )
    if analysis.review_id != normalized_review:
        raise PortfolioReviewArtifactInvalidError()
    return analysis


def read_portfolio_review_decision(
    *,
    root: str | Path,
    review_id: str,
    source_id: str,
) -> PortfolioReviewDecisionArtifact:
    """Reconstruct one decision through the exact reopened analysis."""
    normalized_review = _normalized_id(review_id, "review_id")
    analysis = read_portfolio_review_analysis(
        root=root,
        review_id=normalized_review,
        source_id=source_id,
    )
    decision = _read_and_reconstruct(
        root=root,
        relative_path=portfolio_review_decision_relative_path(normalized_review),
        reconstruct=lambda payload: _decision_from_payload(
            payload,
            analysis=analysis,
        ),
    )
    if decision.review_id != normalized_review:
        raise PortfolioReviewArtifactInvalidError()
    return decision


def _serialized(payload: dict[str, object]) -> bytes:
    return (
        json.dumps(
            payload,
            indent=2,
            allow_nan=False,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _publish_exclusive(path: Path, content: bytes) -> bool:
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    descriptor: int | None = None
    try:
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            return False
        return True
    except FileExistsError:
        return False
    except OSError as exc:
        raise PortfolioReviewArtifactUnavailableError() from exc
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def _write_or_reuse(
    *,
    root: str | Path,
    relative_path: str,
    payload: dict[str, object],
    reopen: Callable[[], ArtifactT],
) -> ArtifactT:
    canonical_root = validate_portfolio_review_artifact_root(root)
    target = _selected_file(
        root=canonical_root,
        relative_path=relative_path,
        create_parents=True,
        required=False,
    )
    if not target.exists():
        _publish_exclusive(target, _serialized(payload))
    try:
        reopened = reopen()
    except PortfolioReviewArtifactInvalidError:
        raise
    except PortfolioReviewArtifactUnavailableError:
        raise
    if reopened.to_dict() != payload:
        raise PortfolioReviewArtifactConflictError()
    return reopened


def write_portfolio_review_source(
    *, root: str | Path, source: PortfolioReviewSource
) -> str:
    """Publish or exactly reuse one source.json authority."""
    if type(source) is not PortfolioReviewSource:
        raise ValueError("source must be a PortfolioReviewSource")
    relative = portfolio_review_source_relative_path(source.source_id)
    _write_or_reuse(
        root=root,
        relative_path=relative,
        payload=source.to_dict(),
        reopen=lambda: read_portfolio_review_source(
            root=root,
            source_id=source.source_id,
        ),
    )
    return relative


def write_portfolio_review_analysis(
    *,
    root: str | Path,
    source_id: str,
    analysis: PortfolioReviewAnalysisArtifact,
) -> str:
    """Publish or exactly reuse one analysis.json authority."""
    if type(analysis) is not PortfolioReviewAnalysisArtifact:
        raise ValueError("analysis must be a PortfolioReviewAnalysisArtifact")
    relative = portfolio_review_analysis_relative_path(analysis.review_id)
    _write_or_reuse(
        root=root,
        relative_path=relative,
        payload=analysis.to_dict(),
        reopen=lambda: read_portfolio_review_analysis(
            root=root,
            review_id=analysis.review_id,
            source_id=source_id,
        ),
    )
    return relative


def write_portfolio_review_decision(
    *,
    root: str | Path,
    source_id: str,
    decision: PortfolioReviewDecisionArtifact,
) -> str:
    """Publish or exactly reuse one decision.json authority."""
    if type(decision) is not PortfolioReviewDecisionArtifact:
        raise ValueError("decision must be a PortfolioReviewDecisionArtifact")
    relative = portfolio_review_decision_relative_path(decision.review_id)
    _write_or_reuse(
        root=root,
        relative_path=relative,
        payload=decision.to_dict(),
        reopen=lambda: read_portfolio_review_decision(
            root=root,
            review_id=decision.review_id,
            source_id=source_id,
        ),
    )
    return relative


__all__ = [
    "PORTFOLIO_REVIEW_ANALYSIS_FILENAME",
    "PORTFOLIO_REVIEW_ARTIFACT_DIRECTORY",
    "PORTFOLIO_REVIEW_DECISION_FILENAME",
    "PORTFOLIO_REVIEW_SOURCE_FILENAME",
    "PortfolioReviewArtifactConflictError",
    "PortfolioReviewArtifactInvalidError",
    "PortfolioReviewArtifactRootUnavailableError",
    "PortfolioReviewArtifactUnavailableError",
    "portfolio_review_analysis_relative_path",
    "portfolio_review_decision_relative_path",
    "portfolio_review_id_path_key",
    "portfolio_review_source_relative_path",
    "read_portfolio_review_analysis",
    "read_portfolio_review_decision",
    "read_portfolio_review_source",
    "validate_portfolio_review_artifact_root",
    "write_portfolio_review_analysis",
    "write_portfolio_review_decision",
    "write_portfolio_review_source",
]
