"""Tests for versioned configured research-run inspection endpoints."""

import json
from pathlib import Path
from urllib.parse import quote
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from el_psy_quant.api.app import RESEARCH_ARTIFACT_ROOT_ENV, create_app
from el_psy_quant.api.middleware import REQUEST_ID_HEADER
from el_psy_quant.api.research_schemas import (
    ResearchRunDetailResponse,
    ResearchRunListResponse,
)
from el_psy_quant.api.schemas import ApiErrorResponse


def _manifest(run_id: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "experiment_name": "My Experiment",
        "strategy": "moving_average_crossover",
        "run_id": run_id,
        "data": {"source": "cache", "symbols": ["AAPL"]},
        "parameters": {
            "fast_window": 10,
            "slow_window": 20,
            "initial_capital": 1.0,
            "transaction_cost_rate": 0.0,
            "slippage_rate": 0.0,
        },
        "evaluation": {
            "periods_per_year": None,
            "annual_risk_free_rate": 0.0,
        },
        "artifacts": {
            "config": "config.yaml",
            "metadata": "metadata.json",
            "summary": "results/summary.csv",
            "metrics": "results/metrics.json",
            "logs_dir": "logs",
        },
    }


def _metrics(run_id: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "run_id": run_id,
        "source_artifact": "results/summary.csv",
        "metrics": [
            {
                "symbol": "AAPL",
                "initial_equity": 1.0,
                "final_equity": 1.1,
                "total_return": 0.1,
                "max_drawdown": -0.02,
                "periods": 10.0,
            }
        ],
    }


def _write_run(root: Path, run_id: str = "run_1") -> None:
    run = root / "my-experiment" / run_id
    (run / "results").mkdir(parents=True)
    (run / "manifest.json").write_text(json.dumps(_manifest(run_id)), encoding="utf-8")
    (run / "results" / "metrics.json").write_text(
        json.dumps(_metrics(run_id)), encoding="utf-8"
    )


def _assert_request_id(response) -> None:
    request_id = response.headers[REQUEST_ID_HEADER]
    assert str(UUID(request_id)) == request_id
    if response.status_code >= 400:
        error = ApiErrorResponse.model_validate(response.json())
        assert error.request_id == request_id


def test_factory_root_override_environment_precedence_and_independence(
    tmp_path: Path, monkeypatch
) -> None:
    environment_root = tmp_path / "environment"
    override_root = tmp_path / "override"
    monkeypatch.setenv(RESEARCH_ARTIFACT_ROOT_ENV, str(environment_root))

    environment_app = create_app()
    override_app = create_app(research_artifact_root=override_root)
    blank_override_app = create_app(research_artifact_root="  ")

    assert environment_app.state.research_artifact_root == environment_root
    assert override_app.state.research_artifact_root == override_root
    assert blank_override_app.state.research_artifact_root is None
    assert (
        environment_app.state.research_artifact_root
        != override_app.state.research_artifact_root
    )


def test_unset_and_blank_environment_are_unconfigured(monkeypatch) -> None:
    monkeypatch.delenv(RESEARCH_ARTIFACT_ROOT_ENV, raising=False)
    assert create_app().state.research_artifact_root is None
    monkeypatch.setenv(RESEARCH_ARTIFACT_ROOT_ENV, "   ")
    assert create_app().state.research_artifact_root is None


def test_application_construction_does_not_touch_filesystem(
    tmp_path: Path, monkeypatch
) -> None:
    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("filesystem access during app construction")

    monkeypatch.setattr(Path, "resolve", forbidden)
    monkeypatch.setattr(Path, "exists", forbidden)
    monkeypatch.setattr(Path, "is_dir", forbidden)
    app = create_app(research_artifact_root=tmp_path / "not-checked")
    assert app.state.research_artifact_root == tmp_path / "not-checked"


def test_unavailable_root_has_stable_503_while_existing_routes_work() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/research-runs")
    assert response.status_code == 503
    assert response.json()["error"] == {
        "code": "research_artifact_root_unavailable",
        "message": "Research artifact root is unavailable",
    }
    _assert_request_id(response)
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/strategies").status_code == 200


def test_empty_root_and_list_success_contract(tmp_path: Path) -> None:
    client = TestClient(create_app(research_artifact_root=tmp_path))
    empty = client.get("/api/v1/research-runs")
    assert empty.status_code == 200
    assert empty.json() == {"runs": []}
    ResearchRunListResponse.model_validate(empty.json())

    _write_run(tmp_path)
    response = client.get("/api/v1/research-runs")
    expected = {
        "runs": [
            {
                "experiment_slug": "my-experiment",
                "run_id": "run_1",
                "experiment_name": "My Experiment",
                "strategy": "moving_average_crossover",
                "data_source": "cache",
                "symbols": ["AAPL"],
            }
        ]
    }
    assert response.status_code == 200
    assert response.json() == expected
    assert (
        ResearchRunListResponse.model_validate(response.json()).model_dump() == expected
    )
    _assert_request_id(response)


def test_detail_success_contract_and_optional_nulls(tmp_path: Path) -> None:
    _write_run(tmp_path)
    response = TestClient(create_app(research_artifact_root=tmp_path)).get(
        "/api/v1/research-runs/my-experiment/run_1"
    )

    assert response.status_code == 200
    payload = response.json()
    detail = ResearchRunDetailResponse.model_validate(payload)
    assert detail.experiment_slug == "my-experiment"
    assert detail.artifacts.metrics == "results/metrics.json"
    assert detail.metrics[0].cagr is None
    assert detail.metrics[0].annualized_volatility is None
    assert detail.metrics[0].sharpe_ratio is None
    assert str(tmp_path) not in response.text
    _assert_request_id(response)


@pytest.mark.parametrize(
    "path",
    (
        "/api/v1/research-runs/my-experiment/missing",
        "/api/v1/research-runs/My-experiment/run_1",
        "/api/v1/research-runs/my-experiment/run.1",
        f"/api/v1/research-runs/{quote('my/experiment', safe='')}/run_1",
    ),
)
def test_missing_invalid_and_encoded_identifiers_do_not_escape(
    tmp_path: Path, path: str
) -> None:
    response = TestClient(create_app(research_artifact_root=tmp_path)).get(path)
    assert response.status_code == 404
    assert str(tmp_path) not in response.text
    if response.json()["error"]["code"] == "research_run_not_found":
        _assert_request_id(response)


def test_malformed_artifact_has_sanitized_422(tmp_path: Path) -> None:
    run = tmp_path / "my-experiment" / "run_1"
    run.mkdir(parents=True)
    (run / "manifest.json").write_text("not-json", encoding="utf-8")

    response = TestClient(create_app(research_artifact_root=tmp_path)).get(
        "/api/v1/research-runs"
    )
    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "research_artifact_invalid",
        "message": "Research artifact is invalid",
    }
    assert "not-json" not in response.text
    assert str(tmp_path) not in response.text
    _assert_request_id(response)


def test_only_two_versioned_research_routes_exist() -> None:
    paths = set(create_app().openapi()["paths"])
    assert "/api/v1/research-runs" in paths
    assert "/api/v1/research-runs/{experiment_slug}/{run_id}" in paths
    assert "/research-runs" not in paths
    assert not any("download" in path or "raw" in path for path in paths)
