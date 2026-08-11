"""Focused Sprint 203 API, cursor, error, audit, and authority tests."""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from el_psy_quant.api.app import create_app
from el_psy_quant.api.dependencies import (
    get_server_utc_timestamp,
    get_strategy_order_application_service,
)
from el_psy_quant.api.middleware import REQUEST_ID_HEADER
from el_psy_quant.api.observability import PRODUCT_LOGGER_NAME
from el_psy_quant.api.strategy_order_errors import (
    StrategyOrderInvalidCursorError,
)
from el_psy_quant.api.strategy_order_pagination import (
    decode_strategy_order_list_cursor,
    encode_strategy_order_list_cursor,
)
from el_psy_quant.application import (
    PaperAccountApplicationService,
    StrategyOrderApplicationService,
    StrategyOrderReconciliationRequiredError,
    StrategyOrderStorageBusyError,
    StrategyOrderStorageFailureError,
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
    create_market_data_replay_record,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUTH = ("strategy-founder", "strategy-secret")
CREATED = datetime(2026, 8, 6, 1, tzinfo=timezone.utc)
AUDIT_TIME = CREATED + timedelta(hours=10)
INSTRUMENT = "XNYS:AAPL"
ERROR_MESSAGES = {
    "order_intent_not_found": "Order Intent was not found",
    "pre_trade_risk_decision_not_found": (
        "Pre-Trade Risk Decision was not found"
    ),
    "request_validation_error": "Request Validation Error",
    "strategy_order_authority_unavailable": (
        "Strategy-to-risk authority is unavailable"
    ),
    "strategy_order_idempotency_conflict": (
        "Strategy-to-risk idempotency key conflicts"
    ),
    "strategy_order_invalid_cursor": "Strategy-to-risk cursor is invalid",
    "strategy_order_invalid_decimal": (
        "Strategy-to-risk decimal value is invalid"
    ),
    "strategy_order_invalid_risk_policy": (
        "Pre-trade risk policy is invalid"
    ),
    "strategy_order_invalid_runtime_configuration": (
        "Strategy runtime configuration is invalid"
    ),
    "strategy_order_reconciliation_required": (
        "Paper Account reconciliation is required"
    ),
    "strategy_order_schema_incompatible": (
        "Strategy-to-risk schema is incompatible"
    ),
    "strategy_order_stale_authority": (
        "Strategy-to-risk authority is stale"
    ),
    "strategy_order_storage_busy": (
        "Strategy-to-risk storage is temporarily unavailable"
    ),
    "strategy_order_storage_failure": "Strategy-to-risk storage failed",
    "strategy_signal_not_found": "Strategy Signal was not found",
}


@dataclass(frozen=True)
class _Configured:
    application: object
    account: object
    account_service: PaperAccountApplicationService
    replay: MarketDataReplayEngine


@pytest.fixture(autouse=True)
def _enable_product_logger() -> None:
    logging.getLogger(PRODUCT_LOGGER_NAME).disabled = False


@pytest.fixture
def configured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> _Configured:
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    command.upgrade(Config(str(PROJECT_ROOT / "alembic.ini")), "head")
    application = create_app(
        product_database_path=path,
        founder_username=AUTH[0],
        founder_password=AUTH[1],
    )
    application.dependency_overrides[get_server_utc_timestamp] = (
        lambda: AUDIT_TIME
    )
    factory = application.state.product_session_factory
    counters: dict[str, int] = {}

    def identifier(kind: str) -> str:
        counters[kind] = counters.get(kind, 0) + 1
        return f"{kind}-s203-{counters[kind]}"

    account_service = PaperAccountApplicationService(
        session_factory=factory,
        clock=lambda: CREATED,
        id_factory=identifier,
    )
    account = account_service.create_account(
        display_name="Sprint 203 account",
        base_currency="USD",
        initial_cash=PaperMoney.parse("2000"),
        creation_idempotency_key="create-s203-account",
        actor="founder",
    ).account
    calendar = create_trading_calendar(
        id="calendar-s203",
        market="XNYS",
        timezone="UTC",
        calendar_version=1,
        created_at=CREATED,
    )
    trading_session = create_trading_session(
        id="session-s203",
        calendar_id=calendar.id,
        trading_date=date(2026, 8, 6),
        open_time=CREATED,
        close_time=CREATED + timedelta(hours=8),
        session_type="regular",
    )
    events = [
        create_market_data_event(
            event_id=f"event-s203-{index}",
            instrument_id=INSTRUMENT,
            event_time=CREATED + timedelta(minutes=index),
            event_type="trade",
            payload={"price": price},
            source="fixture:s203",
        )
        for index, price in enumerate((3, 2, 1, 4), start=1)
    ]
    replay = MarketDataReplayEngine(replay_id="replay-s203", events=events)
    replay.start()
    tuple(replay.iter_remaining())
    with factory.begin() as session:
        repository = SqlAlchemyMarketTimeRepository(session=session)
        repository.add_calendar(calendar=calendar)
        repository.add_session(session=trading_session)
        repository.add_replay(
            replay=create_market_data_replay_record(
                session=replay.session,
                events=replay.events,
            )
        )
    logging.getLogger(PRODUCT_LOGGER_NAME).disabled = False
    return _Configured(application, account, account_service, replay)


def _market(configured: _Configured) -> dict[str, object]:
    return {
        "calendar_id": "calendar-s203",
        "expected_calendar_version": 1,
        "trading_session_id": "session-s203",
        "replay_id": "replay-s203",
        "expected_event_stream_digest": (
            configured.replay.cursor.event_stream_digest
        ),
        "expected_cursor_position": 4,
        "expected_signal_event_id": "event-s203-4",
        "expected_signal_time_utc": (
            configured.replay.events[3].event_time.isoformat()
        ),
        "instrument_id": INSTRUMENT,
    }


def _signal_payload(
    configured: _Configured, *, target: str = "10"
) -> dict[str, object]:
    return {
        "runtime": {
            "strategy_name": "moving_average_crossover",
            "strategy_version": "v1",
            "adapter_version": "v1",
            "runtime_sizing_semantics": "target_position_quantity",
            "fast_window": 2,
            "slow_window": 3,
            "target_position_quantity": target,
        },
        "market": _market(configured),
        "actor": "founder",
    }


def _post_signal(
    client: TestClient,
    configured: _Configured,
    *,
    key: str = "signal-s203",
    target: str = "10",
):
    return client.post(
        "/api/v1/strategy-signals/evaluate",
        auth=AUTH,
        headers={"Idempotency-Key": key},
        json=_signal_payload(configured, target=target),
    )


def _account(account: object) -> dict[str, object]:
    return {
        "account_id": account.account_id,
        "expected_account_head_version": account.head_version,
        "expected_account_head_event_id": account.head_event_id,
        "expected_account_head_chain_digest": account.head_chain_digest,
    }


def _risk_account(account: object) -> dict[str, object]:
    return {
        "expected_account_head_version": account.head_version,
        "expected_account_head_event_id": account.head_event_id,
        "expected_account_head_chain_digest": account.head_chain_digest,
    }


def _post_intent(
    client: TestClient,
    *,
    signal_id: str,
    account: object,
    key: str = "intent-s203",
):
    return client.post(
        "/api/v1/order-intents",
        auth=AUTH,
        headers={"Idempotency-Key": key},
        json={
            "signal_id": signal_id,
            "account": _account(account),
            "intent_policy_version": "target_position_quantity_delta_v1",
            "actor": "founder",
        },
    )


def _risk_payload(
    configured: _Configured,
    *,
    intent_id: str,
    account: object,
    maximum_notional: str | None = None,
) -> dict[str, object]:
    market = _market(configured)
    return {
        "intent_id": intent_id,
        "policy": {
            "policy_id": "long_only_cash_risk_v1",
            "reference_price_policy_id": "latest_trade_price_v1",
            "maximum_order_quantity": None,
            "maximum_order_notional": maximum_notional,
        },
        "account": _risk_account(account),
        "market": {
            "expected_calendar_id": market["calendar_id"],
            "expected_calendar_version": market["expected_calendar_version"],
            "expected_trading_session_id": market["trading_session_id"],
            "expected_replay_id": market["replay_id"],
            "expected_event_stream_digest": market[
                "expected_event_stream_digest"
            ],
            "expected_cursor_position": market["expected_cursor_position"],
            "expected_current_event_id": market["expected_signal_event_id"],
            "expected_current_event_time_utc": market[
                "expected_signal_time_utc"
            ],
            "expected_instrument_id": market["instrument_id"],
        },
        "actor": "founder",
    }


def _post_risk(
    client: TestClient,
    configured: _Configured,
    *,
    intent_id: str,
    account: object,
    key: str = "risk-s203",
    maximum_notional: str | None = None,
):
    return client.post(
        "/api/v1/pre-trade-risk-decisions",
        auth=AUTH,
        headers={"Idempotency-Key": key},
        json=_risk_payload(
            configured,
            intent_id=intent_id,
            account=account,
            maximum_notional=maximum_notional,
        ),
    )


def _assert_error(response, status: int, code: str) -> None:
    assert response.status_code == status, response.text
    body = response.json()
    assert body["error"]["code"] == code
    assert body["error"]["message"] == ERROR_MESSAGES[code]
    request_id = response.headers[REQUEST_ID_HEADER]
    assert str(UUID(request_id)) == request_id == body["request_id"]
    assert "product.sqlite3" not in response.text
    assert "SELECT " not in response.text


def test_exact_route_inventory_authentication_and_operation_ids(
    configured: _Configured,
) -> None:
    document = configured.application.openapi()
    operations = {
        (method.upper(), path, operation["operationId"])
        for path, methods in document["paths"].items()
        if path.startswith(
            (
                "/api/v1/strategy-signals",
                "/api/v1/order-intents",
                "/api/v1/pre-trade-risk-decisions",
            )
        )
        for method, operation in methods.items()
    }
    assert operations == {
        (
            "POST",
            "/api/v1/strategy-signals/evaluate",
            "evaluate_strategy_signal_v1",
        ),
        ("GET", "/api/v1/strategy-signals", "list_strategy_signals_v1"),
        (
            "GET",
            "/api/v1/strategy-signals/{signal_id}",
            "get_strategy_signal_v1",
        ),
        ("POST", "/api/v1/order-intents", "create_order_intent_v1"),
        ("GET", "/api/v1/order-intents", "list_order_intents_v1"),
        (
            "GET",
            "/api/v1/order-intents/{intent_id}",
            "get_order_intent_v1",
        ),
        (
            "POST",
            "/api/v1/pre-trade-risk-decisions",
            "create_pre_trade_risk_decision_v1",
        ),
        (
            "GET",
            "/api/v1/pre-trade-risk-decisions",
            "list_pre_trade_risk_decisions_v1",
        ),
        (
            "GET",
            "/api/v1/pre-trade-risk-decisions/{decision_id}",
            "get_pre_trade_risk_decision_v1",
        ),
    }
    with TestClient(configured.application) as client:
        response = client.get("/api/v1/strategy-signals")
    assert response.status_code == 401


def test_signal_create_replay_convergence_reads_filters_and_correlation(
    configured: _Configured,
) -> None:
    with TestClient(configured.application) as client:
        first = client.post(
            "/api/v1/strategy-signals/evaluate",
            auth=AUTH,
            headers={
                "Idempotency-Key": "signal-s203",
                "X-Request-ID": "caller-owned",
            },
            json=_signal_payload(configured),
        )
        retry = _post_signal(client, configured)
        alternate = _post_signal(
            client, configured, key="signal-s203-alternate"
        )
        body = first.json()
        signal = body["signal"]
        detail = client.get(
            f"/api/v1/strategy-signals/{signal['signal_id']}", auth=AUTH
        )
        listed = client.get(
            "/api/v1/strategy-signals",
            auth=AUTH,
            params={
                "strategy_name": "moving_average_crossover",
                "instrument_id": INSTRUMENT,
            },
        )
    assert first.status_code == 201
    assert retry.status_code == 200
    assert alternate.status_code == 201
    assert body["replayed"] is False
    assert retry.json()["replayed"] is True
    assert alternate.json()["replayed"] is False
    assert retry.json()["signal"]["signal_id"] == signal["signal_id"]
    assert alternate.json()["signal"]["signal_id"] == signal["signal_id"]
    request_id = first.headers[REQUEST_ID_HEADER]
    assert request_id != "caller-owned"
    assert str(UUID(request_id)) == request_id == body["request_id"]
    assert signal["created_at"] == "2026-08-06T11:00:00Z"
    assert signal["target_position_quantity"] == "10"
    assert "payload" not in first.text
    assert "idempotency" not in first.text
    assert detail.status_code == 200
    assert detail.json() == signal
    assert [item["signal_id"] for item in listed.json()["items"]] == [
        signal["signal_id"]
    ]


def test_intent_buy_no_action_reads_and_filters(
    configured: _Configured,
) -> None:
    with TestClient(configured.application) as client:
        signal = _post_signal(client, configured).json()["signal"]
        created = _post_intent(
            client,
            signal_id=signal["signal_id"],
            account=configured.account,
        )
        retry = _post_intent(
            client,
            signal_id=signal["signal_id"],
            account=configured.account,
        )
        intent = created.json()["result"]
        detail = client.get(
            f"/api/v1/order-intents/{intent['intent_id']}", auth=AUTH
        )
        listed = client.get(
            "/api/v1/order-intents",
            auth=AUTH,
            params={
                "signal_id": signal["signal_id"],
                "account_id": configured.account.account_id,
                "instrument_id": INSTRUMENT,
                "side": "buy",
            },
        )
        positioned = configured.account_service.post_position_adjustment(
            account_id=configured.account.account_id,
            expected_account_version=configured.account.head_version,
            command_idempotency_key="position-s203",
            actor="founder",
            reason="no-action fixture",
            symbol=INSTRUMENT,
            adjustment_category="opening_balance",
            signed_quantity_delta=PaperQuantity.parse("10"),
            signed_cost_basis_delta=PaperMoney.parse("0"),
        ).account
        no_action = _post_intent(
            client,
            signal_id=signal["signal_id"],
            account=positioned,
            key="intent-no-action-s203",
        )
        after = client.get("/api/v1/order-intents", auth=AUTH)
    assert created.status_code == 201
    assert retry.status_code == 200
    assert created.json()["result_kind"] == "order_intent"
    assert intent["side"] == "buy"
    assert intent["requested_quantity"] == "10"
    assert "origin_command_idempotency_key" not in created.text
    assert detail.json() == intent
    assert [item["intent_id"] for item in listed.json()["items"]] == [
        intent["intent_id"]
    ]
    assert no_action.status_code == 201
    assert no_action.json()["result_kind"] == "order_intent_no_action"
    assert (
        no_action.json()["result"]["reason_code"]
        == "target_already_satisfied"
    )
    assert len(after.json()["items"]) == 1


def test_risk_allow_reject_replay_reads_filters_and_exact_rules(
    configured: _Configured,
) -> None:
    with TestClient(configured.application) as client:
        signal = _post_signal(client, configured).json()["signal"]
        intent = _post_intent(
            client,
            signal_id=signal["signal_id"],
            account=configured.account,
        ).json()["result"]
        allowed = _post_risk(
            client,
            configured,
            intent_id=intent["intent_id"],
            account=configured.account,
        )
        replayed = _post_risk(
            client,
            configured,
            intent_id=intent["intent_id"],
            account=configured.account,
        )
        rejected = _post_risk(
            client,
            configured,
            intent_id=intent["intent_id"],
            account=configured.account,
            key="risk-reject-s203",
            maximum_notional="1",
        )
        assert allowed.status_code == 201, allowed.text
        assert replayed.status_code == 200, replayed.text
        assert rejected.status_code == 201, rejected.text
        decision = allowed.json()["decision"]
        detail = client.get(
            "/api/v1/pre-trade-risk-decisions/"
            + decision["decision_id"],
            auth=AUTH,
        )
        listed = client.get(
            "/api/v1/pre-trade-risk-decisions",
            auth=AUTH,
            params={
                "intent_id": intent["intent_id"],
                "account_id": configured.account.account_id,
                "outcome": "allow",
            },
        )
    assert allowed.status_code == 201
    assert replayed.status_code == 200
    assert rejected.status_code == 201
    assert decision["outcome"] == "allow"
    assert decision["reason_codes"] == []
    assert [
        rule["rule_code"]
        for rule in decision["input_snapshot"]["rule_evidence"]
    ] == [
        "insufficient_position_quantity",
        "maximum_order_quantity_exceeded",
        "maximum_order_notional_exceeded",
        "insufficient_available_cash",
    ]
    assert rejected.json()["decision"]["outcome"] == "reject"
    assert rejected.json()["decision"]["reason_codes"] == [
        "maximum_order_notional_exceeded"
    ]
    assert "origin_command_idempotency_key" not in allowed.text
    assert detail.json() == decision
    assert [item["decision_id"] for item in listed.json()["items"]] == [
        decision["decision_id"]
    ]


def test_stable_validation_stale_idempotency_and_not_found_errors(
    configured: _Configured,
) -> None:
    with TestClient(configured.application) as client:
        invalid_decimal = _post_signal(client, configured, target="1.0")
        invalid_runtime_payload = _signal_payload(configured)
        invalid_runtime_payload["runtime"]["fast_window"] = 3
        invalid_runtime_payload["runtime"]["slow_window"] = 2
        invalid_runtime = client.post(
            "/api/v1/strategy-signals/evaluate",
            auth=AUTH,
            headers={"Idempotency-Key": "invalid-runtime"},
            json=invalid_runtime_payload,
        )
        stale_payload = _signal_payload(configured)
        stale_payload["market"]["expected_cursor_position"] = 3
        stale = client.post(
            "/api/v1/strategy-signals/evaluate",
            auth=AUTH,
            headers={"Idempotency-Key": "stale-signal"},
            json=stale_payload,
        )
        created = _post_signal(client, configured, key="conflict-signal")
        conflict = _post_signal(
            client,
            configured,
            key="conflict-signal",
            target="11",
        )
        missing_signal = _post_intent(
            client,
            signal_id="sig_" + "f" * 64,
            account=configured.account,
            key="missing-signal",
        )
        missing_intent = client.get(
            "/api/v1/order-intents/oi_" + "e" * 64,
            auth=AUTH,
        )
        missing_decision = client.get(
            "/api/v1/pre-trade-risk-decisions/risk_decision_"
            + "d" * 64,
            auth=AUTH,
        )
        unknown = _signal_payload(configured)
        unknown["signal_id"] = "caller-authored"
        rejected_unknown = client.post(
            "/api/v1/strategy-signals/evaluate",
            auth=AUTH,
            headers={"Idempotency-Key": "unknown-field"},
            json=unknown,
        )
    _assert_error(
        invalid_decimal, 422, "strategy_order_invalid_decimal"
    )
    _assert_error(
        invalid_runtime,
        422,
        "strategy_order_invalid_runtime_configuration",
    )
    _assert_error(stale, 409, "strategy_order_stale_authority")
    assert created.status_code == 201
    _assert_error(conflict, 409, "strategy_order_idempotency_conflict")
    _assert_error(missing_signal, 404, "strategy_signal_not_found")
    _assert_error(missing_intent, 404, "order_intent_not_found")
    _assert_error(
        missing_decision, 404, "pre_trade_risk_decision_not_found"
    )
    _assert_error(rejected_unknown, 422, "request_validation_error")


def test_risk_request_rejects_account_identity_and_invalid_policy(
    configured: _Configured,
) -> None:
    intent_id = "oi_" + "a" * 64
    payload = _risk_payload(
        configured,
        intent_id=intent_id,
        account=configured.account,
    )
    payload["account"]["account_id"] = configured.account.account_id
    with TestClient(configured.application) as client:
        caller_account_id = client.post(
            "/api/v1/pre-trade-risk-decisions",
            auth=AUTH,
            headers={"Idempotency-Key": "risk-account-id"},
            json=payload,
        )
        invalid_policy = _post_risk(
            client,
            configured,
            intent_id=intent_id,
            account=configured.account,
            key="risk-invalid-policy",
            maximum_notional="0",
        )
    _assert_error(caller_account_id, 422, "request_validation_error")
    _assert_error(
        invalid_policy, 422, "strategy_order_invalid_risk_policy"
    )


def test_missing_primary_resources_are_distinct_from_missing_upstream_authority(
    configured: _Configured,
) -> None:
    with TestClient(configured.application) as client:
        signal = _post_signal(client, configured).json()["signal"]
        missing_account_payload = {
            "signal_id": signal["signal_id"],
            "account": {
                **_account(configured.account),
                "account_id": "missing-account",
            },
            "intent_policy_version": "target_position_quantity_delta_v1",
            "actor": "founder",
        }
        missing_account = client.post(
            "/api/v1/order-intents",
            auth=AUTH,
            headers={"Idempotency-Key": "intent-missing-account"},
            json=missing_account_payload,
        )
        missing_intent = _post_risk(
            client,
            configured,
            intent_id="oi_" + "b" * 64,
            account=configured.account,
            key="risk-missing-intent",
        )
        intent = _post_intent(
            client,
            signal_id=signal["signal_id"],
            account=configured.account,
            key="intent-for-missing-market",
        ).json()["result"]
        missing_market_payload = _risk_payload(
            configured,
            intent_id=intent["intent_id"],
            account=configured.account,
        )
        missing_market_payload["market"]["expected_calendar_id"] = (
            "missing-calendar"
        )
        missing_market = client.post(
            "/api/v1/pre-trade-risk-decisions",
            auth=AUTH,
            headers={"Idempotency-Key": "risk-missing-market"},
            json=missing_market_payload,
        )
    _assert_error(
        missing_account, 503, "strategy_order_authority_unavailable"
    )
    _assert_error(missing_intent, 404, "order_intent_not_found")
    _assert_error(
        missing_market, 503, "strategy_order_authority_unavailable"
    )


def test_malformed_list_resource_filters_use_request_validation_error(
    configured: _Configured,
) -> None:
    with TestClient(configured.application) as client:
        malformed_signal = client.get(
            "/api/v1/order-intents",
            auth=AUTH,
            params={"signal_id": "signal-not-an-id"},
        )
        overlong_signal = client.get(
            "/api/v1/order-intents",
            auth=AUTH,
            params={"signal_id": "sig_" + "a" * 65},
        )
        malformed_intent = client.get(
            "/api/v1/pre-trade-risk-decisions",
            auth=AUTH,
            params={"intent_id": "intent-not-an-id"},
        )
        overlong_intent = client.get(
            "/api/v1/pre-trade-risk-decisions",
            auth=AUTH,
            params={"intent_id": "oi_" + "a" * 65},
        )
    for response in (
        malformed_signal,
        overlong_signal,
        malformed_intent,
        overlong_intent,
    ):
        _assert_error(response, 422, "request_validation_error")


def test_reconciliation_busy_and_storage_failure_mappings(
    configured: _Configured,
) -> None:
    class _ReconciliationService:
        def derive_and_store_order_intent(self, **kwargs):
            del kwargs
            raise StrategyOrderReconciliationRequiredError()

    class _ListFailureService:
        def __init__(self, failure: Exception) -> None:
            self.failure = failure

        def list_strategy_signals(self, **kwargs):
            del kwargs
            raise self.failure

    configured.application.dependency_overrides[
        get_strategy_order_application_service
    ] = lambda: _ReconciliationService()
    with TestClient(configured.application) as client:
        reconciliation = _post_intent(
            client,
            signal_id="sig_" + "c" * 64,
            account=configured.account,
            key="reconciliation-required",
        )
        configured.application.dependency_overrides[
            get_strategy_order_application_service
        ] = lambda: _ListFailureService(StrategyOrderStorageBusyError())
        busy = client.get("/api/v1/strategy-signals", auth=AUTH)
        configured.application.dependency_overrides[
            get_strategy_order_application_service
        ] = lambda: _ListFailureService(StrategyOrderStorageFailureError())
        failure = client.get("/api/v1/strategy-signals", auth=AUTH)
    _assert_error(
        reconciliation, 409, "strategy_order_reconciliation_required"
    )
    _assert_error(busy, 503, "strategy_order_storage_busy")
    _assert_error(failure, 503, "strategy_order_storage_failure")


def test_cursor_canonical_round_trip_tampering_cross_type_and_duplicates() -> None:
    signal_id = "sig_" + "a" * 64
    cursor = encode_strategy_order_list_cursor(
        collection_kind="strategy_signals",
        created_at=AUDIT_TIME,
        resource_id=signal_id,
    )
    decoded = decode_strategy_order_list_cursor(
        cursor, expected_collection="strategy_signals"
    )
    assert decoded.created_at == AUDIT_TIME
    assert decoded.resource_id == signal_id
    with pytest.raises(StrategyOrderInvalidCursorError):
        decode_strategy_order_list_cursor(
            cursor, expected_collection="order_intents"
        )
    with pytest.raises(StrategyOrderInvalidCursorError):
        decode_strategy_order_list_cursor(
            cursor[:-1] + ("A" if cursor[-1] != "A" else "B"),
            expected_collection="strategy_signals",
        )
    raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
    envelope = json.loads(raw)
    duplicate = raw.decode("ascii").replace(
        '"schema_version":1',
        '"schema_version":1,"schema_version":1',
    )
    duplicate_cursor = base64.urlsafe_b64encode(
        duplicate.encode("ascii")
    ).decode("ascii").rstrip("=")
    with pytest.raises(StrategyOrderInvalidCursorError):
        decode_strategy_order_list_cursor(
            duplicate_cursor, expected_collection="strategy_signals"
        )
    noncanonical = base64.urlsafe_b64encode(
        json.dumps(envelope).encode("ascii")
    ).decode("ascii").rstrip("=")
    with pytest.raises(StrategyOrderInvalidCursorError):
        decode_strategy_order_list_cursor(
            noncanonical, expected_collection="strategy_signals"
        )
    with pytest.raises(StrategyOrderInvalidCursorError):
        decode_strategy_order_list_cursor(
            "a" * 2049, expected_collection="strategy_signals"
        )


def test_api_keyset_pages_have_no_duplicates_or_omissions(
    configured: _Configured,
) -> None:
    with TestClient(configured.application) as client:
        created = [
            _post_signal(
                client,
                configured,
                key=f"signal-page-{target}",
                target=str(target),
            ).json()["signal"]["signal_id"]
            for target in (10, 11, 12)
        ]
        observed: list[str] = []
        cursor = None
        while True:
            response = client.get(
                "/api/v1/strategy-signals",
                auth=AUTH,
                params={
                    "limit": 1,
                    **({} if cursor is None else {"cursor": cursor}),
                },
            )
            assert response.status_code == 200, response.text
            page = response.json()
            observed.extend(item["signal_id"] for item in page["items"])
            cursor = page["next_cursor"]
            if cursor is None:
                break
        cross_collection = client.get(
            "/api/v1/order-intents",
            auth=AUTH,
            params={
                "cursor": encode_strategy_order_list_cursor(
                    collection_kind="strategy_signals",
                    created_at=AUDIT_TIME,
                    resource_id=created[0],
                )
            },
        )
    assert observed == sorted(created)
    assert len(observed) == len(set(observed)) == 3
    _assert_error(
        cross_collection, 422, "strategy_order_invalid_cursor"
    )


def test_commands_do_not_mutate_m31_or_m32_authority(
    configured: _Configured,
) -> None:
    factory = configured.application.state.product_session_factory

    def frozen_counts() -> tuple[int, ...]:
        with factory() as session:
            return tuple(
                session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
                for table in (
                    "paper_accounts",
                    "paper_account_events",
                    "paper_cash_ledger_entries",
                    "paper_position_ledger_entries",
                    "trading_calendars",
                    "trading_sessions",
                    "market_data_events",
                    "market_data_replays",
                )
            )

    before = frozen_counts()
    with TestClient(configured.application) as client:
        signal = _post_signal(client, configured).json()["signal"]
        intent = _post_intent(
            client,
            signal_id=signal["signal_id"],
            account=configured.account,
        ).json()["result"]
        risk = _post_risk(
            client,
            configured,
            intent_id=intent["intent_id"],
            account=configured.account,
        )
        assert risk.status_code == 201, risk.text
    assert frozen_counts() == before


def test_one_corrupt_row_fails_complete_list_and_detail_reads(
    configured: _Configured,
) -> None:
    factory = configured.application.state.product_session_factory
    configured.application.dependency_overrides[
        get_strategy_order_application_service
    ] = lambda: StrategyOrderApplicationService(session_factory=factory)
    with TestClient(configured.application) as client:
        signal = _post_signal(client, configured).json()["signal"]
        with factory.begin() as session:
            session.execute(
                text("DROP TRIGGER trg_strategy_signals_no_update")
            )
            session.execute(
                text(
                    "UPDATE strategy_signals "
                    "SET instrument_id = 'XNAS:MSFT' "
                    "WHERE signal_id = :signal_id"
                ),
                {"signal_id": signal["signal_id"]},
            )
        listed = client.get("/api/v1/strategy-signals", auth=AUTH)
        detail = client.get(
            f"/api/v1/strategy-signals/{signal['signal_id']}", auth=AUTH
        )
    _assert_error(
        listed, 503, "strategy_order_authority_unavailable"
    )
    _assert_error(
        detail, 503, "strategy_order_authority_unavailable"
    )


def test_command_audit_events_are_bounded_and_non_leaking(
    configured: _Configured,
) -> None:
    logger = logging.getLogger(PRODUCT_LOGGER_NAME)
    records: list[logging.LogRecord] = []

    class _Handler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = _Handler()
    logger.addHandler(handler)
    try:
        with TestClient(configured.application) as client:
            signal = _post_signal(client, configured).json()["signal"]
            intent = _post_intent(
                client,
                signal_id=signal["signal_id"],
                account=configured.account,
            ).json()["result"]
            risk = _post_risk(
                client,
                configured,
                intent_id=intent["intent_id"],
                account=configured.account,
            )
            assert risk.status_code == 201, risk.text
    finally:
        logger.removeHandler(handler)
    events = {getattr(record, "event", None): record for record in records}
    assert {
        "strategy_signal_evaluation_completed",
        "order_intent_derivation_completed",
        "pre_trade_risk_evaluation_completed",
    }.issubset(events)
    rendered = "\n".join(record.getMessage() for record in records)
    for forbidden in (
        "signal-s203",
        "intent-s203",
        "risk-s203",
        "actor=",
        "price=",
        "cash=",
        "quantity=",
        "notional=",
        "SELECT ",
        "product.sqlite3",
    ):
        assert forbidden not in rendered


def test_unavailable_storage_uses_stable_server_request_id() -> None:
    application = create_app(
        product_database_path="",
        founder_username=AUTH[0],
        founder_password=AUTH[1],
    )
    with TestClient(application) as client:
        response = client.get("/api/v1/strategy-signals", auth=AUTH)
    _assert_error(
        response, 503, "strategy_order_authority_unavailable"
    )


def test_incompatible_schema_is_distinct_from_unavailable_storage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    command.upgrade(
        Config(str(PROJECT_ROOT / "alembic.ini")),
        "0009_market_time_runtime",
    )
    application = create_app(
        product_database_path=path,
        founder_username=AUTH[0],
        founder_password=AUTH[1],
    )
    with TestClient(application) as client:
        response = client.get("/api/v1/strategy-signals", auth=AUTH)
    _assert_error(response, 503, "strategy_order_schema_incompatible")
