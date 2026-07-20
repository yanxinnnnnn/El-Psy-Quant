import inspect
import json
import math
from dataclasses import FrozenInstanceError

import pandas as pd
import pytest

from el_psy_quant.portfolio import (
    equity_curve,
    inspect_portfolio_drawdown,
    portfolio_risk_summary,
    summarize_symbol_contributions,
    symbol_contribution_returns,
    weighted_portfolio_return,
)
from el_psy_quant.portfolio_review import (
    PortfolioReviewBaselineScenario,
    PortfolioReviewCandidateBaselineCorrelation,
    PortfolioReviewComponentContribution,
    PortfolioReviewComponentContributionImpact,
    PortfolioReviewInteractionImpactAnalysis,
    PortfolioReviewPairwiseCorrelation,
    PortfolioReviewProposedImpact,
    PortfolioReviewProposedScenario,
    PortfolioReviewScenarioBehavior,
    PortfolioReviewScenarioPair,
    PortfolioReviewSymbolOverlap,
    PortfolioReviewWorstDrawdown,
    SUPPORTED_PORTFOLIO_REVIEW_AVAILABILITY_STATUSES,
    SUPPORTED_PORTFOLIO_REVIEW_CORRELATION_UNAVAILABLE_REASONS,
    SUPPORTED_PORTFOLIO_REVIEW_SYMBOL_OVERLAP_UNAVAILABLE_REASONS,
    analyze_portfolio_review_interaction_and_impact,
    create_portfolio_review_baseline_scenario,
    create_portfolio_review_component,
    create_portfolio_review_evidence_reference,
    create_portfolio_review_proposed_scenario,
    create_portfolio_review_scenario_pair,
    create_portfolio_review_source,
)


def _source(
    *,
    returns: tuple[tuple[float, ...], ...],
    symbols: tuple[tuple[str, ...] | None, ...] | None = None,
    source_id: str = "synthetic-source",
    periods_per_year: float | None = 252.0,
):
    component_count = len(returns)
    if symbols is None:
        symbols = tuple((f"SYN-{index}",) for index in range(component_count))
    components = tuple(
        create_portfolio_review_component(
            component_id=f"component-{index}",
            strategy_id=f"synthetic-strategy-{index}",
            evidence_references=(
                create_portfolio_review_evidence_reference(
                    reference_type="research_run",
                    reference_id=f"synthetic-run-{index}",
                ),
            ),
            symbols=component_symbols,
        )
        for index, component_symbols in enumerate(symbols, start=1)
    )
    return create_portfolio_review_source(
        source_id=source_id,
        components=components,
        aligned_returns=pd.DataFrame(
            {
                component.component_id: component_returns
                for component, component_returns in zip(
                    components,
                    returns,
                    strict=True,
                )
            },
            index=pd.date_range(
                "2025-07-01",
                periods=len(returns[0]),
                freq="D",
            ),
        ),
        evaluation_frequency="daily",
        periods_per_year=periods_per_year,
        created_by="synthetic-founder",
        created_timestamp="2025-07-20T00:00:00Z",
        assumptions=("Synthetic aligned history",),
        warnings=("Scenario weights are not holdings",),
    )


def _pair(
    *,
    source,
    baseline_weights: tuple[float, ...],
    proposed_weights: tuple[float, ...],
    proposed_component_index: int = 1,
):
    baseline = create_portfolio_review_baseline_scenario(
        scenario_id="synthetic-baseline",
        source=source,
        weights=dict(
            zip(source.component_ids, baseline_weights, strict=True)
        ),
        rationale="Synthetic baseline",
    )
    proposed = create_portfolio_review_proposed_scenario(
        scenario_id="synthetic-proposed",
        source=source,
        weights=dict(
            zip(source.component_ids, proposed_weights, strict=True)
        ),
        proposed_component_id=source.component_ids[
            proposed_component_index
        ],
        rationale="Synthetic proposal",
    )
    return create_portfolio_review_scenario_pair(
        source=source,
        baseline=baseline,
        proposed=proposed,
    )


