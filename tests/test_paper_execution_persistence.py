"""Focused Sprint 211 persistence and Sprint 215 adversarial hardening coverage."""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import event, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import el_psy_quant.application.paper_execution as paper_execution_application

from el_psy_quant.application import (
    PaperAccountApplicationService,
    PaperExecutionApplicationService,
    StrategyOrderApplicationService,
)
from el_psy_quant.market_time import (
    MarketDataReplayEngine,
    ReplayCursor,
    create_market_data_event,
    create_trading_calendar,
    create_trading_session,
)
from el_psy_quant.paper_account import PaperMoney, PaperQuantity
from el_psy_quant.paper_account.events import _create_event
from el_psy_quant.paper_execution import (
    PaperExecutionBasisPoints,
    create_paper_execution_order_command,
    create_paper_execution_order_reference,
    create_paper_execution_policy_reference,
    create_paper_execution_risk_handoff_reference,
    create_step_paper_execution_order_command,
)
from el_psy_quant.paper_execution.costs import _build as _build_cost_evidence
from el_psy_quant.paper_execution.fills import _build_fill
from el_psy_quant.persistence import (
    PaperExecutionConcurrencyConflictError,
    PaperExecutionCorruptAuthorityError,
    PaperExecutionIdempotencyConflictError,
    PaperExecutionOperationConflictError,
    PaperExecutionReconciliationRequiredError,
    PaperExecutionStaleAuthorityError,
    PaperExecutionStorageBusyError,
    PaperExecutionStorageFailureError,
    SqlAlchemyMarketTimeRepository,
    SqlAlchemyPaperExecutionRepository,
    create_market_data_replay_record,
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)
from el_psy_quant.persistence.paper_account_repository import (
    SqlAlchemyPaperAccountRepository,
)
from el_psy_quant.persistence.paper_execution_mapping import fill_row
from el_psy_quant.persistence.paper_accounts import (
    PaperAccountPersistenceCorruptionError,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV
from el_psy_quant.persistence.schema import (
    CURRENT_PRODUCT_SCHEMA_REVISION,
    REQUIRED_PRODUCT_INDEXES,
    REQUIRED_PRODUCT_TABLE_COLUMNS,
    verify_product_schema,
)
from el_psy_quant.strategy_order import (
    create_long_only_cash_risk_policy_reference,
    create_moving_average_crossover_runtime_reference,
    create_order_intent_reference,
)
from el_psy_quant.paper_execution.orders import _build_order
from el_psy_quant.paper_execution.upstream_references import (
    _build_account_handoff,
    _build_market_handoff,
    _build_risk_handoff,
)

ROOT = Path(__file__).resolve().parents[1]
CREATED = datetime(2026, 8, 19, 1, tzinfo=timezone.utc)
AUDIT = CREATED + timedelta(hours=10)
INSTRUMENT = "XNYS:AAPL"
TABLES = {
    "paper_execution_orders",
    "paper_execution_attempts",
    "paper_execution_fills",
    "paper_execution_settlement_links",
    "paper_execution_command_receipts",
    "paper_runtimes",
    "paper_runtime_work",
    "paper_runtime_checkpoints",
    "paper_runtime_events",
    "paper_runtime_command_receipts",
}


def _config() -> Config:
    return Config(str(ROOT / "alembic.ini"))


def _migrate(path: Path, monkeypatch: pytest.MonkeyPatch, revision: str) -> None:
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    command.upgrade(_config(), revision)


def _fixture(
    path: Path,
    *,
    fixture_id: str = "s211",
    calendar_version: int = 1,
    signal_prices: tuple[object, ...] = (3, 2, 1, 4),
    extra_events: tuple[tuple[str, str, dict[str, object], int], ...] = (
        ("XNYS:MSFT", "trade", {"price": 9}, 5),
        (INSTRUMENT, "trade", {"price": 5}, 6),
    ),
    session_close_minutes: int = 480,
    max_fill_quantity: str | None = None,
    initial_position: tuple[str, str] | None = None,
):
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=path)
    )
    factory = create_product_session_factory(engine=engine)
    counter: dict[str, int] = {}

    def identifier(kind: str) -> str:
        counter[kind] = counter.get(kind, 0) + 1
        return f"{kind}-{fixture_id}-{counter[kind]}"

    account = (
        PaperAccountApplicationService(
            session_factory=factory,
            clock=lambda: CREATED,
            id_factory=identifier,
        )
        .create_account(
            display_name="Sprint 211 account",
            base_currency="USD",
            initial_cash=PaperMoney.parse("2000"),
            creation_idempotency_key=f"create-account-{fixture_id}",
            actor="founder",
        )
        .account
    )
    if initial_position is not None:
        account = (
            PaperAccountApplicationService(
                session_factory=factory,
                clock=lambda: CREATED,
                id_factory=identifier,
            )
            .post_position_adjustment(
                account_id=account.account_id,
                expected_account_version=account.head_version,
                command_idempotency_key=f"opening-position-{fixture_id}",
                actor="founder",
                reason="deterministic Sprint 211 fixture",
                symbol=INSTRUMENT,
                adjustment_category="opening_balance",
                signed_quantity_delta=PaperQuantity.parse(initial_position[0]),
                signed_cost_basis_delta=PaperMoney.parse(initial_position[1]),
            )
            .account
        )
    calendar = create_trading_calendar(
        id=f"calendar-{fixture_id}",
        market="XNYS",
        timezone="UTC",
        calendar_version=calendar_version,
        created_at=CREATED,
    )
    trading_session = create_trading_session(
        id=f"session-{fixture_id}",
        calendar_id=calendar.id,
        trading_date=date(2026, 8, 19),
        open_time=CREATED,
        close_time=CREATED + timedelta(minutes=session_close_minutes),
        session_type="regular",
    )
    signal_events = tuple(
        create_market_data_event(
            event_id=f"event-{fixture_id}-{index}",
            instrument_id=INSTRUMENT,
            event_time=CREATED + timedelta(minutes=index),
            event_type="trade",
            payload={"price": price},
            source=f"fixture:{fixture_id}",
        )
        for index, price in enumerate(signal_prices, start=1)
    )
    events = signal_events + tuple(
        create_market_data_event(
            event_id=f"event-{fixture_id}-{index + len(signal_events)}",
            instrument_id=instrument_id,
            event_time=CREATED + timedelta(minutes=minute),
            event_type=event_type,
            payload=payload,
            source=f"fixture:{fixture_id}",
        )
        for index, (instrument_id, event_type, payload, minute) in enumerate(
            extra_events, start=1
        )
    )
    replay = MarketDataReplayEngine(replay_id=f"replay-{fixture_id}", events=events)
    replay.start()
    for _ in range(4):
        assert replay.next_event() is not None
    with factory.begin() as db:
        market = SqlAlchemyMarketTimeRepository(session=db)
        market.add_calendar(calendar=calendar)
        market.add_session(session=trading_session)
        market.add_replay(
            replay=create_market_data_replay_record(
                session=replay.session, events=replay.events
            )
        )

    strategy = StrategyOrderApplicationService(session_factory=factory)
    signal = strategy.evaluate_and_store_strategy_signal(
        strategy_runtime_reference=create_moving_average_crossover_runtime_reference(
            fast_window=2,
            slow_window=3,
            target_position_quantity=PaperQuantity.parse("10"),
        ),
        calendar_id=calendar.id,
        expected_calendar_version=calendar.calendar_version,
        trading_session_id=trading_session.id,
        replay_id=replay.session.replay_id,
        expected_event_stream_digest=replay.cursor.event_stream_digest,
        expected_cursor_position=4,
        expected_signal_event_id=events[3].event_id,
        instrument_id=INSTRUMENT,
        command_idempotency_key=f"signal-{fixture_id}",
        actor="founder",
        created_at=AUDIT,
    ).result
    intent = strategy.derive_and_store_order_intent(
        signal_id=signal.signal_id,
        account_id=account.account_id,
        expected_account_head_version=account.head_version,
        expected_account_head_event_id=account.head_event_id,
        expected_account_head_chain_digest=account.head_chain_digest,
        command_idempotency_key=f"intent-{fixture_id}",
        actor="founder",
        created_at=AUDIT + timedelta(minutes=1),
    ).result
    decision = strategy.evaluate_and_store_pre_trade_risk(
        intent_id=intent.intent_id,
        risk_policy_reference=create_long_only_cash_risk_policy_reference(),
        expected_account_head_version=account.head_version,
        expected_account_head_event_id=account.head_event_id,
        expected_account_head_chain_digest=account.head_chain_digest,
        expected_calendar_id=calendar.id,
        expected_calendar_version=calendar.calendar_version,
        expected_trading_session_id=trading_session.id,
        expected_replay_id=replay.session.replay_id,
        expected_event_stream_digest=replay.cursor.event_stream_digest,
        expected_cursor_position=4,
        expected_current_event_id=events[3].event_id,
        expected_instrument_id=INSTRUMENT,
        command_idempotency_key=f"risk-{fixture_id}",
        actor="founder",
        created_at=AUDIT + timedelta(minutes=2),
    ).result
    zero = PaperExecutionBasisPoints.parse("0")
    policy = create_paper_execution_policy_reference(
        max_fill_quantity_per_trade_event=(
            None
            if max_fill_quantity is None
            else PaperQuantity.parse(max_fill_quantity)
        ),
        slippage_bps=zero,
        commission_bps=zero,
        fee_bps=zero,
        buy_tax_bps=zero,
        sell_tax_bps=zero,
    )
    create_command = create_paper_execution_order_command(
        order_intent_reference=create_order_intent_reference(intent),
        risk_handoff_reference=create_paper_execution_risk_handoff_reference(
            decision=decision, intent=intent
        ),
        execution_policy_reference=policy,
        command_idempotency_key=f"create-order-{fixture_id}",
        actor="founder",
    )
    return engine, factory, create_command


