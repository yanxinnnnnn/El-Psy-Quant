"""Persistence, corruption, constraints, and upgrade evidence for Sprint 218."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.exc import DatabaseError, IntegrityError

from el_psy_quant.application import PaperExecutionApplicationService
from el_psy_quant.paper_runtime import (
    create_paper_runtime,
    create_paper_runtime_checkpoint,
    create_paper_runtime_command_receipt,
    create_paper_runtime_event,
    create_paper_runtime_work,
)
from el_psy_quant.persistence import (
    PaperRuntimePersistenceCorruptionError,
    SqlAlchemyPaperExecutionRepository,
    SqlAlchemyPaperRuntimeRepository,
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)
from el_psy_quant.persistence.paper_runtime_mapping import (
    checkpoint_from_row,
    checkpoint_row,
    receipt_from_row,
    receipt_row,
)
from el_psy_quant.persistence.schema import (
    CURRENT_PRODUCT_SCHEMA_REVISION,
    REQUIRED_PRODUCT_TABLE_COLUMNS,
    verify_product_schema,
)
from test_paper_execution_persistence import _config, _fixture, _migrate, _step_command

AUDIT = datetime(2026, 8, 25, 2, tzinfo=timezone.utc)
TABLES = {
    "paper_runtimes",
    "paper_runtime_work",
    "paper_runtime_checkpoints",
    "paper_runtime_events",
    "paper_runtime_command_receipts",
}


def _authorities(path, monkeypatch, *, step: bool = True):
    _migrate(path, monkeypatch, "head")
    engine, factory, command = _fixture(path)
    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT
    )
    order = service.create_order(command).result
    commit = (
        None
        if not step
        else service.step_order(
            _step_command(order, version=0, key="runtime-observed-step")
        ).result
    )
    runtime = create_paper_runtime(
        execution_order=order,
        logical_actor="paper-runtime",
        runtime_policy_id="durable-runtime-v1",
        runtime_policy_version=1,
        created_at=AUDIT,
    )
    work = create_paper_runtime_work(
        runtime=runtime,
        expected_execution_version=0,
        created_at=AUDIT + timedelta(seconds=1),
    )
    event = create_paper_runtime_event(
        runtime=runtime,
        event_sequence=0,
        event_type="runtime_created",
        resulting_runtime_version=0,
        payload={"runtime_id": runtime.runtime_id},
        recorded_at=AUDIT,
    )
    receipt = create_paper_runtime_command_receipt(
        namespace="create_paper_runtime",
        command_idempotency_key="create-runtime",
        command_digest="c" * 64,
        command_actor="founder",
        runtime=runtime,
        result_event=event,
        created_at=AUDIT,
    )
    return engine, factory, order, commit, runtime, work, event, receipt


def test_0012_is_one_linear_head_and_clean_upgrade_has_exact_empty_tables(
    tmp_path, monkeypatch
):
    path = tmp_path / "clean.sqlite3"
    scripts = ScriptDirectory.from_config(_config())
    assert scripts.get_heads() == ["0012_durable_paper_runtime"]
    assert (
        scripts.get_revision("0012_durable_paper_runtime").down_revision
        == "0011_paper_execution"
    )
    assert CURRENT_PRODUCT_SCHEMA_REVISION == "0012_durable_paper_runtime"
    _migrate(path, monkeypatch, "head")
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=path)
    )
    try:
        inspector = inspect(engine)
        assert TABLES.issubset(inspector.get_table_names())
        for table in TABLES:
            assert (
                tuple(column["name"] for column in inspector.get_columns(table))
                == REQUIRED_PRODUCT_TABLE_COLUMNS[table]
            )
        with engine.connect() as connection:
            assert all(
                connection.scalar(text(f'SELECT COUNT(*) FROM "{table}"')) == 0
                for table in TABLES
            )
        assert verify_product_schema(path) == "0012_durable_paper_runtime"
    finally:
        engine.dispose()


def test_repository_reconstructs_runtime_work_checkpoint_event_and_historical_receipt(
    tmp_path, monkeypatch
):
    path = tmp_path / "records.sqlite3"
    engine, factory, order, commit, runtime, work, event, receipt = _authorities(
        path, monkeypatch
    )
    try:
        assert commit is not None
        checkpoint = create_paper_runtime_checkpoint(
            runtime=runtime,
            work=work,
            attempt=commit.step_result.attempt,
            fill=commit.step_result.fill,
            settlement_link=commit.settlement_link,
            observed_at=AUDIT + timedelta(seconds=2),
        )
        with factory.begin() as session:
            repository = SqlAlchemyPaperRuntimeRepository(session=session)
            assert repository.append_runtime(runtime=runtime) == runtime
            assert repository.append_work(work=work) == work
            assert repository.append_checkpoint(checkpoint=checkpoint) == checkpoint
            assert repository.append_event(event=event) == event
            assert repository.append_receipt(receipt=receipt) == receipt
        with factory() as session:
            repository = SqlAlchemyPaperRuntimeRepository(session=session)
            assert repository.get_runtime(runtime_id=runtime.runtime_id) == runtime
            assert repository.get_work(work_id=work.work_id) == work
            assert (
                repository.get_checkpoint(checkpoint_id=checkpoint.checkpoint_id)
                == checkpoint
            )
            assert repository.list_events(runtime_id=runtime.runtime_id) == (event,)
            assert (
                repository.get_receipt(
                    namespace="create_paper_runtime",
                    command_idempotency_key="create-runtime",
                )
                == receipt
            )
    finally:
        engine.dispose()


def test_sql_uniqueness_fk_and_immutability_are_active(tmp_path, monkeypatch):
    path = tmp_path / "constraints.sqlite3"
    engine, factory, order, _commit, runtime, work, event, receipt = _authorities(
        path, monkeypatch, step=True
    )
    try:
        assert _commit is not None
        checkpoint = create_paper_runtime_checkpoint(
            runtime=runtime,
            work=work,
            attempt=_commit.step_result.attempt,
            fill=_commit.step_result.fill,
            settlement_link=_commit.settlement_link,
            observed_at=AUDIT + timedelta(seconds=2),
        )
        with factory.begin() as session:
            repository = SqlAlchemyPaperRuntimeRepository(session=session)
            repository.append_runtime(runtime=runtime)
            repository.append_work(work=work)
            repository.append_checkpoint(checkpoint=checkpoint)
            repository.append_event(event=event)
            repository.append_receipt(receipt=receipt)
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE paper_runtimes SET desired_state='running', row_version=1, updated_at=:now WHERE runtime_id=:id"
                ),
                {"now": AUDIT + timedelta(minutes=1), "id": runtime.runtime_id},
            )
        for statement in (
            "UPDATE paper_runtimes SET logical_actor='other'",
            "DELETE FROM paper_runtimes",
            "UPDATE paper_runtime_work SET m34_step_actor='other'",
            "DELETE FROM paper_runtime_work",
            "UPDATE paper_runtime_checkpoints SET post_cursor_position=999",
            "DELETE FROM paper_runtime_checkpoints",
            "UPDATE paper_runtime_events SET event_type='start_requested'",
            "DELETE FROM paper_runtime_events",
            "UPDATE paper_runtime_command_receipts SET command_actor='other'",
            "DELETE FROM paper_runtime_command_receipts",
        ):
            with pytest.raises(DatabaseError):
                with engine.begin() as connection:
                    connection.execute(text(statement))
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO paper_runtime_work SELECT * FROM paper_runtime_work"
                    )
                )
        for table in (
            "paper_runtimes",
            "paper_runtime_checkpoints",
            "paper_runtime_events",
            "paper_runtime_command_receipts",
        ):
            with pytest.raises(IntegrityError):
                with engine.begin() as connection:
                    connection.execute(
                        text(f"INSERT INTO {table} SELECT * FROM {table}")
                    )
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE paper_runtimes SET owner_id='worker' WHERE runtime_id=:id"
                    ),
                    {"id": runtime.runtime_id},
                )
    finally:
        engine.dispose()


def test_checkpoint_and_receipt_mismatches_fail_closed_in_strict_mappers(
    tmp_path, monkeypatch
):
    path = tmp_path / "mapper-corrupt.sqlite3"
    engine, _factory, _order, commit, runtime, work, event, receipt = _authorities(
        path, monkeypatch
    )
    try:
        assert commit is not None
        checkpoint = create_paper_runtime_checkpoint(
            runtime=runtime,
            work=work,
            attempt=commit.step_result.attempt,
            fill=commit.step_result.fill,
            settlement_link=commit.settlement_link,
            observed_at=AUDIT + timedelta(seconds=2),
        )
        for field, value in (
            ("attempt_digest", "d" * 64),
            ("observed_execution_version", 99),
            ("post_cursor_position", 999),
            ("payload_json", checkpoint_row(checkpoint).payload_json + " "),
        ):
            row = checkpoint_row(checkpoint)
            setattr(row, field, value)
            with pytest.raises(PaperRuntimePersistenceCorruptionError):
                checkpoint_from_row(row, runtime=runtime, work=work)

        wrong_event = create_paper_runtime_event(
            runtime=runtime,
            event_sequence=1,
            event_type="start_requested",
            resulting_runtime_version=1,
            payload={"requested": "running"},
            recorded_at=AUDIT + timedelta(minutes=1),
        )
        for field, value, result_event in (
            ("result_event_digest", "e" * 64, event),
            ("resulting_runtime_version", 9, event),
            ("result_event_id", wrong_event.event_id, wrong_event),
        ):
            row = receipt_row(receipt)
            setattr(row, field, value)
            with pytest.raises(PaperRuntimePersistenceCorruptionError):
                receipt_from_row(row, runtime=runtime, result_event=result_event)
    finally:
        engine.dispose()


def test_payload_and_cross_authority_corruption_fails_closed_without_repair(
    tmp_path, monkeypatch
):
    path = tmp_path / "corrupt.sqlite3"
    engine, factory, _order, _commit, runtime, work, event, receipt = _authorities(
        path, monkeypatch, step=False
    )
    try:
        with factory.begin() as session:
            repository = SqlAlchemyPaperRuntimeRepository(session=session)
            repository.append_runtime(runtime=runtime)
            repository.append_work(work=work)
            repository.append_event(event=event)
            repository.append_receipt(receipt=receipt)
        with engine.begin() as connection:
            original = connection.scalar(
                text("SELECT payload_json FROM paper_runtimes WHERE runtime_id=:id"),
                {"id": runtime.runtime_id},
            )
            connection.execute(
                text(
                    "UPDATE paper_runtimes SET payload_json=:payload WHERE runtime_id=:id"
                ),
                {
                    "payload": original.replace(
                        '"account_id":', '"wrong_account_id":', 1
                    ),
                    "id": runtime.runtime_id,
                },
            )
        with factory() as session:
            with pytest.raises(PaperRuntimePersistenceCorruptionError):
                SqlAlchemyPaperRuntimeRepository(session=session).get_runtime(
                    runtime_id=runtime.runtime_id
                )
        with engine.connect() as connection:
            assert (
                connection.scalar(
                    text(
                        "SELECT payload_json FROM paper_runtimes WHERE runtime_id=:id"
                    ),
                    {"id": runtime.runtime_id},
                )
                != original
            )
    finally:
        engine.dispose()


def test_populated_0011_upgrade_preserves_every_existing_row_and_m34_reconstruction(
    tmp_path, monkeypatch
):
    path = tmp_path / "populated.sqlite3"
    _migrate(path, monkeypatch, "0011_paper_execution")
    engine, factory, command = _fixture(path)
    order = (
        PaperExecutionApplicationService(session_factory=factory)
        .create_order(command)
        .result
    )
    predecessor = tuple(
        name for name in inspect(engine).get_table_names() if name != "alembic_version"
    )
    with engine.connect() as connection:
        before = {
            table: tuple(
                connection.execute(text(f'SELECT * FROM "{table}" ORDER BY rowid'))
            )
            for table in predecessor
        }
    engine.dispose()
    _migrate(path, monkeypatch, "head")
    upgraded = create_product_database_engine(
        config=resolve_product_database_config(database_path=path)
    )
    upgraded_factory = create_product_session_factory(engine=upgraded)
    try:
        with upgraded.connect() as connection:
            after = {
                table: tuple(
                    connection.execute(text(f'SELECT * FROM "{table}" ORDER BY rowid'))
                )
                for table in predecessor
            }
            assert after == before
            assert all(
                connection.scalar(text(f'SELECT COUNT(*) FROM "{table}"')) == 0
                for table in TABLES
            )
        with upgraded_factory() as session:
            history = SqlAlchemyPaperExecutionRepository(
                session=session
            ).load_historical_history(execution_order_id=order.execution_order_id)
            assert history.order == order
    finally:
        upgraded.dispose()
