"""Tests for versioned lifecycle proposal and human-review endpoints."""

from copy import deepcopy
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from el_psy_quant.api.app import create_app
from el_psy_quant.api.lifecycle_command_schemas import (
    LifecycleTransitionProposalCommandResponse,
    LifecycleTransitionReviewCommandResponse,
)
from el_psy_quant.api.middleware import REQUEST_ID_HEADER
from el_psy_quant.api.schemas import ApiErrorResponse


def _proposal_payload() -> dict[str, object]:
    return {
        "proposal_id": " proposal-001 ",
        "source_snapshot": {
            "snapshot_id": " snapshot-research-001 ",
            "strategy_id": " moving_average_crossover ",
            "lifecycle_state": " research_review ",
            "rationale": " Research evidence is ready. ",
            "declared_by": " founder ",
            "declared_timestamp": "2026-07-13T13:00:00Z",
            "notes": [" source note 1 ", " source note 2 "],
            "warnings": [" source warning "],
        },
        "target_state": " paper_review ",
        "rationale": " Request paper-review governance. ",
        "evidence_references": [
            {
                "reference_type": "strategy_decision_record",
                "reference_id": " decision-record-001 ",
                "label": " Research decision ",
                "description": None,
            },
            {
                "reference_type": "promotion_record",
                "reference_id": " promotion-record-001 ",
                "label": None,
                "description": " Promotion evidence ",
            },
            {
                "reference_type": "strategy_decision_record",
                "reference_id": " decision-record-001 ",
                "label": None,
                "description": None,
            },
        ],
        "requested_by": " founder ",
        "requested_timestamp": "2026-07-13T13:05:00Z",
        "notes": [" proposal note 1 ", " proposal note 2 "],
        "warnings": [" proposal warning "],
    }


def _normalized_proposal() -> dict[str, object]:
    return {
        "schema_version": 1,
        "proposal_id": "proposal-001",
        "source_snapshot": {
            "schema_version": 1,
            "snapshot_id": "snapshot-research-001",
            "strategy_id": "moving_average_crossover",
            "lifecycle_state": "research_review",
            "rationale": "Research evidence is ready.",
            "declared_by": "founder",
            "declared_timestamp": "2026-07-13T13:00:00+00:00",
            "notes": ["source note 1", "source note 2"],
            "warnings": ["source warning"],
        },
        "target_state": "paper_review",
        "rationale": "Request paper-review governance.",
        "evidence_references": [
            {
                "schema_version": 1,
                "reference_type": "strategy_decision_record",
                "reference_id": "decision-record-001",
                "label": "Research decision",
                "description": None,
            },
            {
                "schema_version": 1,
                "reference_type": "promotion_record",
                "reference_id": "promotion-record-001",
                "label": None,
                "description": "Promotion evidence",
            },
            {
                "schema_version": 1,
                "reference_type": "strategy_decision_record",
                "reference_id": "decision-record-001",
                "label": None,
                "description": None,
            },
        ],
        "requested_by": "founder",
        "requested_timestamp": "2026-07-13T13:05:00+00:00",
        "notes": ["proposal note 1", "proposal note 2"],
        "warnings": ["proposal warning"],
    }


def _review_payload(outcome: str = "approved") -> dict[str, object]:
    return {
        "transition_record_id": " transition-record-001 ",
        "proposal": _proposal_payload(),
        "review_outcome": outcome,
        "rationale": " Human review outcome. ",
        "resulting_snapshot": (
            {
                "snapshot_id": " snapshot-paper-001 ",
                "strategy_id": " moving_average_crossover ",
                "lifecycle_state": " paper_review ",
                "rationale": " Resulting state declared by caller. ",
                "declared_by": " founder ",
                "declared_timestamp": "2026-07-13T13:10:00Z",
                "notes": [" resulting note "],
                "warnings": [" resulting warning "],
            }
            if outcome == "approved"
            else None
        ),
        "reviewed_by": " founder ",
        "reviewed_timestamp": "2026-07-13T13:10:00Z",
        "notes": [" record note 1 ", " record note 2 "],
        "warnings": [" record warning "],
    }


def _assert_request_id(response) -> None:
    header = response.headers[REQUEST_ID_HEADER]
    assert str(UUID(header)) == header
    if response.status_code >= 400:
        error = ApiErrorResponse.model_validate(response.json())
        assert error.request_id == header


def test_complete_normalized_proposal_response_is_exact() -> None:
    response = TestClient(create_app()).post(
        "/api/v1/lifecycle-transition-proposals",
        json=_proposal_payload(),
    )
    expected = {"proposal": _normalized_proposal()}

    assert response.status_code == 200
    assert response.json() == expected
    assert (
        LifecycleTransitionProposalCommandResponse.model_validate(
            response.json()
        ).model_dump()
        == expected
    )
    _assert_request_id(response)


