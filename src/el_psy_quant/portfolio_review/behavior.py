"""Historical static-scenario behavior for portfolio review."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from el_psy_quant.portfolio import (
    equity_curve,
    inspect_portfolio_drawdown,
    portfolio_risk_summary,
    summarize_symbol_contributions,
    symbol_contribution_returns,
    weighted_portfolio_return,
)
from el_psy_quant.portfolio_review._derived import (
    canonical_float,
    new_derived,
    reject_public_construction,
)
from el_psy_quant.portfolio_review.sources import PortfolioReviewSource

PORTFOLIO_REVIEW_WORST_DRAWDOWN_SCHEMA_VERSION = 1
PORTFOLIO_REVIEW_COMPONENT_CONTRIBUTION_SCHEMA_VERSION = 1
PORTFOLIO_REVIEW_SCENARIO_BEHAVIOR_SCHEMA_VERSION = 1


@dataclass(frozen=True, init=False)
class PortfolioReviewWorstDrawdown:
    """Immutable existing-authority worst-drawdown context."""

    max_drawdown: float
    peak_date: str
    trough_date: str
    recovery_date: str | None
    recovered: bool
    duration_periods: int
    time_to_trough_periods: int
    time_to_recovery_periods: int | None

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic strictly JSON-compatible payload."""
        return {
            "schema_version": PORTFOLIO_REVIEW_WORST_DRAWDOWN_SCHEMA_VERSION,
            "max_drawdown": self.max_drawdown,
            "peak_date": self.peak_date,
            "trough_date": self.trough_date,
            "recovery_date": self.recovery_date,
            "recovered": self.recovered,
            "duration_periods": self.duration_periods,
            "time_to_trough_periods": self.time_to_trough_periods,
            "time_to_recovery_periods": self.time_to_recovery_periods,
        }


@dataclass(frozen=True, init=False)
class PortfolioReviewComponentContribution:
    """Immutable source-ordered static component contribution evidence."""

    component_id: str
    strategy_id: str
    weight: float
    total_contribution: float
    mean_contribution: float
    positive_periods: int
    negative_periods: int
    zero_periods: int

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic strictly JSON-compatible payload."""
        return {
            "schema_version": (
                PORTFOLIO_REVIEW_COMPONENT_CONTRIBUTION_SCHEMA_VERSION
            ),
            "component_id": self.component_id,
            "strategy_id": self.strategy_id,
            "weight": self.weight,
            "total_contribution": self.total_contribution,
            "mean_contribution": self.mean_contribution,
            "positive_periods": self.positive_periods,
            "negative_periods": self.negative_periods,
            "zero_periods": self.zero_periods,
        }


@dataclass(frozen=True, init=False)
class PortfolioReviewScenarioBehavior:
    """Immutable historical behavior for one exact static-weight scenario."""

    scenario_id: str
    scenario_digest: str
    observation_count: int
    evaluation_start_timestamp: str
    evaluation_end_timestamp: str
    periods_per_year: float | None
    mean_return: float
    sample_volatility: float
    annualized_volatility: float | None
    min_return: float
    max_return: float
    positive_periods: int
    negative_periods: int
    zero_periods: int
    loss_rate: float
    ending_equity: float
    cumulative_return: float
    worst_drawdown: PortfolioReviewWorstDrawdown
    component_contributions: tuple[
        PortfolioReviewComponentContribution, ...
    ]

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic strictly JSON-compatible payload."""
        return {
            "schema_version": PORTFOLIO_REVIEW_SCENARIO_BEHAVIOR_SCHEMA_VERSION,
            "scenario_id": self.scenario_id,
            "scenario_digest": self.scenario_digest,
            "observation_count": self.observation_count,
            "evaluation_start_timestamp": self.evaluation_start_timestamp,
            "evaluation_end_timestamp": self.evaluation_end_timestamp,
            "periods_per_year": self.periods_per_year,
            "mean_return": self.mean_return,
            "sample_volatility": self.sample_volatility,
            "annualized_volatility": self.annualized_volatility,
            "min_return": self.min_return,
            "max_return": self.max_return,
            "positive_periods": self.positive_periods,
            "negative_periods": self.negative_periods,
            "zero_periods": self.zero_periods,
            "loss_rate": self.loss_rate,
            "ending_equity": self.ending_equity,
            "cumulative_return": self.cumulative_return,
            "worst_drawdown": self.worst_drawdown.to_dict(),
            "component_contributions": [
                contribution.to_dict()
                for contribution in self.component_contributions
            ],
        }


