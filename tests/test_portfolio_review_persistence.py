from pathlib import Path

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
from el_psy_quant.persistence.schema import REQUIRED_PRODUCT_TABLE_COLUMNS
from el_psy_quant.persistence.schema import CURRENT_PRODUCT_SCHEMA_REVISION

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREVIOUS_REVISION = "0005_paper_job_result_references"
PORTFOLIO_REVIEW_REVISION = "0006_portfolio_reviews"
PAPER_ACCOUNT_REVISION = "0007_paper_account_ledger"
MARKET_TIME_FOUNDATION_REVISION = "0008_market_time_foundation"
MARKET_TIME_RUNTIME_REVISION = "0009_market_time_runtime"
STRATEGY_ORDER_REVISION = "0010_strategy_order_risk"
PAPER_EXECUTION_REVISION = "0011_paper_execution"


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


def test_portfolio_review_is_one_exact_linear_head() -> None:
    scripts = ScriptDirectory.from_config(_config())
    assert scripts.get_heads() == [CURRENT_PRODUCT_SCHEMA_REVISION]
    assert (
        scripts.get_revision(CURRENT_PRODUCT_SCHEMA_REVISION).down_revision
        == PAPER_EXECUTION_REVISION
    )
    assert scripts.get_revision(PAPER_EXECUTION_REVISION).down_revision == (
        STRATEGY_ORDER_REVISION
    )
    assert (
        scripts.get_revision(STRATEGY_ORDER_REVISION).down_revision
        == MARKET_TIME_RUNTIME_REVISION
    )
    assert (
        scripts.get_revision(MARKET_TIME_RUNTIME_REVISION).down_revision
        == MARKET_TIME_FOUNDATION_REVISION
    )
    assert (
        scripts.get_revision(MARKET_TIME_FOUNDATION_REVISION).down_revision
        == PAPER_ACCOUNT_REVISION
    )
    assert scripts.get_revision(PAPER_ACCOUNT_REVISION).down_revision == (
        PORTFOLIO_REVIEW_REVISION
    )
    assert scripts.get_revision(PORTFOLIO_REVIEW_REVISION).down_revision == (
        PREVIOUS_REVISION
    )


def test_upgrade_adds_only_compact_portfolio_review_table(
    tmp_path: Path,
    monkeypatch,
) -> None:
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    command.upgrade(_config(), PREVIOUS_REVISION)
    before_engine = _engine(path)
    try:
        before = set(inspect(before_engine).get_table_names())
    finally:
        before_engine.dispose()

    command.upgrade(_config(), PORTFOLIO_REVIEW_REVISION)

    assert _current(path) == PORTFOLIO_REVIEW_REVISION
    engine = _engine(path)
    try:
        inspector = inspect(engine)
        assert set(inspector.get_table_names()) == before | {"portfolio_reviews"}
        columns = tuple(
            column["name"] for column in inspector.get_columns("portfolio_reviews")
        )
        assert columns == REQUIRED_PRODUCT_TABLE_COLUMNS["portfolio_reviews"]
        assert not any(
            token in column
            for column in columns
            for token in (
                "payload",
                "json",
                "observation",
                "matrix",
                "contribution",
                "cash",
                "position",
                "order",
                "fill",
                "ledger",
            )
        )
        assert inspector.get_pk_constraint("portfolio_reviews") == {
            "name": "pk_portfolio_reviews",
            "constrained_columns": ["review_id"],
        }
        unique_names = {
            item["name"]
            for item in inspector.get_unique_constraints("portfolio_reviews")
        }
        assert unique_names == {
            "uq_portfolio_reviews_create_idempotency_key",
            "uq_portfolio_reviews_analysis_digest",
            "uq_portfolio_reviews_analysis_relative_path",
            "uq_portfolio_reviews_decision_id",
            "uq_portfolio_reviews_decision_digest",
            "uq_portfolio_reviews_decision_relative_path",
            "uq_portfolio_reviews_decision_idempotency_key",
        }
        assert {
            item["name"]
            for item in inspector.get_check_constraints("portfolio_reviews")
        } == {
            "ck_portfolio_reviews_record_schema_version",
            "ck_portfolio_reviews_source_schema_version",
            "ck_portfolio_reviews_analysis_schema_version",
            "ck_portfolio_reviews_decision_schema_version",
            "ck_portfolio_reviews_status",
            "ck_portfolio_reviews_outcome",
            "ck_portfolio_reviews_version",
            "ck_portfolio_reviews_digest_shapes",
            "ck_portfolio_reviews_path_shapes",
            "ck_portfolio_reviews_decision_consistency",
        }
    finally:
        engine.dispose()


def test_downgrade_removes_only_portfolio_reviews(
    tmp_path: Path,
    monkeypatch,
) -> None:
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    command.upgrade(_config(), PORTFOLIO_REVIEW_REVISION)
    engine = _engine(path)
    try:
        before = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    command.downgrade(_config(), PREVIOUS_REVISION)

    assert _current(path) == PREVIOUS_REVISION
    engine = _engine(path)
    try:
        assert set(inspect(engine).get_table_names()) == before - {"portfolio_reviews"}
    finally:
        engine.dispose()
