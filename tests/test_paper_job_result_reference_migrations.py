"""Tests for the focused Sprint 150 result-reference migration."""

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
RECOVERY_REVISION = "0004_paper_job_recovery_audit"
RESULT_REFERENCE_REVISION = "0005_paper_job_result_references"
PORTFOLIO_REVIEW_REVISION = "0006_portfolio_reviews"


def _config() -> Config:
    return Config(str(PROJECT_ROOT / "alembic.ini"))


def _engine(path: Path):
    return create_product_database_engine(
        config=resolve_product_database_config(database_path=path)
    )


def _current(path: Path) -> str | None:
    engine = _engine(path)
    try:
        with engine.connect() as connection:
            return MigrationContext.configure(connection).get_current_revision()
    finally:
        engine.dispose()


def test_exact_result_reference_head_chain() -> None:
    scripts = ScriptDirectory.from_config(_config())

    assert scripts.get_heads() == [PORTFOLIO_REVIEW_REVISION]
    assert scripts.get_revision(PORTFOLIO_REVIEW_REVISION).down_revision == (
        RESULT_REFERENCE_REVISION
    )
    assert scripts.get_revision(RESULT_REFERENCE_REVISION).down_revision == (
        RECOVERY_REVISION
    )


@pytest.mark.parametrize("starting_revision", ("base", RECOVERY_REVISION))
def test_upgrade_adds_exact_one_result_reference_table(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    starting_revision: str,
) -> None:
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    config = _config()
    if starting_revision != "base":
        command.upgrade(config, starting_revision)

    command.upgrade(config, RESULT_REFERENCE_REVISION)

    assert _current(path) == RESULT_REFERENCE_REVISION
    engine = _engine(path)
    try:
        inspector = inspect(engine)
        assert set(inspector.get_table_names()) == {
            "alembic_version",
            "artifact_index_entries",
            "paper_jobs",
            "paper_job_submission_keys",
            "paper_job_attempts",
            "paper_job_result_references",
        }
        columns = inspector.get_columns("paper_job_result_references")
        assert tuple(column["name"] for column in columns) == (
            "record_schema_version",
            "job_id",
            "root_type",
            "artifact_schema_version",
            "result_summary_schema_version",
            "artifact_relative_path",
            "result_summary_relative_path",
            "created_timestamp",
        )
        assert all(column["nullable"] is False for column in columns)
        assert inspector.get_pk_constraint("paper_job_result_references") == {
            "name": "pk_paper_job_result_references",
            "constrained_columns": ["job_id"],
        }
        assert {
            item["name"]: item["column_names"]
            for item in inspector.get_unique_constraints(
                "paper_job_result_references"
            )
        } == {
            "uq_paper_job_result_references_artifact_path": [
                "artifact_relative_path"
            ],
            "uq_paper_job_result_references_summary_path": [
                "result_summary_relative_path"
            ],
        }
        foreign_keys = inspector.get_foreign_keys("paper_job_result_references")
        assert len(foreign_keys) == 1
        assert foreign_keys[0]["referred_table"] == "paper_jobs"
        assert foreign_keys[0]["options"].get("ondelete") == "RESTRICT"
        assert {
            check["name"]
            for check in inspector.get_check_constraints(
                "paper_job_result_references"
            )
        } == {
            "ck_paper_job_result_references_record_schema_version",
            "ck_paper_job_result_references_root_type",
            "ck_paper_job_result_references_artifact_schema_version",
            "ck_paper_job_result_references_summary_schema_version",
            "ck_paper_job_result_references_artifact_path_shape",
            "ck_paper_job_result_references_summary_path_shape",
        }
    finally:
        engine.dispose()


def test_downgrade_removes_only_result_reference_table(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    config = _config()
    command.upgrade(config, RESULT_REFERENCE_REVISION)

    command.downgrade(config, RECOVERY_REVISION)

    assert _current(path) == RECOVERY_REVISION
    engine = _engine(path)
    try:
        assert set(inspect(engine).get_table_names()) == {
            "alembic_version",
            "artifact_index_entries",
            "paper_jobs",
            "paper_job_submission_keys",
            "paper_job_attempts",
        }
    finally:
        engine.dispose()
