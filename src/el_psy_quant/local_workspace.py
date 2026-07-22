"""Explicit local workspace preparation, verification, and backend startup."""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig

from el_psy_quant.demo_workspace import (
    DEMO_WORKSPACE_MODE,
    INSTALL_MARKER_FILE_NAME,
    STANDARD_WORKSPACE_MODE,
    WORKSPACE_DESCRIPTOR_FILE_NAME,
    DemoWorkspaceError,
    install_demo_workspace,
    validate_installed_demo_workspace,
)
from el_psy_quant.persistence.schema import (
    CURRENT_PRODUCT_SCHEMA_REVISION,
    ProductSchemaVerificationError,
    read_product_schema_revision,
    verify_product_schema,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV
from el_psy_quant.persistence.migration_resources import (
    MigrationResourceError,
    validate_migration_resources,
)

WorkspaceMode = Literal["standard", "demo"]

_ARTIFACT_ROOT_NAMES = ("research", "evidence", "paper")
_ARTIFACT_ENVIRONMENT = {
    "research": "EL_PSY_QUANT_RESEARCH_ARTIFACT_ROOT",
    "evidence": "EL_PSY_QUANT_EVIDENCE_ARTIFACT_ROOT",
    "paper": "EL_PSY_QUANT_PAPER_ARTIFACT_ROOT",
}


class LocalWorkspaceError(Exception):
    """Raised for one bounded local preparation or verification refusal."""


@dataclass(frozen=True)
class LocalWorkspaceVerification:
    """Bounded successful verification identity."""

    mode: WorkspaceMode
    schema_revision: str
    dataset_id: str | None = None
    dataset_version: int | None = None


def _real_directory(path: Path, *, label: str) -> Path:
    try:
        if path.is_symlink():
            raise LocalWorkspaceError(f"{label} may not be a symlink")
        resolved = path.resolve(strict=True)
        if not resolved.is_dir():
            raise LocalWorkspaceError(f"{label} must be an existing directory")
        return resolved
    except LocalWorkspaceError:
        raise
    except (OSError, RuntimeError) as exc:
        raise LocalWorkspaceError(f"{label} is unavailable") from exc


def _contained_real_directory(root: Path, child: Path, *, label: str) -> Path:
    resolved = _real_directory(child, label=label)
    if not resolved.is_relative_to(root):
        raise LocalWorkspaceError(f"{label} must be contained by the workspace root")
    return resolved


def verify_local_workspace(
    *,
    mode: WorkspaceMode,
    workspace_root: str | Path,
) -> LocalWorkspaceVerification:
    """Verify one Standard or Demo workspace without creating or changing state."""
    if mode not in (STANDARD_WORKSPACE_MODE, DEMO_WORKSPACE_MODE):
        raise LocalWorkspaceError("workspace mode must be standard or demo")
    if not isinstance(workspace_root, (str, Path)) or not str(workspace_root).strip():
        raise LocalWorkspaceError("workspace root must be an explicit local path")

    root_path = Path(workspace_root)
    root = _real_directory(root_path, label="workspace root")
    database_path = root_path / "product.sqlite3"
    try:
        if database_path.is_symlink():
            raise LocalWorkspaceError("product database may not be a symlink")
        revision = verify_product_schema(database_path)
    except ProductSchemaVerificationError as exc:
        raise LocalWorkspaceError(str(exc)) from exc
    for name in _ARTIFACT_ROOT_NAMES:
        _contained_real_directory(
            root,
            root_path / name,
            label=f"{name} artifact root",
        )

    marker = root_path / INSTALL_MARKER_FILE_NAME
    descriptor = root_path / WORKSPACE_DESCRIPTOR_FILE_NAME
    if mode == STANDARD_WORKSPACE_MODE:
        if marker.exists() or descriptor.exists():
            raise LocalWorkspaceError(
                "Standard workspace may not contain Demo installation identity"
            )
        return LocalWorkspaceVerification(
            mode=STANDARD_WORKSPACE_MODE,
            schema_revision=revision,
        )

    try:
        demo_descriptor = validate_installed_demo_workspace(root_path).to_dict()
    except DemoWorkspaceError as exc:
        raise LocalWorkspaceError(str(exc)) from exc
    return LocalWorkspaceVerification(
        mode=DEMO_WORKSPACE_MODE,
        schema_revision=revision,
        dataset_id=demo_descriptor["dataset_id"],
        dataset_version=demo_descriptor["dataset_version"],
    )


@contextmanager
def _database_environment(database_path: Path):
    previous = os.environ.get(PRODUCT_DATABASE_PATH_ENV)
    os.environ[PRODUCT_DATABASE_PATH_ENV] = str(database_path)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(PRODUCT_DATABASE_PATH_ENV, None)
        else:
            os.environ[PRODUCT_DATABASE_PATH_ENV] = previous


def upgrade_product_database(
    *,
    database_path: Path,
    alembic_config_path: Path,
) -> None:
    """Run the supported forward-only Alembic upgrade for one explicit database."""
    try:
        alembic_config = preflight_product_migration_resources(
            alembic_config_path=alembic_config_path
        )
        if database_path.is_symlink():
            raise LocalWorkspaceError("product database may not be a symlink")
        try:
            database_exists = database_path.exists()
        except OSError as exc:
            raise LocalWorkspaceError("product database is unavailable") from exc
        if database_exists:
            try:
                read_product_schema_revision(database_path)
            except ProductSchemaVerificationError as exc:
                raise LocalWorkspaceError(str(exc)) from exc
        with _database_environment(database_path):
            alembic_command.upgrade(alembic_config, "head")
    except LocalWorkspaceError:
        raise
    except Exception as exc:
        raise LocalWorkspaceError("product database migration failed") from exc


def preflight_product_migration_resources(
    *, alembic_config_path: Path
) -> AlembicConfig:
    """Resolve and validate the installed migration authority without database I/O."""
    try:
        resolved = alembic_config_path.resolve(strict=True)
        if not resolved.is_file():
            raise LocalWorkspaceError("Alembic configuration is unavailable")
        config = AlembicConfig(str(resolved))
        validate_migration_resources(config)
        return config
    except LocalWorkspaceError:
        raise
    except MigrationResourceError as exc:
        raise LocalWorkspaceError(
            "product migration resources are unavailable"
        ) from exc
    except (OSError, RuntimeError, ValueError) as exc:
        raise LocalWorkspaceError("Alembic configuration is unavailable") from exc


def prepare_standard_workspace(
    *,
    workspace_root: Path,
    alembic_config_path: Path,
) -> None:
    """Create only fixed artifact directories and forward-upgrade Standard data."""
    root = _real_directory(workspace_root, label="workspace root")
    try:
        for name in _ARTIFACT_ROOT_NAMES:
            child = workspace_root / name
            child.mkdir(exist_ok=True)
            _contained_real_directory(root, child, label=f"{name} artifact root")
    except LocalWorkspaceError:
        raise
    except OSError as exc:
        raise LocalWorkspaceError(
            "Standard artifact roots could not be prepared"
        ) from exc
    upgrade_product_database(
        database_path=workspace_root / "product.sqlite3",
        alembic_config_path=alembic_config_path,
    )


def _require_exact_runtime_configuration(
    *,
    mode: WorkspaceMode,
    workspace_root: Path,
) -> None:
    expected = {
        PRODUCT_DATABASE_PATH_ENV: workspace_root / "product.sqlite3",
        **{
            environment_name: workspace_root / child_name
            for child_name, environment_name in _ARTIFACT_ENVIRONMENT.items()
        },
    }
    for environment_name, path in expected.items():
        configured = os.getenv(environment_name)
        if configured is None:
            raise LocalWorkspaceError(
                f"{environment_name} is required for local backend startup"
            )
        try:
            if Path(configured).resolve(strict=False) != path.resolve(strict=False):
                raise LocalWorkspaceError(
                    f"{environment_name} does not match the selected workspace"
                )
        except (OSError, RuntimeError) as exc:
            raise LocalWorkspaceError(
                f"{environment_name} is invalid"
            ) from exc
    configured_mode = os.getenv("EL_PSY_QUANT_WORKSPACE_MODE", "standard")
    if configured_mode != mode:
        raise LocalWorkspaceError(
            "EL_PSY_QUANT_WORKSPACE_MODE does not match the selected workspace"
        )
    demo_root = os.getenv("EL_PSY_QUANT_DEMO_WORKSPACE_ROOT")
    if mode == DEMO_WORKSPACE_MODE:
        if demo_root is None or Path(demo_root).resolve(strict=False) != workspace_root.resolve(
            strict=False
        ):
            raise LocalWorkspaceError(
                "EL_PSY_QUANT_DEMO_WORKSPACE_ROOT does not match the selected workspace"
            )
    elif demo_root is not None:
        raise LocalWorkspaceError(
            "Standard backend startup may not configure a Demo workspace root"
        )


def _exec_uvicorn() -> None:
    os.execv(
        sys.executable,
        [
            sys.executable,
            "-m",
            "uvicorn",
            "el_psy_quant.api.app:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ],
    )


def start_local_backend(
    *,
    mode: WorkspaceMode,
    workspace_root: Path,
    alembic_config_path: Path,
    demo_source_root: Path | None = None,
    serve: Callable[[], None] = _exec_uvicorn,
) -> LocalWorkspaceVerification:
    """Prepare, verify, and only then replace the process with Uvicorn."""
    _require_exact_runtime_configuration(mode=mode, workspace_root=workspace_root)
    preflight_product_migration_resources(
        alembic_config_path=alembic_config_path
    )
    if mode == STANDARD_WORKSPACE_MODE:
        if demo_source_root is not None:
            raise LocalWorkspaceError(
                "Standard backend startup may not configure a Demo source"
            )
        prepare_standard_workspace(
            workspace_root=workspace_root,
            alembic_config_path=alembic_config_path,
        )
    elif mode == DEMO_WORKSPACE_MODE:
        if demo_source_root is None:
            raise LocalWorkspaceError(
                "Demo source root is required for Demo backend startup"
            )
        try:
            install_demo_workspace(
                source_root=demo_source_root,
                workspace_root=workspace_root,
                workspace_mode=mode,
                alembic_config_path=alembic_config_path,
            )
        except DemoWorkspaceError as exc:
            raise LocalWorkspaceError(str(exc)) from exc
    else:
        raise LocalWorkspaceError("workspace mode must be standard or demo")

    result = verify_local_workspace(mode=mode, workspace_root=workspace_root)
    serve()
    return result


def format_verification_success(result: LocalWorkspaceVerification) -> str:
    """Format one bounded, path-free verification success message."""
    message = (
        f"{result.mode} workspace verified at schema "
        f"{CURRENT_PRODUCT_SCHEMA_REVISION}"
    )
    if result.mode == DEMO_WORKSPACE_MODE:
        message += f"; dataset {result.dataset_id} v{result.dataset_version}"
    return message


__all__ = [
    "LocalWorkspaceError",
    "LocalWorkspaceVerification",
    "format_verification_success",
    "prepare_standard_workspace",
    "preflight_product_migration_resources",
    "start_local_backend",
    "upgrade_product_database",
    "verify_local_workspace",
]
