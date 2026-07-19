import inspect
import json
import math
from dataclasses import FrozenInstanceError

import pandas as pd
import pytest

from el_psy_quant.portfolio_review import (
    PortfolioReviewBaselineScenario,
    PortfolioReviewComponentExposure,
    PortfolioReviewConcentrationExposureAnalysis,
    PortfolioReviewProposedScenario,
    PortfolioReviewScenarioConcentration,
    PortfolioReviewScenarioPair,
    PortfolioReviewScenarioUniverseCoverage,
    SUPPORTED_PORTFOLIO_REVIEW_SYMBOL_EVIDENCE_STATUSES,
    SUPPORTED_PORTFOLIO_REVIEW_WEIGHT_CHANGE_TYPES,
    analyze_portfolio_review_concentration_and_exposure,
    create_portfolio_review_baseline_scenario,
    create_portfolio_review_component,
    create_portfolio_review_evidence_reference,
    create_portfolio_review_proposed_scenario,
    create_portfolio_review_scenario_pair,
    create_portfolio_review_source,
)


def _source(
    *,
    component_symbols: tuple[tuple[str, ...] | None, ...],
    source_id: str = "synthetic-source",
    return_offset: float = 0.0,
):
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
            symbols=symbols,
        )
        for index, symbols in enumerate(component_symbols, start=1)
    )
    aligned_returns = pd.DataFrame(
        {
            component.component_id: [
                return_offset + (index * 0.001),
                return_offset - (index * 0.002),
                return_offset + (index * 0.003),
            ]
            for index, component in enumerate(components, start=1)
        },
        index=pd.date_range("2025-06-01", periods=3, freq="D"),
    )
    return create_portfolio_review_source(
        source_id=source_id,
        components=components,
        aligned_returns=aligned_returns,
        evaluation_frequency="daily",
        periods_per_year=252,
        created_by="synthetic-founder",
        created_timestamp="2025-06-04T00:00:00Z",
        assumptions=("Synthetic review inputs",),
        warnings=("Scenario weights are not holdings",),
    )


def _scenario_pair(
    *,
    source,
    baseline_weights: tuple[float, ...],
    proposed_weights: tuple[float, ...],
    proposed_component_index: int = 0,
):
    baseline = create_portfolio_review_baseline_scenario(
        scenario_id="synthetic-baseline",
        source=source,
        weights=dict(zip(source.component_ids, baseline_weights, strict=True)),
        rationale="Synthetic baseline",
    )
    proposed = create_portfolio_review_proposed_scenario(
        scenario_id="synthetic-proposed",
        source=source,
        weights=dict(zip(source.component_ids, proposed_weights, strict=True)),
        proposed_component_id=source.component_ids[proposed_component_index],
        rationale="Synthetic proposal",
    )
    return create_portfolio_review_scenario_pair(
        source=source,
        baseline=baseline,
        proposed=proposed,
    )


@pytest.mark.parametrize(
    ("baseline_weights", "proposed_weights", "expected_top_3"),
    [
        ((0.6, 0.4), (0.5, 0.5), 1.0),
        ((0.5, 0.3, 0.2), (0.4, 0.35, 0.25), 1.0),
        ((0.4, 0.3, 0.2, 0.1), (0.35, 0.3, 0.2, 0.15), 0.9),
        (
            (0.2, 0.18, 0.16, 0.1, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.02, 0.01),
            (0.19, 0.19, 0.16, 0.1, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.02, 0.01),
            math.fsum((0.2, 0.18, 0.16)),
        ),
    ],
)
def test_concentration_top_three_and_exact_formulas(
    baseline_weights: tuple[float, ...],
    proposed_weights: tuple[float, ...],
    expected_top_3: float,
) -> None:
    source = _source(component_symbols=(("SYN",),) * len(baseline_weights))
    pair = _scenario_pair(
        source=source,
        baseline_weights=baseline_weights,
        proposed_weights=proposed_weights,
    )

    analysis = analyze_portfolio_review_concentration_and_exposure(
        source=source,
        scenario_pair=pair,
    )
    concentration = analysis.baseline_concentration

    expected_hhi = math.fsum(weight * weight for weight in baseline_weights)
    assert concentration.top_3_weight == expected_top_3
    assert concentration.herfindahl_hirschman_index == expected_hhi
    assert concentration.effective_component_count == 1.0 / expected_hhi


