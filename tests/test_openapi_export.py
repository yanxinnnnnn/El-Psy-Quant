"""Focused tests for the deterministic Web OpenAPI export boundary."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SERVER_LOCAL_ENVIRONMENT_NAMES = (
    "EL_PSY_QUANT_RESEARCH_ARTIFACT_ROOT",
    "EL_PSY_QUANT_EVIDENCE_ARTIFACT_ROOT",
    "EL_PSY_QUANT_PRODUCT_DATABASE_PATH",
    "EL_PSY_QUANT_PAPER_ARTIFACT_ROOT",
    "EL_PSY_QUANT_WORKSPACE_MODE",
    "EL_PSY_QUANT_DEMO_WORKSPACE_ROOT",
)


def test_m33_generated_contracts_are_strict_and_operation_ids_are_stable() -> None:
    snapshot_path = REPOSITORY_ROOT / "web/src/generated/openapi.json"
    types_path = REPOSITORY_ROOT / "web/src/generated/api-types.ts"
    document = json.loads(snapshot_path.read_text(encoding="utf-8"))
    expected = {
        "evaluate_strategy_signal_v1",
        "list_strategy_signals_v1",
        "get_strategy_signal_v1",
        "create_order_intent_v1",
        "list_order_intents_v1",
        "get_order_intent_v1",
        "create_pre_trade_risk_decision_v1",
        "list_pre_trade_risk_decisions_v1",
        "get_pre_trade_risk_decision_v1",
    }
    observed = {
        operation["operationId"]
        for path, methods in document["paths"].items()
        if path.startswith(
            (
                "/api/v1/strategy-signals",
                "/api/v1/order-intents",
                "/api/v1/pre-trade-risk-decisions",
            )
        )
        for operation in methods.values()
    }
    assert observed == expected
    schemas = document["components"]["schemas"]
    for name in (
        "StrategySignalEvaluateRequest",
        "OrderIntentCreateRequest",
        "PreTradeRiskDecisionCreateRequest",
        "StrategySignalResponse",
        "OrderIntentResponse",
        "PreTradeRiskDecisionResponse",
    ):
        assert schemas[name]["additionalProperties"] is False
    assert (
        schemas["MovingAverageRuntimeRequest"]["properties"][
            "target_position_quantity"
        ]["type"]
        == "string"
    )
    risk_account = schemas["PreTradeRiskAccountRequest"]
    assert set(risk_account["properties"]) == {
        "expected_account_head_version",
        "expected_account_head_event_id",
        "expected_account_head_chain_digest",
    }
    assert set(risk_account["required"]) == set(risk_account["properties"])
    assert (
        schemas["PreTradeRiskDecisionCreateRequest"]["properties"][
            "account"
        ]["$ref"]
        == "#/components/schemas/PreTradeRiskAccountRequest"
    )
    for path in (
        "/api/v1/strategy-signals/{signal_id}",
        "/api/v1/order-intents/{intent_id}",
        "/api/v1/pre-trade-risk-decisions/{decision_id}",
    ):
        validation_schema = document["paths"][path]["get"]["responses"][
            "422"
        ]["content"]["application/json"]["schema"]
        assert validation_schema == {
            "$ref": "#/components/schemas/ApiErrorResponse"
        }
        assert "HTTPValidationError" not in json.dumps(
            document["paths"][path]["get"]["responses"]["422"]
        )
    generated = types_path.read_text(encoding="utf-8")
    assert all(operation_id in generated for operation_id in expected)
    assert "StrategySignalEvaluateRequest" in generated
    assert "PreTradeRiskAccountRequest" in generated
    assert "PreTradeRiskDecisionResponse" in generated


def test_canonical_openapi_matches_checked_in_snapshot() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/export_openapi.py", "--check"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_export_neutralizes_local_resources_and_has_no_filesystem_side_effects(
    tmp_path: Path,
) -> None:
    configured_paths = {
        name: tmp_path / name.lower() for name in SERVER_LOCAL_ENVIRONMENT_NAMES
    }
    environment = os.environ.copy()
    environment.update({name: str(path) for name, path in configured_paths.items()})

    result = subprocess.run(
        [sys.executable, "scripts/export_openapi.py", "--check"],
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert all(not path.exists() for path in configured_paths.values())