def _drawdown_result(equity: pd.Series) -> PortfolioReviewWorstDrawdown:
    payload = inspect_portfolio_drawdown(equity)
    recovery_periods = payload["time_to_recovery_periods"]
    return new_derived(
        PortfolioReviewWorstDrawdown,
        max_drawdown=canonical_float(
            float(payload["max_drawdown"]),
            "max_drawdown",
        ),
        peak_date=str(payload["peak_date"]),
        trough_date=str(payload["trough_date"]),
        recovery_date=(
            str(payload["recovery_date"])
            if payload["recovery_date"] is not None
            else None
        ),
        recovered=bool(payload["recovered"]),
        duration_periods=int(payload["duration_periods"]),
        time_to_trough_periods=int(payload["time_to_trough_periods"]),
        time_to_recovery_periods=(
            int(recovery_periods) if recovery_periods is not None else None
        ),
    )  # type: ignore[return-value]


def _component_contributions(
    *,
    source: PortfolioReviewSource,
    aligned_returns: pd.DataFrame,
    component_weights: tuple[tuple[str, float], ...],
) -> tuple[PortfolioReviewComponentContribution, ...]:
    weights = dict(component_weights)
    contribution_returns = symbol_contribution_returns(
        aligned_returns,
        weights,
    )
    summary = summarize_symbol_contributions(contribution_returns)
    results: list[PortfolioReviewComponentContribution] = []
    for index, component in enumerate(source.components):
        row = summary.iloc[index]
        if str(row["symbol"]) != component.component_id:
            raise ValueError(
                "component contribution authority changed source order"
            )
        results.append(
            new_derived(
                PortfolioReviewComponentContribution,
                component_id=component.component_id,
                strategy_id=component.strategy_id,
                weight=weights[component.component_id],
                total_contribution=canonical_float(
                    float(row["total_contribution"]),
                    "total_contribution",
                ),
                mean_contribution=canonical_float(
                    float(row["mean_contribution"]),
                    "mean_contribution",
                ),
                positive_periods=int(row["positive_periods"]),
                negative_periods=int(row["negative_periods"]),
                zero_periods=int(row["zero_periods"]),
            )
        )
    return tuple(results)


def _scenario_behavior(
    *,
    source: PortfolioReviewSource,
    aligned_returns: pd.DataFrame,
    scenario_id: str,
    scenario_digest: str,
    component_weights: tuple[tuple[str, float], ...],
) -> tuple[PortfolioReviewScenarioBehavior, pd.Series]:
    portfolio_return = weighted_portfolio_return(
        aligned_returns,
        dict(component_weights),
    )
    if (portfolio_return <= -1.0).any():
        raise ValueError(
            f"{scenario_id} portfolio period returns must be greater than -1.0"
        )

    risk = portfolio_risk_summary(
        portfolio_return,
        periods_per_year=source.periods_per_year,
    )
    equity = equity_curve(portfolio_return, initial_capital=1.0)
    ending_equity = canonical_float(
        float(equity.iloc[-1]),
        "ending_equity",
    )
    annualized = risk.get("annualized_volatility")
    behavior = new_derived(
        PortfolioReviewScenarioBehavior,
        scenario_id=scenario_id,
        scenario_digest=scenario_digest,
        observation_count=len(source.return_observations),
        evaluation_start_timestamp=(
            source.return_observations[0].timestamp.isoformat()
        ),
        evaluation_end_timestamp=(
            source.return_observations[-1].timestamp.isoformat()
        ),
        periods_per_year=source.periods_per_year,
        mean_return=canonical_float(
            risk["mean_return"],
            "mean_return",
        ),
        sample_volatility=canonical_float(
            risk["volatility"],
            "sample_volatility",
        ),
        annualized_volatility=(
            canonical_float(annualized, "annualized_volatility")
            if annualized is not None
            else None
        ),
        min_return=canonical_float(risk["min_return"], "min_return"),
        max_return=canonical_float(risk["max_return"], "max_return"),
        positive_periods=int(risk["positive_periods"]),
        negative_periods=int(risk["negative_periods"]),
        zero_periods=int(risk["zero_periods"]),
        loss_rate=canonical_float(risk["loss_rate"], "loss_rate"),
        ending_equity=ending_equity,
        cumulative_return=canonical_float(
            ending_equity - 1.0,
            "cumulative_return",
        ),
        worst_drawdown=_drawdown_result(equity),
        component_contributions=_component_contributions(
            source=source,
            aligned_returns=aligned_returns,
            component_weights=component_weights,
        ),
    )
    return behavior, portfolio_return  # type: ignore[return-value]