def _analysis(
    *,
    returns: tuple[tuple[float, ...], ...],
    baseline_weights: tuple[float, ...],
    proposed_weights: tuple[float, ...],
    symbols: tuple[tuple[str, ...] | None, ...] | None = None,
    proposed_component_index: int = 1,
    periods_per_year: float | None = 252.0,
):
    source = _source(
        returns=returns,
        symbols=symbols,
        periods_per_year=periods_per_year,
    )
    pair = _pair(
        source=source,
        baseline_weights=baseline_weights,
        proposed_weights=proposed_weights,
        proposed_component_index=proposed_component_index,
    )
    return (
        source,
        pair,
        analyze_portfolio_review_interaction_and_impact(
            source=source,
            scenario_pair=pair,
        ),
    )


@pytest.mark.parametrize("component_count", [2, 3, 12])
def test_overlap_pair_count_and_source_order(component_count: int) -> None:
    returns = tuple(
        tuple((index + 1) * value for value in (0.01, -0.02, 0.03))
        for index in range(component_count)
    )
    baseline = (1.0,) + (0.0,) * (component_count - 1)
    proposed = (0.5, 0.5) + (0.0,) * (component_count - 2)
    source, _, result = _analysis(
        returns=returns,
        baseline_weights=baseline,
        proposed_weights=proposed,
    )

    expected_pairs = tuple(
        (source.component_ids[left], source.component_ids[right])
        for left in range(component_count - 1)
        for right in range(left + 1, component_count)
    )
    overlap_pairs = tuple(
        (row.left_component_id, row.right_component_id)
        for row in result.symbol_overlaps
    )
    correlation_pairs = tuple(
        (row.left_component_id, row.right_component_id)
        for row in result.pairwise_correlations
    )
    assert len(overlap_pairs) == component_count * (component_count - 1) // 2
    assert overlap_pairs == expected_pairs
    assert correlation_pairs == expected_pairs


def test_symbol_overlap_available_missing_and_exact_set_semantics() -> None:
    _, _, result = _analysis(
        returns=(
            (0.01, 0.02, 0.03),
            (0.02, 0.01, 0.04),
            (-0.01, 0.03, 0.02),
            (0.00, 0.01, -0.01),
            (0.04, -0.02, 0.01),
        ),
        symbols=(
            ("SYN-C", "SYN-A", "SYN-B"),
            ("SYN-B", "SYN-C", "SYN-D"),
            ("SYN-X",),
            None,
            ("SYN-C", "SYN-A", "SYN-B"),
        ),
        baseline_weights=(1.0, 0.0, 0.0, 0.0, 0.0),
        proposed_weights=(0.75, 0.25, 0.0, 0.0, 0.0),
    )
    rows = {
        (row.left_component_id, row.right_component_id): row
        for row in result.symbol_overlaps
    }

    partial = rows[("component-1", "component-2")]
    assert partial.status == "available"
    assert partial.shared_symbols == ("SYN-C", "SYN-B")
    assert partial.shared_symbol_count == 2
    assert partial.union_symbol_count == 4
    assert partial.jaccard_overlap == 0.5
    assert partial.missing_symbol_component_ids == ()
    assert partial.unavailable_reason is None

    disjoint = rows[("component-1", "component-3")]
    assert disjoint.shared_symbols == ()
    assert disjoint.shared_symbol_count == 0
    assert disjoint.union_symbol_count == 4
    assert disjoint.jaccard_overlap == 0.0

    full = rows[("component-1", "component-5")]
    assert full.shared_symbols == ("SYN-C", "SYN-A", "SYN-B")
    assert full.shared_symbol_count == 3
    assert full.union_symbol_count == 3
    assert full.jaccard_overlap == 1.0

    missing = rows[("component-1", "component-4")]
    assert missing.status == "unavailable"
    assert missing.unavailable_reason == "missing_symbol_evidence"
    assert missing.missing_symbol_component_ids == ("component-4",)
    assert missing.shared_symbols is None
    assert missing.shared_symbol_count is None
    assert missing.union_symbol_count is None
    assert missing.jaccard_overlap is None

    both_missing_source = _source(
        returns=((0.01, 0.02, 0.03), (0.02, 0.03, 0.04)),
        symbols=(None, None),
    )
    both_missing_pair = _pair(
        source=both_missing_source,
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.5, 0.5),
    )
    both_missing = analyze_portfolio_review_interaction_and_impact(
        source=both_missing_source,
        scenario_pair=both_missing_pair,
    ).symbol_overlaps[0]
    assert both_missing.missing_symbol_component_ids == (
        "component-1",
        "component-2",
    )
    assert SUPPORTED_PORTFOLIO_REVIEW_AVAILABILITY_STATUSES == (
        "available",
        "unavailable",
    )
    assert SUPPORTED_PORTFOLIO_REVIEW_SYMBOL_OVERLAP_UNAVAILABLE_REASONS == (
        "missing_symbol_evidence",
    )


