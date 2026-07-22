"""Packaged Alembic resource discovery and fail-closed validation coverage."""

from __future__ import annotations

import shutil
from importlib import resources
from pathlib import Path

import pytest
from alembic.config import Config

import el_psy_quant.persistence.migration_resources as resource_module
from el_psy_quant.persistence.migration_resources import (
    ALEMBIC_SCRIPT_LOCATION,
    MIGRATION_RESOURCE_DIRECTORY,
    MIGRATION_RESOURCE_PACKAGE,
    MigrationResourceError,
    REQUIRED_MIGRATION_RESOURCE_PATHS,
    validate_migration_resources,
)
from el_psy_quant.persistence.schema import CURRENT_PRODUCT_SCHEMA_REVISION

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_CONFIG = PROJECT_ROOT / "alembic.ini"


def test_packaged_resource_resolver_exposes_exact_tree_and_head() -> None:
    config = Config(str(ALEMBIC_CONFIG))
    root = resources.files(MIGRATION_RESOURCE_PACKAGE).joinpath(
        MIGRATION_RESOURCE_DIRECTORY
    )

    scripts = validate_migration_resources(config)

    assert config.get_alembic_option("script_location") == ALEMBIC_SCRIPT_LOCATION
    assert all(
        root.joinpath(*Path(path).parts).is_file()
        for path in REQUIRED_MIGRATION_RESOURCE_PATHS
    )
    assert scripts.get_heads() == [CURRENT_PRODUCT_SCHEMA_REVISION]


def test_packaged_resource_resolver_refuses_incomplete_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = (
        PROJECT_ROOT / "src" / "el_psy_quant" / "persistence" / "migrations"
    )
    incomplete = tmp_path / "persistence"
    shutil.copytree(source, incomplete / "migrations")
    (incomplete / "migrations" / "env.py").unlink()
    monkeypatch.setattr(resource_module.resources, "files", lambda _package: incomplete)

    with pytest.raises(MigrationResourceError, match="incomplete"):
        validate_migration_resources(Config(str(ALEMBIC_CONFIG)))


def test_packaged_resource_resolver_refuses_head_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class MismatchedScripts:
        def get_heads(self) -> list[str]:
            return ["0007_unexpected_head"]

    monkeypatch.setattr(
        resource_module.ScriptDirectory,
        "from_config",
        lambda _config: MismatchedScripts(),
    )

    with pytest.raises(MigrationResourceError, match="head"):
        validate_migration_resources(Config(str(ALEMBIC_CONFIG)))
