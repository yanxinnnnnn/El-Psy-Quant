"""Deterministic local deployment, verification, and isolation coverage."""

from __future__ import annotations

import hashlib
import importlib
import json
import shutil
import sqlite3
import subprocess
import tomllib
from pathlib import Path

import pytest
import yaml
from alembic import command
from alembic.config import Config

import el_psy_quant.local_workspace as local_module
from el_psy_quant.api.app import create_app
from el_psy_quant.demo_workspace import install_demo_workspace
from el_psy_quant.local_workspace import (
    LocalWorkspaceError,
    LocalWorkspaceVerification,
    prepare_standard_workspace,
    start_local_backend,
    verify_local_workspace,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV
from el_psy_quant.persistence.schema import CURRENT_PRODUCT_SCHEMA_REVISION

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_CONFIG = PROJECT_ROOT / "alembic.ini"
DEMO_SOURCE = PROJECT_ROOT / "examples" / "demo_workspace"
RUNTIME_EXPORT_COMMAND = (
    "uv",
    "export",
    "--locked",
    "--no-dev",
    "--no-emit-project",
    "--no-hashes",
    "--no-annotate",
    "--no-header",
)
BUILD_EXPORT_COMMAND = (
    "uv",
    "export",
    "--locked",
    "--only-group",
    "build",
    "--no-emit-project",
    "--no-hashes",
    "--no-annotate",
    "--no-header",
)


def _migrated_standard(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    root.mkdir()
    for name in ("research", "evidence", "paper"):
        (root / name).mkdir()
    database = root / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database))
    command.upgrade(Config(str(ALEMBIC_CONFIG)), "head")
    return database


def _tree_digest(root: Path) -> tuple[tuple[str, str, int], ...]:
    result: list[tuple[str, str, int]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_file():
            result.append(
                (
                    relative,
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                    path.stat().st_mtime_ns,
                )
            )
        else:
            result.append((relative + "/", "", path.stat().st_mtime_ns))
    return tuple(result)


def _runtime_environment(
    monkeypatch: pytest.MonkeyPatch,
    *,
    root: Path,
    mode: str,
) -> None:
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(root / "product.sqlite3"))
    monkeypatch.setenv(
        "EL_PSY_QUANT_RESEARCH_ARTIFACT_ROOT", str(root / "research")
    )
    monkeypatch.setenv(
        "EL_PSY_QUANT_EVIDENCE_ARTIFACT_ROOT", str(root / "evidence")
    )
    monkeypatch.setenv("EL_PSY_QUANT_PAPER_ARTIFACT_ROOT", str(root / "paper"))
    monkeypatch.setenv("EL_PSY_QUANT_WORKSPACE_MODE", mode)
    if mode == "demo":
        monkeypatch.setenv("EL_PSY_QUANT_DEMO_WORKSPACE_ROOT", str(root))
    else:
        monkeypatch.delenv("EL_PSY_QUANT_DEMO_WORKSPACE_ROOT", raising=False)


def test_standard_verification_is_read_only_and_accepts_empty_collections(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "standard"
    _migrated_standard(root, monkeypatch)
    before = _tree_digest(root)

    result = verify_local_workspace(mode="standard", workspace_root=root)

    assert result == LocalWorkspaceVerification(
        mode="standard",
        schema_revision=CURRENT_PRODUCT_SCHEMA_REVISION,
    )
    assert _tree_digest(root) == before


@pytest.mark.parametrize(
    "revision_rows",
    [
        (),
        ("0004_paper_job_recovery_audit",),
        ("unexpected_revision",),
        (
            CURRENT_PRODUCT_SCHEMA_REVISION,
            "0004_paper_job_recovery_audit",
        ),
    ],
)
def test_standard_verification_refuses_noncurrent_revision_without_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    revision_rows: tuple[str, ...],
) -> None:
    root = tmp_path / "standard"
    database = _migrated_standard(root, monkeypatch)
    import sqlite3

    with sqlite3.connect(database) as connection:
        connection.execute("DELETE FROM alembic_version")
        connection.executemany(
            "INSERT INTO alembic_version (version_num) VALUES (?)",
            ((revision,) for revision in revision_rows),
        )
    before = database.read_bytes()

    with pytest.raises(LocalWorkspaceError, match="revision"):
        verify_local_workspace(mode="standard", workspace_root=root)

    assert database.read_bytes() == before


