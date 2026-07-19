"""Validated immutable portfolio-review source inputs."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from numbers import Real

import pandas as pd

from el_psy_quant.portfolio_review.evidence_references import (
    PortfolioReviewComponent,
)

PORTFOLIO_REVIEW_RETURN_OBSERVATION_SCHEMA_VERSION = 1
PORTFOLIO_REVIEW_SOURCE_SCHEMA_VERSION = 1


def _normalize_required_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _normalize_string_sequence(
    values: Sequence[str],
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence of non-empty strings")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(
            f"{field_name} must be a sequence of non-empty strings"
        ) from exc
    return tuple(
        _normalize_required_string(value, f"{field_name} item") for value in items
    )


def _normalize_observation_timestamp(value: object) -> pd.Timestamp:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("observation timestamp must be valid") from exc
    if pd.isna(timestamp):
        raise ValueError("observation timestamp must be valid")
    return timestamp


def _normalize_created_timestamp(value: object) -> pd.Timestamp:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("created_timestamp must be timezone-aware") from exc
    if pd.isna(timestamp) or timestamp.tzinfo is None:
        raise ValueError("created_timestamp must be timezone-aware")
    try:
        return timestamp.tz_convert("UTC")
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("created_timestamp must be timezone-aware") from exc


def _normalize_return_value(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError("return values must be numeric and non-boolean")
    normalized = float(value)
    if math.isnan(normalized):
        raise ValueError("return values must not be missing")
    if not math.isfinite(normalized):
        raise ValueError("return values must be finite")
    return 0.0 if normalized == 0.0 else normalized


def _normalize_periods_per_year(value: int | float | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError("periods_per_year must be a positive finite number")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized <= 0.0:
        raise ValueError("periods_per_year must be a positive finite number")
    return normalized


def _canonical_digest(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PortfolioReviewReturnObservation:
    """One timestamped ordered vector of finite component returns."""

    timestamp: pd.Timestamp
    component_returns: tuple[float, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "timestamp",
            _normalize_observation_timestamp(self.timestamp),
        )
        if isinstance(self.component_returns, (str, bytes)):
            raise ValueError("component_returns must be a sequence of values")
        try:
            values = tuple(self.component_returns)
        except TypeError as exc:
            raise ValueError(
                "component_returns must be a sequence of values"
            ) from exc
        if not values:
            raise ValueError("component_returns must not be empty")
        object.__setattr__(
            self,
            "component_returns",
            tuple(_normalize_return_value(value) for value in values),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible observation export."""
        return {
            "schema_version": PORTFOLIO_REVIEW_RETURN_OBSERVATION_SCHEMA_VERSION,
            "timestamp": self.timestamp.isoformat(),
            "component_returns": list(self.component_returns),
        }


def _normalize_components(
    components: Sequence[PortfolioReviewComponent],
) -> tuple[PortfolioReviewComponent, ...]:
    if isinstance(components, (str, bytes)):
        raise ValueError("components must be a sequence of components")
    try:
        normalized = tuple(components)
    except TypeError as exc:
        raise ValueError("components must be a sequence of components") from exc
    if not 2 <= len(normalized) <= 12:
        raise ValueError("source must contain between 2 and 12 components")
    component_ids: set[str] = set()
    for component in normalized:
        if type(component) is not PortfolioReviewComponent:
            raise ValueError(
                "components must contain PortfolioReviewComponent values"
            )
        if component.component_id in component_ids:
            raise ValueError(f"duplicate component_id: {component.component_id}")
        component_ids.add(component.component_id)
    return normalized