def _pearson(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    left_mean = math.fsum(left) / len(left)
    right_mean = math.fsum(right) / len(right)
    numerator = math.fsum(
        (left_value - left_mean) * (right_value - right_mean)
        for left_value, right_value in zip(left, right, strict=True)
    )
    left_ss = math.fsum((value - left_mean) ** 2 for value in left)
    right_ss = math.fsum((value - right_mean) ** 2 for value in right)
    return numerator / math.sqrt(left_ss * right_ss)


def test_pairwise_pearson_formula_range_and_evaluation_identity() -> None:
    returns = (
        (0.01, 0.02, 0.03, 0.04),
        (0.02, 0.04, 0.06, 0.08),
        (-0.01, -0.02, -0.03, -0.04),
        (0.03, -0.01, 0.02, 0.04),
    )
    source, _, result = _analysis(
        returns=returns,
        baseline_weights=(1.0, 0.0, 0.0, 0.0),
        proposed_weights=(0.75, 0.25, 0.0, 0.0),
    )
    rows = {
        (row.left_component_id, row.right_component_id): row
        for row in result.pairwise_correlations
    }

    assert rows[("component-1", "component-2")].correlation == 1.0
    assert rows[("component-1", "component-3")].correlation == -1.0
    assert rows[("component-1", "component-4")].correlation == pytest.approx(
        _pearson(returns[0], returns[3]),
    )
    for row in result.pairwise_correlations:
        assert row.status == "available"
        assert row.unavailable_reason is None
        assert row.zero_variance_series == ()
        assert row.correlation is not None
        assert -1.0 <= row.correlation <= 1.0
        assert row.observation_count == 4
        assert row.evaluation_start_timestamp == (
            source.return_observations[0].timestamp.isoformat()
        )
        assert row.evaluation_end_timestamp == (
            source.return_observations[-1].timestamp.isoformat()
        )


def test_zero_variance_pairwise_and_near_constant_semantics() -> None:
    _, _, result = _analysis(
        returns=(
            (0.01, 0.01, 0.01, 0.01),
            (0.00, 0.01, 0.02, 0.03),
            (0.02, 0.02, 0.02, 0.02),
            (1.0, 1.0 + 1e-12, 1.0 - 1e-12, 1.0 + 2e-12),
        ),
        baseline_weights=(1.0, 0.0, 0.0, 0.0),
        proposed_weights=(0.5, 0.5, 0.0, 0.0),
    )
    rows = {
        (row.left_component_id, row.right_component_id): row
        for row in result.pairwise_correlations
    }

    left_constant = rows[("component-1", "component-2")]
    assert left_constant.status == "unavailable"
    assert left_constant.unavailable_reason == "zero_variance"
    assert left_constant.zero_variance_series == ("component-1",)
    assert left_constant.correlation is None

    both_constant = rows[("component-1", "component-3")]
    assert both_constant.zero_variance_series == (
        "component-1",
        "component-3",
    )
    assert both_constant.correlation is None

    right_constant = rows[("component-2", "component-3")]
    assert right_constant.zero_variance_series == ("component-3",)
    assert rows[("component-2", "component-4")].status == "available"
    assert SUPPORTED_PORTFOLIO_REVIEW_CORRELATION_UNAVAILABLE_REASONS == (
        "zero_variance",
    )
    json.dumps(result.to_dict(), allow_nan=False)


def test_pairwise_repeated_point_one_left_component_is_zero_variance() -> None:
    _, _, result = _analysis(
        returns=((0.1, 0.1, 0.1), (0.01, 0.02, 0.03)),
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.5, 0.5),
    )

    correlation = result.pairwise_correlations[0]
    assert correlation.status == "unavailable"
    assert correlation.unavailable_reason == "zero_variance"
    assert correlation.zero_variance_series == ("component-1",)
    assert correlation.correlation is None


