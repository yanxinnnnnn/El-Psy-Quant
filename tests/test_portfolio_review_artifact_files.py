import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from el_psy_quant.portfolio_review import (
    PortfolioReviewArtifactConflictError,
    PortfolioReviewArtifactInvalidError,
    PortfolioReviewArtifactRootUnavailableError,
    create_portfolio_review_analysis_artifact,
    create_portfolio_review_baseline_scenario,
    create_portfolio_review_component,
    create_portfolio_review_decision_artifact,
    create_portfolio_review_evidence_reference,
    create_portfolio_review_proposed_scenario,
    create_portfolio_review_scenario_pair,
    create_portfolio_review_source,
    portfolio_review_analysis_relative_path,
    portfolio_review_decision_relative_path,
    portfolio_review_id_path_key,
    portfolio_review_source_relative_path,
    read_portfolio_review_analysis,
    read_portfolio_review_decision,
    read_portfolio_review_source,
    validate_portfolio_review_artifact_root,
    write_portfolio_review_analysis,
    write_portfolio_review_decision,
    write_portfolio_review_source,
)


def _artifacts(*, return_shift: float = 0.0):
    components = tuple(
        create_portfolio_review_component(
            component_id=f"synthetic-component-{index}",
            strategy_id=f"synthetic-strategy-{index}",
            evidence_references=(
                create_portfolio_review_evidence_reference(
                    reference_type="research_run",
                    reference_id=f"synthetic-run-{index}",
                ),
            ),
            symbols=None if index == 2 else (f"SYN-{index}",),
        )
        for index in (1, 2)
    )
    source = create_portfolio_review_source(
        source_id="synthetic/../source-中文",
        components=components,
        aligned_returns=pd.DataFrame(
            {
                components[0].component_id: (
                    0.01 + return_shift,
                    -0.01,
                    0.02,
                ),
                components[1].component_id: (0.02, 0.01, -0.01),
            },
            index=pd.date_range("2026-07-01", periods=3),
        ),
        evaluation_frequency="daily",
        periods_per_year=252,
        created_by="synthetic-source-actor",
        created_timestamp="2026-07-04T00:00:00Z",
    )
    baseline = create_portfolio_review_baseline_scenario(
        scenario_id="synthetic-baseline",
        source=source,
        weights=dict.fromkeys(source.component_ids, 0.5),
        rationale="Synthetic baseline only",
    )
    proposed = create_portfolio_review_proposed_scenario(
        scenario_id="synthetic-proposed",
        source=source,
        weights={
            source.component_ids[0]: 0.25,
            source.component_ids[1]: 0.75,
        },
        proposed_component_id=source.component_ids[1],
        rationale="Synthetic proposal only",
    )
    pair = create_portfolio_review_scenario_pair(
        source=source,
        baseline=baseline,
        proposed=proposed,
    )
    analysis = create_portfolio_review_analysis_artifact(
        review_id="synthetic\\absolute-looking:C:/review",
        source=source,
        scenario_pair=pair,
        created_by="synthetic-analysis-actor",
        created_timestamp="2026-07-05T00:00:00Z",
    )
    decision = create_portfolio_review_decision_artifact(
        decision_id="synthetic-decision",
        analysis=analysis,
        outcome="deferred",
        rationale="Synthetic governance-only rationale",
        reviewed_by="synthetic-founder",
        reviewed_timestamp="2026-07-06T00:00:00Z",
    )
    return source, analysis, decision


@pytest.mark.parametrize(
    "value",
    (
        "ordinary",
        "中文",
        "slash/value",
        r"backslash\value",
        "../escape",
        "C:/drive-looking",
        "/absolute-looking",
    ),
)
def test_ids_are_only_lowercase_sha256_path_keys(value: str) -> None:
    expected = hashlib.sha256(value.encode("utf-8")).hexdigest()

    assert portfolio_review_id_path_key(value) == expected
    assert expected in portfolio_review_source_relative_path(value)
    assert expected in portfolio_review_analysis_relative_path(value)
    assert expected in portfolio_review_decision_relative_path(value)
    assert value not in portfolio_review_source_relative_path(value)


