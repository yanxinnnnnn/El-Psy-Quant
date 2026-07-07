"""Tests for local paper run result summaries."""

import copy
from dataclasses import FrozenInstanceError
import json
from pathlib import Path

import pytest

from el_psy_quant.paper import (
    PAPER_RUN_REQUEST_SCHEMA_VERSION,
    PAPER_RUN_RESULT_SUMMARY_SCHEMA_VERSION,
    PaperRunResultSummary,
    create_paper_account_state,
    create_paper_fill,
    create_paper_order_record,
    create_paper_run_request,
    create_paper_run_result_summary,
    create_paper_trading_artifact_audit_summary,
    create_paper_trading_artifact_file_payload,
    run_paper_trading_request,
)


def make_starting_state():
    return create_paper_account_state(
        starting_cash=1_000.0,
        current_cash=1_000.0,
        positions={"MSFT": 1.0},
        timestamp="2026-01-01",
    )


def make_ending_state():
    return create_paper_account_state(
        starting_cash=1_000.0,
        current_cash=875.0,
        positions={"MSFT": 0.5, "AAPL": 2.0},
        timestamp="2026-01-03",
    )


def make_orders():
    return [
        create_paper_order_record(
            order_id="order-1",
            timestamp="2026-01-02",
            symbol="aapl",
            side="buy",
            quantity=2.0,
            status="filled",
        ),
        create_paper_order_record(
            order_id="order-2",
            timestamp="2026-01-03",
            symbol=" msft ",
            side="sell",
            quantity=0.5,
            status="filled",
        ),
    ]


def make_fills():
    return [
        create_paper_fill(
            timestamp="2026-01-02",
            symbol="AAPL",
            side="buy",
            quantity=2.0,
            price=100.0,
            order_id="order-1",
        ),
        create_paper_fill(
            timestamp="2026-01-03",
            symbol="MSFT",
            side="sell",
            quantity=0.5,
            price=150.0,
            order_id="order-2",
        ),
    ]


def make_request():
    return create_paper_run_request(
        run_id="run-1",
        created_timestamp="2026-01-04T12:00:00Z",
        starting_account_state=make_starting_state(),
        ending_account_state=make_ending_state(),
        orders=make_orders(),
        fills=make_fills(),
    )


def make_artifact():
    return run_paper_trading_request(make_request())


def make_audit_summary(artifact=None):
    normalized_artifact = artifact or make_artifact()
    payload = create_paper_trading_artifact_file_payload(normalized_artifact)
    return create_paper_trading_artifact_audit_summary(payload)


def make_result_summary(
    *,
    request=None,
    artifact=None,
    artifact_path: str | Path = "paper-run-artifact.json",
    audit_summary=None,
):
    normalized_request = request or make_request()
    normalized_artifact = artifact or run_paper_trading_request(normalized_request)
    normalized_audit = audit_summary or make_audit_summary(normalized_artifact)

    return create_paper_run_result_summary(
        request=normalized_request,
        artifact=normalized_artifact,
        artifact_path=artifact_path,
        audit_summary=normalized_audit,
    )


def test_valid_paper_run_result_summary_creation() -> None:
    summary = make_result_summary()

    assert isinstance(summary, PaperRunResultSummary)


def test_result_summary_schema_version_exists() -> None:
    assert PAPER_RUN_RESULT_SUMMARY_SCHEMA_VERSION == 1
    json.dumps(
        {"schema_version": PAPER_RUN_RESULT_SUMMARY_SCHEMA_VERSION},
        allow_nan=False,
    )


def test_result_summary_to_dict_contains_expected_sections() -> None:
    request = make_request()
    artifact = run_paper_trading_request(request)
    audit = make_audit_summary(artifact)

    summary = make_result_summary(
        request=request,
        artifact=artifact,
        artifact_path="paper-run-artifact.json",
        audit_summary=audit,
    ).to_dict()

    assert summary == {
        "schema_version": PAPER_RUN_RESULT_SUMMARY_SCHEMA_VERSION,
        "run_id": "run-1",
        "request": {
            "schema_version": PAPER_RUN_REQUEST_SCHEMA_VERSION,
            "created_timestamp": "2026-01-04T12:00:00+00:00",
        },
        "artifact": {
            "schema_version": artifact.to_dict()["schema_version"],
            "created_timestamp": artifact.to_dict()["created_timestamp"],
            "path": "paper-run-artifact.json",
        },
        "audit": audit.to_dict(),
    }


