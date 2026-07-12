"""Tests for versioned built-in strategy read endpoints."""

from urllib.parse import quote
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from el_psy_quant.api.app import create_app
from el_psy_quant.api.middleware import REQUEST_ID_HEADER
from el_psy_quant.api.schemas import (
    ApiErrorResponse,
    StrategyDetailResponse,
    StrategyListResponse,
)

STRATEGY_NAME = "moving_average_crossover"
DESCRIPTION = (
    "Produces research results from fast and slow moving-average crossover signals."
)


def _assert_uuid(value: str) -> None:
    assert str(UUID(value)) == value


def test_strategy_list_endpoint_is_exact_versioned_and_schema_valid() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/strategies")
    expected = {
        "strategies": [
            {
                "name": STRATEGY_NAME,
                "display_name": "Moving Average Crossover",
                "description": DESCRIPTION,
            }
        ]
    }

    assert response.status_code == 200
    assert response.json() == expected
    assert StrategyListResponse.model_validate(response.json()).model_dump() == expected
    _assert_uuid(response.headers[REQUEST_ID_HEADER])
    assert client.get("/strategies").status_code == 404


def test_strategy_detail_endpoint_is_exact_and_schema_valid() -> None:
    response = TestClient(create_app()).get(f"/api/v1/strategies/{STRATEGY_NAME}")
    expected = {
        "name": STRATEGY_NAME,
        "display_name": "Moving Average Crossover",
        "description": DESCRIPTION,
        "parameters": [
            {
                "name": "fast_window",
                "value_type": "integer",
                "required": True,
                "default": None,
            },
            {
                "name": "slow_window",
                "value_type": "integer",
                "required": True,
                "default": None,
            },
            {
                "name": "initial_capital",
                "value_type": "number",
                "required": False,
                "default": 1.0,
            },
            {
                "name": "transaction_cost_rate",
                "value_type": "number",
                "required": False,
                "default": 0.0,
            },
            {
                "name": "slippage_rate",
                "value_type": "number",
                "required": False,
                "default": 0.0,
            },
        ],
    }

    assert response.status_code == 200
    assert response.json() == expected
    assert (
        StrategyDetailResponse.model_validate(response.json()).model_dump() == expected
    )
    _assert_uuid(response.headers[REQUEST_ID_HEADER])


@pytest.mark.parametrize(
    "strategy_name",
    ("unknown", "Moving_Average_Crossover", " moving_average_crossover "),
)
def test_unknown_and_non_exact_strategy_names_use_stable_404_envelope(
    strategy_name: str,
) -> None:
    encoded_name = quote(strategy_name, safe="")
    response = TestClient(create_app()).get(f"/api/v1/strategies/{encoded_name}")
    payload = response.json()

    assert response.status_code == 404
    assert payload["error"] == {"code": "not_found", "message": "Not Found"}
    error = ApiErrorResponse.model_validate(payload)
    assert error.request_id == response.headers[REQUEST_ID_HEADER]
    _assert_uuid(error.request_id)
    assert strategy_name not in response.text


def test_strategy_routes_are_only_the_two_approved_versioned_endpoints() -> None:
    paths = set(create_app().openapi()["paths"])

    assert "/api/v1/strategies" in paths
    assert "/api/v1/strategies/{strategy_name}" in paths
    assert "/strategies" not in paths