def test_standard_verification_refuses_missing_malformed_incompatible_and_demo_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing = tmp_path / "missing"
    with pytest.raises(LocalWorkspaceError, match="workspace root"):
        verify_local_workspace(mode="standard", workspace_root=missing)
    assert not missing.exists()

    malformed = tmp_path / "malformed"
    malformed.mkdir()
    for name in ("research", "evidence", "paper"):
        (malformed / name).mkdir()
    (malformed / "product.sqlite3").write_bytes(b"not-sqlite")
    with pytest.raises(LocalWorkspaceError, match="revision|verification"):
        verify_local_workspace(mode="standard", workspace_root=malformed)

    incompatible = tmp_path / "incompatible"
    database = _migrated_standard(incompatible, monkeypatch)
    import sqlite3

    with sqlite3.connect(database) as connection:
        connection.execute("DROP TABLE artifact_index_entries")
    with pytest.raises(LocalWorkspaceError, match="incompatible"):
        verify_local_workspace(mode="standard", workspace_root=incompatible)

    marked = tmp_path / "marked"
    _migrated_standard(marked, monkeypatch)
    (marked / ".demo-workspace-install.json").write_text(
        "{}\n", encoding="utf-8"
    )
    with pytest.raises(LocalWorkspaceError, match="Demo installation identity"):
        verify_local_workspace(mode="standard", workspace_root=marked)


def test_standard_verification_refuses_wrong_root_types_and_symlink_escape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "standard"
    _migrated_standard(root, monkeypatch)
    shutil.rmtree(root / "paper")
    (root / "paper").write_text("not-a-directory", encoding="utf-8")
    with pytest.raises(LocalWorkspaceError, match="paper artifact root"):
        verify_local_workspace(mode="standard", workspace_root=root)

    (root / "paper").unlink()
    (root / "paper").mkdir()
    original_is_symlink = Path.is_symlink
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda path: path == root / "paper" or original_is_symlink(path),
    )
    with pytest.raises(LocalWorkspaceError, match="symlink"):
        verify_local_workspace(mode="standard", workspace_root=root)


def test_demo_verification_reads_complete_descriptor_journey_without_changes(
    tmp_path: Path,
) -> None:
    root = tmp_path / "demo"
    install_demo_workspace(
        source_root=DEMO_SOURCE,
        workspace_root=root,
        workspace_mode="demo",
        alembic_config_path=ALEMBIC_CONFIG,
    )
    before = _tree_digest(root)

    result = verify_local_workspace(mode="demo", workspace_root=root)

    assert result == LocalWorkspaceVerification(
        mode="demo",
        schema_revision=CURRENT_PRODUCT_SCHEMA_REVISION,
        dataset_id="founder-demo-workspace",
        dataset_version=2,
    )
    assert _tree_digest(root) == before