def test_pairwise_repeated_point_one_both_components_are_zero_variance() -> None:
    _, _, result = _analysis(
        returns=((0.1, 0.1, 0.1), (0.1, 0.1, 0.1)),
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.5, 0.5),
    )

    correlation = result.pairwise_correlations[0]
    assert correlation.status == "unavailable"
    assert correlation.unavailable_reason == "zero_variance"
    assert correlation.zero_variance_series == (
        "component-1",
        "component-2",
    )
    assert correlation.correlation is None


def test_candidate_correlation_zero_weight_and_self_inclusion() -> None:
    returns = (
        (0.01, 0.02, -0.01, 0.03),
        (0.03, -0.02, 0.04, 0.01),
    )
    _, pair_zero, result_zero = _analysis(
        returns=returns,
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.5, 0.5),
    )
    zero = result_zero.candidate_baseline_correlation
    assert zero.candidate_component_id == "component-2"
    assert zero.candidate_baseline_weight == 0.0
    assert zero.baseline_scenario_id == pair_zero.baseline.scenario_id
    assert zero.baseline_scenario_digest == pair_zero.baseline.scenario_digest
    assert zero.correlation == pytest.approx(_pearson(returns[1], returns[0]))

    source_included = _source(returns=returns)
    pair_included = _pair(
        source=source_included,
        baseline_weights=(0.5, 0.5),
        proposed_weights=(0.25, 0.75),
    )
    result_included = analyze_portfolio_review_interaction_and_impact(
        source=source_included,
        scenario_pair=pair_included,
    )
    baseline_return = tuple(
        0.5 * left + 0.5 * right
        for left, right in zip(returns[0], returns[1], strict=True)
    )
    included = result_included.candidate_baseline_correlation
    assert included.candidate_baseline_weight == 0.5
    assert included.correlation == pytest.approx(
        _pearson(returns[1], baseline_return)
    )


def test_repeated_point_one_candidate_is_zero_variance() -> None:
    _, _, result = _analysis(
        returns=((0.01, 0.02, 0.03), (0.1, 0.1, 0.1)),
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.5, 0.5),
    )

    correlation = result.candidate_baseline_correlation
    assert correlation.status == "unavailable"
    assert correlation.unavailable_reason == "zero_variance"
    assert correlation.zero_variance_series == ("component-2",)
    assert correlation.correlation is None


def test_repeated_point_one_baseline_portfolio_is_zero_variance() -> None:
    _, _, result = _analysis(
        returns=((0.1, 0.1, 0.1), (0.01, 0.02, 0.03)),
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.5, 0.5),
    )

    correlation = result.candidate_baseline_correlation
    assert correlation.status == "unavailable"
    assert correlation.unavailable_reason == "zero_variance"
    assert correlation.zero_variance_series == ("baseline_portfolio",)
    assert correlation.correlation is None


def test_repeated_point_one_candidate_and_baseline_are_zero_variance() -> None:
    _, _, result = _analysis(
        returns=((0.1, 0.1, 0.1), (0.1, 0.1, 0.1)),
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.5, 0.5),
    )

    correlation = result.candidate_baseline_correlation
    assert correlation.status == "unavailable"
    assert correlation.unavailable_reason == "zero_variance"
    assert correlation.zero_variance_series == (
        "component-2",
        "baseline_portfolio",
    )
    assert correlation.correlation is None


