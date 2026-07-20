import hashlib
import inspect
import json
from dataclasses import FrozenInstanceError

import pandas as pd
import pytest

from el_psy_quant.portfolio_review import (
    PORTFOLIO_REVIEW_DECISION_ARTIFACT_SCHEMA_VERSION,
    PORTFOLIO_REVIEW_DECISION_SCOPE,
    SUPPORTED_PORTFOLIO_REVIEW_DECISION_OUTCOMES,
    PortfolioReviewDecisionArtifact,
    create_portfolio_review_analysis_artifact,
    create_portfolio_review_baseline_scenario,
    create_portfolio_review_component,
    create_portfolio_review_decision_artifact,
    create_portfolio_review_evidence_reference,
    create_portfolio_review_proposed_scenario,
    create_portfolio_review_scenario_pair,
    create_portfolio_review_source,
)


def _analysis(*, review_id: str = "synthetic-review"):
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
            symbols=(f"SYN-{index}",),
        )
        for index in (1, 2)
    )
    source = create_portfolio_review_source(
        source_id="synthetic-source",
        components=components,
        aligned_returns=pd.DataFrame(
            {
                "component-1": (0.01, -0.02, 0.03, 0.01),
                "component-2": (0.02, 0.01, -0.01, 0.03),
            },
            index=pd.date_range("2025-07-01", periods=4, freq="D"),
        ),
        evaluation_frequency="daily",
        periods_per_year=252.0,
        created_by="synthetic-source-creator",
        created_timestamp="2025-07-19T12:00:00Z",
    )
    baseline = create_portfolio_review_baseline_scenario(
        scenario_id="synthetic-baseline",
        source=source,
        weights={"component-1": 1.0, "component-2": 0.0},
        rationale="Synthetic baseline",
    )
    proposed = create_portfolio_review_proposed_scenario(
        scenario_id="synthetic-proposed",
        source=source,
        weights={"component-1": 0.6, "component-2": 0.4},
        proposed_component_id="component-2",
        rationale="Synthetic proposal",
    )
    pair = create_portfolio_review_scenario_pair(
        source=source,
        baseline=baseline,
        proposed=proposed,
    )
    return create_portfolio_review_analysis_artifact(
        review_id=review_id,
        source=source,
        scenario_pair=pair,
        created_by="synthetic-analysis-creator",
        created_timestamp="2025-07-20T12:00:00Z",
    )


def _decision(
    *,
    analysis=None,
    decision_id: str = "synthetic-decision",
    outcome: str = "approved",
    rationale: str = "Synthetic human rationale",
    reviewed_by: str = "synthetic-reviewer",
    reviewed_timestamp: object = "2025-07-21T12:00:00Z",
    notes: tuple[str, ...] = ("Second note", "First note", "Second note"),
    warnings: tuple[str, ...] = ("Synthetic decision warning",),
):
    linked_analysis = _analysis() if analysis is None else analysis
    return create_portfolio_review_decision_artifact(
        decision_id=decision_id,
        analysis=linked_analysis,
        outcome=outcome,
        rationale=rationale,
        reviewed_by=reviewed_by,
        reviewed_timestamp=reviewed_timestamp,
        notes=notes,
        warnings=warnings,
    )


@pytest.mark.parametrize(
    "outcome",
    SUPPORTED_PORTFOLIO_REVIEW_DECISION_OUTCOMES,
)
def test_all_exact_governance_outcomes_are_supported(outcome: str) -> None:
    analysis = _analysis()
    decision = _decision(analysis=analysis, outcome=outcome)

    assert decision.outcome == outcome
    assert decision.decision_scope == PORTFOLIO_REVIEW_DECISION_SCOPE
    assert decision.decision_scope == "portfolio_review_governance_only"
    assert decision.review_id == analysis.review_id
    assert decision.analysis_digest == analysis.analysis_digest
    assert decision.source_id == analysis.source_id
    assert decision.source_digest == analysis.source_digest
    assert decision.baseline_scenario_id == analysis.baseline_scenario_id
    assert decision.baseline_scenario_digest == (
        analysis.baseline_scenario_digest
    )
    assert decision.proposed_scenario_id == analysis.proposed_scenario_id
    assert decision.proposed_scenario_digest == (
        analysis.proposed_scenario_digest
    )


def test_decision_normalizes_audit_data_without_embedding_analysis() -> None:
    analysis = _analysis()
    analysis_before = analysis.to_dict()
    decision = _decision(
        analysis=analysis,
        decision_id="  synthetic-decision  ",
        rationale="  Human rationale  ",
        reviewed_by="  synthetic-reviewer  ",
        reviewed_timestamp="2025-07-21T20:00:00+08:00",
    )
    payload = decision.to_dict()

    assert decision.decision_id == "synthetic-decision"
    assert decision.rationale == "Human rationale"
    assert decision.reviewed_by == "synthetic-reviewer"
    assert decision.reviewed_timestamp.isoformat() == (
        "2025-07-21T12:00:00+00:00"
    )
    assert decision.notes == ("Second note", "First note", "Second note")
    assert "analysis" not in payload
    assert "concentration_exposure_analysis" not in payload
    assert "interaction_impact_analysis" not in payload
    assert analysis.to_dict() == analysis_before


