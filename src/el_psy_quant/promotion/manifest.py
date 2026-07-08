"""Promotion manifest and candidate reference contracts."""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from el_psy_quant.promotion.records import (
    PROMOTION_RECORD_STATUSES,
    PromotionRecord,
)

PROMOTION_CANDIDATE_REFERENCE_SCHEMA_VERSION = 1
PROMOTION_MANIFEST_SCHEMA_VERSION = 1


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
        raise ValueError(
            f"unsupported promotion status: {status}; supported: {supported}"
        )
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


def _normalize_promotion_records(
    promotion_records: Sequence[PromotionRecord],
) -> tuple[PromotionRecord, ...]:
    if isinstance(promotion_records, str) or not isinstance(
        promotion_records,
        Sequence,
    ):
        raise ValueError(
            "promotion_records must be a non-empty sequence of PromotionRecord "
            "objects"
        )

    normalized = tuple(promotion_records)
    if not normalized:
        raise ValueError("promotion_records must not be empty")

    for promotion_record in normalized:
        if not isinstance(promotion_record, PromotionRecord):
            raise ValueError(
                "promotion_records must contain only PromotionRecord objects"
            )
    return normalized


def _normalize_candidate_references(
    candidate_references: Sequence["PromotionCandidateReference"],
) -> tuple["PromotionCandidateReference", ...]:
    if isinstance(candidate_references, str) or not isinstance(
        candidate_references,
        Sequence,
    ):
        raise ValueError(
            "candidate_references must be a non-empty sequence of "
            "PromotionCandidateReference objects"
        )

    normalized = tuple(candidate_references)
    if not normalized:
        raise ValueError("candidate_references must not be empty")

    for candidate_reference in normalized:
        if not isinstance(candidate_reference, PromotionCandidateReference):
            raise ValueError(
                "candidate_references must contain only "
                "PromotionCandidateReference objects"
            )
    return normalized


@dataclass(frozen=True)
class PromotionCandidateReference:
    """Compact deterministic reference to a paper promotion candidate."""

    record_id: str
    candidate_id: str
    status: str
    reference: str | None = None
    label: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "record_id",
            _normalize_required_string(self.record_id, "record_id"),
        )
        object.__setattr__(
            self,
            "candidate_id",
            _normalize_required_string(self.candidate_id, "candidate_id"),
        )
        object.__setattr__(self, "status", _normalize_status(self.status))
        object.__setattr__(
            self,
            "reference",
            _normalize_optional_string(self.reference, "reference"),
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
        """Return a deterministic JSON-compatible candidate reference export."""
        return {
            "schema_version": PROMOTION_CANDIDATE_REFERENCE_SCHEMA_VERSION,
            "record_id": self.record_id,
            "candidate_id": self.candidate_id,
            "status": self.status,
            "reference": self.reference,
            "label": self.label,
            "description": self.description,
        }


@dataclass(frozen=True)
class PromotionManifest:
    """Immutable local promotion manifest for manual inspection."""

    manifest_id: str
    promotion_records: Sequence[PromotionRecord]
    candidate_references: Sequence[PromotionCandidateReference]
    created_timestamp: object | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "manifest_id",
            _normalize_required_string(self.manifest_id, "manifest_id"),
        )
        object.__setattr__(
            self,
            "promotion_records",
            _normalize_promotion_records(self.promotion_records),
        )
        object.__setattr__(
            self,
            "candidate_references",
            _normalize_candidate_references(self.candidate_references),
        )
        object.__setattr__(
            self,
            "created_timestamp",
            _normalize_optional_timestamp(self.created_timestamp),
        )
        object.__setattr__(
            self,
            "description",
            _normalize_optional_string(self.description, "description"),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible promotion manifest export."""
        return {
            "schema_version": PROMOTION_MANIFEST_SCHEMA_VERSION,
            "manifest_id": self.manifest_id,
            "promotion_records": [
                promotion_record.to_dict()
                for promotion_record in self.promotion_records
            ],
            "candidate_references": [
                candidate_reference.to_dict()
                for candidate_reference in self.candidate_references
            ],
            "created_timestamp": (
                None
                if self.created_timestamp is None
                else self.created_timestamp.isoformat()
            ),
            "description": self.description,
        }


def create_promotion_candidate_reference(
    *,
    record_id: str,
    candidate_id: str,
    status: str,
    reference: str | None = None,
    label: str | None = None,
    description: str | None = None,
) -> PromotionCandidateReference:
    """Create and validate one compact promotion candidate reference."""
    return PromotionCandidateReference(
        record_id=record_id,
        candidate_id=candidate_id,
        status=status,
        reference=reference,
        label=label,
        description=description,
    )


def create_promotion_manifest(
    *,
    manifest_id: str,
    promotion_records: Sequence[PromotionRecord],
    candidate_references: Sequence[PromotionCandidateReference],
    created_timestamp: object | None = None,
    description: str | None = None,
) -> PromotionManifest:
    """Create and validate one local promotion manifest."""
    return PromotionManifest(
        manifest_id=manifest_id,
        promotion_records=promotion_records,
        candidate_references=candidate_references,
        created_timestamp=created_timestamp,
        description=description,
    )