def test_result_summary_export_is_deterministic_and_json_compatible() -> None:
    summary = make_result_summary()

    first = summary.to_dict()
    second = summary.to_dict()

    assert first == second
    json.dumps(first, allow_nan=False)


def test_result_summary_records_path_without_touching_files(tmp_path) -> None:
    destination = tmp_path / "paper-run-artifact.json"

    summary = make_result_summary(artifact_path=destination)

    assert summary.to_dict()["artifact"]["path"] == str(destination)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("request", {"request": object()}),
        ("artifact", {"artifact": object()}),
        ("audit_summary", {"audit_summary": object()}),
    ],
)
def test_invalid_object_inputs_raise_value_error(field_name: str, kwargs) -> None:
    with pytest.raises(ValueError, match=field_name):
        make_result_summary(**kwargs)


@pytest.mark.parametrize("artifact_path", [object(), ""])
def test_invalid_artifact_path_raises_value_error(artifact_path: object) -> None:
    with pytest.raises(ValueError, match="artifact_path"):
        make_result_summary(artifact_path=artifact_path)  # type: ignore[arg-type]


def test_audit_summary_must_match_artifact_identity() -> None:
    request = make_request()
    artifact = run_paper_trading_request(request)
    other_request = create_paper_run_request(
        run_id="run-2",
        created_timestamp="2026-01-05T12:00:00Z",
        starting_account_state=make_starting_state(),
        ending_account_state=make_ending_state(),
        orders=make_orders(),
        fills=make_fills(),
    )
    mismatched_audit = make_audit_summary(run_paper_trading_request(other_request))

    with pytest.raises(ValueError, match="audit_summary must match artifact identity"):
        make_result_summary(
            request=request,
            artifact=artifact,
            audit_summary=mismatched_audit,
        )


def test_result_summary_is_immutable() -> None:
    summary = make_result_summary()

    with pytest.raises(FrozenInstanceError):
        summary.artifact_path = "other.json"  # type: ignore[misc]


def test_result_summary_does_not_mutate_inputs() -> None:
    request = make_request()
    artifact = run_paper_trading_request(request)
    audit = make_audit_summary(artifact)
    request_before = copy.deepcopy(request.to_dict())
    artifact_before = copy.deepcopy(artifact.to_dict())
    audit_before = copy.deepcopy(audit.to_dict())

    summary = make_result_summary(
        request=request,
        artifact=artifact,
        audit_summary=audit,
    )
    summary.to_dict()

    assert request.to_dict() == request_before
    assert artifact.to_dict() == artifact_before
    assert audit.to_dict() == audit_before


def test_result_summary_does_not_create_artifact_or_recompute_audit() -> None:
    request = make_request()
    artifact = run_paper_trading_request(request)
    audit = make_audit_summary(artifact)

    summary = make_result_summary(
        request=request,
        artifact=artifact,
        audit_summary=audit,
    )

    assert summary.request is request
    assert summary.artifact is artifact
    assert summary.audit_summary is audit


def test_run_result_module_does_not_add_workflow_io_or_report_behavior() -> None:
    import el_psy_quant.paper.run_result as run_result  # noqa: PLC0415

    assert not hasattr(run_result, "run_paper_trading_request")
    assert not hasattr(run_result, "persist_paper_run_artifact")
    assert not hasattr(run_result, "read_paper_trading_artifact_file")
    assert not hasattr(run_result, "write_paper_trading_artifact_file")
    assert not hasattr(run_result, "render_paper_run_report")
    assert not hasattr(run_result, "create_paper_run_dashboard")


def test_package_exports_work() -> None:
    import el_psy_quant.paper as paper  # noqa: PLC0415

    summary = paper.create_paper_run_result_summary(
        request=make_request(),
        artifact=make_artifact(),
        artifact_path="paper-run-artifact.json",
        audit_summary=make_audit_summary(),
    )

    assert (
        paper.PAPER_RUN_RESULT_SUMMARY_SCHEMA_VERSION
        == PAPER_RUN_RESULT_SUMMARY_SCHEMA_VERSION
    )
    assert paper.PaperRunResultSummary is PaperRunResultSummary
    assert paper.create_paper_run_result_summary is create_paper_run_result_summary
    assert isinstance(summary, PaperRunResultSummary)
