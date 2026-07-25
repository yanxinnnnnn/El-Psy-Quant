from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from el_psy_quant.api.app import create_app
from el_psy_quant.api.dependencies import (
    get_paper_account_application_service,
)
from el_psy_quant.api.middleware import REQUEST_ID_HEADER
from el_psy_quant.api.observability import PRODUCT_LOGGER_NAME
from el_psy_quant.application import PaperAccountApplicationService
from el_psy_quant.paper_account import ApprovedPortfolioReviewReference
from el_psy_quant.persistence.paper_account_repository import (
    SqlAlchemyPaperAccountRepository,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUTH = ("paper-founder", "paper-secret")


@pytest.fixture(autouse=True)
def _enable_product_logger_after_alembic() -> None:
    logging.getLogger(PRODUCT_LOGGER_NAME).disabled = False


class _Authority:
    def __init__(self) -> None:
        self.counter = 0

    def id(self, kind: str) -> str:
        self.counter += 1
        return f"{kind}-{self.counter:04d}"

    def clock(self) -> datetime:
        self.counter += 1
        return datetime(2026, 7, 25, tzinfo=timezone.utc) + timedelta(
            seconds=self.counter
        )


def _approved_reference() -> ApprovedPortfolioReviewReference:
    reference = object.__new__(ApprovedPortfolioReviewReference)
    for name, value in {
        "review_id": "approved-review",
        "source_id": "approved-source",
        "source_digest": "1" * 64,
        "analysis_digest": "2" * 64,
        "decision_id": "approved-decision",
        "decision_digest": "3" * 64,
        "outcome": "approved",
    }.items():
        object.__setattr__(reference, name, value)
    return reference


@pytest.fixture
def configured_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    database_path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    command.upgrade(Config(str(PROJECT_ROOT / "alembic.ini")), "head")
    application = create_app(
        product_database_path=database_path,
        founder_username=AUTH[0],
        founder_password=AUTH[1],
    )
    authority = _Authority()
    service = PaperAccountApplicationService(
        session_factory=application.state.product_session_factory,
        clock=authority.clock,
        id_factory=authority.id,
        approved_review_verifier=lambda review_id: (
            _approved_reference()
            if review_id == "approved-review"
            else (_ for _ in ()).throw(ValueError("invalid review"))
        ),
    )
    application.dependency_overrides[
        get_paper_account_application_service
    ] = lambda: service
    application.state.paper_account_test_service = service
    logging.getLogger(PRODUCT_LOGGER_NAME).disabled = False
    return application


def _error(response, status: int, code: str) -> None:
    assert response.status_code == status, response.text
    body = response.json()
    assert body["error"]["code"] == code
    request_id = response.headers[REQUEST_ID_HEADER]
    assert str(UUID(request_id)) == request_id == body["request_id"]
    rendered = response.text
    for forbidden in (
        "Traceback",
        "SELECT ",
        "paper_account_events",
        "product.sqlite3",
    ):
        assert forbidden not in rendered


def _create(
    client: TestClient,
    *,
    key: str = "create-account",
    display_name: str = "Founder account",
    initial_cash: object = "100",
):
    return client.post(
        "/api/v1/paper-accounts",
        auth=AUTH,
        headers={"Idempotency-Key": key},
        json={
            "display_name": display_name,
            "base_currency": "USD",
            "initial_cash": initial_cash,
            "actor": "founder",
        },
    )


def _anchors(body: dict[str, object]) -> dict[str, object]:
    account = body["account"]
    assert isinstance(account, dict)
    return {
        "expected_account_version": account["head_version"],
        "expected_head_event_id": account["head_event_id"],
        "expected_head_chain_digest": account["head_chain_digest"],
        "actor": "founder",
        "reason": "bounded evidence",
    }


def test_exact_route_inventory_authentication_and_side_effect_free_openapi(
    configured_app,
    tmp_path: Path,
) -> None:
    paths = configured_app.openapi()["paths"]
    exact = {
        (method.upper(), path)
        for path, operations in paths.items()
        if path.startswith("/api/v1/paper-accounts")
        for method in operations
    }
    assert exact == {
        ("POST", "/api/v1/paper-accounts"),
        ("GET", "/api/v1/paper-accounts"),
        ("GET", "/api/v1/paper-accounts/{account_id}"),
        ("GET", "/api/v1/paper-accounts/{account_id}/ledger"),
        (
            "POST",
            "/api/v1/paper-accounts/{account_id}/cash-movements",
        ),
        (
            "POST",
            "/api/v1/paper-accounts/{account_id}/position-adjustments",
        ),
        (
            "POST",
            "/api/v1/paper-accounts/{account_id}/evidence-links",
        ),
        ("POST", "/api/v1/paper-accounts/{account_id}/lifecycle"),
        ("POST", "/api/v1/paper-accounts/{account_id}/snapshots"),
        (
            "POST",
            "/api/v1/paper-accounts/{account_id}/reconciliations",
        ),
    }
    assert "/paper-accounts" not in paths
    assert "/api/v1/paper-account" not in paths
    assert not any("rebuild" in path for _, path in exact)

    with TestClient(configured_app) as client:
        for method, path in sorted(exact):
            concrete = path.replace("{account_id}", "missing-account")
            response = getattr(client, method.lower())(concrete)
            _error(response, 401, "founder_authentication_required")

    absent = tmp_path / "openapi-must-not-create.sqlite3"
    app = create_app(product_database_path=absent)
    app.openapi()
    assert not absent.exists()
    with TestClient(app) as client:
        _error(
            client.get("/api/v1/paper-accounts"),
            503,
            "product_database_unavailable",
        )

    incompatible = tmp_path / "incompatible.sqlite3"
    incompatible.touch()
    with TestClient(
        create_app(product_database_path=incompatible)
    ) as client:
        _error(
            client.get("/api/v1/paper-accounts"),
            503,
            "paper_account_schema_incompatible",
        )


def test_create_replay_list_detail_and_bounded_pagination(configured_app) -> None:
    with TestClient(configured_app) as client:
        missing_key = client.post(
            "/api/v1/paper-accounts",
            auth=AUTH,
            json={
                "display_name": "Missing key",
                "base_currency": "USD",
                "initial_cash": "1",
                "actor": "founder",
            },
        )
        _error(missing_key, 422, "request_validation_error")

        first = _create(client)
        assert first.status_code == 201, first.text
        first_body = first.json()
        assert first_body["replayed"] is False
        assert (
            first_body["request_id"]
            == first.headers[REQUEST_ID_HEADER]
        )
        assert first_body["account"]["head_version"] == 1
        assert first_body["projection"]["cash_balance"] == "100"
        assert first_body["projection"]["available_cash"] == "100"
        assert first_body["projection"]["positions"] == []
        assert first_body["event"]["event_type"] == "account_created"
        assert first_body["event"]["cash_postings"][0]["signed_amount"] == "100"
        assert "command_idempotency_key" not in first_body["event"]
        assert "idempotency" not in first.text.lower()

        replay = _create(client)
        assert replay.status_code == 200
        assert replay.json()["replayed"] is True
        for field in ("account", "event", "projection"):
            assert replay.json()[field] == first_body[field]

        conflict = _create(client, display_name="Changed intent")
        _error(conflict, 409, "paper_account_idempotency_conflict")

        second = _create(
            client,
            key="create-second",
            display_name="Second account",
            initial_cash="20",
        )
        third = _create(
            client,
            key="create-third",
            display_name="Third account",
            initial_cash="30",
        )
        assert second.status_code == third.status_code == 201

        page_one = client.get(
            "/api/v1/paper-accounts?limit=2",
            auth=AUTH,
        )
        assert page_one.status_code == 200
        assert len(page_one.json()["items"]) == 2
        cursor = page_one.json()["next_cursor"]
        assert cursor and "product.sqlite3" not in cursor
        page_two = client.get(
            "/api/v1/paper-accounts",
            params={"limit": 2, "cursor": cursor},
            auth=AUTH,
        )
        assert page_two.status_code == 200
        all_ids = [
            item["account_id"]
            for item in (
                page_one.json()["items"] + page_two.json()["items"]
            )
        ]
        assert len(all_ids) == len(set(all_ids)) == 3
        assert page_two.json()["next_cursor"] is None

        tampered = f"{cursor[:-1]}{'A' if cursor[-1] != 'A' else 'B'}"
        _error(
            client.get(
                "/api/v1/paper-accounts",
                params={"cursor": tampered},
                auth=AUTH,
            ),
            422,
            "request_validation_error",
        )

        detail = client.get(
            f"/api/v1/paper-accounts/{first_body['account']['account_id']}",
            auth=AUTH,
        )
        assert detail.status_code == 200
        assert detail.json()["account"] == first_body["account"]
        assert detail.json()["projection"] == first_body["projection"]
        _error(
            client.get(
                "/api/v1/paper-accounts/missing-account",
                auth=AUTH,
            ),
            404,
            "paper_account_not_found",
        )


def test_ledger_mutations_errors_and_exact_json_scalars(configured_app) -> None:
    with TestClient(configured_app) as client:
        created = _create(client).json()
        account_id = created["account"]["account_id"]
        cash = client.post(
            f"/api/v1/paper-accounts/{account_id}/cash-movements",
            auth=AUTH,
            headers={"Idempotency-Key": "deposit"},
            json={
                "expected_account_version": 1,
                "actor": "founder",
                "reason": "fund account",
                "movement_type": "deposit",
                "requested_amount": "5.25",
            },
        )
        assert cash.status_code == 201, cash.text
        assert cash.json()["projection"]["cash_balance"] == "105.25"
        assert (
            cash.json()["event"]["cash_postings"][0]["signed_amount"]
            == "5.25"
        )

        position = client.post(
            f"/api/v1/paper-accounts/{account_id}/position-adjustments",
            auth=AUTH,
            headers={"Idempotency-Key": "position"},
            json={
                "expected_account_version": 2,
                "actor": "founder",
                "reason": "opening authority",
                "symbol": "SYN",
                "adjustment_category": "opening_balance",
                "signed_quantity_delta": "2",
                "signed_cost_basis_delta": "10.5",
            },
        )
        assert position.status_code == 201, position.text
        assert position.json()["projection"]["positions"] == [
            {
                "schema_version": 1,
                "symbol": "SYN",
                "quantity": "2",
                "aggregate_cost_basis": "10.5",
                "average_unit_cost": "5.25",
                "average_unit_cost_is_rounded": False,
            }
        ]

        first_page = client.get(
            f"/api/v1/paper-accounts/{account_id}/ledger",
            params={"limit": 2},
            auth=AUTH,
        )
        assert first_page.status_code == 200, first_page.text
        assert [
            event["sequence_number"] for event in first_page.json()["events"]
        ] == [1, 2]
        assert first_page.json()["next_after_sequence_number"] == 2
        second_page = client.get(
            f"/api/v1/paper-accounts/{account_id}/ledger",
            params={"after_sequence_number": 2, "limit": 2},
            auth=AUTH,
        )
        assert second_page.status_code == 200, second_page.text
        assert [
            event["sequence_number"] for event in second_page.json()["events"]
        ] == [3]
        assert second_page.json()["next_after_sequence_number"] is None

        noncanonical = client.post(
            f"/api/v1/paper-accounts/{account_id}/cash-movements",
            auth=AUTH,
            headers={"Idempotency-Key": "bad-decimal"},
            json={
                "expected_account_version": 3,
                "actor": "founder",
                "reason": "invalid",
                "movement_type": "deposit",
                "requested_amount": "01.0",
            },
        )
        _error(noncanonical, 422, "paper_account_invalid_decimal")

        json_float = client.post(
            f"/api/v1/paper-accounts/{account_id}/cash-movements",
            auth=AUTH,
            headers={"Idempotency-Key": "float"},
            json={
                "expected_account_version": 3,
                "actor": "founder",
                "reason": "invalid",
                "movement_type": "deposit",
                "requested_amount": 1.25,
            },
        )
        _error(json_float, 422, "request_validation_error")

        boolean_version = client.post(
            f"/api/v1/paper-accounts/{account_id}/cash-movements",
            auth=AUTH,
            headers={"Idempotency-Key": "boolean"},
            json={
                "expected_account_version": True,
                "actor": "founder",
                "reason": "invalid",
                "movement_type": "deposit",
                "requested_amount": "1",
            },
        )
        _error(boolean_version, 422, "request_validation_error")

        insufficient = client.post(
            f"/api/v1/paper-accounts/{account_id}/cash-movements",
            auth=AUTH,
            headers={"Idempotency-Key": "withdraw-too-much"},
            json={
                "expected_account_version": 3,
                "actor": "founder",
                "reason": "invalid",
                "movement_type": "withdrawal",
                "requested_amount": "999",
            },
        )
        _error(
            insufficient,
            409,
            "paper_account_insufficient_available_cash",
        )

        negative_position = client.post(
            f"/api/v1/paper-accounts/{account_id}/position-adjustments",
            auth=AUTH,
            headers={"Idempotency-Key": "negative-position"},
            json={
                "expected_account_version": 3,
                "actor": "founder",
                "reason": "invalid",
                "symbol": "SYN",
                "adjustment_category": "manual_correction",
                "signed_quantity_delta": "-3",
                "signed_cost_basis_delta": "-10.5",
            },
        )
        _error(negative_position, 409, "paper_account_negative_position")


def test_evidence_lifecycle_snapshot_reconciliation_and_fail_closed_detail(
    configured_app,
) -> None:
    with TestClient(configured_app) as client:
        created_response = _create(client, initial_cash="0")
        created = created_response.json()
        account_id = created["account"]["account_id"]
        service = configured_app.state.paper_account_test_service
        initial_projection = service.get_current_projection(
            account_id=account_id
        )
        linked = client.post(
            f"/api/v1/paper-accounts/{account_id}/evidence-links",
            auth=AUTH,
            headers={"Idempotency-Key": "link-review"},
            json={
                "expected_account_version": 1,
                "actor": "founder",
                "reason": "governance provenance only",
                "review_id": "approved-review",
            },
        )
        assert linked.status_code == 201, linked.text
        assert len(
            linked.json()["projection"]["approved_portfolio_reviews"]
        ) == 1

        frozen = client.post(
            f"/api/v1/paper-accounts/{account_id}/lifecycle",
            auth=AUTH,
            headers={"Idempotency-Key": "freeze"},
            json={
                "expected_account_version": 2,
                "actor": "founder",
                "reason": "pause",
                "action": "freeze",
            },
        )
        assert frozen.status_code == 201
        blocked = client.post(
            f"/api/v1/paper-accounts/{account_id}/cash-movements",
            auth=AUTH,
            headers={"Idempotency-Key": "blocked"},
            json={
                "expected_account_version": 3,
                "actor": "founder",
                "reason": "blocked",
                "movement_type": "deposit",
                "requested_amount": "1",
            },
        )
        _error(blocked, 409, "paper_account_frozen")

        snapshot = client.post(
            f"/api/v1/paper-accounts/{account_id}/snapshots",
            auth=AUTH,
            headers={"Idempotency-Key": "snapshot"},
            json=_anchors(frozen.json()),
        )
        assert snapshot.status_code == 201, snapshot.text
        assert snapshot.json()["replayed"] is False
        assert "operation_idempotency_key" not in snapshot.text
        snapshot_replay = client.post(
            f"/api/v1/paper-accounts/{account_id}/snapshots",
            auth=AUTH,
            headers={"Idempotency-Key": "snapshot"},
            json=_anchors(frozen.json()),
        )
        assert snapshot_replay.status_code == 200
        assert snapshot_replay.json()["replayed"] is True

        reconciliation = client.post(
            f"/api/v1/paper-accounts/{account_id}/reconciliations",
            auth=AUTH,
            headers={"Idempotency-Key": "reconcile"},
            json=_anchors(frozen.json()),
        )
        assert reconciliation.status_code == 201, reconciliation.text
        assert reconciliation.json()["reconciliation"]["outcome"] == "matched"
        assert "operation_idempotency_key" not in reconciliation.text

        with service._session_factory.begin() as session:
            repository = SqlAlchemyPaperAccountRepository(session=session)
            repository.replace_projection(
                projection=initial_projection,
                updated_timestamp=datetime.now(timezone.utc),
            )
        mismatched = client.post(
            f"/api/v1/paper-accounts/{account_id}/reconciliations",
            auth=AUTH,
            headers={"Idempotency-Key": "reconcile-stale"},
            json=_anchors(frozen.json()),
        )
        assert mismatched.status_code == 201, mismatched.text
        assert (
            mismatched.json()["reconciliation"]["outcome"]
            == "mismatched"
        )
        assert mismatched.json()["reconciliation"]["mismatch_codes"]
        _error(
            client.get(
                f"/api/v1/paper-accounts/{account_id}",
                auth=AUTH,
            ),
            409,
            "paper_account_projection_stale",
        )
        listed = client.get("/api/v1/paper-accounts", auth=AUTH)
        assert listed.status_code == 200
        assert listed.json()["items"][0]["head_version"] == 3
        assert (
            listed.json()["items"][0]["projection_status"]
            == "reconciliation_required"
        )


def test_bounded_audit_events_exclude_sensitive_values(
    configured_app,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=PRODUCT_LOGGER_NAME)
    with TestClient(configured_app) as client:
        response = _create(
            client,
            key="super-secret-idempotency",
            initial_cash="98765.4321",
        )
        assert response.status_code == 201
        account_id = response.json()["account"]["account_id"]
        snapshot = client.post(
            f"/api/v1/paper-accounts/{account_id}/snapshots",
            auth=AUTH,
            headers={"Idempotency-Key": "snapshot-secret"},
            json={
                **_anchors(response.json()),
                "actor": "sensitive-actor",
                "reason": "sensitive-reason",
            },
        )
        assert snapshot.status_code == 201

    records = [
        record
        for record in caplog.records
        if record.name == PRODUCT_LOGGER_NAME
        and record.event
        in {
            "paper_account_command_completed",
            "paper_account_snapshot_completed",
            "paper_account_reconciliation_completed",
        }
    ]
    assert [record.event for record in records] == [
        "paper_account_command_completed",
        "paper_account_snapshot_completed",
    ]
    rendered = " ".join(
        f"{record.getMessage()} {record.__dict__}" for record in records
    )
    for forbidden in (
        "super-secret-idempotency",
        "snapshot-secret",
        "sensitive-actor",
        "sensitive-reason",
        "98765.4321",
        "idempotency_key",
        "cash_balance",
        "symbol",
        "digest",
        "database",
        "payload",
        "Traceback",
    ):
        assert forbidden not in rendered
