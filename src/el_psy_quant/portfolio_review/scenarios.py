"""Immutable baseline and proposed portfolio-review scenario contracts."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from numbers import Real

from el_psy_quant.portfolio_review.sources import PortfolioReviewSource

PORTFOLIO_REVIEW_BASELINE_SCENARIO_SCHEMA_VERSION = 1
PORTFOLIO_REVIEW_PROPOSED_SCENARIO_SCHEMA_VERSION = 1
PORTFOLIO_REVIEW_SCENARIO_PAIR_SCHEMA_VERSION = 1


def _normalize_required_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _normalize_digest(value: str, field_name: str) -> str:
    normalized = _normalize_required_string(value, field_name)
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return normalized


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


def _canonical_digest(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_weight(value: object, component_id: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{component_id} weight must be numeric")
    normalized = float(value)
    if math.isnan(normalized):
        raise ValueError(f"{component_id} weight must not be missing")
    if not math.isfinite(normalized):
        raise ValueError(f"{component_id} weight must be finite")
    if normalized < 0.0:
        raise ValueError(f"{component_id} weight must be non-negative")
    return 0.0 if normalized == 0.0 else normalized


def _normalize_ordered_weights(
    values: Sequence[tuple[str, float]],
) -> tuple[tuple[str, float], ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("component_weights must be an ordered sequence")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "component_weights must be an ordered sequence"
        ) from exc
    if not items:
        raise ValueError("component_weights must not be empty")

    normalized: list[tuple[str, float]] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            raise ValueError(
                "component_weights must contain component ID and weight pairs"
            )
        component_id = _normalize_required_string(item[0], "component_id")
        if component_id in seen:
            raise ValueError(f"duplicate component weight: {component_id}")
        seen.add(component_id)
        normalized.append(
            (component_id, _normalize_weight(item[1], component_id))
        )

    weights = [weight for _, weight in normalized]
    if not any(weight > 0.0 for weight in weights):
        raise ValueError("at least one component weight must be positive")
    if not math.isclose(sum(weights), 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("weights must sum to 1.0")
    return tuple(normalized)


def _weights_for_source(
    source: PortfolioReviewSource,
    weights: Mapping[str, float],
) -> tuple[tuple[str, float], ...]:
    if type(source) is not PortfolioReviewSource:
        raise ValueError("source must be a PortfolioReviewSource")
    if not isinstance(weights, Mapping):
        raise ValueError("weights must be a mapping")

    component_ids = source.component_ids
    caller_keys = tuple(weights.keys())
    missing = [item for item in component_ids if item not in weights]
    if missing:
        raise ValueError(f"weights missing components: {', '.join(missing)}")
    expected = set(component_ids)
    extra = [item for item in caller_keys if item not in expected]
    if extra:
        rendered = ", ".join(str(item) for item in extra)
        raise ValueError(f"weights contain unknown components: {rendered}")
    if len(caller_keys) != len(component_ids):
        raise ValueError("weights must contain each source component exactly once")

    return _normalize_ordered_weights(
        tuple((component_id, weights[component_id]) for component_id in component_ids)
    )


def _weights_payload(
    component_weights: tuple[tuple[str, float], ...],
) -> list[dict[str, object]]:
    return [
        {"component_id": component_id, "weight": weight}
        for component_id, weight in component_weights
    ]


@dataclass(frozen=True)
class PortfolioReviewBaselineScenario:
    """Founder's explicit baseline static-weight review assumption."""

    scenario_id: str
    source_id: str
    source_digest: str
    component_weights: tuple[tuple[str, float], ...]
    rationale: str
    assumptions: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    scenario_digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "scenario_id",
            _normalize_required_string(self.scenario_id, "scenario_id"),
        )
        object.__setattr__(
            self,
            "source_id",
            _normalize_required_string(self.source_id, "source_id"),
        )
        object.__setattr__(
            self,
            "source_digest",
            _normalize_digest(self.source_digest, "source_digest"),
        )
        object.__setattr__(
            self,
            "component_weights",
            _normalize_ordered_weights(self.component_weights),
        )
        object.__setattr__(
            self,
            "rationale",
            _normalize_required_string(self.rationale, "rationale"),
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
            "scenario_digest",
            _canonical_digest(self._payload_without_digest()),
        )

    @property
    def component_ids(self) -> tuple[str, ...]:
        """Return component IDs in source order."""
        return tuple(component_id for component_id, _ in self.component_weights)

    def _payload_without_digest(self) -> dict[str, object]:
        return {
            "schema_version": PORTFOLIO_REVIEW_BASELINE_SCENARIO_SCHEMA_VERSION,
            "scenario_id": self.scenario_id,
            "source_id": self.source_id,
            "source_digest": self.source_digest,
            "component_weights": _weights_payload(self.component_weights),
            "rationale": self.rationale,
            "assumptions": list(self.assumptions),
            "warnings": list(self.warnings),
        }

    def to_dict(self) -> dict[str, object]:
        """Return the baseline scenario and canonical digest."""
        payload = self._payload_without_digest()
        payload["scenario_digest"] = self.scenario_digest
        return payload


