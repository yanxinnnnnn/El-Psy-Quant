from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pandas as pd
import pytest
from alembic import command
from alembic.config import Config

import el_psy_quant.application.portfolio_reviews as portfolio_review_services
from el_psy_quant.application import (
    PortfolioReviewArtifactUnavailableError,
    PortfolioReviewArtifactConflictError,
    PortfolioReviewConflictError,
    PortfolioReviewIdempotencyConflictError,
    PortfolioReviewInvalidError,
    PortfolioReviewSettledConflictError,
    create_portfolio_review_with_outcome,
    get_portfolio_review_detail,
    list_portfolio_reviews,
    record_portfolio_review_decision_with_outcome,
)
from el_psy_quant.persistence import (
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV
from el_psy_quant.portfolio_review import (
    create_portfolio_review_baseline_scenario,
    create_portfolio_review_component,
    create_portfolio_review_evidence_reference,
    create_portfolio_review_proposed_scenario,
    create_portfolio_review_scenario_pair,
    create_portfolio_review_source,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def durable_environment(tmp_path: Path, monkeypatch):
    database_path = tmp_path / "product.sqlite3"
    artifact_root = tmp_path / "evidence"
    artifact_root.mkdir()
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    command.upgrade(Config(str(PROJECT_ROOT / "alembic.ini")), "head")
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=database_path)
    )
    try:
        yield create_product_session_factory(engine=engine), artifact_root
    finally:
        engine.dispose()


def _source_pair(*, review_suffix: str = "1", return_shift: float = 0.0):
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
            symbols=(f"SYN-{index}",),
        )
        for index in (1, 2)
    )
    source = create_portfolio_review_source(
        source_id="synthetic-shared-source",
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
        scenario_id=f"synthetic-baseline-{review_suffix}",
        source=source,
        weights={
            source.component_ids[0]: 1.0,
            source.component_ids[1]: 0.0,
        },
        rationale="Synthetic baseline",
    )
    proposed = create_portfolio_review_proposed_scenario(
        scenario_id=f"synthetic-proposed-{review_suffix}",
        source=source,
        weights={
            source.component_ids[0]: 0.5,
            source.component_ids[1]: 0.5,
        },
        proposed_component_id=source.component_ids[1],
        rationale="Synthetic proposal",
    )
    return source, create_portfolio_review_scenario_pair(
        source=source,
        baseline=baseline,
        proposed=proposed,
    )


def _create(
    environment,
    *,
    key: str = "synthetic-create-key",
    review_id: str = "synthetic-review-1",
    suffix: str = "1",
    return_shift: float = 0.0,
):
    session_factory, artifact_root = environment
    source, pair = _source_pair(
        review_suffix=suffix,
        return_shift=return_shift,
    )
    return create_portfolio_review_with_outcome(
        session_factory=session_factory,
        artifact_root=artifact_root,
        idempotency_key=key,
        review_id=review_id,
        source=source,
        scenario_pair=pair,
        created_by="synthetic-analysis-actor",
        created_timestamp="2026-07-05T00:00:00Z",
    )


def test_create_replay_compact_list_and_exact_detail(durable_environment) -> None:
    session_factory, artifact_root = durable_environment

    created = _create(durable_environment)
    replayed = _create(durable_environment)
    listed = list_portfolio_reviews(
        session_factory=session_factory,
        limit=50,
    )
    detail = get_portfolio_review_detail(
        session_factory=session_factory,
        artifact_root=artifact_root,
        review_id=created.review.record.review_id,
    )

    assert created.outcome == "created"
    assert replayed.outcome == "replayed"
    assert replayed.review == created.review
    assert tuple(view.record.review_id for view in listed) == (
        "synthetic-review-1",
    )
    assert detail.source.to_dict() == created.review.source.to_dict()
    assert detail.analysis.to_dict() == created.review.analysis.to_dict()
    assert detail.decision is None


def test_create_idempotency_identity_and_source_conflicts(
    durable_environment,
) -> None:
    _create(durable_environment)
    with pytest.raises(PortfolioReviewIdempotencyConflictError):
        _create(
            durable_environment,
            key="synthetic-create-key",
            review_id="different-review",
            suffix="2",
        )
    with pytest.raises(PortfolioReviewConflictError):
        _create(
            durable_environment,
            key="new-create-key",
            review_id="synthetic-review-1",
        )
    with pytest.raises(PortfolioReviewArtifactConflictError):
        _create(
            durable_environment,
            key="changed-source-key",
            review_id="synthetic-review-2",
            suffix="2",
            return_shift=0.001,
        )