def test_0011_is_additive_linear_and_has_five_empty_tables(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    scripts = ScriptDirectory.from_config(_config())
    assert scripts.get_heads() == ["0012_durable_paper_runtime"]
    assert (
        scripts.get_revision("0011_paper_execution").down_revision
        == "0010_strategy_order_risk"
    )
    assert CURRENT_PRODUCT_SCHEMA_REVISION == "0012_durable_paper_runtime"
    _migrate(path, monkeypatch, "0010_strategy_order_risk")
    before_engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=path)
    )
    before = set(inspect(before_engine).get_table_names())
    before_engine.dispose()
    _migrate(path, monkeypatch, "head")
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=path)
    )
    try:
        inspector = inspect(engine)
        assert set(inspector.get_table_names()) == before | TABLES
        for table in TABLES:
            assert (
                tuple(c["name"] for c in inspector.get_columns(table))
                == REQUIRED_PRODUCT_TABLE_COLUMNS[table]
            )
            assert set(REQUIRED_PRODUCT_INDEXES[table]).issubset(
                {index["name"] for index in inspector.get_indexes(table)}
            )
        with engine.connect() as connection:
            assert all(
                connection.scalar(text(f"SELECT COUNT(*) FROM {table}")) == 0
                for table in TABLES
            )
        assert verify_product_schema(path) == "0012_durable_paper_runtime"
    finally:
        engine.dispose()


def test_populated_0010_upgrade_preserves_m31_m32_m33_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, monkeypatch, "0010_strategy_order_risk")
    engine, factory, create_command = _fixture(path)
    strategy = StrategyOrderApplicationService(session_factory=factory)
    intent = strategy.get_order_intent(
        intent_id=create_command.order_intent_reference.intent_id
    )
    reject = strategy.evaluate_and_store_pre_trade_risk(
        intent_id=intent.intent_id,
        risk_policy_reference=create_long_only_cash_risk_policy_reference(
            maximum_order_quantity=PaperQuantity.parse("1")
        ),
        expected_account_head_version=intent.account_reference.account_head_version,
        expected_account_head_event_id=intent.account_reference.account_head_event_id,
        expected_account_head_chain_digest=(
            intent.account_reference.account_head_chain_digest
        ),
        expected_calendar_id=intent.market_reference.calendar_id,
        expected_calendar_version=intent.market_reference.calendar_version,
        expected_trading_session_id=intent.market_reference.trading_session_id,
        expected_replay_id=intent.market_reference.replay_id,
        expected_event_stream_digest=intent.market_reference.event_stream_digest,
        expected_cursor_position=intent.market_reference.cursor_position,
        expected_current_event_id=intent.market_reference.signal_event_id,
        expected_instrument_id=intent.market_reference.instrument_id,
        command_idempotency_key="risk-reject-s215-upgrade",
        actor="founder",
        created_at=AUDIT + timedelta(minutes=3),
    ).result
    assert reject.outcome == "reject"
    predecessor_tables = (
        "paper_accounts",
        "paper_account_events",
        "paper_cash_ledger_entries",
        "paper_account_projections",
        "trading_calendars",
        "trading_sessions",
        "market_data_events",
        "market_data_replays",
        "market_data_replay_events",
        "strategy_signals",
        "order_intents",
        "pre_trade_risk_decisions",
        "strategy_order_command_receipts",
    )
    with engine.connect() as connection:
        before = {
            table: tuple(
                connection.execute(text(f'SELECT * FROM "{table}" ORDER BY rowid'))
            )
            for table in predecessor_tables
        }
    engine.dispose()

    _migrate(path, monkeypatch, "head")
    upgraded = create_product_database_engine(
        config=resolve_product_database_config(database_path=path)
    )
    try:
        with upgraded.connect() as connection:
            assert {
                table: tuple(
                    connection.execute(text(f'SELECT * FROM "{table}" ORDER BY rowid'))
                )
                for table in predecessor_tables
            } == before
            assert all(
                connection.scalar(text(f'SELECT COUNT(*) FROM "{table}"')) == 0
                for table in TABLES
            )
            assert connection.scalar(
                text("SELECT version_num FROM alembic_version")
            ) == ("0012_durable_paper_runtime")
        assert verify_product_schema(path) == "0012_durable_paper_runtime"
        upgraded_factory = create_product_session_factory(engine=upgraded)
        execution = PaperExecutionApplicationService(
            session_factory=upgraded_factory,
            clock=lambda: AUDIT + timedelta(hours=1),
        )
        order = execution.create_order(create_command).result
        committed = execution.step_order(
            _step_command(order, version=0, key="post-upgrade-step-s215")
        ).result
        assert committed.step_result.attempt.execution_version_after == 1
        assert (
            execution.reconcile_order(
                execution_order_id=order.execution_order_id
            ).state.execution_version
            == 1
        )
        assert not (tmp_path / ".demo-install.json").exists()
        assert not (tmp_path / "workspace-descriptor.json").exists()
    finally:
        upgraded.dispose()


def test_create_no_fill_fill_replay_and_durable_reconciliation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, create_command = _fixture(path)
    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT + timedelta(hours=1)
    )
    created = service.create_order(create_command)
    assert not created.replayed
    assert service.create_order(create_command).replayed
    order = created.result

    first_command = create_step_paper_execution_order_command(
        execution_order_reference=create_paper_execution_order_reference(order),
        expected_execution_version=0,
        command_idempotency_key="step-no-fill-s211",
        actor="founder",
    )
    first = service.step_order(first_command)
    assert not first.replayed
    assert first.result.step_result.fill is None
    assert first.result.step_result.attempt.post_step_cursor.position == 5
    assert service.step_order(first_command).replayed

    fill_command = create_step_paper_execution_order_command(
        execution_order_reference=create_paper_execution_order_reference(order),
        expected_execution_version=1,
        command_idempotency_key="step-fill-s211",
        actor="founder",
    )
    filled = service.step_order(fill_command)
    assert filled.result.step_result.fill is not None
    assert filled.result.settlement_link is not None
    assert service.step_order(fill_command).replayed
    history = service.reconcile_order(execution_order_id=order.execution_order_id)
    assert history.state.status == "filled"
    assert len(history.attempts) == 2
    assert len(history.fills) == len(history.settlement_links) == 1

    with engine.connect() as connection:
        counts = {
            table: connection.scalar(text(f"SELECT COUNT(*) FROM {table}"))
            for table in TABLES
        }
        assert counts == {
            "paper_execution_orders": 1,
            "paper_execution_attempts": 2,
            "paper_execution_fills": 1,
            "paper_execution_settlement_links": 1,
            "paper_execution_command_receipts": 3,
            "paper_runtimes": 0,
            "paper_runtime_work": 0,
            "paper_runtime_checkpoints": 0,
            "paper_runtime_events": 0,
            "paper_runtime_command_receipts": 0,
        }
        assert (
            connection.scalar(
                text(
                    "SELECT COUNT(*) FROM paper_account_events WHERE event_type = 'execution_fill_posted'"
                )
            )
            == 1
        )
        assert connection.scalar(text("SELECT position FROM market_data_replays")) == 6
    engine.dispose()


