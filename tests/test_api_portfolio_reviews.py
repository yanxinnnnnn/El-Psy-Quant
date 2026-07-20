from pathlib import Path
from uuid import UUID

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from el_psy_quant.api.app import create_app
from el_psy_quant.api.middleware import REQUEST_ID_HEADER
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUTH = ("synthetic-founder", "synthetic-secret")


def _payload() -> dict[str, object]:
    return {
        "review_id": "synthetic-review",
        "source": {
            "source_id": "synthetic-source",
            "components": [
                {
                    "component_id": "synthetic-component-1",
                    "strategy_id": "synthetic-strategy-1",
                    "evidence_references": [
                        {
                            "reference_type": "research_run",
                            "reference_id": "synthetic-run-1",
                        }
                    ],
                    "symbols": ["SYN-A"],
                },
                {
                    "component_id": "synthetic-component-2",
                    "strategy_id": "synthetic-strategy-2",
                    "evidence_references": [
                        {
                            "reference_type": "research_run",
                            "reference_id": "synthetic-run-2",
                        }
                    ],
                    "symbols": None,
                },
            ],
            "return_observations": [
                {
                    "timestamp": "2026-07-01T00:00:00Z",
                    "component_returns": [0.01, 0.02],
                },
                {
                    "timestamp": "2026-07-02T00:00:00Z",
                    "component_returns": [-0.01, 0.01],
                },
                {
                    "timestamp": "2026-07-03T00:00:00Z",
                    "component_returns": [0.02, -0.01],
                },
            ],
            "evaluation_frequency": "daily",
            "periods_per_year": 252,
            "created_by": "synthetic-source-actor",
            "created_timestamp": "2026-07-04T00:00:00Z",
            "assumptions": ["Synthetic history only"],
            "warnings": ["Synthetic values only"],
            "missing_evidence": ["Second symbol set unavailable"],
        },
        "baseline_scenario": {
            "scenario_id": "synthetic-baseline",
            "weights": {
                "synthetic-component-1": 1.0,
                "synthetic-component-2": 0.0,
            },
            "rationale": "Synthetic baseline",
        },
        "proposed_scenario": {
            "scenario_id": "synthetic-proposed",
            "weights": {
                "synthetic-component-1": 0.5,
                "synthetic-component-2": 0.5,
            },
            "proposed_component_id": "synthetic-component-2",
            "rationale": "Synthetic proposal",
        },
        "analysis": {
            "created_by": "synthetic-analysis-actor",
            "created_timestamp": "2026-07-05T00:00:00Z",
            "assumptions": ["Historical scenario evidence only"],
            "warnings": [],
            "missing_evidence": ["Symbol overlap unavailable"],
        },
    }


@pytest.fixture
def configured_app(tmp_path: Path, monkeypatch):
    database_path = tmp_path / "product.sqlite3"
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    command.upgrade(Config(str(PROJECT_ROOT / "alembic.ini")), "head")
    return create_app(
        product_database_path=database_path,
        evidence_artifact_root=evidence_root,
        founder_username=AUTH[0],
        founder_password=AUTH[1],
    )


def _assert_error(response, status: int, code: str) -> None:
    assert response.status_code == status, response.text
    payload = response.json()
    assert payload["error"]["code"] == code
    request_id = response.headers[REQUEST_ID_HEADER]
    assert str(UUID(request_id)) == request_id == payload["request_id"]


def test_all_routes_require_existing_authentication(configured_app) -> None:
    with TestClient(configured_app) as client:
        for method, path in (
            ("post", "/api/v1/portfolio-reviews"),
            ("get", "/api/v1/portfolio-reviews"),
            ("get", "/api/v1/portfolio-reviews/synthetic-review"),
            (
                "post",
                "/api/v1/portfolio-reviews/synthetic-review/decision",
            ),
        ):
            response = getattr(client, method)(path)
            _assert_error(response, 401, "founder_authentication_required")


