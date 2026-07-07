"""Tests for explicit local paper run artifact persistence."""

import json
from pathlib import Path

import pytest

from el_psy_quant.paper import (
    create_paper_account_state,
    create_paper_fill,
    create_paper_order_record,
    create_paper_trading_artifact,
    create_paper_trading_artifact_file_payload,
    create_paper_trading_session_summary,
    persist_paper_run_artifact,
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


def make_artifact():
    starting = make_starting_state()
    ending = make_ending_state()
    orders = make_orders()
    fills = make_fills()
    summary = create_paper_trading_session_summary(
        starting_account_state=starting,
        ending_account_state=ending,
        orders=orders,
        fills=fills,
    )

    return create_paper_trading_artifact(
        created_timestamp="2026-01-04T12:00:00",
        starting_account_state=starting,
        ending_account_state=ending,
        orders=orders,
        fills=fills,
        session_summary=summary,
    )


def test_persist_paper_run_artifact_writes_requested_file(tmp_path) -> None:
    artifact = make_artifact()
    destination = tmp_path / "paper-run-artifact.json"

    result = persist_paper_run_artifact(artifact, destination)

    assert result == destination
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "paper-run-artifact.json"
    ]


def test_persisted_content_matches_file_contract_payload(tmp_path) -> None:
    artifact = make_artifact()
    destination = tmp_path / "paper-run-artifact.json"

    persist_paper_run_artifact(artifact, destination)

    assert json.loads(destination.read_text(encoding="utf-8")) == (
        create_paper_trading_artifact_file_payload(artifact)
    )


def test_persist_paper_run_artifact_returns_path_for_string_input(tmp_path) -> None:
    artifact = make_artifact()
    destination = tmp_path / "paper-run-artifact.json"

    result = persist_paper_run_artifact(artifact, str(destination))

    assert result == Path(destination)


def test_invalid_artifact_input_raises(tmp_path) -> None:
    with pytest.raises(ValueError, match="PaperTradingArtifact"):
        persist_paper_run_artifact(object(), tmp_path / "artifact.json")


@pytest.mark.parametrize("destination_path", [object(), ""])
def test_invalid_path_input_raises(destination_path) -> None:
    with pytest.raises(ValueError, match="destination_path"):
        persist_paper_run_artifact(make_artifact(), destination_path)


def test_missing_parent_directory_raises_and_does_not_create_directories(tmp_path) -> None:
    destination = tmp_path / "missing" / "artifact.json"

    with pytest.raises(ValueError, match="parent directory"):
        persist_paper_run_artifact(make_artifact(), destination)

    assert not destination.exists()
    assert not destination.parent.exists()


def test_directory_destination_raises(tmp_path) -> None:
    with pytest.raises(ValueError, match="file path"):
        persist_paper_run_artifact(make_artifact(), tmp_path)


def test_persist_paper_run_artifact_does_not_mutate_artifact_or_nested_inputs(
    tmp_path,
) -> None:
    artifact = make_artifact()
    artifact_before = artifact.to_dict()
    starting_before = artifact.starting_account_state.to_dict()
    ending_before = artifact.ending_account_state.to_dict()
    orders_before = [order.to_dict() for order in artifact.orders]
    fills_before = [fill.to_dict() for fill in artifact.fills]
    summary_before = artifact.session_summary.to_dict()

    persist_paper_run_artifact(artifact, tmp_path / "artifact.json")

    assert artifact.to_dict() == artifact_before
    assert artifact.starting_account_state.to_dict() == starting_before
    assert artifact.ending_account_state.to_dict() == ending_before
    assert [order.to_dict() for order in artifact.orders] == orders_before
    assert [fill.to_dict() for fill in artifact.fills] == fills_before
    assert artifact.session_summary.to_dict() == summary_before


def test_run_persistence_module_does_not_add_reader_execution_or_summary_behavior() -> None:
    import el_psy_quant.paper.run_persistence as persistence  # noqa: PLC0415

    assert not hasattr(persistence, "read_paper_trading_artifact_file")
    assert not hasattr(persistence, "run_paper_trading_request")
    assert not hasattr(persistence, "create_paper_run_result_summary")
    assert not hasattr(persistence, "create_paper_trading_artifact_audit_summary")


def test_persistence_does_not_add_artifact_methods() -> None:
    artifact = make_artifact()

    assert not hasattr(artifact, "write")
    assert not hasattr(artifact, "save")
    assert not hasattr(artifact, "path")


def test_package_exports_work(tmp_path) -> None:
    import el_psy_quant.paper as paper  # noqa: PLC0415

    destination = tmp_path / "paper-run-artifact.json"

    assert paper.persist_paper_run_artifact is persist_paper_run_artifact
    assert paper.persist_paper_run_artifact(make_artifact(), destination) == destination
