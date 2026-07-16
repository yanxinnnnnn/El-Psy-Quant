"""Deterministic source and isolated installer coverage for Sprint 160."""

import json
import shutil
from pathlib import Path

import pytest

from el_psy_quant.application.paper_jobs import read_paper_job_result
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
    assert load_demo_workspace_descriptor(target).to_dict()["dataset_version"] == 1


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
    assert "install-demo-workspace" in demo