@pytest.mark.parametrize(
    ("returns", "baseline_weights", "expected_zero_variance"),
    [
        (
            ((0.01, 0.02, 0.03), (0.04, 0.04, 0.04)),
            (1.0, 0.0),
            ("component-2",),
        ),
        (
            ((0.01, 0.02, 0.03), (0.03, 0.02, 0.01)),
            (0.5, 0.5),
            ("baseline_portfolio",),
        ),
        (
            ((0.00, 0.00, 0.00), (0.04, 0.04, 0.04)),
            (0.5, 0.5),
            ("component-2", "baseline_portfolio"),
        ),
    ],
)
def test_candidate_zero_variance_evidence(
    returns: tuple[tuple[float, ...], ...],
    baseline_weights: tuple[float, ...],
    expected_zero_variance: tuple[str, ...],
) -> None:
    _, _, result = _analysis(
        returns=returns,
        baseline_weights=baseline_weights,
        proposed_weights=(0.25, 0.75),
    )
    candidate = result.candidate_baseline_correlation
    assert candidate.status == "unavailable"
    assert candidate.unavailable_reason == "zero_variance"
    assert candidate.zero_variance_series == expected_zero_variance
    assert candidate.correlation is None


@pytest.mark.parametrize("periods_per_year", [None, 252.0])
def test_scenario_behavior_reuses_existing_portfolio_authority(
    periods_per_year: float | None,
) -> None:
    returns = (
        (0.10, -0.20, 0.25, 0.00),
        (-0.05, 0.10, -0.02, 0.04),
        (0.50, -0.50, 0.25, -0.25),
    )
    source, pair, result = _analysis(
        returns=returns,
        baseline_weights=(0.6, 0.4, 0.0),
        proposed_weights=(0.4, 0.4, 0.2),
        proposed_component_index=2,
        periods_per_year=periods_per_year,
    )
    aligned_returns = pd.DataFrame(
        {
            component_id: component_returns
            for component_id, component_returns in zip(
                source.component_ids,
                returns,
                strict=True,
            )
        },
        index=pd.DatetimeIndex(
            [
                observation.timestamp
                for observation in source.return_observations
            ]
        ),
    )
    expected_return = weighted_portfolio_return(
        aligned_returns,
        dict(pair.baseline.component_weights),
    )
    expected_risk = portfolio_risk_summary(
        expected_return,
        periods_per_year=periods_per_year,
    )
    expected_equity = equity_curve(expected_return, initial_capital=1.0)
    expected_drawdown = inspect_portfolio_drawdown(expected_equity)
    expected_contributions = summarize_symbol_contributions(
        symbol_contribution_returns(
            aligned_returns,
            dict(pair.baseline.component_weights),
        )
    )
    behavior = result.baseline_behavior

    assert behavior.scenario_id == pair.baseline.scenario_id
    assert behavior.scenario_digest == pair.baseline.scenario_digest
    assert behavior.observation_count == len(expected_return)
    assert behavior.periods_per_year == periods_per_year
    assert behavior.mean_return == expected_risk["mean_return"]
    assert behavior.sample_volatility == expected_risk["volatility"]
    assert behavior.annualized_volatility == expected_risk.get(
        "annualized_volatility"
    )
    assert behavior.min_return == expected_risk["min_return"]
    assert behavior.max_return == expected_risk["max_return"]
    assert behavior.positive_periods == int(expected_risk["positive_periods"])
    assert behavior.negative_periods == int(expected_risk["negative_periods"])
    assert behavior.zero_periods == int(expected_risk["zero_periods"])
    assert behavior.loss_rate == expected_risk["loss_rate"]
    assert behavior.ending_equity == expected_equity.iloc[-1]
    assert behavior.cumulative_return == expected_equity.iloc[-1] - 1.0
    assert behavior.worst_drawdown.max_drawdown == (
        expected_drawdown["max_drawdown"]
    )
    assert behavior.worst_drawdown.peak_date == expected_drawdown["peak_date"]
    assert behavior.worst_drawdown.trough_date == (
        expected_drawdown["trough_date"]
    )
    assert behavior.worst_drawdown.recovery_date == (
        expected_drawdown["recovery_date"]
    )

    assert tuple(
        row.component_id for row in behavior.component_contributions
    ) == source.component_ids
    assert tuple(
        row.strategy_id for row in behavior.component_contributions
    ) == tuple(component.strategy_id for component in source.components)
    for index, row in enumerate(behavior.component_contributions):
        expected = expected_contributions.iloc[index]
        assert row.weight == pair.baseline.component_weights[index][1]
        assert row.total_contribution == expected["total_contribution"]
        assert row.mean_contribution == expected["mean_contribution"]
        assert row.positive_periods == expected["positive_periods"]
        assert row.negative_periods == expected["negative_periods"]
        assert row.zero_periods == expected["zero_periods"]

    zero_weight = behavior.component_contributions[2]
    assert zero_weight.weight == 0.0
    assert zero_weight.total_contribution == 0.0
    assert zero_weight.mean_contribution == 0.0
    assert zero_weight.zero_periods == len(expected_return)
    assert isinstance(behavior.positive_periods, int)
    assert isinstance(behavior.worst_drawdown.duration_periods, int)

    payload = behavior.to_dict()
    assert "portfolio_return" not in payload
    assert "equity" not in payload
    json.dumps(payload, allow_nan=False)


