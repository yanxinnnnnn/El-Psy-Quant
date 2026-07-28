"""Tests for explicit local product database configuration."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from el_psy_quant.api.app import create_app
from el_psy_quant.persistence import (
    ProductDatabaseConfig,
    resolve_product_database_config,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV


def test_explicit_path_override_wins_over_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    environment_path = tmp_path / "environment.sqlite3"
    explicit_path = tmp_path / "explicit.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(environment_path))

    config = resolve_product_database_config(database_path=explicit_path)

    assert config == ProductDatabaseConfig(database_path=explicit_path.resolve())


def test_environment_path_is_used_without_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))

    config = resolve_product_database_config()

    assert config.database_path == database_path.resolve()


def test_missing_configuration_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(PRODUCT_DATABASE_PATH_ENV, raising=False)

    with pytest.raises(ValueError, match=PRODUCT_DATABASE_PATH_ENV):
        resolve_product_database_config()


@pytest.mark.parametrize("database_path", ["", "   "])
def test_blank_configuration_is_rejected(database_path: str) -> None:
    with pytest.raises(ValueError, match="must not be blank"):
        resolve_product_database_config(database_path=database_path)


@pytest.mark.parametrize(
    "database_path",
    [
        "sqlite:///product.sqlite3",
        "postgresql://localhost/product",
        Path("sqlite:///product.sqlite3"),
    ],
)
def test_database_urls_are_rejected(database_path: str | Path) -> None:
    with pytest.raises(ValueError, match="not a database URL"):
        resolve_product_database_config(database_path=database_path)


def test_path_resolution_is_side_effect_free(tmp_path: Path) -> None:
    database_path = tmp_path / "missing" / "product.sqlite3"

    config = resolve_product_database_config(database_path=database_path)

    assert config.database_path == database_path.resolve()
    assert not database_path.exists()
    assert not database_path.parent.exists()


def test_config_is_immutable(tmp_path: Path) -> None:
    config = resolve_product_database_config(
        database_path=tmp_path / "product.sqlite3"
    )

    with pytest.raises(FrozenInstanceError):
        config.database_path = tmp_path / "other.sqlite3"  # type: ignore[misc]


def test_imports_do_not_create_the_configured_database(tmp_path: Path) -> None:
    database_path = tmp_path / "product.sqlite3"
    environment = os.environ.copy()
    environment[PRODUCT_DATABASE_PATH_ENV] = str(database_path)

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import el_psy_quant; import el_psy_quant.persistence; "
            "import el_psy_quant.application; import el_psy_quant.api.app",
        ],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert not database_path.exists()


def test_existing_api_remains_usable_without_database_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(PRODUCT_DATABASE_PATH_ENV, raising=False)

    application = create_app()
    response = TestClient(application).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert application.state.product_database_path is None
    assert application.state.product_session_factory is None


def test_persistence_package_exports_only_the_approved_foundation() -> None:
    import el_psy_quant.persistence as persistence  # noqa: PLC0415

    assert set(persistence.__all__) == {
        "ArtifactIndexEntry",
        "ArtifactIndexRepository",
        "MARKET_TIME_PERSISTENCE_RECORD_SCHEMA_VERSION",
        "MarketDataReplayRecord",
        "MarketTimeRepository",
        "PAPER_ACCOUNT_PERSISTENCE_RECORD_SCHEMA_VERSION",
        "PAPER_ACCOUNT_RECORD_SCHEMA_VERSION",
        "PaperAccountApprovedEvidenceError",
        "PaperAccountCommandResult",
        "PaperAccountConcurrencyConflictError",
        "PaperAccountCreationKeyRecord",
        "PaperAccountIdempotencyConflictError",
        "PaperAccountNotFoundError",
        "PaperAccountOperationConflictError",
        "PaperAccountPersistenceCorruptionError",
        "PaperAccountProjectionReconciliationRequiredError",
        "PaperAccountReconciliationResult",
        "PaperAccountRecord",
        "PaperAccountRepository",
        "PaperAccountSnapshotResult",
        "PaperAccountStorageBusyError",
        "PaperAccountVersionConflictError",
        "PaperJobRecord",
        "PaperJobAttemptRecord",
        "PaperJobAttemptRepository",
        "PaperJobAttemptStatus",
        "PaperJobErrorCode",
        "PaperJobRepository",
        "PaperJobResultReference",
        "PaperJobResultReferenceRepository",
        "PaperJobStatus",
        "PaperJobSubmissionKeyRecord",
        "PaperJobSubmissionKeyRepository",
        "PreparedPaperRunRequest",
        "PortfolioReviewRecord",
        "PortfolioReviewRepository",
        "PortfolioReviewStatus",
        "PORTFOLIO_REVIEW_LIST_LIMIT_MAXIMUM",
        "PORTFOLIO_REVIEW_RECORD_SCHEMA_VERSION",
        "ProductDatabaseConfig",
        "ProductPersistenceBase",
        "SqlAlchemyArtifactIndexRepository",
        "SqlAlchemyMarketTimeRepository",
        "SqlAlchemyPaperAccountRepository",
        "SqlAlchemyPaperJobAttemptRepository",
        "SqlAlchemyPaperJobRepository",
        "SqlAlchemyPaperJobResultReferenceRepository",
        "SqlAlchemyPaperJobSubmissionKeyRepository",
        "SqlAlchemyPortfolioReviewRepository",
        "complete_paper_job_attempt",
        "create_artifact_index_entry",
        "create_market_data_replay_record",
        "create_product_database_engine",
        "create_product_session_factory",
        "create_awaiting_portfolio_review_record",
        "create_queued_paper_job_record",
        "create_paper_job_submission_key_record",
        "create_paper_job_result_reference",
        "create_running_paper_job_attempt",
        "deserialize_paper_run_request",
        "digest_prepared_paper_run_request",
        "digest_portfolio_review_command",
        "prepare_paper_run_request_for_persistence",
        "resolve_product_database_config",
        "serialize_paper_run_request",
        "transition_paper_job_record",
        "validate_paper_job_idempotency_key",
        "validate_portfolio_review_idempotency_key",
    }
    assert not hasattr(persistence, "Repository")
    assert not hasattr(persistence, "JobStatus")
