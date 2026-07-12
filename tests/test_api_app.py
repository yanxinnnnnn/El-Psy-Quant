"""Focused tests for the Sprint 138 local API skeleton."""

from uuid import UUID

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.testclient import TestClient

from el_psy_quant import __version__
from el_psy_quant.api.app import app, create_app
from el_psy_quant.api.middleware import REQUEST_ID_HEADER
from el_psy_quant.api.schemas import ApiErrorResponse, HealthResponse


def _assert_uuid(value: str) -> None:
    assert str(UUID(value)) == value


def test_application_factory_returns_independent_fastapi_instances() -> None:
    first = create_app()
    second = create_app()

    assert isinstance(first, FastAPI)
    assert isinstance(second, FastAPI)
    assert first is not second
    assert isinstance(app, FastAPI)
    assert first.title == "el-psy-quant"
    assert first.version == __version__ == "0.1.0"


def test_application_has_no_startup_or_shutdown_dependencies() -> None:
    application = create_app()

    assert application.router.on_startup == []
    assert application.router.on_shutdown == []
    assert application.state._state == {
        "research_artifact_root": None,
        "evidence_artifact_root": None,
    }


def test_health_contract_is_exact_json_and_schema_valid() -> None:
    response = TestClient(create_app()).get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "status": "ok",
        "service": "el-psy-quant",
        "api_version": "v1",
    }
    assert (
        HealthResponse.model_validate(response.json()).model_dump() == response.json()
    )


def test_health_is_versioned_and_not_unversioned() -> None:
    client = TestClient(create_app())

    assert client.get("/api/v1/health").status_code == 200
    unversioned = client.get("/health")
    assert unversioned.status_code == 404
    assert unversioned.json()["error"]["code"] == "not_found"


def test_success_responses_have_distinct_server_owned_request_ids() -> None:
    client = TestClient(create_app())

    first = client.get(
        "/api/v1/health",
        headers={REQUEST_ID_HEADER: "caller-controlled-value"},
    )
    second = client.get("/api/v1/health")
    first_id = first.headers[REQUEST_ID_HEADER]
    second_id = second.headers[REQUEST_ID_HEADER]

    _assert_uuid(first_id)
    _assert_uuid(second_id)
    assert first_id != "caller-controlled-value"
    assert first_id != second_id


def test_request_id_is_stored_on_request_state() -> None:
    application = create_app()

    @application.get("/api/v1/test-request-state")
    async def request_state_route(request: Request) -> dict[str, str]:
        return {"request_id": request.state.request_id}

    response = TestClient(application).get("/api/v1/test-request-state")

    assert response.json()["request_id"] == response.headers[REQUEST_ID_HEADER]
    _assert_uuid(response.json()["request_id"])


def test_unknown_route_uses_stable_not_found_envelope() -> None:
    response = TestClient(create_app()).get("/api/v1/missing")

    assert response.status_code == 404
    assert response.json()["error"] == {
        "code": "not_found",
        "message": "Not Found",
    }
    _assert_error_request_id(response)


def test_unsupported_method_uses_stable_method_not_allowed_envelope() -> None:
    response = TestClient(create_app()).post("/api/v1/health")

    assert response.status_code == 405
    assert response.json()["error"] == {
        "code": "method_not_allowed",
        "message": "Method Not Allowed",
    }
    assert "GET" in response.headers["allow"].split(", ")
    _assert_error_request_id(response)


def test_request_validation_errors_use_stable_envelope() -> None:
    application = create_app()

    @application.get("/api/v1/test-validation")
    async def validation_route(value: int = Query()) -> dict[str, int]:
        return {"value": value}

    response = TestClient(application).get(
        "/api/v1/test-validation",
        params={"value": "not-an-integer"},
    )

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "request_validation_error",
        "message": "Request Validation Error",
    }
    assert "not-an-integer" not in response.text
    _assert_error_request_id(response)


def test_other_http_exceptions_use_generic_http_error_code() -> None:
    application = create_app()

    @application.get("/api/v1/test-http-error")
    async def http_error_route() -> None:
        raise HTTPException(status_code=418, detail="internal detail")

    response = TestClient(application).get("/api/v1/test-http-error")

    assert response.status_code == 418
    assert response.json()["error"] == {
        "code": "http_error",
        "message": "I'm a Teapot",
    }
    assert "internal detail" not in response.text
    _assert_error_request_id(response)


def test_unexpected_exceptions_are_sanitized() -> None:
    application = create_app()

    @application.get("/api/v1/test-error")
    async def error_route() -> None:
        raise RuntimeError("secret detail from C:\\private\\artifact.json")

    response = TestClient(application, raise_server_exceptions=False).get(
        "/api/v1/test-error"
    )

    assert response.status_code == 500
    assert response.json()["error"] == {
        "code": "internal_server_error",
        "message": "Internal Server Error",
    }
    assert "secret detail" not in response.text
    assert "private" not in response.text
    assert "RuntimeError" not in response.text
    assert "Traceback" not in response.text
    _assert_error_request_id(response)


def _assert_error_request_id(response) -> None:
    payload = response.json()
    assert set(payload) == {"error", "request_id"}
    assert set(payload["error"]) == {"code", "message"}
    body = ApiErrorResponse.model_validate(payload)
    header_request_id = response.headers[REQUEST_ID_HEADER]
    assert body.request_id == header_request_id
    _assert_uuid(body.request_id)


def test_api_package_exposes_only_the_application_boundary() -> None:
    from el_psy_quant import api

    assert api.app is app
    assert api.create_app is create_app
    forbidden = {
        "StrategyCatalogService",
        "ArtifactInspectionService",
        "start_paper_run",
        "create_lifecycle_proposal",
        "review_lifecycle_proposal",
        "Repository",
        "JobWorker",
        "JobStatus",
        "QmtClient",
        "BrokerClient",
        "execute_live_order",
    }
    assert all(not hasattr(api, name) for name in forbidden)


def test_production_routes_include_no_artifact_or_runtime_behavior() -> None:
    paths = set(create_app().openapi()["paths"])

    assert "/api/v1/health" in paths
    assert "/health" not in paths
    assert not any(
        path.startswith(
            (
                "/api/v1/artifacts",
                "/api/v1/paper-runs",
                "/api/v1/lifecycle",
                "/api/v1/jobs",
                "/api/v1/brokers",
            )
        )
        for path in paths
    )