def _normalize_observations(
    observations: Sequence[PortfolioReviewReturnObservation],
    *,
    component_count: int,
) -> tuple[PortfolioReviewReturnObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("return_observations must be a sequence")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("return_observations must be a sequence") from exc
    if len(normalized) < 3:
        raise ValueError("aligned_returns must contain at least three observations")

    previous: pd.Timestamp | None = None
    for observation in normalized:
        if type(observation) is not PortfolioReviewReturnObservation:
            raise ValueError(
                "return_observations must contain "
                "PortfolioReviewReturnObservation values"
            )
        if len(observation.component_returns) != component_count:
            raise ValueError(
                "each observation must contain one return per component"
            )
        if previous is not None:
            try:
                strictly_increasing = observation.timestamp > previous
            except TypeError as exc:
                raise ValueError(
                    "observation timestamps must be strictly increasing"
                ) from exc
            if not strictly_increasing:
                raise ValueError(
                    "observation timestamps must be strictly increasing and unique"
                )
        previous = observation.timestamp
    return normalized


@dataclass(frozen=True)
class PortfolioReviewSource:
    """One exact immutable authority for later portfolio-review calculations."""

    source_id: str
    components: tuple[PortfolioReviewComponent, ...]
    return_observations: tuple[PortfolioReviewReturnObservation, ...]
    evaluation_frequency: str
    periods_per_year: float | None
    created_by: str
    created_timestamp: pd.Timestamp
    assumptions: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()
    source_digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_id",
            _normalize_required_string(self.source_id, "source_id"),
        )
        components = _normalize_components(self.components)
        object.__setattr__(self, "components", components)
        object.__setattr__(
            self,
            "return_observations",
            _normalize_observations(
                self.return_observations,
                component_count=len(components),
            ),
        )
        object.__setattr__(
            self,
            "evaluation_frequency",
            _normalize_required_string(
                self.evaluation_frequency,
                "evaluation_frequency",
            ),
        )
        object.__setattr__(
            self,
            "periods_per_year",
            _normalize_periods_per_year(self.periods_per_year),
        )
        object.__setattr__(
            self,
            "created_by",
            _normalize_required_string(self.created_by, "created_by"),
        )
        object.__setattr__(
            self,
            "created_timestamp",
            _normalize_created_timestamp(self.created_timestamp),
        )
        object.__setattr__(
            self,
            "assumptions",
            _normalize_string_sequence(self.assumptions, "assumptions"),
        )
        object.__setattr__(
            self,
            "warnings",
            _normalize_string_sequence(self.warnings, "warnings"),
        )
        object.__setattr__(
            self,
            "missing_evidence",
            _normalize_string_sequence(
                self.missing_evidence,
                "missing_evidence",
            ),
        )
        object.__setattr__(
            self,
            "source_digest",
            _canonical_digest(self._payload_without_digest()),
        )

    @property
    def component_ids(self) -> tuple[str, ...]:
        """Return source component identity in its authoritative order."""
        return tuple(component.component_id for component in self.components)

    def _payload_without_digest(self) -> dict[str, object]:
        return {
            "schema_version": PORTFOLIO_REVIEW_SOURCE_SCHEMA_VERSION,
            "source_id": self.source_id,
            "components": [component.to_dict() for component in self.components],
            "return_observations": [
                observation.to_dict()
                for observation in self.return_observations
            ],
            "evaluation_frequency": self.evaluation_frequency,
            "periods_per_year": self.periods_per_year,
            "created_by": self.created_by,
            "created_timestamp": self.created_timestamp.isoformat(),
            "assumptions": list(self.assumptions),
            "warnings": list(self.warnings),
            "missing_evidence": list(self.missing_evidence),
        }

    def to_dict(self) -> dict[str, object]:
        """Return the normalized source payload and its canonical digest."""
        payload = self._payload_without_digest()
        payload["source_digest"] = self.source_digest
        return payload


def _observations_from_aligned_returns(
    aligned_returns: pd.DataFrame,
    *,
    component_ids: tuple[str, ...],
) -> tuple[PortfolioReviewReturnObservation, ...]:
    if not isinstance(aligned_returns, pd.DataFrame):
        raise ValueError("aligned_returns must be a pandas DataFrame")
    if not isinstance(aligned_returns.index, pd.DatetimeIndex):
        raise ValueError("aligned_returns must have a DatetimeIndex")
    if len(aligned_returns.index) < 3:
        raise ValueError("aligned_returns must contain at least three observations")
    if aligned_returns.index.hasnans:
        raise ValueError("aligned_returns timestamps must be valid")
    if (
        not aligned_returns.index.is_monotonic_increasing
        or not aligned_returns.index.is_unique
    ):
        raise ValueError(
            "aligned_returns timestamps must be strictly increasing and unique"
        )
    if tuple(aligned_returns.columns) != component_ids:
        raise ValueError(
            "aligned_returns columns must exactly match component IDs in source order"
        )

    for component_id in component_ids:
        series = aligned_returns[component_id]
        if pd.api.types.is_bool_dtype(series.dtype):
            raise ValueError(f"{component_id} returns must not be boolean")
        if not pd.api.types.is_numeric_dtype(series.dtype):
            raise ValueError(f"{component_id} returns must be numeric")

    observations: list[PortfolioReviewReturnObservation] = []
    for row in aligned_returns.itertuples(index=True, name=None):
        observations.append(
            PortfolioReviewReturnObservation(
                timestamp=row[0],
                component_returns=tuple(row[1:]),
            )
        )
    return tuple(observations)


def create_portfolio_review_source(
    *,
    source_id: str,
    components: Sequence[PortfolioReviewComponent],
    aligned_returns: pd.DataFrame,
    evaluation_frequency: str,
    periods_per_year: int | float | None = None,
    created_by: str,
    created_timestamp: object,
    assumptions: Sequence[str] = (),
    warnings: Sequence[str] = (),
    missing_evidence: Sequence[str] = (),
) -> PortfolioReviewSource:
    """Create a source from one already-aligned finite returns table."""
    normalized_components = _normalize_components(components)
    component_ids = tuple(
        component.component_id for component in normalized_components
    )
    observations = _observations_from_aligned_returns(
        aligned_returns,
        component_ids=component_ids,
    )
    return PortfolioReviewSource(
        source_id=source_id,
        components=normalized_components,
        return_observations=observations,
        evaluation_frequency=evaluation_frequency,
        periods_per_year=periods_per_year,
        created_by=created_by,
        created_timestamp=_normalize_created_timestamp(created_timestamp),
        assumptions=_normalize_string_sequence(assumptions, "assumptions"),
        warnings=_normalize_string_sequence(warnings, "warnings"),
        missing_evidence=_normalize_string_sequence(
            missing_evidence,
            "missing_evidence",
        ),
    )
