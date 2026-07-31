"""Authoritative Sprint 167 migration-chain and preservation matrix."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, inspect

from el_psy_quant.persistence import (
    create_product_database_engine,
    resolve_product_database_config,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV
from el_psy_quant.persistence.schema import (
    CURRENT_PRODUCT_SCHEMA_REVISION,
    REQUIRED_PRODUCT_INDEXES,
    REQUIRED_PRODUCT_TABLE_COLUMNS,
    verify_product_schema,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_CONFIG_PATH = PROJECT_ROOT / "alembic.ini"
MIGRATION_CHAIN = (
    "0001_product_baseline",
    "0002_artifact_index",
    "0003_paper_jobs",
    "0004_paper_job_recovery_audit",
    "0005_paper_job_result_references",
    "0006_portfolio_reviews",
    "0007_paper_account_ledger",
    "0008_market_time_foundation",
    "0009_market_time_runtime",
    CURRENT_PRODUCT_SCHEMA_REVISION,
)


def _config() -> Config:
    return Config(str(ALEMBIC_CONFIG_PATH))


def _engine(path: Path) -> Engine:
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


def _populate_revision(engine: Engine, revision: str) -> None:
    with engine.begin() as connection:
        if revision >= "0002":
            connection.exec_driver_sql(
                """
                INSERT INTO artifact_index_entries
                (record_schema_version, artifact_type, artifact_key, root_type,
                 relative_path, source_id)
                VALUES (1, 'research_run_manifest', 'upgrade-artifact', 'research',
                        'upgrade/manifest.json', 'upgrade-source')
                """
            )
        if revision >= "0003":
            connection.exec_driver_sql(
                """
                INSERT INTO paper_jobs
                (record_schema_version, job_id, run_id, status,
                 request_schema_version, request_payload,
                 submitted_timestamp, updated_timestamp)
                VALUES (1, '16700000-0000-4000-8000-000000000001',
                        'upgrade-run', 'succeeded', 1, '{"schema_version":1}',
                        '2026-07-18 00:00:00', '2026-07-18 00:01:00')
                """
            )
        if revision >= "0004":
            connection.exec_driver_sql(
                """
                INSERT INTO paper_job_submission_keys
                (record_schema_version, idempotency_key, job_id,
                 request_schema_version, request_digest, created_timestamp)
                VALUES (1, 'upgrade-key',
                        '16700000-0000-4000-8000-000000000001',
                        1, 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                        '2026-07-18 00:00:00')
                """
            )
            connection.exec_driver_sql(
                """
                INSERT INTO paper_job_attempts
                (record_schema_version, attempt_id, job_id, attempt_number,
                 status, started_timestamp, completed_timestamp, error_code)
                VALUES (1, '16700000-0000-4000-8000-000000000002',
                        '16700000-0000-4000-8000-000000000001', 1,
                        'succeeded', '2026-07-18 00:00:30',
                        '2026-07-18 00:01:00', NULL)
                """
            )
        if revision >= "0005":
            connection.exec_driver_sql(
                """
                INSERT INTO paper_job_result_references
                (record_schema_version, job_id, root_type,
                 artifact_schema_version, result_summary_schema_version,
                 artifact_relative_path, result_summary_relative_path,
                 created_timestamp)
                VALUES (1, '16700000-0000-4000-8000-000000000001', 'paper',
                        1, 1,
                        'jobs/16700000-0000-4000-8000-000000000001/paper/paper_run_artifact.json',
                        'jobs/16700000-0000-4000-8000-000000000001/paper/paper_run_result_summary.json',
                        '2026-07-18 00:01:00')
                """
            )


def _rows(engine: Engine) -> dict[str, tuple[tuple[object, ...], ...]]:
    result: dict[str, tuple[tuple[object, ...], ...]] = {}
    with engine.connect() as connection:
        tables = set(inspect(connection).get_table_names())
        for table_name in REQUIRED_PRODUCT_TABLE_COLUMNS:
            if table_name in tables:
                rows = connection.exec_driver_sql(
                    f'SELECT * FROM "{table_name}" ORDER BY 1, 2'
                ).fetchall()
                result[table_name] = tuple(tuple(row) for row in rows)
    return result


def test_one_exact_linear_head_and_direct_ancestry() -> None:
    scripts = ScriptDirectory.from_config(_config())

    assert scripts.get_heads() == [CURRENT_PRODUCT_SCHEMA_REVISION]
    assert tuple(
        revision.revision
        for revision in scripts.walk_revisions(base="base", head="heads")
    ) == tuple(reversed(MIGRATION_CHAIN))
    for index, revision in enumerate(MIGRATION_CHAIN):
        expected_parent = None if index == 0 else MIGRATION_CHAIN[index - 1]
        script = scripts.get_revision(revision)
        assert script.down_revision == expected_parent
        assert script.branch_labels == set()
        assert script.dependencies is None


@pytest.mark.parametrize("starting_revision", ("base", *MIGRATION_CHAIN[:-1]))
def test_every_historical_revision_upgrades_to_head_and_preserves_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    starting_revision: str,
) -> None:
    database_path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    config = _config()
    if starting_revision != "base":
        command.upgrade(config, starting_revision)
        engine = _engine(database_path)
        try:
            _populate_revision(engine, starting_revision)
            before = _rows(engine)
        finally:
            engine.dispose()
    else:
        before = {}

    command.upgrade(config, "head")

    assert _current(database_path) == CURRENT_PRODUCT_SCHEMA_REVISION
    assert verify_product_schema(database_path) == CURRENT_PRODUCT_SCHEMA_REVISION
    engine = _engine(database_path)
    try:
        after = _rows(engine)
        for table_name, rows in before.items():
            assert after[table_name] == rows
    finally:
        engine.dispose()


def test_populated_head_repeat_upgrade_is_a_no_op_for_rows_and_artifact_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "product.sqlite3"
    artifact = tmp_path / "paper" / "existing-result.json"
    artifact.parent.mkdir()
    artifact.write_bytes(b'{"authoritative":true}\n')
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    command.upgrade(_config(), "head")
    engine = _engine(database_path)
    try:
        _populate_revision(engine, CURRENT_PRODUCT_SCHEMA_REVISION)
        before_rows = _rows(engine)
    finally:
        engine.dispose()
    before_database = database_path.read_bytes()
    before_artifact = artifact.read_bytes()

    command.upgrade(_config(), "head")

    engine = _engine(database_path)
    try:
        assert _rows(engine) == before_rows
    finally:
        engine.dispose()
    assert database_path.read_bytes() == before_database
    assert artifact.read_bytes() == before_artifact


def test_head_has_exact_tables_columns_constraints_foreign_keys_and_indexes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    command.upgrade(_config(), "head")
    engine = _engine(path)
    try:
        inspector = inspect(engine)
        assert set(inspector.get_table_names()) == {
            "alembic_version",
            *REQUIRED_PRODUCT_TABLE_COLUMNS,
        }
        for table_name, expected_columns in REQUIRED_PRODUCT_TABLE_COLUMNS.items():
            assert tuple(
                column["name"] for column in inspector.get_columns(table_name)
            ) == expected_columns
            actual_indexes = {
                item["name"] for item in inspector.get_indexes(table_name)
            }
            assert actual_indexes == set(
                REQUIRED_PRODUCT_INDEXES.get(table_name, ())
            )
        for table_name in (
            "paper_job_submission_keys",
            "paper_job_attempts",
            "paper_job_result_references",
        ):
            foreign_keys = inspector.get_foreign_keys(table_name)
            assert len(foreign_keys) == 1
            assert foreign_keys[0]["referred_table"] == "paper_jobs"
            assert foreign_keys[0]["options"].get("ondelete") == "RESTRICT"
    finally:
        engine.dispose()


def test_offline_head_sql_is_cwd_independent_and_creates_no_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "product.sqlite3"
    working = tmp_path / "other-working-directory"
    working.mkdir()
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    monkeypatch.chdir(working)
    output = StringIO()
    config = _config()
    config.output_buffer = output

    command.upgrade(config, "head", sql=True)

    assert CURRENT_PRODUCT_SCHEMA_REVISION in output.getvalue()
    assert not path.exists()


def test_migration_shape_matches_the_approved_linear_chain() -> None:
    version_root = (
        PROJECT_ROOT
        / "src"
        / "el_psy_quant"
        / "persistence"
        / "migrations"
        / "versions"
    )

    assert tuple(path.stem for path in sorted(version_root.glob("*.py"))) == (
        "0001_product_persistence_baseline",
        "0002_artifact_index",
        "0003_paper_jobs",
        "0004_paper_job_recovery_audit",
        "0005_paper_job_result_references",
        "0006_portfolio_reviews",
        "0007_paper_account_ledger",
        "0008_market_time_foundation",
        "0009_market_time_runtime",
        "0010_strategy_order_risk",
    )
