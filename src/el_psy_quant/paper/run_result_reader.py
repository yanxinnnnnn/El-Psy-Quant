"""Strict local reader and recovery consistency checks for result summaries."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any, Literal, cast

import pandas as pd

from el_psy_quant.paper.artifact import PAPER_TRADING_ARTIFACT_SCHEMA_VERSION
from el_psy_quant.paper.audit import (
    PaperTradingArtifactAuditSummary,
    create_paper_trading_artifact_audit_summary,
)
from el_psy_quant.paper.file_contract import PAPER_TRADING_ARTIFACT_FILE_ENCODING
from el_psy_quant.paper.reader import validate_paper_trading_artifact_file_payload
from el_psy_quant.paper.run_request import (
    PAPER_RUN_REQUEST_SCHEMA_VERSION,
    PaperRunRequest,
)
from el_psy_quant.paper.run_result import PAPER_RUN_RESULT_SUMMARY_SCHEMA_VERSION

_TOP_LEVEL_FIELDS = {"schema_version", "run_id", "request", "artifact", "audit"}
_REQUEST_FIELDS = {"schema_version", "created_timestamp"}
_ARTIFACT_FIELDS = {"schema_version", "created_timestamp", "path"}
_AUDIT_FIELDS = {
    "schema_version",
    "created_timestamp",
    "session_start_timestamp",
    "session_end_timestamp",
    "starting_cash",
    "ending_cash",
    "cash_change",
    "order_count",
    "fill_count",
    "starting_position_count",
    "ending_position_count",
    "position_change_count",
}


def _invalid_summary() -> ValueError:
    return ValueError("paper run result summary is invalid")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _invalid_summary()
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    raise _invalid_summary()


def _object(value: object, fields: set[str]) -> dict[str, Any]:
    if type(value) is not dict or set(value) != fields:
        raise _invalid_summary()
    return cast(dict[str, Any], value)


def _version(value: object, expected: int) -> int:
    if type(value) is not int or value != expected:
        raise _invalid_summary()
    return value


def _text(value: object) -> str:
    if type(value) is not str or not value:
        raise _invalid_summary()
    return value


def _timestamp(value: object) -> str:
    text = _text(value)
    try:
        timestamp = pd.Timestamp(text)
    except (TypeError, ValueError) as exc:
        raise _invalid_summary() from exc
    if pd.isna(timestamp) or timestamp.isoformat() != text:
        raise _invalid_summary()
    return text


def _finite_number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise _invalid_summary()
    normalized = float(value)
    if not math.isfinite(normalized):
        raise _invalid_summary()
    return normalized


def _count(value: object) -> int:
    if type(value) is not int or value < 0:
        raise _invalid_summary()
    return value


def _audit(value: object) -> PaperTradingArtifactAuditSummary:
    payload = _object(value, _AUDIT_FIELDS)
    return PaperTradingArtifactAuditSummary(
        schema_version=_version(
            payload["schema_version"],
            PAPER_TRADING_ARTIFACT_SCHEMA_VERSION,
        ),
        created_timestamp=_timestamp(payload["created_timestamp"]),
        session_start_timestamp=_timestamp(payload["session_start_timestamp"]),
        session_end_timestamp=_timestamp(payload["session_end_timestamp"]),
        starting_cash=_finite_number(payload["starting_cash"]),
        ending_cash=_finite_number(payload["ending_cash"]),
        cash_change=_finite_number(payload["cash_change"]),
        order_count=_count(payload["order_count"]),
        fill_count=_count(payload["fill_count"]),
        starting_position_count=_count(payload["starting_position_count"]),
        ending_position_count=_count(payload["ending_position_count"]),
        position_change_count=_count(payload["position_change_count"]),
    )


@dataclass(frozen=True)
class ValidatedPaperRunResultSummary:
    """Strict compact value read from one saved result-summary file."""

    schema_version: Literal[1]
    run_id: str
    request_schema_version: Literal[1]
    request_created_timestamp: str
    artifact_schema_version: Literal[1]
    artifact_created_timestamp: str
    artifact_path: str
    audit_summary: PaperTradingArtifactAuditSummary


def validate_paper_run_result_summary_payload(
    payload: object,
) -> ValidatedPaperRunResultSummary:
    """Validate the exact emitted paper result-summary shape."""
    root = _object(payload, _TOP_LEVEL_FIELDS)
    request = _object(root["request"], _REQUEST_FIELDS)
    artifact = _object(root["artifact"], _ARTIFACT_FIELDS)
    return ValidatedPaperRunResultSummary(
        schema_version=_version(
            root["schema_version"],
            PAPER_RUN_RESULT_SUMMARY_SCHEMA_VERSION,
        ),  # type: ignore[arg-type]
        run_id=_text(root["run_id"]),
        request_schema_version=_version(
            request["schema_version"],
            PAPER_RUN_REQUEST_SCHEMA_VERSION,
        ),  # type: ignore[arg-type]
        request_created_timestamp=_timestamp(request["created_timestamp"]),
        artifact_schema_version=_version(
            artifact["schema_version"],
            PAPER_TRADING_ARTIFACT_SCHEMA_VERSION,
        ),  # type: ignore[arg-type]
        artifact_created_timestamp=_timestamp(artifact["created_timestamp"]),
        artifact_path=_text(artifact["path"]),
        audit_summary=_audit(root["audit"]),
    )


def read_paper_run_result_summary_file(
    source_path: str | Path,
) -> ValidatedPaperRunResultSummary:
    """Read one explicit existing UTF-8 JSON result-summary file."""
    if not isinstance(source_path, str | Path):
        raise ValueError("source_path must be a str or pathlib.Path")
    if isinstance(source_path, str) and not source_path.strip():
        raise ValueError("source_path must not be empty")
    path = Path(source_path)
    if not path.exists():
        raise ValueError("source_path file does not exist")
    if path.is_dir():
        raise ValueError("source_path must be a file path, not a directory")
    try:
        payload = json.loads(
            path.read_text(encoding=PAPER_TRADING_ARTIFACT_FILE_ENCODING),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
        return validate_paper_run_result_summary_payload(payload)
    except (json.JSONDecodeError, UnicodeError, TypeError, ValueError) as exc:
        if isinstance(exc, ValueError) and str(exc) == str(_invalid_summary()):
            raise
        raise _invalid_summary() from exc


def _require_finite_json(value: object) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("paper artifact payload contains a non-finite number")
    if isinstance(value, dict):
        for nested in value.values():
            _require_finite_json(nested)
    elif isinstance(value, list):
        for nested in value:
            _require_finite_json(nested)


def validate_paper_run_recovery_consistency(
    *,
    request: PaperRunRequest,
    artifact_payload: object,
    summary: ValidatedPaperRunResultSummary,
    expected_artifact_path: str | Path,
) -> None:
    """Confirm saved outputs match each other, the request, and reserved path."""
    if type(request) is not PaperRunRequest:
        raise ValueError("request must be a PaperRunRequest")
    if type(summary) is not ValidatedPaperRunResultSummary:
        raise ValueError("summary must be a ValidatedPaperRunResultSummary")
    artifact = validate_paper_trading_artifact_file_payload(artifact_payload)
    _require_finite_json(artifact)
    artifact_created = _timestamp(artifact["created_timestamp"])
    expected_path = Path(expected_artifact_path).resolve()
    if (
        summary.run_id != request.run_id
        or summary.request_created_timestamp != request.created_timestamp.isoformat()
        or summary.artifact_schema_version != artifact["schema_version"]
        or summary.artifact_created_timestamp != artifact_created
        or Path(summary.artifact_path).resolve() != expected_path
    ):
        raise ValueError("paper run outputs are inconsistent")
    recomputed_audit = create_paper_trading_artifact_audit_summary(artifact)
    if summary.audit_summary.to_dict() != recomputed_audit.to_dict():
        raise ValueError("paper run output audit facts are inconsistent")
