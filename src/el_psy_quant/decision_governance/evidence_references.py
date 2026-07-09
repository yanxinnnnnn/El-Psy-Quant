"""Decision evidence reference contract."""

from dataclasses import dataclass

DECISION_EVIDENCE_REFERENCE_SCHEMA_VERSION = 1

SUPPORTED_DECISION_EVIDENCE_REFERENCE_TYPES = (
    "promotion_record",
    "promotion_candidate_reference",
    "promotion_manifest",
    "paper_comparison_summary",
    "paper_review_decision",
    "paper_review_manifest",
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
    if not isinstance(reference_type, str):
        raise ValueError("reference_type must be a string")
    normalized = reference_type.strip()
    if not normalized:
        raise ValueError("reference_type must be a non-empty string")
    if normalized not in SUPPORTED_DECISION_EVIDENCE_REFERENCE_TYPES:
        supported = ", ".join(SUPPORTED_DECISION_EVIDENCE_REFERENCE_TYPES)
        raise ValueError(
            f"unsupported reference_type: {reference_type}; supported: {supported}"
        )
    return normalized


@dataclass(frozen=True)
class DecisionEvidenceReference:
    """Immutable reference to existing promotion or paper-review evidence."""

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
        """Return a deterministic JSON-compatible evidence reference export."""
        return {
            "schema_version": DECISION_EVIDENCE_REFERENCE_SCHEMA_VERSION,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "label": self.label,
            "description": self.description,
        }


def create_decision_evidence_reference(
    *,
    reference_type: str,
    reference_id: str,
    label: str | None = None,
    description: str | None = None,
) -> DecisionEvidenceReference:
    """Create and validate one decision evidence reference."""
    return DecisionEvidenceReference(
        reference_type=reference_type,
        reference_id=reference_id,
        label=label,
        description=description,
    )
