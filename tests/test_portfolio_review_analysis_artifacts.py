import hashlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass

import pandas as pd
import pytest

from el_psy_quant.portfolio_review import (
    PORTFOLIO_REVIEW_ANALYSIS_ARTIFACT_SCHEMA_VERSION,
    PORTFOLIO_REVIEW_ANALYSIS_EVIDENCE_SCOPE,
    PortfolioReviewAnalysisArtifact,
    PortfolioReviewBaselineScenario,
    PortfolioReviewProposedScenario,
    PortfolioReviewScenarioPair,
    analyze_portfolio_review_concentration_and_exposure,
    analyze_portfolio_review_interaction_and_impact,
    create_portfolio_review_analysis_artifact,
    create_portfolio_review_baseline_scenario,
    create_portfolio_review_component,
    create_portfolio_review_evidence_reference,
    create_portfolio_review_proposed_scenario,
    create_portfolio_review_scenario_pair,
    create_portfolio_review_source,
)


def _review(
    *,
    component_count: int = 2,
    review_id: str = "synthetic-review",
    source_id: str = "synthetic-source",
    return_shift: float = 0.0,
    proposed_weight: float = 0.4,
    source_assumption: str = "Synthetic source assumption",
    baseline_rationale: str = "Synthetic baseline rationale",
    created_by: str = "synthetic-creator",
    created_timestamp: object = "2025-07-20T12:00:00Z",
    analysis_assumptions: tuple[str, ...] = (
        "Synthetic analysis assumption",
    ),
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
            symbols=(
                None
                if index == 2
                else (f"SYN-{index}", "SYN-SHARED")
            ),
        )
        for index in range(1, component_count + 1)
    )
    aligned_returns = pd.DataFrame(
        {
            component.component_id: (
                0.01 * index + (return_shift if index == 1 else 0.0),
                -0.005 * index,
                0.004 * (index + 1),
                0.002 * index,
            )
            for index, component in enumerate(components, start=1)
        },
        index=pd.date_range("2025-07-01", periods=4, freq="D"),
    )
    source = create_portfolio_review_source(
        source_id=source_id,
        components=components,
        aligned_returns=aligned_returns,
        evaluation_frequency="daily",
        periods_per_year=252.0,
        created_by="synthetic-source-creator",
        created_timestamp="2025-07-19T12:00:00Z",
        assumptions=(source_assumption,),
        warnings=("Synthetic source warning",),
        missing_evidence=("Synthetic source limitation",),
    )
    baseline_weights = {
        component_id: 1.0 if index == 0 else 0.0
        for index, component_id in enumerate(source.component_ids)
    }
    proposed_weights = {
        component_id: (
            1.0 - proposed_weight
            if index == 0
            else proposed_weight
            if index == 1
            else 0.0
        )
        for index, component_id in enumerate(source.component_ids)
    }
    baseline = create_portfolio_review_baseline_scenario(
        scenario_id="synthetic-baseline",
        source=source,
        weights=baseline_weights,
        rationale=baseline_rationale,
        assumptions=("Synthetic baseline assumption",),
        warnings=("Synthetic baseline warning",),
    )
    proposed = create_portfolio_review_proposed_scenario(
        scenario_id="synthetic-proposed",
        source=source,
        weights=proposed_weights,
        proposed_component_id=source.component_ids[1],
        rationale="Synthetic proposed rationale",
        assumptions=("Synthetic proposed assumption",),
        warnings=("Synthetic proposed warning",),
    )
    pair = create_portfolio_review_scenario_pair(
        source=source,
        baseline=baseline,
        proposed=proposed,
    )
    artifact = create_portfolio_review_analysis_artifact(
        review_id=review_id,
        source=source,
        scenario_pair=pair,
        created_by=created_by,
        created_timestamp=created_timestamp,
        assumptions=analysis_assumptions,
        warnings=("First warning", "First warning"),
        missing_evidence=("Missing symbols remain unavailable",),
    )
    return source, pair, artifact


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value).union(
            *(_all_keys(item) for item in value.values()),
            set(),
        )
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def _assert_no_mutable_pandas(value: object) -> None:
    assert not isinstance(value, (pd.DataFrame, pd.Series))
    if is_dataclass(value):
        for field in fields(value):
            _assert_no_mutable_pandas(getattr(value, field.name))
    elif isinstance(value, tuple):
        for item in value:
            _assert_no_mutable_pandas(item)