def test_alternate_keys_converge_and_same_version_race_has_one_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, command_value = _fixture(path)
    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT + timedelta(hours=1)
    )
    order = service.create_order(command_value).result
    alternate_create = create_paper_execution_order_command(
        order_intent_reference=command_value.order_intent_reference,
        risk_handoff_reference=command_value.risk_handoff_reference,
        execution_policy_reference=command_value.execution_policy_reference,
        command_idempotency_key="alternate-create-s211",
        actor="founder-2",
    )
    assert service.create_order(alternate_create).result == order

    def run(key: str):
        return PaperExecutionApplicationService(
            session_factory=factory, clock=lambda: AUDIT + timedelta(hours=1)
        ).step_order(
            create_step_paper_execution_order_command(
                execution_order_reference=create_paper_execution_order_reference(order),
                expected_execution_version=0,
                command_idempotency_key=key,
                actor="founder",
            )
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(pool.map(run, ("race-a-s211", "race-b-s211")))
    assert (
        results[0].result.step_result.attempt == results[1].result.step_result.attempt
    )
    with engine.connect() as connection:
        assert (
            connection.scalar(text("SELECT COUNT(*) FROM paper_execution_orders")) == 1
        )
        assert (
            connection.scalar(text("SELECT COUNT(*) FROM paper_execution_attempts"))
            == 1
        )
        assert (
            connection.scalar(text("SELECT COUNT(*) FROM paper_execution_fills")) == 0
        )
        assert connection.scalar(text("SELECT position FROM market_data_replays")) == 5
        assert (
            connection.scalar(
                text("SELECT COUNT(*) FROM paper_execution_command_receipts")
            )
            == 4
        )
    engine.dispose()


def _step_command(order, *, version: int, key: str, actor: str = "founder"):
    return create_step_paper_execution_order_command(
        execution_order_reference=create_paper_execution_order_reference(order),
        expected_execution_version=version,
        command_idempotency_key=key,
        actor=actor,
    )


def _authority_counts(engine) -> dict[str, int]:
    with engine.connect() as connection:
        return {
            "attempts": connection.scalar(
                text("SELECT COUNT(*) FROM paper_execution_attempts")
            ),
            "fills": connection.scalar(
                text("SELECT COUNT(*) FROM paper_execution_fills")
            ),
            "links": connection.scalar(
                text("SELECT COUNT(*) FROM paper_execution_settlement_links")
            ),
            "receipts": connection.scalar(
                text("SELECT COUNT(*) FROM paper_execution_command_receipts")
            ),
            "account_events": connection.scalar(
                text(
                    "SELECT COUNT(*) FROM paper_account_events "
                    "WHERE event_type = 'execution_fill_posted'"
                )
            ),
            "cash": connection.scalar(
                text(
                    "SELECT COUNT(*) FROM paper_cash_ledger_entries "
                    "WHERE movement_type = 'execution_settlement'"
                )
            ),
            "positions": connection.scalar(
                text(
                    "SELECT COUNT(*) FROM paper_position_ledger_entries "
                    "WHERE adjustment_category = 'execution_fill'"
                )
            ),
            "cursor": connection.scalar(
                text("SELECT position FROM market_data_replays")
            ),
        }


def test_idempotency_conflicts_and_indexed_tamper_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, create_command = _fixture(path)
    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT
    )
    order = service.create_order(create_command).result
    conflicting_create = create_paper_execution_order_command(
        order_intent_reference=create_command.order_intent_reference,
        risk_handoff_reference=create_command.risk_handoff_reference,
        execution_policy_reference=create_command.execution_policy_reference,
        command_idempotency_key=create_command.command_idempotency_key,
        actor="different-actor",
    )
    with pytest.raises(PaperExecutionIdempotencyConflictError):
        service.create_order(conflicting_create)

    step = _step_command(order, version=0, key="same-step-key-s211")
    service.step_order(step)
    with pytest.raises(PaperExecutionIdempotencyConflictError):
        service.step_order(
            _step_command(
                order,
                version=0,
                key="same-step-key-s211",
                actor="different-actor",
            )
        )

    with engine.begin() as connection:
        connection.execute(text("DROP TRIGGER trg_paper_execution_orders_no_update"))
        connection.execute(
            text(
                "UPDATE paper_execution_orders SET instrument_id = 'XNYS:IBM' "
                "WHERE execution_order_id = :order_id"
            ),
            {"order_id": order.execution_order_id},
        )
    with pytest.raises(PaperExecutionCorruptAuthorityError):
        service.reconcile_order(execution_order_id=order.execution_order_id)
    engine.dispose()


@pytest.mark.parametrize("stale_authority", ["m31", "m32"])
def test_create_stale_handoff_leaves_no_order_or_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stale_authority: str,
) -> None:
    path = tmp_path / f"product-stale-{stale_authority}.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, create_command = _fixture(path)
    if stale_authority == "m31":
        with engine.connect() as connection:
            account_id = connection.scalar(
                text("SELECT account_id FROM paper_accounts")
            )
            account_version = connection.scalar(
                text("SELECT head_version FROM paper_accounts")
            )
        PaperAccountApplicationService(
            session_factory=factory, clock=lambda: AUDIT
        ).post_cash_movement(
            account_id=account_id,
            expected_account_version=account_version,
            command_idempotency_key="stale-account-s211",
            actor="founder",
            reason="make execution handoff stale",
            movement_type="deposit",
            requested_amount=PaperMoney.parse("1"),
        )
    else:
        with factory.begin() as session:
            repository = SqlAlchemyMarketTimeRepository(session=session)
            record = repository.get_replay(replay_id="replay-s211")
            assert record is not None
            replay_engine = MarketDataReplayEngine(
                replay_id=record.session.replay_id,
                events=record.events,
                cursor=record.session.cursor,
            )
            expected_cursor = replay_engine.cursor
            assert replay_engine.next_event() is not None
            assert repository.replace_replay_checkpoint(
                expected_cursor=expected_cursor,
                session=replay_engine.session,
            )

    with pytest.raises(PaperExecutionStaleAuthorityError):
        PaperExecutionApplicationService(
            session_factory=factory, clock=lambda: AUDIT
        ).create_order(create_command)
    with engine.connect() as connection:
        assert (
            connection.scalar(text("SELECT COUNT(*) FROM paper_execution_orders")) == 0
        )
        assert (
            connection.scalar(
                text("SELECT COUNT(*) FROM paper_execution_command_receipts")
            )
            == 0
        )
    engine.dispose()


@pytest.mark.parametrize("cas_target", ["m31", "m32"])
def test_fill_cas_failure_rolls_back_every_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cas_target: str,
) -> None:
    path = tmp_path / f"product-{cas_target}.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, create_command = _fixture(path)
    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT
    )
    order = service.create_order(create_command).result
    service.step_order(_step_command(order, version=0, key=f"prefill-{cas_target}"))
    before = _authority_counts(engine)

    if cas_target == "m31":
        monkeypatch.setattr(
            SqlAlchemyPaperAccountRepository,
            "append_mutation",
            lambda self, **kwargs: False,
        )
    else:
        monkeypatch.setattr(
            SqlAlchemyMarketTimeRepository,
            "replace_replay_checkpoint",
            lambda self, **kwargs: False,
        )
    with pytest.raises(PaperExecutionConcurrencyConflictError):
        service.step_order(
            _step_command(order, version=1, key=f"failing-fill-{cas_target}")
        )
    assert _authority_counts(engine) == before
    engine.dispose()


def test_failure_after_fill_derivation_rolls_back_all_flushed_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, create_command = _fixture(
        path,
        extra_events=((INSTRUMENT, "trade", {"price": 5}, 5),),
    )
    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT
    )
    order = service.create_order(create_command).result
    before = _authority_counts(engine)

    def fail_receipt(self, *, receipt):
        del self, receipt
        raise RuntimeError("injected after settlement flush")

    monkeypatch.setattr(
        SqlAlchemyPaperExecutionRepository, "append_receipt", fail_receipt
    )
    with pytest.raises(RuntimeError, match="injected"):
        service.step_order(_step_command(order, version=0, key="rollback-after-fill"))
    assert _authority_counts(engine) == before
    engine.dispose()


@pytest.mark.parametrize(
    ("extra_event", "expected_result"),
    [
        (("XNYS:MSFT", "trade", {"price": 9}, 5), "no_fill"),
        ((INSTRUMENT, "quote", {"bid": 4, "ask": 5}, 5), "no_fill"),
        ((INSTRUMENT, "trade", {"price": "invalid"}, 5), "no_fill"),
        ((INSTRUMENT, "trade", {"price": 500}, 5), "risk_rejected"),
    ],
)
def test_final_consumed_event_commits_exact_terminal_semantics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    extra_event: tuple[str, str, dict[str, object], int],
    expected_result: str,
) -> None:
    path = tmp_path / f"product-{expected_result}-{extra_event[1]}.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, create_command = _fixture(path, extra_events=(extra_event,))
    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT
    )
    order = service.create_order(create_command).result
    committed = service.step_order(_step_command(order, version=0, key="terminal-step"))
    assert committed.result.step_result.attempt.attempt_result == expected_result
    assert committed.result.step_result.order_state.terminal
    assert _authority_counts(engine)["cursor"] == 5
    assert (
        len(
            service.reconcile_order(
                execution_order_id=order.execution_order_id
            ).attempts
        )
        == 1
    )
    engine.dispose()


