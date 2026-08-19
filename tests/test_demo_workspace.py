"""Deterministic source and isolated Demo installer coverage."""

import json
import shutil
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Barrier

import pytest
import el_psy_quant.demo_workspace as demo_workspace_module
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from el_psy_quant.application.paper_accounts import (
    PaperAccountApplicationService,
)
from el_psy_quant.application.paper_jobs import read_paper_job_result
from el_psy_quant.application.strategy_order import (
    StrategyOrderApplicationService,
    StrategyOrderIdempotencyConflictError,
    StrategyOrderStaleAuthorityError,
    StrategyOrderStorageBusyError,
)
from el_psy_quant.application.portfolio_reviews import (
    get_portfolio_review_detail,
    record_portfolio_review_decision_with_outcome,
)
from el_psy_quant.demo_workspace import (
    DemoWorkspaceConflictError,
    DemoWorkspacePaths,
    DemoWorkspaceSourceInvalidError,
    DemoWorkspaceTargetRefusedError,
    DemoWorkspaceUnavailableError,
    install_demo_workspace,
    load_demo_workspace_descriptor,
    validate_installed_demo_workspace,
    validate_demo_workspace_source,
)
from el_psy_quant.market_time import MarketDataReplayEngine
from el_psy_quant.persistence import (
    SqlAlchemyMarketTimeRepository,
    SqlAlchemyPaperJobAttemptRepository,
    SqlAlchemyPaperJobRepository,
    StrategyOrderCorruptAuthorityError,
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)
from el_psy_quant.strategy_order import (
    create_long_only_cash_risk_policy_reference,
    create_moving_average_crossover_runtime_reference,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV
from el_psy_quant.paper_account import PaperQuantity

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_SOURCE = PROJECT_ROOT / "examples" / "demo_workspace"
ALEMBIC_CONFIG = PROJECT_ROOT / "alembic.ini"


def _install(source: Path, target: Path):
    return install_demo_workspace(
        source_root=source,
        workspace_root=target,
        workspace_mode="demo",
        alembic_config_path=ALEMBIC_CONFIG,
    )


def _demo_m33(target: Path):
    paths = DemoWorkspacePaths.from_root(target)
    descriptor = load_demo_workspace_descriptor(target).to_dict()
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    return (
        engine,
        create_product_session_factory(engine=engine),
        descriptor["strategy_order"],
    )


def test_versioned_source_validates_every_authoritative_contract() -> None:
    source = validate_demo_workspace_source(DEMO_SOURCE)

    assert source.manifest.dataset_id == "founder-demo-workspace"
    assert source.manifest.canonical_strategy_name == "moving_average_crossover"
    assert len(source.paper_requests) == 2
    assert source.manifest.comparison_candidate_job_ids == (
        "16000000-0000-4000-8000-000000000001",
        "16000000-0000-4000-8000-000000000002",
    )
    assert len(set(source.manifest.comparison_candidate_job_ids)) == 2
    descriptor = source.descriptor.to_dict()
    assert descriptor["schema_version"] == 5
    assert descriptor["dataset_version"] == 5
    assert descriptor["portfolio_review_example"]["create_idempotency_key"] == (
        "demo-portfolio-review-create-v1"
    )
    assert descriptor["portfolio_review_example"]["request"]["review_id"] == (
        "demo-portfolio-review-001"
    )
    assert descriptor["lifecycle_review_example"]["review_outcome"] == "deferred"
    assert descriptor["lifecycle_review_example"]["resulting_snapshot"] is None
    assert descriptor["paper_account"] == {
        "account_id": "demo-paper-account-001",
        "head_version": 5,
        "event_types": [
            "account_created",
            "cash_movement_posted",
            "position_adjustment_posted",
            "account_frozen",
            "account_reactivated",
        ],
        "snapshot_id": "demo-paper-account-snapshot-001",
        "reconciliation_id": "demo-paper-account-reconciliation-001",
    }
    assert descriptor["market_time"] == {
        "calendar_id": "demo-xnys-2026-v1",
        "session_ids": [
            "demo-xnys-2026-07-28-regular",
            "demo-xnys-2026-07-29-regular",
        ],
        "replay_id": "demo-market-replay-001",
        "event_count": 5,
        "event_stream_digest": (
            "f529dc98893820bbbffc79c9fa740b808967ddd13e0e7da9ba21b78c1c8ec78f"
        ),
        "checkpoint": {
            "status": "paused",
            "position": 4,
            "last_event_id": "demo-market-event-004",
            "current_time": "2026-07-28T13:31:30+00:00",
        },
        "recovery": {
            "remaining_event_ids": [
                "demo-market-event-005",
            ],
            "final_status": "completed",
            "final_position": 5,
            "last_event_id": "demo-market-event-005",
            "current_time": "2026-07-28T13:32:00+00:00",
        },
    }
    assert "DEMO" in descriptor["warning"]
    assert descriptor["strategy_order"]["workspace_path"] == "/strategy-to-risk"
    assert descriptor["strategy_order"]["allow_decision"]["outcome"] == "allow"
    assert descriptor["strategy_order"]["reject_decision"]["reason_codes"] == [
        "maximum_order_quantity_exceeded"
    ]


def test_installer_success_replay_and_two_authoritative_results(tmp_path: Path) -> None:
    target = tmp_path / "demo-workspace"

    first = _install(DEMO_SOURCE, target)
    replay = _install(DEMO_SOURCE, target)

    assert first.already_installed is False
    assert replay.already_installed is True
    paths = DemoWorkspacePaths.from_root(target)
    assert set(path.name for path in target.iterdir()) == {
        ".demo-workspace-install.json",
        "evidence",
        "paper",
        "product.sqlite3",
        "research",
        "workspace-descriptor.json",
    }
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    factory = create_product_session_factory(engine=engine)
    try:
        with factory() as session:
            jobs = SqlAlchemyPaperJobRepository(session=session).list()
            assert [job.status for job in jobs] == ["succeeded", "succeeded"]
            assert [job.job_id for job in jobs] == [
                "16000000-0000-4000-8000-000000000001",
                "16000000-0000-4000-8000-000000000002",
            ]
            for job in jobs:
                attempts = SqlAlchemyPaperJobAttemptRepository(
                    session=session
                ).list_for_job(job_id=job.job_id)
                assert len(attempts) == 1
                assert attempts[0].status == "succeeded"
        for job_id in (
            "16000000-0000-4000-8000-000000000001",
            "16000000-0000-4000-8000-000000000002",
        ):
            result = read_paper_job_result(
                session_factory=factory,
                job_id=job_id,
                paper_artifact_root=paths.paper_root,
            )
            assert result.job_id == job_id
        review = get_portfolio_review_detail(
            session_factory=factory,
            artifact_root=paths.evidence_root,
            review_id="demo-portfolio-review-001",
        )
        assert review.record.status == "awaiting_decision"
        assert review.source.source_id == "demo-portfolio-review-source-001"
        assert review.analysis.proposed_component_id == "demo-msft-sleeve"
        assert review.decision is None
        service = PaperAccountApplicationService(session_factory=factory)
        detail = service.get_account_detail(
            account_id="demo-paper-account-001"
        )
        history = service.get_account_history(
            account_id="demo-paper-account-001"
        )
        snapshot = service.get_snapshot(
            snapshot_id="demo-paper-account-snapshot-001"
        )
        reconciliation = service.get_reconciliation(
            reconciliation_id="demo-paper-account-reconciliation-001"
        )
        assert detail.account.head_version == 5
        assert detail.account.lifecycle_status == "active"
        assert detail.projection.cash_balance.canonical == "125000"
        assert [bundle.event.event_type for bundle in history] == [
            "account_created",
            "cash_movement_posted",
            "position_adjustment_posted",
            "account_frozen",
            "account_reactivated",
        ]
        assert snapshot.projection.to_dict() == detail.projection.to_dict()
        assert reconciliation.outcome == "matched"
        assert reconciliation.mismatch_codes == ()
        with factory() as session:
            market_time = SqlAlchemyMarketTimeRepository(session=session)
            calendar = market_time.get_calendar(
                calendar_id="demo-xnys-2026-v1"
            )
            sessions = market_time.list_sessions(
                calendar_id="demo-xnys-2026-v1"
            )
            durable_replay = market_time.get_replay(
                replay_id="demo-market-replay-001"
            )
        assert calendar is not None
        assert [item.id for item in sessions] == [
            "demo-xnys-2026-07-28-regular",
            "demo-xnys-2026-07-29-regular",
        ]
        assert durable_replay is not None
        assert durable_replay.session.status == "paused"
        assert durable_replay.session.cursor.position == 4
        recovered = MarketDataReplayEngine(
            replay_id=durable_replay.session.replay_id,
            events=durable_replay.events,
            cursor=durable_replay.session.cursor,
        )
        recovered.resume()
        assert [event.event_id for event in recovered.iter_remaining()] == [
            "demo-market-event-005",
        ]
        assert recovered.session.status == "completed"
        with factory() as session:
            unchanged = SqlAlchemyMarketTimeRepository(
                session=session
            ).get_replay(replay_id="demo-market-replay-001")
        assert unchanged == durable_replay
    finally:
        engine.dispose()


def test_demo_v5_restart_exact_replay_conflict_and_concurrent_convergence(
    tmp_path: Path,
) -> None:
    target = tmp_path / "demo-workspace"
    _install(DEMO_SOURCE, target)
    engine, factory, journey = _demo_m33(target)
    descriptor = load_demo_workspace_descriptor(target).to_dict()
    account = PaperAccountApplicationService(session_factory=factory).get_account_detail(
        account_id=journey["account_id"]
    ).account
    market = descriptor["market_time"]
    runtime = create_moving_average_crossover_runtime_reference(
        fast_window=2,
        slow_window=3,
        target_position_quantity=PaperQuantity.parse("10"),
    )
    engine.dispose()

    reopened = create_product_database_engine(
        config=resolve_product_database_config(
            database_path=DemoWorkspacePaths.from_root(target).database_path
        )
    )
    reopened_factory = create_product_session_factory(engine=reopened)
    service = StrategyOrderApplicationService(session_factory=reopened_factory)
    with reopened.connect() as connection:
        before_counts = tuple(
            connection.exec_driver_sql(f"SELECT COUNT(*) FROM {table}").scalar_one()
            for table in (
                "strategy_signals",
                "order_intents",
                "pre_trade_risk_decisions",
                "strategy_order_command_receipts",
            )
        )
    exact = service.evaluate_and_store_strategy_signal(
        strategy_runtime_reference=runtime,
        calendar_id=market["calendar_id"],
        expected_calendar_version=1,
        trading_session_id=journey["trading_session_id"],
        replay_id=market["replay_id"],
        expected_event_stream_digest=market["event_stream_digest"],
        expected_cursor_position=market["checkpoint"]["position"],
        expected_signal_event_id=market["checkpoint"]["last_event_id"],
        instrument_id=journey["instrument_id"],
        command_idempotency_key="demo-m33-signal-v1",
        actor="demo-founder",
        created_at=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    assert exact.replayed
    assert exact.result.signal_id == journey["signal"]["id"]
    assert exact.result.signal_digest == journey["signal"]["digest"]
    exact_intent = service.derive_and_store_order_intent(
        signal_id=journey["signal"]["id"],
        account_id=journey["account_id"],
        expected_account_head_version=account.head_version,
        expected_account_head_event_id=account.head_event_id,
        expected_account_head_chain_digest=account.head_chain_digest,
        command_idempotency_key=journey["intent"]["receipt"]["idempotency_key"],
        actor="demo-founder",
        created_at=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    assert exact_intent.replayed
    assert exact_intent.result.intent_id == journey["intent"]["id"]
    assert exact_intent.result.intent_digest == journey["intent"]["digest"]
    risk_common = {
        "intent_id": journey["intent"]["id"],
        "expected_account_head_version": account.head_version,
        "expected_account_head_event_id": account.head_event_id,
        "expected_account_head_chain_digest": account.head_chain_digest,
        "expected_calendar_id": market["calendar_id"],
        "expected_calendar_version": 1,
        "expected_trading_session_id": journey["trading_session_id"],
        "expected_replay_id": market["replay_id"],
        "expected_event_stream_digest": market["event_stream_digest"],
        "expected_cursor_position": market["checkpoint"]["position"],
        "expected_current_event_id": market["checkpoint"]["last_event_id"],
        "expected_instrument_id": journey["instrument_id"],
        "actor": "demo-founder",
        "created_at": datetime(2030, 1, 1, tzinfo=timezone.utc),
    }
    for name, maximum in (("allow_decision", None), ("reject_decision", "5")):
        replayed = service.evaluate_and_store_pre_trade_risk(
            **risk_common,
            risk_policy_reference=create_long_only_cash_risk_policy_reference(
                maximum_order_quantity=(
                    None if maximum is None else PaperQuantity.parse(maximum)
                )
            ),
            command_idempotency_key=journey[name]["receipt"]["idempotency_key"],
        )
        assert replayed.replayed
        assert replayed.result.decision_id == journey[name]["id"]
        assert replayed.result.decision_digest == journey[name]["digest"]
    with reopened.connect() as connection:
        assert tuple(
            connection.exec_driver_sql(f"SELECT COUNT(*) FROM {table}").scalar_one()
            for table in (
                "strategy_signals",
                "order_intents",
                "pre_trade_risk_decisions",
                "strategy_order_command_receipts",
            )
        ) == before_counts
    with pytest.raises(StrategyOrderIdempotencyConflictError):
        service.evaluate_and_store_strategy_signal(
            strategy_runtime_reference=create_moving_average_crossover_runtime_reference(
                fast_window=1,
                slow_window=3,
                target_position_quantity=PaperQuantity.parse("10"),
            ),
            calendar_id=market["calendar_id"],
            expected_calendar_version=1,
            trading_session_id=journey["trading_session_id"],
            replay_id=market["replay_id"],
            expected_event_stream_digest=market["event_stream_digest"],
            expected_cursor_position=market["checkpoint"]["position"],
            expected_signal_event_id=market["checkpoint"]["last_event_id"],
            instrument_id=journey["instrument_id"],
            command_idempotency_key="demo-m33-signal-v1",
            actor="demo-founder",
            created_at=datetime(2030, 1, 1, tzinfo=timezone.utc),
        )

    def alternate(index: int):
        return StrategyOrderApplicationService(
            session_factory=reopened_factory
        ).derive_and_store_order_intent(
            signal_id=journey["signal"]["id"],
            account_id=journey["account_id"],
            expected_account_head_version=account.head_version,
            expected_account_head_event_id=account.head_event_id,
            expected_account_head_chain_digest=account.head_chain_digest,
            command_idempotency_key=f"demo-m33-intent-concurrent-{index}",
            actor=f"demo-concurrent-{index}",
            created_at=datetime(2030, 1, index + 1, tzinfo=timezone.utc),
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(pool.map(alternate, (1, 2)))
    assert {item.result.intent_id for item in results} == {journey["intent"]["id"]}
    assert not any(item.replayed for item in results)

    def duplicate():
        return StrategyOrderApplicationService(
            session_factory=reopened_factory
        ).derive_and_store_order_intent(
            signal_id=journey["signal"]["id"],
            account_id=journey["account_id"],
            expected_account_head_version=account.head_version,
            expected_account_head_event_id=account.head_event_id,
            expected_account_head_chain_digest=account.head_chain_digest,
            command_idempotency_key="demo-m33-intent-duplicate-race",
            actor="demo-duplicate-race",
            created_at=datetime(2030, 1, 10, tzinfo=timezone.utc),
        )

    with reopened.connect() as connection:
        before_duplicate = tuple(
            connection.exec_driver_sql(f"SELECT COUNT(*) FROM {table}").scalar_one()
            for table in ("order_intents", "strategy_order_command_receipts")
        )
    with ThreadPoolExecutor(max_workers=2) as pool:
        duplicates = tuple(pool.map(lambda _: duplicate(), (1, 2)))
    assert {item.result for item in duplicates} == {exact_intent.result}
    assert {item.replayed for item in duplicates} == {False, True}
    with reopened.connect() as connection:
        after_duplicate = tuple(
            connection.exec_driver_sql(f"SELECT COUNT(*) FROM {table}").scalar_one()
            for table in ("order_intents", "strategy_order_command_receipts")
        )
    assert after_duplicate == (before_duplicate[0], before_duplicate[1] + 1)

    blocker = reopened.connect()
    try:
        blocker.exec_driver_sql("BEGIN IMMEDIATE")
        with pytest.raises(StrategyOrderStorageBusyError):
            duplicate()
    finally:
        blocker.rollback()
        blocker.close()
    with reopened.connect() as connection:
        assert tuple(
            connection.exec_driver_sql(f"SELECT COUNT(*) FROM {table}").scalar_one()
            for table in ("order_intents", "strategy_order_command_receipts")
        ) == after_duplicate
    reopened.dispose()


def test_demo_v5_duplicate_signal_race_creates_one_absent_authority(
    tmp_path: Path,
) -> None:
    target = tmp_path / "demo-workspace"
    _install(DEMO_SOURCE, target)
    paths = DemoWorkspacePaths.from_root(target)
    descriptor = load_demo_workspace_descriptor(target).to_dict()
    journey = descriptor["strategy_order"]
    market = descriptor["market_time"]
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    factory = create_product_session_factory(engine=engine)
    account_service = PaperAccountApplicationService(session_factory=factory)
    signal_service = StrategyOrderApplicationService(session_factory=factory)
    account_before = account_service.get_account_detail(
        account_id=journey["account_id"]
    )
    history_before = account_service.get_account_history(
        account_id=journey["account_id"]
    )
    with factory() as session:
        replay_before = SqlAlchemyMarketTimeRepository(session=session).get_replay(
            replay_id=market["replay_id"]
        )
    assert replay_before is not None

    runtime = create_moving_average_crossover_runtime_reference(
        fast_window=2,
        slow_window=3,
        target_position_quantity=PaperQuantity.parse("11"),
    )
    command_key = "demo-m33-signal-absent-duplicate-race"
    actor = "demo-absent-signal-race"
    created_at = datetime(2030, 1, 11, tzinfo=timezone.utc)
    signals_before = signal_service.list_strategy_signals(limit=10).items
    assert len(signals_before) == 1
    assert signals_before[0].signal_id == journey["signal"]["id"]
    assert signals_before[0].strategy_runtime_reference != runtime
    with engine.connect() as connection:
        counts_before = tuple(
            connection.exec_driver_sql(f"SELECT COUNT(*) FROM {table}").scalar_one()
            for table in (
                "strategy_signals",
                "order_intents",
                "pre_trade_risk_decisions",
                "strategy_order_command_receipts",
            )
        )
        scoped_receipts_before = connection.exec_driver_sql(
            "SELECT COUNT(*) FROM strategy_order_command_receipts "
            "WHERE namespace = ? AND command_idempotency_key = ?",
            ("evaluate_strategy_signal", command_key),
        ).scalar_one()
    assert scoped_receipts_before == 0

    start = Barrier(2)

    def create_signal():
        start.wait()
        return StrategyOrderApplicationService(
            session_factory=factory
        ).evaluate_and_store_strategy_signal(
            strategy_runtime_reference=runtime,
            calendar_id=market["calendar_id"],
            expected_calendar_version=1,
            trading_session_id=journey["trading_session_id"],
            replay_id=market["replay_id"],
            expected_event_stream_digest=market["event_stream_digest"],
            expected_cursor_position=market["checkpoint"]["position"],
            expected_signal_event_id=market["checkpoint"]["last_event_id"],
            instrument_id=journey["instrument_id"],
            command_idempotency_key=command_key,
            actor=actor,
            created_at=created_at,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(pool.map(lambda _: create_signal(), (1, 2)))

    assert {result.replayed for result in results} == {False, True}
    assert len({result.result.signal_id for result in results}) == 1
    assert len({result.result.signal_digest for result in results}) == 1
    created = results[0].result
    assert created.strategy_runtime_reference == runtime
    assert created.signal_id != journey["signal"]["id"]
    assert signal_service.get_strategy_signal(signal_id=created.signal_id) == created
    assert signal_service.list_strategy_signals(limit=10).items == (
        created,
        signals_before[0],
    )

    with engine.connect() as connection:
        counts_after = tuple(
            connection.exec_driver_sql(f"SELECT COUNT(*) FROM {table}").scalar_one()
            for table in (
                "strategy_signals",
                "order_intents",
                "pre_trade_risk_decisions",
                "strategy_order_command_receipts",
            )
        )
        scoped_receipts_after = connection.exec_driver_sql(
            "SELECT COUNT(*) FROM strategy_order_command_receipts "
            "WHERE namespace = ? AND command_idempotency_key = ?",
            ("evaluate_strategy_signal", command_key),
        ).scalar_one()
        duplicate_authority = connection.exec_driver_sql(
            "SELECT COUNT(*) FROM strategy_signals WHERE signal_id = ?",
            (created.signal_id,),
        ).scalar_one()
        orphan_receipts = connection.exec_driver_sql(
            "SELECT COUNT(*) FROM strategy_order_command_receipts AS receipt "
            "LEFT JOIN strategy_signals AS signal "
            "ON receipt.result_id = signal.signal_id "
            "WHERE receipt.namespace = ? "
            "AND receipt.command_idempotency_key = ? "
            "AND signal.signal_id IS NULL",
            ("evaluate_strategy_signal", command_key),
        ).scalar_one()
    assert counts_after == (
        counts_before[0] + 1,
        counts_before[1],
        counts_before[2],
        counts_before[3] + 1,
    )
    assert scoped_receipts_after == 1
    assert duplicate_authority == 1
    assert orphan_receipts == 0

    account_after = account_service.get_account_detail(
        account_id=journey["account_id"]
    )
    history_after = account_service.get_account_history(
        account_id=journey["account_id"]
    )
    with factory() as session:
        replay_after = SqlAlchemyMarketTimeRepository(session=session).get_replay(
            replay_id=market["replay_id"]
        )
    assert account_after == account_before
    assert history_after == history_before
    assert replay_after == replay_before
    engine.dispose()


def test_demo_v5_stale_authority_and_corruption_fail_closed_without_repair(
    tmp_path: Path,
) -> None:
    target = tmp_path / "demo-workspace"
    _install(DEMO_SOURCE, target)
    engine, factory, journey = _demo_m33(target)
    descriptor = load_demo_workspace_descriptor(target).to_dict()
    service = StrategyOrderApplicationService(session_factory=factory)
    with engine.connect() as connection:
        before = connection.exec_driver_sql(
            "SELECT COUNT(*) FROM strategy_order_command_receipts"
        ).scalar_one()
    with pytest.raises(StrategyOrderStaleAuthorityError):
        service.derive_and_store_order_intent(
            signal_id=journey["signal"]["id"],
            account_id=journey["account_id"],
            expected_account_head_version=999,
            expected_account_head_event_id="stale-event",
            expected_account_head_chain_digest="0" * 64,
            command_idempotency_key="demo-stale-account",
            actor="demo-founder",
            created_at=datetime(2030, 1, 1, tzinfo=timezone.utc),
        )
    runtime = create_moving_average_crossover_runtime_reference(
        fast_window=2,
        slow_window=3,
        target_position_quantity=PaperQuantity.parse("10"),
    )
    with pytest.raises(StrategyOrderStaleAuthorityError):
        service.evaluate_and_store_strategy_signal(
            strategy_runtime_reference=runtime,
            calendar_id=descriptor["market_time"]["calendar_id"],
            expected_calendar_version=1,
            trading_session_id=journey["trading_session_id"],
            replay_id=descriptor["market_time"]["replay_id"],
            expected_event_stream_digest="0" * 64,
            expected_cursor_position=4,
            expected_signal_event_id="demo-market-event-004",
            instrument_id=journey["instrument_id"],
            command_idempotency_key="demo-stale-market",
            actor="demo-founder",
            created_at=datetime(2030, 1, 1, tzinfo=timezone.utc),
        )
    with engine.connect() as connection:
        after = connection.exec_driver_sql(
            "SELECT COUNT(*) FROM strategy_order_command_receipts"
        ).scalar_one()
    assert after == before
    engine.dispose()

    database = DemoWorkspacePaths.from_root(target).database_path
    with sqlite3.connect(database) as connection:
        connection.execute("DROP TRIGGER trg_strategy_order_command_receipts_no_update")
        connection.execute(
            "UPDATE strategy_order_command_receipts SET result_digest = ? "
            "WHERE namespace = ? AND command_idempotency_key = ?",
            (
                "f" * 64,
                "evaluate_strategy_signal",
                "demo-m33-signal-v1",
            ),
        )
        connection.commit()
    with pytest.raises(DemoWorkspaceUnavailableError):
        validate_installed_demo_workspace(target)
    with pytest.raises(DemoWorkspaceUnavailableError):
        install_demo_workspace(
            source_root=DEMO_SOURCE,
            workspace_root=target,
            workspace_mode="demo",
            alembic_config_path=ALEMBIC_CONFIG,
        )
    with sqlite3.connect(database) as connection:
        persisted = connection.execute(
            "SELECT result_digest FROM strategy_order_command_receipts "
            "WHERE namespace = ? AND command_idempotency_key = ?",
            ("evaluate_strategy_signal", "demo-m33-signal-v1"),
        ).fetchone()
    assert persisted == ("f" * 64,)
    corrupt_engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=database)
    )
    corrupt_service = StrategyOrderApplicationService(
        session_factory=create_product_session_factory(engine=corrupt_engine)
    )
    with pytest.raises(StrategyOrderCorruptAuthorityError):
        corrupt_service.evaluate_and_store_strategy_signal(
            strategy_runtime_reference=runtime,
            calendar_id=descriptor["market_time"]["calendar_id"],
            expected_calendar_version=1,
            trading_session_id=journey["trading_session_id"],
            replay_id=descriptor["market_time"]["replay_id"],
            expected_event_stream_digest=descriptor["market_time"]["event_stream_digest"],
            expected_cursor_position=4,
            expected_signal_event_id="demo-market-event-004",
            instrument_id=journey["instrument_id"],
            command_idempotency_key="demo-m33-signal-v1",
            actor="demo-founder",
            created_at=datetime(2030, 1, 1, tzinfo=timezone.utc),
        )
    corrupt_engine.dispose()


def test_populated_0009_upgrade_then_explicit_demo_v5_install_and_verify(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Migration stays seed-free; the explicit installer adds M33 exactly once."""
    target = tmp_path / "demo-workspace"
    _install(DEMO_SOURCE, target)
    paths = DemoWorkspacePaths.from_root(target)
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(paths.database_path))
    config = AlembicConfig(str(ALEMBIC_CONFIG))
    alembic_command.downgrade(config, "0009_market_time_runtime")
    with sqlite3.connect(paths.database_path) as connection:
        assert connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone() == ("0009_market_time_runtime",)
        for table in (
            "strategy_signals",
            "order_intents",
            "pre_trade_risk_decisions",
            "strategy_order_command_receipts",
        ):
            assert connection.execute(
                "SELECT COUNT(*) FROM sqlite_master "
                "WHERE type = 'table' AND name = ?",
                (table,),
            ).fetchone() == (0,)
        account_count = connection.execute(
            "SELECT COUNT(*) FROM paper_accounts"
        ).fetchone()
        replay_count = connection.execute(
            "SELECT COUNT(*) FROM market_data_replays"
        ).fetchone()

    original_seed = demo_workspace_module._seed_demo_strategy_order
    observed_migration_counts: list[tuple[int, int, int, int]] = []

    def seed_after_upgrade(*, paths, source):
        with sqlite3.connect(paths.database_path) as connection:
            assert connection.execute(
                "SELECT version_num FROM alembic_version"
            ).fetchone() == ("0011_paper_execution",)
            observed_migration_counts.append(
                tuple(
                    connection.execute(
                        f"SELECT COUNT(*) FROM {table}"
                    ).fetchone()[0]
                    for table in (
                        "strategy_signals",
                        "order_intents",
                        "pre_trade_risk_decisions",
                        "strategy_order_command_receipts",
                    )
                )
            )
            assert connection.execute(
                "SELECT COUNT(*) FROM paper_accounts"
            ).fetchone() == account_count
            assert connection.execute(
                "SELECT COUNT(*) FROM market_data_replays"
            ).fetchone() == replay_count
        original_seed(paths=paths, source=source)

    monkeypatch.setattr(
        demo_workspace_module,
        "_seed_demo_strategy_order",
        seed_after_upgrade,
    )
    installed = _install(DEMO_SOURCE, target)
    assert installed.already_installed
    assert observed_migration_counts == [(0, 0, 0, 0)]
    validate_installed_demo_workspace(target)
    with sqlite3.connect(paths.database_path) as connection:
        counts = tuple(
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "strategy_signals",
                "order_intents",
                "pre_trade_risk_decisions",
                "strategy_order_command_receipts",
            )
        )
    assert counts == (1, 1, 2, 4)
    replayed = _install(DEMO_SOURCE, target)
    assert replayed.already_installed
    validate_installed_demo_workspace(target)
    with sqlite3.connect(paths.database_path) as connection:
        assert tuple(
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "strategy_signals",
                "order_intents",
                "pre_trade_risk_decisions",
                "strategy_order_command_receipts",
            )
        ) == counts


def test_prior_dataset_marker_is_refused_without_reinstall_or_mutation(
    tmp_path: Path,
) -> None:
    target = tmp_path / "demo-workspace"
    _install(DEMO_SOURCE, target)
    paths = DemoWorkspacePaths.from_root(target)
    marker_path = target / ".demo-workspace-install.json"
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    marker["dataset_version"] = 2
    marker_path.write_text(json.dumps(marker), encoding="utf-8")
    artifacts_before = {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in target.rglob("*")
        if path.is_file() and path != paths.database_path
    }

    with pytest.raises(DemoWorkspaceConflictError):
        _install(DEMO_SOURCE, target)

    assert {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in target.rglob("*")
        if path.is_file() and path != paths.database_path
    } == artifacts_before


def test_exact_replay_preserves_an_existing_human_decision(tmp_path: Path) -> None:
    target = tmp_path / "demo-workspace"
    _install(DEMO_SOURCE, target)
    paths = DemoWorkspacePaths.from_root(target)
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    factory = create_product_session_factory(engine=engine)
    try:
        decided = record_portfolio_review_decision_with_outcome(
            session_factory=factory,
            artifact_root=paths.evidence_root,
            review_id="demo-portfolio-review-001",
            idempotency_key="demo-founder-decision-v1",
            decision_id="demo-portfolio-decision-001",
            outcome="deferred",
            rationale="Founder acceptance test decision; no execution authority.",
            reviewed_by="demo-founder",
            reviewed_timestamp="2026-01-18T12:10:00Z",
            notes=("Preserved across exact Demo replay.",),
        )
        assert decided.review.record.status == "deferred"

        replay = _install(DEMO_SOURCE, target)

        assert replay.already_installed is True
        reopened = get_portfolio_review_detail(
            session_factory=factory,
            artifact_root=paths.evidence_root,
            review_id="demo-portfolio-review-001",
        )
        assert reopened.record.status == "deferred"
        assert reopened.decision is not None
        assert reopened.decision.decision_id == "demo-portfolio-decision-001"
    finally:
        engine.dispose()


def test_source_validation_failure_precedes_target_creation(tmp_path: Path) -> None:
    source = tmp_path / "source"
    shutil.copytree(DEMO_SOURCE, source)
    metrics = (
        source
        / "research_artifacts"
        / "moving-average-crossover-demo"
        / "demo-research-001"
        / "results"
        / "metrics.json"
    )
    metrics.write_text("not-json", encoding="utf-8")
    target = tmp_path / "target"

    with pytest.raises(DemoWorkspaceSourceInvalidError):
        _install(source, target)

    assert not target.exists()


@pytest.mark.parametrize(
    "case",
    (
        "invalid_path",
        "extra_root_child",
        "extra_request_key",
        "unsupported_reference_type",
        "duplicate_evidence",
        "invalid_return_matrix",
        "invalid_weight",
        "invalid_timestamp",
        "non_demo_warning",
    ),
)
def test_portfolio_review_source_mutations_fail_before_target_creation(
    tmp_path: Path,
    case: str,
) -> None:
    source = tmp_path / f"source-{case}"
    shutil.copytree(DEMO_SOURCE, source)
    manifest_path = source / "workspace-manifest.json"
    request_path = source / "portfolio_reviews" / "create-request.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    request = json.loads(request_path.read_text(encoding="utf-8"))
    if case == "invalid_path":
        manifest["portfolio_review_example"]["request_relative_path"] = (
            "../create-request.json"
        )
    elif case == "extra_root_child":
        (source / "unexpected").mkdir()
    elif case == "extra_request_key":
        request["unexpected"] = True
    elif case == "unsupported_reference_type":
        request["source"]["components"][0]["evidence_references"][0][
            "reference_type"
        ] = "unsupported_reference_type"
    elif case == "duplicate_evidence":
        references = request["source"]["components"][0]["evidence_references"]
        references.append(dict(references[0]))
    elif case == "invalid_return_matrix":
        request["source"]["return_observations"][0]["component_returns"] = [0.01]
    elif case == "invalid_weight":
        request["baseline_scenario"]["weights"]["demo-aapl-sleeve"] = -0.1
    elif case == "invalid_timestamp":
        request["analysis"]["created_timestamp"] = "not-a-timestamp"
    elif case == "non_demo_warning":
        request["source"]["warnings"] = ["Synthetic evidence only."]
    else:  # pragma: no cover - the parameter list is exhaustive
        raise AssertionError(case)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    request_path.write_text(json.dumps(request), encoding="utf-8")
    target = tmp_path / f"target-{case}"

    with pytest.raises(DemoWorkspaceSourceInvalidError):
        _install(source, target)

    assert not target.exists()


@pytest.mark.parametrize(
    "case",
    (
        "invalid_path",
        "extra_key",
        "noncanonical_cash",
        "wrong_version",
        "duplicate_authority_id",
        "wrong_event_order",
    ),
)
def test_paper_account_source_mutations_fail_before_target_creation(
    tmp_path: Path,
    case: str,
) -> None:
    source = tmp_path / f"source-paper-account-{case}"
    shutil.copytree(DEMO_SOURCE, source)
    manifest_path = source / "workspace-manifest.json"
    journey_path = source / "paper_accounts" / "account-journey.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    journey = json.loads(journey_path.read_text(encoding="utf-8"))
    if case == "invalid_path":
        manifest["paper_account_example"]["request_relative_path"] = (
            "../account-journey.json"
        )
    elif case == "extra_key":
        journey["unexpected"] = True
    elif case == "noncanonical_cash":
        journey["creation"]["initial_cash"] = "100000.0"
    elif case == "wrong_version":
        journey["position_adjustment"]["expected_account_version"] = 3
    elif case == "duplicate_authority_id":
        journey["authority_ids"][1]["value"] = journey["authority_ids"][0][
            "value"
        ]
    elif case == "wrong_event_order":
        journey["expected"]["event_types"].reverse()
    else:  # pragma: no cover - the parameter list is exhaustive
        raise AssertionError(case)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    journey_path.write_text(json.dumps(journey), encoding="utf-8")
    target = tmp_path / f"target-paper-account-{case}"

    with pytest.raises(DemoWorkspaceSourceInvalidError):
        _install(source, target)

    assert not target.exists()


@pytest.mark.parametrize(
    "case",
    (
        "invalid_path",
        "wrong_digest",
        "event_outside_session",
        "completed_checkpoint",
    ),
)
def test_market_time_source_mutations_fail_before_target_creation(
    tmp_path: Path,
    case: str,
) -> None:
    source = tmp_path / f"source-market-time-{case}"
    shutil.copytree(DEMO_SOURCE, source)
    manifest_path = source / "workspace-manifest.json"
    journey_path = source / "market_time" / "replay-journey.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    journey = json.loads(journey_path.read_text(encoding="utf-8"))
    if case == "invalid_path":
        manifest["market_time_example"]["request_relative_path"] = (
            "../replay-journey.json"
        )
    elif case == "wrong_digest":
        journey["expected"]["event_stream_digest"] = "0" * 64
    elif case == "event_outside_session":
        journey["events"][0]["event_time"] = "2026-07-28T21:00:00Z"
    elif case == "completed_checkpoint":
        journey["checkpoint_after_event_count"] = len(journey["events"])
    else:  # pragma: no cover - the parameter list is exhaustive
        raise AssertionError(case)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    journey_path.write_text(json.dumps(journey), encoding="utf-8")
    target = tmp_path / f"target-market-time-{case}"

    with pytest.raises(DemoWorkspaceSourceInvalidError):
        _install(source, target)

    assert not target.exists()


def test_conflicting_dataset_replay_is_refused_without_changes(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    shutil.copytree(DEMO_SOURCE, source)
    target = tmp_path / "target"
    _install(source, target)
    marker_before = (target / ".demo-workspace-install.json").read_bytes()
    (source / "README.md").write_text("changed demo source\n", encoding="utf-8")

    with pytest.raises(DemoWorkspaceConflictError):
        _install(source, target)

    assert (target / ".demo-workspace-install.json").read_bytes() == marker_before
    assert load_demo_workspace_descriptor(target).to_dict()["dataset_version"] == 5


def test_descriptor_requires_exact_dataset_version_five(tmp_path: Path) -> None:
    target = tmp_path / "demo-workspace"
    _install(DEMO_SOURCE, target)
    descriptor_path = target / "workspace-descriptor.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor["dataset_version"] = 2
    descriptor_path.write_text(json.dumps(descriptor), encoding="utf-8")

    with pytest.raises(DemoWorkspaceUnavailableError):
        load_demo_workspace_descriptor(target)


def test_seeded_portfolio_review_corruption_fails_closed(tmp_path: Path) -> None:
    target = tmp_path / "demo-workspace"
    _install(DEMO_SOURCE, target)
    source_path = next(
        path
        for path in (target / "evidence").rglob("*.json")
        if json.loads(path.read_text(encoding="utf-8")).get("source_id")
        == "demo-portfolio-review-source-001"
    )
    source_payload = json.loads(source_path.read_text(encoding="utf-8"))
    source_payload["evaluation_frequency"] = "tampered"
    source_path.write_text(json.dumps(source_payload), encoding="utf-8")

    with pytest.raises(DemoWorkspaceUnavailableError):
        _install(DEMO_SOURCE, target)


def test_projection_corruption_fails_closed_without_repair(tmp_path: Path) -> None:
    target = tmp_path / "demo-workspace"
    _install(DEMO_SOURCE, target)
    database = target / "product.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE paper_account_projections "
            "SET cash_balance = '999', available_cash = '999' "
            "WHERE account_id = 'demo-paper-account-001'"
        )
        connection.commit()

    with pytest.raises(DemoWorkspaceUnavailableError):
        _install(DEMO_SOURCE, target)

    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT cash_balance, available_cash "
            "FROM paper_account_projections "
            "WHERE account_id = 'demo-paper-account-001'"
        ).fetchone()
    assert row == ("999", "999")


def test_market_time_checkpoint_corruption_fails_closed_without_repair_or_account_change(
    tmp_path: Path,
) -> None:
    target = tmp_path / "demo-workspace"
    _install(DEMO_SOURCE, target)
    database = target / "product.sqlite3"
    with sqlite3.connect(database) as connection:
        account_before = connection.execute(
            "SELECT account_id, head_version, head_event_id, "
            "head_chain_digest FROM paper_accounts ORDER BY account_id"
        ).fetchall()
        connection.execute(
            "UPDATE market_data_replays "
            "SET position = 1, last_event_id = 'demo-market-event-001', "
            "current_event_time = '2026-07-28 13:30:00.000000', "
            "status = 'paused' "
            "WHERE replay_id = 'demo-market-replay-001'"
        )
        connection.commit()

    with pytest.raises(DemoWorkspaceUnavailableError):
        _install(DEMO_SOURCE, target)

    with sqlite3.connect(database) as connection:
        checkpoint = connection.execute(
            "SELECT position, last_event_id, status "
            "FROM market_data_replays "
            "WHERE replay_id = 'demo-market-replay-001'"
        ).fetchone()
        account_after = connection.execute(
            "SELECT account_id, head_version, head_event_id, "
            "head_chain_digest FROM paper_accounts ORDER BY account_id"
        ).fetchall()
    assert checkpoint == (1, "demo-market-event-001", "paused")
    assert account_after == account_before


def test_demo_install_never_changes_separate_standard_storage(
    tmp_path: Path,
) -> None:
    standard = tmp_path / "standard"
    standard.mkdir()
    standard_database = standard / "product.sqlite3"
    standard_artifact = standard / "founder-evidence.json"
    standard_database.write_bytes(b"standard-database-sentinel")
    standard_artifact.write_bytes(b'{"standard":true}\n')
    before = {
        path.name: path.read_bytes()
        for path in standard.iterdir()
    }

    _install(DEMO_SOURCE, tmp_path / "demo-workspace")

    assert {
        path.name: path.read_bytes()
        for path in standard.iterdir()
    } == before


def test_non_demo_and_nonempty_targets_are_refused(tmp_path: Path) -> None:
    standard_target = tmp_path / "standard"
    with pytest.raises(DemoWorkspaceTargetRefusedError):
        install_demo_workspace(
            source_root=DEMO_SOURCE,
            workspace_root=standard_target,
            workspace_mode="standard",
            alembic_config_path=ALEMBIC_CONFIG,
        )
    assert not standard_target.exists()

    nonempty_target = tmp_path / "user-workspace"
    nonempty_target.mkdir()
    user_file = nonempty_target / "user-artifact.json"
    user_file.write_text('{"user": true}\n', encoding="utf-8")
    with pytest.raises(DemoWorkspaceTargetRefusedError):
        _install(DEMO_SOURCE, nonempty_target)
    assert json.loads(user_file.read_text(encoding="utf-8")) == {"user": True}
    assert tuple(nonempty_target.iterdir()) == (user_file,)


def test_failure_leaves_no_partial_visible_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import el_psy_quant.demo_workspace as demo_module

    target = tmp_path / "target"
    target.mkdir()

    def fail_population(**_kwargs) -> None:
        raise RuntimeError("injected failure")

    monkeypatch.setattr(demo_module, "_populate_database", fail_population)

    with pytest.raises(DemoWorkspaceUnavailableError):
        _install(DEMO_SOURCE, target)

    assert target.is_dir()
    assert tuple(target.iterdir()) == ()
    assert not (tmp_path / ".target.demo-install-staging").exists()


def test_standard_and_demo_compose_storage_are_distinct() -> None:
    standard = (PROJECT_ROOT / "compose.yaml").read_text(encoding="utf-8")
    demo = (PROJECT_ROOT / "compose.demo.yaml").read_text(encoding="utf-8")

    assert "name: el-psy-quant-mvp" in standard
    assert "name: el-psy-quant-demo" in demo
    assert "mvp-data:/data" in standard
    assert "demo-data:/data" in demo
    assert "EL_PSY_QUANT_WORKSPACE_MODE: demo" in demo
    assert "install-demo-workspace" not in standard
    assert "start-local-backend" in demo
