"""Focused Sprint 223 runtime API, read-only inspection, and contracts."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from el_psy_quant.api.app import create_app
from el_psy_quant.application import PaperAccountApplicationService
from el_psy_quant.application.paper_runtime import PaperRuntimeOwnershipService
from el_psy_quant.paper_account import PaperMoney
from test_api_paper_execution import AUTH, _Configured, _create
from test_paper_runtime_runner import _run_one, _runner_fixture

pytest_plugins = ("test_api_paper_execution",)


def _runtime_payload(order: dict[str, object]) -> dict[str, object]:
    return {
        "execution_order_id": order["execution_order_id"],
        "execution_order_digest": order["execution_order_digest"],
        "logical_actor": "stable-runtime-actor",
        "runtime_policy_id": "durable-runtime-v1",
        "runtime_policy_version": 1,
        "actor": "founder",
    }


def _create_runtime(client: TestClient, value: _Configured, key: str = "runtime-create"):
    order = _create(client, value, "runtime-order").json()["result"]["order"]
    response = client.post(
        "/api/v1/paper-runtimes",
        auth=AUTH,
        headers={"Idempotency-Key": key},
        json=_runtime_payload(order),
    )
    return response, order


def _control(client: TestClient, runtime: dict[str, object], operation: str, key: str):
    return client.post(
        f"/api/v1/paper-runtimes/{runtime['runtime_id']}/{operation}",
        auth=AUTH,
        headers={"Idempotency-Key": key},
        json={
            "runtime_binding_digest": runtime["runtime_binding_digest"],
            "expected_runtime_version": runtime["row_version"],
            "actor": "founder",
        },
    )


def _counts(path) -> tuple[int, ...]:
    with sqlite3.connect(path) as connection:
        return tuple(
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "paper_runtime_work",
                "paper_runtime_checkpoints",
                "paper_execution_attempts",
                "paper_execution_fills",
                "paper_execution_settlement_links",
                "paper_account_events",
            )
        )


def test_all_twelve_routes_are_authenticated_and_have_stable_operation_ids(
    configured: _Configured,
) -> None:
    document = configured.application.openapi()
    operations = {
        operation["operationId"]
        for path, methods in document["paths"].items()
        if path.startswith("/api/v1/paper-runtimes")
        for operation in methods.values()
    }
    assert operations == {
        "create_paper_runtime_v1",
        "list_paper_runtimes_v1",
        "get_paper_runtime_v1",
        "start_paper_runtime_v1",
        "stop_paper_runtime_v1",
        "resume_paper_runtime_v1",
        "recover_paper_runtime_v1",
        "get_paper_runtime_health_v1",
        "get_paper_runtime_reconciliation_v1",
        "list_paper_runtime_audit_v1",
        "list_paper_runtime_work_v1",
        "list_paper_runtime_checkpoints_v1",
    }
    runtime_id = "prt_" + "0" * 64
    requests = (
        ("post", "/api/v1/paper-runtimes"),
        ("get", "/api/v1/paper-runtimes"),
        ("get", f"/api/v1/paper-runtimes/{runtime_id}"),
        *(
            ("post", f"/api/v1/paper-runtimes/{runtime_id}/{name}")
            for name in ("start", "stop", "resume", "recover")
        ),
        ("get", f"/api/v1/paper-runtimes/{runtime_id}/health"),
        ("get", f"/api/v1/paper-runtimes/{runtime_id}/reconciliation"),
        ("get", f"/api/v1/paper-runtimes/{runtime_id}/audit"),
        ("get", f"/api/v1/paper-runtimes/{runtime_id}/work"),
        ("get", f"/api/v1/paper-runtimes/{runtime_id}/checkpoints"),
    )
    with TestClient(configured.application) as client:
        for method, path in requests:
            assert client.request(method, path).status_code == 401


def test_lifecycle_replay_conflict_and_http_recover_are_control_intent_only(
    configured: _Configured,
) -> None:
    with TestClient(configured.application) as client:
        created, _order = _create_runtime(client, configured)
        assert created.status_code == 201, created.text
        runtime = created.json()["runtime"]
        replay = client.post(
            "/api/v1/paper-runtimes",
            auth=AUTH,
            headers={"Idempotency-Key": "runtime-create"},
            json=_runtime_payload(_order),
        )
        assert replay.status_code == 200
        assert replay.json()["replayed"] is True
        assert replay.json()["runtime"] == created.json()["runtime"]

        changed = _runtime_payload(_order)
        changed["logical_actor"] = "changed-runtime-actor"
        conflict = client.post(
            "/api/v1/paper-runtimes",
            auth=AUTH,
            headers={"Idempotency-Key": "runtime-create"},
            json=changed,
        )
        assert conflict.status_code == 409
        assert conflict.json()["error"]["code"] == "paper_runtime_idempotency_conflict"

        started = _control(client, runtime, "start", "runtime-start")
        assert started.status_code == 201, started.text
        running = started.json()["runtime"]
        before = _counts(configured.database_path)
        recovered = _control(client, running, "recover", "runtime-recover")
        assert recovered.status_code == 201, recovered.text
        after = _counts(configured.database_path)
        assert before == after
        assert recovered.json()["runtime"]["owner_id"] is None
        assert recovered.json()["runtime"]["observed_state"] == "ready"
        audit = client.get(
            f"/api/v1/paper-runtimes/{runtime['runtime_id']}/audit", auth=AUTH
        )
        assert [item["event_type"] for item in audit.json()["items"]] == [
            "runtime_created",
            "start_requested",
            "recover_requested",
        ]
        assert all("payload" not in item for item in audit.json()["items"])


def test_detail_list_health_and_reconciliation_are_read_only(
    configured: _Configured,
) -> None:
    with TestClient(configured.application) as client:
        created, order = _create_runtime(client, configured, "read-runtime-create")
        runtime = created.json()["runtime"]
        database_before = _counts(configured.database_path)
        detail = client.get(
            f"/api/v1/paper-runtimes/{runtime['runtime_id']}", auth=AUTH
        )
        listed = client.get(
            f"/api/v1/paper-runtimes?account_id={runtime['account_id']}", auth=AUTH
        )
        health = client.get(
            f"/api/v1/paper-runtimes/{runtime['runtime_id']}/health", auth=AUTH
        )
        reconciliation = client.get(
            f"/api/v1/paper-runtimes/{runtime['runtime_id']}/reconciliation",
            auth=AUTH,
        )
        assert detail.json() == runtime
        assert listed.json()["items"] == [runtime]
        assert health.json()["lease_status"] == "unowned"
        assert reconciliation.json()["historical_coherent"] is True
        assert reconciliation.json()["status"] == "coherent_stopped"
        assert _counts(configured.database_path) == database_before

        service = PaperAccountApplicationService(
            session_factory=configured.application.state.product_session_factory,
            clock=lambda: datetime(2026, 8, 27, tzinfo=timezone.utc),
            id_factory=lambda kind: f"{kind}-runtime-divergence",
        )
        account = service.get_account(account_id=runtime["account_id"])
        service.post_cash_movement(
            account_id=account.account_id,
            expected_account_version=account.head_version,
            command_idempotency_key="runtime-live-divergence",
            actor="founder",
            reason="legitimate later live divergence",
            movement_type="deposit",
            requested_amount=PaperMoney.parse("1"),
        )
        stale = client.get(
            f"/api/v1/paper-runtimes/{runtime['runtime_id']}/reconciliation",
            auth=AUTH,
        )
        assert stale.status_code == 200, stale.text
        assert stale.json()["historical_coherent"] is True
        assert stale.json()["continuation_status"] == "stale"
        assert stale.json()["status"] == "continuation_stale"
        assert stale.json()["execution_order_id"] == order["execution_order_id"]


def test_health_classifies_active_claim_without_mutation(configured: _Configured) -> None:
    with TestClient(configured.application) as client:
        created, _order = _create_runtime(client, configured, "health-runtime-create")
        runtime = created.json()["runtime"]
    factory = configured.application.state.product_session_factory
    now = datetime.now(timezone.utc)
    claimed = PaperRuntimeOwnershipService(
        session_factory=factory,
        lease_duration=timedelta(days=1),
        clock=lambda: now,
    ).claim_runtime(runtime_id=runtime["runtime_id"], owner_id="health-worker").runtime
    with TestClient(configured.application) as client:
        response = client.get(
            f"/api/v1/paper-runtimes/{claimed.runtime_id}/health", auth=AUTH
        )
    assert response.status_code == 200
    assert response.json()["lease_status"] == "active"
    assert response.json()["claimed"] is True
    assert response.json()["fencing_token"] == claimed.fencing_token


def test_runtime_schema_unavailable_is_distinct_and_sanitized(tmp_path) -> None:
    application = create_app(
        product_database_path=tmp_path / "missing.sqlite3",
        founder_username=AUTH[0],
        founder_password=AUTH[1],
    )
    with TestClient(application) as client:
        response = client.get("/api/v1/paper-runtimes", auth=AUTH)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "paper_runtime_authority_unavailable"
    assert "missing.sqlite3" not in response.text


def test_audit_work_and_checkpoint_transport_is_bounded_ordered_and_sanitized(
    tmp_path, monkeypatch
) -> None:
    path = tmp_path / "runtime-inspection.sqlite3"
    engine, _factory, _order, _lifecycle, _ownership, runner, _clock, claim = (
        _runner_fixture(path, monkeypatch)
    )
    _run_one(runner, claim)
    application = create_app(
        product_database_path=path,
        founder_username=AUTH[0],
        founder_password=AUTH[1],
    )
    with TestClient(application) as client:
        work = client.get(
            f"/api/v1/paper-runtimes/{claim.runtime_id}/work?limit=1", auth=AUTH
        )
        checkpoints = client.get(
            f"/api/v1/paper-runtimes/{claim.runtime_id}/checkpoints?limit=1",
            auth=AUTH,
        )
        assert work.status_code == checkpoints.status_code == 200
        assert len(work.json()["items"]) == len(checkpoints.json()["items"]) == 1
        assert work.json()["items"][0]["expected_execution_version"] == 0
        assert checkpoints.json()["items"][0]["observed_execution_version"] == 1

        sequences = []
        cursor = None
        while True:
            suffix = "" if cursor is None else f"&cursor={cursor}"
            page = client.get(
                f"/api/v1/paper-runtimes/{claim.runtime_id}/audit?limit=1{suffix}",
                auth=AUTH,
            )
            assert page.status_code == 200, page.text
            item = page.json()["items"][0]
            assert "payload" not in item and "payload_json" not in item
            sequences.append(item["event_sequence"])
            cursor = page.json()["next_cursor"]
            if cursor is None:
                break
        assert sequences == list(range(len(sequences)))
    engine.dispose()