@dataclass(frozen=True)
class PortfolioReviewProposedScenario:
    """Founder's explicit proposed static-weight review assumption."""

    scenario_id: str
    source_id: str
    source_digest: str
    component_weights: tuple[tuple[str, float], ...]
    proposed_component_id: str
    rationale: str
    assumptions: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    scenario_digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "scenario_id",
            _normalize_required_string(self.scenario_id, "scenario_id"),
        )
        object.__setattr__(
            self,
            "source_id",
            _normalize_required_string(self.source_id, "source_id"),
        )
        object.__setattr__(
            self,
            "source_digest",
            _normalize_digest(self.source_digest, "source_digest"),
        )
        weights = _normalize_ordered_weights(self.component_weights)
        object.__setattr__(self, "component_weights", weights)
        proposed_component_id = _normalize_required_string(
            self.proposed_component_id,
            "proposed_component_id",
        )
        if proposed_component_id not in {
            component_id for component_id, _ in weights
        }:
            raise ValueError("proposed_component_id must identify a source component")
        object.__setattr__(
            self,
            "proposed_component_id",
            proposed_component_id,
        )
        object.__setattr__(
            self,
            "rationale",
            _normalize_required_string(self.rationale, "rationale"),
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
            "scenario_digest",
            _canonical_digest(self._payload_without_digest()),
        )

    @property
    def component_ids(self) -> tuple[str, ...]:
        """Return component IDs in source order."""
        return tuple(component_id for component_id, _ in self.component_weights)

    def _payload_without_digest(self) -> dict[str, object]:
        return {
            "schema_version": PORTFOLIO_REVIEW_PROPOSED_SCENARIO_SCHEMA_VERSION,
            "scenario_id": self.scenario_id,
            "source_id": self.source_id,
            "source_digest": self.source_digest,
            "component_weights": _weights_payload(self.component_weights),
            "proposed_component_id": self.proposed_component_id,
            "rationale": self.rationale,
            "assumptions": list(self.assumptions),
            "warnings": list(self.warnings),
        }

    def to_dict(self) -> dict[str, object]:
        """Return the proposed scenario and canonical digest."""
        payload = self._payload_without_digest()
        payload["scenario_digest"] = self.scenario_digest
        return payload