def test_out_of_session_boundary_does_not_advance_replay_or_account(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, create_command = _fixture(
        path,
        session_close_minutes=10,
        extra_events=((INSTRUMENT, "trade", {"price": 5}, 20),),
    )
    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT
    )
    order = service.create_order(create_command).result
    committed = service.step_order(_step_command(order, version=0, key="boundary"))
    assert committed.result.step_result.attempt.attempt_result == "boundary_rejected"
    assert (
        committed.result.step_result.attempt.pre_step_cursor
        == committed.result.step_result.attempt.post_step_cursor
    )
    assert _authority_counts(engine) == {
        "attempts": 1,
        "fills": 0,
        "links": 0,
        "receipts": 2,
        "account_events": 0,
        "cash": 0,
        "positions": 0,
        "cursor": 4,
    }
    engine.dispose()


@pytest.mark.parametrize(
    ("signal_prices", "initial_position", "expected_cash"),
    [
        ((3, 2, 1, 4), None, "1950"),
        ((1, 5, 4, 2), ("10", "100"), "2050"),
    ],
)
def test_partial_then_full_buy_and_sell_settlement_reconcile_after_reload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    signal_prices: tuple[object, ...],
    initial_position: tuple[str, str] | None,
    expected_cash: str,
) -> None:
    path = tmp_path / f"product-{'sell' if initial_position else 'buy'}.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, create_command = _fixture(
        path,
        signal_prices=signal_prices,
        extra_events=tuple(
            (INSTRUMENT, "trade", {"price": 5}, minute) for minute in (5, 6, 7)
        ),
        max_fill_quantity="4",
        initial_position=initial_position,
    )
    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT
    )
    order = service.create_order(create_command).result
    for version in range(3):
        service.step_order(
            _step_command(order, version=version, key=f"partial-{version}")
        )
    history = service.reconcile_order(execution_order_id=order.execution_order_id)
    assert history.state.status == "filled"
    assert [fill.fill_quantity.canonical for fill in history.fills] == ["4", "4", "2"]
    with factory() as session:
        account = SqlAlchemyPaperAccountRepository(session=session).get_account(
            account_id=order.account_id
        )
        assert account is not None
        account_history = SqlAlchemyPaperAccountRepository(session=session).get_history(
            account=account
        )
        assert (
            account_history[-1].resulting_state.cash_balance.canonical == expected_cash
        )
        positions = account_history[-1].resulting_state.positions
        assert (
            (not positions)
            if initial_position
            else positions[0].quantity.canonical == "10"
        )
    counts = _authority_counts(engine)
    assert counts["attempts"] == counts["fills"] == counts["links"] == 3
    assert counts["account_events"] == counts["cash"] == counts["positions"] == 3
    engine.dispose()


def test_historical_receipts_and_alternate_keys_survive_later_valid_progression(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product-historical-replay.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, create_command = _fixture(
        path,
        extra_events=(
            (INSTRUMENT, "trade", {"price": 5}, 5),
            (INSTRUMENT, "trade", {"price": 6}, 6),
        ),
        max_fill_quantity="4",
    )
    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT
    )
    order = service.create_order(create_command).result
    step_command = _step_command(order, version=0, key="historical-fill")
    original_step = service.step_order(step_command).result
    assert original_step.step_result.fill is not None
    assert not original_step.step_result.order_state.terminal

    with factory() as session:
        account_repo = SqlAlchemyPaperAccountRepository(session=session)
        account = account_repo.get_account(account_id=order.account_id)
        assert account is not None
    PaperAccountApplicationService(
        session_factory=factory, clock=lambda: AUDIT + timedelta(hours=1)
    ).post_cash_movement(
        account_id=order.account_id,
        expected_account_version=account.head_version,
        command_idempotency_key="later-valid-deposit",
        actor="founder",
        reason="valid progression after committed execution result",
        movement_type="deposit",
        requested_amount=PaperMoney.parse("1"),
    )
    with factory.begin() as session:
        market = SqlAlchemyMarketTimeRepository(session=session)
        replay = market.get_replay(replay_id="replay-s211")
        assert replay is not None
        replay_engine = MarketDataReplayEngine(
            replay_id=replay.session.replay_id,
            events=replay.events,
            cursor=replay.session.cursor,
        )
        expected_cursor = replay_engine.cursor
        assert replay_engine.next_event() is not None
        assert market.replace_replay_checkpoint(
            expected_cursor=expected_cursor,
            session=replay_engine.session,
        )

    progressed = _authority_counts(engine)
    assert service.create_order(create_command).result == order
    assert service.step_order(step_command).result == original_step
    assert _authority_counts(engine) == progressed

    alternate_time = AUDIT + timedelta(hours=2)
    alternate_service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: alternate_time
    )
    alternate_create = create_paper_execution_order_command(
        order_intent_reference=create_command.order_intent_reference,
        risk_handoff_reference=create_command.risk_handoff_reference,
        execution_policy_reference=create_command.execution_policy_reference,
        command_idempotency_key="historical-alternate-create",
        actor="second-founder",
    )
    alternate_step = _step_command(
        order,
        version=0,
        key="historical-alternate-step",
        actor="second-founder",
    )
    assert alternate_service.create_order(alternate_create).result == order
    assert alternate_service.step_order(alternate_step).result == original_step
    after_alternates = _authority_counts(engine)
    assert after_alternates == {**progressed, "receipts": progressed["receipts"] + 2}

    with factory() as session:
        repository = SqlAlchemyPaperExecutionRepository(session=session)
        create_receipt = repository.get_receipt(
            namespace="create_paper_execution_order",
            command_idempotency_key="historical-alternate-create",
        )
        step_receipt = repository.get_receipt(
            namespace="step_paper_execution_order",
            command_idempotency_key="historical-alternate-step",
        )
        assert create_receipt is not None and step_receipt is not None
        assert create_receipt.created_at == alternate_time
        assert step_receipt.created_at == alternate_time

    assert after_alternates["attempts"] == 1
    assert after_alternates["fills"] == after_alternates["links"] == 1
    assert after_alternates["account_events"] == 1
    assert after_alternates["cursor"] == 6
    with pytest.raises(PaperExecutionStaleAuthorityError):
        service.step_order(_step_command(order, version=1, key="genuinely-new-step"))
    assert _authority_counts(engine) == after_alternates
    engine.dispose()


@pytest.mark.parametrize("forged_authority", ["m31", "m32", "m33"])
def test_historical_reconstruction_rejects_self_consistent_forged_handoff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    forged_authority: str,
) -> None:
    path = tmp_path / f"product-forged-{forged_authority}.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, create_command = _fixture(path)
    order = (
        PaperExecutionApplicationService(session_factory=factory, clock=lambda: AUDIT)
        .create_order(create_command)
        .result
    )

    account_handoff = order.account_handoff_reference
    market_handoff = order.market_handoff_reference
    risk_handoff = order.risk_handoff_reference
    origin_digest = order.origin_command_digest
    with factory.begin() as session:
        if forged_authority == "m31":
            account_handoff = _build_account_handoff(
                account_id=account_handoff.account_id,
                base_currency=account_handoff.base_currency,
                lifecycle_status=account_handoff.lifecycle_status,
                account_head_version=account_handoff.account_head_version,
                account_head_event_id=account_handoff.account_head_event_id,
                account_head_chain_digest=account_handoff.account_head_chain_digest,
                cash_balance=PaperMoney.parse("1999"),
                available_cash=PaperMoney.parse("1999"),
                instrument_id=account_handoff.instrument_id,
                current_instrument_quantity=(
                    account_handoff.current_instrument_quantity
                ),
            )
        elif forged_authority == "m32":
            market = SqlAlchemyMarketTimeRepository(session=session)
            calendar = market.get_calendar(calendar_id=market_handoff.calendar_id)
            replay = market.get_replay(replay_id=market_handoff.replay_id)
            assert calendar is not None and replay is not None
            wrong_session = create_trading_session(
                id=market_handoff.trading_session_id,
                calendar_id=market_handoff.calendar_id,
                trading_date=market_handoff.trading_date,
                open_time=market_handoff.session_open_time,
                close_time=market_handoff.session_close_time + timedelta(minutes=1),
                session_type=market_handoff.session_type,
            )
            historical_replay = MarketDataReplayEngine(
                replay_id=market_handoff.replay_id,
                events=replay.events,
                cursor=ReplayCursor(
                    replay_id=market_handoff.replay_id,
                    event_stream_digest=market_handoff.event_stream_digest,
                    position=market_handoff.cursor_position,
                    last_event_id=market_handoff.last_event_id,
                    current_event_time=market_handoff.current_event_time,
                    status=market_handoff.handoff_replay_status,
                ),
            )
            market_handoff = _build_market_handoff(
                calendar=calendar,
                session=wrong_session,
                replay_engine=historical_replay,
            )
        else:
            risk_handoff = _build_risk_handoff(
                order_intent_reference=risk_handoff.order_intent_reference,
                risk_decision_id=risk_handoff.risk_decision_id,
                risk_decision_digest=risk_handoff.risk_decision_digest,
                risk_snapshot_id=risk_handoff.risk_snapshot_id,
                risk_snapshot_digest=risk_handoff.risk_snapshot_digest,
                risk_policy_reference=create_long_only_cash_risk_policy_reference(
                    maximum_order_quantity=PaperQuantity.parse("9")
                ),
            )
            origin_digest = create_paper_execution_order_command(
                order_intent_reference=order.order_intent_reference,
                risk_handoff_reference=risk_handoff,
                execution_policy_reference=order.execution_policy_reference,
                command_idempotency_key=order.origin_command_idempotency_key,
                actor=order.origin_actor,
            ).command_digest

        forged = _build_order(
            order_intent_reference=order.order_intent_reference,
            risk_handoff_reference=risk_handoff,
            account_handoff_reference=account_handoff,
            market_handoff_reference=market_handoff,
            execution_policy_reference=order.execution_policy_reference,
            account_id=order.account_id,
            instrument_id=order.instrument_id,
            side=order.side,
            requested_quantity=order.requested_quantity,
            origin_command_idempotency_key=order.origin_command_idempotency_key,
            origin_command_digest=origin_digest,
            origin_actor=order.origin_actor,
            created_at=order.created_at,
        )
        repository = SqlAlchemyPaperExecutionRepository(session=session)
        repository.append_order(order=forged)
        with pytest.raises(PaperExecutionCorruptAuthorityError):
            repository.load_historical_history(
                execution_order_id=forged.execution_order_id
            )
    engine.dispose()


