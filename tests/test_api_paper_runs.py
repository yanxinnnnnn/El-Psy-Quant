"""Tests for the versioned synchronous paper-run command endpoint."""

from uuid import UUID
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from el_psy_quant.api.app import create_app
from el_psy_quant.api.middleware import REQUEST_ID_HEADER
from el_psy_quant.api.paper_run_schemas import PaperRunCommandResponse
from el_psy_quant.api.schemas import ApiErrorResponse
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV


def _payload() -> dict[str, object]:
    return {
        "run_id": " paper-run-001 ",
        "created_timestamp": "2026-07-13T12:00:00Z",
        "starting_account_state": {
            "timestamp": "2026-07-13T12:00:00Z",
            "starting_cash": 10_000,
            "current_cash": 10_000,
            "positions": {"MSFT": 1, "aapl": 2},
        },
        "ending_account_state": {
            "timestamp": "2026-07-13T12:05:00Z",
            "starting_cash": 10_000,
            "current_cash": 9_000,
            "positions": {"MSFT": 0.5, "aapl": 12},
        },
        "orders": [
            {
                "order_id": "order-002",
                "timestamp": "2026-07-13T12:03:00Z",
                "symbol": "msft",
                "side": "SELL",
                "quantity": 0.5,
                "status": "FILLED",
            },
            {
                "order_id": " order-001 ",
                "timestamp": "2026-07-13T12:01:00Z",
                "symbol": "aapl",
                "side": "BUY",
                "quantity": 10,
                "status": "FILLED",
            },
        ],
        "fills": [
            {
                "timestamp": "2026-07-13T12:04:00Z",
                "symbol": "msft",
                "side": "SELL",
                "quantity": 0.5,
                "price": 200,
            },
            {
                "order_id": " order-001 ",
                "timestamp": "2026-07-13T12:02:00Z",
                "symbol": "aapl",
                "side": "BUY",
                "quantity": 10,
                "price": 100,
            },
        ],
    }


def _assert_request_id(response) -> None:
    header = response.headers[REQUEST_ID_HEADER]
    assert str(UUID(header)) == header
    if response.status_code >= 400:
        error = ApiErrorResponse.model_validate(response.json())
        assert error.request_id == header


def test_success_response_is_exact_normalized_and_schema_valid() -> None:
    response = TestClient(create_app()).post("/api/v1/paper-runs", json=_payload())
    expected = {
        "run_id": "paper-run-001",
        "request_schema_version": 1,
        "artifact": {
            "schema_version": 1,
            "created_timestamp": "2026-07-13T12:00:00+00:00",
            "starting_account_state": {
                "timestamp": "2026-07-13T12:00:00+00:00",
                "starting_cash": 10_000.0,
                "current_cash": 10_000.0,
                "positions": [
                    {"symbol": "AAPL", "quantity": 2.0},
                    {"symbol": "MSFT", "quantity": 1.0},
                ],
            },
            "ending_account_state": {
                "timestamp": "2026-07-13T12:05:00+00:00",
                "starting_cash": 10_000.0,
                "current_cash": 9_000.0,
                "positions": [
                    {"symbol": "AAPL", "quantity": 12.0},
                    {"symbol": "MSFT", "quantity": 0.5},
                ],
            },
            "orders": [
                {
                    "order_id": "order-002",
                    "timestamp": "2026-07-13T12:03:00+00:00",
                    "symbol": "MSFT",
                    "side": "sell",
                    "quantity": 0.5,
                    "status": "filled",
                },
                {
                    "order_id": "order-001",
                    "timestamp": "2026-07-13T12:01:00+00:00",
                    "symbol": "AAPL",
                    "side": "buy",
                    "quantity": 10.0,
                    "status": "filled",
                },
            ],
            "fills": [
                {
                    "timestamp": "2026-07-13T12:04:00+00:00",
                    "symbol": "MSFT",
                    "side": "sell",
                    "quantity": 0.5,
                    "price": 200.0,
                    "order_id": None,
                },
                {
                    "timestamp": "2026-07-13T12:02:00+00:00",
                    "symbol": "AAPL",
                    "side": "buy",
                    "quantity": 10.0,
                    "price": 100.0,
                    "order_id": "order-001",
                },
            ],
            "session_summary": {
                "session_start_timestamp": "2026-07-13T12:00:00+00:00",
                "session_end_timestamp": "2026-07-13T12:05:00+00:00",
                "starting_cash": 10_000.0,
                "ending_cash": 9_000.0,
                "cash_change": -1_000.0,
                "starting_positions": [
                    {"symbol": "AAPL", "quantity": 2.0},
                    {"symbol": "MSFT", "quantity": 1.0},
                ],
                "ending_positions": [
                    {"symbol": "AAPL", "quantity": 12.0},
                    {"symbol": "MSFT", "quantity": 0.5},
                ],
                "position_changes": [
                    {
                        "symbol": "AAPL",
                        "starting_quantity": 2.0,
                        "ending_quantity": 12.0,
                        "quantity_change": 10.0,
                    },
                    {
                        "symbol": "MSFT",
                        "starting_quantity": 1.0,
                        "ending_quantity": 0.5,
                        "quantity_change": -0.5,
                    },
                ],
                "order_count": 2,
                "fill_count": 2,
            },
        },
    }

    assert response.status_code == 200
    assert response.json() == expected
    assert PaperRunCommandResponse.model_validate(response.json()).model_dump() == expected
    _assert_request_id(response)


