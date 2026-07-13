"""Immutable compact product artifact-index entries."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath
from typing import Literal, TypeAlias, cast

ARTIFACT_INDEX_RECORD_SCHEMA_VERSION = 1

ArtifactType: TypeAlias = Literal[
    "research_run_manifest",
    "strategy_decision_manifest",
    "report_artifact_manifest",
    "strategy_review_workflow_manifest",
]
ArtifactRootType: TypeAlias = Literal["research", "evidence"]

SUPPORTED_ARTIFACT_TYPES: tuple[ArtifactType, ...] = (
    "research_run_manifest",
    "strategy_decision_manifest",
    "report_artifact_manifest",
    "strategy_review_workflow_manifest",
)
SUPPORTED_ARTIFACT_ROOT_TYPES: tuple[ArtifactRootType, ...] = (
    "research",
    "evidence",
)

_ROOT_TYPE_BY_ARTIFACT_TYPE: dict[ArtifactType, ArtifactRootType] = {
    "research_run_manifest": "research",
    "strategy_decision_manifest": "evidence",
    "report_artifact_manifest": "evidence",
    "strategy_review_workflow_manifest": "evidence",
}
_EVIDENCE_CATEGORY_BY_ARTIFACT_TYPE: dict[ArtifactType, str] = {
    "strategy_decision_manifest": "strategy-decisions",
    "report_artifact_manifest": "report-artifacts",
    "strategy_review_workflow_manifest": "strategy-review",
}
_EXPERIMENT_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_RUN_OR_ARTIFACT_KEY = re.compile(r"[A-Za-z0-9_-]+\Z")


def _artifact_type(value: object) -> ArtifactType:
    if not isinstance(value, str) or value not in SUPPORTED_ARTIFACT_TYPES:
        raise ValueError("artifact_type is unsupported")
    return cast(ArtifactType, value)


def _root_type(value: object) -> ArtifactRootType:
    if not isinstance(value, str) or value not in SUPPORTED_ARTIFACT_ROOT_TYPES:
        raise ValueError("root_type is unsupported")
    return cast(ArtifactRootType, value)


def _artifact_key(artifact_type: ArtifactType, value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("artifact_key is invalid")
    if artifact_type == "research_run_manifest":
        parts = value.split("/")
        if (
            len(parts) != 2
            or _EXPERIMENT_SLUG.fullmatch(parts[0]) is None
            or _RUN_OR_ARTIFACT_KEY.fullmatch(parts[1]) is None
        ):
            raise ValueError("artifact_key is invalid for research_run_manifest")
        return value
    if _RUN_OR_ARTIFACT_KEY.fullmatch(value) is None:
        raise ValueError("artifact_key is invalid for evidence manifest")
    return value


def _expected_locator(artifact_type: ArtifactType, artifact_key: str) -> str:
    if artifact_type == "research_run_manifest":
        return f"{artifact_key}/manifest.json"
    return f"{_EVIDENCE_CATEGORY_BY_ARTIFACT_TYPE[artifact_type]}/{artifact_key}.json"


def _relative_path(value: object) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("relative_path must be a normalized relative POSIX path")
    posix_path = PurePosixPath(value)
    windows_path = PureWindowsPath(value)
    raw_parts = value.split("/")
    if (
        "\\" in value
        or posix_path.is_absolute()
        or windows_path.is_absolute()
        or bool(windows_path.drive)
        or any(part in ("", ".", "..") for part in raw_parts)
    ):
        raise ValueError("relative_path must be a normalized relative POSIX path")
    return value


def _source_id(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError("source_id must be a normalized non-empty string")
    return value


@dataclass(frozen=True)
class ArtifactIndexEntry:
    """Compact rebuildable pointer to one authoritative artifact manifest."""

    record_schema_version: Literal[1]
    artifact_type: ArtifactType
    artifact_key: str
    root_type: ArtifactRootType
    relative_path: str
    source_id: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.record_schema_version, int)
            or isinstance(self.record_schema_version, bool)
            or self.record_schema_version != ARTIFACT_INDEX_RECORD_SCHEMA_VERSION
        ):
            raise ValueError("record_schema_version must be 1")
        artifact_type = _artifact_type(self.artifact_type)
        artifact_key = _artifact_key(artifact_type, self.artifact_key)
        root_type = _root_type(self.root_type)
        if root_type != _ROOT_TYPE_BY_ARTIFACT_TYPE[artifact_type]:
            raise ValueError("artifact_type and root_type do not match")
        relative_path = _relative_path(self.relative_path)
        if relative_path != _expected_locator(artifact_type, artifact_key):
            raise ValueError("relative_path does not match the supported layout")
        source_id = _source_id(self.source_id)
        if (
            artifact_type == "research_run_manifest"
            and source_id != artifact_key.split("/", maxsplit=1)[1]
        ):
            raise ValueError("research source_id must match the indexed run_id")


def create_artifact_index_entry(
    *,
    artifact_type: str,
    artifact_key: str,
    source_id: str,
) -> ArtifactIndexEntry:
    """Create an entry with the approved root and exact fixed locator."""
    normalized_type = _artifact_type(artifact_type)
    normalized_key = _artifact_key(normalized_type, artifact_key)
    return ArtifactIndexEntry(
        record_schema_version=1,
        artifact_type=normalized_type,
        artifact_key=normalized_key,
        root_type=_ROOT_TYPE_BY_ARTIFACT_TYPE[normalized_type],
        relative_path=_expected_locator(normalized_type, normalized_key),
        source_id=source_id,
    )