def test_create_replay_list_and_exact_awaiting_detail(configured_app) -> None:
    with TestClient(configured_app) as client:
        missing_key = client.post(
            "/api/v1/portfolio-reviews",
            auth=AUTH,
            json=_payload(),
        )
        _assert_error(missing_key, 422, "request_validation_error")

        created = client.post(
            "/api/v1/portfolio-reviews",
            auth=AUTH,
            headers={"Idempotency-Key": "synthetic-create-key"},
            json=_payload(),
        )
        assert created.status_code == 201, created.text
        assert created.json()["outcome"] == "created"
        detail = created.json()["review"]
        assert detail["record"]["status"] == "awaiting_decision"
        assert detail["decision"] is None
        assert detail["source"]["return_observations"]
        assert (
            detail["analysis"]["interaction_impact_analysis"][
                "symbol_overlaps"
            ][0]["jaccard_overlap"]
            is None
        )
        assert "source_relative_path" not in detail["record"]
        assert "create_idempotency_key" not in detail["record"]

        replayed = client.post(
            "/api/v1/portfolio-reviews",
            auth=AUTH,
            headers={"Idempotency-Key": "synthetic-create-key"},
            json=_payload(),
        )
        assert replayed.status_code == 200
        assert replayed.json()["outcome"] == "replayed"
        assert replayed.json()["review"] == detail

        listed = client.get(
            "/api/v1/portfolio-reviews?status=awaiting_decision&limit=50",
            auth=AUTH,
        )
        assert listed.status_code == 200
        assert [item["review_id"] for item in listed.json()] == [
            "synthetic-review"
        ]
        reopened = client.get(
            "/api/v1/portfolio-reviews/synthetic-review",
            auth=AUTH,
        )
        assert reopened.status_code == 200
        assert reopened.json() == detail


def test_decision_created_replayed_and_settled_conflict(configured_app) -> None:
    with TestClient(configured_app) as client:
        created = client.post(
            "/api/v1/portfolio-reviews",
            auth=AUTH,
            headers={"Idempotency-Key": "synthetic-create-key"},
            json=_payload(),
        )
        assert created.status_code == 201
        decision = {
            "decision_id": "synthetic-decision",
            "outcome": "approved",
            "rationale": "Synthetic governance-only approval",
            "reviewed_by": "synthetic-founder",
            "reviewed_timestamp": "2026-07-06T00:00:00Z",
            "notes": ["No execution authority"],
            "warnings": ["Approval is governance evidence only"],
        }
        missing_key = client.post(
            "/api/v1/portfolio-reviews/synthetic-review/decision",
            auth=AUTH,
            json=decision,
        )
        _assert_error(missing_key, 422, "request_validation_error")

        settled = client.post(
            "/api/v1/portfolio-reviews/synthetic-review/decision",
            auth=AUTH,
            headers={"Idempotency-Key": "synthetic-decision-key"},
            json=decision,
        )
        assert settled.status_code == 201, settled.text
        assert settled.json()["outcome"] == "created"
        assert settled.json()["review"]["record"]["status"] == "approved"
        assert settled.json()["review"]["decision"]["outcome"] == "approved"

        replayed = client.post(
            "/api/v1/portfolio-reviews/synthetic-review/decision",
            auth=AUTH,
            headers={"Idempotency-Key": "synthetic-decision-key"},
            json=decision,
        )
        assert replayed.status_code == 200
        assert replayed.json()["outcome"] == "replayed"

        conflict = client.post(
            "/api/v1/portfolio-reviews/synthetic-review/decision",
            auth=AUTH,
            headers={"Idempotency-Key": "different-decision-key"},
            json={**decision, "decision_id": "different-decision"},
        )
        _assert_error(conflict, 409, "portfolio_review_settled_conflict")


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    (
        ("component_return", "0.01"),
        ("scenario_weight", "0.5"),
        ("periods_per_year", "252"),
        ("component_return", True),
        ("scenario_weight", False),
        ("periods_per_year", True),
    ),
)
def test_create_rejects_coercive_numeric_transport_values(
    configured_app,
    field: str,
    invalid_value: object,
) -> None:
    payload = _payload()
    if field == "component_return":
        payload["source"]["return_observations"][0]["component_returns"][0] = (
            invalid_value
        )
    elif field == "scenario_weight":
        payload["proposed_scenario"]["weights"]["synthetic-component-1"] = (
            invalid_value
        )
    else:
        payload["source"]["periods_per_year"] = invalid_value

    with TestClient(configured_app) as client:
        response = client.post(
            "/api/v1/portfolio-reviews",
            auth=AUTH,
            headers={"Idempotency-Key": "synthetic-create-key"},
            json=payload,
        )

    _assert_error(response, 422, "request_validation_error")


