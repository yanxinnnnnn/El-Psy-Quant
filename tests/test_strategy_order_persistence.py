"""Focused Sprint 202 migration, persistence, and application coverage."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.exc import DatabaseError

from el_psy_quant.application import (
    PaperAccountApplicationService,
    StrategyOrderApplicationService,
    StrategyOrderIdempotencyConflictError,
    StrategyOrderReconciliationRequiredError,
    StrategyOrderStaleAuthorityError,
    StrategyOrderStorageBusyError,
)
from el_psy_quant.market_time import (
    MarketDataReplayEngine,
    create_market_data_event,
    create_trading_calendar,
    create_trading_session,
)
from el_psy_quant.paper_account import PaperMoney, PaperQuantity
from el_psy_quant.persistence import (
    SqlAlchemyMarketTimeRepository,
    SqlAlchemyOrderIntentRepository,
    SqlAlchemyPreTradeRiskDecisionRepository,
    SqlAlchemyStrategySignalRepository,
    StrategyOrderCorruptAuthorityError,
    create_market_data_replay_record,
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV
from el_psy_quant.persistence.schema import (
    CURRENT_PRODUCT_SCHEMA_REVISION,
    REQUIRED_PRODUCT_INDEXES,
    REQUIRED_PRODUCT_TABLE_COLUMNS,
    REQUIRED_PRODUCT_TRIGGERS,
    verify_product_schema,
)
from el_psy_quant.strategy_order import (
    PRE_TRADE_RISK_OUTCOME_ALLOW,
    PRE_TRADE_RISK_OUTCOME_REJECT,
    create_long_only_cash_risk_policy_reference,
    create_moving_average_crossover_runtime_reference,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREVIOUS_REVISION = "0009_market_time_runtime"
REVISION = "0010_strategy_order_risk"
CREATED = datetime(2026, 7, 31, 9, tzinfo=timezone.utc)
INSTRUMENT = "XNYS:AAPL"
NEW_TABLES = {
    "strategy_signals",
    "order_intents",
    "pre_trade_risk_decisions",
    "strategy_order_command_receipts",
}


def _config() -> Config:
    return Config(str(PROJECT_ROOT / "alembic.ini"))


def _engine(path: Path):
    return create_product_database_engine(
        config=resolve_product_database_config(database_path=path)
    )


def _migrate(path: Path, monkeypatch: pytest.MonkeyPatch, revision: str) -> None:
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    command.upgrade(_config(), revision)


def _seed(path: Path, *, initial_position: str | None = None):
    engine = _engine(path)
    factory = create_product_session_factory(engine=engine)
    counters: dict[str, int] = {}

    def identifier(kind: str) -> str:
        counters[kind] = counters.get(kind, 0) + 1
        return f"{kind}-s202-{counters[kind]}"

    account_service = PaperAccountApplicationService(
        session_factory=factory,
        clock=lambda: CREATED,
        id_factory=identifier,
    )
    account = account_service.create_account(
        display_name="Sprint 202 account",
        base_currency="USD",
        initial_cash=PaperMoney.parse("2000"),
        creation_idempotency_key="create-s202-account",
        actor="founder",
    ).account
    if initial_position is not None:
        account = account_service.post_position_adjustment(
            account_id=account.account_id,
            expected_account_version=account.head_version,
            command_idempotency_key="opening-position-s202",
            actor="founder",
            reason="deterministic Sprint 202 fixture",
            symbol=INSTRUMENT,
            adjustment_category="opening_balance",
            signed_quantity_delta=PaperQuantity.parse(initial_position),
            signed_cost_basis_delta=PaperMoney.parse("0"),
        ).account

    calendar = create_trading_calendar(
        id="calendar-s202",
        market="XNYS",
        timezone="UTC",
        calendar_version=1,
        created_at=CREATED,
    )
    session = create_trading_session(
        id="session-s202",
        calendar_id=calendar.id,
        trading_date=date(2026, 7, 31),
        open_time=CREATED,
        close_time=CREATED + timedelta(hours=8),
        session_type="regular",
    )
    events = [
        create_market_data_event(
            event_id=f"event-s202-{index}",
            instrument_id=INSTRUMENT,
            event_time=CREATED + timedelta(minutes=index),
            event_type="trade",
            payload={"price": price},
            source="fixture:s202",
        )
        for index, price in enumerate((3, 2, 1, 4), start=1)
    ]
    replay = MarketDataReplayEngine(replay_id="replay-s202", events=events)
    replay.start()
    tuple(replay.iter_remaining())
    with factory.begin() as db:
        repository = SqlAlchemyMarketTimeRepository(session=db)
        repository.add_calendar(calendar=calendar)
        repository.add_session(session=session)
        repository.add_replay(
            replay=create_market_data_replay_record(
                session=replay.session,
                events=replay.events,
            )
        )
    return engine, factory, account, calendar, session, replay


def _signal(service: StrategyOrderApplicationService, replay):
    runtime = create_moving_average_crossover_runtime_reference(
        fast_window=2,
        slow_window=3,
        target_position_quantity=PaperQuantity.parse("10"),
    )
    result = service.evaluate_and_store_strategy_signal(
        strategy_runtime_reference=runtime,
        calendar_id="calendar-s202",
        expected_calendar_version=1,
        trading_session_id="session-s202",
        replay_id="replay-s202",
        expected_event_stream_digest=replay.cursor.event_stream_digest,
        expected_cursor_position=4,
        expected_signal_event_id="event-s202-4",
        instrument_id=INSTRUMENT,
        command_idempotency_key="signal-command-s202",
        actor="founder",
        created_at=CREATED + timedelta(hours=9),
    )
    return result


def test_0010_is_additive_linear_append_only_and_current(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    scripts = ScriptDirectory.from_config(_config())
    assert scripts.get_heads() == [REVISION]
    assert scripts.get_revision(REVISION).down_revision == PREVIOUS_REVISION
    assert CURRENT_PRODUCT_SCHEMA_REVISION == REVISION

    _migrate(path, monkeypatch, PREVIOUS_REVISION)
    engine = _engine(path)
    before = set(inspect(engine).get_table_names())
    engine.dispose()
    _migrate(path, monkeypatch, REVISION)
    engine = _engine(path)
    try:
        inspector = inspect(engine)
        assert set(inspector.get_table_names()) == before | NEW_TABLES
        for table in NEW_TABLES:
            assert tuple(
                column["name"] for column in inspector.get_columns(table)
            ) == REQUIRED_PRODUCT_TABLE_COLUMNS[table]
            assert set(REQUIRED_PRODUCT_INDEXES[table]).issubset(
                {index["name"] for index in inspector.get_indexes(table)}
            )
        with engine.connect() as connection:
            triggers = {
                row[0]
                for row in connection.execute(
                    text(
                        "SELECT name FROM sqlite_master WHERE type = 'trigger'"
                    )
                )
            }
        assert {
            trigger
            for trigger in REQUIRED_PRODUCT_TRIGGERS
            if "strategy" in trigger
            or "order_intents" in trigger
            or "pre_trade" in trigger
        }.issubset(triggers)
        assert verify_product_schema(path) == REVISION
    finally:
        engine.dispose()


def test_populated_0009_upgrade_preserves_m31_m32_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, monkeypatch, PREVIOUS_REVISION)
    engine, _, _, _, _, _ = _seed(path, initial_position="7")
    try:
        table_names = tuple(
            table
            for table in inspect(engine).get_table_names()
            if table != "alembic_version"
        )
        with engine.connect() as connection:
            before = {
                table: tuple(
                    connection.execute(
                        text(f'SELECT * FROM "{table}" ORDER BY rowid')
                    ).all()
                )
                for table in table_names
            }
    finally:
        engine.dispose()

    _migrate(path, monkeypatch, REVISION)
    upgraded = _engine(path)
    try:
        with upgraded.connect() as connection:
            after = {
                table: tuple(
                    connection.execute(
                        text(f'SELECT * FROM "{table}" ORDER BY rowid')
                    ).all()
                )
                for table in table_names
            }
        assert after == before
        assert set(inspect(upgraded).get_table_names()) == (
            set(table_names) | NEW_TABLES | {"alembic_version"}
        )
    finally:
        upgraded.dispose()


def test_application_round_trip_replay_and_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, account, _, _, replay = _seed(path)
    service = StrategyOrderApplicationService(session_factory=factory)

    signal_result = _signal(service, replay)
    assert not signal_result.replayed
    assert _signal(service, replay) == type(signal_result)(
        result=signal_result.result,
        replayed=True,
    )
    intent_result = service.derive_and_store_order_intent(
        signal_id=signal_result.result.signal_id,
        account_id=account.account_id,
        expected_account_head_version=account.head_version,
        expected_account_head_event_id=account.head_event_id,
        expected_account_head_chain_digest=account.head_chain_digest,
        command_idempotency_key="intent-command-s202",
        actor="founder",
        created_at=CREATED + timedelta(hours=9, minutes=1),
    )
    assert not intent_result.replayed
    risk_result = service.evaluate_and_store_pre_trade_risk(
        intent_id=intent_result.result.intent_id,
        risk_policy_reference=create_long_only_cash_risk_policy_reference(),
        expected_account_head_version=account.head_version,
        expected_account_head_event_id=account.head_event_id,
        expected_account_head_chain_digest=account.head_chain_digest,
        expected_calendar_id="calendar-s202",
        expected_calendar_version=1,
        expected_trading_session_id="session-s202",
        expected_replay_id="replay-s202",
        expected_event_stream_digest=replay.cursor.event_stream_digest,
        expected_cursor_position=4,
        expected_current_event_id="event-s202-4",
        expected_instrument_id=INSTRUMENT,
        command_idempotency_key="risk-command-s202",
        actor="founder",
        created_at=CREATED + timedelta(hours=9, minutes=2),
    )
    assert risk_result.result.outcome == PRE_TRADE_RISK_OUTCOME_ALLOW
    engine.dispose()

    reopened = _engine(path)
    reopened_factory = create_product_session_factory(engine=reopened)
    restored = StrategyOrderApplicationService(
        session_factory=reopened_factory
    )
    assert (
        restored.get_strategy_signal(
            signal_id=signal_result.result.signal_id
        ).to_dict()
        == signal_result.result.to_dict()
    )
    assert (
        restored.get_order_intent(
            intent_id=intent_result.result.intent_id
        ).to_dict()
        == intent_result.result.to_dict()
    )
    assert (
        restored.get_pre_trade_risk_decision(
            decision_id=risk_result.result.decision_id
        ).to_dict()
        == risk_result.result.to_dict()
    )
    reopened.dispose()


def test_alternate_signal_keys_converge_and_pages_are_bounded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, _, _, _, replay = _seed(path)
    service = StrategyOrderApplicationService(session_factory=factory)
    first = _signal(service, replay)
    runtime = first.result.strategy_runtime_reference
    second = service.evaluate_and_store_strategy_signal(
        strategy_runtime_reference=runtime,
        calendar_id="calendar-s202",
        expected_calendar_version=1,
        trading_session_id="session-s202",
        replay_id="replay-s202",
        expected_event_stream_digest=replay.cursor.event_stream_digest,
        expected_cursor_position=4,
        expected_signal_event_id="event-s202-4",
        instrument_id=INSTRUMENT,
        command_idempotency_key="alternate-signal-key",
        actor="another-actor",
        created_at=CREATED + timedelta(days=1),
    )
    assert second.result.signal_id == first.result.signal_id
    with factory() as db:
        repository = SqlAlchemyStrategySignalRepository(session=db)
        page = repository.list_page(limit=1, instrument_id=INSTRUMENT)
        assert page.items == (first.result,)
        assert not page.has_more
        with pytest.raises(ValueError, match="1 to 200"):
            repository.list_page(limit=201)
    engine.dispose()


def test_same_key_changed_command_conflicts_and_concurrent_retry_converges(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, _, _, _, replay = _seed(path)
    service = StrategyOrderApplicationService(session_factory=factory)
    first = _signal(service, replay)
    changed_runtime = create_moving_average_crossover_runtime_reference(
        fast_window=1,
        slow_window=3,
        target_position_quantity=PaperQuantity.parse("10"),
    )
    with pytest.raises(StrategyOrderIdempotencyConflictError):
        service.evaluate_and_store_strategy_signal(
            strategy_runtime_reference=changed_runtime,
            calendar_id="calendar-s202",
            expected_calendar_version=1,
            trading_session_id="session-s202",
            replay_id="replay-s202",
            expected_event_stream_digest=replay.cursor.event_stream_digest,
            expected_cursor_position=4,
            expected_signal_event_id="event-s202-4",
            instrument_id=INSTRUMENT,
            command_idempotency_key="signal-command-s202",
            actor="founder",
            created_at=CREATED,
        )

    def exact_retry():
        return _signal(
            StrategyOrderApplicationService(session_factory=factory), replay
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        retried = tuple(pool.map(lambda _value: exact_retry(), range(2)))
    assert all(item.replayed for item in retried)
    assert {item.result.signal_id for item in retried} == {
        first.result.signal_id
    }

    def simultaneous_initial():
        concurrent_service = StrategyOrderApplicationService(
            session_factory=factory
        )
        runtime = first.result.strategy_runtime_reference
        return concurrent_service.evaluate_and_store_strategy_signal(
            strategy_runtime_reference=runtime,
            calendar_id="calendar-s202",
            expected_calendar_version=1,
            trading_session_id="session-s202",
            replay_id="replay-s202",
            expected_event_stream_digest=replay.cursor.event_stream_digest,
            expected_cursor_position=4,
            expected_signal_event_id="event-s202-4",
            instrument_id=INSTRUMENT,
            command_idempotency_key="simultaneous-initial-s202",
            actor="concurrent-founder",
            created_at=CREATED + timedelta(days=2),
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        simultaneous = tuple(
            pool.map(lambda _value: simultaneous_initial(), range(2))
        )
    assert sorted(item.replayed for item in simultaneous) == [False, True]
    assert {item.result.signal_id for item in simultaneous} == {
        first.result.signal_id
    }
    engine.dispose()


def test_intent_and_decision_concurrency_conflict_and_alternate_key_convergence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, account, _, _, replay = _seed(path)
    signal = _signal(
        StrategyOrderApplicationService(session_factory=factory), replay
    ).result

    def create_intent():
        return StrategyOrderApplicationService(
            session_factory=factory
        ).derive_and_store_order_intent(
            signal_id=signal.signal_id,
            account_id=account.account_id,
            expected_account_head_version=account.head_version,
            expected_account_head_event_id=account.head_event_id,
            expected_account_head_chain_digest=account.head_chain_digest,
            command_idempotency_key="concurrent-intent-s202",
            actor="founder",
            created_at=CREATED + timedelta(hours=13),
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        intents = tuple(pool.map(lambda _value: create_intent(), range(2)))
    assert sorted(item.replayed for item in intents) == [False, True]
    intent = intents[0].result
    assert {item.result.intent_id for item in intents} == {intent.intent_id}

    service = StrategyOrderApplicationService(session_factory=factory)
    alternate_intent = service.derive_and_store_order_intent(
        signal_id=signal.signal_id,
        account_id=account.account_id,
        expected_account_head_version=account.head_version,
        expected_account_head_event_id=account.head_event_id,
        expected_account_head_chain_digest=account.head_chain_digest,
        command_idempotency_key="alternate-intent-s202",
        actor="alternate-founder",
        created_at=CREATED + timedelta(days=1),
    )
    assert not alternate_intent.replayed
    assert alternate_intent.result.intent_id == intent.intent_id
    with pytest.raises(StrategyOrderIdempotencyConflictError):
        service.derive_and_store_order_intent(
            signal_id=signal.signal_id,
            account_id=account.account_id,
            expected_account_head_version=account.head_version,
            expected_account_head_event_id=account.head_event_id,
            expected_account_head_chain_digest=account.head_chain_digest,
            command_idempotency_key="concurrent-intent-s202",
            actor="changed-actor",
            created_at=CREATED,
        )

    policy = create_long_only_cash_risk_policy_reference()

    def create_decision():
        return StrategyOrderApplicationService(
            session_factory=factory
        ).evaluate_and_store_pre_trade_risk(
            intent_id=intent.intent_id,
            risk_policy_reference=policy,
            expected_account_head_version=account.head_version,
            expected_account_head_event_id=account.head_event_id,
            expected_account_head_chain_digest=account.head_chain_digest,
            expected_calendar_id="calendar-s202",
            expected_calendar_version=1,
            expected_trading_session_id="session-s202",
            expected_replay_id="replay-s202",
            expected_event_stream_digest=replay.cursor.event_stream_digest,
            expected_cursor_position=4,
            expected_current_event_id="event-s202-4",
            expected_instrument_id=INSTRUMENT,
            command_idempotency_key="concurrent-risk-s202",
            actor="founder",
            created_at=CREATED + timedelta(hours=14),
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        decisions = tuple(
            pool.map(lambda _value: create_decision(), range(2))
        )
    assert sorted(item.replayed for item in decisions) == [False, True]
    decision = decisions[0].result
    assert {item.result.decision_id for item in decisions} == {
        decision.decision_id
    }
    alternate_decision = service.evaluate_and_store_pre_trade_risk(
        intent_id=intent.intent_id,
        risk_policy_reference=policy,
        expected_account_head_version=account.head_version,
        expected_account_head_event_id=account.head_event_id,
        expected_account_head_chain_digest=account.head_chain_digest,
        expected_calendar_id="calendar-s202",
        expected_calendar_version=1,
        expected_trading_session_id="session-s202",
        expected_replay_id="replay-s202",
        expected_event_stream_digest=replay.cursor.event_stream_digest,
        expected_cursor_position=4,
        expected_current_event_id="event-s202-4",
        expected_instrument_id=INSTRUMENT,
        command_idempotency_key="alternate-risk-s202",
        actor="alternate-founder",
        created_at=CREATED + timedelta(days=1),
    )
    assert not alternate_decision.replayed
    assert alternate_decision.result.decision_id == decision.decision_id
    with pytest.raises(StrategyOrderIdempotencyConflictError):
        service.evaluate_and_store_pre_trade_risk(
            intent_id=intent.intent_id,
            risk_policy_reference=create_long_only_cash_risk_policy_reference(
                maximum_order_notional=PaperMoney.parse("1")
            ),
            expected_account_head_version=account.head_version,
            expected_account_head_event_id=account.head_event_id,
            expected_account_head_chain_digest=account.head_chain_digest,
            expected_calendar_id="calendar-s202",
            expected_calendar_version=1,
            expected_trading_session_id="session-s202",
            expected_replay_id="replay-s202",
            expected_event_stream_digest=replay.cursor.event_stream_digest,
            expected_cursor_position=4,
            expected_current_event_id="event-s202-4",
            expected_instrument_id=INSTRUMENT,
            command_idempotency_key="concurrent-risk-s202",
            actor="founder",
            created_at=CREATED,
        )
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT COUNT(*) FROM order_intents")) == 1
        assert (
            connection.scalar(
                text("SELECT COUNT(*) FROM pre_trade_risk_decisions")
            )
            == 1
        )
    engine.dispose()


def test_corrupt_metadata_and_append_only_mutation_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, _, _, _, replay = _seed(path)
    result = _signal(
        StrategyOrderApplicationService(session_factory=factory), replay
    ).result
    with engine.begin() as connection:
        with pytest.raises(DatabaseError, match="append-only"):
            connection.execute(
                text(
                    "UPDATE strategy_signals SET instrument_id = 'XNAS:MSFT' "
                    "WHERE signal_id = :signal_id"
                ),
                {"signal_id": result.signal_id},
            )
        with pytest.raises(DatabaseError, match="cannot be deleted"):
            connection.execute(
                text(
                    "DELETE FROM strategy_order_command_receipts "
                    "WHERE namespace = 'evaluate_strategy_signal'"
                )
            )
    engine.dispose()


def test_repository_round_trips_all_three_authorities(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, account, _, _, replay = _seed(path)
    service = StrategyOrderApplicationService(session_factory=factory)
    signal = _signal(service, replay).result
    intent = service.derive_and_store_order_intent(
        signal_id=signal.signal_id,
        account_id=account.account_id,
        expected_account_head_version=account.head_version,
        expected_account_head_event_id=account.head_event_id,
        expected_account_head_chain_digest=account.head_chain_digest,
        command_idempotency_key="intent-repository-roundtrip",
        actor="founder",
        created_at=CREATED + timedelta(hours=10),
    ).result
    decision = service.evaluate_and_store_pre_trade_risk(
        intent_id=intent.intent_id,
        risk_policy_reference=create_long_only_cash_risk_policy_reference(),
        expected_account_head_version=account.head_version,
        expected_account_head_event_id=account.head_event_id,
        expected_account_head_chain_digest=account.head_chain_digest,
        expected_calendar_id="calendar-s202",
        expected_calendar_version=1,
        expected_trading_session_id="session-s202",
        expected_replay_id="replay-s202",
        expected_event_stream_digest=replay.cursor.event_stream_digest,
        expected_cursor_position=4,
        expected_current_event_id="event-s202-4",
        expected_instrument_id=INSTRUMENT,
        command_idempotency_key="risk-repository-roundtrip",
        actor="founder",
        created_at=CREATED + timedelta(hours=10, minutes=1),
    ).result
    with factory() as db:
        assert (
            SqlAlchemyStrategySignalRepository(session=db).get(
                signal_id=signal.signal_id
            )
            == signal
        )
        assert (
            SqlAlchemyOrderIntentRepository(session=db).get(
                intent_id=intent.intent_id
            )
            == intent
        )
        assert (
            SqlAlchemyPreTradeRiskDecisionRepository(session=db).get(
                decision_id=decision.decision_id
            )
            == decision
        )
    engine.dispose()


def test_no_action_is_receipt_evidence_without_an_intent_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, account, _, _, replay = _seed(
        path, initial_position="10"
    )
    service = StrategyOrderApplicationService(session_factory=factory)
    signal = _signal(service, replay).result

    def derive_no_action():
        return StrategyOrderApplicationService(
            session_factory=factory
        ).derive_and_store_order_intent(
            signal_id=signal.signal_id,
            account_id=account.account_id,
            expected_account_head_version=account.head_version,
            expected_account_head_event_id=account.head_event_id,
            expected_account_head_chain_digest=account.head_chain_digest,
            command_idempotency_key="no-action-command-s202",
            actor="founder",
            created_at=CREATED + timedelta(hours=11),
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        concurrent = tuple(
            pool.map(lambda _value: derive_no_action(), range(2))
        )
    assert sorted(item.replayed for item in concurrent) == [False, True]
    first = concurrent[0]
    replayed = service.derive_and_store_order_intent(
        signal_id=signal.signal_id,
        account_id=account.account_id,
        expected_account_head_version=account.head_version,
        expected_account_head_event_id=account.head_event_id,
        expected_account_head_chain_digest=account.head_chain_digest,
        command_idempotency_key="no-action-command-s202",
        actor="founder",
        created_at=CREATED + timedelta(days=1),
    )
    assert all(
        item.result.to_dict() == first.result.to_dict()
        for item in (*concurrent, replayed)
    )
    assert replayed.replayed
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT COUNT(*) FROM order_intents")) == 0
        assert (
            connection.scalar(
                text(
                    "SELECT COUNT(*) FROM strategy_order_command_receipts "
                    "WHERE result_kind = 'order_intent_no_action'"
                )
            )
            == 1
        )
    engine.dispose()


def test_sell_stale_reconciliation_and_storage_busy_boundaries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, account, _, _, replay = _seed(
        path, initial_position="20"
    )
    service = StrategyOrderApplicationService(session_factory=factory)
    signal = _signal(service, replay).result
    sell = service.derive_and_store_order_intent(
        signal_id=signal.signal_id,
        account_id=account.account_id,
        expected_account_head_version=account.head_version,
        expected_account_head_event_id=account.head_event_id,
        expected_account_head_chain_digest=account.head_chain_digest,
        command_idempotency_key="sell-intent-s202",
        actor="founder",
        created_at=CREATED + timedelta(hours=15),
    ).result
    assert sell.side == "sell"

    with pytest.raises(StrategyOrderStaleAuthorityError):
        service.derive_and_store_order_intent(
            signal_id=signal.signal_id,
            account_id=account.account_id,
            expected_account_head_version=account.head_version + 1,
            expected_account_head_event_id=account.head_event_id,
            expected_account_head_chain_digest=account.head_chain_digest,
            command_idempotency_key="stale-intent-s202",
            actor="founder",
            created_at=CREATED,
        )
    with pytest.raises(StrategyOrderStaleAuthorityError):
        service.evaluate_and_store_strategy_signal(
            strategy_runtime_reference=signal.strategy_runtime_reference,
            calendar_id="calendar-s202",
            expected_calendar_version=1,
            trading_session_id="session-s202",
            replay_id="replay-s202",
            expected_event_stream_digest=replay.cursor.event_stream_digest,
            expected_cursor_position=3,
            expected_signal_event_id="event-s202-3",
            instrument_id=INSTRUMENT,
            command_idempotency_key="stale-signal-s202",
            actor="founder",
            created_at=CREATED,
        )

    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE paper_accounts "
                "SET projection_status = 'reconciliation_required' "
                "WHERE account_id = :account_id"
            ),
            {"account_id": account.account_id},
        )
    with pytest.raises(StrategyOrderReconciliationRequiredError):
        service.derive_and_store_order_intent(
            signal_id=signal.signal_id,
            account_id=account.account_id,
            expected_account_head_version=account.head_version,
            expected_account_head_event_id=account.head_event_id,
            expected_account_head_chain_digest=account.head_chain_digest,
            command_idempotency_key="reconciliation-intent-s202",
            actor="founder",
            created_at=CREATED,
        )

    blocker = engine.connect()
    try:
        blocker.exec_driver_sql("BEGIN IMMEDIATE")
        with pytest.raises(StrategyOrderStorageBusyError):
            service.evaluate_and_store_strategy_signal(
                strategy_runtime_reference=signal.strategy_runtime_reference,
                calendar_id="calendar-s202",
                expected_calendar_version=1,
                trading_session_id="session-s202",
                replay_id="replay-s202",
                expected_event_stream_digest=replay.cursor.event_stream_digest,
                expected_cursor_position=4,
                expected_signal_event_id="event-s202-4",
                instrument_id=INSTRUMENT,
                command_idempotency_key="storage-busy-s202",
                actor="founder",
                created_at=CREATED,
            )
    finally:
        blocker.rollback()
        blocker.close()
        engine.dispose()


def test_reject_decision_round_trips_as_immutable_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, account, _, _, replay = _seed(path)
    service = StrategyOrderApplicationService(session_factory=factory)
    signal = _signal(service, replay).result
    intent = service.derive_and_store_order_intent(
        signal_id=signal.signal_id,
        account_id=account.account_id,
        expected_account_head_version=account.head_version,
        expected_account_head_event_id=account.head_event_id,
        expected_account_head_chain_digest=account.head_chain_digest,
        command_idempotency_key="reject-intent-s202",
        actor="founder",
        created_at=CREATED + timedelta(hours=12),
    ).result
    rejected = service.evaluate_and_store_pre_trade_risk(
        intent_id=intent.intent_id,
        risk_policy_reference=create_long_only_cash_risk_policy_reference(
            maximum_order_notional=PaperMoney.parse("1")
        ),
        expected_account_head_version=account.head_version,
        expected_account_head_event_id=account.head_event_id,
        expected_account_head_chain_digest=account.head_chain_digest,
        expected_calendar_id="calendar-s202",
        expected_calendar_version=1,
        expected_trading_session_id="session-s202",
        expected_replay_id="replay-s202",
        expected_event_stream_digest=replay.cursor.event_stream_digest,
        expected_cursor_position=4,
        expected_current_event_id="event-s202-4",
        expected_instrument_id=INSTRUMENT,
        command_idempotency_key="reject-risk-s202",
        actor="founder",
        created_at=CREATED + timedelta(hours=12, minutes=1),
    ).result
    assert rejected.outcome == PRE_TRADE_RISK_OUTCOME_REJECT
    assert service.get_pre_trade_risk_decision(
        decision_id=rejected.decision_id
    ).to_dict() == rejected.to_dict()
    engine.dispose()


def test_duplicate_key_json_corruption_fails_strict_get(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, _, _, _, replay = _seed(path)
    _signal(StrategyOrderApplicationService(session_factory=factory), replay)
    digest = "0" * 64
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO strategy_signals "
                "SELECT record_schema_version, signal_schema_version, "
                ":signal_id, :digest, :payload, strategy_name, "
                "strategy_version, adapter_version, parameters_digest, "
                "calendar_id, calendar_version, trading_session_id, replay_id, "
                "event_stream_digest, cursor_position, signal_event_id, "
                "instrument_id, target_semantics, target_position_quantity, "
                "created_at FROM strategy_signals LIMIT 1"
            ),
            {
                "signal_id": f"sig_{digest}",
                "digest": digest,
                "payload": '{"schema_version":1,"schema_version":1}',
            },
        )
    with factory() as db:
        with pytest.raises(StrategyOrderCorruptAuthorityError):
            SqlAlchemyStrategySignalRepository(session=db).get(
                signal_id=f"sig_{digest}"
            )
    engine.dispose()
