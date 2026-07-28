"""Exercise the built wheel's installed Alembic authority outside the source tree."""

from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from contextlib import closing
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WHEEL_MIGRATION_ROOT = "el_psy_quant/persistence/migrations"
EXPECTED_MIGRATION_RESOURCES = (
    f"{WHEEL_MIGRATION_ROOT}/env.py",
    f"{WHEEL_MIGRATION_ROOT}/script.py.mako",
    f"{WHEEL_MIGRATION_ROOT}/versions/0001_product_persistence_baseline.py",
    f"{WHEEL_MIGRATION_ROOT}/versions/0002_artifact_index.py",
    f"{WHEEL_MIGRATION_ROOT}/versions/0003_paper_jobs.py",
    f"{WHEEL_MIGRATION_ROOT}/versions/0004_paper_job_recovery_audit.py",
    f"{WHEEL_MIGRATION_ROOT}/versions/0005_paper_job_result_references.py",
    f"{WHEEL_MIGRATION_ROOT}/versions/0006_portfolio_reviews.py",
    f"{WHEEL_MIGRATION_ROOT}/versions/0007_paper_account_ledger.py",
    f"{WHEEL_MIGRATION_ROOT}/versions/0008_market_time_foundation.py",
    f"{WHEEL_MIGRATION_ROOT}/versions/0009_market_time_runtime.py",
)
EXPECTED_HEAD_OUTPUT = "0009_market_time_runtime (head)"
EXPECTED_PRODUCT_TABLES = {
    "alembic_version",
    "artifact_index_entries",
    "market_data_events",
    "market_data_replay_events",
    "market_data_replays",
    "paper_account_creation_keys",
    "paper_account_events",
    "paper_account_position_projections",
    "paper_account_projections",
    "paper_account_reconciliations",
    "paper_account_snapshots",
    "paper_accounts",
    "paper_cash_ledger_entries",
    "paper_jobs",
    "paper_job_submission_keys",
    "paper_job_attempts",
    "paper_job_result_references",
    "paper_position_ledger_entries",
    "portfolio_reviews",
    "trading_calendars",
    "trading_sessions",
}
EXPECTED_MARKET_TIME_TABLES = {
    "trading_calendars",
    "trading_sessions",
}
EXPECTED_MARKET_TIME_RUNTIME_TABLES = {
    "market_data_events",
    "market_data_replay_events",
    "market_data_replays",
}
EXPECTED_0007_TABLES = EXPECTED_PRODUCT_TABLES - {
    "alembic_version",
    "artifact_index_entries",
    "paper_jobs",
    "paper_job_submission_keys",
    "paper_job_attempts",
    "paper_job_result_references",
    *EXPECTED_MARKET_TIME_TABLES,
    *EXPECTED_MARKET_TIME_RUNTIME_TABLES,
}
EXPECTED_PAPER_ACCOUNT_TABLES = EXPECTED_0007_TABLES - {
    "portfolio_reviews",
}
EXPECTED_PORTFOLIO_REVIEW_COLUMNS = (
    "record_schema_version",
    "review_id",
    "status",
    "source_schema_version",
    "source_id",
    "source_digest",
    "source_relative_path",
    "baseline_scenario_id",
    "baseline_scenario_digest",
    "proposed_scenario_id",
    "proposed_scenario_digest",
    "proposed_component_id",
    "analysis_schema_version",
    "analysis_digest",
    "analysis_relative_path",
    "create_idempotency_key",
    "create_command_digest",
    "created_by",
    "created_timestamp",
    "decision_schema_version",
    "decision_id",
    "decision_digest",
    "decision_relative_path",
    "decision_idempotency_key",
    "decision_command_digest",
    "outcome",
    "reviewed_by",
    "reviewed_timestamp",
    "version",
    "updated_timestamp",
)


class GateError(Exception):
    """Raised when the installed-wheel migration gate fails."""