def test_paged_m31_history_rejects_rehashed_execution_settlement_forgery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product-forged-paged-settlement.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, create_command = _fixture(
        path,
        extra_events=((INSTRUMENT, "trade", {"price": 5}, 5),),
    )
    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT
    )
    order = service.create_order(create_command).result
    service.step_order(_step_command(order, version=0, key="fill-for-page-forgery"))

    with factory() as session:
        account_repo = SqlAlchemyPaperAccountRepository(session=session)
        account = account_repo.get_account(account_id=order.account_id)
        assert account is not None
        history = account_repo.get_history(account=account)
        settlement = next(
            bundle
            for bundle in history
            if bundle.event.event_type == "execution_fill_posted"
        )
    event = settlement.event
    forged = _create_event(
        event_id=event.event_id,
        account_id=event.account_id,
        sequence_number=event.sequence_number,
        event_type=event.event_type,
        command_idempotency_key=event.command_idempotency_key,
        command_digest="0" * 64,
        expected_account_version=event.expected_account_version,
        actor=event.actor,
        reason=event.reason,
        recorded_timestamp_utc=event.recorded_timestamp_utc,
        effective_timestamp_utc=event.effective_timestamp_utc,
        previous_chain_digest=event.previous_chain_digest,
        details=event.details,
        cash_entries=settlement.cash_entries,
        position_entries=settlement.position_entries,
    )
    with engine.begin() as connection:
        connection.execute(text("DROP TRIGGER trg_paper_account_events_no_update"))
        connection.execute(
            text(
                "UPDATE paper_account_events SET command_digest = :command_digest, "
                "event_digest = :event_digest, chain_digest = :chain_digest "
                "WHERE event_id = :event_id"
            ),
            {
                "command_digest": forged.command_digest,
                "event_digest": forged.event_digest,
                "chain_digest": forged.chain_digest,
                "event_id": forged.event_id,
            },
        )
        connection.execute(
            text(
                "UPDATE paper_accounts SET head_chain_digest = :chain_digest "
                "WHERE account_id = :account_id"
            ),
            {
                "chain_digest": forged.chain_digest,
                "account_id": forged.account_id,
            },
        )

    with factory() as session:
        account_repo = SqlAlchemyPaperAccountRepository(session=session)
        account = account_repo.get_account(account_id=order.account_id)
        assert account is not None
        with pytest.raises(PaperAccountPersistenceCorruptionError):
            account_repo.get_history_page(
                account=account,
                after_sequence_number=1,
                limit=1,
            )
    engine.dispose()


@pytest.mark.parametrize("same_key", [True, False], ids=["same-key", "alternate-key"])
def test_s215_concurrent_create_has_one_deterministic_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    same_key: bool,
) -> None:
    path = tmp_path / f"create-race-{same_key}.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, original = _fixture(path)
    barrier = Barrier(2)

    def run(index: int):
        command_value = create_paper_execution_order_command(
            order_intent_reference=original.order_intent_reference,
            risk_handoff_reference=original.risk_handoff_reference,
            execution_policy_reference=original.execution_policy_reference,
            command_idempotency_key=(
                original.command_idempotency_key
                if same_key
                else f"alternate-create-race-{index}"
            ),
            actor="founder",
        )
        barrier.wait(timeout=10)
        return PaperExecutionApplicationService(
            session_factory=factory,
            clock=lambda: AUDIT + timedelta(hours=1),
        ).create_order(command_value)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(pool.map(run, (1, 2)))

    assert results[0].result == results[1].result
    assert results[0].result.execution_order_id == results[1].result.execution_order_id
    assert (
        results[0].result.execution_order_digest
        == results[1].result.execution_order_digest
    )
    with engine.connect() as connection:
        assert (
            connection.scalar(text("SELECT COUNT(*) FROM paper_execution_orders")) == 1
        )
        assert connection.scalar(
            text("SELECT COUNT(*) FROM paper_execution_command_receipts")
        ) == (1 if same_key else 2)
    assert _authority_counts(engine) == {
        "attempts": 0,
        "fills": 0,
        "links": 0,
        "receipts": 1 if same_key else 2,
        "account_events": 0,
        "cash": 0,
        "positions": 0,
        "cursor": 4,
    }
    engine.dispose()


@pytest.mark.parametrize("same_key", [True, False], ids=["same-key", "alternate-key"])
def test_s215_concurrent_fill_step_has_one_financial_and_cursor_winner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    same_key: bool,
) -> None:
    path = tmp_path / f"step-race-{same_key}.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, create_command = _fixture(
        path,
        extra_events=((INSTRUMENT, "trade", {"price": 5}, 5),),
    )
    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT
    )
    order = service.create_order(create_command).result
    barrier = Barrier(2)

    def run(index: int):
        command_value = _step_command(
            order,
            version=0,
            key="same-step-race" if same_key else f"alternate-step-race-{index}",
        )
        barrier.wait(timeout=10)
        return PaperExecutionApplicationService(
            session_factory=factory, clock=lambda: AUDIT
        ).step_order(command_value)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(pool.map(run, (1, 2)))

    first = results[0].result
    second = results[1].result
    assert first.step_result.attempt == second.step_result.attempt
    assert first.step_result.fill == second.step_result.fill
    assert first.settlement_link == second.settlement_link
    assert first.step_result.order_state.execution_version == 1
    assert _authority_counts(engine) == {
        "attempts": 1,
        "fills": 1,
        "links": 1,
        "receipts": 2 if same_key else 3,
        "account_events": 1,
        "cash": 1,
        "positions": 1,
        "cursor": 5,
    }
    engine.dispose()


def _forged_intent_reference(reference, *, digest_character: str):
    digest_value = digest_character * 64
    result = object.__new__(type(reference))
    object.__setattr__(result, "schema_version", reference.schema_version)
    object.__setattr__(result, "intent_id", f"oi_{digest_value}")
    object.__setattr__(result, "intent_digest", digest_value)
    return result


def _forged_order_reference(reference, *, digest_character: str):
    digest_value = digest_character * 64
    result = object.__new__(type(reference))
    object.__setattr__(result, "schema_version", reference.schema_version)
    object.__setattr__(result, "execution_order_id", f"peo_{digest_value}")
    object.__setattr__(result, "execution_order_digest", digest_value)
    return result