def test_concentration_ties_zero_weights_equal_weights_and_identities() -> None:
    source = _source(
        component_symbols=(("SYN-A",), ("SYN-B",), ("SYN-C",), ("SYN-D",))
    )
    pair = _scenario_pair(
        source=source,
        baseline_weights=(0.25, 0.25, 0.25, 0.25),
        proposed_weights=(1.0, 0.0, 0.0, 0.0),
        proposed_component_index=0,
    )

    analysis = analyze_portfolio_review_concentration_and_exposure(
        source=source,
        scenario_pair=pair,
    )

    baseline = analysis.baseline_concentration
    proposed = analysis.proposed_concentration
    assert baseline.largest_component_id == "component-1"
    assert baseline.largest_component_weight == 0.25
    assert baseline.herfindahl_hirschman_index == 0.25
    assert baseline.effective_component_count == 4.0
    assert proposed.largest_component_id == "component-1"
    assert proposed.herfindahl_hirschman_index == 1.0
    assert proposed.effective_component_count == 1.0
    assert proposed.scenario_id == pair.proposed.scenario_id
    assert proposed.scenario_digest == pair.proposed.scenario_digest
    assert baseline.scenario_id == pair.baseline.scenario_id
    assert baseline.scenario_digest == pair.baseline.scenario_digest


def test_concentration_applies_no_rounding_clamping_or_reordering() -> None:
    baseline_weights = (
        0.33333333333333337,
        0.3333333333333333,
        0.3333333333333333,
    )
    proposed_weights = (
        0.3333333333333333,
        0.33333333333333337,
        0.3333333333333333,
    )
    source = _source(component_symbols=(("SYN-A",), ("SYN-B",), ("SYN-C",)))
    pair = _scenario_pair(
        source=source,
        baseline_weights=baseline_weights,
        proposed_weights=proposed_weights,
        proposed_component_index=0,
    )

    result = analyze_portfolio_review_concentration_and_exposure(
        source=source,
        scenario_pair=pair,
    ).baseline_concentration

    assert result.largest_component_id == "component-1"
    assert result.largest_component_weight == baseline_weights[0]
    assert result.top_3_weight == math.fsum(baseline_weights)
    assert result.herfindahl_hirschman_index == math.fsum(
        weight * weight for weight in baseline_weights
    )
    assert result.herfindahl_hirschman_index != round(
        result.herfindahl_hirschman_index,
        6,
    )


def test_all_exact_weight_changes_and_declared_symbol_evidence() -> None:
    source = _source(
        component_symbols=(
            ("SYN-A", "SYN-DUP"),
            None,
            ("SYN-DUP",),
            ("SYN-D",),
            ("SYN-E",),
        )
    )
    pair = _scenario_pair(
        source=source,
        baseline_weights=(0.0, 0.2, 0.2, 0.3, 0.3),
        proposed_weights=(0.1, 0.0, 0.4, 0.2, 0.3),
        proposed_component_index=0,
    )
    source_before = source.to_dict()
    pair_before = pair.to_dict()

    analysis = analyze_portfolio_review_concentration_and_exposure(
        source=source,
        scenario_pair=pair,
    )
    exposures = analysis.component_exposures

    assert tuple(item.component_id for item in exposures) == source.component_ids
    assert tuple(item.change_type for item in exposures) == (
        "added",
        "removed",
        "increased",
        "decreased",
        "unchanged",
    )
    assert tuple(item.weight_delta for item in exposures) == (
        0.1,
        -0.2,
        0.2,
        -0.09999999999999998,
        0.0,
    )
    assert tuple(item.baseline_active for item in exposures) == (
        False,
        True,
        True,
        True,
        True,
    )
    assert tuple(item.proposed_active for item in exposures) == (
        True,
        False,
        True,
        True,
        True,
    )
    assert tuple(item.strategy_id for item in exposures) == tuple(
        component.strategy_id for component in source.components
    )
    assert exposures[0].symbols == ("SYN-A", "SYN-DUP")
    assert exposures[1].symbols is None
    assert exposures[2].symbols == ("SYN-DUP",)
    assert tuple(item.symbol_evidence_status for item in exposures) == (
        "available",
        "missing",
        "available",
        "available",
        "available",
    )
    assert source.to_dict() == source_before
    assert pair.to_dict() == pair_before
    assert SUPPORTED_PORTFOLIO_REVIEW_WEIGHT_CHANGE_TYPES == (
        "added",
        "removed",
        "increased",
        "decreased",
        "unchanged",
    )
    assert SUPPORTED_PORTFOLIO_REVIEW_SYMBOL_EVIDENCE_STATUSES == (
        "available",
        "missing",
    )