@pytest.mark.parametrize("outcome", ("approved", "rejected", "deferred"))
def test_all_human_outcomes_settle_and_reopen(
    durable_environment,
    outcome: str,
) -> None:
    session_factory, artifact_root = durable_environment
    created = _create(durable_environment)

    decided = record_portfolio_review_decision_with_outcome(
        session_factory=session_factory,
        artifact_root=artifact_root,
        review_id=created.review.record.review_id,
        idempotency_key=f"synthetic-decision-{outcome}",
        decision_id=f"synthetic-decision-{outcome}",
        outcome=outcome,
        rationale="Synthetic governance-only decision",
        reviewed_by="synthetic-founder",
        reviewed_timestamp="2026-07-06T00:00:00Z",
    )

    assert decided.outcome == "created"
    assert decided.review.record.status == outcome
    assert decided.review.record.version == 2
    assert decided.review.decision is not None
    assert decided.review.decision.outcome == outcome
    reopened = get_portfolio_review_detail(
        session_factory=session_factory,
        artifact_root=artifact_root,
        review_id=created.review.record.review_id,
    )
    assert reopened == decided.review


def test_decision_replay_conflicts_and_timestamp_boundary(
    durable_environment,
) -> None:
    session_factory, artifact_root = durable_environment
    created = _create(durable_environment)
    arguments = {
        "session_factory": session_factory,
        "artifact_root": artifact_root,
        "review_id": created.review.record.review_id,
        "idempotency_key": "synthetic-decision-key",
        "decision_id": "synthetic-decision",
        "outcome": "approved",
        "rationale": "Synthetic governance-only decision",
        "reviewed_by": "synthetic-founder",
        "reviewed_timestamp": "2026-07-06T00:00:00Z",
    }
    first = record_portfolio_review_decision_with_outcome(**arguments)
    replay = record_portfolio_review_decision_with_outcome(**arguments)
    assert first.outcome == "created"
    assert replay.outcome == "replayed"

    with pytest.raises(PortfolioReviewIdempotencyConflictError):
        record_portfolio_review_decision_with_outcome(
            **{**arguments, "outcome": "rejected"}
        )
    with pytest.raises(PortfolioReviewSettledConflictError):
        record_portfolio_review_decision_with_outcome(
            **{
                **arguments,
                "idempotency_key": "new-decision-key",
                "decision_id": "new-decision",
            }
        )

def test_decision_write_failure_rolls_back_database(
    durable_environment,
    monkeypatch,
) -> None:
    session_factory, artifact_root = durable_environment
    created = _create(durable_environment)

    def fail_write(**_values):
        raise PortfolioReviewArtifactUnavailableError()

    monkeypatch.setattr(
        portfolio_review_services,
        "write_portfolio_review_decision",
        fail_write,
    )
    with pytest.raises(PortfolioReviewArtifactUnavailableError):
        record_portfolio_review_decision_with_outcome(
            session_factory=session_factory,
            artifact_root=artifact_root,
            review_id=created.review.record.review_id,
            idempotency_key="synthetic-decision-key",
            decision_id="synthetic-decision",
            outcome="approved",
            rationale="Synthetic governance-only decision",
            reviewed_by="synthetic-founder",
            reviewed_timestamp="2026-07-06T00:00:00Z",
        )

    assert list_portfolio_reviews(
        session_factory=session_factory
    )[0].record.status == "awaiting_decision"


def test_two_concurrent_decisions_have_one_winner(durable_environment) -> None:
    session_factory, artifact_root = durable_environment
    created = _create(durable_environment)
    barrier = Barrier(2)

    def decide(index: int):
        barrier.wait()
        try:
            return record_portfolio_review_decision_with_outcome(
                session_factory=session_factory,
                artifact_root=artifact_root,
                review_id=created.review.record.review_id,
                idempotency_key=f"decision-key-{index}",
                decision_id=f"decision-{index}",
                outcome="approved" if index == 1 else "rejected",
                rationale=f"Synthetic decision {index}",
                reviewed_by=f"synthetic-founder-{index}",
                reviewed_timestamp="2026-07-06T00:00:00Z",
            )
        except PortfolioReviewSettledConflictError:
            return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(decide, (1, 2)))

    assert sum(result is not None for result in results) == 1
    detail = get_portfolio_review_detail(
        session_factory=session_factory,
        artifact_root=artifact_root,
        review_id=created.review.record.review_id,
    )
    assert detail.record.status in {"approved", "rejected"}
    assert detail.decision is not None


def test_reviewed_timestamp_cannot_precede_analysis(durable_environment) -> None:
    session_factory, artifact_root = durable_environment
    created = _create(durable_environment)
    with pytest.raises(PortfolioReviewInvalidError):
        record_portfolio_review_decision_with_outcome(
            session_factory=session_factory,
            artifact_root=artifact_root,
            review_id=created.review.record.review_id,
            idempotency_key="synthetic-decision-key",
            decision_id="synthetic-decision",
            outcome="approved",
            rationale="Synthetic governance-only decision",
            reviewed_by="synthetic-founder",
            reviewed_timestamp="2026-07-04T00:00:00Z",
        )