def test_s215_create_changed_content_idempotency_matrix_is_non_mutating(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "create-conflicts.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, original = _fixture(path)
    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT
    )
    service.create_order(original)
    before = _authority_counts(engine)
    fake_intent = _forged_intent_reference(
        original.order_intent_reference, digest_character="a"
    )
    fake_intent_risk = _build_risk_handoff(
        order_intent_reference=fake_intent,
        risk_decision_id=f"risk_decision_{'b' * 64}",
        risk_decision_digest="b" * 64,
        risk_snapshot_id=f"risk_input_{'c' * 64}",
        risk_snapshot_digest="c" * 64,
        risk_policy_reference=original.risk_handoff_reference.risk_policy_reference,
    )
    fake_decision_risk = _build_risk_handoff(
        order_intent_reference=original.order_intent_reference,
        risk_decision_id=f"risk_decision_{'d' * 64}",
        risk_decision_digest="d" * 64,
        risk_snapshot_id=f"risk_input_{'e' * 64}",
        risk_snapshot_digest="e" * 64,
        risk_policy_reference=original.risk_handoff_reference.risk_policy_reference,
    )
    zero = PaperExecutionBasisPoints.parse("0")
    changed_policy = create_paper_execution_policy_reference(
        max_fill_quantity_per_trade_event=None,
        slippage_bps=PaperExecutionBasisPoints.parse("1"),
        commission_bps=zero,
        fee_bps=zero,
        buy_tax_bps=zero,
        sell_tax_bps=zero,
    )
    variants = (
        create_paper_execution_order_command(
            order_intent_reference=fake_intent,
            risk_handoff_reference=fake_intent_risk,
            execution_policy_reference=original.execution_policy_reference,
            command_idempotency_key=original.command_idempotency_key,
            actor=original.actor,
        ),
        create_paper_execution_order_command(
            order_intent_reference=original.order_intent_reference,
            risk_handoff_reference=fake_decision_risk,
            execution_policy_reference=original.execution_policy_reference,
            command_idempotency_key=original.command_idempotency_key,
            actor=original.actor,
        ),
        create_paper_execution_order_command(
            order_intent_reference=original.order_intent_reference,
            risk_handoff_reference=original.risk_handoff_reference,
            execution_policy_reference=changed_policy,
            command_idempotency_key=original.command_idempotency_key,
            actor=original.actor,
        ),
        create_paper_execution_order_command(
            order_intent_reference=original.order_intent_reference,
            risk_handoff_reference=original.risk_handoff_reference,
            execution_policy_reference=original.execution_policy_reference,
            command_idempotency_key=original.command_idempotency_key,
            actor="different-founder",
        ),
    )
    for variant in variants:
        with pytest.raises(PaperExecutionIdempotencyConflictError):
            service.create_order(variant)
        assert _authority_counts(engine) == before
    engine.dispose()


def test_s215_step_changed_content_idempotency_matrix_is_non_mutating(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "step-conflicts.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, create_command = _fixture(path)
    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT
    )
    order = service.create_order(create_command).result
    original = _step_command(order, version=0, key="step-conflict-key")
    service.step_order(original)
    before = _authority_counts(engine)
    order_reference = create_paper_execution_order_reference(order)
    variants = (
        create_step_paper_execution_order_command(
            execution_order_reference=_forged_order_reference(
                order_reference, digest_character="f"
            ),
            expected_execution_version=0,
            command_idempotency_key=original.command_idempotency_key,
            actor=original.actor,
        ),
        create_step_paper_execution_order_command(
            execution_order_reference=order_reference,
            expected_execution_version=1,
            command_idempotency_key=original.command_idempotency_key,
            actor=original.actor,
        ),
        create_step_paper_execution_order_command(
            execution_order_reference=order_reference,
            expected_execution_version=0,
            command_idempotency_key=original.command_idempotency_key,
            actor="different-founder",
        ),
    )
    for variant in variants:
        with pytest.raises(PaperExecutionIdempotencyConflictError):
            service.step_order(variant)
        assert _authority_counts(engine) == before
    engine.dispose()


@pytest.mark.parametrize("operation", ["create", "step"])
def test_s215_sqlite_busy_refusal_is_bounded_non_mutating_and_retryable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    path = tmp_path / f"busy-{operation}.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, create_command = _fixture(
        path,
        extra_events=((INSTRUMENT, "trade", {"price": 5}, 5),),
    )

    @event.listens_for(engine, "connect")
    def _bounded_busy_timeout(dbapi_connection, _connection_record) -> None:
        dbapi_connection.execute("PRAGMA busy_timeout=100")

    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT
    )
    order = None
    command_value = create_command
    if operation == "step":
        order = service.create_order(create_command).result
        command_value = _step_command(order, version=0, key="busy-step")
    engine.dispose()
    before = _authority_counts(engine)
    lock = sqlite3.connect(path, timeout=0, isolation_level=None)
    try:
        lock.execute("BEGIN IMMEDIATE")
        with pytest.raises(PaperExecutionStorageBusyError):
            if operation == "create":
                service.create_order(command_value)
            else:
                service.step_order(command_value)
        assert _authority_counts(engine) == before
    finally:
        lock.rollback()
        lock.close()

    if operation == "create":
        stored = service.create_order(command_value)
        assert not stored.replayed
        assert _authority_counts(engine)["receipts"] == 1
    else:
        stored = service.step_order(command_value)
        assert stored.result.step_result.fill is not None
        assert _authority_counts(engine) == {
            "attempts": 1,
            "fills": 1,
            "links": 1,
            "receipts": 2,
            "account_events": 1,
            "cash": 1,
            "positions": 1,
            "cursor": 5,
        }
    engine.dispose()


def _inject_step_fault(
    faults: pytest.MonkeyPatch,
    point: str,
) -> type[Exception]:
    if point == "after_reconstruction":
        original = SqlAlchemyPaperExecutionRepository.load_historical_history

        def fail_after_reconstruction(self, **kwargs):
            original(self, **kwargs)
            raise RuntimeError("injected after historical reconstruction")

        faults.setattr(
            SqlAlchemyPaperExecutionRepository,
            "load_historical_history",
            fail_after_reconstruction,
        )
        return RuntimeError
    if point == "after_event_derivation":
        original = paper_execution_application.step_paper_execution_order

        def fail_after_event_derivation(*args, **kwargs):
            original(*args, **kwargs)
            raise RuntimeError("injected after in-memory event consumption")

        faults.setattr(
            paper_execution_application,
            "step_paper_execution_order",
            fail_after_event_derivation,
        )
        return RuntimeError
    if point == "after_settlement_derivation":
        original = paper_execution_application.settle_paper_execution_fill

        def fail_after_settlement_derivation(*args, **kwargs):
            original(*args, **kwargs)
            raise RuntimeError("injected after settlement derivation")

        faults.setattr(
            paper_execution_application,
            "settle_paper_execution_fill",
            fail_after_settlement_derivation,
        )
        return RuntimeError
    if point == "after_m31_append":
        original = SqlAlchemyPaperAccountRepository.append_mutation

        def fail_after_m31_append(self, **kwargs):
            original(self, **kwargs)
            raise RuntimeError("injected after M31 append")

        faults.setattr(
            SqlAlchemyPaperAccountRepository,
            "append_mutation",
            fail_after_m31_append,
        )
        return RuntimeError
    if point == "after_m34_append":
        original = SqlAlchemyPaperExecutionRepository.append_settlement_link

        def fail_after_m34_append(self, **kwargs):
            original(self, **kwargs)
            raise RuntimeError("injected after M34 append")

        faults.setattr(
            SqlAlchemyPaperExecutionRepository,
            "append_settlement_link",
            fail_after_m34_append,
        )
        return RuntimeError
    if point == "after_checkpoint_cas":
        original = SqlAlchemyMarketTimeRepository.replace_replay_checkpoint

        def fail_after_checkpoint_cas(self, **kwargs):
            original(self, **kwargs)
            raise RuntimeError("injected after M32 checkpoint CAS")

        faults.setattr(
            SqlAlchemyMarketTimeRepository,
            "replace_replay_checkpoint",
            fail_after_checkpoint_cas,
        )
        return RuntimeError
    if point == "after_receipt_append":
        original = SqlAlchemyPaperExecutionRepository.append_receipt

        def fail_after_receipt_append(self, **kwargs):
            original(self, **kwargs)
            raise RuntimeError("injected after receipt append")

        faults.setattr(
            SqlAlchemyPaperExecutionRepository,
            "append_receipt",
            fail_after_receipt_append,
        )
        return RuntimeError
    if point == "commit_failure":

        def fail_commit(self) -> None:
            self.flush()
            raise SQLAlchemyError("injected commit failure")

        faults.setattr(Session, "commit", fail_commit)
        return PaperExecutionStorageFailureError
    raise AssertionError(f"unknown fault point: {point}")


@pytest.mark.parametrize(
    "fault_point",
    (
        "after_reconstruction",
        "after_event_derivation",
        "after_settlement_derivation",
        "after_m31_append",
        "after_m34_append",
        "after_checkpoint_cas",
        "after_receipt_append",
        "commit_failure",
    ),
)
def test_s215_fill_step_fault_matrix_rolls_back_and_clean_retry_converges(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault_point: str,
) -> None:
    path = tmp_path / f"rollback-{fault_point}.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, create_command = _fixture(
        path,
        extra_events=((INSTRUMENT, "trade", {"price": 5}, 5),),
    )
    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT
    )
    order = service.create_order(create_command).result
    step_command = _step_command(order, version=0, key=f"rollback-{fault_point}")
    before = _authority_counts(engine)

    with monkeypatch.context() as faults:
        expected_error = _inject_step_fault(faults, fault_point)
        with pytest.raises(expected_error):
            service.step_order(step_command)
    assert _authority_counts(engine) == before

    committed = service.step_order(step_command)
    assert not committed.replayed
    assert committed.result.step_result.fill is not None
    assert (
        service.reconcile_order(
            execution_order_id=order.execution_order_id
        ).state.status
        == "filled"
    )
    assert _authority_counts(engine) == {
        "attempts": 1,
        "fills": 1,
        "links": 1,
        "receipts": 2,
        "account_events": 1,
        "cash": 1,
        "positions": 1,
        "cursor": 5,
    }
    engine.dispose()


