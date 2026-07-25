"""Tests for the SQLite engine and caller-owned session factory."""

from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from el_psy_quant.persistence import (
    ProductPersistenceBase,
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)


def _engine_for(database_path: Path):
    config = resolve_product_database_config(database_path=database_path)
    return create_product_database_engine(config=config)


def test_engine_targets_configured_file_without_creating_it(tmp_path: Path) -> None:
    database_path = tmp_path / "product.sqlite3"

    engine = _engine_for(database_path)

    assert engine.url.get_backend_name() == "sqlite"
    assert Path(engine.url.database).resolve() == database_path.resolve()
    assert not database_path.exists()
    engine.dispose()


def test_declarative_metadata_contains_only_approved_product_tables() -> None:
    assert set(ProductPersistenceBase.metadata.tables) == {
        "artifact_index_entries",
        "paper_account_creation_keys",
        "paper_account_events",
        "paper_account_position_projections",
        "paper_account_projections",
        "paper_account_reconciliations",
        "paper_account_snapshots",
        "paper_accounts",
        "paper_cash_ledger_entries",
        "paper_job_attempts",
        "paper_job_result_references",
        "paper_job_submission_keys",
        "paper_jobs",
        "paper_position_ledger_entries",
        "portfolio_reviews",
    }


def test_foreign_keys_are_enabled_on_independent_connections(
    tmp_path: Path,
) -> None:
    engine = _engine_for(tmp_path / "product.sqlite3")

    with engine.connect() as first_connection:
        with engine.connect() as second_connection:
            first = first_connection.scalar(text("PRAGMA foreign_keys"))
            second = second_connection.scalar(text("PRAGMA foreign_keys"))

    assert first == 1
    assert second == 1
    engine.dispose()


def test_session_factory_creates_separate_caller_owned_sessions(
    tmp_path: Path,
) -> None:
    engine = _engine_for(tmp_path / "product.sqlite3")
    session_factory = create_product_session_factory(engine=engine)

    first = session_factory()
    second = session_factory()
    try:
        assert isinstance(first, Session)
        assert isinstance(second, Session)
        assert first is not second
    finally:
        first.close()
        second.close()
        engine.dispose()


def test_committed_work_is_visible_to_a_later_session(tmp_path: Path) -> None:
    engine = _engine_for(tmp_path / "product.sqlite3")
    session_factory = create_product_session_factory(engine=engine)
    with engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE persistence_test (value TEXT NOT NULL)")
        )

    with session_factory() as session:
        session.execute(
            text("INSERT INTO persistence_test (value) VALUES (:value)"),
            {"value": "committed"},
        )
        session.commit()

    with session_factory() as later_session:
        values = later_session.scalars(
            text("SELECT value FROM persistence_test")
        ).all()

    assert values == ["committed"]
    engine.dispose()


def test_rolled_back_work_is_not_visible(tmp_path: Path) -> None:
    engine = _engine_for(tmp_path / "product.sqlite3")
    session_factory = create_product_session_factory(engine=engine)
    with engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE persistence_test (value TEXT NOT NULL)")
        )

    with session_factory() as session:
        session.execute(
            text("INSERT INTO persistence_test (value) VALUES (:value)"),
            {"value": "rolled-back"},
        )
        session.rollback()

    with session_factory() as later_session:
        count = later_session.scalar(text("SELECT COUNT(*) FROM persistence_test"))

    assert count == 0
    engine.dispose()
