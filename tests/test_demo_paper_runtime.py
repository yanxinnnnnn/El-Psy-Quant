"""Sprint 226 non-Docker Demo v7 durable Paper Runtime acceptance."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from el_psy_quant.api.app import create_app
from el_psy_quant.api.demo_workspace_schemas import DemoWorkspaceDescriptorResponse
from el_psy_quant.application import PaperExecutionApplicationService
from el_psy_quant.application.paper_runtime import PaperRuntimeRecoveryService
from el_psy_quant.cli import run_paper_runtime_process
from el_psy_quant.demo_workspace import (
    DemoWorkspacePaths,
    DemoWorkspaceUnavailableError,
    install_demo_workspace,
    load_demo_workspace_descriptor,
    validate_installed_demo_workspace,
)
from el_psy_quant.paper_execution import create_step_paper_execution_order_command
from el_psy_quant.persistence import (
    PaperExecutionStorageFailureError,
    SqlAlchemyMarketTimeRepository,
    SqlAlchemyPaperExecutionRepository,
    SqlAlchemyPaperRuntimeRepository,
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_SOURCE = PROJECT_ROOT / "examples" / "demo_workspace"
ALEMBIC_CONFIG = PROJECT_ROOT / "alembic.ini"
AUTH = ("founder", "demo-secret")


@pytest.fixture
def demo_v7(tmp_path: Path) -> tuple[Path, DemoWorkspaceDescriptorResponse]:
    root = tmp_path / "demo-v7"
    result = install_demo_workspace(
        source_root=DEMO_SOURCE,
        workspace_root=root,
        workspace_mode="demo",
        alembic_config_path=ALEMBIC_CONFIG,
    )
    assert result.dataset_version == 7
    descriptor = DemoWorkspaceDescriptorResponse.model_validate(
        load_demo_workspace_descriptor(root).to_dict()
    )
    return root, descriptor


def _application(root: Path):
    return create_app(
        product_database_path=DemoWorkspacePaths.from_root(root).database_path,
        workspace_mode="demo",
        demo_workspace_root=root,
        founder_username=AUTH[0],
        founder_password=AUTH[1],
    )


def _control(
    client: TestClient,
    runtime: dict[str, object],
    operation: str,
    key: str,
):
    return client.post(
        f"/api/v1/paper-runtimes/{runtime['runtime_id']}/{operation}",
        auth=AUTH,
        headers={"Idempotency-Key": key},
        json={
            "runtime_binding_digest": runtime["runtime_binding_digest"],
            "expected_runtime_version": runtime["row_version"],
            "actor": "demo-founder",
        },
    )


def _authority_snapshot(root: Path, runtime_id: str):
    path = DemoWorkspacePaths.from_root(root).database_path
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=path)
    )
    factory = create_product_session_factory(engine=engine)
    try:
        with factory() as session:
            runtimes = SqlAlchemyPaperRuntimeRepository(session=session)
            runtime = runtimes.get_runtime(runtime_id=runtime_id)
            assert runtime is not None
            history = SqlAlchemyPaperExecutionRepository(
                session=session
            ).load_historical_history(execution_order_id=runtime.execution_order_id)
            replay = SqlAlchemyMarketTimeRepository(session=session).get_replay(
                replay_id=runtime.replay_id
            )
            assert replay is not None
            account_events = tuple(
                session.execute(
                    text(
                        "SELECT event_id, event_type FROM paper_account_events "
                        "WHERE account_id=:account_id ORDER BY account_version"
                    ),
                    {"account_id": runtime.account_id},
                )
            )
            return (
                runtime,
                runtimes.list_all_work(runtime_id=runtime_id),
                runtimes.list_all_checkpoints(runtime_id=runtime_id),
                runtimes.list_all_events(runtime_id=runtime_id),
                history,
                replay.session.cursor.position,
                replay.session.cursor.last_event_id,
                account_events,
            )
    finally:
        engine.dispose()


def test_fresh_demo_v7_runtime_is_exact_idempotent_and_inspectable(
    demo_v7: tuple[Path, DemoWorkspaceDescriptorResponse],
) -> None:
    root, descriptor = demo_v7
    reference = descriptor.paper_runtime
    before = _authority_snapshot(root, reference.runtime_id)
    runtime, work, checkpoints, events, history, position, last_event, account = before
    assert descriptor.schema_version == descriptor.dataset_version == 7
    assert runtime.runtime_binding_digest == reference.runtime_binding_digest
    assert runtime.execution_order_id == reference.execution_order_id
    assert runtime.execution_order_digest == reference.execution_order_digest
    assert runtime.account_id == reference.account_id
    assert runtime.replay_id == reference.replay_id
    assert runtime.trading_session_id == reference.trading_session_id
    assert (runtime.desired_state, runtime.observed_state) == ("stopped", "ready")
    assert runtime.owner_id is None
    assert runtime.fencing_token == runtime.row_version == 0
    assert work == checkpoints == history.attempts == history.fills == ()
    assert history.settlement_links == ()
    assert tuple(item.event_type for item in events) == ("runtime_created",)
    assert (position, last_event) == (4, "demo-runtime-event-004")
    assert tuple(item.event_type for item in account) == ("account_created",)

    reinstalled = install_demo_workspace(
        source_root=DEMO_SOURCE,
        workspace_root=root,
        workspace_mode="demo",
        alembic_config_path=ALEMBIC_CONFIG,
    )
    assert reinstalled.already_installed is True
    assert _authority_snapshot(root, reference.runtime_id) == before

    application = _application(root)
    paths = application.openapi()["paths"]
    runtime_operations = {
        operation["operationId"]
        for path, methods in paths.items()
        if path.startswith("/api/v1/paper-runtimes")
        for operation in methods.values()
    }
    assert len(runtime_operations) == 12
    with TestClient(application) as client:
        responses = (
            client.get("/api/v1/demo-workspace", auth=AUTH),
            client.get("/api/v1/paper-runtimes", auth=AUTH),
            client.get(f"/api/v1/paper-runtimes/{reference.runtime_id}", auth=AUTH),
            client.get(
                f"/api/v1/paper-runtimes/{reference.runtime_id}/health", auth=AUTH
            ),
            client.get(
                f"/api/v1/paper-runtimes/{reference.runtime_id}/reconciliation",
                auth=AUTH,
            ),
            client.get(
                f"/api/v1/paper-runtimes/{reference.runtime_id}/audit", auth=AUTH
            ),
            client.get(
                f"/api/v1/paper-runtimes/{reference.runtime_id}/work", auth=AUTH
            ),
            client.get(
                f"/api/v1/paper-runtimes/{reference.runtime_id}/checkpoints",
                auth=AUTH,
            ),
        )
    assert all(response.status_code == 200 for response in responses)
    assert responses[0].json()["paper_runtime"]["runtime_id"] == reference.runtime_id
    assert any(
        item["runtime_id"] == reference.runtime_id
        for item in responses[1].json()["items"]
    )
    assert responses[3].json()["lease_status"] == "unowned"
    assert responses[4].json()["continuation_status"] == "current"
    assert responses[6].json()["items"] == responses[7].json()["items"] == []
    assert _authority_snapshot(root, reference.runtime_id) == before


@pytest.mark.parametrize("mutation", ("v6", "partial", "mixed"))
def test_demo_v7_descriptor_version_and_runtime_mismatch_fail_closed(
    demo_v7: tuple[Path, DemoWorkspaceDescriptorResponse],
    mutation: str,
) -> None:
    root, _descriptor = demo_v7
    descriptor_path = DemoWorkspacePaths.from_root(root).descriptor_path
    payload = json.loads(descriptor_path.read_text(encoding="utf-8"))
    if mutation == "v6":
        payload["schema_version"] = 6
        payload["dataset_version"] = 6
    elif mutation == "partial":
        del payload["paper_runtime"]["replay_id"]
    else:
        payload["paper_runtime"]["runtime_binding_digest"] = "f" * 64
        payload["paper_runtime"]["runtime_id"] = "prt_" + "f" * 64
    descriptor_path.write_text(json.dumps(payload), encoding="utf-8")
    before = descriptor_path.read_bytes()

    with pytest.raises(DemoWorkspaceUnavailableError):
        validate_installed_demo_workspace(root)

    assert descriptor_path.read_bytes() == before


def test_demo_v7_real_process_restart_control_fill_and_completion(
    demo_v7: tuple[Path, DemoWorkspaceDescriptorResponse],
) -> None:
    root, descriptor = demo_v7
    reference = descriptor.paper_runtime
    database = DemoWorkspacePaths.from_root(root).database_path
    application = _application(root)
    with TestClient(application) as client:
        runtime = client.get(
            f"/api/v1/paper-runtimes/{reference.runtime_id}", auth=AUTH
        ).json()
        before_start = _authority_snapshot(root, reference.runtime_id)
        started = _control(client, runtime, "start", "demo-v7-start")
        assert started.status_code == 201, started.text
        runtime = started.json()["runtime"]
        assert (runtime["desired_state"], runtime["observed_state"]) == (
            "running",
            "ready",
        )
        assert _authority_snapshot(root, reference.runtime_id)[1:3] == ((), ())
        recovered = _control(client, runtime, "recover", "demo-v7-recover-request")
        assert recovered.status_code == 201, recovered.text
        runtime = recovered.json()["runtime"]
        after_request = _authority_snapshot(root, reference.runtime_id)
        assert after_request[1:3] == ((), ())
        assert after_request[4:] == before_start[4:]
        assert runtime["owner_id"] is None

    first = run_paper_runtime_process(
        database_path=database,
        runtime_id=reference.runtime_id,
        owner_id="demo-worker-a",
        iteration_budget=1,
    )
    after_first = _authority_snapshot(root, reference.runtime_id)
    runtime, work, checkpoints, _events, history, position, last_event, account = (
        after_first
    )
    assert first.runner_outcome == "iteration_budget_exhausted"
    assert first.iterations == 1
    assert (runtime.desired_state, runtime.observed_state) == ("running", "running")
    assert runtime.owner_id is None
    assert len(work) == len(checkpoints) == len(history.attempts) == 1
    assert work[0].expected_execution_version == 0
    assert checkpoints[0].fill_id is None
    assert history.attempts[0].attempt_result == "no_fill"
    assert (position, last_event) == (5, "demo-runtime-event-005")
    assert history.fills == history.settlement_links == ()
    assert tuple(item.event_type for item in account) == ("account_created",)

    second = run_paper_runtime_process(
        database_path=database,
        runtime_id=reference.runtime_id,
        owner_id="demo-worker-b",
        iteration_budget=1,
    )
    after_second = _authority_snapshot(root, reference.runtime_id)
    runtime, work, checkpoints, _events, history, position, last_event, account = (
        after_second
    )
    assert second.runner_outcome == "iteration_budget_exhausted"
    assert second.fencing_token > first.fencing_token
    assert (runtime.desired_state, runtime.observed_state) == ("running", "running")
    assert runtime.owner_id is None
    assert tuple(item.expected_execution_version for item in work) == (0, 1)
    assert len(work) == len(checkpoints) == len(history.attempts) == 2
    assert len(history.fills) == len(history.settlement_links) == 1
    assert checkpoints[1].fill_id == history.fills[0].fill_id
    assert (position, last_event) == (6, "demo-runtime-event-006")
    assert tuple(item.event_type for item in account) == (
        "account_created",
        "execution_fill_posted",
    )

    with TestClient(application) as client:
        current = client.get(
            f"/api/v1/paper-runtimes/{reference.runtime_id}", auth=AUTH
        ).json()
        stopped = _control(client, current, "stop", "demo-v7-stop")
        assert stopped.status_code == 201, stopped.text
    stopped_process = run_paper_runtime_process(
        database_path=database,
        runtime_id=reference.runtime_id,
        owner_id="demo-worker-c",
        iteration_budget=1,
    )
    after_stop = _authority_snapshot(root, reference.runtime_id)
    assert stopped_process.recovery_outcome == "stopped"
    assert stopped_process.runner_outcome is None
    assert stopped_process.fencing_token > second.fencing_token
    assert after_stop[0].desired_state == after_stop[0].observed_state == "stopped"
    assert after_stop[1:3] == after_second[1:3]
    assert after_stop[4:] == after_second[4:]

    with TestClient(application) as client:
        current = client.get(
            f"/api/v1/paper-runtimes/{reference.runtime_id}", auth=AUTH
        ).json()
        resumed = _control(client, current, "resume", "demo-v7-resume")
        assert resumed.status_code == 201, resumed.text
    after_resume = _authority_snapshot(root, reference.runtime_id)
    assert after_resume[0].desired_state == "running"
    assert after_resume[0].observed_state == "stopped"
    assert after_resume[1:3] == after_second[1:3]
    assert after_resume[4:] == after_second[4:]

    completed = run_paper_runtime_process(
        database_path=database,
        runtime_id=reference.runtime_id,
        owner_id="demo-worker-d",
        iteration_budget=1,
    )
    final = _authority_snapshot(root, reference.runtime_id)
    runtime, work, checkpoints, _events, history, position, last_event, account = final
    assert completed.runner_outcome == "completed"
    assert completed.fencing_token > stopped_process.fencing_token
    assert runtime.desired_state == "running"
    assert runtime.observed_state == "completed"
    assert runtime.owner_id is None
    assert tuple(item.expected_execution_version for item in work) == (0, 1, 2)
    assert len(work) == len(checkpoints) == len(history.attempts) == 3
    assert tuple(item.attempt_result for item in history.attempts) == (
        "no_fill",
        "fill",
        "boundary_rejected",
    )
    assert len(history.fills) == len(history.settlement_links) == 1
    assert (position, last_event) == (6, "demo-runtime-event-006")
    assert tuple(item.event_type for item in account) == (
        "account_created",
        "execution_fill_posted",
    )

    repeated = run_paper_runtime_process(
        database_path=database,
        runtime_id=reference.runtime_id,
        owner_id="demo-worker-e",
        iteration_budget=1,
    )
    assert repeated.recovery_outcome == "completed"
    assert repeated.runner_outcome is None
    repeated_final = _authority_snapshot(root, reference.runtime_id)
    assert repeated_final[0].observed_state == "completed"
    assert repeated_final[0].owner_id is None
    assert repeated_final[0].fencing_token > final[0].fencing_token
    assert repeated_final[1:3] == final[1:3]
    assert repeated_final[4:] == final[4:]

    validated = validate_installed_demo_workspace(root)
    assert validated.to_dict()["paper_runtime"]["runtime_id"] == reference.runtime_id
    reinstalled = install_demo_workspace(
        source_root=DEMO_SOURCE,
        workspace_root=root,
        workspace_mode="demo",
        alembic_config_path=ALEMBIC_CONFIG,
    )
    assert reinstalled.already_installed is True
    assert _authority_snapshot(root, reference.runtime_id) == repeated_final


def test_demo_v7_process_recovery_converges_ambiguous_attempt_without_work_receipt(
    demo_v7: tuple[Path, DemoWorkspaceDescriptorResponse],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, descriptor = demo_v7
    reference = descriptor.paper_runtime
    database = DemoWorkspacePaths.from_root(root).database_path
    application = _application(root)
    with TestClient(application) as client:
        runtime = client.get(
            f"/api/v1/paper-runtimes/{reference.runtime_id}", auth=AUTH
        ).json()
        assert _control(client, runtime, "start", "recovery-start").status_code == 201

    original_step = PaperExecutionApplicationService.step_order

    def lose_before_step(self, command):
        del self, command
        raise PaperExecutionStorageFailureError()

    monkeypatch.setattr(
        PaperExecutionApplicationService, "step_order", lose_before_step
    )
    with pytest.raises(PaperExecutionStorageFailureError):
        run_paper_runtime_process(
            database_path=database,
            runtime_id=reference.runtime_id,
            owner_id="demo-recovery-worker",
            iteration_budget=1,
        )
    monkeypatch.setattr(PaperExecutionApplicationService, "step_order", original_step)

    pending = _authority_snapshot(root, reference.runtime_id)
    runtime, work, checkpoints, _events, history, *_ = pending
    assert len(work) == 1
    assert checkpoints == history.attempts == ()
    pending_work = work[0]
    pending_command = PaperRuntimeRecoveryService._work_command(runtime, pending_work)
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=database)
    )
    factory = create_product_session_factory(engine=engine)
    try:
        execution = PaperExecutionApplicationService(session_factory=factory)
        committed = execution.step_order(
            create_step_paper_execution_order_command(
                execution_order_reference=pending_command.execution_order_reference,
                expected_execution_version=pending_work.expected_execution_version,
                command_idempotency_key="demo-v7-ambiguous-alternate-step",
                actor=pending_work.m34_step_actor,
            )
        )
        assert committed.replayed is False
        with factory() as session:
            repository = SqlAlchemyPaperExecutionRepository(session=session)
            assert (
                repository.get_receipt(
                    namespace="step_paper_execution_order",
                    command_idempotency_key=pending_work.m34_step_idempotency_key,
                )
                is None
            )
    finally:
        engine.dispose()

    after_commit = _authority_snapshot(root, reference.runtime_id)
    assert len(after_commit[1]) == len(after_commit[4].attempts) == 1
    assert after_commit[2] == ()
    with TestClient(application) as client:
        current = client.get(
            f"/api/v1/paper-runtimes/{reference.runtime_id}", auth=AUTH
        ).json()
        assert _control(client, current, "stop", "recovery-stop").status_code == 201

    recovered = run_paper_runtime_process(
        database_path=database,
        runtime_id=reference.runtime_id,
        owner_id="demo-recovery-worker",
        iteration_budget=1,
    )
    final = _authority_snapshot(root, reference.runtime_id)
    assert recovered.recovery_outcome == "stopped"
    assert recovered.runner_outcome is None
    assert final[0].owner_id is None
    assert final[1] == after_commit[1]
    assert len(final[2]) == 1
    assert final[2][0].work_id == pending_work.work_id
    assert final[4].attempts == after_commit[4].attempts
    assert final[4].fills == after_commit[4].fills
    assert final[5:] == after_commit[5:]
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=database)
    )
    factory = create_product_session_factory(engine=engine)
    try:
        with factory() as session:
            receipt = SqlAlchemyPaperExecutionRepository(session=session).get_receipt(
                namespace="step_paper_execution_order",
                command_idempotency_key=pending_work.m34_step_idempotency_key,
            )
        assert receipt is not None
        assert receipt.command_actor == pending_work.m34_step_actor
        assert receipt.attempt_id == final[4].attempts[0].attempt_id
    finally:
        engine.dispose()