def test_s215_no_fill_fault_rolls_back_attempt_checkpoint_and_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "rollback-no-fill.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, create_command = _fixture(
        path,
        extra_events=(("XNYS:MSFT", "trade", {"price": 5}, 5),),
    )
    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT
    )
    order = service.create_order(create_command).result
    step_command = _step_command(order, version=0, key="rollback-no-fill")
    before = _authority_counts(engine)
    with monkeypatch.context() as faults:
        _inject_step_fault(faults, "after_receipt_append")
        with pytest.raises(RuntimeError, match="receipt"):
            service.step_order(step_command)
    assert _authority_counts(engine) == before

    committed = service.step_order(step_command)
    assert committed.result.step_result.fill is None
    assert (
        service.reconcile_order(
            execution_order_id=order.execution_order_id
        ).state.execution_version
        == 1
    )
    assert _authority_counts(engine) == {
        "attempts": 1,
        "fills": 0,
        "links": 0,
        "receipts": 2,
        "account_events": 0,
        "cash": 0,
        "positions": 0,
        "cursor": 5,
    }
    engine.dispose()


@pytest.mark.parametrize(
    ("lifecycle", "extra_events", "max_fill_quantity", "steps", "terminal"),
    (
        (
            "created",
            ((INSTRUMENT, "trade", {"price": 5}, 5),),
            None,
            0,
            False,
        ),
        (
            "no_fill",
            (
                ("XNYS:MSFT", "trade", {"price": 9}, 5),
                (INSTRUMENT, "trade", {"price": 5}, 6),
            ),
            None,
            1,
            False,
        ),
        (
            "partial_fill",
            (
                (INSTRUMENT, "trade", {"price": 5}, 5),
                (INSTRUMENT, "trade", {"price": 5}, 6),
            ),
            "4",
            1,
            False,
        ),
        (
            "full_fill",
            ((INSTRUMENT, "trade", {"price": 5}, 5),),
            None,
            1,
            True,
        ),
        (
            "risk_rejected",
            ((INSTRUMENT, "trade", {"price": 500}, 5),),
            None,
            1,
            True,
        ),
        (
            "session_exhausted",
            ((INSTRUMENT, "trade", {"price": 5}, 600),),
            None,
            1,
            True,
        ),
    ),
)
def test_s215_restart_reconstructs_every_execution_lifecycle_edge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    lifecycle: str,
    extra_events: tuple[tuple[str, str, dict[str, object], int], ...],
    max_fill_quantity: str | None,
    steps: int,
    terminal: bool,
) -> None:
    path = tmp_path / f"restart-{lifecycle}.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, create_command = _fixture(
        path,
        extra_events=extra_events,
        max_fill_quantity=max_fill_quantity,
    )
    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT
    )
    order = service.create_order(create_command).result
    commands = tuple(
        _step_command(order, version=version, key=f"restart-{lifecycle}-{version}")
        for version in range(steps)
    )
    commits = tuple(
        service.step_order(command_value).result for command_value in commands
    )
    before_history = service.reconcile_order(
        execution_order_id=order.execution_order_id
    )
    assert before_history.state.terminal is terminal
    with factory() as session:
        account_repo = SqlAlchemyPaperAccountRepository(session=session)
        before_account = account_repo.get_account(account_id=order.account_id)
        assert before_account is not None
        before_account_history = account_repo.get_history(account=before_account)
        before_replay = SqlAlchemyMarketTimeRepository(session=session).get_replay(
            replay_id=order.market_handoff_reference.replay_id
        )
    assert before_replay is not None
    before_counts = _authority_counts(engine)
    del service, factory
    engine.dispose()

    reopened = create_product_database_engine(
        config=resolve_product_database_config(database_path=path)
    )
    reopened_factory = create_product_session_factory(engine=reopened)
    restarted = PaperExecutionApplicationService(
        session_factory=reopened_factory, clock=lambda: AUDIT + timedelta(hours=1)
    )
    try:
        after_history = restarted.reconcile_order(
            execution_order_id=order.execution_order_id
        )
        assert after_history == before_history
        assert after_history.order.execution_order_id == order.execution_order_id
        assert (
            after_history.order.execution_order_digest == order.execution_order_digest
        )
        with reopened_factory() as session:
            account_repo = SqlAlchemyPaperAccountRepository(session=session)
            after_account = account_repo.get_account(account_id=order.account_id)
            assert after_account == before_account
            assert after_account is not None
            assert (
                account_repo.get_history(account=after_account)
                == before_account_history
            )
            after_replay = SqlAlchemyMarketTimeRepository(session=session).get_replay(
                replay_id=order.market_handoff_reference.replay_id
            )
        assert after_replay is not None
        assert after_replay.session.cursor == before_replay.session.cursor
        assert _authority_counts(reopened) == before_counts

        for command_value, original_commit in zip(commands, commits, strict=True):
            replayed = restarted.step_order(command_value)
            assert replayed.replayed
            assert replayed.result == original_commit
        assert _authority_counts(reopened) == before_counts

        if terminal:
            with pytest.raises(PaperExecutionOperationConflictError):
                restarted.step_order(
                    _step_command(
                        order,
                        version=after_history.state.execution_version,
                        key=f"unsupported-terminal-{lifecycle}",
                    )
                )
            assert _authority_counts(reopened) == before_counts
        else:
            continued = restarted.step_order(
                _step_command(
                    order,
                    version=after_history.state.execution_version,
                    key=f"continued-{lifecycle}",
                )
            )
            assert (
                continued.result.step_result.attempt.execution_version_after
                == after_history.state.execution_version + 1
            )
            continued_counts = _authority_counts(reopened)
            restarted.reconcile_order(execution_order_id=order.execution_order_id)
            assert _authority_counts(reopened) == continued_counts
    finally:
        reopened.dispose()


@pytest.mark.parametrize("movement", ["m31", "m32"])
def test_s215_restart_then_external_progression_preserves_history_without_rebase(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    movement: str,
) -> None:
    path = tmp_path / f"restart-external-{movement}.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, create_command = _fixture(
        path,
        extra_events=(
            (INSTRUMENT, "trade", {"price": 5}, 5),
            (INSTRUMENT, "trade", {"price": 6}, 6),
        ),
        max_fill_quantity="4",
    )
    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT
    )
    order = service.create_order(create_command).result
    committed_command = _step_command(order, version=0, key=f"historical-{movement}")
    committed = service.step_order(committed_command).result
    historical = service.get_history(execution_order_id=order.execution_order_id)
    del service, factory
    engine.dispose()

    reopened = create_product_database_engine(
        config=resolve_product_database_config(database_path=path)
    )
    reopened_factory = create_product_session_factory(engine=reopened)
    if movement == "m31":
        with reopened_factory() as session:
            account = SqlAlchemyPaperAccountRepository(session=session).get_account(
                account_id=order.account_id
            )
        assert account is not None
        PaperAccountApplicationService(
            session_factory=reopened_factory,
            clock=lambda: AUDIT + timedelta(hours=1),
        ).post_cash_movement(
            account_id=order.account_id,
            expected_account_version=account.head_version,
            command_idempotency_key="external-m31-movement",
            actor="founder",
            reason="deterministic external movement",
            movement_type="deposit",
            requested_amount=PaperMoney.parse("1"),
        )
    else:
        with reopened_factory.begin() as session:
            market = SqlAlchemyMarketTimeRepository(session=session)
            replay = market.get_replay(
                replay_id=order.market_handoff_reference.replay_id
            )
            assert replay is not None
            replay_engine = MarketDataReplayEngine(
                replay_id=replay.session.replay_id,
                events=replay.events,
                cursor=replay.session.cursor,
            )
            expected_cursor = replay_engine.cursor
            assert replay_engine.next_event() is not None
            assert market.replace_replay_checkpoint(
                expected_cursor=expected_cursor,
                session=replay_engine.session,
            )

    restarted = PaperExecutionApplicationService(
        session_factory=reopened_factory, clock=lambda: AUDIT + timedelta(hours=2)
    )
    progressed = _authority_counts(reopened)
    assert (
        restarted.get_history(execution_order_id=order.execution_order_id) == historical
    )
    replayed = restarted.step_order(committed_command)
    assert replayed.replayed and replayed.result == committed
    assert _authority_counts(reopened) == progressed
    with pytest.raises(PaperExecutionReconciliationRequiredError):
        restarted.reconcile_order(execution_order_id=order.execution_order_id)
    with pytest.raises(PaperExecutionStaleAuthorityError):
        restarted.step_order(
            _step_command(order, version=1, key=f"new-after-{movement}")
        )
    assert _authority_counts(reopened) == progressed
    reopened.dispose()


