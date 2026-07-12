"""Tests for versioned configured evidence-manifest endpoints."""

import json
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from el_psy_quant.api.app import (
    EVIDENCE_ARTIFACT_ROOT_ENV,
    RESEARCH_ARTIFACT_ROOT_ENV,
    create_app,
)
from el_psy_quant.api.evidence_schemas import (
    EvidenceManifestListResponse,
    ReportArtifactManifestDetailResponse,
    StrategyDecisionManifestDetailResponse,
    StrategyReviewWorkflowManifestDetailResponse,
)
from el_psy_quant.api.middleware import REQUEST_ID_HEADER
from el_psy_quant.api.schemas import ApiErrorResponse
from el_psy_quant.decision_governance import (
    create_strategy_decision_manifest,
    create_strategy_decision_reference,
)
from el_psy_quant.report_artifacts import (
    create_report_artifact_manifest,
    create_report_artifact_reference,
)
from el_psy_quant.strategy_review import (
    create_strategy_review_workflow_manifest,
    create_strategy_review_workflow_reference,
)

CATEGORIES = {
    "strategy_decision_manifest": "strategy-decisions",
    "report_artifact_manifest": "report-artifacts",
    "strategy_review_workflow_manifest": "strategy-review",
}


def _payload(manifest_type: str) -> dict[str, object]:
    if manifest_type == "strategy_decision_manifest":
        reference = create_strategy_decision_reference(
            reference_type="strategy_decision_record",
            reference_id="decision-record-1",
            label="Decision",
        )
        return create_strategy_decision_manifest(
            manifest_id="decision manifest 001",
            record_references=[reference],
            created_by="founder",
            created_timestamp="2026-07-12T12:00:00Z",
            description="Human-reviewed decision evidence",
        ).to_dict()
    if manifest_type == "report_artifact_manifest":
        reference = create_report_artifact_reference(
            reference_type="report_artifact_summary",
            reference_id="report-1",
        )
        return create_report_artifact_manifest(
            manifest_id="report manifest 001",
            references=[reference],
            label="Review report",
            created_timestamp="caller timestamp",
        ).to_dict()
    reference = create_strategy_review_workflow_reference(
        reference_type="strategy_lifecycle_state_snapshot",
        reference_id="snapshot-1",
    )
    return create_strategy_review_workflow_manifest(
        manifest_id="workflow manifest 001",
        state_snapshot_references=[reference],
        created_timestamp="2026-07-12T12:00:00Z",
    ).to_dict()


def _write(root: Path, manifest_type: str, key: str) -> Path:
    path = root / CATEGORIES[manifest_type] / f"{key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_payload(manifest_type)), encoding="utf-8")
    return path


def _assert_request_id(response) -> None:
    request_id = response.headers[REQUEST_ID_HEADER]
    assert str(UUID(request_id)) == request_id
    if response.status_code >= 400:
        error = ApiErrorResponse.model_validate(response.json())
        assert error.request_id == request_id


def test_factory_environment_override_independence_and_blank_values(
    tmp_path: Path, monkeypatch
) -> None:
    environment = tmp_path / "environment"
    override = tmp_path / "override"
    research = tmp_path / "research"
    monkeypatch.setenv(EVIDENCE_ARTIFACT_ROOT_ENV, str(environment))
    monkeypatch.setenv(RESEARCH_ARTIFACT_ROOT_ENV, str(research))

    environment_app = create_app()
    override_app = create_app(evidence_artifact_root=override)
    blank_app = create_app(evidence_artifact_root="  ")

    assert environment_app.state.evidence_artifact_root == environment
    assert environment_app.state.research_artifact_root == research
    assert override_app.state.evidence_artifact_root == override
    assert override_app.state.research_artifact_root == research
    assert blank_app.state.evidence_artifact_root is None
    assert environment_app.state.evidence_artifact_root != override_app.state.evidence_artifact_root


def test_unset_and_blank_evidence_environment_are_unconfigured(monkeypatch) -> None:
    monkeypatch.delenv(EVIDENCE_ARTIFACT_ROOT_ENV, raising=False)
    assert create_app().state.evidence_artifact_root is None
    monkeypatch.setenv(EVIDENCE_ARTIFACT_ROOT_ENV, "   ")
    assert create_app().state.evidence_artifact_root is None


def test_application_construction_does_not_touch_filesystem(
    tmp_path: Path, monkeypatch
) -> None:
    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("filesystem access during application construction")

    monkeypatch.setattr(Path, "resolve", forbidden)
    monkeypatch.setattr(Path, "exists", forbidden)
    monkeypatch.setattr(Path, "is_dir", forbidden)
    app = create_app(evidence_artifact_root=tmp_path / "not-checked")
    assert app.state.evidence_artifact_root == tmp_path / "not-checked"