@pytest.mark.parametrize(
    ("returns", "expected_recovered", "expected_recovery_date"),
    [
        (
            ((0.01, 0.02, 0.03), (0.02, 0.01, 0.01)),
            True,
            "2025-07-01T00:00:00",
        ),
        (
            ((0.10, -0.20, 0.25), (0.00, 0.00, 0.00)),
            True,
            "2025-07-03T00:00:00",
        ),
        (
            ((0.10, -0.20, 0.05), (0.00, 0.00, 0.00)),
            False,
            None,
        ),
    ],
)
def test_drawdown_no_drawdown_recovered_and_unrecovered_context(
    returns: tuple[tuple[float, ...], ...],
    expected_recovered: bool,
    expected_recovery_date: str | None,
) -> None:
    _, _, result = _analysis(
        returns=returns,
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.5, 0.5),
    )
    drawdown = result.baseline_behavior.worst_drawdown
    assert drawdown.recovered is expected_recovered
    assert drawdown.recovery_date == expected_recovery_date
    if expected_recovery_date is None:
        assert drawdown.time_to_recovery_periods is None
        assert drawdown.duration_periods > 0


def test_scenario_period_return_at_or_below_negative_one_is_rejected() -> None:
    source = _source(
        returns=((-1.0, 0.01, 0.02), (0.00, 0.02, 0.03)),
    )
    pair = _pair(
        source=source,
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.5, 0.5),
    )
    with pytest.raises(ValueError, match="must be greater than -1.0"):
        analyze_portfolio_review_interaction_and_impact(
            source=source,
            scenario_pair=pair,
        )

    below_source = _source(
        returns=((-1.2, 0.01, 0.02), (0.00, 0.02, 0.03)),
    )
    below_pair = _pair(
        source=below_source,
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.5, 0.5),
    )
    with pytest.raises(ValueError, match="must be greater than -1.0"):
        analyze_portfolio_review_interaction_and_impact(
            source=below_source,
            scenario_pair=below_pair,
        )


def test_every_proposed_scalar_and_contribution_impact_is_exact_delta() -> None:
    source, _, result = _analysis(
        returns=(
            (0.10, -0.20, 0.25, 0.00),
            (-0.05, 0.10, -0.02, 0.04),
            (0.02, 0.02, -0.01, -0.01),
        ),
        baseline_weights=(0.6, 0.4, 0.0),
        proposed_weights=(0.4, 0.4, 0.2),
        proposed_component_index=2,
    )
    baseline = result.baseline_behavior
    proposed = result.proposed_behavior
    impact = result.proposed_impact

    scalar_fields = (
        "mean_return",
        "sample_volatility",
        "annualized_volatility",
        "min_return",
        "max_return",
        "loss_rate",
        "ending_equity",
        "cumulative_return",
    )
    for field_name in scalar_fields:
        baseline_value = getattr(baseline, field_name)
        proposed_value = getattr(proposed, field_name)
        delta_value = getattr(impact, f"{field_name}_delta")
        assert delta_value == proposed_value - baseline_value
    for field_name in (
        "positive_periods",
        "negative_periods",
        "zero_periods",
    ):
        delta_value = getattr(impact, f"{field_name}_delta")
        assert delta_value == (
            getattr(proposed, field_name) - getattr(baseline, field_name)
        )
        assert isinstance(delta_value, int)
    assert impact.max_drawdown_delta == (
        proposed.worst_drawdown.max_drawdown
        - baseline.worst_drawdown.max_drawdown
    )

    assert tuple(
        row.component_id for row in result.component_contribution_impacts
    ) == source.component_ids
    for baseline_row, proposed_row, impact_row in zip(
        baseline.component_contributions,
        proposed.component_contributions,
        result.component_contribution_impacts,
        strict=True,
    ):
        assert impact_row.strategy_id == baseline_row.strategy_id
        assert impact_row.baseline_weight == baseline_row.weight
        assert impact_row.proposed_weight == proposed_row.weight
        assert impact_row.total_contribution_delta == (
            proposed_row.total_contribution - baseline_row.total_contribution
        )
        assert impact_row.mean_contribution_delta == (
            proposed_row.mean_contribution - baseline_row.mean_contribution
        )
        assert impact_row.positive_periods_delta == (
            proposed_row.positive_periods - baseline_row.positive_periods
        )
        assert impact_row.negative_periods_delta == (
            proposed_row.negative_periods - baseline_row.negative_periods
        )
        assert impact_row.zero_periods_delta == (
            proposed_row.zero_periods - baseline_row.zero_periods
        )

    unchanged = result.component_contribution_impacts[1]
    assert unchanged.baseline_weight == unchanged.proposed_weight
    assert unchanged.total_contribution_delta == 0.0
    assert unchanged.mean_contribution_delta == 0.0


