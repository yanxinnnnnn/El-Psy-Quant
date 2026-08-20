"""Focused Sprint 214 Demo v6 Paper Execution end-to-end evidence."""

from __future__ import annotations

import inspect
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import el_psy_quant.demo_workspace as demo_workspace_module
import pytest

from el_psy_quant.application import (
    PaperAccountApplicationService,
    PaperExecutionApplicationService,
)
from el_psy_quant.demo_workspace import (
    DemoWorkspacePaths,
    DemoWorkspaceSourceInvalidError,
    install_demo_workspace,
    load_demo_workspace_descriptor,
    validate_demo_workspace_source,
)
from el_psy_quant.local_workspace import (
    LocalWorkspaceVerification,
    start_local_backend,
    verify_local_workspace,
)
from el_psy_quant.paper_account import PaperQuantity
from el_psy_quant.paper_execution import (
    PaperExecutionBasisPoints,
    create_paper_execution_policy_reference,
)
from el_psy_quant.persistence import (
    SqlAlchemyMarketTimeRepository,
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV
from el_psy_quant.persistence.schema import CURRENT_PRODUCT_SCHEMA_REVISION

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "examples" / "demo_workspace"


def _install(target: Path) -> None:
    install_demo_workspace(
        source_root=SOURCE,
        workspace_root=target,
        workspace_mode="demo",
        alembic_config_path=ROOT / "alembic.ini",
    )


def test_demo_v6_uses_only_public_m34_application_orchestration() -> None:
    source = inspect.getsource(demo_workspace_module)

    assert "PaperExecutionApplicationService" in source
    assert "create_order_from_references" in source
    assert "step_order_from_reference" in source
    assert "PaperExecutionOrderRow" not in source
    assert "PaperExecutionAttemptRow" not in source
    assert "PaperExecutionFillRow" not in source
    assert "PaperExecutionSettlementLinkRow" not in source
    assert "INSERT INTO paper_execution" not in source


@pytest.mark.parametrize(
    "case",
    ("unknown_field", "malformed_digest", "duplicate_identity", "mismatched_event"),
)
def test_demo_v6_paper_execution_source_fails_closed(
    tmp_path: Path,
    case: str,
) -> None:
    source = tmp_path / "source"
    shutil.copytree(SOURCE, source)
    path = source / "paper_execution" / "execution-journey.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if case == "unknown_field":
        payload["scenarios"][0]["unexpected"] = True
    elif case == "malformed_digest":
        payload["scenarios"][0]["expected"]["intent"]["digest"] = "bad"
    elif case == "duplicate_identity":
        payload["scenarios"][1]["scenario_id"] = payload["scenarios"][0][
            "scenario_id"
        ]
    else:
        payload["scenarios"][1]["expected"]["attempts"][0][
            "consumed_event_id"
        ] = "wrong-event"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(DemoWorkspaceSourceInvalidError):
        validate_demo_workspace_source(source)


@pytest.mark.parametrize(
    ("field", "value", "valid"),
    (
        ("position_quantity", "0.123456789012", True),
        ("fill_quantity", "0.123456789012", True),
        ("position_quantity", "0.1234567890123", False),
        ("fill_quantity", "0.1234567890123", False),
        ("cash_balance", "0.12345678", True),
        ("cash_balance", "0.123456789", False),
        ("execution_price", "0.123456789", False),
    ),
)
def test_demo_v6_source_uses_exact_quantity_and_money_precision_contracts(
    tmp_path: Path,
    field: str,
    value: str,
    valid: bool,
) -> None:
    source = tmp_path / "source"
    shutil.copytree(SOURCE, source)
    path = source / "paper_execution" / "execution-journey.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if field == "position_quantity":
        payload["scenarios"][0]["expected"]["position_quantity"] = value
    elif field == "fill_quantity":
        payload["scenarios"][1]["expected"]["fills"][0]["quantity"] = value
    elif field == "cash_balance":
        payload["scenarios"][0]["expected"]["cash_balance"] = value
    else:
        payload["scenarios"][1]["expected"]["fills"][0][
            "execution_price"
        ] = value
    path.write_text(json.dumps(payload), encoding="utf-8")

    if valid:
        validate_demo_workspace_source(source)
    else:
        with pytest.raises(DemoWorkspaceSourceInvalidError):
            validate_demo_workspace_source(source)


def test_demo_v6_four_scenarios_reconstruct_exact_e2e_authority(
    tmp_path: Path,
) -> None:
    target = tmp_path / "demo-v6"
    _install(target)
    source = validate_demo_workspace_source(SOURCE)
    descriptor = load_demo_workspace_descriptor(target).to_dict()
    paths = DemoWorkspacePaths.from_root(target)
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    factory = create_product_session_factory(engine=engine)
    execution = PaperExecutionApplicationService(session_factory=factory)
    accounts = PaperAccountApplicationService(session_factory=factory)
    try:
        manual = source.paper_execution_journey.scenarios[0]
        manual_reference = descriptor["paper_execution"]["manual_candidate"]
        assert manual.kind == "manual"
        assert manual_reference["intent_id"] == manual.expected.intent.id
        assert not any(
            item.order.order_intent_reference.intent_id
            == manual_reference["intent_id"]
            for item in execution.list_order_histories(limit=200).items
        )

        completed = source.paper_execution_journey.scenarios[1]
        completed_history = execution.reconcile_order(
            execution_order_id=completed.expected.order.id  # type: ignore[union-attr]
        )
        assert completed_history.state.status == "filled"
        assert completed_history.state.execution_version == 3
        assert completed_history.state.remaining_quantity.to_json_value() == "0"
        assert tuple(item.attempt_result for item in completed_history.attempts) == (
            "no_fill",
            "fill",
            "fill",
        )
        assert completed_history.attempts[0].consumed_event_reference is not None
        assert completed_history.attempts[0].consumed_event_reference.event_id.endswith(
            "event-5"
        )
        assert completed_history.fills[0].execution_event_reference.event_id.endswith(
            "event-6"
        )
        assert completed_history.fills[0].execution_event_reference.event_id != (
            completed_history.order.market_handoff_reference.current_event_id
        )
        assert tuple(item.fill_quantity.to_json_value() for item in completed_history.fills) == (
            "4",
            "4",
        )
        assert all(
            item.execution_price_evidence.slippage_bps.to_json_value() != "0"
            and item.cost_evidence.total_charges.to_json_value() != "0"
            for item in completed_history.fills
        )
        assert len(completed_history.settlement_links) == len(completed_history.fills) == 2
        assert tuple(
            (
                item.pre_step_cursor.position,
                item.post_step_cursor.position,
            )
            for item in completed_history.attempts
        ) == ((4, 5), (5, 6), (6, 7))
        completed_account = accounts.get_account_detail(
            account_id=completed.account.account_id
        )
        assert completed_account.account.head_version == 3
        assert completed_account.projection.cash_balance.to_json_value() == "955.9295736"
        assert completed_account.projection.positions[0].quantity.to_json_value() == "8"
        assert (
            completed_account.projection.positions[0].aggregate_cost_basis.to_json_value()
            == "44.0704264"
        )
        completed_account_history = accounts.get_account_history(
            account_id=completed.account.account_id
        )
        assert tuple(
            item.event.event_type for item in completed_account_history
        ) == (
            "account_created",
            "execution_fill_posted",
            "execution_fill_posted",
        )

        risk = source.paper_execution_journey.scenarios[2]
        risk_history = execution.reconcile_order(
            execution_order_id=risk.expected.order.id  # type: ignore[union-attr]
        )
        assert risk_history.state.status == "rejected"
        assert tuple(item.attempt_result for item in risk_history.attempts) == (
            "risk_rejected",
        )
        assert not risk_history.fills
        assert not risk_history.settlement_links
        assert accounts.get_account_detail(
            account_id=risk.account.account_id
        ).account.head_version == 1

        exhaustion = source.paper_execution_journey.scenarios[3]
        exhaustion_history = execution.reconcile_order(
            execution_order_id=exhaustion.expected.order.id  # type: ignore[union-attr]
        )
        assert exhaustion_history.state.status == "partially_filled_rejected"
        assert tuple(item.attempt_result for item in exhaustion_history.attempts) == (
            "fill",
            "boundary_rejected",
        )
        assert exhaustion_history.attempts[-1].consumed_event_reference is None
        with factory() as session:
            replay = SqlAlchemyMarketTimeRepository(session=session).get_replay(
                replay_id=exhaustion.market.replay_id
            )
        assert replay is not None
        assert replay.session.cursor.position == 5
        assert replay.session.cursor.last_event_id.endswith("event-5")
    finally:
        engine.dispose()


def test_progressed_manual_scenario_survives_supported_demo_restart(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "demo-v6"
    _install(target)
    descriptor = load_demo_workspace_descriptor(target).to_dict()
    paper_execution = descriptor["paper_execution"]
    manual = paper_execution["manual_candidate"]
    policy = paper_execution["policy_draft"]
    paths = DemoWorkspacePaths.from_root(target)
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    factory = create_product_session_factory(engine=engine)
    execution = PaperExecutionApplicationService(
        session_factory=factory,
        clock=lambda: datetime(2026, 8, 24, tzinfo=timezone.utc),
    )
    execution_policy = create_paper_execution_policy_reference(
        max_fill_quantity_per_trade_event=PaperQuantity.parse(
            policy["max_fill_quantity_per_trade_event"]
        ),
        slippage_bps=PaperExecutionBasisPoints.parse(policy["slippage_bps"]),
        commission_bps=PaperExecutionBasisPoints.parse(
            policy["commission_bps"]
        ),
        fee_bps=PaperExecutionBasisPoints.parse(policy["fee_bps"]),
        buy_tax_bps=PaperExecutionBasisPoints.parse(policy["buy_tax_bps"]),
        sell_tax_bps=PaperExecutionBasisPoints.parse(policy["sell_tax_bps"]),
    )
    created = execution.create_order_from_references(
        intent_id=manual["intent_id"],
        intent_digest=manual["intent_digest"],
        decision_id=manual["decision_id"],
        decision_digest=manual["decision_digest"],
        execution_policy_reference=execution_policy,
        command_idempotency_key="demo-v6-review-manual-create",
        actor="demo-founder",
    )
    order = created.result.order
    for execution_version in range(3):
        execution.step_order_from_reference(
            execution_order_id=order.execution_order_id,
            execution_order_digest=order.execution_order_digest,
            expected_execution_version=execution_version,
            command_idempotency_key=(
                f"demo-v6-review-manual-step-{execution_version + 1}"
            ),
            actor="demo-founder",
        )
    before_history = execution.reconcile_order(
        execution_order_id=order.execution_order_id
    )
    accounts = PaperAccountApplicationService(session_factory=factory)
    before_account = accounts.get_account_detail(account_id=order.account_id)
    before_account_history = accounts.get_account_history(
        account_id=order.account_id
    )
    with factory() as session:
        before_replay = SqlAlchemyMarketTimeRepository(session=session).get_replay(
            replay_id=order.market_handoff_reference.replay_id
        )
    assert before_history.state.status == "filled"
    assert tuple(item.attempt_result for item in before_history.attempts) == (
        "no_fill",
        "fill",
        "fill",
    )
    assert len(before_history.fills) == len(before_history.settlement_links) == 2
    assert before_account.account.head_version == 3
    assert before_replay is not None
    assert before_replay.session.cursor.position == 7
    del execution, accounts, factory
    engine.dispose()

    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(paths.database_path))
    monkeypatch.setenv(
        "EL_PSY_QUANT_RESEARCH_ARTIFACT_ROOT", str(paths.research_root)
    )
    monkeypatch.setenv(
        "EL_PSY_QUANT_EVIDENCE_ARTIFACT_ROOT", str(paths.evidence_root)
    )
    monkeypatch.setenv("EL_PSY_QUANT_PAPER_ARTIFACT_ROOT", str(paths.paper_root))
    monkeypatch.setenv("EL_PSY_QUANT_WORKSPACE_MODE", "demo")
    monkeypatch.setenv("EL_PSY_QUANT_DEMO_WORKSPACE_ROOT", str(paths.root))
    served: list[str] = []
    startup = start_local_backend(
        mode="demo",
        workspace_root=paths.root,
        alembic_config_path=ROOT / "alembic.ini",
        demo_source_root=SOURCE,
        serve=lambda: served.append("serve"),
    )
    verified = verify_local_workspace(mode="demo", workspace_root=paths.root)

    expected_verification = LocalWorkspaceVerification(
        mode="demo",
        schema_revision=CURRENT_PRODUCT_SCHEMA_REVISION,
        dataset_id="founder-demo-workspace",
        dataset_version=6,
    )
    assert startup == verified == expected_verification
    assert served == ["serve"]

    reopened_engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=paths.database_path)
    )
    reopened_factory = create_product_session_factory(engine=reopened_engine)
    try:
        reopened_execution = PaperExecutionApplicationService(
            session_factory=reopened_factory
        )
        after_history = reopened_execution.reconcile_order(
            execution_order_id=order.execution_order_id
        )
        reopened_accounts = PaperAccountApplicationService(
            session_factory=reopened_factory
        )
        after_account = reopened_accounts.get_account_detail(
            account_id=order.account_id
        )
        after_account_history = reopened_accounts.get_account_history(
            account_id=order.account_id
        )
        with reopened_factory() as session:
            after_replay = SqlAlchemyMarketTimeRepository(session=session).get_replay(
                replay_id=order.market_handoff_reference.replay_id
            )
        assert after_history == before_history
        assert after_account == before_account
        assert after_account_history == before_account_history
        assert after_replay is not None
        assert after_replay.session.cursor == before_replay.session.cursor
    finally:
        reopened_engine.dispose()