def test_decision_export_digest_immutability_and_constructor_protection() -> None:
    decision = _decision()
    payload = decision.to_dict()

    assert payload["schema_version"] == (
        PORTFOLIO_REVIEW_DECISION_ARTIFACT_SCHEMA_VERSION
    )
    assert json.loads(json.dumps(payload, allow_nan=False)) == payload
    assert len(decision.decision_digest) == 64
    assert set(decision.decision_digest) <= set("0123456789abcdef")
    without_digest = dict(payload)
    del without_digest["decision_digest"]
    canonical = json.dumps(
        without_digest,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert decision.decision_digest == hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()
    assert sum(key == "decision_digest" for key in payload) == 1
    with pytest.raises(FrozenInstanceError):
        decision.outcome = "rejected"  # type: ignore[misc]
    with pytest.raises(TypeError, match="created by"):
        PortfolioReviewDecisionArtifact()

    parameters = inspect.signature(
        create_portfolio_review_decision_artifact
    ).parameters
    assert tuple(parameters) == (
        "decision_id",
        "analysis",
        "outcome",
        "rationale",
        "reviewed_by",
        "reviewed_timestamp",
        "notes",
        "warnings",
    )
    with pytest.raises(TypeError):
        create_portfolio_review_decision_artifact(
            decision_id="synthetic-decision",
            analysis=_analysis(),
            outcome="approved",
            rationale="Synthetic rationale",
            reviewed_by="synthetic-reviewer",
            reviewed_timestamp="2025-07-21T12:00:00Z",
            source_id="override",  # type: ignore[call-arg]
        )


def test_decision_digest_is_deterministic_and_normalizes_equivalent_instants() -> None:
    first = _decision(reviewed_timestamp="2025-07-21T12:00:00Z")
    repeated = _decision(
        reviewed_timestamp="2025-07-21T12:00:00+00:00"
    )
    equivalent = _decision(
        reviewed_timestamp="2025-07-21T20:00:00+08:00"
    )
    assert first.to_dict() == repeated.to_dict() == equivalent.to_dict()


@pytest.mark.parametrize(
    "changes",
    [
        {"decision_id": "changed-decision"},
        {"outcome": "rejected"},
        {"rationale": "Changed rationale"},
        {"reviewed_by": "changed-reviewer"},
        {"reviewed_timestamp": "2025-07-21T12:00:01Z"},
        {"notes": ("Changed note",)},
        {"warnings": ("Changed warning",)},
    ],
)
def test_material_decision_inputs_change_digest(
    changes: dict[str, object],
) -> None:
    baseline = _decision()
    changed = _decision(**changes)
    assert changed.decision_digest != baseline.decision_digest


def test_changed_linked_analysis_changes_decision_digest() -> None:
    baseline = _decision(analysis=_analysis(review_id="review-a"))
    changed = _decision(analysis=_analysis(review_id="review-b"))
    assert changed.analysis_digest != baseline.analysis_digest
    assert changed.decision_digest != baseline.decision_digest


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("decision_id", " "),
        ("rationale", ""),
        ("reviewed_by", "\t"),
    ],
)
def test_decision_rejects_blank_required_fields(
    field_name: str,
    value: object,
) -> None:
    kwargs = {field_name: value}
    with pytest.raises(ValueError, match=field_name):
        _decision(**kwargs)


@pytest.mark.parametrize(
    "timestamp",
    ["2025-07-21T12:00:00", "not-a-timestamp", None],
)
def test_decision_rejects_naive_or_invalid_timestamp(timestamp: object) -> None:
    with pytest.raises(ValueError, match="reviewed_timestamp"):
        _decision(reviewed_timestamp=timestamp)


@pytest.mark.parametrize(
    ("field_name", "values"),
    [
        ("notes", ("valid", " ")),
        ("warnings", "not-a-sequence"),
    ],
)
def test_decision_rejects_invalid_prose_sequences(
    field_name: str,
    values: object,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        _decision(**{field_name: values})


def test_decision_rejects_unsupported_outcome_and_wrong_analysis_type() -> None:
    with pytest.raises(ValueError, match="unsupported outcome"):
        _decision(outcome="pending")
    with pytest.raises(ValueError, match="PortfolioReviewAnalysisArtifact"):
        _decision(analysis=object())


def test_factory_has_no_hidden_settlement_state_or_side_effect() -> None:
    analysis = _analysis()
    before = analysis.to_dict()
    first = _decision(analysis=analysis)
    second = _decision(analysis=analysis)

    assert first.to_dict() == second.to_dict()
    assert analysis.to_dict() == before
    forbidden = {
        "lifecycle",
        "paper_job",
        "account",
        "cash",
        "position",
        "order",
        "fill",
        "broker",
        "settled",
    }
    assert forbidden.isdisjoint(first.to_dict())
