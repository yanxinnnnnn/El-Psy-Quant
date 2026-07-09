"""Report section contract."""

from collections.abc import Sequence
from dataclasses import dataclass

from el_psy_quant.report_artifacts.source_references import (
    ReportSourceReference,
)

REPORT_SECTION_SCHEMA_VERSION = 1


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


def _normalize_source_references(
    source_references: Sequence[ReportSourceReference],
) -> tuple[ReportSourceReference, ...]:
    if isinstance(source_references, ReportSourceReference):
        raise ValueError(
            "source_references must be a sequence of ReportSourceReference objects"
        )
    if isinstance(source_references, str) or not isinstance(
        source_references,
        Sequence,
    ):
        raise ValueError(
            "source_references must be a sequence of ReportSourceReference objects"
        )

    normalized = tuple(source_references)
    for source_reference in normalized:
        if not isinstance(source_reference, ReportSourceReference):
            raise ValueError(
                "source_references must contain only ReportSourceReference objects"
            )
    return normalized


@dataclass(frozen=True)
class ReportSection:
    """Immutable caller-supplied report section."""

    section_id: str
    title: str
    content: str
    source_references: Sequence[ReportSourceReference] = ()
    section_type: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "section_id",
            _normalize_required_string(self.section_id, "section_id"),
        )
        object.__setattr__(
            self,
            "title",
            _normalize_required_string(self.title, "title"),
        )
        object.__setattr__(
            self,
            "content",
            _normalize_required_string(self.content, "content"),
        )
        object.__setattr__(
            self,
            "source_references",
            _normalize_source_references(self.source_references),
        )
        object.__setattr__(
            self,
            "section_type",
            _normalize_optional_string(self.section_type, "section_type"),
        )
        object.__setattr__(
            self,
            "notes",
            _normalize_optional_string(self.notes, "notes"),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible report section."""
        return {
            "schema_version": REPORT_SECTION_SCHEMA_VERSION,
            "section_id": self.section_id,
            "title": self.title,
            "content": self.content,
            "source_references": [
                source_reference.to_dict()
                for source_reference in self.source_references
            ],
            "section_type": self.section_type,
            "notes": self.notes,
        }


def create_report_section(
    *,
    section_id: str,
    title: str,
    content: str,
    source_references: Sequence[ReportSourceReference] = (),
    section_type: str | None = None,
    notes: str | None = None,
) -> ReportSection:
    """Create and validate one report section."""
    return ReportSection(
        section_id=section_id,
        title=title,
        content=content,
        source_references=source_references,
        section_type=section_type,
        notes=notes,
    )