def test_complete_normalized_approved_record_response_is_exact() -> None:
    response = TestClient(create_app()).post(
        "/api/v1/lifecycle-transition-records",
        json=_review_payload(),
    )
    expected = {
        "transition_record": {
            "schema_version": 1,
            "transition_record_id": "transition-record-001",
            "proposal": _normalized_proposal(),
            "review_outcome": "approved",
            "rationale": "Human review outcome.",
            "resulting_snapshot": {
                "schema_version": 1,
                "snapshot_id": "snapshot-paper-001",
                "strategy_id": "moving_average_crossover",
                "lifecycle_state": "paper_review",
                "rationale": "Resulting state declared by caller.",
                "declared_by": "founder",
                "declared_timestamp": "2026-07-13T13:10:00+00:00",
                "notes": ["resulting note"],
                "warnings": ["resulting warning"],
            },
            "reviewed_by": "founder",
            "reviewed_timestamp": "2026-07-13T13:10:00+00:00",
            "notes": ["record note 1", "record note 2"],
            "warnings": ["record warning"],
        }
    }

    assert response.status_code == 200
    assert response.json() == expected
    assert (
        LifecycleTransitionReviewCommandResponse.model_validate(
            response.json()
        ).model_dump()
        == expected
    )
    _assert_request_id(response)


@pytest.mark.parametrize("outcome", ("rejected", "deferred"))
def test_rejected_and_deferred_records_return_null_snapshot(outcome: str) -> None:
    response = TestClient(create_app()).post(
        "/api/v1/lifecycle-transition-records",
        json=_review_payload(outcome),
    )

    assert response.status_code == 200
    record = response.json()["transition_record"]
    assert record["review_outcome"] == outcome
    assert record["resulting_snapshot"] is None
    _assert_request_id(response)


def _unknown_field_payloads() -> tuple[tuple[str, dict[str, object]], ...]:
    proposal_top = _proposal_payload()
    proposal_top["path"] = "C:\\private\\proposal.json"
    proposal_snapshot = _proposal_payload()
    proposal_snapshot["source_snapshot"]["current"] = True  # type: ignore[index]
    proposal_evidence = _proposal_payload()
    proposal_evidence["evidence_references"][0]["artifact_key"] = "private"  # type: ignore[index]
    review_top = _review_payload()
    review_top["execute"] = True
    review_proposal = _review_payload()
    review_proposal["proposal"]["status"] = "private"  # type: ignore[index]
    review_snapshot = _review_payload()
    review_snapshot["resulting_snapshot"]["job_id"] = "private"  # type: ignore[index]
    return (
        ("/api/v1/lifecycle-transition-proposals", proposal_top),
        ("/api/v1/lifecycle-transition-proposals", proposal_snapshot),
        ("/api/v1/lifecycle-transition-proposals", proposal_evidence),
        ("/api/v1/lifecycle-transition-records", review_top),
        ("/api/v1/lifecycle-transition-records", review_proposal),
        ("/api/v1/lifecycle-transition-records", review_snapshot),
    )


@pytest.mark.parametrize("path,payload", _unknown_field_payloads())
def test_unknown_fields_at_every_nested_level_use_validation_error(
    path: str,
    payload: dict[str, object],
) -> None:
    response = TestClient(create_app()).post(path, json=payload)

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "request_validation_error",
        "message": "Request Validation Error",
    }
    assert "private" not in response.text
    _assert_request_id(response)


def _structurally_invalid_payloads() -> tuple[tuple[str, dict[str, object]], ...]:
    missing = _proposal_payload()
    missing.pop("proposal_id")
    wrong_evidence = _proposal_payload()
    wrong_evidence["evidence_references"] = {}
    wrong_notes = _proposal_payload()
    wrong_notes["source_snapshot"]["notes"] = "not-an-array"  # type: ignore[index]
    boolean_string = _proposal_payload()
    boolean_string["target_state"] = True
    review_proposal = _review_payload()
    review_proposal["proposal"] = "proposal-001"
    review_result = _review_payload()
    review_result["resulting_snapshot"] = []
    return (
        ("/api/v1/lifecycle-transition-proposals", missing),
        ("/api/v1/lifecycle-transition-proposals", wrong_evidence),
        ("/api/v1/lifecycle-transition-proposals", wrong_notes),
        ("/api/v1/lifecycle-transition-proposals", boolean_string),
        ("/api/v1/lifecycle-transition-records", review_proposal),
        ("/api/v1/lifecycle-transition-records", review_result),
    )


