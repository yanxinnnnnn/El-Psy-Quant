"""Integration tests for the caller-owned artifact-index repository."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from el_psy_quant.persistence import (
    SqlAlchemyArtifactIndexRepository,
    create_artifact_index_entry,
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)
from el_psy_quant.persistence.artifact_index_model import ArtifactIndexRecord
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    database_path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    command.upgrade(Config(str(PROJECT_ROOT / "alembic.ini")), "head")
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=database_path)
    )
    factory = create_product_session_factory(engine=engine)
    try:
        yield engine, factory
    finally:
        engine.dispose()


def _research(key: str):
    experiment_slug, run_id = key.split("/")
    return create_artifact_index_entry(
        artifact_type="research_run_manifest",
        artifact_key=f"{experiment_slug}/{run_id}",
        source_id=run_id,
    )


def _evidence(artifact_type: str, key: str, source_id: str | None = None):
    return create_artifact_index_entry(
        artifact_type=artifact_type,
        artifact_key=key,
        source_id=source_id or f"manifest {key}",
    )


def test_replace_get_list_filter_and_stale_cleanup(database) -> None:
    _, factory = database
    research_a = _research("experiment/run_a")
    research_b = _research("experiment/run_b")
    decision = _evidence("strategy_decision_manifest", "decision")
    report = _evidence("report_artifact_manifest", "report")
    with factory.begin() as session:
        repository = SqlAlchemyArtifactIndexRepository(session=session)
        repository.replace_root_entries(
            root_type="research", entries=(research_b, research_a)
        )
        repository.replace_root_entries(
            root_type="evidence", entries=(decision, report)
        )

    with factory() as session:
        repository = SqlAlchemyArtifactIndexRepository(session=session)
        assert (
            repository.get(
                artifact_type="research_run_manifest",
                artifact_key="experiment/run_a",
            )
            == research_a
        )
        assert repository.list() == (report, research_a, research_b, decision)
        assert repository.list(root_type="research") == (research_a, research_b)
        assert repository.list(artifact_type="report_artifact_manifest") == (report,)
        repository.replace_root_entries(root_type="research", entries=(research_b,))
        session.commit()

    with factory() as session:
        repository = SqlAlchemyArtifactIndexRepository(session=session)
        assert repository.list(root_type="research") == (research_b,)
        assert repository.list(root_type="evidence") == (report, decision)


def test_empty_replacement_clears_only_selected_root_and_is_idempotent(
    database,
) -> None:
    _, factory = database
    decision = _evidence("strategy_decision_manifest", "decision")
    with factory.begin() as session:
        repository = SqlAlchemyArtifactIndexRepository(session=session)
        repository.replace_root_entries(
            root_type="research", entries=(_research("experiment/run"),)
        )
        repository.replace_root_entries(root_type="evidence", entries=(decision,))
    with factory.begin() as session:
        repository = SqlAlchemyArtifactIndexRepository(session=session)
        assert repository.replace_root_entries(root_type="research", entries=()) == ()
        assert repository.replace_root_entries(root_type="research", entries=()) == ()

    with factory() as session:
        assert SqlAlchemyArtifactIndexRepository(session=session).list() == (decision,)


def test_repository_does_not_commit_and_caller_rollback_is_authoritative(
    database,
) -> None:
    _, factory = database
    first = _research("experiment/first")
    second = _research("experiment/second")
    with factory() as session:
        SqlAlchemyArtifactIndexRepository(session=session).replace_root_entries(
            root_type="research", entries=(first,)
        )
        session.rollback()
    with factory() as session:
        assert SqlAlchemyArtifactIndexRepository(session=session).list() == ()

    with factory.begin() as session:
        SqlAlchemyArtifactIndexRepository(session=session).replace_root_entries(
            root_type="research", entries=(first,)
        )
    with factory() as session:
        SqlAlchemyArtifactIndexRepository(session=session).replace_root_entries(
            root_type="research", entries=(second,)
        )
        session.rollback()
    with factory() as session:
        assert SqlAlchemyArtifactIndexRepository(session=session).list() == (first,)


def test_replacement_rejects_wrong_root_and_duplicate_inputs(database) -> None:
    _, factory = database
    entry = _research("experiment/run")
    with factory() as session:
        repository = SqlAlchemyArtifactIndexRepository(session=session)
        with pytest.raises(ValueError, match="selected root_type"):
            repository.replace_root_entries(root_type="evidence", entries=(entry,))
        with pytest.raises(ValueError, match="duplicate artifact identity"):
            repository.replace_root_entries(
                root_type="research", entries=(entry, entry)
            )


@pytest.mark.parametrize(
    "values",
    (
        {
            "record_schema_version": 2,
            "artifact_type": "research_run_manifest",
            "artifact_key": "experiment/run",
            "root_type": "research",
            "relative_path": "experiment/run/manifest.json",
            "source_id": "run",
        },
        {
            "record_schema_version": 1,
            "artifact_type": "research_run_manifest",
            "artifact_key": "experiment/run",
            "root_type": "evidence",
            "relative_path": "experiment/run/manifest.json",
            "source_id": "run",
        },
    ),
)
def test_database_checks_reject_invalid_rows(
    database, values: dict[str, object]
) -> None:
    _, factory = database
    with factory() as session:
        session.add(ArtifactIndexRecord(**values))
        with pytest.raises(IntegrityError):
            session.flush()


def test_database_rejects_duplicate_root_locator(database) -> None:
    engine, _ = database
    independent_factory = sessionmaker(bind=engine)
    shared = {
        "record_schema_version": 1,
        "root_type": "evidence",
        "relative_path": "report-artifacts/shared.json",
        "source_id": "manifest",
    }
    with independent_factory() as session:
        session.add_all(
            [
                ArtifactIndexRecord(
                    artifact_type="report_artifact_manifest",
                    artifact_key="one",
                    **shared,
                ),
                ArtifactIndexRecord(
                    artifact_type="report_artifact_manifest",
                    artifact_key="two",
                    **shared,
                ),
            ]
        )
        with pytest.raises(IntegrityError):
            session.flush()
