"""Focused Sprint 212 API and Sprint 215 adversarial error-surface coverage."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import event

from el_psy_quant.api.app import create_app
from el_psy_quant.api.middleware import REQUEST_ID_HEADER
from el_psy_quant.api.observability import PRODUCT_LOGGER_NAME
from el_psy_quant.api.errors import PublicApiError
from el_psy_quant.api.paper_execution_errors import (
    PaperExecutionInvalidCursorError,
    PaperExecutionInvalidDecimalError,
    PaperExecutionInvalidPolicyError,
    raise_paper_execution_api_error,
)
from el_psy_quant.api.paper_execution_pagination import (
    decode_paper_execution_list_cursor,
    encode_paper_execution_list_cursor,
)
from el_psy_quant.application import (
    PaperAccountApplicationService,
    StrategyOrderApplicationService,
)
from el_psy_quant.market_time import (
    MarketDataReplayEngine,
    create_market_data_event,
    create_trading_calendar,
    create_trading_session,
)
from el_psy_quant.paper_account import PaperMoney, PaperQuantity
from el_psy_quant.persistence import (
    PaperExecutionConcurrencyConflictError,
    PaperExecutionCorruptAuthorityError,
    PaperExecutionIdempotencyConflictError,
    PaperExecutionNotFoundError,
    PaperExecutionOperationConflictError,
    PaperExecutionReconciliationRequiredError,
    PaperExecutionStaleAuthorityError,
    PaperExecutionStorageBusyError,
    PaperExecutionStorageFailureError,
    SqlAlchemyMarketTimeRepository,
    create_market_data_replay_record,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV
from el_psy_quant.strategy_order import (
    create_long_only_cash_risk_policy_reference,
    create_moving_average_crossover_runtime_reference,
)

ROOT = Path(__file__).resolve().parents[1]
AUTH = ("execution-founder", "execution-secret")
CREATED = datetime(2026, 8, 19, 1, tzinfo=timezone.utc)
AUDIT = CREATED + timedelta(hours=10)
INSTRUMENT = "XNYS:AAPL"


@dataclass(frozen=True)
class _Configured:
    application: object
    database_path: Path
    account: object
    account_service: PaperAccountApplicationService
    intent: object
    decision: object


@pytest.fixture(autouse=True)
def _enable_product_logger() -> None:
    logging.getLogger(PRODUCT_LOGGER_NAME).disabled = False


@pytest.fixture
def configured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> _Configured:
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    application = create_app(
        product_database_path=path,
        founder_username=AUTH[0],
        founder_password=AUTH[1],
    )
    factory = application.state.product_session_factory
    counter: dict[str, int] = {}

    def identifier(kind: str) -> str:
        counter[kind] = counter.get(kind, 0) + 1
        return f"{kind}-s212-{counter[kind]}"

    account_service = PaperAccountApplicationService(
        session_factory=factory,
        clock=lambda: CREATED,
        id_factory=identifier,
    )
    account = account_service.create_account(
        display_name="Sprint 212 account",
        base_currency="USD",
        initial_cash=PaperMoney.parse("2000"),
        creation_idempotency_key="create-account-s212",
        actor="founder",
    ).account
    calendar = create_trading_calendar(
        id="calendar-s212",
        market="XNYS",
        timezone="UTC",
        calendar_version=1,
        created_at=CREATED,
    )
    trading_session = create_trading_session(
        id="session-s212",
        calendar_id=calendar.id,
        trading_date=date(2026, 8, 19),
        open_time=CREATED,
        close_time=CREATED + timedelta(hours=8),
        session_type="regular",
    )
    events = tuple(
        create_market_data_event(
            event_id=f"event-s212-{index}",
            instrument_id=(INSTRUMENT if index != 5 else "XNYS:MSFT"),
            event_time=CREATED + timedelta(minutes=index),
            event_type="trade",
            payload={"price": price},
            source="fixture:s212",
        )
        for index, price in enumerate((3, 2, 1, 4, 9, 5), start=1)
    )
    replay = MarketDataReplayEngine(replay_id="replay-s212", events=events)
    replay.start()
    for _ in range(4):
        assert replay.next_event() is not None
    with factory.begin() as session:
        repository = SqlAlchemyMarketTimeRepository(session=session)
        repository.add_calendar(calendar=calendar)
        repository.add_session(session=trading_session)
        repository.add_replay(
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
        command_idempotency_key="signal-s212",
        actor="founder",
        created_at=AUDIT,
    ).result
    intent = strategy.derive_and_store_order_intent(
        signal_id=signal.signal_id,
        account_id=account.account_id,
        expected_account_head_version=account.head_version,
        expected_account_head_event_id=account.head_event_id,
        expected_account_head_chain_digest=account.head_chain_digest,
        command_idempotency_key="intent-s212",
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
        command_idempotency_key="risk-s212",
        actor="founder",
        created_at=AUDIT + timedelta(minutes=2),
    ).result
    logging.getLogger(PRODUCT_LOGGER_NAME).disabled = False
    return _Configured(application, path, account, account_service, intent, decision)


def _create_payload(configured: _Configured) -> dict[str, object]:
    return {
        "intent": {
            "intent_id": configured.intent.intent_id,
            "intent_digest": configured.intent.intent_digest,
        },
        "decision": {
            "decision_id": configured.decision.decision_id,
            "decision_digest": configured.decision.decision_digest,
        },
        "execution_policy": {
            "max_fill_quantity_per_trade_event": None,
            "slippage_bps": "1.5",
            "commission_bps": "2",
            "fee_bps": "0.5",
            "buy_tax_bps": "0",
            "sell_tax_bps": "1",
        },
        "actor": "founder",
    }


def _create(client: TestClient, configured: _Configured, key: str = "create-s212"):
    return client.post(
        "/api/v1/paper-execution/orders",
        auth=AUTH,
        headers={"Idempotency-Key": key},
        json=_create_payload(configured),
    )


def _assert_error(response, status: int, code: str) -> None:
    assert response.status_code == status, response.text
    body = response.json()
    assert body["error"]["code"] == code
    assert body["request_id"] == response.headers[REQUEST_ID_HEADER]
    assert "SELECT " not in response.text
    assert "product.sqlite3" not in response.text


def test_exact_nine_route_inventory_auth_and_operation_ids(
    configured: _Configured,
) -> None:
    document = configured.application.openapi()
    operations = {
        (method.upper(), path, operation["operationId"])
        for path, methods in document["paths"].items()
        if path.startswith("/api/v1/paper-execution")
        for method, operation in methods.items()
    }
    assert operations == {
        ("POST", "/api/v1/paper-execution/orders", "create_paper_execution_order_v1"),
        ("GET", "/api/v1/paper-execution/orders", "list_paper_execution_orders_v1"),
        (
            "GET",
            "/api/v1/paper-execution/orders/{execution_order_id}",
            "get_paper_execution_order_v1",
        ),
        (
            "POST",
            "/api/v1/paper-execution/orders/{execution_order_id}/steps",
            "step_paper_execution_order_v1",
        ),
        (
            "GET",
            "/api/v1/paper-execution/orders/{execution_order_id}/attempts",
            "list_paper_execution_attempts_v1",
        ),
        (
            "GET",
            "/api/v1/paper-execution/attempts/{attempt_id}",
            "get_paper_execution_attempt_v1",
        ),
        ("GET", "/api/v1/paper-execution/fills", "list_paper_execution_fills_v1"),
        (
            "GET",
            "/api/v1/paper-execution/fills/{fill_id}",
            "get_paper_execution_fill_v1",
        ),
        (
            "GET",
            "/api/v1/paper-execution/orders/{execution_order_id}/reconciliation",
            "get_paper_execution_reconciliation_v1",
        ),
    }
    forbidden = ("cancel", "amend", "replace", "direct-fill", "settlement")
    assert not any(word in path for _, path, _ in operations for word in forbidden)
    with TestClient(configured.application) as client:
        response = client.get("/api/v1/paper-execution/orders")
    assert response.status_code == 401


def test_create_replay_convergence_strict_input_and_public_projection(
    configured: _Configured,
) -> None:
    with TestClient(configured.application) as client:
        created = _create(client, configured)
        assert created.status_code == 201, created.text
        body = created.json()
        order = body["result"]["order"]
        assert body["replayed"] is False
        assert body["request_id"] == created.headers[REQUEST_ID_HEADER]
        assert body["result"]["state"]["status"] == "working"
        assert "origin_command_idempotency_key" not in created.text
        assert isinstance(order["requested_quantity"], str)
        assert isinstance(order["execution_policy_reference"]["slippage_bps"], str)

        same = _create(client, configured)
        alternate = _create(client, configured, "alternate-create-s212")
        assert same.status_code == alternate.status_code == 200
        assert same.json()["replayed"] and alternate.json()["replayed"]
        assert (
            same.json()["result"]["order"]["execution_order_id"]
            == alternate.json()["result"]["order"]["execution_order_id"]
            == order["execution_order_id"]
        )

        extra = _create_payload(configured)
        extra["side"] = "buy"
        rejected = client.post(
            "/api/v1/paper-execution/orders",
            auth=AUTH,
            headers={"Idempotency-Key": "extra-field"},
            json=extra,
        )
        _assert_error(rejected, 422, "request_validation_error")

        invalid = _create_payload(configured)
        invalid["execution_policy"]["slippage_bps"] = "01"
        decimal_error = client.post(
            "/api/v1/paper-execution/orders",
            auth=AUTH,
            headers={"Idempotency-Key": "invalid-decimal"},
            json=invalid,
        )
        _assert_error(decimal_error, 422, "paper_execution_invalid_decimal")


def test_create_missing_upstream_is_stable_404(configured: _Configured) -> None:
    payload = _create_payload(configured)
    payload["intent"] = {
        "intent_id": "oi_" + "a" * 64,
        "intent_digest": "a" * 64,
    }
    with TestClient(configured.application) as client:
        response = client.post(
            "/api/v1/paper-execution/orders",
            auth=AUTH,
            headers={"Idempotency-Key": "missing-upstream"},
            json=payload,
        )
    _assert_error(response, 404, "paper_execution_upstream_authority_not_found")


def test_step_no_fill_fill_replay_reads_and_reconciliation(
    configured: _Configured,
) -> None:
    with TestClient(configured.application) as client:
        order = _create(client, configured).json()["result"]["order"]
        path = f"/api/v1/paper-execution/orders/{order['execution_order_id']}/steps"
        command = {
            "execution_order_digest": order["execution_order_digest"],
            "expected_execution_version": 0,
            "actor": "founder",
        }
        first = client.post(
            path,
            auth=AUTH,
            headers={"Idempotency-Key": "step-no-fill-s212"},
            json=command,
        )
        assert first.status_code == 201, first.text
        assert first.json()["result"]["fill"] is None
        assert first.json()["result"]["attempt"]["attempt_result"] == "no_fill"
        replay = client.post(
            path,
            auth=AUTH,
            headers={"Idempotency-Key": "step-no-fill-s212"},
            json=command,
        )
        assert replay.status_code == 200 and replay.json()["replayed"]

        command["expected_execution_version"] = 1
        filled = client.post(
            path,
            auth=AUTH,
            headers={"Idempotency-Key": "step-fill-s212"},
            json=command,
        )
        assert filled.status_code == 201, filled.text
        result = filled.json()["result"]
        assert result["fill"] is not None
        assert result["settlement_link"] is not None
        assert result["account_event_id"] is not None
        assert result["order_state"]["status"] == "filled"
        assert all(isinstance(result["fill"][key], str) for key in ("fill_quantity",))

        order_id = order["execution_order_id"]
        attempt_id = result["attempt"]["attempt_id"]
        fill_id = result["fill"]["fill_id"]
        assert (
            client.get(
                f"/api/v1/paper-execution/orders/{order_id}", auth=AUTH
            ).status_code
            == 200
        )
        assert (
            client.get(
                f"/api/v1/paper-execution/attempts/{attempt_id}", auth=AUTH
            ).status_code
            == 200
        )
        assert (
            client.get(
                f"/api/v1/paper-execution/fills/{fill_id}", auth=AUTH
            ).status_code
            == 200
        )
        reconciliation = client.get(
            f"/api/v1/paper-execution/orders/{order_id}/reconciliation",
            auth=AUTH,
        )
        assert reconciliation.status_code == 200
        assert len(reconciliation.json()["attempts"]) == 2
        assert len(reconciliation.json()["fills"]) == 1
        assert len(reconciliation.json()["settlement_links"]) == 1


def test_attempt_pagination_has_no_skip_or_duplicate(configured: _Configured) -> None:
    with TestClient(configured.application) as client:
        order = _create(client, configured).json()["result"]["order"]
        step_path = (
            f"/api/v1/paper-execution/orders/{order['execution_order_id']}/steps"
        )
        for version, key in ((0, "page-step-0"), (1, "page-step-1")):
            response = client.post(
                step_path,
                auth=AUTH,
                headers={"Idempotency-Key": key},
                json={
                    "execution_order_digest": order["execution_order_digest"],
                    "expected_execution_version": version,
                    "actor": "founder",
                },
            )
            assert response.status_code == 201, response.text
        path = f"/api/v1/paper-execution/orders/{order['execution_order_id']}/attempts"
        first = client.get(path, auth=AUTH, params={"limit": 1})
        assert first.status_code == 200
        cursor = first.json()["next_cursor"]
        assert cursor and "=" not in cursor
        second = client.get(path, auth=AUTH, params={"limit": 1, "cursor": cursor})
        identities = [
            first.json()["items"][0]["attempt_id"],
            second.json()["items"][0]["attempt_id"],
        ]
        assert len(set(identities)) == 2
        assert second.json()["next_cursor"] is None
        tampered = cursor[:-1] + ("A" if cursor[-1] != "A" else "B")
        invalid = client.get(path, auth=AUTH, params={"cursor": tampered})
        _assert_error(invalid, 422, "paper_execution_invalid_cursor")


def test_cursor_rejects_padding_wrong_collection_and_context() -> None:
    created_at = datetime(2026, 8, 19, tzinfo=timezone.utc)
    value = encode_paper_execution_list_cursor(
        collection_kind="paper_execution_orders",
        resource_id="peo_" + "a" * 64,
        created_at=created_at,
        query_context={"account_id": None},
    )
    decoded = decode_paper_execution_list_cursor(
        value,
        expected_collection="paper_execution_orders",
        query_context={"account_id": None},
    )
    assert decoded.created_at == created_at
    for candidate, collection, context in (
        (value + "=", "paper_execution_orders", {"account_id": None}),
        (value, "paper_execution_fills", {"account_id": None}),
        (value, "paper_execution_orders", {"account_id": "changed"}),
        ("x" * 2049, "paper_execution_orders", {"account_id": None}),
    ):
        with pytest.raises(PaperExecutionInvalidCursorError):
            decode_paper_execution_list_cursor(
                candidate,
                expected_collection=collection,
                query_context=context,
            )


def test_historical_read_survives_later_progression_but_live_checks_refuse(
    configured: _Configured,
) -> None:
    with TestClient(configured.application) as client:
        order = _create(client, configured).json()["result"]["order"]
        step_path = (
            f"/api/v1/paper-execution/orders/{order['execution_order_id']}/steps"
        )
        first = client.post(
            step_path,
            auth=AUTH,
            headers={"Idempotency-Key": "historical-step"},
            json={
                "execution_order_digest": order["execution_order_digest"],
                "expected_execution_version": 0,
                "actor": "founder",
            },
        )
        assert first.status_code == 201
        configured.account_service.post_cash_movement(
            account_id=configured.account.account_id,
            expected_account_version=configured.account.head_version,
            command_idempotency_key="later-cash",
            actor="founder",
            reason="later legitimate progression",
            requested_amount=PaperMoney.parse("1"),
            movement_type="deposit",
        )
        detail = client.get(
            f"/api/v1/paper-execution/orders/{order['execution_order_id']}",
            auth=AUTH,
        )
        assert detail.status_code == 200
        reconciliation = client.get(
            f"/api/v1/paper-execution/orders/{order['execution_order_id']}/reconciliation",
            auth=AUTH,
        )
        _assert_error(reconciliation, 409, "paper_execution_reconciliation_required")
        next_step = client.post(
            step_path,
            auth=AUTH,
            headers={"Idempotency-Key": "stale-step"},
            json={
                "execution_order_digest": order["execution_order_digest"],
                "expected_execution_version": 1,
                "actor": "founder",
            },
        )
        _assert_error(next_step, 409, "paper_execution_stale_authority")


def test_audit_events_are_bounded_and_replay_never_claims_creation(
    configured: _Configured, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger=PRODUCT_LOGGER_NAME)
    with TestClient(configured.application) as client:
        created = _create(client, configured)
        _create(client, configured)
        order = created.json()["result"]["order"]
        client.post(
            f"/api/v1/paper-execution/orders/{order['execution_order_id']}/steps",
            auth=AUTH,
            headers={"Idempotency-Key": "audit-step"},
            json={
                "execution_order_digest": order["execution_order_digest"],
                "expected_execution_version": 0,
                "actor": "founder",
            },
        )
    records = [
        record
        for record in caplog.records
        if record.name == PRODUCT_LOGGER_NAME
        and str(getattr(record, "event", "")).startswith("paper_execution_")
    ]
    assert {record.event for record in records} >= {
        "paper_execution_order_created",
        "paper_execution_idempotent_replay",
        "paper_execution_step_no_fill",
    }
    created_records = [
        record for record in records if record.event == "paper_execution_order_created"
    ]
    assert len(created_records) == 1
    forbidden = {
        "command_idempotency_key",
        "actor",
        "cash_balance",
        "available_cash",
        "execution_price",
        "posting_amount",
        "request_body",
    }
    assert all(not forbidden.intersection(record.__dict__) for record in records)


def test_openapi_decimal_fields_are_strings_and_requests_are_strict(
    configured: _Configured,
) -> None:
    document = configured.application.openapi()
    schemas = document["components"]["schemas"]
    for name in (
        "PaperExecutionOrderCreateRequest",
        "PaperExecutionOrderStepRequest",
        "PaperExecutionOrderResponse",
        "PaperExecutionAttemptResponse",
        "PaperExecutionFillResponse",
    ):
        assert schemas[name]["additionalProperties"] is False
    assert (
        schemas["PaperExecutionPolicyRequest"]["properties"]["slippage_bps"]["type"]
        == "string"
    )
    assert (
        schemas["PaperExecutionFillResponse"]["properties"]["fill_quantity"]["type"]
        == "string"
    )


def test_unavailable_storage_uses_stable_server_request_id() -> None:
    application = create_app(
        product_database_path="",
        founder_username=AUTH[0],
        founder_password=AUTH[1],
    )
    with TestClient(application) as client:
        response = client.get("/api/v1/paper-execution/orders", auth=AUTH)
    _assert_error(response, 503, "paper_execution_authority_unavailable")


def test_incompatible_schema_is_distinct_from_unavailable_storage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    command.upgrade(
        Config(str(ROOT / "alembic.ini")),
        "0010_strategy_order_risk",
    )
    application = create_app(
        product_database_path=path,
        founder_username=AUTH[0],
        founder_password=AUTH[1],
    )
    with TestClient(application) as client:
        response = client.get("/api/v1/paper-execution/orders", auth=AUTH)
    _assert_error(response, 503, "paper_execution_schema_incompatible")


@pytest.mark.parametrize(
    ("failure", "operation", "status", "code"),
    (
        (
            PaperExecutionNotFoundError("secret upstream"),
            "order_create",
            404,
            "paper_execution_upstream_authority_not_found",
        ),
        (
            PaperExecutionNotFoundError("secret order"),
            "order_detail",
            404,
            "paper_execution_order_not_found",
        ),
        (
            PaperExecutionNotFoundError("secret attempt"),
            "attempt_detail",
            404,
            "paper_execution_attempt_not_found",
        ),
        (
            PaperExecutionNotFoundError("secret fill"),
            "fill_detail",
            404,
            "paper_execution_fill_not_found",
        ),
        (
            PaperExecutionIdempotencyConflictError("secret key"),
            "order_create",
            409,
            "paper_execution_idempotency_conflict",
        ),
        (
            PaperExecutionStaleAuthorityError("secret value"),
            "order_step",
            409,
            "paper_execution_stale_authority",
        ),
        (
            PaperExecutionOperationConflictError("secret state"),
            "order_step",
            409,
            "paper_execution_operation_conflict",
        ),
        (
            PaperExecutionConcurrencyConflictError("secret race"),
            "order_step",
            409,
            "paper_execution_concurrency_conflict",
        ),
        (
            PaperExecutionReconciliationRequiredError("secret balance"),
            "reconciliation",
            409,
            "paper_execution_reconciliation_required",
        ),
        (
            PaperExecutionInvalidPolicyError("secret policy"),
            "order_create",
            422,
            "paper_execution_invalid_policy",
        ),
        (
            PaperExecutionInvalidDecimalError("secret decimal"),
            "order_create",
            422,
            "paper_execution_invalid_decimal",
        ),
        (
            PaperExecutionInvalidCursorError("secret cursor"),
            "order_list",
            422,
            "paper_execution_invalid_cursor",
        ),
        (
            PaperExecutionCorruptAuthorityError("secret SQL table"),
            "order_detail",
            503,
            "paper_execution_authority_unavailable",
        ),
        (
            PaperExecutionStorageBusyError("secret lock"),
            "order_list",
            503,
            "paper_execution_storage_busy",
        ),
        (
            PaperExecutionStorageFailureError("secret path"),
            "fill_list",
            503,
            "paper_execution_storage_failure",
        ),
    ),
)
def test_every_paper_execution_error_mapping_is_stable_and_sanitized(
    failure: Exception,
    operation: str,
    status: int,
    code: str,
) -> None:
    with pytest.raises(PublicApiError) as caught:
        raise_paper_execution_api_error(failure, operation=operation)
    assert caught.value.status_code == status
    assert caught.value.code == code
    assert "secret" not in caught.value.message.lower()


def _database_dump(path: Path) -> tuple[str, ...]:
    with sqlite3.connect(path) as connection:
        return tuple(connection.iterdump())


def test_s215_api_corruption_is_sanitized_and_non_mutating(
    configured: _Configured,
) -> None:
    with TestClient(configured.application) as client:
        order = _create(client, configured, "api-corruption-create").json()["result"][
            "order"
        ]
    with sqlite3.connect(configured.database_path) as connection:
        connection.execute("DROP TRIGGER trg_paper_execution_orders_no_update")
        connection.execute(
            "UPDATE paper_execution_orders SET instrument_id = 'XNYS:SECRET' "
            "WHERE execution_order_id = ?",
            (order["execution_order_id"],),
        )
        connection.execute(
            "CREATE TRIGGER trg_paper_execution_orders_no_update "
            "BEFORE UPDATE ON paper_execution_orders "
            "BEGIN SELECT RAISE(ABORT, 'M34 authority is append-only'); END"
        )
        connection.commit()
    corrupted = _database_dump(configured.database_path)

    with TestClient(configured.application) as client:
        detail = client.get(
            f"/api/v1/paper-execution/orders/{order['execution_order_id']}",
            auth=AUTH,
        )
        _assert_error(detail, 503, "paper_execution_authority_unavailable")
        refused_step = client.post(
            f"/api/v1/paper-execution/orders/{order['execution_order_id']}/steps",
            auth=AUTH,
            headers={"Idempotency-Key": "secret-corruption-step-key"},
            json={
                "execution_order_digest": order["execution_order_digest"],
                "expected_execution_version": 0,
                "actor": "founder",
            },
        )
        _assert_error(refused_step, 503, "paper_execution_authority_unavailable")
    exposed = (detail.text + refused_step.text).lower()
    assert all(
        secret not in exposed
        for secret in (
            "sqlite",
            "instrument_id",
            "xnys:secret",
            "secret-corruption-step-key",
            "paper_execution_orders",
        )
    )
    configured.application.state.product_database_engine.dispose()
    assert _database_dump(configured.database_path) == corrupted


def test_s215_api_storage_busy_is_sanitized_retryable_and_non_mutating(
    configured: _Configured,
) -> None:
    engine = configured.application.state.product_database_engine

    @event.listens_for(engine, "connect")
    def _bounded_busy_timeout(dbapi_connection, _connection_record) -> None:
        dbapi_connection.execute("PRAGMA busy_timeout=100")

    engine.dispose()
    lock = sqlite3.connect(configured.database_path, timeout=0, isolation_level=None)
    try:
        lock.execute("BEGIN IMMEDIATE")
        with TestClient(configured.application) as client:
            refused = _create(client, configured, "secret-busy-create-key")
        _assert_error(refused, 503, "paper_execution_storage_busy")
        assert all(
            secret not in refused.text.lower()
            for secret in (
                "database is locked",
                "sqlite",
                "secret-busy-create-key",
                "begin immediate",
            )
        )
        assert lock.execute(
            "SELECT COUNT(*) FROM paper_execution_orders"
        ).fetchone() == (0,)
        assert lock.execute(
            "SELECT COUNT(*) FROM paper_execution_command_receipts"
        ).fetchone() == (0,)
    finally:
        lock.rollback()
        lock.close()

    with TestClient(configured.application) as client:
        retry = _create(client, configured, "secret-busy-create-key")
    assert retry.status_code == 201, retry.text
    assert retry.json()["replayed"] is False