def test_universe_coverage_distinguishes_source_and_active_evidence() -> None:
    source = _source(
        component_symbols=(
            ("SYN-A", "SYN-DUP"),
            None,
            ("SYN-DUP",),
            ("SYN-D",),
            ("SYN-E",),
        )
    )
    pair = _scenario_pair(
        source=source,
        baseline_weights=(0.0, 0.2, 0.2, 0.3, 0.3),
        proposed_weights=(0.1, 0.0, 0.4, 0.2, 0.3),
        proposed_component_index=0,
    )

    analysis = analyze_portfolio_review_concentration_and_exposure(
        source=source,
        scenario_pair=pair,
    )
    baseline = analysis.baseline_universe_coverage
    proposed = analysis.proposed_universe_coverage

    assert baseline.components_with_symbol_evidence == (
        "component-1",
        "component-3",
        "component-4",
        "component-5",
    )
    assert baseline.components_missing_symbol_evidence == ("component-2",)
    assert baseline.active_component_ids == (
        "component-2",
        "component-3",
        "component-4",
        "component-5",
    )
    assert baseline.active_components_with_symbol_evidence == (
        "component-3",
        "component-4",
        "component-5",
    )
    assert baseline.active_components_missing_symbol_evidence == (
        "component-2",
    )
    assert baseline.source_component_count == 5
    assert baseline.components_with_symbol_evidence_count == 4
    assert baseline.components_missing_symbol_evidence_count == 1
    assert baseline.active_component_count == 4
    assert baseline.active_components_with_symbol_evidence_count == 3
    assert baseline.active_components_missing_symbol_evidence_count == 1
    assert baseline.active_coverage_complete is False
    assert proposed.active_component_ids == (
        "component-1",
        "component-3",
        "component-4",
        "component-5",
    )
    assert proposed.active_components_missing_symbol_evidence == ()
    assert proposed.active_components_with_symbol_evidence_count == 4
    assert proposed.active_components_missing_symbol_evidence_count == 0
    assert proposed.active_coverage_complete is True

    payload = analysis.to_dict()
    assert "SYN-DUP" in payload["component_exposures"][0]["symbols"]
    assert "SYN-DUP" in payload["component_exposures"][2]["symbols"]
    forbidden = {
        "shared_symbols",
        "union_symbols",
        "jaccard_overlap",
        "correlation",
        "weighted_symbol_exposure",
    }
    assert forbidden.isdisjoint(payload)
    assert all(
        forbidden.isdisjoint(exposure)
        for exposure in payload["component_exposures"]
    )


def test_results_are_immutable_constructor_protected_and_json_compatible() -> None:
    source = _source(component_symbols=(("SYN-A",), None))
    pair = _scenario_pair(
        source=source,
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.75, 0.25),
    )
    analysis = analyze_portfolio_review_concentration_and_exposure(
        source=source,
        scenario_pair=pair,
    )

    assert (
        json.loads(json.dumps(analysis.to_dict(), allow_nan=False))
        == analysis.to_dict()
    )
    with pytest.raises(FrozenInstanceError):
        analysis.source_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        analysis.component_exposures[0].weight_delta = 9.0  # type: ignore[misc]
    for result_type in (
        PortfolioReviewScenarioConcentration,
        PortfolioReviewComponentExposure,
        PortfolioReviewScenarioUniverseCoverage,
        PortfolioReviewConcentrationExposureAnalysis,
    ):
        with pytest.raises(TypeError, match="created by analyze"):
            result_type()  # type: ignore[call-arg]

    parameters = inspect.signature(
        analyze_portfolio_review_concentration_and_exposure
    ).parameters
    assert tuple(parameters) == ("source", "scenario_pair")
    with pytest.raises(TypeError):
        analyze_portfolio_review_concentration_and_exposure(
            source=source,
            scenario_pair=pair,
            herfindahl_hirschman_index=0.0,  # type: ignore[call-arg]
        )