def test_annualized_impact_is_none_when_source_has_no_annualization() -> None:
    _, _, result = _analysis(
        returns=((0.01, 0.02, -0.01), (0.02, -0.01, 0.03)),
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.5, 0.5),
        periods_per_year=None,
    )
    assert result.baseline_behavior.annualized_volatility is None
    assert result.proposed_behavior.annualized_volatility is None
    assert result.proposed_impact.annualized_volatility_delta is None


def test_results_are_constructor_protected_frozen_and_json_compatible() -> None:
    source, pair, result = _analysis(
        returns=((0.01, 0.02, -0.01), (0.02, -0.01, 0.03)),
        symbols=(("SYN-A",), None),
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.5, 0.5),
    )
    source_before = source.to_dict()
    pair_before = pair.to_dict()
    payload = result.to_dict()

    assert json.loads(json.dumps(payload, allow_nan=False)) == payload
    assert source.to_dict() == source_before
    assert pair.to_dict() == pair_before
    with pytest.raises(FrozenInstanceError):
        result.source_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.baseline_behavior.mean_return = 9.0  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.symbol_overlaps[0].status = "available"  # type: ignore[misc]

    derived_types = (
        PortfolioReviewSymbolOverlap,
        PortfolioReviewPairwiseCorrelation,
        PortfolioReviewCandidateBaselineCorrelation,
        PortfolioReviewWorstDrawdown,
        PortfolioReviewComponentContribution,
        PortfolioReviewScenarioBehavior,
        PortfolioReviewProposedImpact,
        PortfolioReviewComponentContributionImpact,
        PortfolioReviewInteractionImpactAnalysis,
    )
    for result_type in derived_types:
        with pytest.raises(TypeError, match="created by analyze"):
            result_type()  # type: ignore[call-arg]

    parameters = inspect.signature(
        analyze_portfolio_review_interaction_and_impact
    ).parameters
    assert tuple(parameters) == ("source", "scenario_pair")
    with pytest.raises(TypeError):
        analyze_portfolio_review_interaction_and_impact(
            source=source,
            scenario_pair=pair,
            correlation=0.0,  # type: ignore[call-arg]
        )


