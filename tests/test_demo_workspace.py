"""Deterministic source and isolated Demo installer coverage."""

import json
import shutil
from pathlib import Path

import pytest
from el_psy_quant.application.paper_jobs import read_paper_job_result
from el_psy_quant.application.portfolio_reviews import (
    get_portfolio_review_detail,
    record_portfolio_review_decision_with_outcome,
)
from el_psy_quant.demo_workspace import (
    DemoWorkspaceConflictError,
    DemoWorkspacePaths,
    DemoWorkspaceSourceInvalidError,
    DemoWorkspaceTargetRefusedError,
    DemoWorkspaceUnavailableError,
    install_demo_workspace,
    load_demo_workspace_descriptor,
    validate_demo_workspace_source,
)
from el_psy_quant.persistence import (
    SqlAlchemyPaperJobAttemptRepository,
    SqlAlchemyPaperJobRepository,
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_SOURCE = PROJECT_ROOT / "examples" / "demo_workspace"
ALEMBIC_CONFIG = PROJECT_ROOT / "alembic.ini"


def _install(source: Path, target: Path):
    return install_demo_workspace(
        source_root=source,
        workspace_root=target,
        workspace_mode="demo",
        alembic_config_path=ALEMBIC_CONFIG,
    )


def test_versioned_source_validates_every_authoritative_contract() -> None:
    source = validate_demo_workspace_source(DEMO_SOURCE)

    assert source.manifest.dataset_id == "founder-demo-workspace"
    assert source.manifest.canonical_strategy_name == "moving_average_crossover"
    assert len(source.paper_requests) == 2
    assert source.manifest.comparison_candidate_job_ids == (
        "16000000-0000-4000-8000-000000000001",
        "16000000-0000-4000-8000-000000000002",
    )
    assert len(set(source.manifest.comparison_candidate_job_ids)) == 2
    descriptor = source.descriptor.to_dict()
    assert descriptor["schema_version"] == 2
    assert descriptor["dataset_version"] == 2
    assert descriptor["portfolio_review_example"]["create_idempotency_key"] == (
        "demo-portfolio-review-create-v1"
    )
    assert descriptor["portfolio_review_example"]["request"]["review_id"] == (
        "demo-portfolio-review-001"
    )
    assert descriptor["lifecycle_review_example"]["review_outcome"] == "deferred"
    assert descriptor["lifecycle_review_example"]["resulting_snapshot"] is None
    assert "DEMO" in descriptor["warning"]


def test_installer_success_replay_and_two_authoritative_results(tmp_path: Path) -> None:
    target = tmp_path / "demo-workspace"

    first = _install(DEMO_SOURCE, target)
    replay = _install(DEMO_SOURCE, target)

    assert first.already_installed is False
    assert replay.already_installed is True
    paths = DemoWorkspacePaths.from_root(target)
    assert set(path.name for path in target.iterdir()) == {
        ".demo-workspace-install.json",
        "evidence",
        "paper",
        "product.sqlite3",
        "research",
        "workspace-descriptor.json",
    }
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    factory = create_product_session_factory(engine=engine)
    try:
        with factory() as session:
            jobs = SqlAlchemyPaperJobRepository(session=session).list()
            assert [job.status for job in jobs] == ["succeeded", "succeeded"]
            assert [job.job_id for job in jobs] == [
                "16000000-0000-4000-8000-000000000001",
                "16000000-0000-4000-8000-000000000002",
            ]
            for job in jobs:
                attempts = SqlAlchemyPaperJobAttemptRepository(
                    session=session
                ).list_for_job(job_id=job.job_id)
                assert len(attempts) == 1
                assert attempts[0].status == "succeeded"
        for job_id in (
            "16000000-0000-4000-8000-000000000001",
            "16000000-0000-4000-8000-000000000002",
        ):
            result = read_paper_job_result(
                session_factory=factory,
                job_id=job_id,
                paper_artifact_root=paths.paper_root,
            )
            assert result.job_id == job_id
        review = get_portfolio_review_detail(
            session_factory=factory,
            artifact_root=paths.evidence_root,
            review_id="demo-portfolio-review-001",
        )
        assert review.record.status == "awaiting_decision"
        assert review.source.source_id == "demo-portfolio-review-source-001"
        assert review.analysis.proposed_component_id == "demo-msft-sleeve"
        assert review.decision is None
    finally:
        engine.dispose()


def test_prior_dataset_marker_is_refused_without_reinstall_or_mutation(
    tmp_path: Path,
) -> None:
    target = tmp_path / "demo-workspace"
    _install(DEMO_SOURCE, target)
    paths = DemoWorkspacePaths.from_root(target)
    marker_path = target / ".demo-workspace-install.json"
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    marker["dataset_version"] = 1
    marker_path.write_text(json.dumps(marker), encoding="utf-8")
    artifacts_before = {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in target.rglob("*")
        if path.is_file() and path != paths.database_path
    }

    with pytest.raises(DemoWorkspaceConflictError):
        _install(DEMO_SOURCE, target)

    assert {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in target.rglob("*")
        if path.is_file() and path != paths.database_path
    } == artifacts_before


def test_exact_replay_preserves_an_existing_human_decision(tmp_path: Path) -> None:
    target = tmp_path / "demo-workspace"
    _install(DEMO_SOURCE, target)
    paths = DemoWorkspacePaths.from_root(target)
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    factory = create_product_session_factory(engine=engine)
    try:
        decided = record_portfolio_review_decision_with_outcome(
            session_factory=factory,
            artifact_root=paths.evidence_root,
            review_id="demo-portfolio-review-001",
            idempotency_key="demo-founder-decision-v1",
            decision_id="demo-portfolio-decision-001",
            outcome="deferred",
            rationale="Founder acceptance test decision; no execution authority.",
            reviewed_by="demo-founder",
            reviewed_timestamp="2026-01-18T12:10:00Z",
            notes=("Preserved across exact Demo replay.",),
        )
        assert decided.review.record.status == "deferred"

        replay = _install(DEMO_SOURCE, target)

        assert replay.already_installed is True
        reopened = get_portfolio_review_detail(
            session_factory=factory,
            artifact_root=paths.evidence_root,
            review_id="demo-portfolio-review-001",
        )
        assert reopened.record.status == "deferred"
        assert reopened.decision is not None
        assert reopened.decision.decision_id == "demo-portfolio-decision-001"
    finally:
        engine.dispose()


def test_source_validation_failure_precedes_target_creation(tmp_path: Path) -> None:
    source = tmp_path / "source"
    shutil.copytree(DEMO_SOURCE, source)
    metrics = (
        source
        / "research_artifacts"
        / "moving-average-crossover-demo"
        / "demo-research-001"
        / "results"
        / "metrics.json"
    )
    metrics.write_text("not-json", encoding="utf-8")
    target = tmp_path / "target"

    with pytest.raises(DemoWorkspaceSourceInvalidError):
        _install(source, target)

    assert not target.exists()


@pytest.mark.parametrize(
    "case",
    (
        "invalid_path",
        "extra_root_child",
        "extra_request_key",
        "unsupported_reference_type",
        "duplicate_evidence",
        "invalid_return_matrix",
        "invalid_weight",
        "invalid_timestamp",
        "non_demo_warning",
    ),
)
def test_portfolio_review_source_mutations_fail_before_target_creation(
    tmp_path: Path,
    case: str,
) -> None:
    source = tmp_path / f"source-{case}"
    shutil.copytree(DEMO_SOURCE, source)
    manifest_path = source / "workspace-manifest.json"
    request_path = source / "portfolio_reviews" / "create-request.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    request = json.loads(request_path.read_text(encoding="utf-8"))
    if case == "invalid_path":
        manifest["portfolio_review_example"]["request_relative_path"] = (
            "../create-request.json"
        )
    elif case == "extra_root_child":
        (source / "unexpected").mkdir()
    elif case == "extra_request_key":
        request["unexpected"] = True
    elif case == "unsupported_reference_type":
        request["source"]["components"][0]["evidence_references"][0][
            "reference_type"
        ] = "unsupported_reference_type"
    elif case == "duplicate_evidence":
        references = request["source"]["components"][0]["evidence_references"]
        references.append(dict(references[0]))
    elif case == "invalid_return_matrix":
        request["source"]["return_observations"][0]["component_returns"] = [0.01]
    elif case == "invalid_weight":
        request["baseline_scenario"]["weights"]["demo-aapl-sleeve"] = -0.1
    elif case == "invalid_timestamp":
        request["analysis"]["created_timestamp"] = "not-a-timestamp"
    elif case == "non_demo_warning":
        request["source"]["warnings"] = ["Synthetic evidence only."]
    else:  # pragma: no cover - the parameter list is exhaustive
        raise AssertionError(case)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    request_path.write_text(json.dumps(request), encoding="utf-8")
    target = tmp_path / f"target-{case}"

    with pytest.raises(DemoWorkspaceSourceInvalidError):
        _install(source, target)

    assert not target.exists()


def test_conflicting_dataset_replay_is_refused_without_changes(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    shutil.copytree(DEMO_SOURCE, source)
    target = tmp_path / "target"
    _install(source, target)
    marker_before = (target / ".demo-workspace-install.json").read_bytes()
    (source / "README.md").write_text("changed demo source\n", encoding="utf-8")

    with pytest.raises(DemoWorkspaceConflictError):
        _install(source, target)

    assert (target / ".demo-workspace-install.json").read_bytes() == marker_before
    assert load_demo_workspace_descriptor(target).to_dict()["dataset_version"] == 2


def test_descriptor_requires_exact_dataset_version_two(tmp_path: Path) -> None:
    target = tmp_path / "demo-workspace"
    _install(DEMO_SOURCE, target)
    descriptor_path = target / "workspace-descriptor.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor["dataset_version"] = 1
    descriptor_path.write_text(json.dumps(descriptor), encoding="utf-8")

    with pytest.raises(DemoWorkspaceUnavailableError):
        load_demo_workspace_descriptor(target)


def test_seeded_portfolio_review_corruption_fails_closed(tmp_path: Path) -> None:
    target = tmp_path / "demo-workspace"
    _install(DEMO_SOURCE, target)
    source_path = next(
        path
        for path in (target / "evidence").rglob("*.json")
        if json.loads(path.read_text(encoding="utf-8")).get("source_id")
        == "demo-portfolio-review-source-001"
    )
    source_payload = json.loads(source_path.read_text(encoding="utf-8"))
    source_payload["evaluation_frequency"] = "tampered"
    source_path.write_text(json.dumps(source_payload), encoding="utf-8")

    with pytest.raises(DemoWorkspaceUnavailableError):
        _install(DEMO_SOURCE, target)


def test_non_demo_and_nonempty_targets_are_refused(tmp_path: Path) -> None:
    standard_target = tmp_path / "standard"
    with pytest.raises(DemoWorkspaceTargetRefusedError):
        install_demo_workspace(
            source_root=DEMO_SOURCE,
            workspace_root=standard_target,
            workspace_mode="standard",
            alembic_config_path=ALEMBIC_CONFIG,
        )
    assert not standard_target.exists()

    nonempty_target = tmp_path / "user-workspace"
    nonempty_target.mkdir()
    user_file = nonempty_target / "user-artifact.json"
    user_file.write_text('{"user": true}\n', encoding="utf-8")
    with pytest.raises(DemoWorkspaceTargetRefusedError):
        _install(DEMO_SOURCE, nonempty_target)
    assert json.loads(user_file.read_text(encoding="utf-8")) == {"user": True}
    assert tuple(nonempty_target.iterdir()) == (user_file,)


def test_failure_leaves_no_partial_visible_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import el_psy_quant.demo_workspace as demo_module

    target = tmp_path / "target"
    target.mkdir()

    def fail_population(**_kwargs) -> None:
        raise RuntimeError("injected failure")

    monkeypatch.setattr(demo_module, "_populate_database", fail_population)

    with pytest.raises(DemoWorkspaceUnavailableError):
        _install(DEMO_SOURCE, target)

    assert target.is_dir()
    assert tuple(target.iterdir()) == ()
    assert not (tmp_path / ".target.demo-install-staging").exists()


def test_standard_and_demo_compose_storage_are_distinct() -> None:
    standard = (PROJECT_ROOT / "compose.yaml").read_text(encoding="utf-8")
    demo = (PROJECT_ROOT / "compose.demo.yaml").read_text(encoding="utf-8")

    assert "name: el-psy-quant-mvp" in standard
    assert "name: el-psy-quant-demo" in demo
    assert "mvp-data:/data" in standard
    assert "demo-data:/data" in demo
    assert "EL_PSY_QUANT_WORKSPACE_MODE: demo" in demo
    assert "install-demo-workspace" not in standard
    assert "start-local-backend" in demo
