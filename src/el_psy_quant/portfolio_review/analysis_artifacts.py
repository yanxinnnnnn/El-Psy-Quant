"""Immutable portfolio-review analysis artifact payloads."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from el_psy_quant.portfolio_review.analysis import (
    PortfolioReviewConcentrationExposureAnalysis,
    analyze_portfolio_review_concentration_and_exposure,
)
from el_psy_quant.portfolio_review.interaction_impact import (
    PortfolioReviewInteractionImpactAnalysis,
    analyze_portfolio_review_interaction_and_impact,
)
from el_psy_quant.portfolio_review.scenarios import (
    PortfolioReviewBaselineScenario,
    PortfolioReviewProposedScenario,
    PortfolioReviewScenarioPair,
)
from el_psy_quant.portfolio_review.sources import PortfolioReviewSource

PORTFOLIO_REVIEW_ANALYSIS_ARTIFACT_SCHEMA_VERSION = 1
PORTFOLIO_REVIEW_ANALYSIS_EVIDENCE_SCOPE = (
    "historical_scenario_evidence"
)

_CONSTRUCTOR_MESSAGE = (
    "portfolio-review analysis artifacts are created by "
    "create_portfolio_review_analysis_artifact"
)


def _reject_public_construction(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise TypeError(_CONSTRUCTOR_MESSAGE)


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
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(
            f"{field_name} must be a sequence of non-empty strings"
        ) from exc
    return tuple(
        _normalize_required_string(value, f"{field_name} item")
        for value in normalized
    )


def _normalize_utc_timestamp(value: object, field_name: str) -> pd.Timestamp:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field_name} must be timezone-aware") from exc
    if pd.isna(timestamp) or timestamp.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    try:
        return timestamp.tz_convert("UTC")
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field_name} must be timezone-aware") from exc


def _canonical_digest(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, init=False)
class PortfolioReviewAnalysisArtifact:
    """Settled historical scenario evidence for one exact portfolio review."""

    review_id: str
    analysis_evidence_scope: str
    source_id: str
    source_digest: str
    component_ids: tuple[str, ...]
    baseline_scenario_id: str
    baseline_scenario_digest: str
    proposed_scenario_id: str
    proposed_scenario_digest: str
    proposed_component_id: str
    baseline_scenario: PortfolioReviewBaselineScenario
    proposed_scenario: PortfolioReviewProposedScenario
    concentration_exposure_analysis: (
        PortfolioReviewConcentrationExposureAnalysis
    )
    interaction_impact_analysis: PortfolioReviewInteractionImpactAnalysis
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    created_by: str
    created_timestamp: pd.Timestamp
    analysis_digest: str

    __init__ = _reject_public_construction

    def _payload_without_digest(self) -> dict[str, object]:
        return {
            "schema_version": (
                PORTFOLIO_REVIEW_ANALYSIS_ARTIFACT_SCHEMA_VERSION
            ),
            "review_id": self.review_id,
            "analysis_evidence_scope": self.analysis_evidence_scope,
            "source_id": self.source_id,
            "source_digest": self.source_digest,
            "component_ids": list(self.component_ids),
            "baseline_scenario_id": self.baseline_scenario_id,
            "baseline_scenario_digest": self.baseline_scenario_digest,
            "proposed_scenario_id": self.proposed_scenario_id,
            "proposed_scenario_digest": self.proposed_scenario_digest,
            "proposed_component_id": self.proposed_component_id,
            "baseline_scenario": self.baseline_scenario.to_dict(),
            "proposed_scenario": self.proposed_scenario.to_dict(),
            "concentration_exposure_analysis": (
                self.concentration_exposure_analysis.to_dict()
            ),
            "interaction_impact_analysis": (
                self.interaction_impact_analysis.to_dict()
            ),
            "assumptions": list(self.assumptions),
            "warnings": list(self.warnings),
            "missing_evidence": list(self.missing_evidence),
            "created_by": self.created_by,
            "created_timestamp": self.created_timestamp.isoformat(),
        }

    def to_dict(self) -> dict[str, object]:
        """Return the normalized analysis payload and canonical digest."""
        payload = self._payload_without_digest()
        payload["analysis_digest"] = self.analysis_digest
        return payload


def _validate_input_authority(
    source: PortfolioReviewSource,
    scenario_pair: PortfolioReviewScenarioPair,
) -> None:
    if type(source) is not PortfolioReviewSource:
        raise ValueError("source must be a PortfolioReviewSource")
    if type(scenario_pair) is not PortfolioReviewScenarioPair:
        raise ValueError(
            "scenario_pair must be a PortfolioReviewScenarioPair"
        )
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
    if type(scenario_pair.baseline) is not PortfolioReviewBaselineScenario:
        raise ValueError(
            "baseline must be a PortfolioReviewBaselineScenario"
        )
    if type(scenario_pair.proposed) is not PortfolioReviewProposedScenario:
        raise ValueError(
            "proposed must be a PortfolioReviewProposedScenario"
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


def _expected_component_pairs(
    component_ids: tuple[str, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        (component_ids[left], component_ids[right])
        for left in range(len(component_ids) - 1)
        for right in range(left + 1, len(component_ids))
    )


def _validate_derived_authority(
    *,
    source: PortfolioReviewSource,
    scenario_pair: PortfolioReviewScenarioPair,
    concentration: PortfolioReviewConcentrationExposureAnalysis,
    interaction: PortfolioReviewInteractionImpactAnalysis,
) -> None:
    baseline = scenario_pair.baseline
    proposed = scenario_pair.proposed
    common_identity = (
        concentration.source_id == source.source_id
        and concentration.source_digest == source.source_digest
        and concentration.component_ids == source.component_ids
        and interaction.source_id == source.source_id
        and interaction.source_digest == source.source_digest
        and interaction.component_ids == source.component_ids
    )
    if not common_identity:
        raise ValueError(
            "derived analyses must preserve exact source and component identity"
        )

    concentration_scenarios = (
        (
            concentration.baseline_concentration,
            concentration.baseline_universe_coverage,
            baseline,
        ),
        (
            concentration.proposed_concentration,
            concentration.proposed_universe_coverage,
            proposed,
        ),
    )
    if any(
        summary.scenario_id != scenario.scenario_id
        or summary.scenario_digest != scenario.scenario_digest
        or coverage.scenario_id != scenario.scenario_id
        or coverage.scenario_digest != scenario.scenario_digest
        for summary, coverage, scenario in concentration_scenarios
    ):
        raise ValueError(
            "concentration evidence must preserve exact scenario identity"
        )
    if tuple(
        exposure.component_id
        for exposure in concentration.component_exposures
    ) != source.component_ids:
        raise ValueError(
            "component exposure evidence must preserve source order"
        )

    if (
        interaction.proposed_component_id
        != proposed.proposed_component_id
        or interaction.baseline_behavior.scenario_id != baseline.scenario_id
        or interaction.baseline_behavior.scenario_digest
        != baseline.scenario_digest
        or interaction.proposed_behavior.scenario_id != proposed.scenario_id
        or interaction.proposed_behavior.scenario_digest
        != proposed.scenario_digest
        or interaction.candidate_baseline_correlation.candidate_component_id
        != proposed.proposed_component_id
        or interaction.candidate_baseline_correlation.baseline_scenario_id
        != baseline.scenario_id
        or interaction.candidate_baseline_correlation.baseline_scenario_digest
        != baseline.scenario_digest
    ):
        raise ValueError(
            "interaction evidence must preserve exact scenario authority"
        )
    expected_pairs = _expected_component_pairs(source.component_ids)
    if tuple(
        (row.left_component_id, row.right_component_id)
        for row in interaction.symbol_overlaps
    ) != expected_pairs or tuple(
        (row.left_component_id, row.right_component_id)
        for row in interaction.pairwise_correlations
    ) != expected_pairs:
        raise ValueError(
            "interaction evidence must preserve source pair order"
        )
    if tuple(
        row.component_id
        for row in interaction.baseline_behavior.component_contributions
    ) != source.component_ids or tuple(
        row.component_id
        for row in interaction.proposed_behavior.component_contributions
    ) != source.component_ids or tuple(
        row.component_id
        for row in interaction.component_contribution_impacts
    ) != source.component_ids:
        raise ValueError(
            "behavior and impact evidence must preserve source order"
        )


def _new_analysis_artifact(
    **values: object,
) -> PortfolioReviewAnalysisArtifact:
    result = object.__new__(PortfolioReviewAnalysisArtifact)
    for field_name, value in values.items():
        object.__setattr__(result, field_name, value)
    object.__setattr__(
        result,
        "analysis_digest",
        _canonical_digest(result._payload_without_digest()),
    )
    return result


def create_portfolio_review_analysis_artifact(
    *,
    review_id: str,
    source: PortfolioReviewSource,
    scenario_pair: PortfolioReviewScenarioPair,
    created_by: str,
    created_timestamp: object,
    assumptions: Sequence[str] = (),
    warnings: Sequence[str] = (),
    missing_evidence: Sequence[str] = (),
) -> PortfolioReviewAnalysisArtifact:
    """Compose exact S170-S172 authority into one immutable analysis."""
    _validate_input_authority(source, scenario_pair)
    concentration = analyze_portfolio_review_concentration_and_exposure(
        source=source,
        scenario_pair=scenario_pair,
    )
    interaction = analyze_portfolio_review_interaction_and_impact(
        source=source,
        scenario_pair=scenario_pair,
    )
    _validate_derived_authority(
        source=source,
        scenario_pair=scenario_pair,
        concentration=concentration,
        interaction=interaction,
    )
    baseline = scenario_pair.baseline
    proposed = scenario_pair.proposed
    return _new_analysis_artifact(
        review_id=_normalize_required_string(review_id, "review_id"),
        analysis_evidence_scope=PORTFOLIO_REVIEW_ANALYSIS_EVIDENCE_SCOPE,
        source_id=source.source_id,
        source_digest=source.source_digest,
        component_ids=source.component_ids,
        baseline_scenario_id=baseline.scenario_id,
        baseline_scenario_digest=baseline.scenario_digest,
        proposed_scenario_id=proposed.scenario_id,
        proposed_scenario_digest=proposed.scenario_digest,
        proposed_component_id=proposed.proposed_component_id,
        baseline_scenario=baseline,
        proposed_scenario=proposed,
        concentration_exposure_analysis=concentration,
        interaction_impact_analysis=interaction,
        assumptions=_normalize_string_sequence(assumptions, "assumptions"),
        warnings=_normalize_string_sequence(warnings, "warnings"),
        missing_evidence=_normalize_string_sequence(
            missing_evidence,
            "missing_evidence",
        ),
        created_by=_normalize_required_string(created_by, "created_by"),
        created_timestamp=_normalize_utc_timestamp(
            created_timestamp,
            "created_timestamp",
        ),
    )
