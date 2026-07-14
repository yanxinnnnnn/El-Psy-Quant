"""Tests for compact immutable paper-job result references and repository."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from el_psy_quant.paper import create_paper_account_state, create_paper_run_request
from el_psy_quant.persistence import (
    PaperJobResultReference,
    SqlAlchemyPaperJobRepository,
    SqlAlchemyPaperJobResultReferenceRepository,
    create_paper_job_result_reference,
    create_product_database_engine,
    create_product_session_factory,
    create_queued_paper_job_record,
    prepare_paper_run_request_for_persistence,
    resolve_product_database_config,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV
from el_psy_quant.persistence.paper_job_model import PaperJobRow

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JOB_ID = "00000000-0000-4000-8000-000000000001"
OTHER_JOB_ID = "00000000-0000-4000-8000-000000000002"
NOW = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    command.upgrade(Config(str(PROJECT_ROOT / "alembic.ini")), "head")
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=path)
    )
    factory = create_product_session_factory(engine=engine)
    try:
        yield factory
    finally:
        engine.dispose()


def _request():
    state = create_paper_account_state(
        starting_cash=1_000,
        current_cash=1_000,
        positions={},
        timestamp="2026-07-14T11:00:00Z",
    )
    return create_paper_run_request(
        run_id="run-1",
        created_timestamp="2026-07-14T11:30:00Z",
        starting_account_state=state,
        ending_account_state=state,
        orders=(),
        fills=(),
    )


def _add_job(factory) -> None:
    request = _request()
    job = create_queued_paper_job_record(
        job_id=JOB_ID,
        request=request,
        submitted_timestamp=NOW,
    )
    with factory.begin() as session:
        SqlAlchemyPaperJobRepository(session=session).add(
            job=job,
            prepared_request=prepare_paper_run_request_for_persistence(request),
        )


def test_factory_creates_exact_job_owned_posix_paths_and_frozen_contract() -> None:
    reference = create_paper_job_result_reference(
        job_id=JOB_ID,
        created_timestamp=NOW,
    )

    assert reference == PaperJobResultReference(
        record_schema_version=1,
        job_id=JOB_ID,
        root_type="paper",
        artifact_schema_version=1,
        result_summary_schema_version=1,
        artifact_relative_path=(
            f"jobs/{JOB_ID}/paper/paper_run_artifact.json"
        ),
        result_summary_relative_path=(
            f"jobs/{JOB_ID}/paper/paper_run_result_summary.json"
        ),
        created_timestamp=NOW,
    )
    with pytest.raises(FrozenInstanceError):
        reference.job_id = OTHER_JOB_ID  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("artifact_relative_path", "C:/output/paper_run_artifact.json"),
        ("artifact_relative_path", "/jobs/output/paper_run_artifact.json"),
        ("artifact_relative_path", "jobs\\output\\paper_run_artifact.json"),
        ("artifact_relative_path", f"jobs/{JOB_ID}/../paper_run_artifact.json"),
        ("artifact_relative_path", f" jobs/{JOB_ID}/paper/paper_run_artifact.json"),
        ("artifact_relative_path", f"jobs/{JOB_ID}/paper/wrong.json"),
        (
            "artifact_relative_path",
            f"jobs/{OTHER_JOB_ID}/paper/paper_run_artifact.json",
        ),
        (
            "result_summary_relative_path",
            f"jobs/{JOB_ID}/paper/paper_run_artifact.json",
        ),
    ),
)
def test_contract_rejects_unsafe_or_mismatched_paths(field: str, value: str) -> None:
    reference = create_paper_job_result_reference(
        job_id=JOB_ID,
        created_timestamp=NOW,
    )

    with pytest.raises(ValueError):
        replace(reference, **{field: value})


def test_repository_is_caller_transaction_owned_and_round_trips(database) -> None:
    factory = database
    _add_job(factory)
    reference = create_paper_job_result_reference(
        job_id=JOB_ID,
        created_timestamp=NOW,
    )

    with factory() as session:
        repository = SqlAlchemyPaperJobResultReferenceRepository(session=session)
        assert repository.add(reference=reference) == reference
        session.rollback()
    with factory() as session:
        assert (
            SqlAlchemyPaperJobResultReferenceRepository(
                session=session
            ).get_by_job_id(job_id=JOB_ID)
            is None
        )
    with factory.begin() as session:
        SqlAlchemyPaperJobResultReferenceRepository(session=session).add(
            reference=reference
        )
    with factory() as session:
        assert SqlAlchemyPaperJobResultReferenceRepository(
            session=session
        ).get_by_job_id(job_id=JOB_ID) == reference


def test_reference_prevents_parent_job_deletion(database) -> None:
    factory = database
    _add_job(factory)
    with factory.begin() as session:
        SqlAlchemyPaperJobResultReferenceRepository(session=session).add(
            reference=create_paper_job_result_reference(
                job_id=JOB_ID,
                created_timestamp=NOW,
            )
        )

    with pytest.raises(IntegrityError):
        with factory.begin() as session:
            session.execute(delete(PaperJobRow).where(PaperJobRow.job_id == JOB_ID))


def test_repository_has_no_generic_mutation_or_filesystem_surface() -> None:
    forbidden = {
        "update",
        "patch",
        "delete",
        "refresh",
        "scan",
        "register_path",
        "open",
        "commit",
        "rollback",
        "close",
    }

    assert all(
        not hasattr(SqlAlchemyPaperJobResultReferenceRepository, name)
        for name in forbidden
    )
