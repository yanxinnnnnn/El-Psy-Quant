"""Deterministic inventory, request-event, and redaction coverage."""

from concurrent.futures import ThreadPoolExecutor
import logging
from logging import LogRecord
import subprocess
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from el_psy_quant.api.app import create_app
from el_psy_quant.api.error_inventory import (
    STABLE_API_ERRORS,
    StableApiError,
    build_stable_error_index,
)
from el_psy_quant.api.observability import (
    API_OPERATIONS,
    MAX_DURATION_MS,
    PRODUCT_LOGGER_NAME,
    ApiOperation,
    bounded_duration_ms,
    build_operation_indexes,
)

EXPECTED_STABLE_CODES = {
    "not_found",
    "method_not_allowed",
    "http_error",
    "request_validation_error",
    "internal_server_error",
    "founder_authentication_required",
    "research_artifact_root_unavailable",
    "research_run_not_found",
    "research_artifact_invalid",
    "evidence_artifact_root_unavailable",
    "evidence_manifest_not_found",
    "evidence_artifact_invalid",
    "paper_run_invalid",
    "product_database_unavailable",
    "paper_artifact_root_unavailable",
    "paper_job_not_found",
    "paper_job_invalid",
    "paper_job_idempotency_conflict",
    "paper_job_conflict",
    "paper_job_state_conflict",
    "paper_job_output_conflict",
    "paper_job_recovery_failed",
    "paper_job_result_unavailable",
    "paper_job_result_invalid",
    "lifecycle_transition_proposal_invalid",
    "lifecycle_transition_record_invalid",
    "demo_workspace_not_configured",
    "demo_workspace_unavailable",
}


@pytest.fixture(autouse=True)
def _enable_product_logger_after_alembic_logging_configuration() -> None:
    """Keep capture deterministic after Alembic disables existing loggers."""
    logging.getLogger(PRODUCT_LOGGER_NAME).disabled = False


def _product_records(caplog: pytest.LogCaptureFixture) -> list[LogRecord]:
    return [
        record
        for record in caplog.records
        if record.name == PRODUCT_LOGGER_NAME
    ]


def _request_record(caplog: pytest.LogCaptureFixture) -> LogRecord:
    records = [
        record
        for record in _product_records(caplog)
        if record.event == "api_request_completed"
    ]
    assert len(records) == 1
    return records[0]


def test_stable_error_inventory_is_complete_unique_and_categorized() -> None:
    assert {item.code for item in STABLE_API_ERRORS} == EXPECTED_STABLE_CODES
    assert len(STABLE_API_ERRORS) == len(EXPECTED_STABLE_CODES)
    assert all(
        item.category
        in {
            "authentication",
            "not_found",
            "invalid",
            "conflict",
            "unavailable",
            "protocol",
            "internal",
        }
        for item in STABLE_API_ERRORS
    )


def test_duplicate_error_codes_and_operation_names_fail_deterministically() -> None:
    duplicate_error = StableApiError("duplicate", "invalid")
    with pytest.raises(ValueError, match="error codes"):
        build_stable_error_index((duplicate_error, duplicate_error))

    first = ApiOperation("GET", "/one", "one.read")
    with pytest.raises(ValueError, match="method and route-template"):
        build_operation_indexes((first, ApiOperation("GET", "/one", "two.read")))
    with pytest.raises(ValueError, match="operation names"):
        build_operation_indexes((first, ApiOperation("GET", "/two", "one.read")))

    assert len(API_OPERATIONS) == len({item.operation for item in API_OPERATIONS})