def test_unavailable_and_nul_roots_have_stable_sanitized_503() -> None:
    for configured_root in (None, "invalid\0root"):
        response = TestClient(
            create_app(evidence_artifact_root=configured_root)
        ).get("/api/v1/evidence-manifests")
        assert response.status_code == 503
        assert response.json()["error"] == {
            "code": "evidence_artifact_root_unavailable",
            "message": "Evidence artifact root is unavailable",
        }
        assert "invalid" not in response.text
        _assert_request_id(response)


def test_other_endpoints_are_independent_from_evidence_root(tmp_path: Path) -> None:
    client = TestClient(create_app(research_artifact_root=tmp_path))
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/strategies").status_code == 200
    assert client.get("/api/v1/research-runs").status_code == 200
    assert client.get("/api/v1/evidence-manifests").status_code == 503

    evidence_client = TestClient(create_app(evidence_artifact_root=tmp_path))
    assert evidence_client.get("/api/v1/evidence-manifests").status_code == 200
    assert evidence_client.get("/api/v1/research-runs").status_code == 503


def test_list_contract_is_deterministic_explicit_and_path_free(tmp_path: Path) -> None:
    _write(tmp_path, "strategy_review_workflow_manifest", "workflow-1")
    _write(tmp_path, "report_artifact_manifest", "report-1")
    _write(tmp_path, "strategy_decision_manifest", "decision-1")
    response = TestClient(create_app(evidence_artifact_root=tmp_path)).get(
        "/api/v1/evidence-manifests",
        headers={REQUEST_ID_HEADER: "caller-owned"},
    )

    assert response.status_code == 200
    parsed = EvidenceManifestListResponse.model_validate(response.json())
    assert [item.manifest_type for item in parsed.manifests] == [
        "strategy_decision_manifest",
        "report_artifact_manifest",
        "strategy_review_workflow_manifest",
    ]
    assert [item.reference_count for item in parsed.manifests] == [1, 1, 1]
    assert str(tmp_path) not in response.text
    assert response.headers[REQUEST_ID_HEADER] != "caller-owned"
    _assert_request_id(response)


@pytest.mark.parametrize(
    ("manifest_type", "schema"),
    (
        ("strategy_decision_manifest", StrategyDecisionManifestDetailResponse),
        ("report_artifact_manifest", ReportArtifactManifestDetailResponse),
        (
            "strategy_review_workflow_manifest",
            StrategyReviewWorkflowManifestDetailResponse,
        ),
    ),
)
def test_each_detail_contract_uses_explicit_discriminator_and_schema(
    tmp_path: Path, manifest_type: str, schema
) -> None:
    _write(tmp_path, manifest_type, "artifact_1")
    response = TestClient(create_app(evidence_artifact_root=tmp_path)).get(
        f"/api/v1/evidence-manifests/{manifest_type}/artifact_1"
    )
    assert response.status_code == 200
    detail = schema.model_validate(response.json())
    assert detail.manifest_type == manifest_type
    assert detail.artifact_key == "artifact_1"
    assert str(tmp_path) not in response.text
    _assert_request_id(response)


@pytest.mark.parametrize(
    "path",
    (
        "/api/v1/evidence-manifests/unsupported/key",
        "/api/v1/evidence-manifests/strategy_decision_manifest/missing",
        "/api/v1/evidence-manifests/strategy_decision_manifest/key.json",
        "/api/v1/evidence-manifests/strategy_decision_manifest/Key%20",
        "/api/v1/evidence-manifests/STRATEGY_DECISION_MANIFEST/key",
    ),
)
def test_invalid_or_missing_selection_has_stable_404(tmp_path: Path, path: str) -> None:
    response = TestClient(create_app(evidence_artifact_root=tmp_path)).get(path)
    assert response.status_code == 404
    assert response.json()["error"] == {
        "code": "evidence_manifest_not_found",
        "message": "Evidence manifest not found",
    }
    assert str(tmp_path) not in response.text
    _assert_request_id(response)


def test_malformed_artifact_has_sanitized_422_and_request_id(tmp_path: Path) -> None:
    path = tmp_path / "strategy-decisions" / "secret.json"
    path.parent.mkdir()
    path.write_text("private malformed json", encoding="utf-8")
    client = TestClient(create_app(evidence_artifact_root=tmp_path))

    for url in (
        "/api/v1/evidence-manifests",
        "/api/v1/evidence-manifests/strategy_decision_manifest/secret",
    ):
        response = client.get(url)
        assert response.status_code == 422
        assert response.json()["error"] == {
            "code": "evidence_artifact_invalid",
            "message": "Evidence artifact is invalid",
        }
        assert "private" not in response.text
        assert str(tmp_path) not in response.text
        _assert_request_id(response)


def test_only_two_versioned_evidence_routes_and_no_raw_or_download() -> None:
    paths = set(create_app().openapi()["paths"])
    evidence_paths = {path for path in paths if "evidence-manifests" in path}
    assert evidence_paths == {
        "/api/v1/evidence-manifests",
        "/api/v1/evidence-manifests/{manifest_type}/{artifact_key}",
    }
    assert not any("raw" in path or "download" in path for path in paths)