@pytest.mark.parametrize("path,payload", _structurally_invalid_payloads())
def test_structural_errors_use_request_validation_error(
    path: str,
    payload: dict[str, object],
) -> None:
    response = TestClient(create_app()).post(path, json=payload)

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "request_validation_error",
        "message": "Request Validation Error",
    }
    _assert_request_id(response)


def test_domain_invalid_proposal_uses_exact_sanitized_error() -> None:
    payload = _proposal_payload()
    payload["target_state"] = "private-live-ready"
    response = TestClient(create_app()).post(
        "/api/v1/lifecycle-transition-proposals", json=payload
    )

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "lifecycle_transition_proposal_invalid",
        "message": "Lifecycle transition proposal is invalid",
    }
    assert "private-live-ready" not in response.text
    assert "unsupported" not in response.text
    _assert_request_id(response)


def test_domain_invalid_record_uses_exact_sanitized_error() -> None:
    payload = _review_payload()
    payload["review_outcome"] = "private-automatic-approval"
    response = TestClient(create_app()).post(
        "/api/v1/lifecycle-transition-records", json=payload
    )

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "lifecycle_transition_record_invalid",
        "message": "Lifecycle transition record is invalid",
    }
    assert "private-automatic-approval" not in response.text
    assert "unsupported" not in response.text
    _assert_request_id(response)


@pytest.mark.parametrize(
    "payload",
    (
        {**_review_payload(), "resulting_snapshot": None},
        {
            **_review_payload("rejected"),
            "resulting_snapshot": _review_payload()["resulting_snapshot"],
        },
    ),
)
def test_resulting_snapshot_outcome_rules_use_record_error(
    payload: dict[str, object],
) -> None:
    response = TestClient(create_app()).post(
        "/api/v1/lifecycle-transition-records", json=payload
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == (
        "lifecycle_transition_record_invalid"
    )
    _assert_request_id(response)


def test_repeated_caller_ids_are_independent_across_requests() -> None:
    client = TestClient(create_app())

    proposal_first = client.post(
        "/api/v1/lifecycle-transition-proposals", json=_proposal_payload()
    )
    proposal_second = client.post(
        "/api/v1/lifecycle-transition-proposals", json=_proposal_payload()
    )
    record_first = client.post(
        "/api/v1/lifecycle-transition-records", json=_review_payload()
    )
    record_second = client.post(
        "/api/v1/lifecycle-transition-records", json=_review_payload()
    )

    for first, second in (
        (proposal_first, proposal_second),
        (record_first, record_second),
    ):
        assert first.status_code == second.status_code == 200
        assert first.json() == second.json()
        assert first.headers[REQUEST_ID_HEADER] != second.headers[REQUEST_ID_HEADER]


def test_request_ids_are_server_owned_on_success_and_error() -> None:
    client = TestClient(create_app())
    success = client.post(
        "/api/v1/lifecycle-transition-proposals",
        json=_proposal_payload(),
        headers={REQUEST_ID_HEADER: "caller-owned"},
    )
    invalid = deepcopy(_review_payload())
    invalid["review_outcome"] = "invalid"
    error = client.post(
        "/api/v1/lifecycle-transition-records",
        json=invalid,
        headers={REQUEST_ID_HEADER: "caller-owned"},
    )

    for response in (success, error):
        assert response.headers[REQUEST_ID_HEADER] != "caller-owned"
        _assert_request_id(response)


@pytest.mark.parametrize(
    "path",
    (
        "/api/v1/lifecycle-transition-proposals",
        "/api/v1/lifecycle-transition-records",
    ),
)
def test_get_is_method_not_allowed_and_preserves_allow(path: str) -> None:
    response = TestClient(create_app()).get(path)

    assert response.status_code == 405
    assert response.json()["error"] == {
        "code": "method_not_allowed",
        "message": "Method Not Allowed",
    }
    assert "POST" in response.headers["allow"].split(", ")
    _assert_request_id(response)


def test_openapi_exposes_exactly_two_versioned_lifecycle_command_paths() -> None:
    paths = set(create_app().openapi()["paths"])
    lifecycle_paths = {path for path in paths if "lifecycle-transition" in path}

    assert lifecycle_paths == {
        "/api/v1/lifecycle-transition-proposals",
        "/api/v1/lifecycle-transition-records",
    }
    for forbidden in (
        "/lifecycle-transition-proposals",
        "/api/v1/lifecycle-transition-current",
        "/api/v1/lifecycle-transition-apply",
        "/api/v1/lifecycle-transition-status",
    ):
        assert forbidden not in paths


def test_existing_versioned_endpoints_still_exist() -> None:
    paths = set(create_app().openapi()["paths"])

    assert {
        "/api/v1/health",
        "/api/v1/strategies",
        "/api/v1/research-runs",
        "/api/v1/evidence-manifests",
        "/api/v1/paper-runs",
    } <= paths
