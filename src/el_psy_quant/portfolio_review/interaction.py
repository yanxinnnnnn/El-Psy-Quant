"""Declared-symbol overlap and historical return interaction evidence."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import pandas as pd

from el_psy_quant.portfolio_review._derived import (
    canonical_float,
    new_derived,
    reject_public_construction,
)
from el_psy_quant.portfolio_review.sources import PortfolioReviewSource

PORTFOLIO_REVIEW_SYMBOL_OVERLAP_SCHEMA_VERSION = 1
PORTFOLIO_REVIEW_PAIRWISE_CORRELATION_SCHEMA_VERSION = 1
PORTFOLIO_REVIEW_CANDIDATE_BASELINE_CORRELATION_SCHEMA_VERSION = 1

SUPPORTED_PORTFOLIO_REVIEW_AVAILABILITY_STATUSES = (
    "available",
    "unavailable",
)
SUPPORTED_PORTFOLIO_REVIEW_SYMBOL_OVERLAP_UNAVAILABLE_REASONS = (
    "missing_symbol_evidence",
)
SUPPORTED_PORTFOLIO_REVIEW_CORRELATION_UNAVAILABLE_REASONS = (
    "zero_variance",
)

PortfolioReviewAvailabilityStatus = Literal["available", "unavailable"]
PortfolioReviewSymbolOverlapUnavailableReason = Literal[
    "missing_symbol_evidence"
]
PortfolioReviewCorrelationUnavailableReason = Literal["zero_variance"]


@dataclass(frozen=True, init=False)
class PortfolioReviewSymbolOverlap:
    """Immutable declared-symbol overlap for one source-ordered pair."""

    left_component_id: str
    right_component_id: str
    status: PortfolioReviewAvailabilityStatus
    unavailable_reason: PortfolioReviewSymbolOverlapUnavailableReason | None
    missing_symbol_component_ids: tuple[str, ...]
    shared_symbols: tuple[str, ...] | None
    shared_symbol_count: int | None
    union_symbol_count: int | None
    jaccard_overlap: float | None

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic strictly JSON-compatible payload."""
        return {
            "schema_version": PORTFOLIO_REVIEW_SYMBOL_OVERLAP_SCHEMA_VERSION,
            "left_component_id": self.left_component_id,
            "right_component_id": self.right_component_id,
            "status": self.status,
            "unavailable_reason": self.unavailable_reason,
            "missing_symbol_component_ids": list(
                self.missing_symbol_component_ids
            ),
            "shared_symbols": (
                list(self.shared_symbols)
                if self.shared_symbols is not None
                else None
            ),
            "shared_symbol_count": self.shared_symbol_count,
            "union_symbol_count": self.union_symbol_count,
            "jaccard_overlap": self.jaccard_overlap,
        }


@dataclass(frozen=True, init=False)
class PortfolioReviewPairwiseCorrelation:
    """Immutable Pearson correlation for one source-ordered component pair."""

    left_component_id: str
    right_component_id: str
    status: PortfolioReviewAvailabilityStatus
    unavailable_reason: PortfolioReviewCorrelationUnavailableReason | None
    zero_variance_series: tuple[str, ...]
    correlation: float | None
    observation_count: int
    evaluation_start_timestamp: str
    evaluation_end_timestamp: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic strictly JSON-compatible payload."""
        return {
            "schema_version": (
                PORTFOLIO_REVIEW_PAIRWISE_CORRELATION_SCHEMA_VERSION
            ),
            "left_component_id": self.left_component_id,
            "right_component_id": self.right_component_id,
            "status": self.status,
            "unavailable_reason": self.unavailable_reason,
            "zero_variance_series": list(self.zero_variance_series),
            "correlation": self.correlation,
            "observation_count": self.observation_count,
            "evaluation_start_timestamp": self.evaluation_start_timestamp,
            "evaluation_end_timestamp": self.evaluation_end_timestamp,
        }


@dataclass(frozen=True, init=False)
class PortfolioReviewCandidateBaselineCorrelation:
    """Immutable candidate interaction with the exact baseline portfolio."""

    candidate_component_id: str
    candidate_baseline_weight: float
    baseline_scenario_id: str
    baseline_scenario_digest: str
    status: PortfolioReviewAvailabilityStatus
    unavailable_reason: PortfolioReviewCorrelationUnavailableReason | None
    zero_variance_series: tuple[str, ...]
    correlation: float | None
    observation_count: int
    evaluation_start_timestamp: str
    evaluation_end_timestamp: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic strictly JSON-compatible payload."""
        return {
            "schema_version": (
                PORTFOLIO_REVIEW_CANDIDATE_BASELINE_CORRELATION_SCHEMA_VERSION
            ),
            "candidate_component_id": self.candidate_component_id,
            "candidate_baseline_weight": self.candidate_baseline_weight,
            "baseline_scenario_id": self.baseline_scenario_id,
            "baseline_scenario_digest": self.baseline_scenario_digest,
            "status": self.status,
            "unavailable_reason": self.unavailable_reason,
            "zero_variance_series": list(self.zero_variance_series),
            "correlation": self.correlation,
            "observation_count": self.observation_count,
            "evaluation_start_timestamp": self.evaluation_start_timestamp,
            "evaluation_end_timestamp": self.evaluation_end_timestamp,
        }


