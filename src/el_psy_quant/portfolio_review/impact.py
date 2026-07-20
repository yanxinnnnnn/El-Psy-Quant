"""Exact proposed-minus-baseline historical portfolio-review impact."""

from __future__ import annotations

from dataclasses import dataclass

from el_psy_quant.portfolio_review._derived import (
    canonical_float,
    new_derived,
    reject_public_construction,
)
from el_psy_quant.portfolio_review.behavior import (
    PortfolioReviewScenarioBehavior,
)

PORTFOLIO_REVIEW_PROPOSED_IMPACT_SCHEMA_VERSION = 1
PORTFOLIO_REVIEW_COMPONENT_CONTRIBUTION_IMPACT_SCHEMA_VERSION = 1


@dataclass(frozen=True, init=False)
class PortfolioReviewProposedImpact:
    """Immutable scalar impact calculated as proposed minus baseline."""

    mean_return_delta: float
    sample_volatility_delta: float
    annualized_volatility_delta: float | None
    min_return_delta: float
    max_return_delta: float
    positive_periods_delta: int
    negative_periods_delta: int
    zero_periods_delta: int
    loss_rate_delta: float
    ending_equity_delta: float
    cumulative_return_delta: float
    max_drawdown_delta: float

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic strictly JSON-compatible payload."""
        return {
            "schema_version": PORTFOLIO_REVIEW_PROPOSED_IMPACT_SCHEMA_VERSION,
            "mean_return_delta": self.mean_return_delta,
            "sample_volatility_delta": self.sample_volatility_delta,
            "annualized_volatility_delta": self.annualized_volatility_delta,
            "min_return_delta": self.min_return_delta,
            "max_return_delta": self.max_return_delta,
            "positive_periods_delta": self.positive_periods_delta,
            "negative_periods_delta": self.negative_periods_delta,
            "zero_periods_delta": self.zero_periods_delta,
            "loss_rate_delta": self.loss_rate_delta,
            "ending_equity_delta": self.ending_equity_delta,
            "cumulative_return_delta": self.cumulative_return_delta,
            "max_drawdown_delta": self.max_drawdown_delta,
        }


@dataclass(frozen=True, init=False)
class PortfolioReviewComponentContributionImpact:
    """Immutable component impact calculated as proposed minus baseline."""

    component_id: str
    strategy_id: str
    baseline_weight: float
    proposed_weight: float
    total_contribution_delta: float
    mean_contribution_delta: float
    positive_periods_delta: int
    negative_periods_delta: int
    zero_periods_delta: int

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic strictly JSON-compatible payload."""
        return {
            "schema_version": (
                PORTFOLIO_REVIEW_COMPONENT_CONTRIBUTION_IMPACT_SCHEMA_VERSION
            ),
            "component_id": self.component_id,
            "strategy_id": self.strategy_id,
            "baseline_weight": self.baseline_weight,
            "proposed_weight": self.proposed_weight,
            "total_contribution_delta": self.total_contribution_delta,
            "mean_contribution_delta": self.mean_contribution_delta,
            "positive_periods_delta": self.positive_periods_delta,
            "negative_periods_delta": self.negative_periods_delta,
            "zero_periods_delta": self.zero_periods_delta,
        }


def _delta(proposed: float, baseline: float, field_name: str) -> float:
    return canonical_float(proposed - baseline, field_name)


def _proposed_impact(
    *,
    baseline: PortfolioReviewScenarioBehavior,
    proposed: PortfolioReviewScenarioBehavior,
) -> tuple[
    PortfolioReviewProposedImpact,
    tuple[PortfolioReviewComponentContributionImpact, ...],
]:
    if (
        baseline.annualized_volatility is None
        or proposed.annualized_volatility is None
    ):
        annualized_volatility_delta = None
    else:
        annualized_volatility_delta = _delta(
            proposed.annualized_volatility,
            baseline.annualized_volatility,
            "annualized_volatility_delta",
        )

    impact = new_derived(
        PortfolioReviewProposedImpact,
        mean_return_delta=_delta(
            proposed.mean_return,
            baseline.mean_return,
            "mean_return_delta",
        ),
        sample_volatility_delta=_delta(
            proposed.sample_volatility,
            baseline.sample_volatility,
            "sample_volatility_delta",
        ),
        annualized_volatility_delta=annualized_volatility_delta,
        min_return_delta=_delta(
            proposed.min_return,
            baseline.min_return,
            "min_return_delta",
        ),
        max_return_delta=_delta(
            proposed.max_return,
            baseline.max_return,
            "max_return_delta",
        ),
        positive_periods_delta=(
            proposed.positive_periods - baseline.positive_periods
        ),
        negative_periods_delta=(
            proposed.negative_periods - baseline.negative_periods
        ),
        zero_periods_delta=proposed.zero_periods - baseline.zero_periods,
        loss_rate_delta=_delta(
            proposed.loss_rate,
            baseline.loss_rate,
            "loss_rate_delta",
        ),
        ending_equity_delta=_delta(
            proposed.ending_equity,
            baseline.ending_equity,
            "ending_equity_delta",
        ),
        cumulative_return_delta=_delta(
            proposed.cumulative_return,
            baseline.cumulative_return,
            "cumulative_return_delta",
        ),
        max_drawdown_delta=_delta(
            proposed.worst_drawdown.max_drawdown,
            baseline.worst_drawdown.max_drawdown,
            "max_drawdown_delta",
        ),
    )

    contribution_impacts: list[
        PortfolioReviewComponentContributionImpact
    ] = []
    for baseline_row, proposed_row in zip(
        baseline.component_contributions,
        proposed.component_contributions,
        strict=True,
    ):
        if (
            baseline_row.component_id != proposed_row.component_id
            or baseline_row.strategy_id != proposed_row.strategy_id
        ):
            raise ValueError(
                "baseline and proposed contributions must share source order"
            )
        contribution_impacts.append(
            new_derived(
                PortfolioReviewComponentContributionImpact,
                component_id=baseline_row.component_id,
                strategy_id=baseline_row.strategy_id,
                baseline_weight=baseline_row.weight,
                proposed_weight=proposed_row.weight,
                total_contribution_delta=_delta(
                    proposed_row.total_contribution,
                    baseline_row.total_contribution,
                    "total_contribution_delta",
                ),
                mean_contribution_delta=_delta(
                    proposed_row.mean_contribution,
                    baseline_row.mean_contribution,
                    "mean_contribution_delta",
                ),
                positive_periods_delta=(
                    proposed_row.positive_periods
                    - baseline_row.positive_periods
                ),
                negative_periods_delta=(
                    proposed_row.negative_periods
                    - baseline_row.negative_periods
                ),
                zero_periods_delta=(
                    proposed_row.zero_periods - baseline_row.zero_periods
                ),
            )
        )
    return (
        impact,  # type: ignore[return-value]
        tuple(contribution_impacts),
    )