def test_uvicorn_console_emits_all_info_correlation_events_without_caplog() -> None:
    script = """
from logging.config import dictConfig
from uvicorn.config import LOGGING_CONFIG

dictConfig(LOGGING_CONFIG)

from el_psy_quant.api.observability import (
    log_api_request_completed,
    log_paper_job_command_completed,
    log_paper_job_execution_terminal,
)

log_api_request_completed(
    request_id="startup-request",
    method="GET",
    operation="health.read",
    route_template="/api/v1/health",
    status_code=200,
    duration_ms=7,
    error_code=None,
)
log_paper_job_command_completed(
    request_id="startup-request",
    command="run",
    job_id="startup-job",
    durable_status="running",
    attempt_id="startup-attempt",
    attempt_number=1,
)
log_paper_job_execution_terminal(
    event="paper_job_execution_completed",
    request_id="startup-request",
    job_id="startup-job",
    attempt_id="startup-attempt",
    attempt_number=1,
    durable_status="succeeded",
    error_code=None,
)
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stdout == ""
    assert "api_request_completed request_id=startup-request" in completed.stderr
    assert (
        "paper_job_command_completed request_id=startup-request"
        in completed.stderr
    )
    assert (
        "paper_job_execution_completed request_id=startup-request"
        in completed.stderr
    )
    assert "job_id=startup-job" in completed.stderr
    assert "durable_status=succeeded" in completed.stderr


@pytest.mark.parametrize(
    ("method", "path", "expected_status", "operation", "template", "error_code"),
    (
        ("get", "/api/v1/health", 200, "health.read", "/api/v1/health", None),
        ("get", "/api/v1/missing?secret=query-value", 404, "unmatched", "unmatched", "not_found"),
        (
            "post",
            "/api/v1/health",
            405,
            "health.read",
            "/api/v1/health",
            "method_not_allowed",
        ),
        (
            "post",
            "/api/v1/paper-runs",
            422,
            "paper_run.execute",
            "/api/v1/paper-runs",
            "request_validation_error",
        ),
        (
            "get",
            "/api/v1/research-runs",
            503,
            "research_run.list",
            "/api/v1/research-runs",
            "research_artifact_root_unavailable",
        ),
    ),
)
def test_each_handled_request_emits_one_bounded_completion_event(
    caplog: pytest.LogCaptureFixture,
    method: str,
    path: str,
    expected_status: int,
    operation: str,
    template: str,
    error_code: str | None,
) -> None:
    caplog.set_level("INFO", logger=PRODUCT_LOGGER_NAME)
    client = TestClient(create_app())
    response = client.post(path, json={}) if method == "post" else client.get(path)

    assert response.status_code == expected_status
    record = _request_record(caplog)
    assert record.request_id == response.headers["X-Request-ID"]
    assert record.method == method.upper()
    assert record.operation == operation
    assert record.route_template == template
    assert record.status_code == expected_status
    assert type(record.duration_ms) is int
    assert 0 <= record.duration_ms <= MAX_DURATION_MS
    assert record.error_code == error_code


def test_authentication_and_unexpected_failures_are_correlated_and_sanitized(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level("INFO", logger=PRODUCT_LOGGER_NAME)
    protected = TestClient(
        create_app(founder_username="founder", founder_password="private-password")
    )
    unauthorized = protected.get(
        "/api/v1/health",
        headers={"Authorization": "Basic private-authorization"},
    )
    unauthorized_record = _request_record(caplog)
    assert unauthorized.status_code == 401
    assert unauthorized_record.error_code == "founder_authentication_required"

    caplog.clear()
    application = create_app()

    @application.get("/api/v1/sensitive-failure")
    async def sensitive_failure() -> None:
        raise RuntimeError(
            "exception-secret C:\\private\\artifact.json /var/private/a "
            "SELECT * FROM paper_jobs Traceback"
        )

    failed = TestClient(application, raise_server_exceptions=False).get(
        "/api/v1/sensitive-failure?token=query-secret"
    )
    failed_record = _request_record(caplog)
    assert failed.status_code == 500
    assert failed_record.operation == "unmatched"
    assert failed_record.route_template == "unmatched"
    assert failed_record.error_code == "internal_server_error"

    rendered = " ".join(
        f"{record.getMessage()} {record.__dict__}"
        for record in _product_records(caplog)
    )
    for forbidden in (
        "exception-secret",
        "private-authorization",
        "private\\artifact",
        "/var/private",
        "SELECT *",
        "Traceback",
        "query-secret",
        "sensitive-failure",
    ):
        assert forbidden not in rendered


def test_concurrent_request_events_keep_distinct_server_request_ids(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level("INFO", logger=PRODUCT_LOGGER_NAME)
    client = TestClient(create_app())

    with ThreadPoolExecutor(max_workers=4) as executor:
        responses = list(
            executor.map(lambda _index: client.get("/api/v1/health"), range(8))
        )

    records = [
        record
        for record in _product_records(caplog)
        if record.event == "api_request_completed"
    ]
    response_ids = {response.headers["X-Request-ID"] for response in responses}
    record_ids = {record.request_id for record in records}
    assert len(records) == 8
    assert len(response_ids) == 8
    assert record_ids == response_ids


def test_timing_normalization_is_deterministic_and_bounded() -> None:
    assert bounded_duration_ms(10.0, 9.0) == 0
    assert bounded_duration_ms(10.0, 10.0129) == 12
    assert bounded_duration_ms(0.0, float(MAX_DURATION_MS + 10)) == MAX_DURATION_MS


def test_app_construction_emits_no_product_event_or_io(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level("INFO", logger=PRODUCT_LOGGER_NAME)

    application = create_app()

    assert isinstance(application, FastAPI)
    assert _product_records(caplog) == []
