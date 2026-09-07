"""Focused Sprint 223 runtime API, read-only inspection, and contracts."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import sqlite3
from datetime import datetime, timedelta, timezone
from threading import Barrier

from fastapi.testclient import TestClient
from sqlalchemy import text

from el_psy_quant.api.app import create_app
from el_psy_quant.api.dependencies import get_paper_runtime_inspection_service
from el_psy_quant.api.paper_runtime_pagination import (
    encode_paper_runtime_list_cursor,
)
from el_psy_quant.application import (
    PaperAccountApplicationService,
    PaperExecutionApplicationService,
)
from el_psy_quant.application.paper_runtime import (
    PaperRuntimeOwnershipService,
    PaperRuntimeRecoveryService,
)
from el_psy_quant.application.paper_runtime_inspection import (
    PaperRuntimeInspectionService,
)
from el_psy_quant.paper_account import PaperMoney
from el_psy_quant.persistence import SqlAlchemyPaperExecutionRepository
from test_api_paper_execution import AUTH, _Configured, _create
from test_paper_execution_persistence import _step_command
from test_paper_runtime_recovery import (
    _canonical_side_effects,
    _leave_work_without_attempt,
)
from test_paper_runtime_runner import _read, _run_one, _runner_fixture

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


def _create_runtime(
    client: TestClient, value: _Configured, key: str = "runtime-create"
):
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


def _runtime_evidence_counts(path) -> tuple[int, int]:
    with sqlite3.connect(path) as connection:
        return (
            connection.execute("SELECT COUNT(*) FROM paper_runtime_events").fetchone()[
                0
            ],
            connection.execute(
                "SELECT COUNT(*) FROM paper_runtime_command_receipts"
            ).fetchone()[0],
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


def test_start_stop_and_resume_transport_preserve_lifecycle_replay(
    configured: _Configured,
) -> None:
    with TestClient(configured.application) as client:
        created, _order = _create_runtime(
            client, configured, "lifecycle-transport-create"
        )
        current = created.json()["runtime"]
        expected_states = {
            "start": ("running", "ready"),
            "stop": ("stopped", "ready"),
            "resume": ("running", "stopped"),
        }
        for operation in ("start", "stop", "resume"):
            key = f"lifecycle-transport-{operation}"
            accepted = _control(client, current, operation, key)
            assert accepted.status_code == 201, accepted.text
            result = accepted.json()
            assert result["replayed"] is False
            assert (
                result["runtime"]["desired_state"],
                result["runtime"]["observed_state"],
            ) == expected_states[operation]

            replay = _control(client, current, operation, key)
            assert replay.status_code == 200, replay.text
            assert replay.json()["replayed"] is True
            assert replay.json()["runtime"] == result["runtime"]
            current = result["runtime"]
            if operation == "stop":
                factory = configured.application.state.product_session_factory
                ownership = PaperRuntimeOwnershipService(
                    session_factory=factory,
                    lease_duration=timedelta(seconds=30),
                )
                settled = PaperRuntimeRecoveryService(
                    session_factory=factory,
                    execution_service=PaperExecutionApplicationService(
                        session_factory=factory
                    ),
                    ownership_service=ownership,
                ).recover_runtime(
                    runtime_id=current["runtime_id"],
                    recovery_owner_id="lifecycle-stop-observer",
                )
                assert settled.outcome == "stopped"
                current = settled.runtime.to_dict()


def test_concurrent_api_start_retries_converge_once_and_changed_digest_is_409(
    configured: _Configured,
) -> None:
    with TestClient(configured.application) as client:
        created, _order = _create_runtime(
            client, configured, "concurrent-api-runtime-create"
        )
    runtime = created.json()["runtime"]
    barrier = Barrier(2)

    def start():
        with TestClient(configured.application) as client:
            barrier.wait(timeout=10)
            response = _control(
                client, runtime, "start", "concurrent-api-runtime-start"
            )
            return response.status_code, response.json()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = tuple(pool.submit(start) for _index in range(2))
        results = tuple(future.result(timeout=15) for future in futures)
    assert sorted(status for status, _body in results) == [200, 201]
    assert sorted(body["replayed"] for _status, body in results) == [False, True]
    assert results[0][1]["runtime"] == results[1][1]["runtime"]
    assert _runtime_evidence_counts(configured.database_path) == (2, 2)

    before = (
        _counts(configured.database_path),
        _runtime_evidence_counts(configured.database_path),
    )
    with TestClient(configured.application) as client:
        conflict = client.post(
            f"/api/v1/paper-runtimes/{runtime['runtime_id']}/start",
            auth=AUTH,
            headers={"Idempotency-Key": "concurrent-api-runtime-start"},
            json={
                "runtime_binding_digest": runtime["runtime_binding_digest"],
                "expected_runtime_version": runtime["row_version"],
                "actor": "different-founder",
            },
        )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "paper_runtime_idempotency_conflict"
    assert (
        _counts(configured.database_path),
        _runtime_evidence_counts(configured.database_path),
    ) == before


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


def test_health_classifies_active_and_expired_claim_without_mutation(
    configured: _Configured,
) -> None:
    with TestClient(configured.application) as client:
        created, _order = _create_runtime(client, configured, "health-runtime-create")
        runtime = created.json()["runtime"]
    factory = configured.application.state.product_session_factory
    now = datetime.now(timezone.utc)
    claimed = (
        PaperRuntimeOwnershipService(
            session_factory=factory,
            lease_duration=timedelta(days=1),
            clock=lambda: now,
        )
        .claim_runtime(runtime_id=runtime["runtime_id"], owner_id="health-worker")
        .runtime
    )
    with TestClient(configured.application) as client:
        response = client.get(
            f"/api/v1/paper-runtimes/{claimed.runtime_id}/health", auth=AUTH
        )
    assert response.status_code == 200
    assert response.json()["lease_status"] == "active"
    assert response.json()["claimed"] is True
    assert response.json()["fencing_token"] == claimed.fencing_token
    before = _read(factory, claimed.runtime_id)
    assert claimed.lease_expires_at is not None
    configured.application.dependency_overrides[
        get_paper_runtime_inspection_service
    ] = lambda: PaperRuntimeInspectionService(
        session_factory=factory, clock=lambda: claimed.lease_expires_at
    )
    try:
        with TestClient(configured.application) as client:
            expired = client.get(
                f"/api/v1/paper-runtimes/{claimed.runtime_id}/health", auth=AUTH
            )
    finally:
        configured.application.dependency_overrides.pop(
            get_paper_runtime_inspection_service, None
        )
    assert expired.status_code == 200
    assert expired.json()["lease_status"] == "expired"
    assert expired.json()["claimed"] is True
    assert _read(factory, claimed.runtime_id) == before


def test_reconciliation_accepts_ambiguous_attempt_then_s222_converges_exact_work(
    tmp_path, monkeypatch
) -> None:
    path = tmp_path / "runtime-ambiguous-inspection.sqlite3"
    engine, factory, order, _lifecycle, ownership, runner, clock, claim = (
        _runner_fixture(path, monkeypatch)
    )
    _leave_work_without_attempt(runner, claim, monkeypatch)
    current, works, checkpoints, events, history = _read(factory, claim.runtime_id)
    assert len(works) == 1
    pending = works[0]
    assert checkpoints == history.attempts == ()

    committed = runner._execution_service.step_order(
        _step_command(
            order,
            version=pending.expected_execution_version,
            key="alternate-command-for-ambiguous-attempt",
            actor=pending.m34_step_actor,
        )
    )
    assert committed.replayed is False
    with factory() as session:
        assert (
            SqlAlchemyPaperExecutionRepository(session=session).get_receipt(
                namespace="step_paper_execution_order",
                command_idempotency_key=pending.m34_step_idempotency_key,
            )
            is None
        )

    application = create_app(
        product_database_path=path,
        founder_username=AUTH[0],
        founder_password=AUTH[1],
    )
    before_inspection = _read(factory, claim.runtime_id)
    effects_after_commit = _canonical_side_effects(
        factory, claim.runtime_id, order.market_handoff_reference.replay_id
    )
    with TestClient(application) as client:
        response = client.get(
            f"/api/v1/paper-runtimes/{claim.runtime_id}/reconciliation", auth=AUTH
        )
    assert response.status_code == 200, response.text
    assert response.json()["historical_coherent"] is True
    assert response.json()["pending_work_id"] == pending.work_id
    assert _read(factory, claim.runtime_id) == before_inspection

    assert current.lease_expires_at is not None
    clock.value = current.lease_expires_at
    recovered = PaperRuntimeRecoveryService(
        session_factory=factory,
        execution_service=runner._execution_service,
        ownership_service=ownership,
        clock=clock,
    ).recover_runtime(
        runtime_id=claim.runtime_id,
        recovery_owner_id="ambiguous-convergence-worker",
    )
    runtime, later_work, later_checkpoints, later_events, later_history = _read(
        factory, claim.runtime_id
    )
    assert recovered.outcome == "runnable"
    assert recovered.work == pending == later_work[0]
    assert recovered.step_replayed is True
    assert len(later_work) == len(later_checkpoints) == len(later_history.attempts) == 1
    assert later_checkpoints[0].work_id == pending.work_id
    assert [event.event_type for event in later_events].count("work_observed") == 1
    assert runtime.fencing_token == claim.fencing_token + 1
    assert (
        _canonical_side_effects(
            factory, claim.runtime_id, order.market_handoff_reference.replay_id
        )
        == effects_after_commit
    )
    engine.dispose()


def test_reconciliation_corruption_is_sanitized_and_fail_closed(
    tmp_path, monkeypatch
) -> None:
    path = tmp_path / "runtime-corrupt-inspection.sqlite3"
    engine, _factory, _order, _lifecycle, _ownership, runner, _clock, claim = (
        _runner_fixture(path, monkeypatch)
    )
    _leave_work_without_attempt(runner, claim, monkeypatch)
    with engine.begin() as connection:
        connection.execute(text("DROP TRIGGER trg_paper_runtime_work_no_update"))
        connection.execute(
            text(
                "UPDATE paper_runtime_work SET payload_json=:payload "
                "WHERE runtime_id=:runtime_id"
            ),
            {
                "payload": '{"secret":"C:/private/runtime.sqlite3"}',
                "runtime_id": claim.runtime_id,
            },
        )
        connection.execute(
            text(
                "CREATE TRIGGER trg_paper_runtime_work_no_update "
                "BEFORE UPDATE ON paper_runtime_work BEGIN SELECT RAISE(ABORT, "
                "'paper_runtime_work is append-only'); END"
            )
        )
    application = create_app(
        product_database_path=path,
        founder_username=AUTH[0],
        founder_password=AUTH[1],
    )
    with TestClient(application) as client:
        response = client.get(
            f"/api/v1/paper-runtimes/{claim.runtime_id}/reconciliation", auth=AUTH
        )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "paper_runtime_authority_corrupt"
    assert "private" not in response.text.lower()
    assert "payload" not in response.text.lower()
    engine.dispose()


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


def test_all_runtime_pages_are_exact_mutation_free_and_reject_forged_anchors(
    tmp_path, monkeypatch
) -> None:
    path = tmp_path / "runtime-page-hardening.sqlite3"
    engine, factory, _order, _lifecycle, _ownership, runner, _clock, claim = (
        _runner_fixture(path, monkeypatch)
    )
    completed = runner.run_claimed_runtime(
        runtime_id=claim.runtime_id,
        owner_id=claim.owner_id,
        fencing_token=claim.fencing_token,
        iteration_budget=3,
    )
    assert completed.outcome == "completed"
    application = create_app(
        product_database_path=path,
        founder_username=AUTH[0],
        founder_password=AUTH[1],
    )
    before = (
        _read(factory, claim.runtime_id),
        _counts(path),
        _runtime_evidence_counts(path),
    )

    def collect(client, collection: str, identity_field: str):
        items = []
        cursor = None
        while True:
            suffix = "" if cursor is None else f"&cursor={cursor}"
            response = client.get(
                f"/api/v1/paper-runtimes/{claim.runtime_id}/{collection}"
                f"?limit=1{suffix}",
                auth=AUTH,
            )
            assert response.status_code == 200, response.text
            page = response.json()
            items.extend(page["items"])
            cursor = page["next_cursor"]
            if cursor is None:
                break
        identities = [item[identity_field] for item in items]
        assert len(identities) == len(set(identities))
        return items

    with TestClient(application) as client:
        audit = collect(client, "audit", "event_id")
        work = collect(client, "work", "work_id")
        checkpoints = collect(client, "checkpoints", "checkpoint_id")
        assert [item["event_sequence"] for item in audit] == list(range(len(audit)))
        assert [item["expected_execution_version"] for item in work] == [0, 1]
        assert [item["observed_execution_version"] for item in checkpoints] == [1, 2]
        for collection in ("audit", "work", "checkpoints"):
            assert (
                client.get(
                    f"/api/v1/paper-runtimes/{claim.runtime_id}/{collection}?limit=0",
                    auth=AUTH,
                ).status_code
                == 422
            )
            assert (
                client.get(
                    f"/api/v1/paper-runtimes/{claim.runtime_id}/{collection}?limit=201",
                    auth=AUTH,
                ).status_code
                == 422
            )

        context = {"runtime_id": claim.runtime_id}
        forged = (
            (
                "audit",
                encode_paper_runtime_list_cursor(
                    collection_kind="paper_runtime_audit",
                    resource_id="pre_" + "0" * 64,
                    position=0,
                    query_context=context,
                ),
            ),
            (
                "work",
                encode_paper_runtime_list_cursor(
                    collection_kind="paper_runtime_work",
                    resource_id="prw_" + "0" * 64,
                    position=0,
                    query_context=context,
                ),
            ),
            (
                "checkpoints",
                encode_paper_runtime_list_cursor(
                    collection_kind="paper_runtime_checkpoints",
                    resource_id="prc_" + "0" * 64,
                    position=1,
                    query_context=context,
                ),
            ),
        )
        for collection, cursor in forged:
            response = client.get(
                f"/api/v1/paper-runtimes/{claim.runtime_id}/{collection}"
                f"?limit=1&cursor={cursor}",
                auth=AUTH,
            )
            assert response.status_code == 422
            assert response.json()["error"]["code"] == "paper_runtime_invalid_cursor"
            assert "sqlite" not in response.text.lower()

        runtime = completed.runtime
        runtime_cursor = encode_paper_runtime_list_cursor(
            collection_kind="paper_runtimes",
            resource_id="prt_" + "0" * 64,
            created_at=runtime.created_at,
            query_context={
                "account_id": None,
                "replay_id": None,
                "trading_session_id": None,
                "desired_state": None,
                "observed_state": None,
            },
        )
        response = client.get(
            f"/api/v1/paper-runtimes?limit=1&cursor={runtime_cursor}", auth=AUTH
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "paper_runtime_invalid_cursor"

    assert (
        _read(factory, claim.runtime_id),
        _counts(path),
        _runtime_evidence_counts(path),
    ) == before
    engine.dispose()
