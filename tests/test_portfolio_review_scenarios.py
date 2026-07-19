import json
from dataclasses import FrozenInstanceError

import pandas as pd
import pytest

from el_psy_quant.portfolio_review import (
    PortfolioReviewBaselineScenario,
    create_portfolio_review_baseline_scenario,
    create_portfolio_review_component,
    create_portfolio_review_evidence_reference,
    create_portfolio_review_proposed_scenario,
    create_portfolio_review_scenario_pair,
    create_portfolio_review_source,
)


def _source(source_id: str = "source-1"):
    evidence_a = create_portfolio_review_evidence_reference(
        reference_type="research_run",
        reference_id="run-a",
    )
    evidence_b = create_portfolio_review_evidence_reference(
        reference_type="configured_run",
        reference_id="run-b",
    )
    components = (
        create_portfolio_review_component(
            component_id="component-a",
            strategy_id="strategy-a",
            evidence_references=(evidence_a,),
        ),
        create_portfolio_review_component(
            component_id="component-b",
            strategy_id="strategy-b",
            evidence_references=(evidence_b,),
        ),
    )
    return create_portfolio_review_source(
        source_id=source_id,
        components=components,
        aligned_returns=pd.DataFrame(
            {
                "component-a": [0.01, -0.01, 0.02],
                "component-b": [0.0, 0.01, 0.01],
            },
            index=pd.date_range("2025-01-01", periods=3, freq="D"),
        ),
        evaluation_frequency="daily",
        periods_per_year=252,
        created_by="founder",
        created_timestamp="2025-01-04T00:00:00Z",
    )


def _scenarios(
    *,
    source=None,
    baseline_id: str = "baseline-1",
    proposed_id: str = "proposed-1",
    baseline_weights=None,
    proposed_weights=None,
    proposed_component_id: str = "component-b",
):
    review_source = _source() if source is None else source
    baseline = create_portfolio_review_baseline_scenario(
        scenario_id=baseline_id,
        source=review_source,
        weights=(
            {"component-a": 1.0, "component-b": 0.0}
            if baseline_weights is None
            else baseline_weights
        ),
        rationale="Baseline review assumption",
        assumptions=("Static weights",),
        warnings=("Not account holdings",),
    )
    proposed = create_portfolio_review_proposed_scenario(
        scenario_id=proposed_id,
        source=review_source,
        weights=(
            {"component-a": 0.75, "component-b": 0.25}
            if proposed_weights is None
            else proposed_weights
        ),
        proposed_component_id=proposed_component_id,
        rationale="Proposed review assumption",
        assumptions=("Static weights",),
        warnings=("Not capital allocation",),
    )
    return review_source, baseline, proposed


def test_valid_pair_preserves_source_order_zero_weight_and_caller_inputs() -> None:
    source = _source()
    baseline_weights = {"component-b": 0.0, "component-a": 1.0}
    proposed_weights = {"component-b": 0.25, "component-a": 0.75}
    baseline_snapshot = baseline_weights.copy()
    proposed_snapshot = proposed_weights.copy()
    _, baseline, proposed = _scenarios(
        source=source,
        baseline_weights=baseline_weights,
        proposed_weights=proposed_weights,
    )

    pair = create_portfolio_review_scenario_pair(
        source=source,
        baseline=baseline,
        proposed=proposed,
    )

    assert baseline.component_weights == (
        ("component-a", 1.0),
        ("component-b", 0.0),
    )
    assert proposed.component_weights == (
        ("component-a", 0.75),
        ("component-b", 0.25),
    )
    assert pair.component_ids == source.component_ids
    assert baseline_weights == baseline_snapshot
    assert proposed_weights == proposed_snapshot
    assert json.loads(json.dumps(pair.to_dict(), allow_nan=False)) == pair.to_dict()
    assert len(baseline.scenario_digest) == 64
    assert len(proposed.scenario_digest) == 64
    with pytest.raises(FrozenInstanceError):
        baseline.scenario_id = "other"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("baseline_weights", "proposed_weights", "proposed_component_id"),
    [
        (
            {"component-a": 0.75, "component-b": 0.25},
            {"component-a": 0.5, "component-b": 0.5},
            "component-b",
        ),
        (
            {"component-a": 0.5, "component-b": 0.5},
            {"component-a": 0.75, "component-b": 0.25},
            "component-b",
        ),
        (
            {"component-a": 1.0, "component-b": 0.0},
            {"component-a": 0.75, "component-b": 0.25},
            "component-b",
        ),
        (
            {"component-a": 0.75, "component-b": 0.25},
            {"component-a": 1.0, "component-b": 0.0},
            "component-b",
        ),
    ],
)
def test_proposed_component_may_increase_decrease_be_added_or_removed(
    baseline_weights,
    proposed_weights,
    proposed_component_id: str,
) -> None:
    source, baseline, proposed = _scenarios(
        baseline_weights=baseline_weights,
        proposed_weights=proposed_weights,
        proposed_component_id=proposed_component_id,
    )

    pair = create_portfolio_review_scenario_pair(
        source=source,
        baseline=baseline,
        proposed=proposed,
    )

    assert pair.proposed.proposed_component_id == proposed_component_id


