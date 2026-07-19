"""Pure concentration and review-exposure analysis for portfolio reviews."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from el_psy_quant.portfolio_review.scenarios import (
    PortfolioReviewScenarioPair,
)
from el_psy_quant.portfolio_review.sources import PortfolioReviewSource

PORTFOLIO_REVIEW_SCENARIO_CONCENTRATION_SCHEMA_VERSION = 1
PORTFOLIO_REVIEW_COMPONENT_EXPOSURE_SCHEMA_VERSION = 1
PORTFOLIO_REVIEW_SCENARIO_UNIVERSE_COVERAGE_SCHEMA_VERSION = 1
PORTFOLIO_REVIEW_CONCENTRATION_EXPOSURE_ANALYSIS_SCHEMA_VERSION = 1

SUPPORTED_PORTFOLIO_REVIEW_WEIGHT_CHANGE_TYPES = (
    "added",
    "removed",
    "increased",
    "decreased",
    "unchanged",
)
SUPPORTED_PORTFOLIO_REVIEW_SYMBOL_EVIDENCE_STATUSES = (
    "available",
    "missing",
)

PortfolioReviewWeightChangeType = Literal[
    "added",
    "removed",
    "increased",
    "decreased",
    "unchanged",
]
PortfolioReviewSymbolEvidenceStatus = Literal["available", "missing"]

_DERIVED_CONSTRUCTOR_MESSAGE = (
    "portfolio-review analysis values are created by "
    "analyze_portfolio_review_concentration_and_exposure"
)


def _reject_public_construction(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise TypeError(_DERIVED_CONSTRUCTOR_MESSAGE)


def _canonical_zero(value: float) -> float:
    return 0.0 if value == 0.0 else value


@dataclass(frozen=True, init=False)
class PortfolioReviewScenarioConcentration:
    """Immutable concentration evidence calculated for one exact scenario."""

    scenario_id: str
    scenario_digest: str
    largest_component_id: str
    largest_component_weight: float
    top_3_weight: float
    herfindahl_hirschman_index: float
    effective_component_count: float

    __init__ = _reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic strictly JSON-compatible payload."""
        return {
            "schema_version": (
                PORTFOLIO_REVIEW_SCENARIO_CONCENTRATION_SCHEMA_VERSION
            ),
            "scenario_id": self.scenario_id,
            "scenario_digest": self.scenario_digest,
            "largest_component_id": self.largest_component_id,
            "largest_component_weight": self.largest_component_weight,
            "top_3_weight": self.top_3_weight,
            "herfindahl_hirschman_index": self.herfindahl_hirschman_index,
            "effective_component_count": self.effective_component_count,
        }


@dataclass(frozen=True, init=False)
class PortfolioReviewComponentExposure:
    """Immutable ordered component-weight and declared-symbol evidence."""

    component_id: str
    strategy_id: str
    baseline_weight: float
    proposed_weight: float
    weight_delta: float
    change_type: PortfolioReviewWeightChangeType
    baseline_active: bool
    proposed_active: bool
    symbols: tuple[str, ...] | None
    symbol_evidence_status: PortfolioReviewSymbolEvidenceStatus

    __init__ = _reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic strictly JSON-compatible payload."""
        return {
            "schema_version": PORTFOLIO_REVIEW_COMPONENT_EXPOSURE_SCHEMA_VERSION,
            "component_id": self.component_id,
            "strategy_id": self.strategy_id,
            "baseline_weight": self.baseline_weight,
            "proposed_weight": self.proposed_weight,
            "weight_delta": self.weight_delta,
            "change_type": self.change_type,
            "baseline_active": self.baseline_active,
            "proposed_active": self.proposed_active,
            "symbols": list(self.symbols) if self.symbols is not None else None,
            "symbol_evidence_status": self.symbol_evidence_status,
        }


@dataclass(frozen=True, init=False)
class PortfolioReviewScenarioUniverseCoverage:
    """Immutable declared-symbol metadata coverage for one exact scenario."""

    scenario_id: str
    scenario_digest: str
    components_with_symbol_evidence: tuple[str, ...]
    components_missing_symbol_evidence: tuple[str, ...]
    active_component_ids: tuple[str, ...]
    active_components_with_symbol_evidence: tuple[str, ...]
    active_components_missing_symbol_evidence: tuple[str, ...]
    source_component_count: int
    components_with_symbol_evidence_count: int
    components_missing_symbol_evidence_count: int
    active_component_count: int
    active_components_with_symbol_evidence_count: int
    active_components_missing_symbol_evidence_count: int
    active_coverage_complete: bool

    __init__ = _reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic strictly JSON-compatible payload."""
        return {
            "schema_version": (
                PORTFOLIO_REVIEW_SCENARIO_UNIVERSE_COVERAGE_SCHEMA_VERSION
            ),
            "scenario_id": self.scenario_id,
            "scenario_digest": self.scenario_digest,
            "components_with_symbol_evidence": list(
                self.components_with_symbol_evidence
            ),
            "components_missing_symbol_evidence": list(
                self.components_missing_symbol_evidence
            ),
            "active_component_ids": list(self.active_component_ids),
            "active_components_with_symbol_evidence": list(
                self.active_components_with_symbol_evidence
            ),
            "active_components_missing_symbol_evidence": list(
                self.active_components_missing_symbol_evidence
            ),
            "source_component_count": self.source_component_count,
            "components_with_symbol_evidence_count": (
                self.components_with_symbol_evidence_count
            ),
            "components_missing_symbol_evidence_count": (
                self.components_missing_symbol_evidence_count
            ),
            "active_component_count": self.active_component_count,
            "active_components_with_symbol_evidence_count": (
                self.active_components_with_symbol_evidence_count
            ),
            "active_components_missing_symbol_evidence_count": (
                self.active_components_missing_symbol_evidence_count
            ),
            "active_coverage_complete": self.active_coverage_complete,
        }


