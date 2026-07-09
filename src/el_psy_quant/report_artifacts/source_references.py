"""Report source reference contract."""

from dataclasses import dataclass

REPORT_SOURCE_REFERENCE_SCHEMA_VERSION = 1

SUPPORTED_REPORT_SOURCE_REFERENCE_TYPES = (
    "promotion_evidence_summary",
    "promotion_record",
    "promotion_manifest",
    "paper_comparison_summary",
    "paper_review_decision",
    "paper_review_manifest",
    "strategy_decision_summary",
    "strategy_decision_record",
    "strategy_decision_manifest",
)


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
    normalized = _normalize_required_string(reference_type, "reference_type")
    if normalized not in SUPPORTED_REPORT_SOURCE_REFERENCE_TYPES:
        supported = ", ".join(SUPPORTED_REPORT_SOURCE_REFERENCE_TYPES)
        raise ValueError(
            f"unsupported reference_type: {reference_type}; supported: {supported}"
        )
    return normalized


@dataclass(frozen=True)
class ReportSourceReference:
    """Immutable reference to completed governance evidence for future reports."""

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
        """Return a deterministic JSON-compatible report source reference."""
        return {
            "schema_version": REPORT_SOURCE_REFERENCE_SCHEMA_VERSION,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "label": self.label,
            "description": self.description,
        }


def create_report_source_reference(
    *,
    reference_type: str,
    reference_id: str,
    label: str | None = None,
    description: str | None = None,
) -> ReportSourceReference:
    """Create and validate one report source reference."""
    return ReportSourceReference(
        reference_type=reference_type,
        reference_id=reference_id,
        label=label,
        description=description,
    )