def _run(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _installed_environment(target: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(target)
    environment["PYTHONNOUSERSITE"] = "1"
    return environment


def _run_installed_python(
    target: Path,
    arguments: list[str],
    *,
    cwd: Path,
    database_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = _installed_environment(target)
    if database_path is not None:
        environment["EL_PSY_QUANT_PRODUCT_DATABASE_PATH"] = str(database_path)
    return _run(
        [sys.executable, *arguments],
        cwd=cwd,
        environment=environment,
    )


def _assert_installed_import(target: Path, working: Path) -> None:
    result = _run_installed_python(
        target,
        [
            "-c",
            (
                "from pathlib import Path; import el_psy_quant; "
                "print(Path(el_psy_quant.__file__).resolve())"
            ),
        ],
        cwd=working,
    )
    imported = Path(result.stdout.strip())
    if not imported.is_relative_to(target.resolve()):
        raise GateError("installed-wheel probe imported repository source")


def _wheel_resources(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
    migration_files = tuple(
        sorted(
            name
            for name in names
            if name.startswith(f"{WHEEL_MIGRATION_ROOT}/")
            and not name.endswith("/")
        )
    )
    if migration_files != tuple(sorted(EXPECTED_MIGRATION_RESOURCES)):
        raise GateError("wheel migration resources do not match the approved tree")
    if any(names.count(path) != 1 for path in EXPECTED_MIGRATION_RESOURCES):
        raise GateError("wheel migration resources are duplicated")


def _installed_resources(target: Path) -> None:
    root = target / Path(WHEEL_MIGRATION_ROOT)
    installed = tuple(
        sorted(
            path.relative_to(target).as_posix()
            for path in root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )
    )
    if installed != tuple(sorted(EXPECTED_MIGRATION_RESOURCES)):
        raise GateError("installed migration resources do not match the wheel")


def _alembic(
    target: Path,
    config: Path,
    working: Path,
    *arguments: str,
    database_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return _run_installed_python(
        target,
        ["-m", "alembic", "-c", str(config), *arguments],
        cwd=working,
        database_path=database_path,
    )


def _tables(connection: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        if not row[0].startswith("sqlite_")
    }


def _rows(
    connection: sqlite3.Connection, tables: set[str]
) -> dict[str, tuple[tuple[object, ...], ...]]:
    return {
        table: tuple(
            tuple(row)
            for row in connection.execute(
                f'SELECT * FROM "{table}" ORDER BY rowid'
            ).fetchall()
        )
        for table in tables
        if table != "alembic_version"
    }


def _verify_fresh_upgrade(
    target: Path, config: Path, working: Path, database: Path
) -> None:
    _alembic(
        target,
        config,
        working,
        "upgrade",
        "head",
        database_path=database,
    )
    with closing(sqlite3.connect(database)) as connection:
        revision_rows = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchall()
        if revision_rows != [("0009_market_time_runtime",)]:
            raise GateError("fresh installed-wheel upgrade did not reach head")
        if _tables(connection) != EXPECTED_PRODUCT_TABLES:
            raise GateError("fresh installed-wheel upgrade created an invalid schema")


def _verify_0005_upgrade(
    target: Path, config: Path, working: Path, database: Path
) -> None:
    _alembic(
        target,
        config,
        working,
        "upgrade",
        "0005_paper_job_result_references",
        database_path=database,
    )
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            "CREATE TABLE preserved_gate_data (identity TEXT PRIMARY KEY, value TEXT)"
        )
        connection.execute(
            "INSERT INTO preserved_gate_data VALUES ('existing', 'preserve-me')"
        )
        connection.execute(
            """
            INSERT INTO artifact_index_entries
            (record_schema_version, artifact_type, artifact_key, root_type,
             relative_path, source_id)
            VALUES (1, 'research_run_manifest', 'wheel-gate', 'research',
                    'wheel-gate/manifest.json', 'wheel-gate-source')
            """
        )
        connection.commit()
        before_tables = _tables(connection)
        before_rows = _rows(connection, before_tables)

    _alembic(
        target,
        config,
        working,
        "upgrade",
        "head",
        database_path=database,
    )

    with closing(sqlite3.connect(database)) as connection:
        if connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchall() != [("0009_market_time_runtime",)]:
            raise GateError("installed-wheel 0005 upgrade did not reach 0009")
        if _tables(connection) != (
            before_tables
            | EXPECTED_0007_TABLES
            | EXPECTED_MARKET_TIME_TABLES
            | EXPECTED_MARKET_TIME_RUNTIME_TABLES
        ):
            raise GateError("installed-wheel 0005 upgrade changed unrelated tables")
        if _rows(connection, before_tables) != before_rows:
            raise GateError("installed-wheel 0005 upgrade changed existing data")
        columns = tuple(
            row[1]
            for row in connection.execute(
                'PRAGMA table_info("portfolio_reviews")'
            ).fetchall()
        )
        if columns != EXPECTED_PORTFOLIO_REVIEW_COLUMNS:
            raise GateError("installed-wheel 0006 table does not match the schema")


def _verify_0006_upgrade(
    target: Path, config: Path, working: Path, database: Path
) -> None:
    _alembic(
        target,
        config,
        working,
        "upgrade",
        "0006_portfolio_reviews",
        database_path=database,
    )
    source_digest = "a" * 64
    analysis_digest = "b" * 64
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            """
            INSERT INTO portfolio_reviews (
                record_schema_version, review_id, status,
                source_schema_version, source_id, source_digest,
                source_relative_path, baseline_scenario_id,
                baseline_scenario_digest, proposed_scenario_id,
                proposed_scenario_digest, proposed_component_id,
                analysis_schema_version, analysis_digest,
                analysis_relative_path, create_idempotency_key,
                create_command_digest, created_by, created_timestamp,
                decision_schema_version, decision_id, decision_digest,
                decision_relative_path, decision_idempotency_key,
                decision_command_digest, outcome, reviewed_by,
                reviewed_timestamp, version, updated_timestamp
            ) VALUES (
                1, 'packaged-upgrade-review', 'awaiting_decision',
                1, 'packaged-upgrade-source', ?, ?,
                'packaged-baseline', ?, 'packaged-proposed', ?,
                'packaged-component', 1, ?, ?,
                'packaged-upgrade-create', ?, 'packaged-gate',
                '2026-07-26 00:00:00',
                NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
                1, '2026-07-26 00:00:00'
            )
            """,
            (
                source_digest,
                (
                    "portfolio-reviews/sources/"
                    f"{source_digest}/source.json"
                ),
                "c" * 64,
                "d" * 64,
                analysis_digest,
                (
                    "portfolio-reviews/reviews/"
                    f"{analysis_digest}/analysis.json"
                ),
                "e" * 64,
            ),
        )
        connection.execute(
            "CREATE TABLE preserved_0006_gate_data "
            "(identity TEXT PRIMARY KEY, value TEXT)"
        )
        connection.execute(
            "INSERT INTO preserved_0006_gate_data "
            "VALUES ('existing', 'preserve-me')"
        )
        connection.commit()
        before_tables = _tables(connection)
        before_rows = _rows(connection, before_tables)

    _alembic(
        target,
        config,
        working,
        "upgrade",
        "head",
        database_path=database,
    )

    with closing(sqlite3.connect(database)) as connection:
        if connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchall() != [("0009_market_time_runtime",)]:
            raise GateError("installed-wheel 0006 upgrade did not reach 0009")
        if _tables(connection) != (
            before_tables
            | EXPECTED_PAPER_ACCOUNT_TABLES
            | EXPECTED_MARKET_TIME_TABLES
            | EXPECTED_MARKET_TIME_RUNTIME_TABLES
        ):
            raise GateError("installed-wheel 0006 upgrade changed unrelated tables")
        if _rows(connection, before_tables) != before_rows:
            raise GateError("installed-wheel 0006 upgrade changed existing data")
        if connection.execute(
            "SELECT COUNT(*) FROM paper_accounts"
        ).fetchone() != (0,):
            raise GateError("installed-wheel 0006 upgrade seeded Paper Accounts")


def _verify_0007_upgrade(
    target: Path, config: Path, working: Path, database: Path
) -> None:
    _alembic(
        target,
        config,
        working,
        "upgrade",
        "0007_paper_account_ledger",
        database_path=database,
    )
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            "CREATE TABLE preserved_0007_gate_data "
            "(identity TEXT PRIMARY KEY, value TEXT)"
        )
        connection.execute(
            "INSERT INTO preserved_0007_gate_data "
            "VALUES ('existing', 'preserve-me')"
        )
        connection.commit()
        before_tables = _tables(connection)
        before_rows = _rows(connection, before_tables)

    _alembic(
        target,
        config,
        working,
        "upgrade",
        "head",
        database_path=database,
    )

    with closing(sqlite3.connect(database)) as connection:
        if connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchall() != [("0009_market_time_runtime",)]:
            raise GateError("installed-wheel 0007 upgrade did not reach 0009")
        if _tables(connection) != (
            before_tables
            | EXPECTED_MARKET_TIME_TABLES
            | EXPECTED_MARKET_TIME_RUNTIME_TABLES
        ):
            raise GateError("installed-wheel 0007 upgrade changed unrelated tables")
        if _rows(connection, before_tables) != before_rows:
            raise GateError("installed-wheel 0007 upgrade changed existing data")
        if any(
            connection.execute(
                f'SELECT COUNT(*) FROM "{table_name}"'
            ).fetchone()
            != (0,)
            for table_name in (
                EXPECTED_MARKET_TIME_TABLES
                | EXPECTED_MARKET_TIME_RUNTIME_TABLES
            )
        ):
            raise GateError("installed-wheel 0007 upgrade seeded market time")


def _verify_0008_upgrade(
    target: Path, config: Path, working: Path, database: Path
) -> None:
    _alembic(
        target,
        config,
        working,
        "upgrade",
        "0008_market_time_foundation",
        database_path=database,
    )
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            """
            INSERT INTO trading_calendars (
                record_schema_version, calendar_id, market, timezone,
                calendar_version, created_at
            ) VALUES (
                1, 'packaged-xnys-v1', 'XNYS', 'America/New_York',
                1, '2026-07-28 00:00:00'
            )
            """
        )
        connection.execute(
            "CREATE TABLE preserved_0008_gate_data "
            "(identity TEXT PRIMARY KEY, value TEXT)"
        )
        connection.execute(
            "INSERT INTO preserved_0008_gate_data "
            "VALUES ('existing', 'preserve-me')"
        )
        connection.commit()
        before_tables = _tables(connection)
        before_rows = _rows(connection, before_tables)

    _alembic(
        target,
        config,
        working,
        "upgrade",
        "head",
        database_path=database,
    )

    with closing(sqlite3.connect(database)) as connection:
        if connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchall() != [("0009_market_time_runtime",)]:
            raise GateError("installed-wheel 0008 upgrade did not reach 0009")
        if _tables(connection) != (
            before_tables | EXPECTED_MARKET_TIME_RUNTIME_TABLES
        ):
            raise GateError("installed-wheel 0008 upgrade changed unrelated tables")
        if _rows(connection, before_tables) != before_rows:
            raise GateError("installed-wheel 0008 upgrade changed existing data")
        if any(
            connection.execute(
                f'SELECT COUNT(*) FROM "{table_name}"'
            ).fetchone()
            != (0,)
            for table_name in EXPECTED_MARKET_TIME_RUNTIME_TABLES
        ):
            raise GateError("installed-wheel 0008 upgrade seeded replay state")


def _verify_fail_closed(
    target: Path, config: Path, working: Path, database: Path
) -> None:
    probe = (
        "from pathlib import Path; "
        "from el_psy_quant.local_workspace import "
        "LocalWorkspaceError, upgrade_product_database; "
        f"database = Path({str(database)!r}); "
        "\ntry:\n"
        f"    upgrade_product_database(database_path=database, "
        f"alembic_config_path=Path({str(config)!r}))\n"
        "except LocalWorkspaceError as error:\n"
        "    assert str(error) == 'product migration resources are unavailable'\n"
        "else:\n"
        "    raise AssertionError('migration resource failure was not refused')\n"
        "assert not database.exists()\n"
    )
    _run_installed_python(target, ["-c", probe], cwd=working)


def main() -> int:
    """Build, install, and exercise the exact packaged migration authority."""
    uv = shutil.which("uv")
    if uv is None:
        print("installed-wheel migration-resource gate failed: uv is unavailable")
        return 1
    try:
        with tempfile.TemporaryDirectory(
            prefix="el-psy-quant-packaged-migrations-"
        ) as temporary:
            root = Path(temporary).resolve()
            if root.is_relative_to(PROJECT_ROOT):
                raise GateError("packaged-wheel gate must run outside the repository")
            wheelhouse = root / "wheelhouse"
            installed = root / "installed"
            working = root / "working"
            wheelhouse.mkdir()
            working.mkdir()
            config = working / "alembic.ini"
            shutil.copyfile(PROJECT_ROOT / "alembic.ini", config)

            _run(
                [
                    uv,
                    "build",
                    "--wheel",
                    "--no-build-isolation",
                    "--offline",
                    "--out-dir",
                    str(wheelhouse),
                ],
                cwd=PROJECT_ROOT,
            )
            wheels = tuple(wheelhouse.glob("el_psy_quant-*.whl"))
            if len(wheels) != 1:
                raise GateError("wheel build did not produce exactly one artifact")
            wheel = wheels[0]
            _wheel_resources(wheel)
            _run(
                [
                    uv,
                    "pip",
                    "install",
                    "--offline",
                    "--no-deps",
                    "--target",
                    str(installed),
                    str(wheel),
                ],
                cwd=working,
            )
            _installed_resources(installed)
            _assert_installed_import(installed, working)

            heads = _alembic(installed, config, working, "heads")
            if heads.stdout.strip() != EXPECTED_HEAD_OUTPUT:
                raise GateError("installed-wheel Alembic head is not exact")
            _verify_fresh_upgrade(
                installed,
                config,
                working,
                root / "fresh.sqlite3",
            )
            _verify_0005_upgrade(
                installed,
                config,
                working,
                root / "upgrade.sqlite3",
            )
            _verify_0006_upgrade(
                installed,
                config,
                working,
                root / "upgrade-0006.sqlite3",
            )
            _verify_0007_upgrade(
                installed,
                config,
                working,
                root / "upgrade-0007.sqlite3",
            )
            _verify_0008_upgrade(
                installed,
                config,
                working,
                root / "upgrade-0008.sqlite3",
            )

            missing = root / "missing-resource"
            shutil.copytree(installed, missing)
            (missing / Path(WHEEL_MIGRATION_ROOT) / "env.py").unlink()
            _verify_fail_closed(
                missing,
                config,
                working,
                root / "missing.sqlite3",
            )

            mismatched = root / "mismatched-head"
            shutil.copytree(installed, mismatched)
            revision_path = (
                mismatched
                / Path(WHEEL_MIGRATION_ROOT)
                / "versions"
                / "0009_market_time_runtime.py"
            )
            revision_text = revision_path.read_text(encoding="utf-8")
            revision_path.write_text(
                revision_text.replace(
                    'revision: str = "0009_market_time_runtime"',
                    'revision: str = "0010_unexpected_head"',
                    1,
                ),
                encoding="utf-8",
            )
            _verify_fail_closed(
                mismatched,
                config,
                working,
                root / "mismatched.sqlite3",
            )
    except (GateError, OSError, sqlite3.Error, subprocess.CalledProcessError) as exc:
        print(f"installed-wheel migration-resource gate failed: {exc}")
        return 1

    print(
        "installed-wheel migration-resource gate passed: complete resources; "
        "0009_market_time_runtime head; fresh, 0005, populated 0006, "
        "preserved 0007, and populated 0008 upgrades; "
        "fail-closed probes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
