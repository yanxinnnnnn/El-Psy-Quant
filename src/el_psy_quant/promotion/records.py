"""Explicit promotion record contract."""

from dataclasses import dataclass

import pandas as pd

from el_psy_quant.promotion.evidence import PromotionEvidenceSummary

PROMOTION_RECORD_SCHEMA_VERSION = 1

PROMOTION_RECORD_STATUSES = (
    "proposed",
    "approved_for_paper",
    "rejected",
    "deferred",
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


def _normalize_status(status: str) -> str:
    if not isinstance(status, str):
        raise ValueError("status must be a string")
    normalized = status.strip()
    if normalized not in PROMOTION_RECORD_STATUSES:
        supported = ", ".join(PROMOTION_RECORD_STATUSES)
        raise ValueError(f"unsupported promotion status: {status}; supported: {supported}")
    return normalized


def _normalize_optional_timestamp(created_timestamp: object | None) -> pd.Timestamp | None:
    if created_timestamp is None:
        return None
    try:
        normalized = pd.Timestamp(created_timestamp)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "created_timestamp must be convertible to a pandas Timestamp"
        ) from exc

    if pd.isna(normalized):
        raise ValueError("created_timestamp must be valid")
    return normalized


def _validate_evidence_summary(
    evidence_summary: PromotionEvidenceSummary,
) -> PromotionEvidenceSummary:
    if not isinstance(evidence_summary, PromotionEvidenceSummary):
        raise ValueError("evidence_summary must be a PromotionEvidenceSummary")
    return evidence_summary


@dataclass(frozen=True)
class PromotionRecord:
    """Immutable human-controlled research-to-paper promotion record."""

    record_id: str
    evidence_summary: PromotionEvidenceSummary
    status: str
    rationale: str
    reviewer: str | None = None
    created_timestamp: object | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "record_id",
            _normalize_required_string(self.record_id, "record_id"),
        )
        object.__setattr__(
            self,
            "evidence_summary",
            _validate_evidence_summary(self.evidence_summary),
        )
        object.__setattr__(self, "status", _normalize_status(self.status))
        object.__setattr__(
            self,
            "rationale",
            _normalize_required_string(self.rationale, "rationale"),
        )
        object.__setattr__(
            self,
            "reviewer",
            _normalize_optional_string(self.reviewer, "reviewer"),
        )
        object.__setattr__(
            self,
            "created_timestamp",
            _normalize_optional_timestamp(self.created_timestamp),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible promotion record export."""
        return {
            "schema_version": PROMOTION_RECORD_SCHEMA_VERSION,
            "record_id": self.record_id,
            "evidence_summary": self.evidence_summary.to_dict(),
            "status": self.status,
            "rationale": self.rationale,
            "reviewer": self.reviewer,
            "created_timestamp": (
                None
                if self.created_timestamp is None
                else self.created_timestamp.isoformat()
            ),
        }


def create_promotion_record(
    *,
    record_id: str,
    evidence_summary: PromotionEvidenceSummary,
    status: str,
    rationale: str,
    reviewer: str | None = None,
    created_timestamp: object | None = None,
) -> PromotionRecord:
    """Create and validate one explicit human-controlled promotion record."""
    return PromotionRecord(
        record_id=record_id,
        evidence_summary=evidence_summary,
        status=status,
        rationale=rationale,
        reviewer=reviewer,
        created_timestamp=created_timestamp,
    )
