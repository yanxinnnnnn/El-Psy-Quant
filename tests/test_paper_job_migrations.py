"""Tests for the focused Sprint 147 paper-jobs migration."""

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
BASELINE_REVISION = "0001_product_baseline"
ARTIFACT_INDEX_REVISION = "0002_artifact_index"
PAPER_JOBS_REVISION = "0003_paper_jobs"
RECOVERY_AUDIT_REVISION = "0004_paper_job_recovery_audit"
RESULT_REFERENCE_REVISION = "0005_paper_job_result_references"


def _config() -> Config:
    return Config(str(PROJECT_ROOT / "alembic.ini"))


def _engine(database_path: Path):
    return create_product_database_engine(
        config=resolve_product_database_config(database_path=database_path)
    )


def _current(database_path: Path) -> str | None:
    engine = _engine(database_path)
    try:
        with engine.connect() as connection:
            return MigrationContext.configure(connection).get_current_revision()
    finally:
        engine.dispose()


def test_exact_migration_chain() -> None:
    scripts = ScriptDirectory.from_config(_config())

    assert scripts.get_heads() == [RESULT_REFERENCE_REVISION]
    assert scripts.get_revision(RESULT_REFERENCE_REVISION).down_revision == (
        RECOVERY_AUDIT_REVISION
    )
    assert scripts.get_revision(RECOVERY_AUDIT_REVISION).down_revision == (
        PAPER_JOBS_REVISION
    )
    assert scripts.get_revision(PAPER_JOBS_REVISION).down_revision == (
        ARTIFACT_INDEX_REVISION
    )
    assert scripts.get_revision(ARTIFACT_INDEX_REVISION).down_revision == (
        BASELINE_REVISION
    )
    assert scripts.get_revision(BASELINE_REVISION).down_revision is None


@pytest.mark.parametrize("starting_revision", ("base", ARTIFACT_INDEX_REVISION))
def test_upgrade_creates_only_approved_tables_and_exact_paper_job_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    starting_revision: str,
) -> None:
    database_path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    config = _config()
    if starting_revision != "base":
        command.upgrade(config, starting_revision)

    command.upgrade(config, PAPER_JOBS_REVISION)

    assert _current(database_path) == PAPER_JOBS_REVISION
    engine = _engine(database_path)
    try:
        inspector = inspect(engine)
        assert set(inspector.get_table_names()) == {
            "alembic_version",
            "artifact_index_entries",
            "paper_jobs",
        }
        columns = inspector.get_columns("paper_jobs")
        assert tuple(column["name"] for column in columns) == (
            "record_schema_version",
            "job_id",
            "run_id",
            "status",
            "request_schema_version",
            "request_payload",
            "submitted_timestamp",
            "updated_timestamp",
        )
        assert all(column["nullable"] is False for column in columns)
        assert all(column["default"] is None for column in columns)
        assert inspector.get_pk_constraint("paper_jobs") == {
            "constrained_columns": ["job_id"],
            "name": "pk_paper_jobs",
        }
        assert inspector.get_unique_constraints("paper_jobs") == [
            {"name": "uq_paper_jobs_run_id", "column_names": ["run_id"]}
        ]
        assert {
            check["name"] for check in inspector.get_check_constraints("paper_jobs")
        } == {
            "ck_paper_jobs_record_schema_version",
            "ck_paper_jobs_request_schema_version",
            "ck_paper_jobs_status",
        }
        forbidden_fragments = {
            "result",
            "error",
            "retry",
            "attempt",
            "idempotency",
            "lifecycle",
            "auth",
            "user",
            "worker",
            "lease",
            "heartbeat",
            "broker",
            "capital",
        }
        names = set(inspector.get_table_names()) | {
            column["name"] for column in columns
        }
        assert all(
            fragment not in name for fragment in forbidden_fragments for name in names
        )
    finally:
        engine.dispose()


def test_downgrade_to_artifact_index_removes_only_paper_jobs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    config = _config()
    command.upgrade(config, "head")

    command.downgrade(config, ARTIFACT_INDEX_REVISION)

    assert _current(database_path) == ARTIFACT_INDEX_REVISION
    engine = _engine(database_path)
    try:
        assert set(inspect(engine).get_table_names()) == {
            "alembic_version",
            "artifact_index_entries",
        }
    finally:
        engine.dispose()
