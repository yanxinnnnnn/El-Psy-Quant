"""Bounded read-only inspection of configured evidence manifests."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypeAlias

from el_psy_quant.decision_governance import (
    STRATEGY_DECISION_MANIFEST_SCHEMA_VERSION,
    STRATEGY_DECISION_REFERENCE_SCHEMA_VERSION,
    create_strategy_decision_manifest,
    create_strategy_decision_reference,
)
from el_psy_quant.report_artifacts import (
    REPORT_ARTIFACT_MANIFEST_SCHEMA_VERSION,
    REPORT_ARTIFACT_REFERENCE_SCHEMA_VERSION,
    create_report_artifact_manifest,
    create_report_artifact_reference,
)
from el_psy_quant.strategy_review import (
    STRATEGY_REVIEW_WORKFLOW_MANIFEST_SCHEMA_VERSION,
    STRATEGY_REVIEW_WORKFLOW_REFERENCE_SCHEMA_VERSION,
    create_strategy_review_workflow_manifest,
    create_strategy_review_workflow_reference,
)

EvidenceManifestType: TypeAlias = Literal[
    "strategy_decision_manifest",
    "report_artifact_manifest",
    "strategy_review_workflow_manifest",
]

SUPPORTED_EVIDENCE_MANIFEST_TYPES: tuple[EvidenceManifestType, ...] = (
    "strategy_decision_manifest",
    "report_artifact_manifest",
    "strategy_review_workflow_manifest",
)

_CATEGORY_BY_TYPE: dict[EvidenceManifestType, str] = {
    "strategy_decision_manifest": "strategy-decisions",
    "report_artifact_manifest": "report-artifacts",
    "strategy_review_workflow_manifest": "strategy-review",
}
_ARTIFACT_KEY = re.compile(r"[A-Za-z0-9_-]+\Z")


class EvidenceArtifactRootUnavailableError(Exception):
    """Raised when the configured evidence root cannot be used."""


class EvidenceManifestNotFoundError(Exception):
    """Raised when an exact supported manifest cannot be selected."""


class EvidenceArtifactInvalidError(Exception):
    """Raised when a configured evidence artifact is unsafe or invalid."""


@dataclass(frozen=True)
class EvidenceManifestReference:
    schema_version: Literal[1]
    reference_type: str
    reference_id: str
    label: str | None
    description: str | None


@dataclass(frozen=True)
class EvidenceManifestSummary:
    manifest_type: EvidenceManifestType
    artifact_key: str
    manifest_id: str
    reference_count: int
    created_by: str | None
    created_timestamp: str | None
    label: str | None
    description: str | None


@dataclass(frozen=True)
class StrategyDecisionManifestDetail:
    manifest_type: Literal["strategy_decision_manifest"]
    artifact_key: str
    schema_version: Literal[1]
    manifest_id: str
    summary_references: tuple[EvidenceManifestReference, ...]
    record_references: tuple[EvidenceManifestReference, ...]
    created_by: str | None
    created_timestamp: str | None
    description: str | None


@dataclass(frozen=True)
class ReportArtifactManifestDetail:
    manifest_type: Literal["report_artifact_manifest"]
    artifact_key: str
    schema_version: Literal[1]
    manifest_id: str
    references: tuple[EvidenceManifestReference, ...]
    label: str | None
    description: str | None
    created_by: str | None
    created_timestamp: str | None
    notes: str | None


@dataclass(frozen=True)
class StrategyReviewWorkflowManifestDetail:
    manifest_type: Literal["strategy_review_workflow_manifest"]
    artifact_key: str
    schema_version: Literal[1]
    manifest_id: str
    state_snapshot_references: tuple[EvidenceManifestReference, ...]
    transition_proposal_references: tuple[EvidenceManifestReference, ...]
    transition_record_references: tuple[EvidenceManifestReference, ...]
    created_by: str | None
    created_timestamp: str | None
    description: str | None


EvidenceManifestDetail: TypeAlias = (
    StrategyDecisionManifestDetail
    | ReportArtifactManifestDetail
    | StrategyReviewWorkflowManifestDetail
)


def _invalid() -> EvidenceArtifactInvalidError:
    return EvidenceArtifactInvalidError("evidence artifact is invalid")


def _not_found() -> EvidenceManifestNotFoundError:
    return EvidenceManifestNotFoundError("evidence manifest not found")


def _canonical_root(artifact_root: str | Path) -> Path:
    if not isinstance(artifact_root, (str, Path)):
        raise EvidenceArtifactRootUnavailableError(
            "evidence artifact root unavailable"
        )
    if isinstance(artifact_root, str) and not artifact_root.strip():
        raise EvidenceArtifactRootUnavailableError(
            "evidence artifact root unavailable"
        )
    try:
        root = Path(artifact_root).resolve(strict=True)
        if not root.is_dir():
            raise EvidenceArtifactRootUnavailableError(
                "evidence artifact root unavailable"
            )
    except EvidenceArtifactRootUnavailableError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise EvidenceArtifactRootUnavailableError(
            "evidence artifact root unavailable"
        ) from exc
    return root


def _manifest_type(value: object) -> EvidenceManifestType | None:
    if value in SUPPORTED_EVIDENCE_MANIFEST_TYPES:
        return value  # type: ignore[return-value]
    return None


def _valid_artifact_key(value: object) -> bool:
    return isinstance(value, str) and _ARTIFACT_KEY.fullmatch(value) is not None


def _object(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _invalid()
    return value


def _sequence(value: object) -> list[object]:
    if not isinstance(value, list):
        raise _invalid()
    return value


def _schema_version(value: object, expected: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value != expected:
        raise _invalid()


def _json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise _invalid() from exc
    return _object(payload)


def _category_directory(root: Path, manifest_type: EvidenceManifestType) -> Path | None:
    category = root / _CATEGORY_BY_TYPE[manifest_type]
    try:
        if category.is_symlink():
            raise _invalid()
        if not category.exists():
            return None
        if not category.is_dir():
            raise _invalid()
        canonical = category.resolve(strict=True)
        if not canonical.is_relative_to(root):
            raise _invalid()
    except EvidenceArtifactInvalidError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise _invalid() from exc
    return canonical


def _safe_selected_file(category: Path, artifact_key: str) -> Path:
    path = category / f"{artifact_key}.json"
    try:
        if path.is_symlink():
            raise _invalid()
        canonical = path.resolve(strict=True)
        if not canonical.is_file() or not canonical.is_relative_to(category):
            raise _invalid()
    except EvidenceArtifactInvalidError:
        raise
    except FileNotFoundError as exc:
        raise _not_found() from exc
    except (OSError, RuntimeError, ValueError) as exc:
        raise _invalid() from exc
    return canonical


def _discoverable_files(category: Path) -> tuple[tuple[str, Path], ...]:
    discovered: list[tuple[str, Path]] = []
    try:
        entries = sorted(category.iterdir(), key=lambda entry: entry.name)
        for entry in entries:
            if entry.suffix != ".json" or not _valid_artifact_key(entry.stem):
                continue
            if entry.is_symlink():
                raise _invalid()
            if not entry.is_file():
                continue
            canonical = entry.resolve(strict=True)
            if not canonical.is_relative_to(category):
                raise _invalid()
            discovered.append((entry.stem, canonical))
    except EvidenceArtifactInvalidError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise _invalid() from exc
    return tuple(discovered)


def _reference_fields(value: object, expected_schema: int) -> dict[str, Any]:
    reference = _object(value)
    _schema_version(reference.get("schema_version"), expected_schema)
    return reference


def _product_reference(reference: object) -> EvidenceManifestReference:
    return EvidenceManifestReference(
        schema_version=1,
        reference_type=reference.reference_type,  # type: ignore[attr-defined]
        reference_id=reference.reference_id,  # type: ignore[attr-defined]
        label=reference.label,  # type: ignore[attr-defined]
        description=reference.description,  # type: ignore[attr-defined]
    )


def _decision_detail(
    payload: dict[str, Any], artifact_key: str
) -> StrategyDecisionManifestDetail:
    _schema_version(payload.get("schema_version"), STRATEGY_DECISION_MANIFEST_SCHEMA_VERSION)
    try:
        summaries = tuple(
            create_strategy_decision_reference(
                reference_type=reference.get("reference_type"),
                reference_id=reference.get("reference_id"),
                label=reference.get("label"),
                description=reference.get("description"),
            )
            for reference in (
                _reference_fields(item, STRATEGY_DECISION_REFERENCE_SCHEMA_VERSION)
                for item in _sequence(payload.get("summary_references"))
            )
        )
        records = tuple(
            create_strategy_decision_reference(
                reference_type=reference.get("reference_type"),
                reference_id=reference.get("reference_id"),
                label=reference.get("label"),
                description=reference.get("description"),
            )
            for reference in (
                _reference_fields(item, STRATEGY_DECISION_REFERENCE_SCHEMA_VERSION)
                for item in _sequence(payload.get("record_references"))
            )
        )
        manifest = create_strategy_decision_manifest(
            manifest_id=payload.get("manifest_id"),
            summary_references=summaries,
            record_references=records,
            created_by=payload.get("created_by"),
            created_timestamp=payload.get("created_timestamp"),
            description=payload.get("description"),
        )
    except (TypeError, ValueError) as exc:
        raise _invalid() from exc
    serialized = manifest.to_dict()
    return StrategyDecisionManifestDetail(
        manifest_type="strategy_decision_manifest",
        artifact_key=artifact_key,
        schema_version=1,
        manifest_id=manifest.manifest_id,
        summary_references=tuple(_product_reference(item) for item in summaries),
        record_references=tuple(_product_reference(item) for item in records),
        created_by=manifest.created_by,
        created_timestamp=serialized["created_timestamp"],  # type: ignore[arg-type]
        description=manifest.description,
    )


def _report_detail(
    payload: dict[str, Any], artifact_key: str
) -> ReportArtifactManifestDetail:
    _schema_version(payload.get("schema_version"), REPORT_ARTIFACT_MANIFEST_SCHEMA_VERSION)
    try:
        references = tuple(
            create_report_artifact_reference(
                reference_type=reference.get("reference_type"),
                reference_id=reference.get("reference_id"),
                label=reference.get("label"),
                description=reference.get("description"),
            )
            for reference in (
                _reference_fields(item, REPORT_ARTIFACT_REFERENCE_SCHEMA_VERSION)
                for item in _sequence(payload.get("references"))
            )
        )
        manifest = create_report_artifact_manifest(
            manifest_id=payload.get("manifest_id"),
            references=references,
            label=payload.get("label"),
            description=payload.get("description"),
            created_by=payload.get("created_by"),
            created_timestamp=payload.get("created_timestamp"),
            notes=payload.get("notes"),
        )
    except (TypeError, ValueError) as exc:
        raise _invalid() from exc
    return ReportArtifactManifestDetail(
        manifest_type="report_artifact_manifest",
        artifact_key=artifact_key,
        schema_version=1,
        manifest_id=manifest.manifest_id,
        references=tuple(_product_reference(item) for item in references),
        label=manifest.label,
        description=manifest.description,
        created_by=manifest.created_by,
        created_timestamp=manifest.created_timestamp,
        notes=manifest.notes,
    )


def _workflow_detail(
    payload: dict[str, Any], artifact_key: str
) -> StrategyReviewWorkflowManifestDetail:
    _schema_version(
        payload.get("schema_version"), STRATEGY_REVIEW_WORKFLOW_MANIFEST_SCHEMA_VERSION
    )

    def references(field: str):
        return tuple(
            create_strategy_review_workflow_reference(
                reference_type=reference.get("reference_type"),
                reference_id=reference.get("reference_id"),
                label=reference.get("label"),
                description=reference.get("description"),
            )
            for reference in (
                _reference_fields(item, STRATEGY_REVIEW_WORKFLOW_REFERENCE_SCHEMA_VERSION)
                for item in _sequence(payload.get(field))
            )
        )

    try:
        snapshots = references("state_snapshot_references")
        proposals = references("transition_proposal_references")
        records = references("transition_record_references")
        manifest = create_strategy_review_workflow_manifest(
            manifest_id=payload.get("manifest_id"),
            state_snapshot_references=snapshots,
            transition_proposal_references=proposals,
            transition_record_references=records,
            created_by=payload.get("created_by"),
            created_timestamp=payload.get("created_timestamp"),
            description=payload.get("description"),
        )
    except (TypeError, ValueError) as exc:
        raise _invalid() from exc
    serialized = manifest.to_dict()
    return StrategyReviewWorkflowManifestDetail(
        manifest_type="strategy_review_workflow_manifest",
        artifact_key=artifact_key,
        schema_version=1,
        manifest_id=manifest.manifest_id,
        state_snapshot_references=tuple(
            _product_reference(item) for item in snapshots
        ),
        transition_proposal_references=tuple(
            _product_reference(item) for item in proposals
        ),
        transition_record_references=tuple(
            _product_reference(item) for item in records
        ),
        created_by=manifest.created_by,
        created_timestamp=serialized["created_timestamp"],  # type: ignore[arg-type]
        description=manifest.description,
    )


def _read_detail(
    path: Path,
    manifest_type: EvidenceManifestType,
    artifact_key: str,
) -> EvidenceManifestDetail:
    payload = _json_object(path)
    if manifest_type == "strategy_decision_manifest":
        return _decision_detail(payload, artifact_key)
    if manifest_type == "report_artifact_manifest":
        return _report_detail(payload, artifact_key)
    return _workflow_detail(payload, artifact_key)


def _summary(detail: EvidenceManifestDetail) -> EvidenceManifestSummary:
    if isinstance(detail, StrategyDecisionManifestDetail):
        count = len(detail.summary_references) + len(detail.record_references)
        label = None
    elif isinstance(detail, ReportArtifactManifestDetail):
        count = len(detail.references)
        label = detail.label
    else:
        count = (
            len(detail.state_snapshot_references)
            + len(detail.transition_proposal_references)
            + len(detail.transition_record_references)
        )
        label = None
    return EvidenceManifestSummary(
        manifest_type=detail.manifest_type,
        artifact_key=detail.artifact_key,
        manifest_id=detail.manifest_id,
        reference_count=count,
        created_by=detail.created_by,
        created_timestamp=detail.created_timestamp,
        label=label,
        description=detail.description,
    )


def list_evidence_manifests(
    *, artifact_root: str | Path
) -> tuple[EvidenceManifestSummary, ...]:
    """List validated direct evidence manifests in fixed deterministic order."""
    root = _canonical_root(artifact_root)
    summaries: list[EvidenceManifestSummary] = []
    for manifest_type in SUPPORTED_EVIDENCE_MANIFEST_TYPES:
        category = _category_directory(root, manifest_type)
        if category is None:
            continue
        for artifact_key, path in _discoverable_files(category):
            summaries.append(_summary(_read_detail(path, manifest_type, artifact_key)))
    return tuple(summaries)


def get_evidence_manifest_detail(
    *,
    artifact_root: str | Path,
    manifest_type: str,
    artifact_key: str,
) -> EvidenceManifestDetail:
    """Read one exact supported evidence manifest without resolving references."""
    selected_type = _manifest_type(manifest_type)
    if selected_type is None or not _valid_artifact_key(artifact_key):
        raise _not_found()
    root = _canonical_root(artifact_root)
    category = _category_directory(root, selected_type)
    if category is None:
        raise _not_found()
    path = _safe_selected_file(category, artifact_key)
    return _read_detail(path, selected_type, artifact_key)