def test_scenario_digests_are_deterministic_and_material() -> None:
    source, baseline, proposed = _scenarios()
    _, same_baseline, same_proposed = _scenarios(source=source)
    changed_rationale = create_portfolio_review_baseline_scenario(
        scenario_id="baseline-1",
        source=source,
        weights={"component-a": 1.0, "component-b": 0.0},
        rationale="Different rationale",
        assumptions=("Static weights",),
        warnings=("Not account holdings",),
    )
    changed_weights = create_portfolio_review_proposed_scenario(
        scenario_id="proposed-1",
        source=source,
        weights={"component-a": 0.5, "component-b": 0.5},
        proposed_component_id="component-b",
        rationale="Proposed review assumption",
        assumptions=("Static weights",),
        warnings=("Not capital allocation",),
    )

    assert baseline.scenario_digest == same_baseline.scenario_digest
    assert proposed.scenario_digest == same_proposed.scenario_digest
    assert baseline.scenario_digest != changed_rationale.scenario_digest
    assert proposed.scenario_digest != changed_weights.scenario_digest


@pytest.mark.parametrize(
    ("weights", "message"),
    [
        ({"component-a": 1.0}, "missing"),
        (
            {"component-a": 1.0, "component-b": 0.0, "extra": 0.0},
            "unknown",
        ),
        ({"component-a": True, "component-b": 0.0}, "numeric"),
        ({"component-a": "1", "component-b": 0.0}, "numeric"),
        ({"component-a": 1.1, "component-b": -0.1}, "non-negative"),
        ({"component-a": float("nan"), "component-b": 0.0}, "missing"),
        ({"component-a": float("inf"), "component-b": 0.0}, "finite"),
        ({"component-a": 0.4, "component-b": 0.4}, "sum to 1.0"),
    ],
)
def test_scenario_rejects_invalid_weights(weights, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        create_portfolio_review_baseline_scenario(
            scenario_id="baseline-1",
            source=_source(),
            weights=weights,
            rationale="Baseline",
        )


def test_pair_rejects_matching_scenario_ids() -> None:
    source, baseline, proposed = _scenarios(proposed_id="baseline-1")

    with pytest.raises(ValueError, match="IDs must be distinct"):
        create_portfolio_review_scenario_pair(
            source=source,
            baseline=baseline,
            proposed=proposed,
        )


def test_pair_rejects_source_identity_mismatch() -> None:
    source, baseline, _ = _scenarios()
    other_source, _, other_proposed = _scenarios(source=_source("source-2"))

    with pytest.raises(ValueError, match="exact source ID and digest"):
        create_portfolio_review_scenario_pair(
            source=source,
            baseline=baseline,
            proposed=other_proposed,
        )
    assert other_source.source_id == "source-2"


def test_pair_rejects_identical_weights_even_when_rationale_changes() -> None:
    source = _source()
    baseline = create_portfolio_review_baseline_scenario(
        scenario_id="baseline-1",
        source=source,
        weights={"component-a": 0.5, "component-b": 0.5},
        rationale="Baseline",
    )
    proposed = create_portfolio_review_proposed_scenario(
        scenario_id="proposed-1",
        source=source,
        weights={"component-a": 0.5, "component-b": 0.5},
        proposed_component_id="component-b",
        rationale="Different rationale",
    )

    with pytest.raises(ValueError, match="must differ"):
        create_portfolio_review_scenario_pair(
            source=source,
            baseline=baseline,
            proposed=proposed,
        )


def test_proposed_scenario_rejects_unknown_component() -> None:
    with pytest.raises(ValueError, match="source component"):
        create_portfolio_review_proposed_scenario(
            scenario_id="proposed-1",
            source=_source(),
            weights={"component-a": 0.75, "component-b": 0.25},
            proposed_component_id="unknown",
            rationale="Proposed",
        )


def test_pair_rejects_unchanged_proposed_component_weight() -> None:
    evidence = create_portfolio_review_evidence_reference(
        reference_type="backtest_artifact",
        reference_id="run-c",
    )
    components = (
        *_source().components,
        create_portfolio_review_component(
            component_id="component-c",
            strategy_id="strategy-c",
            evidence_references=(evidence,),
        ),
    )
    source = create_portfolio_review_source(
        source_id="source-3",
        components=components,
        aligned_returns=pd.DataFrame(
            {
                "component-a": [0.01, -0.01, 0.02],
                "component-b": [0.0, 0.01, 0.01],
                "component-c": [0.02, 0.0, -0.01],
            },
            index=pd.date_range("2025-01-01", periods=3, freq="D"),
        ),
        evaluation_frequency="daily",
        created_by="founder",
        created_timestamp="2025-01-04T00:00:00Z",
    )
    baseline = create_portfolio_review_baseline_scenario(
        scenario_id="baseline-1",
        source=source,
        weights={
            "component-a": 0.5,
            "component-b": 0.25,
            "component-c": 0.25,
        },
        rationale="Baseline",
    )
    proposed = create_portfolio_review_proposed_scenario(
        scenario_id="proposed-1",
        source=source,
        weights={
            "component-a": 0.5,
            "component-b": 0.4,
            "component-c": 0.1,
        },
        proposed_component_id="component-a",
        rationale="Proposed",
    )

    with pytest.raises(ValueError, match="proposed component weight"):
        create_portfolio_review_scenario_pair(
            source=source,
            baseline=baseline,
            proposed=proposed,
        )


def test_pair_rejects_reordered_complete_component_set() -> None:
    source, _, proposed = _scenarios()
    reordered_baseline = PortfolioReviewBaselineScenario(
        scenario_id="baseline-1",
        source_id=source.source_id,
        source_digest=source.source_digest,
        component_weights=(
            ("component-b", 0.0),
            ("component-a", 1.0),
        ),
        rationale="Baseline",
    )

    with pytest.raises(ValueError, match="ordered source component set"):
        create_portfolio_review_scenario_pair(
            source=source,
            baseline=reordered_baseline,
            proposed=proposed,
        )