def test_demo_verification_refuses_standard_and_tampered_references(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    standard = tmp_path / "standard"
    _migrated_standard(standard, monkeypatch)
    with pytest.raises(LocalWorkspaceError, match="layout|marker|install"):
        verify_local_workspace(mode="demo", workspace_root=standard)

    demo = tmp_path / "demo"
    install_demo_workspace(
        source_root=DEMO_SOURCE,
        workspace_root=demo,
        workspace_mode="demo",
        alembic_config_path=ALEMBIC_CONFIG,
    )
    descriptor_path = demo / "workspace-descriptor.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor["research_run"]["run_id"] = "missing-run"
    descriptor_path.write_text(json.dumps(descriptor), encoding="utf-8")
    with pytest.raises(LocalWorkspaceError, match="verification failed|unavailable"):
        verify_local_workspace(mode="demo", workspace_root=demo)


def test_verification_never_calls_migration_or_demo_installer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "standard"
    _migrated_standard(root, monkeypatch)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("verification must not mutate the workspace")

    monkeypatch.setattr(local_module.alembic_command, "upgrade", forbidden)
    monkeypatch.setattr(local_module, "install_demo_workspace", forbidden)

    verify_local_workspace(mode="standard", workspace_root=root)


def test_standard_startup_orders_prepare_verify_serve_and_failures_never_serve(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "standard"
    root.mkdir()
    _runtime_environment(monkeypatch, root=root, mode="standard")
    events: list[str] = []

    monkeypatch.setattr(
        local_module,
        "prepare_standard_workspace",
        lambda **_kwargs: events.append("prepare"),
    )
    monkeypatch.setattr(
        local_module,
        "verify_local_workspace",
        lambda **_kwargs: (
            events.append("verify")
            or LocalWorkspaceVerification(
                mode="standard",
                schema_revision=CURRENT_PRODUCT_SCHEMA_REVISION,
            )
        ),
    )

    start_local_backend(
        mode="standard",
        workspace_root=root,
        alembic_config_path=ALEMBIC_CONFIG,
        serve=lambda: events.append("serve"),
    )
    assert events == ["prepare", "verify", "serve"]

    events.clear()

    def fail_prepare(**_kwargs) -> None:
        events.append("prepare")
        raise LocalWorkspaceError("migration failed")

    monkeypatch.setattr(local_module, "prepare_standard_workspace", fail_prepare)
    with pytest.raises(LocalWorkspaceError, match="migration failed"):
        start_local_backend(
            mode="standard",
            workspace_root=root,
            alembic_config_path=ALEMBIC_CONFIG,
            serve=lambda: events.append("serve"),
        )
    assert events == ["prepare"]


def test_migration_resource_failure_precedes_mutation_demo_install_and_serve(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    standard = tmp_path / "standard"
    standard.mkdir()
    existing_artifact = standard / "existing.json"
    existing_artifact.write_bytes(b'{"preserve":true}\n')
    _runtime_environment(monkeypatch, root=standard, mode="standard")
    events: list[str] = []

    def fail_preflight(**_kwargs) -> None:
        raise LocalWorkspaceError("product migration resources are unavailable")

    monkeypatch.setattr(
        local_module,
        "preflight_product_migration_resources",
        fail_preflight,
    )
    monkeypatch.setattr(
        local_module,
        "prepare_standard_workspace",
        lambda **_kwargs: events.append("prepare"),
    )
    monkeypatch.setattr(
        local_module,
        "install_demo_workspace",
        lambda **_kwargs: events.append("install"),
    )

    with pytest.raises(LocalWorkspaceError, match="migration resources"):
        start_local_backend(
            mode="standard",
            workspace_root=standard,
            alembic_config_path=ALEMBIC_CONFIG,
            serve=lambda: events.append("serve"),
        )

    assert events == []
    assert existing_artifact.read_bytes() == b'{"preserve":true}\n'
    assert not (standard / "product.sqlite3").exists()
    assert not any((standard / name).exists() for name in ("research", "evidence", "paper"))

    demo = tmp_path / "demo"
    _runtime_environment(monkeypatch, root=demo, mode="demo")
    with pytest.raises(LocalWorkspaceError, match="migration resources"):
        start_local_backend(
            mode="demo",
            workspace_root=demo,
            alembic_config_path=ALEMBIC_CONFIG,
            demo_source_root=DEMO_SOURCE,
            serve=lambda: events.append("serve"),
        )

    assert events == []
    assert not demo.exists()


@pytest.mark.parametrize(
    ("revision_state", "expected_message"),
    (
        ("missing", "revision is unavailable"),
        ("empty", "exactly one revision"),
        ("malformed", "revision"),
        ("multiple", "exactly one revision"),
        ("unknown", "not recognized"),
        ("newer", "not recognized"),
    ),
)
def test_existing_invalid_standard_database_is_never_migrated_or_served(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    revision_state: str,
    expected_message: str,
) -> None:
    root = tmp_path / revision_state
    root.mkdir()
    database = root / "product.sqlite3"
    if revision_state == "malformed":
        database.write_bytes(b"not-a-sqlite-database")
    else:
        with sqlite3.connect(database) as connection:
            if revision_state == "missing":
                connection.execute("CREATE TABLE unrelated (value TEXT NOT NULL)")
                connection.execute(
                    "INSERT INTO unrelated (value) VALUES ('preserve-me')"
                )
            else:
                connection.execute(
                    "CREATE TABLE alembic_version (version_num TEXT NOT NULL)"
                )
                revisions = {
                    "empty": (),
                    "multiple": (
                        "0001_product_baseline",
                        "0002_artifact_index",
                    ),
                    "unknown": ("unrelated_revision",),
                    "newer": ("0006_future_revision",),
                }[revision_state]
                connection.executemany(
                    "INSERT INTO alembic_version (version_num) VALUES (?)",
                    ((revision,) for revision in revisions),
                )

    before = database.read_bytes()
    _runtime_environment(monkeypatch, root=root, mode="standard")
    events: list[str] = []
    monkeypatch.setattr(
        local_module.alembic_command,
        "upgrade",
        lambda *_args, **_kwargs: events.append("migrate"),
    )

    with pytest.raises(LocalWorkspaceError, match=expected_message):
        start_local_backend(
            mode="standard",
            workspace_root=root,
            alembic_config_path=ALEMBIC_CONFIG,
            serve=lambda: events.append("serve"),
        )

    assert database.read_bytes() == before
    assert events == []


def test_existing_approved_standard_revision_migrates_before_serving(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "standard"
    root.mkdir()
    database = root / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database))
    command.upgrade(Config(str(ALEMBIC_CONFIG)), "0001_product_baseline")
    _runtime_environment(monkeypatch, root=root, mode="standard")
    events: list[str] = []

    result = start_local_backend(
        mode="standard",
        workspace_root=root,
        alembic_config_path=ALEMBIC_CONFIG,
        serve=lambda: events.append("serve"),
    )

    assert result.schema_revision == CURRENT_PRODUCT_SCHEMA_REVISION
    assert events == ["serve"]


def test_missing_standard_database_uses_fresh_install_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "standard"
    root.mkdir()
    _runtime_environment(monkeypatch, root=root, mode="standard")
    events: list[str] = []

    result = start_local_backend(
        mode="standard",
        workspace_root=root,
        alembic_config_path=ALEMBIC_CONFIG,
        serve=lambda: events.append("serve"),
    )

    assert result.schema_revision == CURRENT_PRODUCT_SCHEMA_REVISION
    assert (root / "product.sqlite3").is_file()
    assert events == ["serve"]


def test_demo_startup_orders_install_verify_serve_and_failure_never_serves(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "demo"
    _runtime_environment(monkeypatch, root=root, mode="demo")
    events: list[str] = []
    monkeypatch.setattr(
        local_module,
        "install_demo_workspace",
        lambda **_kwargs: events.append("install"),
    )
    monkeypatch.setattr(
        local_module,
        "verify_local_workspace",
        lambda **_kwargs: (
            events.append("verify")
            or LocalWorkspaceVerification(
                mode="demo",
                schema_revision=CURRENT_PRODUCT_SCHEMA_REVISION,
                dataset_id="demo",
                dataset_version=1,
            )
        ),
    )

    start_local_backend(
        mode="demo",
        workspace_root=root,
        alembic_config_path=ALEMBIC_CONFIG,
        demo_source_root=DEMO_SOURCE,
        serve=lambda: events.append("serve"),
    )
    assert events == ["install", "verify", "serve"]

    events.clear()

    def fail_install(**_kwargs) -> None:
        events.append("install")
        raise local_module.DemoWorkspaceError("install failed")

    monkeypatch.setattr(local_module, "install_demo_workspace", fail_install)
    with pytest.raises(LocalWorkspaceError, match="install failed"):
        start_local_backend(
            mode="demo",
            workspace_root=root,
            alembic_config_path=ALEMBIC_CONFIG,
            demo_source_root=DEMO_SOURCE,
            serve=lambda: events.append("serve"),
        )
    assert events == ["install"]


def test_standard_migration_failure_preserves_existing_database_and_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "standard"
    database = _migrated_standard(root, monkeypatch)
    artifact = root / "paper" / "existing.json"
    artifact.write_bytes(b'{"keep":true}\n')
    before_database = database.read_bytes()
    before_artifact = artifact.read_bytes()

    def fail_upgrade(*_args, **_kwargs) -> None:
        raise RuntimeError("injected migration failure")

    monkeypatch.setattr(local_module.alembic_command, "upgrade", fail_upgrade)
    with pytest.raises(LocalWorkspaceError, match="migration failed"):
        prepare_standard_workspace(
            workspace_root=root,
            alembic_config_path=ALEMBIC_CONFIG,
        )

    assert database.read_bytes() == before_database
    assert artifact.read_bytes() == before_artifact


def test_import_app_construction_and_request_never_run_migrations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        local_module.alembic_command,
        "upgrade",
        lambda *_args, **_kwargs: calls.append("migration"),
    )

    app_module = importlib.import_module("el_psy_quant.api.app")
    importlib.reload(app_module)
    application = create_app()
    assert application.openapi()["info"]["title"] == "el-psy-quant"
    assert calls == []


def _compose_files() -> tuple[dict[str, object], dict[str, object]]:
    standard = yaml.safe_load((PROJECT_ROOT / "compose.yaml").read_text("utf-8"))
    demo = yaml.safe_load(
        (PROJECT_ROOT / "compose.demo.yaml").read_text("utf-8")
    )
    return standard, demo


def test_direct_and_effective_compose_identity_volume_root_and_auth_isolation() -> None:
    standard, overlay = _compose_files()
    standard_backend = standard["services"]["backend"]
    standard_web = standard["services"]["web"]
    demo_backend = {
        **standard_backend,
        **overlay["services"]["backend"],
        "environment": {
            **standard_backend["environment"],
            **overlay["services"]["backend"]["environment"],
        },
    }
    demo_web_environment = {
        **standard_web["environment"],
        **overlay["services"]["web"]["environment"],
    }

    assert standard["name"] == "el-psy-quant-mvp"
    assert set(standard["volumes"]) == {"mvp-data"}
    assert standard_backend["volumes"] == ["mvp-data:/data"]
    assert "EL_PSY_QUANT_WORKSPACE_MODE" not in standard_backend["environment"]
    assert "EL_PSY_QUANT_DEMO_WORKSPACE_ROOT" not in standard_backend["environment"]
    assert "demo" not in " ".join(standard_backend.get("command", ())).lower()

    assert overlay["name"] == "el-psy-quant-demo"
    assert set(overlay["volumes"]) == {"demo-data"}
    assert demo_backend["volumes"] == ["demo-data:/data"]
    assert demo_backend["environment"]["EL_PSY_QUANT_WORKSPACE_MODE"] == "demo"
    assert (
        demo_backend["environment"]["EL_PSY_QUANT_DEMO_WORKSPACE_ROOT"]
        == "/data/workspace"
    )
    assert demo_backend["environment"]["EL_PSY_QUANT_PRODUCT_DATABASE_PATH"] == (
        "/data/workspace/product.sqlite3"
    )
    assert demo_backend["command"][:4] == [
        "el-psy-quant",
        "start-local-backend",
        "--mode",
        "demo",
    ]

    for service in (standard_backend, standard_web):
        assert all(str(port).startswith("127.0.0.1:") for port in service["ports"])
    for environment in (
        standard_backend["environment"],
        standard_web["environment"],
    ):
        assert "${EL_PSY_QUANT_FOUNDER_USERNAME:?" in environment[
            "EL_PSY_QUANT_FOUNDER_USERNAME"
        ]
        assert "${EL_PSY_QUANT_FOUNDER_PASSWORD:?" in environment[
            "EL_PSY_QUANT_FOUNDER_PASSWORD"
        ]
    assert standard_web["environment"]["EL_PSY_QUANT_API_ORIGIN"] == (
        "http://backend:8000"
    )
    assert standard_web["environment"][
        "EL_PSY_QUANT_ALLOW_COMPOSE_API_ORIGIN"
    ] == "1"
    assert demo_web_environment["EL_PSY_QUANT_WORKSPACE_MODE"] == "demo"
    assert "volumes" not in standard_web


def test_compose_and_documentation_have_no_standard_volume_reset_helper() -> None:
    inspected_paths = [
        PROJECT_ROOT / "compose.yaml",
        PROJECT_ROOT / "compose.demo.yaml",
        PROJECT_ROOT / "README.md",
        *sorted((PROJECT_ROOT / "docs").rglob("*.md")),
        *sorted((PROJECT_ROOT / "scripts").glob("*")),
    ]
    repository_lines = [
        line.strip()
        for path in inspected_paths
        if path.is_file()
        for line in path.read_text(encoding="utf-8").splitlines()
    ]

    volume_commands = [
        line
        for line in repository_lines
        if line.startswith("docker compose") and "down --volumes" in line
    ]
    assert volume_commands
    assert all(
        "-f compose.yaml -f compose.demo.yaml" in command
        for command in volume_commands
    )
    repository_text = "\n".join(repository_lines)
    assert "mvp-data:/data" in repository_text
    assert (
        "docker compose -f compose.yaml -f compose.demo.yaml down --volumes"
        in repository_text
    )


def test_backend_image_uses_locked_builder_and_runtime_only_final_stage() -> None:
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")
    web_dockerfile = (PROJECT_ROOT / "web" / "Dockerfile").read_text(
        encoding="utf-8"
    )
    runtime_requirements = (
        PROJECT_ROOT / "requirements-runtime.txt"
    ).read_text(encoding="utf-8")
    build_requirements = (
        PROJECT_ROOT / "requirements-build.txt"
    ).read_text(encoding="utf-8")
    project = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    alembic_configuration = (
        PROJECT_ROOT / "alembic.ini"
    ).read_text(encoding="utf-8")

    builder, runtime = dockerfile.split(
        "FROM python:3.11-slim AS runtime",
        maxsplit=1,
    )
    normalized_runtime = " ".join(runtime.replace("\\\n", "").split())
    assert "FROM python:3.11-slim AS builder" in builder
    assert "COPY requirements-build.txt ./" in builder
    assert (
        "python -m pip install --no-cache-dir --requirement "
        "requirements-build.txt"
    ) in builder
    assert "python -m pip wheel --no-cache-dir --no-deps --no-build-isolation" in (
        builder
    )
    assert "COPY requirements-runtime.txt ./" in runtime
    assert (
        "python -m pip install --no-cache-dir --requirement "
        "requirements-runtime.txt"
    ) in runtime
    assert "COPY --from=builder /wheelhouse /wheelhouse" in runtime
    assert (
        "python -m pip install --no-cache-dir --no-deps "
        "/wheelhouse/el_psy_quant-*.whl"
    ) in normalized_runtime
    assert "requirements-build.txt" not in runtime
    assert "hatchling" not in runtime.lower()
    assert "COPY src" not in runtime
    assert "COPY . " not in runtime
    assert "/app/src" not in runtime
    assert "COPY alembic.ini ./" in runtime
    assert (
        "script_location = el_psy_quant.persistence:migrations"
        in alembic_configuration
    )
    assert "%(here)s/src" not in alembic_configuration
    assert "-e ." not in runtime_requirements
    assert "el-psy-quant" not in runtime_requirements
    assert "hatchling" not in runtime_requirements
    assert all(
        "==" in line
        for line in runtime_requirements.splitlines()
        if line and not line.startswith("#")
    )
    assert "hatchling==1.27.0" in build_requirements.splitlines()
    assert all(
        "==" in line
        for line in build_requirements.splitlines()
        if line and not line.startswith("#")
    )
    assert project["build-system"]["requires"] == project["dependency-groups"]["build"]
    assert "RUN npm ci" in web_dockerfile


def test_build_and_runtime_exports_match_lock_and_ci_refuses_lock_drift() -> None:
    generated_runtime = subprocess.run(
        RUNTIME_EXPORT_COMMAND,
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    generated_build = subprocess.run(
        BUILD_EXPORT_COMMAND,
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    committed_runtime = (
        PROJECT_ROOT / "requirements-runtime.txt"
    ).read_text(encoding="utf-8")
    committed_build = (
        PROJECT_ROOT / "requirements-build.txt"
    ).read_text(encoding="utf-8")
    workflow = (
        PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
    ).read_text(encoding="utf-8")
    quality_gate = (PROJECT_ROOT / "scripts" / "check.py").read_text(
        encoding="utf-8"
    )

    assert generated_runtime == committed_runtime
    assert generated_build == committed_build
    assert "uv sync --locked" in workflow
    assert '("uv", "lock", "--check")' in quality_gate
    assert "scripts/check_build_requirements.py" in quality_gate
    assert "scripts/check_runtime_requirements.py" in quality_gate
    assert "scripts/check_packaged_migration_resources.py" in quality_gate