@dataclass(frozen=True)
class PortfolioReviewScenarioPair:
    """Cross-validated baseline and proposed scenarios for one exact source."""

    source_id: str
    source_digest: str
    component_ids: tuple[str, ...]
    baseline: PortfolioReviewBaselineScenario
    proposed: PortfolioReviewProposedScenario

    def __post_init__(self) -> None:
        source_id = _normalize_required_string(self.source_id, "source_id")
        source_digest = _normalize_digest(self.source_digest, "source_digest")
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "source_digest", source_digest)

        if isinstance(self.component_ids, (str, bytes)):
            raise ValueError("component_ids must be an ordered sequence")
        component_ids = tuple(
            _normalize_required_string(value, "component_id")
            for value in self.component_ids
        )
        if not 2 <= len(component_ids) <= 12 or len(set(component_ids)) != len(
            component_ids
        ):
            raise ValueError(
                "component_ids must contain 2 to 12 unique component IDs"
            )
        object.__setattr__(self, "component_ids", component_ids)

        if type(self.baseline) is not PortfolioReviewBaselineScenario:
            raise ValueError(
                "baseline must be a PortfolioReviewBaselineScenario"
            )
        if type(self.proposed) is not PortfolioReviewProposedScenario:
            raise ValueError(
                "proposed must be a PortfolioReviewProposedScenario"
            )
        if self.baseline.scenario_id == self.proposed.scenario_id:
            raise ValueError("baseline and proposed scenario IDs must be distinct")
        for scenario in (self.baseline, self.proposed):
            if (
                scenario.source_id != source_id
                or scenario.source_digest != source_digest
            ):
                raise ValueError(
                    "scenarios must reference the exact source ID and digest"
                )
            if scenario.component_ids != component_ids:
                raise ValueError(
                    "scenarios must use the complete ordered source component set"
                )

        baseline_weights = dict(self.baseline.component_weights)
        proposed_weights = dict(self.proposed.component_weights)
        if all(
            baseline_weights[component_id] == proposed_weights[component_id]
            for component_id in component_ids
        ):
            raise ValueError(
                "proposed weights must differ from baseline weights"
            )
        proposed_component_id = self.proposed.proposed_component_id
        if proposed_component_id not in component_ids:
            raise ValueError(
                "proposed_component_id must identify a source component"
            )
        if (
            baseline_weights[proposed_component_id]
            == proposed_weights[proposed_component_id]
        ):
            raise ValueError(
                "the proposed component weight must differ between scenarios"
            )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible pair export."""
        return {
            "schema_version": PORTFOLIO_REVIEW_SCENARIO_PAIR_SCHEMA_VERSION,
            "source_id": self.source_id,
            "source_digest": self.source_digest,
            "component_ids": list(self.component_ids),
            "baseline": self.baseline.to_dict(),
            "proposed": self.proposed.to_dict(),
        }


def create_portfolio_review_baseline_scenario(
    *,
    scenario_id: str,
    source: PortfolioReviewSource,
    weights: Mapping[str, float],
    rationale: str,
    assumptions: Sequence[str] = (),
    warnings: Sequence[str] = (),
) -> PortfolioReviewBaselineScenario:
    """Create one baseline scenario in exact source component order."""
    return PortfolioReviewBaselineScenario(
        scenario_id=scenario_id,
        source_id=source.source_id,
        source_digest=source.source_digest,
        component_weights=_weights_for_source(source, weights),
        rationale=rationale,
        assumptions=_normalize_string_sequence(assumptions, "assumptions"),
        warnings=_normalize_string_sequence(warnings, "warnings"),
    )


def create_portfolio_review_proposed_scenario(
    *,
    scenario_id: str,
    source: PortfolioReviewSource,
    weights: Mapping[str, float],
    proposed_component_id: str,
    rationale: str,
    assumptions: Sequence[str] = (),
    warnings: Sequence[str] = (),
) -> PortfolioReviewProposedScenario:
    """Create one proposed scenario in exact source component order."""
    proposed_component = _normalize_required_string(
        proposed_component_id,
        "proposed_component_id",
    )
    if proposed_component not in source.component_ids:
        raise ValueError("proposed_component_id must identify a source component")
    return PortfolioReviewProposedScenario(
        scenario_id=scenario_id,
        source_id=source.source_id,
        source_digest=source.source_digest,
        component_weights=_weights_for_source(source, weights),
        proposed_component_id=proposed_component,
        rationale=rationale,
        assumptions=_normalize_string_sequence(assumptions, "assumptions"),
        warnings=_normalize_string_sequence(warnings, "warnings"),
    )


def create_portfolio_review_scenario_pair(
    *,
    source: PortfolioReviewSource,
    baseline: PortfolioReviewBaselineScenario,
    proposed: PortfolioReviewProposedScenario,
) -> PortfolioReviewScenarioPair:
    """Cross-validate two scenarios against one exact immutable source."""
    if type(source) is not PortfolioReviewSource:
        raise ValueError("source must be a PortfolioReviewSource")
    return PortfolioReviewScenarioPair(
        source_id=source.source_id,
        source_digest=source.source_digest,
        component_ids=source.component_ids,
        baseline=baseline,
        proposed=proposed,
    )
