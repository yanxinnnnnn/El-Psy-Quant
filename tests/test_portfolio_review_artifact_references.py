import json
from dataclasses import FrozenInstanceError

import pandas as pd
import pytest

from el_psy_quant.portfolio_review import (
    PORTFOLIO_REVIEW_ARTIFACT_REFERENCE_SCHEMA_VERSION,
    SUPPORTED_PORTFOLIO_REVIEW_ARTIFACT_TYPES,
    create_portfolio_review_analysis_artifact,
    create_portfolio_review_artifact_reference,
    create_portfolio_review_artifact_reference_from_analysis,
    create_portfolio_review_artifact_reference_from_decision,
    create_portfolio_review_artifact_reference_from_source,
    create_portfolio_review_baseline_scenario,
    create_portfolio_review_component,
    create_portfolio_review_decision_artifact,
    create_portfolio_review_evidence_reference,
    create_portfolio_review_proposed_scenario,
    create_portfolio_review_scenario_pair,
    create_portfolio_review_source,
)


def _artifacts():
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
                "component-1": (0.01, -0.02, 0.03),
                "component-2": (0.02, 0.01, -0.01),
            },
            index=pd.date_range("2025-07-01", periods=3, freq="D"),
        ),
        evaluation_frequency="daily",
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
    analysis = create_portfolio_review_analysis_artifact(
        review_id="synthetic-review",
        source=source,
        scenario_pair=pair,
        created_by="synthetic-analysis-creator",
        created_timestamp="2025-07-20T12:00:00Z",
    )
    decision = create_portfolio_review_decision_artifact(
        decision_id="synthetic-decision",
        analysis=analysis,
        outcome="deferred",
        rationale="Synthetic human rationale",
        reviewed_by="synthetic-reviewer",
        reviewed_timestamp="2025-07-21T12:00:00Z",
    )
    return source, analysis, decision


@pytest.mark.parametrize(
    "artifact_type",
    SUPPORTED_PORTFOLIO_REVIEW_ARTIFACT_TYPES,
)
def test_all_exact_artifact_types_are_supported(artifact_type: str) -> None:
    reference = create_portfolio_review_artifact_reference(
        artifact_type=artifact_type,
        artifact_id="  synthetic-id  ",
        artifact_digest="0" * 64,
        label="  Synthetic label  ",
        description="  ",
    )

    assert reference.artifact_type == artifact_type
    assert reference.artifact_id == "synthetic-id"
    assert reference.artifact_digest == "0" * 64
    assert reference.label == "Synthetic label"
    assert reference.description is None


def test_artifact_reference_rejects_unsupported_type_and_blank_identity() -> None:
    with pytest.raises(ValueError, match="unsupported artifact_type"):
        create_portfolio_review_artifact_reference(
            artifact_type="portfolio_review_path",
            artifact_id="synthetic-id",
            artifact_digest="0" * 64,
        )
    with pytest.raises(ValueError, match="artifact_id"):
        create_portfolio_review_artifact_reference(
            artifact_type="portfolio_review_source",
            artifact_id=" ",
            artifact_digest="0" * 64,
        )


@pytest.mark.parametrize(
    "digest",
    [
        "A" * 64,
        "0" * 63,
        "0" * 65,
        "g" * 64,
        "",
        123,
    ],
)
def test_artifact_reference_rejects_invalid_digest(digest: object) -> None:
    with pytest.raises(ValueError, match="artifact_digest"):
        create_portfolio_review_artifact_reference(
            artifact_type="portfolio_review_source",
            artifact_id="synthetic-id",
            artifact_digest=digest,  # type: ignore[arg-type]
        )


def test_typed_helpers_copy_exact_approved_id_and_digest() -> None:
    source, analysis, decision = _artifacts()
    source_reference = create_portfolio_review_artifact_reference_from_source(
        source,
    )
    analysis_reference = (
        create_portfolio_review_artifact_reference_from_analysis(analysis)
    )
    decision_reference = (
        create_portfolio_review_artifact_reference_from_decision(decision)
    )

    assert (
        source_reference.artifact_type,
        source_reference.artifact_id,
        source_reference.artifact_digest,
    ) == (
        "portfolio_review_source",
        source.source_id,
        source.source_digest,
    )
    assert (
        analysis_reference.artifact_type,
        analysis_reference.artifact_id,
        analysis_reference.artifact_digest,
    ) == (
        "portfolio_review_analysis",
        analysis.review_id,
        analysis.analysis_digest,
    )
    assert (
        decision_reference.artifact_type,
        decision_reference.artifact_id,
        decision_reference.artifact_digest,
    ) == (
        "portfolio_review_decision",
        decision.decision_id,
        decision.decision_digest,
    )


@pytest.mark.parametrize(
    ("helper", "message"),
    [
        (
            create_portfolio_review_artifact_reference_from_source,
            "PortfolioReviewSource",
        ),
        (
            create_portfolio_review_artifact_reference_from_analysis,
            "PortfolioReviewAnalysisArtifact",
        ),
        (
            create_portfolio_review_artifact_reference_from_decision,
            "PortfolioReviewDecisionArtifact",
        ),
    ],
)
def test_typed_helpers_reject_wrong_input_types(helper, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        helper(object())


def test_artifact_reference_is_immutable_json_compatible_and_path_free() -> None:
    reference = create_portfolio_review_artifact_reference(
        artifact_type="portfolio_review_analysis",
        artifact_id="synthetic-review",
        artifact_digest="a" * 64,
    )
    payload = reference.to_dict()

    assert payload["schema_version"] == (
        PORTFOLIO_REVIEW_ARTIFACT_REFERENCE_SCHEMA_VERSION
    )
    assert json.loads(json.dumps(payload, allow_nan=False)) == payload
    assert set(payload) == {
        "schema_version",
        "artifact_type",
        "artifact_id",
        "artifact_digest",
        "label",
        "description",
    }
    assert {
        "path",
        "url",
        "root",
        "database_id",
        "payload",
    }.isdisjoint(payload)
    with pytest.raises(FrozenInstanceError):
        reference.artifact_id = "changed"  # type: ignore[misc]
