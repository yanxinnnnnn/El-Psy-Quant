from __future__ import annotations

import threading
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text, update
from sqlalchemy.exc import DatabaseError

from el_psy_quant.application.paper_accounts import (
    PaperAccountApplicationService,
)
from el_psy_quant.paper_account import (
    ApprovedPortfolioReviewReference,
    PaperMoney,
    PaperQuantity,
    replay_paper_account_ledger,
)
from el_psy_quant.persistence import (
    PaperAccountIdempotencyConflictError,
    PaperAccountOperationConflictError,
    PaperAccountProjectionReconciliationRequiredError,
    PaperAccountVersionConflictError,
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)
from el_psy_quant.persistence.paper_account_model import (
    PaperAccountEventRow,
    PaperAccountProjectionRow,
)
from el_psy_quant.persistence.paper_account_repository import (
    SqlAlchemyPaperAccountRepository,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV
from el_psy_quant.persistence.schema import (
    REQUIRED_PRODUCT_INDEXES,
    REQUIRED_PRODUCT_TABLE_COLUMNS,
    REQUIRED_PRODUCT_TRIGGERS,
    read_product_schema_revision,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREVIOUS_REVISION = "0006_portfolio_reviews"
REVISION = "0007_paper_account_ledger"
NEW_TABLES = {
    "paper_accounts",
    "paper_account_events",
    "paper_cash_ledger_entries",
    "paper_position_ledger_entries",
    "paper_account_creation_keys",
    "paper_account_projections",
    "paper_account_position_projections",
    "paper_account_snapshots",
    "paper_account_reconciliations",
}


def _config() -> Config:
    return Config(str(PROJECT_ROOT / "alembic.ini"))


def _engine(path: Path):
    return create_product_database_engine(
        config=resolve_product_database_config(database_path=path)
    )


class DeterministicAuthority:
    def __init__(self) -> None:
        self._counter = 0
        self._lock = threading.Lock()

    def id(self, kind: str) -> str:
        with self._lock:
            self._counter += 1
            return f"{kind}-{self._counter:04d}"

    def clock(self) -> datetime:
        with self._lock:
            self._counter += 1
            return datetime(2026, 7, 24, tzinfo=timezone.utc) + timedelta(
                seconds=self._counter
            )


@pytest.fixture
def migrated_database(tmp_path: Path):
    path = tmp_path / "product.sqlite3"
    _migrate(path, "head")
    engine = _engine(path)
    try:
        yield path, engine, create_product_session_factory(engine=engine)
    finally:
        engine.dispose()


def _migrate(path: Path, revision: str) -> None:
    prior = os.environ.get(PRODUCT_DATABASE_PATH_ENV)
    os.environ[PRODUCT_DATABASE_PATH_ENV] = str(path)
    try:
        command.upgrade(_config(), revision)
    finally:
        if prior is None:
            os.environ.pop(PRODUCT_DATABASE_PATH_ENV, None)
        else:
            os.environ[PRODUCT_DATABASE_PATH_ENV] = prior


def _downgrade(path: Path, revision: str) -> None:
    prior = os.environ.get(PRODUCT_DATABASE_PATH_ENV)
    os.environ[PRODUCT_DATABASE_PATH_ENV] = str(path)
    try:
        command.downgrade(_config(), revision)
    finally:
        if prior is None:
            os.environ.pop(PRODUCT_DATABASE_PATH_ENV, None)
        else:
            os.environ[PRODUCT_DATABASE_PATH_ENV] = prior


def _service(session_factory):
    authority = DeterministicAuthority()
    return PaperAccountApplicationService(
        session_factory=session_factory,
        id_factory=authority.id,
        clock=authority.clock,
    )


def _create(service: PaperAccountApplicationService):
    return service.create_account(
        display_name="Founder account",
        base_currency="usd",
        initial_cash=PaperMoney.parse("100"),
        creation_idempotency_key="create-account",
        actor="founder",
    )


def test_migration_adds_exact_tables_indexes_triggers_and_downgrades(
    tmp_path: Path,
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, PREVIOUS_REVISION)
    engine = _engine(path)
    before = set(inspect(engine).get_table_names())
    engine.dispose()

    _migrate(path, REVISION)
    engine = _engine(path)
    try:
        inspector = inspect(engine)
        assert set(inspector.get_table_names()) == before | NEW_TABLES
        for table in NEW_TABLES:
            assert tuple(
                column["name"] for column in inspector.get_columns(table)
            ) == REQUIRED_PRODUCT_TABLE_COLUMNS[table]
            assert inspector.get_pk_constraint(table)["name"] is not None
            assert all(
                item["name"] is not None
                for item in inspector.get_check_constraints(table)
            )
            assert all(
                item["name"] is not None
                for item in inspector.get_unique_constraints(table)
            )
            assert all(
                item["name"] is not None
                for item in inspector.get_foreign_keys(table)
            )
        for table, names in REQUIRED_PRODUCT_INDEXES.items():
            if table not in NEW_TABLES:
                continue
            actual = {item["name"] for item in inspector.get_indexes(table)}
            assert set(names).issubset(actual)
        with engine.connect() as connection:
            triggers = {
                row[0]
                for row in connection.execute(
                    text(
                        "SELECT name FROM sqlite_master "
                        "WHERE type = 'trigger'"
                    )
                )
            }
        assert {
            name
            for name in REQUIRED_PRODUCT_TRIGGERS
            if not name.startswith("trg_trading_")
        }.issubset(triggers)
        assert read_product_schema_revision(path) == REVISION
    finally:
        engine.dispose()

    _downgrade(path, PREVIOUS_REVISION)
    engine = _engine(path)
    try:
        assert set(inspect(engine).get_table_names()) == before
    finally:
        engine.dispose()
    _migrate(path, REVISION)
    assert read_product_schema_revision(path) == REVISION


def test_populated_downgrade_removes_only_s184_graph_and_reupgrades(
    tmp_path: Path,
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, PREVIOUS_REVISION)
    engine = _engine(path)
    before_tables = set(inspect(engine).get_table_names())
    with engine.begin() as connection:
        assert connection.scalar(text("PRAGMA foreign_keys")) == 1
        connection.execute(
            text(
                "INSERT INTO artifact_index_entries "
                "(record_schema_version, artifact_type, artifact_key, "
                "root_type, relative_path, source_id) "
                "VALUES (1, 'research_run_manifest', 'preserved-s184-test', "
                "'research', 'preserved/manifest.json', 'preserved-source')"
            )
        )
    engine.dispose()

    _migrate(path, REVISION)
    engine = _engine(path)
    session_factory = create_product_session_factory(engine=engine)
    service = _service(session_factory)
    created = _create(service)
    adjusted = service.post_position_adjustment(
        account_id=created.account.account_id,
        expected_account_version=1,
        command_idempotency_key="opening-position",
        actor="founder",
        reason="populated downgrade coverage",
        symbol="AAPL",
        adjustment_category="opening_balance",
        signed_quantity_delta=PaperQuantity.parse("2"),
        signed_cost_basis_delta=PaperMoney.parse("40"),
    )
    snapshot = service.create_snapshot(
        account_id=created.account.account_id,
        expected_account_version=2,
        expected_head_event_id=adjusted.account.head_event_id,
        expected_head_chain_digest=adjusted.account.head_chain_digest,
        operation_idempotency_key="populated-downgrade-snapshot",
        actor="founder",
        reason="populated downgrade coverage",
    )
    reconciliation = service.reconcile_projection(
        account_id=created.account.account_id,
        expected_account_version=2,
        expected_head_event_id=adjusted.account.head_event_id,
        expected_head_chain_digest=adjusted.account.head_chain_digest,
        operation_idempotency_key="populated-downgrade-reconciliation",
        actor="founder",
        reason="populated downgrade coverage",
    )

    expected_counts = {
        "paper_accounts": 1,
        "paper_account_events": 2,
        "paper_cash_ledger_entries": 1,
        "paper_position_ledger_entries": 1,
        "paper_account_creation_keys": 1,
        "paper_account_projections": 1,
        "paper_account_position_projections": 1,
        "paper_account_snapshots": 1,
        "paper_account_reconciliations": 1,
    }
    with engine.connect() as connection:
        assert connection.scalar(text("PRAGMA foreign_keys")) == 1
        for table_name, expected_count in expected_counts.items():
            assert connection.scalar(
                text(f'SELECT COUNT(*) FROM "{table_name}"')
            ) == expected_count
        s184_index_trigger_names = {
            row[1]
            for row in connection.execute(
                text(
                    "SELECT type, name, tbl_name FROM sqlite_master "
                    "WHERE type IN ('index', 'trigger')"
                )
            )
            if row[2] in NEW_TABLES
        }
    history = service.get_account_history(
        account_id=created.account.account_id
    )
    assert len(history) == 2
    assert service.get_current_projection(
        account_id=created.account.account_id
    ).projection_digest == adjusted.projection.projection_digest
    assert service.get_snapshot(
        snapshot_id=snapshot.snapshot.snapshot_id
    ) == snapshot.snapshot
    assert service.get_reconciliation(
        reconciliation_id=reconciliation.reconciliation.reconciliation_id
    ) == reconciliation.reconciliation
    engine.dispose()

    _downgrade(path, PREVIOUS_REVISION)
    engine = _engine(path)
    try:
        assert read_product_schema_revision(path) == PREVIOUS_REVISION
        assert set(inspect(engine).get_table_names()) == before_tables
        with engine.connect() as connection:
            assert connection.scalar(text("PRAGMA foreign_keys")) == 1
            assert connection.execute(
                text(
                    "SELECT relative_path, source_id "
                    "FROM artifact_index_entries "
                    "WHERE artifact_key = 'preserved-s184-test'"
                )
            ).one() == (
                "preserved/manifest.json",
                "preserved-source",
            )
            remaining_objects = {
                row[1]
                for row in connection.execute(
                    text(
                        "SELECT type, name FROM sqlite_master "
                        "WHERE type IN ('index', 'trigger')"
                    )
                )
            }
        assert remaining_objects.isdisjoint(s184_index_trigger_names)
    finally:
        engine.dispose()

    _migrate(path, REVISION)
    engine = _engine(path)
    try:
        inspector = inspect(engine)
        assert read_product_schema_revision(path) == REVISION
        assert set(inspector.get_table_names()) == before_tables | NEW_TABLES
        with engine.connect() as connection:
            assert connection.scalar(text("PRAGMA foreign_keys")) == 1
            assert all(
                connection.scalar(
                    text(f'SELECT COUNT(*) FROM "{table_name}"')
                )
                == 0
                for table_name in NEW_TABLES
            )
        assert read_product_schema_revision(path) == REVISION
    finally:
        engine.dispose()


def test_creation_mutations_idempotency_snapshot_reconciliation_and_restart(
    tmp_path: Path,
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, "head")
    engine = _engine(path)
    session_factory = create_product_session_factory(engine=engine)
    service = _service(session_factory)

    created = _create(service)
    assert created.account.head_version == 1
    assert created.projection.cash_balance.canonical == "100"
    replayed = _create(service)
    assert replayed.replayed is True
    assert replayed.event == created.event
    with pytest.raises(PaperAccountIdempotencyConflictError):
        service.create_account(
            display_name="Different",
            base_currency="USD",
            initial_cash=PaperMoney.parse("100"),
            creation_idempotency_key="create-account",
            actor="founder",
        )

    deposit = service.post_cash_movement(
        account_id=created.account.account_id,
        expected_account_version=1,
        command_idempotency_key="deposit-1",
        actor="founder",
        reason="explicit funding",
        movement_type="deposit",
        requested_amount=PaperMoney.parse("25"),
    )
    assert deposit.projection.cash_balance.canonical == "125"
    assert service.post_cash_movement(
        account_id=created.account.account_id,
        expected_account_version=1,
        command_idempotency_key="deposit-1",
        actor="founder",
        reason="explicit funding",
        movement_type="deposit",
        requested_amount=PaperMoney.parse("25"),
    ).replayed

    position = service.post_position_adjustment(
        account_id=created.account.account_id,
        expected_account_version=2,
        command_idempotency_key="position-1",
        actor="founder",
        reason="opening ledger fact",
        symbol="aapl",
        adjustment_category="opening_balance",
        signed_quantity_delta=PaperQuantity.parse("2"),
        signed_cost_basis_delta=PaperMoney.parse("40"),
    )
    assert position.projection.positions[0].symbol == "AAPL"
    first_replay_after_later_mutation = service.post_cash_movement(
        account_id=created.account.account_id,
        expected_account_version=1,
        command_idempotency_key="deposit-1",
        actor="founder",
        reason="explicit funding",
        movement_type="deposit",
        requested_amount=PaperMoney.parse("25"),
    )
    assert first_replay_after_later_mutation.account.head_version == 2
    assert len(first_replay_after_later_mutation.history) == 2
    frozen = service.freeze_account(
        account_id=created.account.account_id,
        expected_account_version=3,
        command_idempotency_key="freeze-1",
        actor="founder",
        reason="control pause",
    )
    assert frozen.account.lifecycle_status == "frozen"
    active = service.reactivate_account(
        account_id=created.account.account_id,
        expected_account_version=4,
        command_idempotency_key="reactivate-1",
        actor="founder",
        reason="resume",
    )
    assert active.account.lifecycle_status == "active"
    history = service.get_account_history(account_id=created.account.account_id)
    assert replay_paper_account_ledger(history).head_version == 5

    snapshot = service.create_snapshot(
        account_id=created.account.account_id,
        expected_account_version=5,
        expected_head_event_id=active.account.head_event_id,
        expected_head_chain_digest=active.account.head_chain_digest,
        operation_idempotency_key="snapshot-1",
        actor="founder",
        reason="checkpoint",
    )
    assert not snapshot.replayed
    assert service.create_snapshot(
        account_id=created.account.account_id,
        expected_account_version=5,
        expected_head_event_id=active.account.head_event_id,
        expected_head_chain_digest=active.account.head_chain_digest,
        operation_idempotency_key="snapshot-1",
        actor="founder",
        reason="checkpoint",
    ).replayed
    with pytest.raises(PaperAccountOperationConflictError):
        service.create_snapshot(
            account_id=created.account.account_id,
            expected_account_version=5,
            expected_head_event_id=active.account.head_event_id,
            expected_head_chain_digest=active.account.head_chain_digest,
            operation_idempotency_key="snapshot-1",
            actor="founder",
            reason="different reason",
        )
    reconciliation = service.reconcile_projection(
        account_id=created.account.account_id,
        expected_account_version=5,
        expected_head_event_id=active.account.head_event_id,
        expected_head_chain_digest=active.account.head_chain_digest,
        operation_idempotency_key="reconcile-1",
        actor="founder",
        reason="verify",
    )
    assert reconciliation.reconciliation.outcome == "matched"
    assert service.reconcile_projection(
        account_id=created.account.account_id,
        expected_account_version=5,
        expected_head_event_id=active.account.head_event_id,
        expected_head_chain_digest=active.account.head_chain_digest,
        operation_idempotency_key="reconcile-1",
        actor="founder",
        reason="verify",
    ).replayed
    assert service.get_account(
        account_id=created.account.account_id
    ).head_version == 5
    engine.dispose()

    reopened = _engine(path)
    try:
        restarted = _service(
            create_product_session_factory(engine=reopened)
        )
        projection = restarted.get_current_projection(
            account_id=created.account.account_id
        )
        assert projection.projection_digest == active.projection.projection_digest
        assert restarted.get_snapshot(
            snapshot_id=snapshot.snapshot.snapshot_id
        ) == snapshot.snapshot
    finally:
        reopened.dispose()


def test_append_only_triggers_reject_direct_sql_and_orm(
    tmp_path: Path,
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, "head")
    engine = _engine(path)
    session_factory = create_product_session_factory(engine=engine)
    created = _create(_service(session_factory))

    with engine.begin() as connection:
        with pytest.raises(DatabaseError, match="append-only"):
            connection.execute(
                text(
                    "UPDATE paper_account_events "
                    "SET actor = 'tampered' WHERE event_id = :event_id"
                ),
                {"event_id": created.event.event_id},
            )
    with session_factory() as session:
        with pytest.raises(DatabaseError, match="append-only"):
            session.execute(
                update(PaperAccountEventRow)
                .where(
                    PaperAccountEventRow.event_id == created.event.event_id
                )
                .values(actor="tampered")
            )
            session.flush()
        session.rollback()
    with engine.begin() as connection:
        with pytest.raises(DatabaseError, match="cannot be deleted"):
            connection.execute(
                text(
                    "DELETE FROM paper_accounts WHERE account_id = :account_id"
                ),
                {"account_id": created.account.account_id},
            )
    engine.dispose()


def test_all_cash_and_position_vocabularies_persist_and_replay(
    tmp_path: Path,
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, "head")
    engine = _engine(path)
    session_factory = create_product_session_factory(engine=engine)
    service = _service(session_factory)
    created = service.create_account(
        display_name="Vocabulary account",
        base_currency="USD",
        initial_cash=PaperMoney.parse("1000"),
        creation_idempotency_key="create-vocabulary",
        actor="founder",
    )
    movements = (
        ("deposit", "10"),
        ("withdrawal", "5"),
        ("manual_adjustment", "1"),
        ("fee", "2"),
        ("commission", "3"),
        ("tax", "4"),
    )
    version = 1
    for movement_type, amount in movements:
        result = service.post_cash_movement(
            account_id=created.account.account_id,
            expected_account_version=version,
            command_idempotency_key=f"cash-{movement_type}",
            actor="founder",
            reason=f"{movement_type} fact",
            movement_type=movement_type,  # type: ignore[arg-type]
            requested_amount=PaperMoney.parse(amount),
        )
        version = result.account.head_version
    assert result.projection.cash_balance.canonical == "997"

    adjustments = (
        ("AAPL", "opening_balance", "1", "10"),
        ("AAPL", "manual_correction", "1", "5"),
        ("MSFT", "corporate_action", "2", "20"),
        ("GOOG", "other", "1", "7"),
    )
    for index, (symbol, category, quantity, cost) in enumerate(adjustments):
        result = service.post_position_adjustment(
            account_id=created.account.account_id,
            expected_account_version=version,
            command_idempotency_key=f"position-{index}",
            actor="founder",
            reason=f"{category} fact",
            symbol=symbol,
            adjustment_category=category,
            signed_quantity_delta=PaperQuantity.parse(quantity),
            signed_cost_basis_delta=PaperMoney.parse(cost),
        )
        version = result.account.head_version
    state = replay_paper_account_ledger(
        service.get_account_history(account_id=created.account.account_id)
    )
    assert state.head_version == 11
    assert [position.symbol for position in state.positions] == [
        "AAPL",
        "GOOG",
        "MSFT",
    ]
    engine.dispose()


def test_domain_failure_rolls_back_without_partial_mutation(
    tmp_path: Path,
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, "head")
    engine = _engine(path)
    session_factory = create_product_session_factory(engine=engine)
    service = _service(session_factory)
    created = _create(service)
    with pytest.raises(ValueError, match="negative"):
        service.post_cash_movement(
            account_id=created.account.account_id,
            expected_account_version=1,
            command_idempotency_key="too-large",
            actor="founder",
            reason="invalid",
            movement_type="withdrawal",
            requested_amount=PaperMoney.parse("101"),
        )
    history = service.get_account_history(account_id=created.account.account_id)
    assert len(history) == 1
    with engine.connect() as connection:
        assert connection.execute(
            text(
                "SELECT COUNT(*) FROM paper_account_events "
                "WHERE account_id = :account_id"
            ),
            {"account_id": created.account.account_id},
        ).scalar_one() == 1
    engine.dispose()


def test_identity_factory_failure_rolls_back_creation_graph(
    tmp_path: Path,
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, "head")
    engine = _engine(path)
    session_factory = create_product_session_factory(engine=engine)

    def failing_factory(kind: str) -> str:
        if kind == "paper_cash_entry":
            raise RuntimeError("injected identity failure")
        return f"{kind}-fixed"

    service = PaperAccountApplicationService(
        session_factory=session_factory,
        id_factory=failing_factory,
        clock=lambda: datetime(2026, 7, 24, tzinfo=timezone.utc),
    )
    with pytest.raises(RuntimeError, match="injected"):
        service.create_account(
            display_name="Rollback",
            base_currency="USD",
            initial_cash=PaperMoney.parse("1"),
            creation_idempotency_key="rollback-create",
            actor="founder",
        )
    with engine.connect() as connection:
        for table in NEW_TABLES:
            assert connection.execute(
                text(f'SELECT COUNT(*) FROM "{table}"')
            ).scalar_one() == 0
    engine.dispose()


def test_valid_stale_projection_reconciles_then_explicit_rebuilds(
    tmp_path: Path,
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, "head")
    engine = _engine(path)
    session_factory = create_product_session_factory(engine=engine)
    service = _service(session_factory)
    created = _create(service)
    deposit = service.post_cash_movement(
        account_id=created.account.account_id,
        expected_account_version=1,
        command_idempotency_key="deposit",
        actor="founder",
        reason="fund",
        movement_type="deposit",
        requested_amount=PaperMoney.parse("5"),
    )

    with session_factory.begin() as session:
        repository = SqlAlchemyPaperAccountRepository(session=session)
        repository.replace_projection(
            projection=created.projection,
            updated_timestamp=datetime(2026, 7, 24, 1, tzinfo=timezone.utc),
        )
    with pytest.raises(PaperAccountProjectionReconciliationRequiredError):
        service.get_current_projection(account_id=created.account.account_id)

    evidence = service.reconcile_projection(
        account_id=created.account.account_id,
        expected_account_version=2,
        expected_head_event_id=deposit.account.head_event_id,
        expected_head_chain_digest=deposit.account.head_chain_digest,
        operation_idempotency_key="stale-reconcile",
        actor="founder",
        reason="detect stale cache",
    )
    assert evidence.reconciliation.outcome == "mismatched"
    rebuilt = service.rebuild_projection(
        account_id=created.account.account_id,
        expected_account_version=2,
        expected_head_event_id=deposit.account.head_event_id,
        expected_head_chain_digest=deposit.account.head_chain_digest,
    )
    assert rebuilt.projection_digest == deposit.projection.projection_digest
    assert service.get_current_projection(
        account_id=created.account.account_id
    ) == rebuilt
    engine.dispose()


def test_two_sessions_have_one_winner_for_same_prior_version(
    tmp_path: Path,
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, "head")
    engine = _engine(path)
    session_factory = create_product_session_factory(engine=engine)
    service = _service(session_factory)
    created = _create(service)
    barrier = threading.Barrier(2)

    def mutate(key: str):
        barrier.wait(timeout=5)
        return service.post_cash_movement(
            account_id=created.account.account_id,
            expected_account_version=1,
            command_idempotency_key=key,
            actor="founder",
            reason="race",
            movement_type="deposit",
            requested_amount=PaperMoney.parse("1"),
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(mutate, key) for key in ("race-a", "race-b")]
    outcomes = []
    for future in futures:
        try:
            outcomes.append(future.result())
        except PaperAccountVersionConflictError:
            outcomes.append("version-conflict")
    assert sum(item != "version-conflict" for item in outcomes) == 1
    history = service.get_account_history(account_id=created.account.account_id)
    assert len(history) == 2
    assert replay_paper_account_ledger(history).head_version == 2
    engine.dispose()


def test_importing_persistence_models_does_not_open_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    __import__("el_psy_quant.persistence.paper_account_model")
    __import__("el_psy_quant.persistence.paper_account_mapping")
    __import__("el_psy_quant.persistence.paper_account_repository")
    assert list(tmp_path.iterdir()) == []


def test_injected_approved_review_verifier_is_rechecked_before_link(
    tmp_path: Path,
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, "head")
    engine = _engine(path)
    session_factory = create_product_session_factory(engine=engine)
    reference = object.__new__(ApprovedPortfolioReviewReference)
    for name, value in {
        "review_id": "review-1",
        "source_id": "source-1",
        "source_digest": "1" * 64,
        "analysis_digest": "2" * 64,
        "decision_id": "decision-1",
        "decision_digest": "3" * 64,
        "outcome": "approved",
    }.items():
        object.__setattr__(reference, name, value)
    calls: list[str] = []
    authority = DeterministicAuthority()
    service = PaperAccountApplicationService(
        session_factory=session_factory,
        id_factory=authority.id,
        clock=authority.clock,
        approved_review_verifier=lambda review_id: (
            calls.append(review_id) or reference
        ),
    )
    created = _create(service)
    linked = service.link_approved_portfolio_review(
        account_id=created.account.account_id,
        expected_account_version=1,
        command_idempotency_key="link-1",
        actor="founder",
        reason="approved governance evidence",
        review_id="review-1",
    )
    assert calls == ["review-1"]
    assert linked.projection.approved_portfolio_reviews == (reference,)
    replay = service.link_approved_portfolio_review(
        account_id=created.account.account_id,
        expected_account_version=1,
        command_idempotency_key="link-1",
        actor="founder",
        reason="approved governance evidence",
        review_id="review-1",
    )
    assert replay.replayed
    assert calls == ["review-1"]
    engine.dispose()


def test_malformed_projection_decimal_is_corruption(
    tmp_path: Path,
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, "head")
    engine = _engine(path)
    session_factory = create_product_session_factory(engine=engine)
    service = _service(session_factory)
    created = _create(service)
    with engine.begin() as connection:
        connection.execute(
            update(PaperAccountProjectionRow)
            .where(
                PaperAccountProjectionRow.account_id
                == created.account.account_id
            )
            .values(cash_balance="100.0", available_cash="100.0")
        )
    from el_psy_quant.persistence import (
        PaperAccountPersistenceCorruptionError,
    )

    with pytest.raises(PaperAccountPersistenceCorruptionError):
        service.get_current_projection(account_id=created.account.account_id)
    engine.dispose()
