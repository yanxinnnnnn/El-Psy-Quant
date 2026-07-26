"""Versioned read-only Demo Workspace descriptor API coverage."""

import base64
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from el_psy_quant.api.app import create_app
from el_psy_quant.api.demo_workspace_schemas import (
    DemoWorkspaceDescriptorResponse,
)
from el_psy_quant.demo_workspace import install_demo_workspace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_SOURCE = PROJECT_ROOT / "examples" / "demo_workspace"
ALEMBIC_CONFIG = PROJECT_ROOT / "alembic.ini"


@pytest.fixture
def installed_demo(tmp_path: Path) -> Path:
    root = tmp_path / "demo"
    install_demo_workspace(
        source_root=DEMO_SOURCE,
        workspace_root=root,
        workspace_mode="demo",
        alembic_config_path=ALEMBIC_CONFIG,
    )
    return root


def test_descriptor_is_hidden_when_demo_mode_is_disabled(tmp_path: Path) -> None:
    for app in (
        create_app(workspace_mode="standard", demo_workspace_root=tmp_path),
        create_app(workspace_mode="demo"),
    ):
        response = TestClient(app).get("/api/v1/demo-workspace")
        assert response.status_code == 404
        assert response.json()["error"] == {
            "code": "demo_workspace_not_configured",
            "message": "Demo workspace is not configured",
        }


def test_enabled_descriptor_is_valid_path_free_and_ordered(
    installed_demo: Path,
) -> None:
    response = TestClient(
        create_app(workspace_mode="demo", demo_workspace_root=installed_demo)
    ).get("/api/v1/demo-workspace")

    assert response.status_code == 200
    descriptor = DemoWorkspaceDescriptorResponse.model_validate(response.json())
    assert descriptor.schema_version == 3
    assert descriptor.dataset_version == 3
    assert descriptor.dataset_id == "founder-demo-workspace"
    assert descriptor.comparison_candidate_job_ids == [
        "16000000-0000-4000-8000-000000000001",
        "16000000-0000-4000-8000-000000000002",
    ]
    assert len(set(descriptor.comparison_candidate_job_ids)) == 2
    assert [item.job_id for item in descriptor.paper_jobs] == (
        descriptor.comparison_candidate_job_ids
    )
    assert descriptor.paper_job_submission_example.request.run_id == (
        "demo-founder-submission-example"
    )
    assert descriptor.portfolio_review_example.create_idempotency_key == (
        "demo-portfolio-review-create-v1"
    )
    assert descriptor.portfolio_review_example.request.review_id == (
        "demo-portfolio-review-001"
    )
    assert descriptor.portfolio_review_example.request.source.source_id == (
        "demo-portfolio-review-source-001"
    )
    assert descriptor.paper_account.account_id == "demo-paper-account-001"
    assert descriptor.paper_account.head_version == 5
    assert descriptor.paper_account.event_types == [
        "account_created",
        "cash_movement_posted",
        "position_adjustment_posted",
        "account_frozen",
        "account_reactivated",
    ]
    assert (
        descriptor.paper_account.snapshot_id
        == "demo-paper-account-snapshot-001"
    )
    assert (
        descriptor.paper_account.reconciliation_id
        == "demo-paper-account-reconciliation-001"
    )
    assert str(installed_demo) not in response.text
    assert "paper_run_artifact.json" not in response.text


def test_enabled_but_invalid_workspace_is_bounded_503(tmp_path: Path) -> None:
    root = tmp_path / "broken-demo"
    root.mkdir()
    response = TestClient(
        create_app(workspace_mode="demo", demo_workspace_root=root)
    ).get("/api/v1/demo-workspace")

    assert response.status_code == 503
    assert response.json()["error"] == {
        "code": "demo_workspace_unavailable",
        "message": "Demo workspace is unavailable",
    }
    assert str(root) not in response.text


def test_tampered_descriptor_is_rejected_as_unavailable(
    installed_demo: Path,
) -> None:
    descriptor_path = installed_demo / "workspace-descriptor.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    candidate = descriptor["comparison_candidate_job_ids"][0]
    descriptor["comparison_candidate_job_ids"] = [candidate, candidate]
    descriptor_path.write_text(json.dumps(descriptor), encoding="utf-8")

    response = TestClient(
        create_app(workspace_mode="demo", demo_workspace_root=installed_demo)
    ).get("/api/v1/demo-workspace")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "demo_workspace_unavailable"


def test_descriptor_preserves_founder_authentication(installed_demo: Path) -> None:
    client = TestClient(
        create_app(
            workspace_mode="demo",
            demo_workspace_root=installed_demo,
            founder_username="founder",
            founder_password="demo-secret",
        )
    )
    unauthorized = client.get("/api/v1/demo-workspace")
    token = base64.b64encode(b"founder:demo-secret").decode("ascii")
    authorized = client.get(
        "/api/v1/demo-workspace",
        headers={"Authorization": f"Basic {token}"},
    )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
    assert "demo-secret" not in unauthorized.text + authorized.text


def test_openapi_contains_only_the_versioned_read_endpoint() -> None:
    document = create_app().openapi()
    path = document["paths"]["/api/v1/demo-workspace"]

    assert set(path) == {"get"}
    assert "/demo-workspace" not in document["paths"]