def _component_pairs(
    source: PortfolioReviewSource,
) -> tuple[tuple[int, int], ...]:
    return tuple(
        (left_index, right_index)
        for left_index in range(len(source.components) - 1)
        for right_index in range(left_index + 1, len(source.components))
    )


def _symbol_overlaps(
    source: PortfolioReviewSource,
) -> tuple[PortfolioReviewSymbolOverlap, ...]:
    overlaps: list[PortfolioReviewSymbolOverlap] = []
    for left_index, right_index in _component_pairs(source):
        left = source.components[left_index]
        right = source.components[right_index]
        missing = tuple(
            component.component_id
            for component in (left, right)
            if component.symbols is None
        )
        if missing:
            overlaps.append(
                new_derived(
                    PortfolioReviewSymbolOverlap,
                    left_component_id=left.component_id,
                    right_component_id=right.component_id,
                    status="unavailable",
                    unavailable_reason="missing_symbol_evidence",
                    missing_symbol_component_ids=missing,
                    shared_symbols=None,
                    shared_symbol_count=None,
                    union_symbol_count=None,
                    jaccard_overlap=None,
                )
            )
            continue

        assert left.symbols is not None
        assert right.symbols is not None
        right_symbols = set(right.symbols)
        shared_symbols = tuple(
            symbol for symbol in left.symbols if symbol in right_symbols
        )
        union_symbol_count = len(set(left.symbols).union(right.symbols))
        shared_symbol_count = len(shared_symbols)
        overlaps.append(
            new_derived(
                PortfolioReviewSymbolOverlap,
                left_component_id=left.component_id,
                right_component_id=right.component_id,
                status="available",
                unavailable_reason=None,
                missing_symbol_component_ids=(),
                shared_symbols=shared_symbols,
                shared_symbol_count=shared_symbol_count,
                union_symbol_count=union_symbol_count,
                jaccard_overlap=canonical_float(
                    shared_symbol_count / union_symbol_count,
                    "jaccard_overlap",
                ),
            )
        )
    return tuple(overlaps)


def _pearson_correlation(
    left_values: tuple[float, ...],
    right_values: tuple[float, ...],
) -> tuple[float | None, bool, bool]:
    if len(left_values) != len(right_values):
        raise ValueError("correlation series must share an observation count")
    observation_count = len(left_values)
    left_mean = math.fsum(left_values) / observation_count
    right_mean = math.fsum(right_values) / observation_count
    left_centered = tuple(value - left_mean for value in left_values)
    right_centered = tuple(value - right_mean for value in right_values)
    left_ss = math.fsum(value * value for value in left_centered)
    right_ss = math.fsum(value * value for value in right_centered)
    left_zero_variance = left_ss == 0.0
    right_zero_variance = right_ss == 0.0
    if left_zero_variance or right_zero_variance:
        return None, left_zero_variance, right_zero_variance

    numerator = math.fsum(
        left_value * right_value
        for left_value, right_value in zip(
            left_centered,
            right_centered,
            strict=True,
        )
    )
    correlation = numerator / math.sqrt(left_ss * right_ss)
    if correlation > 1.0:
        if correlation - 1.0 <= 1e-12:
            correlation = 1.0
        else:
            raise ValueError("derived correlation exceeds 1.0")
    elif correlation < -1.0:
        if -1.0 - correlation <= 1e-12:
            correlation = -1.0
        else:
            raise ValueError("derived correlation is below -1.0")
    return canonical_float(correlation, "correlation"), False, False


