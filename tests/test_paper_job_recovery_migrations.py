"""Tests for the focused Sprint 149 recovery-audit migration."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from el_psy_quant.persistence import (
    create_product_database_engine,
    resolve_product_database_config,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAPER_JOBS_REVISION = "0003_paper_jobs"
RECOVERY_AUDIT_REVISION = "0004_paper_job_recovery_audit"


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


@pytest.mark.parametrize("starting_revision", ("base", PAPER_JOBS_REVISION))
def test_upgrade_adds_exact_recovery_audit_tables(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    starting_revision: str,
) -> None:
    database_path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    config = _config()
    if starting_revision != "base":
        command.upgrade(config, starting_revision)

    command.upgrade(config, "head")

    assert _current(database_path) == RECOVERY_AUDIT_REVISION
    engine = _engine(database_path)
    try:
        inspector = inspect(engine)
        assert set(inspector.get_table_names()) == {
            "alembic_version",
            "artifact_index_entries",
            "paper_jobs",
            "paper_job_submission_keys",
            "paper_job_attempts",
        }
        key_columns = inspector.get_columns("paper_job_submission_keys")
        assert tuple(column["name"] for column in key_columns) == (
            "record_schema_version",
            "idempotency_key",
            "job_id",
            "request_schema_version",
            "request_digest",
            "created_timestamp",
        )
        attempt_columns = inspector.get_columns("paper_job_attempts")
        assert tuple(column["name"] for column in attempt_columns) == (
            "record_schema_version",
            "attempt_id",
            "job_id",
            "attempt_number",
            "status",
            "started_timestamp",
            "completed_timestamp",
            "error_code",
        )
        assert all(column["nullable"] is False for column in key_columns)
        assert [column["nullable"] for column in attempt_columns] == [
            False,
            False,
            False,
            False,
            False,
            False,
            True,
            True,
        ]
        assert inspector.get_pk_constraint("paper_job_submission_keys")[
            "constrained_columns"
        ] == ["idempotency_key"]
        assert inspector.get_pk_constraint("paper_job_attempts")[
            "constrained_columns"
        ] == ["attempt_id"]
        assert inspector.get_unique_constraints("paper_job_submission_keys") == [
            {
                "name": "uq_paper_job_submission_keys_job_id",
                "column_names": ["job_id"],
            }
        ]
        assert inspector.get_unique_constraints("paper_job_attempts") == [
            {
                "name": "uq_paper_job_attempts_job_number",
                "column_names": ["job_id", "attempt_number"],
            }
        ]
        for table in ("paper_job_submission_keys", "paper_job_attempts"):
            foreign_keys = inspector.get_foreign_keys(table)
            assert len(foreign_keys) == 1
            assert foreign_keys[0]["referred_table"] == "paper_jobs"
            assert foreign_keys[0]["options"].get("ondelete") == "RESTRICT"
    finally:
        engine.dispose()


def test_downgrade_removes_only_sprint_149_tables(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    config = _config()
    command.upgrade(config, "head")

    command.downgrade(config, PAPER_JOBS_REVISION)

    assert _current(database_path) == PAPER_JOBS_REVISION
    engine = _engine(database_path)
    try:
        assert set(inspect(engine).get_table_names()) == {
            "alembic_version",
            "artifact_index_entries",
            "paper_jobs",
        }
    finally:
        engine.dispose()