def test_repeated_run_id_is_independent_and_not_a_durable_job_id() -> None:
    client = TestClient(create_app())

    first = client.post("/api/v1/paper-runs", json=_payload())
    second = client.post("/api/v1/paper-runs", json=_payload())

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert first.headers[REQUEST_ID_HEADER] != second.headers[REQUEST_ID_HEADER]


def test_synchronous_endpoint_remains_database_free(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))

    response = TestClient(create_app()).post("/api/v1/paper-runs", json=_payload())

    assert response.status_code == 200
    assert not database_path.exists()


def test_domain_invalid_request_has_sanitized_stable_422() -> None:
    payload = _payload()
    payload["created_timestamp"] = "private-invalid-timestamp"
    response = TestClient(create_app()).post("/api/v1/paper-runs", json=payload)

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "paper_run_invalid",
        "message": "Paper run request is invalid",
    }
    assert "private-invalid-timestamp" not in response.text
    assert "DateParseError" not in response.text
    _assert_request_id(response)


def _malformed_payloads() -> tuple[dict[str, object], ...]:
    missing = _payload()
    missing.pop("run_id")
    wrong_orders = _payload()
    wrong_orders["orders"] = {}
    wrong_fills = _payload()
    wrong_fills["fills"] = {}
    wrong_positions = _payload()
    wrong_positions["starting_account_state"] = {
        **wrong_positions["starting_account_state"],  # type: ignore[dict-item]
        "positions": [],
    }
    unknown_top = _payload()
    unknown_top["run_dir"] = "C:\\private\\output"
    unknown_nested = _payload()
    unknown_nested["starting_account_state"] = {
        **unknown_nested["starting_account_state"],  # type: ignore[dict-item]
        "secret": "private-value",
    }
    boolean_cash = _payload()
    boolean_cash["starting_account_state"] = {
        **boolean_cash["starting_account_state"],  # type: ignore[dict-item]
        "current_cash": True,
    }
    boolean_quantity = _payload()
    boolean_quantity["orders"] = [
        {**boolean_quantity["orders"][0], "quantity": False}  # type: ignore[index]
    ]
    return (
        missing,
        wrong_orders,
        wrong_fills,
        wrong_positions,
        unknown_top,
        unknown_nested,
        boolean_cash,
        boolean_quantity,
    )


@pytest.mark.parametrize("payload", _malformed_payloads())
def test_malformed_shapes_unknown_fields_and_booleans_use_validation_error(
    payload: dict[str, object],
) -> None:
    response = TestClient(create_app()).post("/api/v1/paper-runs", json=payload)

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "request_validation_error",
        "message": "Request Validation Error",
    }
    assert "private-value" not in response.text
    assert "private\\output" not in response.text
    _assert_request_id(response)


def test_caller_request_id_is_ignored_on_success_and_error() -> None:
    client = TestClient(create_app())
    success = client.post(
        "/api/v1/paper-runs",
        json=_payload(),
        headers={REQUEST_ID_HEADER: "caller-owned"},
    )
    invalid = _payload()
    invalid["created_timestamp"] = "invalid"
    error = client.post(
        "/api/v1/paper-runs",
        json=invalid,
        headers={REQUEST_ID_HEADER: "caller-owned"},
    )

    assert success.headers[REQUEST_ID_HEADER] != "caller-owned"
    assert error.headers[REQUEST_ID_HEADER] != "caller-owned"
    _assert_request_id(success)
    _assert_request_id(error)


def test_get_is_method_not_allowed_and_preserves_allow_and_request_id() -> None:
    response = TestClient(create_app()).get("/api/v1/paper-runs")

    assert response.status_code == 405
    assert response.json()["error"] == {
        "code": "method_not_allowed",
        "message": "Method Not Allowed",
    }
    assert "POST" in response.headers["allow"].split(", ")
    _assert_request_id(response)


def test_only_one_versioned_paper_run_endpoint_exists() -> None:
    paths = set(create_app().openapi()["paths"])
    paper_paths = {path for path in paths if "paper-runs" in path}

    assert paper_paths == {"/api/v1/paper-runs"}
    assert "/paper-runs" not in paths
