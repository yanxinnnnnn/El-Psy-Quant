"""Immutable evidence and component inputs for portfolio review."""

from collections.abc import Sequence
from dataclasses import dataclass

from el_psy_quant.data.universe import build_symbol_universe

PORTFOLIO_REVIEW_EVIDENCE_REFERENCE_SCHEMA_VERSION = 1
PORTFOLIO_REVIEW_COMPONENT_SCHEMA_VERSION = 1

SUPPORTED_PORTFOLIO_REVIEW_EVIDENCE_REFERENCE_TYPES = (
    "research_run",
    "configured_run",
    "backtest_artifact",
    "portfolio_artifact",
    "attribution_artifact",
    "promotion_record",
    "paper_comparison_summary",
    "paper_review_decision",
    "strategy_decision_record",
    "report_artifact_summary",
    "strategy_lifecycle_state_snapshot",
    "strategy_lifecycle_transition_record",
)

PORTFOLIO_REVIEW_RESEARCH_ORIGIN_REFERENCE_TYPES = (
    "research_run",
    "configured_run",
    "backtest_artifact",
    "portfolio_artifact",
    "attribution_artifact",
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
    if normalized not in SUPPORTED_PORTFOLIO_REVIEW_EVIDENCE_REFERENCE_TYPES:
        supported = ", ".join(
            SUPPORTED_PORTFOLIO_REVIEW_EVIDENCE_REFERENCE_TYPES
        )
        raise ValueError(
            f"unsupported reference_type: {reference_type}; supported: {supported}"
        )
    return normalized


@dataclass(frozen=True)
class PortfolioReviewEvidenceReference:
    """Immutable pointer to evidence used to identify one review component."""

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
        """Return a deterministic JSON-compatible evidence pointer."""
        return {
            "schema_version": PORTFOLIO_REVIEW_EVIDENCE_REFERENCE_SCHEMA_VERSION,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "label": self.label,
            "description": self.description,
        }


def create_portfolio_review_evidence_reference(
    *,
    reference_type: str,
    reference_id: str,
    label: str | None = None,
    description: str | None = None,
) -> PortfolioReviewEvidenceReference:
    """Create one validated portfolio-review evidence pointer."""
    return PortfolioReviewEvidenceReference(
        reference_type=reference_type,
        reference_id=reference_id,
        label=label,
        description=description,
    )


def _normalize_evidence_references(
    evidence_references: Sequence[PortfolioReviewEvidenceReference],
) -> tuple[PortfolioReviewEvidenceReference, ...]:
    if isinstance(evidence_references, (str, bytes)):
        raise ValueError("evidence_references must be a sequence of references")
    try:
        normalized = tuple(evidence_references)
    except TypeError as exc:
        raise ValueError(
            "evidence_references must be a sequence of references"
        ) from exc
    if not normalized:
        raise ValueError("evidence_references must not be empty")

    seen: set[tuple[str, str]] = set()
    has_research_origin = False
    for reference in normalized:
        if type(reference) is not PortfolioReviewEvidenceReference:
            raise ValueError(
                "evidence_references must contain "
                "PortfolioReviewEvidenceReference values"
            )
        identity = (reference.reference_type, reference.reference_id)
        if identity in seen:
            raise ValueError(
                "duplicate evidence reference: "
                f"{reference.reference_type}/{reference.reference_id}"
            )
        seen.add(identity)
        if (
            reference.reference_type
            in PORTFOLIO_REVIEW_RESEARCH_ORIGIN_REFERENCE_TYPES
        ):
            has_research_origin = True

    if not has_research_origin:
        raise ValueError(
            "evidence_references must include at least one research-origin reference"
        )
    return normalized


@dataclass(frozen=True)
class PortfolioReviewComponent:
    """One immutable strategy return stream included in a review source."""

    component_id: str
    strategy_id: str
    evidence_references: tuple[PortfolioReviewEvidenceReference, ...]
    symbols: tuple[str, ...] | None = None
    label: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "component_id",
            _normalize_required_string(self.component_id, "component_id"),
        )
        object.__setattr__(
            self,
            "strategy_id",
            _normalize_required_string(self.strategy_id, "strategy_id"),
        )
        object.__setattr__(
            self,
            "evidence_references",
            _normalize_evidence_references(self.evidence_references),
        )
        if self.symbols is not None:
            object.__setattr__(
                self,
                "symbols",
                build_symbol_universe(self.symbols),
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
        """Return a deterministic JSON-compatible component export."""
        return {
            "schema_version": PORTFOLIO_REVIEW_COMPONENT_SCHEMA_VERSION,
            "component_id": self.component_id,
            "strategy_id": self.strategy_id,
            "evidence_references": [
                reference.to_dict() for reference in self.evidence_references
            ],
            "symbols": list(self.symbols) if self.symbols is not None else None,
            "label": self.label,
            "description": self.description,
        }


def create_portfolio_review_component(
    *,
    component_id: str,
    strategy_id: str,
    evidence_references: Sequence[PortfolioReviewEvidenceReference],
    symbols: Sequence[str] | None = None,
    label: str | None = None,
    description: str | None = None,
) -> PortfolioReviewComponent:
    """Create one validated immutable portfolio-review component."""
    return PortfolioReviewComponent(
        component_id=component_id,
        strategy_id=strategy_id,
        evidence_references=_normalize_evidence_references(evidence_references),
        symbols=None if symbols is None else build_symbol_universe(symbols),
        label=label,
        description=description,
    )