def test_analysis_rejects_wrong_types_and_cross_source_authority() -> None:
    source = _source(
        returns=((0.01, 0.02, 0.03), (0.02, 0.01, 0.04)),
    )
    pair = _pair(
        source=source,
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.5, 0.5),
    )
    with pytest.raises(ValueError, match="PortfolioReviewSource"):
        analyze_portfolio_review_interaction_and_impact(
            source=object(),  # type: ignore[arg-type]
            scenario_pair=pair,
        )
    with pytest.raises(ValueError, match="PortfolioReviewScenarioPair"):
        analyze_portfolio_review_interaction_and_impact(
            source=source,
            scenario_pair=object(),  # type: ignore[arg-type]
        )

    different_id_source = _source(
        source_id="different-source",
        returns=((0.01, 0.02, 0.03), (0.02, 0.01, 0.04)),
    )
    different_id_pair = _pair(
        source=different_id_source,
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.5, 0.5),
    )
    with pytest.raises(ValueError, match="exact source ID and digest"):
        analyze_portfolio_review_interaction_and_impact(
            source=source,
            scenario_pair=different_id_pair,
        )

    different_digest_source = _source(
        returns=((0.011, 0.02, 0.03), (0.02, 0.01, 0.04)),
    )
    different_digest_pair = _pair(
        source=different_digest_source,
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.5, 0.5),
    )
    with pytest.raises(ValueError, match="exact source ID and digest"):
        analyze_portfolio_review_interaction_and_impact(
            source=source,
            scenario_pair=different_digest_pair,
        )


def test_analysis_rejects_reordered_component_authority() -> None:
    source = _source(
        returns=((0.01, 0.02, 0.03), (0.02, 0.01, 0.04)),
    )
    reversed_ids = tuple(reversed(source.component_ids))
    baseline = PortfolioReviewBaselineScenario(
        scenario_id="reordered-baseline",
        source_id=source.source_id,
        source_digest=source.source_digest,
        component_weights=((reversed_ids[0], 0.0), (reversed_ids[1], 1.0)),
        rationale="Synthetic reordered baseline",
    )
    proposed = PortfolioReviewProposedScenario(
        scenario_id="reordered-proposed",
        source_id=source.source_id,
        source_digest=source.source_digest,
        component_weights=((reversed_ids[0], 0.5), (reversed_ids[1], 0.5)),
        proposed_component_id=reversed_ids[0],
        rationale="Synthetic reordered proposal",
    )
    reordered_pair = PortfolioReviewScenarioPair(
        source_id=source.source_id,
        source_digest=source.source_digest,
        component_ids=reversed_ids,
        baseline=baseline,
        proposed=proposed,
    )
    with pytest.raises(ValueError, match="ordered source component set"):
        analyze_portfolio_review_interaction_and_impact(
            source=source,
            scenario_pair=reordered_pair,
        )


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value).union(
            *(_all_keys(item) for item in value.values()),
            set(),
        )
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def test_payload_preserves_explicit_sprint_boundaries_and_neutrality() -> None:
    _, _, result = _analysis(
        returns=((0.01, 0.02, -0.01), (0.02, -0.01, 0.03)),
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.5, 0.5),
    )
    keys = _all_keys(result.to_dict())
    forbidden_fields = {
        "analysis_id",
        "analysis_digest",
        "review_id",
        "decision_id",
        "creator",
        "created_timestamp",
        "artifact_path",
        "covariance",
        "p_value",
        "significance",
        "rank",
        "score",
        "recommendation",
        "improved",
        "worsened",
        "better",
        "forecast",
        "expected_alpha",
        "account_id",
        "cash",
        "position",
        "order",
        "fill",
        "broker",
        "qmt",
        "live",
        "portfolio_returns",
        "equity_curve",
        "union_symbols",
        "weighted_overlap",
    }
    assert forbidden_fields.isdisjoint(keys)


def test_repeated_identical_inputs_produce_identical_exports() -> None:
    source_a = _source(
        returns=((0.01, 0.02, -0.01), (0.02, -0.01, 0.03)),
        symbols=(("SYN-A", "SYN-B"), ("SYN-B",)),
    )
    source_b = _source(
        returns=((0.01, 0.02, -0.01), (0.02, -0.01, 0.03)),
        symbols=(("SYN-A", "SYN-B"), ("SYN-B",)),
    )
    pair_a = _pair(
        source=source_a,
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.5, 0.5),
    )
    pair_b = _pair(
        source=source_b,
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.5, 0.5),
    )

    result_a = analyze_portfolio_review_interaction_and_impact(
        source=source_a,
        scenario_pair=pair_a,
    )
    result_b = analyze_portfolio_review_interaction_and_impact(
        source=source_b,
        scenario_pair=pair_b,
    )
    assert result_a.to_dict() == result_b.to_dict()
