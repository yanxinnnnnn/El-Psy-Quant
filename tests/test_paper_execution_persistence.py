"""Focused Sprint 211 durable transaction and reconciliation coverage."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

from el_psy_quant.application import (
    PaperAccountApplicationService,
    PaperExecutionApplicationService,
    StrategyOrderApplicationService,
)
from el_psy_quant.market_time import (
    MarketDataReplayEngine,
    create_market_data_event,
    create_trading_calendar,
    create_trading_session,
)
from el_psy_quant.paper_account import PaperMoney, PaperQuantity
from el_psy_quant.paper_execution import (
    PaperExecutionBasisPoints,
    create_paper_execution_order_command,
    create_paper_execution_order_reference,
    create_paper_execution_policy_reference,
    create_paper_execution_risk_handoff_reference,
    create_step_paper_execution_order_command,
)
from el_psy_quant.persistence import (
    PaperExecutionConcurrencyConflictError,
    PaperExecutionCorruptAuthorityError,
    PaperExecutionIdempotencyConflictError,
    PaperExecutionStaleAuthorityError,
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
}


def _config() -> Config:
    return Config(str(ROOT / "alembic.ini"))


def _migrate(path: Path, monkeypatch: pytest.MonkeyPatch, revision: str) -> None:
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    command.upgrade(_config(), revision)


def _fixture(
    path: Path,
    *,
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
        return f"{kind}-s211-{counter[kind]}"

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
            creation_idempotency_key="create-account-s211",
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
                command_idempotency_key="opening-position-s211",
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
        id="calendar-s211",
        market="XNYS",
        timezone="UTC",
        calendar_version=1,
        created_at=CREATED,
    )
    trading_session = create_trading_session(
        id="session-s211",
        calendar_id=calendar.id,
        trading_date=date(2026, 8, 19),
        open_time=CREATED,
        close_time=CREATED + timedelta(minutes=session_close_minutes),
        session_type="regular",
    )
    signal_events = tuple(
        create_market_data_event(
            event_id=f"event-s211-{index}",
            instrument_id=INSTRUMENT,
            event_time=CREATED + timedelta(minutes=index),
            event_type="trade",
            payload={"price": price},
            source="fixture:s211",
        )
        for index, price in enumerate(signal_prices, start=1)
    )
    events = signal_events + tuple(
        create_market_data_event(
            event_id=f"event-s211-{index + len(signal_events)}",
            instrument_id=instrument_id,
            event_time=CREATED + timedelta(minutes=minute),
            event_type=event_type,
            payload=payload,
            source="fixture:s211",
        )
        for index, (instrument_id, event_type, payload, minute) in enumerate(
            extra_events, start=1
        )
    )
    replay = MarketDataReplayEngine(replay_id="replay-s211", events=events)
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
        command_idempotency_key="signal-s211",
        actor="founder",
        created_at=AUDIT,
    ).result
    intent = strategy.derive_and_store_order_intent(
        signal_id=signal.signal_id,
        account_id=account.account_id,
        expected_account_head_version=account.head_version,
        expected_account_head_event_id=account.head_event_id,
        expected_account_head_chain_digest=account.head_chain_digest,
        command_idempotency_key="intent-s211",
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
        command_idempotency_key="risk-s211",
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
        command_idempotency_key="create-order-s211",
        actor="founder",
    )
    return engine, factory, create_command


def test_0011_is_additive_linear_and_has_five_empty_tables(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    scripts = ScriptDirectory.from_config(_config())
    assert scripts.get_heads() == ["0011_paper_execution"]
    assert (
        scripts.get_revision("0011_paper_execution").down_revision
        == "0010_strategy_order_risk"
    )
    assert CURRENT_PRODUCT_SCHEMA_REVISION == "0011_paper_execution"
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
        assert verify_product_schema(path) == "0011_paper_execution"
    finally:
        engine.dispose()


def test_populated_0010_upgrade_preserves_m31_m32_m33_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "product.sqlite3"
    _migrate(path, monkeypatch, "0010_strategy_order_risk")
    engine, _factory, _create_command = _fixture(path)
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
                    connection.execute(
                        text(f'SELECT * FROM "{table}" ORDER BY rowid')
                    )
                )
                for table in predecessor_tables
            } == before
            assert all(
                connection.scalar(text(f'SELECT COUNT(*) FROM "{table}"')) == 0
                for table in TABLES
            )
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