def test_create_accepts_integer_and_float_numeric_transport_values(
    configured_app,
) -> None:
    payload = _payload()
    payload["source"]["return_observations"][0]["component_returns"][0] = 0
    payload["source"]["periods_per_year"] = 252.0
    payload["baseline_scenario"]["weights"]["synthetic-component-1"] = 1

    with TestClient(configured_app) as client:
        response = client.post(
            "/api/v1/portfolio-reviews",
            auth=AUTH,
            headers={"Idempotency-Key": "synthetic-create-key"},
            json=payload,
        )

    assert response.status_code == 201, response.text
    assert response.json()["outcome"] == "created"


def test_stable_invalid_not_found_root_and_database_errors(
    configured_app,
    tmp_path: Path,
) -> None:
    invalid = _payload()
    invalid["source"]["return_observations"][0]["component_returns"][0] = "NaN"
    with TestClient(configured_app) as client:
        response = client.post(
            "/api/v1/portfolio-reviews",
            auth=AUTH,
            headers={"Idempotency-Key": "synthetic-create-key"},
            json=invalid,
        )
        _assert_error(response, 422, "request_validation_error")
        missing = client.get(
            "/api/v1/portfolio-reviews/missing",
            auth=AUTH,
        )
        _assert_error(missing, 404, "portfolio_review_not_found")

    unavailable_root_app = create_app(
        product_database_path=configured_app.state.product_database_path,
        evidence_artifact_root=tmp_path / "missing-root",
        founder_username=AUTH[0],
        founder_password=AUTH[1],
    )
    with TestClient(unavailable_root_app) as client:
        response = client.get(
            "/api/v1/portfolio-reviews/missing",
            auth=AUTH,
        )
        _assert_error(
            response,
            503,
            "portfolio_review_artifact_root_unavailable",
        )

    unavailable_database_app = create_app(
        evidence_artifact_root=configured_app.state.evidence_artifact_root,
        product_database_path="",
        founder_username=AUTH[0],
        founder_password=AUTH[1],
    )
    with TestClient(unavailable_database_app) as client:
        response = client.get("/api/v1/portfolio-reviews", auth=AUTH)
        _assert_error(response, 503, "product_database_unavailable")


def test_openapi_has_only_four_explicit_portfolio_review_operations(
    configured_app,
) -> None:
    document = configured_app.openapi()
    paths = {
        path: set(methods)
        for path, methods in document["paths"].items()
        if path.startswith("/api/v1/portfolio-reviews")
    }
    assert paths == {
        "/api/v1/portfolio-reviews": {"get", "post"},
        "/api/v1/portfolio-reviews/{review_id}": {"get"},
        "/api/v1/portfolio-reviews/{review_id}/decision": {"post"},
    }
    schemas = document["components"]["schemas"]
    for name in (
        "PortfolioReviewCreateRequest",
        "PortfolioReviewDecisionRequest",
        "PortfolioReviewSourceResponse",
        "PortfolioReviewAnalysisResponse",
        "PortfolioReviewDecisionResponse",
        "PortfolioReviewDetailResponse",
    ):
        assert name in schemas
