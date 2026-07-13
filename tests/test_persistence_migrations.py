"""Tests for the Sprint 145 empty Alembic baseline."""

from io import StringIO
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
ALEMBIC_CONFIG_PATH = PROJECT_ROOT / "alembic.ini"
BASELINE_REVISION = "0001_product_baseline"


def _alembic_config() -> Config:
    return Config(str(ALEMBIC_CONFIG_PATH))


def _current_revision(database_path: Path) -> str | None:
    config = resolve_product_database_config(database_path=database_path)
    engine = create_product_database_engine(config=config)
    try:
        with engine.connect() as connection:
            return MigrationContext.configure(connection).get_current_revision()
    finally:
        engine.dispose()


def test_fresh_database_upgrades_to_empty_baseline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))

    command.upgrade(_alembic_config(), BASELINE_REVISION)

    assert database_path.exists()
    assert _current_revision(database_path) == BASELINE_REVISION
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=database_path)
    )
    try:
        assert set(inspect(engine).get_table_names()) == {"alembic_version"}
    finally:
        engine.dispose()


def test_baseline_revision_remains_unchanged() -> None:
    scripts = ScriptDirectory.from_config(_alembic_config())

    assert scripts.get_revision(BASELINE_REVISION).down_revision is None


def test_offline_upgrade_generates_sql_without_creating_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    output = StringIO()
    alembic_config = _alembic_config()
    alembic_config.output_buffer = output

    command.upgrade(alembic_config, BASELINE_REVISION, sql=True)

    generated_sql = output.getvalue()
    assert "CREATE TABLE alembic_version" in generated_sql
    assert BASELINE_REVISION in generated_sql
    assert not database_path.exists()


def test_baseline_downgrades_deterministically_to_base(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    alembic_config = _alembic_config()
    command.upgrade(alembic_config, BASELINE_REVISION)

    command.downgrade(alembic_config, "base")

    assert _current_revision(database_path) is None
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=database_path)
    )
    try:
        assert set(inspect(engine).get_table_names()) <= {"alembic_version"}
    finally:
        engine.dispose()


def test_migration_configuration_is_independent_of_working_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "product.sqlite3"
    other_working_directory = tmp_path / "working"
    other_working_directory.mkdir()
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    monkeypatch.chdir(other_working_directory)

    command.upgrade(_alembic_config(), BASELINE_REVISION)

    assert _current_revision(database_path) == BASELINE_REVISION