def _sqlite_authority_dump(path: Path) -> tuple[str, ...]:
    with sqlite3.connect(path) as connection:
        return tuple(connection.iterdump())


def _corrupt_execution_authority(
    path: Path,
    *,
    corruption: str,
    order_id: str,
    attempt_id: str,
    fill_id: str,
    intent_id: str,
    decision_id: str,
    forged_fill=None,
) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys=OFF")
        if corruption == "order_payload_column":
            connection.execute("DROP TRIGGER trg_paper_execution_orders_no_update")
            connection.execute(
                "UPDATE paper_execution_orders SET instrument_id = 'XNYS:IBM' "
                "WHERE execution_order_id = ?",
                (order_id,),
            )
        elif corruption == "attempt_cursor_chain":
            connection.execute("DROP TRIGGER trg_paper_execution_attempts_no_update")
            connection.execute(
                "UPDATE paper_execution_attempts SET post_cursor_position = 99 "
                "WHERE attempt_id = ?",
                (attempt_id,),
            )
        elif corruption == "fill_event_reference":
            connection.execute("DROP TRIGGER trg_paper_execution_fills_no_update")
            connection.execute(
                "UPDATE paper_execution_fills SET consumed_event_position = 4 "
                "WHERE fill_id = ?",
                (fill_id,),
            )
        elif corruption == "impossible_fill_quantity":
            if forged_fill is None:
                raise AssertionError("forged Fill is required")
            row = fill_row(forged_fill)
            connection.execute("DROP TRIGGER trg_paper_execution_fills_no_update")
            connection.execute(
                "UPDATE paper_execution_fills SET fill_id = ?, fill_digest = ?, "
                "payload_json = ?, created_at = ? WHERE fill_id = ?",
                (
                    row.fill_id,
                    row.fill_digest,
                    row.payload_json,
                    row.created_at,
                    fill_id,
                ),
            )
        elif corruption == "missing_fill":
            connection.execute(
                "DROP TRIGGER trg_paper_execution_settlement_links_no_delete"
            )
            connection.execute("DROP TRIGGER trg_paper_execution_fills_no_delete")
            connection.execute(
                "DELETE FROM paper_execution_settlement_links WHERE fill_id = ?",
                (fill_id,),
            )
            connection.execute(
                "DELETE FROM paper_execution_fills WHERE fill_id = ?", (fill_id,)
            )
        elif corruption == "missing_settlement_link":
            connection.execute(
                "DROP TRIGGER trg_paper_execution_settlement_links_no_delete"
            )
            connection.execute(
                "DELETE FROM paper_execution_settlement_links WHERE fill_id = ?",
                (fill_id,),
            )
        elif corruption == "wrong_settlement_event":
            connection.execute(
                "DROP TRIGGER trg_paper_execution_settlement_links_no_update"
            )
            initial_event_id = connection.execute(
                "SELECT event_id FROM paper_account_events "
                "WHERE event_type = 'account_created'"
            ).fetchone()[0]
            connection.execute(
                "UPDATE paper_execution_settlement_links SET account_event_id = ? "
                "WHERE fill_id = ?",
                (initial_event_id, fill_id),
            )
        elif corruption == "missing_cash_posting":
            connection.execute("DROP TRIGGER trg_paper_cash_ledger_entries_no_delete")
            connection.execute(
                "DELETE FROM paper_cash_ledger_entries "
                "WHERE movement_type = 'execution_settlement'"
            )
        elif corruption == "missing_position_posting":
            connection.execute(
                "DROP TRIGGER trg_paper_position_ledger_entries_no_delete"
            )
            connection.execute(
                "DELETE FROM paper_position_ledger_entries "
                "WHERE adjustment_category = 'execution_fill'"
            )
        elif corruption == "m31_chain_projection":
            connection.execute(
                "UPDATE paper_accounts SET head_chain_digest = ? "
                "WHERE account_id = (SELECT account_id FROM paper_execution_orders "
                "WHERE execution_order_id = ?)",
                ("0" * 64, order_id),
            )
        elif corruption == "m32_checkpoint":
            connection.execute(
                "UPDATE market_data_replays SET last_event_id = 'event-s211-1' "
                "WHERE replay_id = 'replay-s211'"
            )
        elif corruption == "missing_intent":
            connection.execute("DROP TRIGGER trg_order_intents_no_delete")
            connection.execute(
                "DELETE FROM order_intents WHERE intent_id = ?", (intent_id,)
            )
        elif corruption == "missing_decision":
            connection.execute("DROP TRIGGER trg_pre_trade_risk_decisions_no_delete")
            connection.execute(
                "DELETE FROM pre_trade_risk_decisions WHERE decision_id = ?",
                (decision_id,),
            )
        elif corruption == "receipt_result_digest":
            connection.execute(
                "DROP TRIGGER trg_paper_execution_command_receipts_no_update"
            )
            connection.execute(
                "UPDATE paper_execution_command_receipts SET attempt_digest = ? "
                "WHERE namespace = 'step_paper_execution_order'",
                ("0" * 64,),
            )
        else:
            raise AssertionError(f"unknown corruption case: {corruption}")
        connection.commit()


@pytest.mark.parametrize(
    "corruption",
    (
        "order_payload_column",
        "attempt_cursor_chain",
        "fill_event_reference",
        "impossible_fill_quantity",
        "missing_fill",
        "missing_settlement_link",
        "wrong_settlement_event",
        "missing_cash_posting",
        "missing_position_posting",
        "m31_chain_projection",
        "m32_checkpoint",
        "missing_intent",
        "missing_decision",
        "receipt_result_digest",
    ),
)
def test_s215_corruption_matrix_fails_closed_and_never_repairs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    corruption: str,
) -> None:
    path = tmp_path / f"corrupt-{corruption}.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, create_command = _fixture(
        path,
        extra_events=(
            (INSTRUMENT, "trade", {"price": 5}, 5),
            (INSTRUMENT, "trade", {"price": 6}, 6),
        ),
        max_fill_quantity="4",
    )
    service = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT
    )
    order = service.create_order(create_command).result
    committed_command = _step_command(
        order, version=0, key=f"corruption-source-{corruption}"
    )
    committed = service.step_order(committed_command).result
    valid_history = service.reconcile_order(execution_order_id=order.execution_order_id)
    attempt = committed.step_result.attempt
    fill = committed.step_result.fill
    assert fill is not None
    forged_fill = None
    if corruption == "impossible_fill_quantity":
        quantity = PaperQuantity.parse("40")
        costs = _build_cost_evidence(
            execution_price_evidence=fill.execution_price_evidence,
            fill_quantity=quantity,
            commission_bps=fill.cost_evidence.commission_bps,
            fee_bps=fill.cost_evidence.fee_bps,
            side_tax_bps=fill.cost_evidence.side_tax_bps,
        )
        forged_fill = _build_fill(
            execution_order_reference=fill.execution_order_reference,
            attempt_reference=fill.attempt_reference,
            execution_event_reference=fill.execution_event_reference,
            side=fill.side,
            fill_quantity=quantity,
            execution_price_evidence=fill.execution_price_evidence,
            cost_evidence=costs,
            created_at=fill.created_at,
        )
    del service, factory
    engine.dispose()

    _corrupt_execution_authority(
        path,
        corruption=corruption,
        order_id=order.execution_order_id,
        attempt_id=attempt.attempt_id,
        fill_id=fill.fill_id,
        intent_id=order.order_intent_reference.intent_id,
        decision_id=order.risk_handoff_reference.risk_decision_id,
        forged_fill=forged_fill,
    )
    corrupted_dump = _sqlite_authority_dump(path)
    reopened = create_product_database_engine(
        config=resolve_product_database_config(database_path=path)
    )
    reopened_factory = create_product_session_factory(engine=reopened)
    restarted = PaperExecutionApplicationService(
        session_factory=reopened_factory, clock=lambda: AUDIT + timedelta(hours=1)
    )
    if corruption == "receipt_result_digest":
        assert (
            restarted.get_history(execution_order_id=order.execution_order_id)
            == valid_history
        )
        assert (
            restarted.reconcile_order(execution_order_id=order.execution_order_id)
            == valid_history
        )
        with pytest.raises(PaperExecutionCorruptAuthorityError):
            restarted.step_order(committed_command)
    else:
        with pytest.raises(PaperExecutionCorruptAuthorityError):
            restarted.get_history(execution_order_id=order.execution_order_id)
        with pytest.raises(PaperExecutionCorruptAuthorityError):
            restarted.reconcile_order(execution_order_id=order.execution_order_id)
        with pytest.raises(PaperExecutionCorruptAuthorityError):
            restarted.step_order(
                _step_command(
                    order,
                    version=1,
                    key=f"refuse-corruption-{corruption}",
                )
            )
    reopened.dispose()
    assert _sqlite_authority_dump(path) == corrupted_dump
