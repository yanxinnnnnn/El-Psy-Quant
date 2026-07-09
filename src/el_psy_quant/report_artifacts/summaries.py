"""Report artifact summary contract."""

from collections.abc import Sequence
from dataclasses import dataclass

from el_psy_quant.report_artifacts.sections import ReportSection

REPORT_ARTIFACT_SUMMARY_SCHEMA_VERSION = 1


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


def _normalize_sections(
    sections: Sequence[ReportSection],
) -> tuple[ReportSection, ...]:
    if isinstance(sections, ReportSection):
        raise ValueError(
            "sections must be a non-empty sequence of ReportSection objects"
        )
    if isinstance(sections, str) or not isinstance(sections, Sequence):
        raise ValueError(
            "sections must be a non-empty sequence of ReportSection objects"
        )

    normalized = tuple(sections)
    if not normalized:
        raise ValueError("sections must not be empty")

    for section in normalized:
        if not isinstance(section, ReportSection):
            raise ValueError("sections must contain only ReportSection objects")
    return normalized


@dataclass(frozen=True)
class ReportArtifactSummary:
    """Immutable caller-supplied report artifact summary."""

    report_id: str
    title: str
    sections: Sequence[ReportSection]
    summary: str | None = None
    purpose: str | None = None
    created_by: str | None = None
    created_timestamp: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "report_id",
            _normalize_required_string(self.report_id, "report_id"),
        )
        object.__setattr__(
            self,
            "title",
            _normalize_required_string(self.title, "title"),
        )
        object.__setattr__(
            self,
            "sections",
            _normalize_sections(self.sections),
        )
        object.__setattr__(
            self,
            "summary",
            _normalize_optional_string(self.summary, "summary"),
        )
        object.__setattr__(
            self,
            "purpose",
            _normalize_optional_string(self.purpose, "purpose"),
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
        """Return a deterministic JSON-compatible report artifact summary."""
        return {
            "schema_version": REPORT_ARTIFACT_SUMMARY_SCHEMA_VERSION,
            "report_id": self.report_id,
            "title": self.title,
            "sections": [section.to_dict() for section in self.sections],
            "summary": self.summary,
            "purpose": self.purpose,
            "created_by": self.created_by,
            "created_timestamp": self.created_timestamp,
            "notes": self.notes,
        }


def create_report_artifact_summary(
    *,
    report_id: str,
    title: str,
    sections: Sequence[ReportSection],
    summary: str | None = None,
    purpose: str | None = None,
    created_by: str | None = None,
    created_timestamp: str | None = None,
    notes: str | None = None,
) -> ReportArtifactSummary:
    """Create and validate one report artifact summary."""
    return ReportArtifactSummary(
        report_id=report_id,
        title=title,
        sections=sections,
        summary=summary,
        purpose=purpose,
        created_by=created_by,
        created_timestamp=created_timestamp,
        notes=notes,
    )
