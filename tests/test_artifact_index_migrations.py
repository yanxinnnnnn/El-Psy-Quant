"""Tests for the focused Sprint 146 artifact-index migration."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from el_psy_quant.persistence import (
    create_product_database_engine,
    resolve_product_database_config,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_INDEX_REVISION = "0002_artifact_index"
BASELINE_REVISION = "0001_product_baseline"


def _alembic_config() -> Config:
    return Config(str(PROJECT_ROOT / "alembic.ini"))


def _engine(database_path: Path):
    return create_product_database_engine(
        config=resolve_product_database_config(database_path=database_path)
    )


def _current_revision(database_path: Path) -> str | None:
    engine = _engine(database_path)
    try:
        with engine.connect() as connection:
            return MigrationContext.configure(connection).get_current_revision()
    finally:
        engine.dispose()


def test_revision_is_directly_after_unchanged_baseline() -> None:
    scripts = ScriptDirectory.from_config(_alembic_config())

    assert (
        scripts.get_revision(ARTIFACT_INDEX_REVISION).down_revision
        == BASELINE_REVISION
    )
    assert scripts.get_revision(BASELINE_REVISION).down_revision is None


@pytest.mark.parametrize("starting_revision", ("base", BASELINE_REVISION))
def test_upgrade_creates_exact_table_and_constraints(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    starting_revision: str,
) -> None:
    database_path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    config = _alembic_config()
    if starting_revision != "base":
        command.upgrade(config, starting_revision)

    command.upgrade(config, ARTIFACT_INDEX_REVISION)

    assert _current_revision(database_path) == ARTIFACT_INDEX_REVISION
    engine = _engine(database_path)
    try:
        inspector = inspect(engine)
        assert set(inspector.get_table_names()) == {
            "alembic_version",
            "artifact_index_entries",
        }
        columns = inspector.get_columns("artifact_index_entries")
        assert tuple(column["name"] for column in columns) == (
            "record_schema_version",
            "artifact_type",
            "artifact_key",
            "root_type",
            "relative_path",
            "source_id",
        )
        assert all(column["nullable"] is False for column in columns)
        assert inspector.get_pk_constraint("artifact_index_entries") == {
            "constrained_columns": ["artifact_type", "artifact_key"],
            "name": "pk_artifact_index_entries",
        }
        unique_constraints = inspector.get_unique_constraints("artifact_index_entries")
        assert unique_constraints == [
            {
                "name": "uq_artifact_index_root_locator",
                "column_names": ["root_type", "relative_path"],
            }
        ]
        check_names = {
            item["name"]
            for item in inspector.get_check_constraints("artifact_index_entries")
        }
        assert check_names == {
            "ck_artifact_index_artifact_type",
            "ck_artifact_index_root_type",
            "ck_artifact_index_schema_version",
            "ck_artifact_index_type_root_mapping",
        }
    finally:
        engine.dispose()


def test_downgrade_removes_only_artifact_index(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    config = _alembic_config()
    command.upgrade(config, ARTIFACT_INDEX_REVISION)

    command.downgrade(config, BASELINE_REVISION)

    assert _current_revision(database_path) == BASELINE_REVISION
    engine = _engine(database_path)
    try:
        assert set(inspect(engine).get_table_names()) == {"alembic_version"}
    finally:
        engine.dispose()