@pytest.mark.parametrize("component_count", [2, 12])
def test_analysis_composes_exact_s170_s172_authority(
    component_count: int,
) -> None:
    source, pair, artifact = _review(component_count=component_count)

    assert artifact.analysis_evidence_scope == (
        PORTFOLIO_REVIEW_ANALYSIS_EVIDENCE_SCOPE
    )
    assert artifact.analysis_evidence_scope == "historical_scenario_evidence"
    assert artifact.source_id == source.source_id
    assert artifact.source_digest == source.source_digest
    assert artifact.component_ids == source.component_ids
    assert artifact.baseline_scenario is pair.baseline
    assert artifact.proposed_scenario is pair.proposed
    assert artifact.baseline_scenario_id == pair.baseline.scenario_id
    assert artifact.baseline_scenario_digest == pair.baseline.scenario_digest
    assert artifact.proposed_scenario_id == pair.proposed.scenario_id
    assert artifact.proposed_scenario_digest == pair.proposed.scenario_digest
    assert artifact.proposed_component_id == (
        pair.proposed.proposed_component_id
    )
    assert artifact.concentration_exposure_analysis.to_dict() == (
        analyze_portfolio_review_concentration_and_exposure(
            source=source,
            scenario_pair=pair,
        ).to_dict()
    )
    assert artifact.interaction_impact_analysis.to_dict() == (
        analyze_portfolio_review_interaction_and_impact(
            source=source,
            scenario_pair=pair,
        ).to_dict()
    )
    assert tuple(
        row.component_id
        for row in artifact.concentration_exposure_analysis.component_exposures
    ) == source.component_ids


def test_analysis_preserves_unavailable_evidence_audit_order_and_source_separation() -> None:
    source, pair, artifact = _review(
        analysis_assumptions=("Second", "First", "Second"),
        created_timestamp="2025-07-20T20:00:00+08:00",
    )
    payload = artifact.to_dict()

    assert artifact.assumptions == ("Second", "First", "Second")
    assert artifact.warnings == ("First warning", "First warning")
    assert artifact.created_timestamp.isoformat() == "2025-07-20T12:00:00+00:00"
    assert payload["baseline_scenario"] == pair.baseline.to_dict()
    assert payload["proposed_scenario"] == pair.proposed.to_dict()
    overlap = artifact.interaction_impact_analysis.symbol_overlaps[0]
    assert overlap.status == "unavailable"
    assert overlap.shared_symbols is None
    assert artifact.interaction_impact_analysis.pairwise_correlations[0].correlation is not None
    keys = _all_keys(payload)
    assert "return_observations" not in keys
    assert "aligned_returns" not in keys
    assert source.return_observations
    _assert_no_mutable_pandas(artifact)


def test_analysis_export_digest_immutability_and_constructor_protection() -> None:
    source, pair, artifact = _review()
    source_before = source.to_dict()
    pair_before = pair.to_dict()
    payload = artifact.to_dict()

    assert payload["schema_version"] == (
        PORTFOLIO_REVIEW_ANALYSIS_ARTIFACT_SCHEMA_VERSION
    )
    assert json.loads(json.dumps(payload, allow_nan=False)) == payload
    assert len(artifact.analysis_digest) == 64
    assert set(artifact.analysis_digest) <= set("0123456789abcdef")
    without_digest = dict(payload)
    del without_digest["analysis_digest"]
    canonical = json.dumps(
        without_digest,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert artifact.analysis_digest == hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()
    assert sum(
        key == "analysis_digest" for key in payload
    ) == 1
    assert source.to_dict() == source_before
    assert pair.to_dict() == pair_before
    with pytest.raises(FrozenInstanceError):
        artifact.review_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        artifact.interaction_impact_analysis.source_id = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError, match="created by"):
        PortfolioReviewAnalysisArtifact()

    parameters = inspect.signature(
        create_portfolio_review_analysis_artifact
    ).parameters
    assert tuple(parameters) == (
        "review_id",
        "source",
        "scenario_pair",
        "created_by",
        "created_timestamp",
        "assumptions",
        "warnings",
        "missing_evidence",
    )
    with pytest.raises(TypeError):
        create_portfolio_review_analysis_artifact(
            review_id="synthetic-review",
            source=source,
            scenario_pair=pair,
            created_by="synthetic-creator",
            created_timestamp="2025-07-20T12:00:00Z",
            analysis_digest="0" * 64,  # type: ignore[call-arg]
        )