def test_write_reopen_and_exact_reuse_are_deterministic(tmp_path: Path) -> None:
    source, analysis, decision = _artifacts()
    root = tmp_path / "evidence"
    root.mkdir()

    source_relative = write_portfolio_review_source(root=root, source=source)
    analysis_relative = write_portfolio_review_analysis(
        root=root,
        source_id=source.source_id,
        analysis=analysis,
    )
    decision_relative = write_portfolio_review_decision(
        root=root,
        source_id=source.source_id,
        decision=decision,
    )

    assert read_portfolio_review_source(
        root=root, source_id=source.source_id
    ).to_dict() == source.to_dict()
    assert read_portfolio_review_analysis(
        root=root,
        review_id=analysis.review_id,
        source_id=source.source_id,
    ).to_dict() == analysis.to_dict()
    assert read_portfolio_review_decision(
        root=root,
        review_id=analysis.review_id,
        source_id=source.source_id,
    ).to_dict() == decision.to_dict()
    assert write_portfolio_review_source(root=root, source=source) == source_relative
    assert (
        write_portfolio_review_analysis(
            root=root,
            source_id=source.source_id,
            analysis=analysis,
        )
        == analysis_relative
    )
    assert (
        write_portfolio_review_decision(
            root=root,
            source_id=source.source_id,
            decision=decision,
        )
        == decision_relative
    )
    source_bytes = (root / Path(source_relative)).read_bytes()
    assert source_bytes.endswith(b"\n")
    assert source_bytes == (
        json.dumps(
            source.to_dict(),
            indent=2,
            allow_nan=False,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def test_different_valid_source_cannot_overwrite_reserved_path(
    tmp_path: Path,
) -> None:
    source, _, _ = _artifacts()
    changed_source, _, _ = _artifacts(return_shift=0.001)
    root = tmp_path / "evidence"
    root.mkdir()
    write_portfolio_review_source(root=root, source=source)

    with pytest.raises(PortfolioReviewArtifactConflictError):
        write_portfolio_review_source(root=root, source=changed_source)

    assert read_portfolio_review_source(
        root=root, source_id=source.source_id
    ).source_digest == source.source_digest


@pytest.mark.parametrize(
    "malformed",
    (
        '{"schema_version":1,"schema_version":1}',
        '{"schema_version":NaN}',
        '{"schema_version":Infinity}',
        '{"schema_version":',
    ),
)
def test_strict_reader_rejects_duplicate_nonfinite_and_truncated_json(
    tmp_path: Path,
    malformed: str,
) -> None:
    source, _, _ = _artifacts()
    root = tmp_path / "evidence"
    target = root / Path(portfolio_review_source_relative_path(source.source_id))
    target.parent.mkdir(parents=True)
    target.write_text(malformed, encoding="utf-8")

    with pytest.raises(PortfolioReviewArtifactInvalidError):
        read_portfolio_review_source(root=root, source_id=source.source_id)


def test_analysis_reader_recalculates_and_rejects_derived_tampering(
    tmp_path: Path,
) -> None:
    source, analysis, _ = _artifacts()
    root = tmp_path / "evidence"
    root.mkdir()
    write_portfolio_review_source(root=root, source=source)
    relative = write_portfolio_review_analysis(
        root=root,
        source_id=source.source_id,
        analysis=analysis,
    )
    target = root / Path(relative)
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["concentration_exposure_analysis"]["baseline_concentration"][
        "largest_component_weight"
    ] = 0.99
    target.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(PortfolioReviewArtifactInvalidError):
        read_portfolio_review_analysis(
            root=root,
            review_id=analysis.review_id,
            source_id=source.source_id,
        )


def test_root_must_already_be_one_real_directory(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    file_root = tmp_path / "file"
    file_root.write_text("not a directory", encoding="utf-8")

    with pytest.raises(PortfolioReviewArtifactRootUnavailableError):
        validate_portfolio_review_artifact_root(missing)
    with pytest.raises(PortfolioReviewArtifactRootUnavailableError):
        validate_portfolio_review_artifact_root(file_root)
