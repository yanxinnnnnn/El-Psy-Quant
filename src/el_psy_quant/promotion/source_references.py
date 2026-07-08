"""Promotion source reference contract."""

from dataclasses import dataclass

PROMOTION_SOURCE_REFERENCE_SCHEMA_VERSION = 1

SUPPORTED_PROMOTION_SOURCE_TYPES = (
    "research_run",
    "backtest_artifact",
    "execution_artifact",
    "portfolio_artifact",
    "configured_run",
    "paper_artifact",
    "paper_result_summary",
)


def _normalize_source_type(source_type: str) -> str:
    if not isinstance(source_type, str):
        raise ValueError("source_type must be a string")
    normalized = source_type.strip()
    if normalized not in SUPPORTED_PROMOTION_SOURCE_TYPES:
        supported = ", ".join(SUPPORTED_PROMOTION_SOURCE_TYPES)
        raise ValueError(f"unsupported source_type: {source_type}; supported: {supported}")
    return normalized


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


@dataclass(frozen=True)
class PromotionSourceReference:
    """Immutable reference to local or logical promotion evidence."""

    source_type: str
    reference: str
    run_id: str | None = None
    artifact_id: str | None = None
    label: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_type", _normalize_source_type(self.source_type))
        object.__setattr__(
            self,
            "reference",
            _normalize_required_string(self.reference, "reference"),
        )
        object.__setattr__(
            self,
            "run_id",
            _normalize_optional_string(self.run_id, "run_id"),
        )
        object.__setattr__(
            self,
            "artifact_id",
            _normalize_optional_string(self.artifact_id, "artifact_id"),
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
        """Return a deterministic JSON-compatible source reference export."""
        return {
            "schema_version": PROMOTION_SOURCE_REFERENCE_SCHEMA_VERSION,
            "source_type": self.source_type,
            "reference": self.reference,
            "run_id": self.run_id,
            "artifact_id": self.artifact_id,
            "label": self.label,
            "description": self.description,
        }


def create_promotion_source_reference(
    *,
    source_type: str,
    reference: str,
    run_id: str | None = None,
    artifact_id: str | None = None,
    label: str | None = None,
    description: str | None = None,
) -> PromotionSourceReference:
    """Create and validate one promotion source reference."""
    return PromotionSourceReference(
        source_type=source_type,
        reference=reference,
        run_id=run_id,
        artifact_id=artifact_id,
        label=label,
        description=description,
    )
