"""Report artifact manifest and compact reference contracts."""

from collections.abc import Sequence
from dataclasses import dataclass

from el_psy_quant.report_artifacts.summaries import ReportArtifactSummary

REPORT_ARTIFACT_REFERENCE_SCHEMA_VERSION = 1
REPORT_ARTIFACT_MANIFEST_SCHEMA_VERSION = 1

SUPPORTED_REPORT_ARTIFACT_REFERENCE_TYPES = ("report_artifact_summary",)


def _normalize_required_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _normalize_optional_string(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string when provided")
    normalized = value.strip()
    return normalized or None


def _normalize_reference_type(reference_type: str) -> str:
    if not isinstance(reference_type, str):
        raise ValueError("reference_type must be a string")
    normalized = reference_type.strip()
    if normalized not in SUPPORTED_REPORT_ARTIFACT_REFERENCE_TYPES:
        supported = ", ".join(SUPPORTED_REPORT_ARTIFACT_REFERENCE_TYPES)
        raise ValueError(
            f"unsupported reference_type: {reference_type}; supported: {supported}"
        )
    return normalized


@dataclass(frozen=True)
class ReportArtifactReference:
    """Immutable compact reference to a report artifact summary."""

    reference_type: str
    reference_id: str
    label: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reference_type",
            _normalize_reference_type(self.reference_type),
        )
        object.__setattr__(
            self,
            "reference_id",
            _normalize_required_string(self.reference_id, "reference_id"),
        )
        object.__setattr__(
            self,
            "label",
            _normalize_optional_string(self.label, "label"),
        )
        object.__setattr__(
            self,
            "description",
            _normalize_optional_string(self.description, "description"),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible report artifact reference."""
        return {
            "schema_version": REPORT_ARTIFACT_REFERENCE_SCHEMA_VERSION,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "label": self.label,
            "description": self.description,
        }


def _normalize_references(
    references: Sequence[ReportArtifactReference],
) -> tuple[ReportArtifactReference, ...]:
    if isinstance(references, ReportArtifactReference):
        raise ValueError(
            "references must be a non-empty sequence of "
            "ReportArtifactReference objects"
        )
    if isinstance(references, str) or not isinstance(references, Sequence):
        raise ValueError(
            "references must be a non-empty sequence of "
            "ReportArtifactReference objects"
        )

    normalized = tuple(references)
    if not normalized:
        raise ValueError("references must not be empty")
    for reference in normalized:
        if not isinstance(reference, ReportArtifactReference):
            raise ValueError(
                "references must contain only ReportArtifactReference objects"
            )
    return normalized


@dataclass(frozen=True)
class ReportArtifactManifest:
    """Immutable local manifest of explicit report artifact references."""

    manifest_id: str
    references: tuple[ReportArtifactReference, ...]
    label: str | None = None
    description: str | None = None
    created_by: str | None = None
    created_timestamp: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "manifest_id",
            _normalize_required_string(self.manifest_id, "manifest_id"),
        )
        object.__setattr__(self, "references", _normalize_references(self.references))
        object.__setattr__(
            self,
            "label",
            _normalize_optional_string(self.label, "label"),
        )
        object.__setattr__(
            self,
            "description",
            _normalize_optional_string(self.description, "description"),
        )
        object.__setattr__(
            self,
            "created_by",
            _normalize_optional_string(self.created_by, "created_by"),
        )
        object.__setattr__(
            self,
            "created_timestamp",
            _normalize_optional_string(
                self.created_timestamp,
                "created_timestamp",
            ),
        )
        object.__setattr__(
            self,
            "notes",
            _normalize_optional_string(self.notes, "notes"),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible report artifact manifest."""
        return {
            "schema_version": REPORT_ARTIFACT_MANIFEST_SCHEMA_VERSION,
            "manifest_id": self.manifest_id,
            "references": [reference.to_dict() for reference in self.references],
            "label": self.label,
            "description": self.description,
            "created_by": self.created_by,
            "created_timestamp": self.created_timestamp,
            "notes": self.notes,
        }


def create_report_artifact_reference(
    *,
    reference_type: str,
    reference_id: str,
    label: str | None = None,
    description: str | None = None,
) -> ReportArtifactReference:
    """Create and validate one compact report artifact reference."""
    return ReportArtifactReference(
        reference_type=reference_type,
        reference_id=reference_id,
        label=label,
        description=description,
    )


def create_report_artifact_manifest(
    *,
    manifest_id: str,
    references: Sequence[ReportArtifactReference],
    label: str | None = None,
    description: str | None = None,
    created_by: str | None = None,
    created_timestamp: str | None = None,
    notes: str | None = None,
) -> ReportArtifactManifest:
    """Create and validate one local report artifact manifest."""
    return ReportArtifactManifest(
        manifest_id=manifest_id,
        references=references,  # type: ignore[arg-type]
        label=label,
        description=description,
        created_by=created_by,
        created_timestamp=created_timestamp,
        notes=notes,
    )


def create_report_artifact_reference_from_summary(
    summary: ReportArtifactSummary,
    *,
    label: str | None = None,
    description: str | None = None,
) -> ReportArtifactReference:
    """Reference an existing summary by its stable report ID only."""
    if not isinstance(summary, ReportArtifactSummary):
        raise ValueError("summary must be a ReportArtifactSummary")
    return create_report_artifact_reference(
        reference_type="report_artifact_summary",
        reference_id=summary.report_id,
        label=label,
        description=description,
    )
