"""Bounded approved-M30 governance evidence references."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

from el_psy_quant.portfolio_review.decision_artifacts import (
    PORTFOLIO_REVIEW_DECISION_SCOPE,
    PortfolioReviewDecisionArtifact,
)

APPROVED_PORTFOLIO_REVIEW_REFERENCE_SCHEMA_VERSION = 1

ApprovedPortfolioReviewOutcome = Literal["approved"]

_MAX_REFERENCE_ID_LENGTH = 512
_LOWERCASE_HEXADECIMAL = frozenset("0123456789abcdef")


def _canonical_digest(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_id(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty exact string")
    if len(value) > _MAX_REFERENCE_ID_LENGTH:
        raise ValueError(
            f"{field_name} must be at most {_MAX_REFERENCE_ID_LENGTH} characters"
        )
    return value


def _validate_digest(value: object, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _LOWERCASE_HEXADECIMAL for character in value)
    ):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _reject_public_construction(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise TypeError(
        "approved portfolio-review references are created by the trusted factory"
    )


@dataclass(frozen=True, init=False)
class ApprovedPortfolioReviewReference:
    """A governance-provenance edge with no account mutation authority."""

    review_id: str
    source_id: str
    source_digest: str
    analysis_digest: str
    decision_id: str
    decision_digest: str
    outcome: ApprovedPortfolioReviewOutcome

    __init__ = _reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return the minimal deterministic JSON-compatible provenance edge."""
        return {
            "schema_version": (
                APPROVED_PORTFOLIO_REVIEW_REFERENCE_SCHEMA_VERSION
            ),
            "review_id": self.review_id,
            "source_id": self.source_id,
            "source_digest": self.source_digest,
            "analysis_digest": self.analysis_digest,
            "decision_id": self.decision_id,
            "decision_digest": self.decision_digest,
            "outcome": self.outcome,
        }


def create_approved_portfolio_review_reference(
    decision: PortfolioReviewDecisionArtifact,
) -> ApprovedPortfolioReviewReference:
    """Create a bounded reference from one genuine approved M30 decision."""
    if type(decision) is not PortfolioReviewDecisionArtifact:
        raise ValueError(
            "decision must be a PortfolioReviewDecisionArtifact"
        )
    if decision.decision_scope != PORTFOLIO_REVIEW_DECISION_SCOPE:
        raise ValueError("decision must use the governance-only decision scope")
    if decision.outcome != "approved":
        raise ValueError("decision outcome must be approved")

    review_id = _validate_id(decision.review_id, "review_id")
    source_id = _validate_id(decision.source_id, "source_id")
    decision_id = _validate_id(decision.decision_id, "decision_id")
    source_digest = _validate_digest(decision.source_digest, "source_digest")
    analysis_digest = _validate_digest(
        decision.analysis_digest,
        "analysis_digest",
    )
    decision_digest = _validate_digest(
        decision.decision_digest,
        "decision_digest",
    )

    _validate_id(decision.baseline_scenario_id, "baseline_scenario_id")
    _validate_id(decision.proposed_scenario_id, "proposed_scenario_id")
    _validate_digest(
        decision.baseline_scenario_digest,
        "baseline_scenario_digest",
    )
    _validate_digest(
        decision.proposed_scenario_digest,
        "proposed_scenario_digest",
    )

    decision_payload = decision.to_dict()
    exported_digest = decision_payload.pop("decision_digest", None)
    if exported_digest != decision_digest or (
        _canonical_digest(decision_payload) != decision_digest
    ):
        raise ValueError("decision digest does not match its canonical payload")

    result = object.__new__(ApprovedPortfolioReviewReference)
    object.__setattr__(result, "review_id", review_id)
    object.__setattr__(result, "source_id", source_id)
    object.__setattr__(result, "source_digest", source_digest)
    object.__setattr__(result, "analysis_digest", analysis_digest)
    object.__setattr__(result, "decision_id", decision_id)
    object.__setattr__(result, "decision_digest", decision_digest)
    object.__setattr__(result, "outcome", "approved")
    return result
