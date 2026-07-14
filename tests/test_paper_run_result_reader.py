"""Tests for strict saved paper-run result-summary recovery reads."""

import copy
import json
from pathlib import Path

import pytest

from el_psy_quant.configured_paper import run_paper_workflow_request
from el_psy_quant.paper import (
    ValidatedPaperRunResultSummary,
    create_paper_account_state,
    create_paper_run_request,
    read_paper_run_result_summary_file,
    read_paper_trading_artifact_file,
    validate_paper_run_recovery_consistency,
    validate_paper_run_result_summary_payload,
)


def _request(run_id: str = "reader-run"):
    starting = create_paper_account_state(
        timestamp="2026-07-14T12:00:00Z",
        starting_cash=1_000,
        current_cash=1_000,
        positions={},
    )
    ending = create_paper_account_state(
        timestamp="2026-07-14T12:30:00Z",
        starting_cash=1_000,
        current_cash=1_000,
        positions={},
    )
    return create_paper_run_request(
        run_id=run_id,
        created_timestamp="2026-07-14T12:45:00Z",
        starting_account_state=starting,
        ending_account_state=ending,
        orders=(),
        fills=(),
    )


def _workflow(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    result = run_paper_workflow_request(request=_request(), run_dir=run_dir)
    payload = json.loads(
        result.paper_run_result_summary_path.read_text(encoding="utf-8")
    )
    return result, payload


def test_strict_reader_returns_validated_compact_value(tmp_path: Path) -> None:
    workflow, payload = _workflow(tmp_path)

    summary = read_paper_run_result_summary_file(
        workflow.paper_run_result_summary_path
    )

    assert isinstance(summary, ValidatedPaperRunResultSummary)
    assert summary.run_id == "reader-run"
    assert summary.audit_summary.to_dict() == payload["audit"]


@pytest.mark.parametrize(
    "mutation",
    (
        lambda payload: payload.pop("audit"),
        lambda payload: payload.update({"unexpected": 1}),
        lambda payload: payload["request"].update({"unexpected": 1}),
        lambda payload: payload.update({"schema_version": 2}),
        lambda payload: payload["artifact"].update({"path": ""}),
        lambda payload: payload["audit"].update({"order_count": True}),
        lambda payload: payload["audit"].update({"starting_cash": float("nan")}),
        lambda payload: payload["audit"].update({"ending_cash": float("inf")}),
    ),
)
def test_strict_payload_rejects_missing_unexpected_malformed_and_nonfinite(
    tmp_path: Path,
    mutation,
) -> None:
    _, original = _workflow(tmp_path)
    payload = copy.deepcopy(original)
    mutation(payload)

    with pytest.raises(ValueError, match="result summary is invalid"):
        validate_paper_run_result_summary_payload(payload)


@pytest.mark.parametrize(
    "document",
    (
        "{",
        '{"schema_version":1,"schema_version":1}',
        '{"schema_version":NaN}',
    ),
)
def test_reader_rejects_invalid_duplicate_and_nonstandard_json(
    tmp_path: Path,
    document: str,
) -> None:
    path = tmp_path / "summary.json"
    path.write_text(document, encoding="utf-8")

    with pytest.raises(ValueError):
        read_paper_run_result_summary_file(path)


def test_recovery_consistency_accepts_exact_saved_outputs(tmp_path: Path) -> None:
    workflow, _ = _workflow(tmp_path)
    artifact = read_paper_trading_artifact_file(workflow.paper_run_artifact_path)
    summary = read_paper_run_result_summary_file(
        workflow.paper_run_result_summary_path
    )

    validate_paper_run_recovery_consistency(
        request=workflow.request,
        artifact_payload=artifact,
        summary=summary,
        expected_artifact_path=workflow.paper_run_artifact_path,
    )


@pytest.mark.parametrize(
    "field",
    ("run_id", "request_timestamp", "artifact_timestamp", "path", "audit"),
)
def test_recovery_consistency_rejects_each_cross_file_mismatch(
    tmp_path: Path,
    field: str,
) -> None:
    workflow, payload = _workflow(tmp_path)
    artifact = read_paper_trading_artifact_file(workflow.paper_run_artifact_path)
    if field == "run_id":
        payload["run_id"] = "other"
    elif field == "request_timestamp":
        payload["request"]["created_timestamp"] = "2026-07-14T12:46:00+00:00"
    elif field == "artifact_timestamp":
        payload["artifact"]["created_timestamp"] = "2026-07-14T12:46:00+00:00"
    elif field == "path":
        payload["artifact"]["path"] = str(tmp_path / "other.json")
    else:
        payload["audit"]["order_count"] = 1
    summary = validate_paper_run_result_summary_payload(payload)

    with pytest.raises(ValueError, match="inconsistent"):
        validate_paper_run_recovery_consistency(
            request=workflow.request,
            artifact_payload=artifact,
            summary=summary,
            expected_artifact_path=workflow.paper_run_artifact_path,
        )


def test_reader_requires_explicit_existing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        read_paper_run_result_summary_file(tmp_path / "missing.json")
    with pytest.raises(ValueError):
        read_paper_run_result_summary_file(tmp_path)