def _evaluation_identity(source: PortfolioReviewSource) -> tuple[int, str, str]:
    return (
        len(source.return_observations),
        source.return_observations[0].timestamp.isoformat(),
        source.return_observations[-1].timestamp.isoformat(),
    )


def _pairwise_correlations(
    source: PortfolioReviewSource,
) -> tuple[PortfolioReviewPairwiseCorrelation, ...]:
    observation_count, evaluation_start, evaluation_end = _evaluation_identity(
        source
    )
    results: list[PortfolioReviewPairwiseCorrelation] = []
    for left_index, right_index in _component_pairs(source):
        left = source.components[left_index]
        right = source.components[right_index]
        correlation, left_constant, right_constant = _pearson_correlation(
            tuple(
                observation.component_returns[left_index]
                for observation in source.return_observations
            ),
            tuple(
                observation.component_returns[right_index]
                for observation in source.return_observations
            ),
        )
        zero_variance_series = tuple(
            component_id
            for component_id, is_constant in (
                (left.component_id, left_constant),
                (right.component_id, right_constant),
            )
            if is_constant
        )
        results.append(
            new_derived(
                PortfolioReviewPairwiseCorrelation,
                left_component_id=left.component_id,
                right_component_id=right.component_id,
                status=(
                    "unavailable"
                    if zero_variance_series
                    else "available"
                ),
                unavailable_reason=(
                    "zero_variance" if zero_variance_series else None
                ),
                zero_variance_series=zero_variance_series,
                correlation=correlation,
                observation_count=observation_count,
                evaluation_start_timestamp=evaluation_start,
                evaluation_end_timestamp=evaluation_end,
            )
        )
    return tuple(results)


def _candidate_baseline_correlation(
    *,
    source: PortfolioReviewSource,
    aligned_returns: pd.DataFrame,
    baseline_portfolio_return: pd.Series,
    candidate_component_id: str,
    candidate_baseline_weight: float,
    baseline_scenario_id: str,
    baseline_scenario_digest: str,
) -> PortfolioReviewCandidateBaselineCorrelation:
    observation_count, evaluation_start, evaluation_end = _evaluation_identity(
        source
    )
    candidate_values = tuple(
        float(value) for value in aligned_returns[candidate_component_id]
    )
    baseline_values = tuple(float(value) for value in baseline_portfolio_return)
    correlation, candidate_constant, baseline_constant = _pearson_correlation(
        candidate_values,
        baseline_values,
    )
    zero_variance_series = tuple(
        series_id
        for series_id, is_constant in (
            (candidate_component_id, candidate_constant),
            ("baseline_portfolio", baseline_constant),
        )
        if is_constant
    )
    return new_derived(
        PortfolioReviewCandidateBaselineCorrelation,
        candidate_component_id=candidate_component_id,
        candidate_baseline_weight=candidate_baseline_weight,
        baseline_scenario_id=baseline_scenario_id,
        baseline_scenario_digest=baseline_scenario_digest,
        status="unavailable" if zero_variance_series else "available",
        unavailable_reason=(
            "zero_variance" if zero_variance_series else None
        ),
        zero_variance_series=zero_variance_series,
        correlation=correlation,
        observation_count=observation_count,
        evaluation_start_timestamp=evaluation_start,
        evaluation_end_timestamp=evaluation_end,
    )  # type: ignore[return-value]
