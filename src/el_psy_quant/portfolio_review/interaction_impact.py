"""Pure Sprint 172 interaction and proposed-impact analysis boundary."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from el_psy_quant.portfolio_review._derived import (
    new_derived,
    reject_public_construction,
)
from el_psy_quant.portfolio_review.behavior import (
    PortfolioReviewScenarioBehavior,
    _scenario_behavior,
)
from el_psy_quant.portfolio_review.impact import (
    PortfolioReviewComponentContributionImpact,
    PortfolioReviewProposedImpact,
    _proposed_impact,
)
from el_psy_quant.portfolio_review.interaction import (
    PortfolioReviewCandidateBaselineCorrelation,
    PortfolioReviewPairwiseCorrelation,
    PortfolioReviewSymbolOverlap,
    _candidate_baseline_correlation,
    _pairwise_correlations,
    _symbol_overlaps,
)
from el_psy_quant.portfolio_review.scenarios import (
    PortfolioReviewBaselineScenario,
    PortfolioReviewProposedScenario,
    PortfolioReviewScenarioPair,
)
from el_psy_quant.portfolio_review.sources import PortfolioReviewSource

PORTFOLIO_REVIEW_INTERACTION_IMPACT_ANALYSIS_SCHEMA_VERSION = 1


@dataclass(frozen=True, init=False)
class PortfolioReviewInteractionImpactAnalysis:
    """Immutable derived Sprint 172 result for one exact source and pair."""

    source_id: str
    source_digest: str
    component_ids: tuple[str, ...]
    proposed_component_id: str
    symbol_overlaps: tuple[PortfolioReviewSymbolOverlap, ...]
    pairwise_correlations: tuple[
        PortfolioReviewPairwiseCorrelation, ...
    ]
    candidate_baseline_correlation: (
        PortfolioReviewCandidateBaselineCorrelation
    )
    baseline_behavior: PortfolioReviewScenarioBehavior
    proposed_behavior: PortfolioReviewScenarioBehavior
    proposed_impact: PortfolioReviewProposedImpact
    component_contribution_impacts: tuple[
        PortfolioReviewComponentContributionImpact, ...
    ]

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return the deterministic strictly JSON-compatible analysis."""
        return {
            "schema_version": (
                PORTFOLIO_REVIEW_INTERACTION_IMPACT_ANALYSIS_SCHEMA_VERSION
            ),
            "source_id": self.source_id,
            "source_digest": self.source_digest,
            "component_ids": list(self.component_ids),
            "proposed_component_id": self.proposed_component_id,
            "symbol_overlaps": [
                overlap.to_dict() for overlap in self.symbol_overlaps
            ],
            "pairwise_correlations": [
                correlation.to_dict()
                for correlation in self.pairwise_correlations
            ],
            "candidate_baseline_correlation": (
                self.candidate_baseline_correlation.to_dict()
            ),
            "baseline_behavior": self.baseline_behavior.to_dict(),
            "proposed_behavior": self.proposed_behavior.to_dict(),
            "proposed_impact": self.proposed_impact.to_dict(),
            "component_contribution_impacts": [
                impact.to_dict()
                for impact in self.component_contribution_impacts
            ],
        }


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

    proposed_component_id = scenario_pair.proposed.proposed_component_id
    if proposed_component_id not in source.component_ids:
        raise ValueError(
            "proposed_component_id must identify a source component"
        )
    baseline_weights = dict(scenario_pair.baseline.component_weights)
    proposed_weights = dict(scenario_pair.proposed.component_weights)
    if (
        baseline_weights[proposed_component_id]
        == proposed_weights[proposed_component_id]
    ):
        raise ValueError(
            "the proposed component weight must differ between scenarios"
        )


def _aligned_returns_from_source(
    source: PortfolioReviewSource,
) -> pd.DataFrame:
    """Reconstruct the exact validated source table in memory."""
    return pd.DataFrame(
        [
            observation.component_returns
            for observation in source.return_observations
        ],
        index=pd.DatetimeIndex(
            [
                observation.timestamp
                for observation in source.return_observations
            ]
        ),
        columns=list(source.component_ids),
        dtype=float,
    )


def analyze_portfolio_review_interaction_and_impact(
    *,
    source: PortfolioReviewSource,
    scenario_pair: PortfolioReviewScenarioPair,
) -> PortfolioReviewInteractionImpactAnalysis:
    """Calculate immutable historical interaction and proposed-impact evidence."""
    _validate_analysis_authority(source, scenario_pair)
    aligned_returns = _aligned_returns_from_source(source)
    baseline = scenario_pair.baseline
    proposed = scenario_pair.proposed
    baseline_behavior, baseline_portfolio_return = _scenario_behavior(
        source=source,
        aligned_returns=aligned_returns,
        scenario_id=baseline.scenario_id,
        scenario_digest=baseline.scenario_digest,
        component_weights=baseline.component_weights,
    )
    proposed_behavior, _ = _scenario_behavior(
        source=source,
        aligned_returns=aligned_returns,
        scenario_id=proposed.scenario_id,
        scenario_digest=proposed.scenario_digest,
        component_weights=proposed.component_weights,
    )
    proposed_impact, contribution_impacts = _proposed_impact(
        baseline=baseline_behavior,
        proposed=proposed_behavior,
    )
    proposed_component_id = proposed.proposed_component_id
    baseline_weights = dict(baseline.component_weights)
    return new_derived(
        PortfolioReviewInteractionImpactAnalysis,
        source_id=source.source_id,
        source_digest=source.source_digest,
        component_ids=source.component_ids,
        proposed_component_id=proposed_component_id,
        symbol_overlaps=_symbol_overlaps(source),
        pairwise_correlations=_pairwise_correlations(source),
        candidate_baseline_correlation=_candidate_baseline_correlation(
            source=source,
            aligned_returns=aligned_returns,
            baseline_portfolio_return=baseline_portfolio_return,
            candidate_component_id=proposed_component_id,
            candidate_baseline_weight=baseline_weights[proposed_component_id],
            baseline_scenario_id=baseline.scenario_id,
            baseline_scenario_digest=baseline.scenario_digest,
        ),
        baseline_behavior=baseline_behavior,
        proposed_behavior=proposed_behavior,
        proposed_impact=proposed_impact,
        component_contribution_impacts=contribution_impacts,
    )  # type: ignore[return-value]