@dataclass(frozen=True, init=False)
class PortfolioReviewConcentrationExposureAnalysis:
    """Immutable derived Sprint 171 result for one source and scenario pair."""

    source_id: str
    source_digest: str
    component_ids: tuple[str, ...]
    baseline_concentration: PortfolioReviewScenarioConcentration
    proposed_concentration: PortfolioReviewScenarioConcentration
    component_exposures: tuple[PortfolioReviewComponentExposure, ...]
    baseline_universe_coverage: PortfolioReviewScenarioUniverseCoverage
    proposed_universe_coverage: PortfolioReviewScenarioUniverseCoverage

    __init__ = _reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return the deterministic strictly JSON-compatible analysis."""
        return {
            "schema_version": (
                PORTFOLIO_REVIEW_CONCENTRATION_EXPOSURE_ANALYSIS_SCHEMA_VERSION
            ),
            "source_id": self.source_id,
            "source_digest": self.source_digest,
            "component_ids": list(self.component_ids),
            "baseline_concentration": self.baseline_concentration.to_dict(),
            "proposed_concentration": self.proposed_concentration.to_dict(),
            "component_exposures": [
                exposure.to_dict() for exposure in self.component_exposures
            ],
            "baseline_universe_coverage": (
                self.baseline_universe_coverage.to_dict()
            ),
            "proposed_universe_coverage": (
                self.proposed_universe_coverage.to_dict()
            ),
        }


def _new_derived(result_type: type[object], **values: object) -> object:
    result = object.__new__(result_type)
    for field_name, value in values.items():
        object.__setattr__(result, field_name, value)
    return result


def _scenario_concentration(
    *,
    scenario_id: str,
    scenario_digest: str,
    component_weights: tuple[tuple[str, float], ...],
) -> PortfolioReviewScenarioConcentration:
    weights = tuple(weight for _, weight in component_weights)
    largest_component_weight = max(weights)
    largest_component_id = next(
        component_id
        for component_id, weight in component_weights
        if weight == largest_component_weight
    )
    top_3_weight = _canonical_zero(
        math.fsum(sorted(weights, reverse=True)[:3])
    )
    herfindahl_hirschman_index = _canonical_zero(
        math.fsum(weight * weight for weight in weights)
    )
    return _new_derived(
        PortfolioReviewScenarioConcentration,
        scenario_id=scenario_id,
        scenario_digest=scenario_digest,
        largest_component_id=largest_component_id,
        largest_component_weight=largest_component_weight,
        top_3_weight=top_3_weight,
        herfindahl_hirschman_index=herfindahl_hirschman_index,
        effective_component_count=1.0 / herfindahl_hirschman_index,
    )  # type: ignore[return-value]


def _classify_weight_change(
    baseline_weight: float,
    proposed_weight: float,
) -> PortfolioReviewWeightChangeType:
    if baseline_weight == 0.0 and proposed_weight > 0.0:
        return "added"
    if baseline_weight > 0.0 and proposed_weight == 0.0:
        return "removed"
    if proposed_weight > baseline_weight:
        return "increased"
    if proposed_weight < baseline_weight:
        return "decreased"
    return "unchanged"


def _component_exposures(
    *,
    source: PortfolioReviewSource,
    scenario_pair: PortfolioReviewScenarioPair,
) -> tuple[PortfolioReviewComponentExposure, ...]:
    baseline_weights = dict(scenario_pair.baseline.component_weights)
    proposed_weights = dict(scenario_pair.proposed.component_weights)
    exposures: list[PortfolioReviewComponentExposure] = []
    for component in source.components:
        baseline_weight = baseline_weights[component.component_id]
        proposed_weight = proposed_weights[component.component_id]
        symbols = component.symbols
        exposures.append(
            _new_derived(
                PortfolioReviewComponentExposure,
                component_id=component.component_id,
                strategy_id=component.strategy_id,
                baseline_weight=baseline_weight,
                proposed_weight=proposed_weight,
                weight_delta=_canonical_zero(
                    proposed_weight - baseline_weight
                ),
                change_type=_classify_weight_change(
                    baseline_weight,
                    proposed_weight,
                ),
                baseline_active=baseline_weight > 0.0,
                proposed_active=proposed_weight > 0.0,
                symbols=symbols,
                symbol_evidence_status=(
                    "available" if symbols is not None else "missing"
                ),
            )
        )
    return tuple(exposures)


def _scenario_universe_coverage(
    *,
    scenario_id: str,
    scenario_digest: str,
    component_weights: tuple[tuple[str, float], ...],
    source: PortfolioReviewSource,
) -> PortfolioReviewScenarioUniverseCoverage:
    weights = dict(component_weights)
    components_with_symbol_evidence = tuple(
        component.component_id
        for component in source.components
        if component.symbols is not None
    )
    components_missing_symbol_evidence = tuple(
        component.component_id
        for component in source.components
        if component.symbols is None
    )
    active_component_ids = tuple(
        component.component_id
        for component in source.components
        if weights[component.component_id] > 0.0
    )
    active_components_with_symbol_evidence = tuple(
        component.component_id
        for component in source.components
        if (
            weights[component.component_id] > 0.0
            and component.symbols is not None
        )
    )
    active_components_missing_symbol_evidence = tuple(
        component.component_id
        for component in source.components
        if (
            weights[component.component_id] > 0.0
            and component.symbols is None
        )
    )
    return _new_derived(
        PortfolioReviewScenarioUniverseCoverage,
        scenario_id=scenario_id,
        scenario_digest=scenario_digest,
        components_with_symbol_evidence=components_with_symbol_evidence,
        components_missing_symbol_evidence=components_missing_symbol_evidence,
        active_component_ids=active_component_ids,
        active_components_with_symbol_evidence=(
            active_components_with_symbol_evidence
        ),
        active_components_missing_symbol_evidence=(
            active_components_missing_symbol_evidence
        ),
        source_component_count=len(source.components),
        components_with_symbol_evidence_count=len(
            components_with_symbol_evidence
        ),
        components_missing_symbol_evidence_count=len(
            components_missing_symbol_evidence
        ),
        active_component_count=len(active_component_ids),
        active_components_with_symbol_evidence_count=len(
            active_components_with_symbol_evidence
        ),
        active_components_missing_symbol_evidence_count=len(
            active_components_missing_symbol_evidence
        ),
        active_coverage_complete=(
            not active_components_missing_symbol_evidence
        ),
    )  # type: ignore[return-value]


def _validate_analysis_authority(
    source: PortfolioReviewSource,
    scenario_pair: PortfolioReviewScenarioPair,
) -> None:
    if type(source) is not PortfolioReviewSource:
        raise ValueError("source must be a PortfolioReviewSource")
    if type(scenario_pair) is not PortfolioReviewScenarioPair:
        raise ValueError("scenario_pair must be a PortfolioReviewScenarioPair")
    if (
        scenario_pair.source_id != source.source_id
        or scenario_pair.source_digest != source.source_digest
    ):
        raise ValueError(
            "scenario_pair must reference the exact source ID and digest"
        )
    if scenario_pair.component_ids != source.component_ids:
        raise ValueError(
            "scenario_pair must use the complete ordered source component set"
        )
    for scenario in (scenario_pair.baseline, scenario_pair.proposed):
        if (
            scenario.source_id != source.source_id
            or scenario.source_digest != source.source_digest
        ):
            raise ValueError(
                "scenarios must reference the exact source ID and digest"
            )
        if scenario.component_ids != source.component_ids:
            raise ValueError(
                "scenarios must use the complete ordered source component set"
            )


def analyze_portfolio_review_concentration_and_exposure(
    *,
    source: PortfolioReviewSource,
    scenario_pair: PortfolioReviewScenarioPair,
) -> PortfolioReviewConcentrationExposureAnalysis:
    """Calculate immutable concentration and review-exposure evidence."""
    _validate_analysis_authority(source, scenario_pair)
    baseline = scenario_pair.baseline
    proposed = scenario_pair.proposed
    component_exposures = _component_exposures(
        source=source,
        scenario_pair=scenario_pair,
    )
    return _new_derived(
        PortfolioReviewConcentrationExposureAnalysis,
        source_id=source.source_id,
        source_digest=source.source_digest,
        component_ids=source.component_ids,
        baseline_concentration=_scenario_concentration(
            scenario_id=baseline.scenario_id,
            scenario_digest=baseline.scenario_digest,
            component_weights=baseline.component_weights,
        ),
        proposed_concentration=_scenario_concentration(
            scenario_id=proposed.scenario_id,
            scenario_digest=proposed.scenario_digest,
            component_weights=proposed.component_weights,
        ),
        component_exposures=component_exposures,
        baseline_universe_coverage=_scenario_universe_coverage(
            scenario_id=baseline.scenario_id,
            scenario_digest=baseline.scenario_digest,
            component_weights=baseline.component_weights,
            source=source,
        ),
        proposed_universe_coverage=_scenario_universe_coverage(
            scenario_id=proposed.scenario_id,
            scenario_digest=proposed.scenario_digest,
            component_weights=proposed.component_weights,
            source=source,
        ),
    )  # type: ignore[return-value]