def test_analysis_rejects_wrong_types_and_cross_source_authority() -> None:
    source = _source(component_symbols=(("SYN-A",), ("SYN-B",)))
    pair = _scenario_pair(
        source=source,
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.75, 0.25),
    )

    with pytest.raises(ValueError, match="PortfolioReviewSource"):
        analyze_portfolio_review_concentration_and_exposure(
            source=object(),  # type: ignore[arg-type]
            scenario_pair=pair,
        )
    with pytest.raises(ValueError, match="PortfolioReviewScenarioPair"):
        analyze_portfolio_review_concentration_and_exposure(
            source=source,
            scenario_pair=object(),  # type: ignore[arg-type]
        )

    different_id_source = _source(
        component_symbols=(("SYN-A",), ("SYN-B",)),
        source_id="different-source",
    )
    different_id_pair = _scenario_pair(
        source=different_id_source,
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.75, 0.25),
    )
    with pytest.raises(ValueError, match="exact source ID and digest"):
        analyze_portfolio_review_concentration_and_exposure(
            source=source,
            scenario_pair=different_id_pair,
        )

    different_digest_source = _source(
        component_symbols=(("SYN-A",), ("SYN-B",)),
        return_offset=0.01,
    )
    different_digest_pair = _scenario_pair(
        source=different_digest_source,
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.75, 0.25),
    )
    with pytest.raises(ValueError, match="exact source ID and digest"):
        analyze_portfolio_review_concentration_and_exposure(
            source=source,
            scenario_pair=different_digest_pair,
        )


def test_analysis_rejects_reordered_pair_against_source() -> None:
    source = _source(component_symbols=(("SYN-A",), ("SYN-B",)))
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
        component_weights=((reversed_ids[0], 0.25), (reversed_ids[1], 0.75)),
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
        analyze_portfolio_review_concentration_and_exposure(
            source=source,
            scenario_pair=reordered_pair,
        )


def test_weight_changes_are_material_but_returns_add_no_sprint_171_metric() -> None:
    source = _source(component_symbols=(("SYN-A",), ("SYN-B",)))
    changed_returns_source = _source(
        component_symbols=(("SYN-A",), ("SYN-B",)),
        return_offset=0.02,
    )
    pair = _scenario_pair(
        source=source,
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.75, 0.25),
    )
    changed_returns_pair = _scenario_pair(
        source=changed_returns_source,
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.75, 0.25),
    )
    changed_weights_pair = _scenario_pair(
        source=source,
        baseline_weights=(0.8, 0.2),
        proposed_weights=(0.5, 0.5),
    )

    result = analyze_portfolio_review_concentration_and_exposure(
        source=source,
        scenario_pair=pair,
    )
    changed_returns_result = (
        analyze_portfolio_review_concentration_and_exposure(
            source=changed_returns_source,
            scenario_pair=changed_returns_pair,
        )
    )
    changed_weights_result = (
        analyze_portfolio_review_concentration_and_exposure(
            source=source,
            scenario_pair=changed_weights_pair,
        )
    )

    assert result.source_digest != changed_returns_result.source_digest
    assert (
        result.baseline_concentration.herfindahl_hirschman_index
        == changed_returns_result.baseline_concentration.herfindahl_hirschman_index
    )
    assert result.component_exposures == changed_returns_result.component_exposures
    assert (
        result.baseline_concentration.herfindahl_hirschman_index
        != changed_weights_result.baseline_concentration.herfindahl_hirschman_index
    )
    payload_text = json.dumps(result.to_dict(), allow_nan=False)
    assert "return" not in payload_text
    for forbidden_term in (
        "correlation",
        "covariance",
        "drawdown",
        "volatility",
        "performance",
        "contribution",
        "attribution",
        "impact",
    ):
        assert forbidden_term not in payload_text


def test_repeated_identical_inputs_produce_identical_exports() -> None:
    source_a = _source(component_symbols=(("SYN-A",), None))
    source_b = _source(component_symbols=(("SYN-A",), None))
    pair_a = _scenario_pair(
        source=source_a,
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.75, 0.25),
    )
    pair_b = _scenario_pair(
        source=source_b,
        baseline_weights=(1.0, 0.0),
        proposed_weights=(0.75, 0.25),
    )

    result_a = analyze_portfolio_review_concentration_and_exposure(
        source=source_a,
        scenario_pair=pair_a,
    )
    result_b = analyze_portfolio_review_concentration_and_exposure(
        source=source_b,
        scenario_pair=pair_b,
    )

    assert result_a.to_dict() == result_b.to_dict()