def test_analysis_digest_is_deterministic_and_normalizes_equivalent_instants() -> None:
    _, _, first = _review(
        created_timestamp="2025-07-20T12:00:00Z",
    )
    _, _, repeated = _review(
        created_timestamp="2025-07-20T12:00:00+00:00",
    )
    _, _, equivalent = _review(
        created_timestamp="2025-07-20T20:00:00+08:00",
    )

    assert first.to_dict() == repeated.to_dict() == equivalent.to_dict()


@pytest.mark.parametrize(
    "changes",
    [
        {"review_id": "changed-review"},
        {"source_id": "changed-source"},
        {"return_shift": 0.0001},
        {"proposed_weight": 0.3},
        {"source_assumption": "Changed source assumption"},
        {"baseline_rationale": "Changed baseline rationale"},
        {"created_by": "changed-creator"},
        {"created_timestamp": "2025-07-20T12:00:01Z"},
        {"analysis_assumptions": ("Changed analysis assumption",)},
    ],
)
def test_material_analysis_inputs_change_digest(
    changes: dict[str, object],
) -> None:
    _, _, baseline = _review()
    _, _, changed = _review(**changes)
    assert changed.analysis_digest != baseline.analysis_digest


@pytest.mark.parametrize("field_name", ["review_id", "created_by"])
def test_analysis_rejects_blank_required_audit_fields(field_name: str) -> None:
    source, pair, _ = _review()
    values = {
        "review_id": "synthetic-review",
        "created_by": "synthetic-creator",
    }
    values[field_name] = " "
    with pytest.raises(ValueError, match=field_name):
        create_portfolio_review_analysis_artifact(
            source=source,
            scenario_pair=pair,
            created_timestamp="2025-07-20T12:00:00Z",
            **values,
        )


@pytest.mark.parametrize(
    "timestamp",
    ["2025-07-20T12:00:00", "not-a-timestamp", None],
)
def test_analysis_rejects_naive_or_invalid_timestamp(timestamp: object) -> None:
    source, pair, _ = _review()
    with pytest.raises(ValueError, match="created_timestamp"):
        create_portfolio_review_analysis_artifact(
            review_id="synthetic-review",
            source=source,
            scenario_pair=pair,
            created_by="synthetic-creator",
            created_timestamp=timestamp,
        )


@pytest.mark.parametrize(
    ("field_name", "values"),
    [
        ("assumptions", ("valid", " ")),
        ("warnings", "not-a-sequence"),
        ("missing_evidence", ("",)),
    ],
)
def test_analysis_rejects_invalid_prose_sequences(
    field_name: str,
    values: object,
) -> None:
    source, pair, _ = _review()
    kwargs = {field_name: values}
    with pytest.raises(ValueError, match=field_name):
        create_portfolio_review_analysis_artifact(
            review_id="synthetic-review",
            source=source,
            scenario_pair=pair,
            created_by="synthetic-creator",
            created_timestamp="2025-07-20T12:00:00Z",
            **kwargs,
        )


def test_analysis_rejects_wrong_types_and_cross_source_authority() -> None:
    source, pair, _ = _review()
    other_source, other_pair, _ = _review(source_id="other-source")

    with pytest.raises(ValueError, match="PortfolioReviewSource"):
        create_portfolio_review_analysis_artifact(
            review_id="synthetic-review",
            source=object(),  # type: ignore[arg-type]
            scenario_pair=pair,
            created_by="synthetic-creator",
            created_timestamp="2025-07-20T12:00:00Z",
        )
    with pytest.raises(ValueError, match="PortfolioReviewScenarioPair"):
        create_portfolio_review_analysis_artifact(
            review_id="synthetic-review",
            source=source,
            scenario_pair=object(),  # type: ignore[arg-type]
            created_by="synthetic-creator",
            created_timestamp="2025-07-20T12:00:00Z",
        )
    with pytest.raises(ValueError, match="exact source ID and digest"):
        create_portfolio_review_analysis_artifact(
            review_id="synthetic-review",
            source=source,
            scenario_pair=other_pair,
            created_by="synthetic-creator",
            created_timestamp="2025-07-20T12:00:00Z",
        )
    assert other_source.source_digest != source.source_digest


def test_analysis_rejects_reordered_component_authority() -> None:
    source, _, _ = _review()
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
        create_portfolio_review_analysis_artifact(
            review_id="synthetic-review",
            source=source,
            scenario_pair=reordered_pair,
            created_by="synthetic-creator",
            created_timestamp="2025-07-20T12:00:00Z",
        )
