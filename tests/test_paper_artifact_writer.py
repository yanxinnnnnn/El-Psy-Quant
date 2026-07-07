"""Tests for the local paper trading artifact writer."""

import json
from pathlib import Path

import pytest

from el_psy_quant.paper import (
    PAPER_TRADING_ARTIFACT_FILE_ENCODING,
    create_paper_account_state,
    create_paper_fill,
    create_paper_order_record,
    create_paper_trading_artifact,
    create_paper_trading_artifact_file_payload,
    create_paper_trading_session_summary,
    write_paper_trading_artifact_file,
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


def test_writer_creates_exactly_requested_explicit_file(tmp_path) -> None:
    artifact = make_artifact()
    destination = tmp_path / "paper-artifact.json"

    result = write_paper_trading_artifact_file(artifact, destination)

    assert result == destination
    assert sorted(path.name for path in tmp_path.iterdir()) == ["paper-artifact.json"]


def test_written_json_content_matches_file_payload(tmp_path) -> None:
    artifact = make_artifact()
    destination = tmp_path / "paper-artifact.json"

    write_paper_trading_artifact_file(artifact, destination)

    assert json.loads(destination.read_text(encoding="utf-8")) == (
        create_paper_trading_artifact_file_payload(artifact)
    )


def test_writer_uses_deterministic_utf8_json_format(tmp_path) -> None:
    artifact = make_artifact()
    destination = tmp_path / "paper-artifact.json"

    write_paper_trading_artifact_file(artifact, destination)

    content = destination.read_bytes().decode(PAPER_TRADING_ARTIFACT_FILE_ENCODING)
    assert content.endswith("\n")
    assert content.startswith('{\n  "schema_version": 1,')
    json.loads(content)


def test_writer_returns_destination_path_for_string_input(tmp_path) -> None:
    artifact = make_artifact()
    destination = tmp_path / "paper-artifact.json"

    result = write_paper_trading_artifact_file(artifact, str(destination))

    assert result == destination


def test_invalid_artifact_input_raises(tmp_path) -> None:
    with pytest.raises(ValueError, match="PaperTradingArtifact"):
        write_paper_trading_artifact_file(object(), tmp_path / "artifact.json")


@pytest.mark.parametrize("destination_path", [object(), ""])
def test_invalid_path_input_raises(destination_path) -> None:
    with pytest.raises(ValueError, match="destination_path"):
        write_paper_trading_artifact_file(make_artifact(), destination_path)


def test_missing_parent_directory_raises_and_does_not_create_directories(tmp_path) -> None:
    destination = tmp_path / "missing" / "artifact.json"

    with pytest.raises(ValueError, match="parent directory"):
        write_paper_trading_artifact_file(make_artifact(), destination)

    assert not destination.exists()
    assert not destination.parent.exists()


def test_directory_destination_raises(tmp_path) -> None:
    with pytest.raises(ValueError, match="file path"):
        write_paper_trading_artifact_file(make_artifact(), tmp_path)


def test_writer_does_not_mutate_artifact_or_nested_inputs(tmp_path) -> None:
    artifact = make_artifact()
    artifact_before = artifact.to_dict()
    starting_before = artifact.starting_account_state.to_dict()
    ending_before = artifact.ending_account_state.to_dict()
    orders_before = [order.to_dict() for order in artifact.orders]
    fills_before = [fill.to_dict() for fill in artifact.fills]
    summary_before = artifact.session_summary.to_dict()

    write_paper_trading_artifact_file(artifact, tmp_path / "artifact.json")

    assert artifact.to_dict() == artifact_before
    assert artifact.starting_account_state.to_dict() == starting_before
    assert artifact.ending_account_state.to_dict() == ending_before
    assert [order.to_dict() for order in artifact.orders] == orders_before
    assert [fill.to_dict() for fill in artifact.fills] == fills_before
    assert artifact.session_summary.to_dict() == summary_before


def test_writer_does_not_add_reader_behavior() -> None:
    import el_psy_quant.paper as paper  # noqa: PLC0415

    assert not hasattr(paper, "read_paper_trading_artifact_file")
    assert not hasattr(paper, "load_paper_trading_artifact_file")


def test_writer_does_not_add_artifact_methods() -> None:
    artifact = make_artifact()

    assert not hasattr(artifact, "write")
    assert not hasattr(artifact, "save")
    assert not hasattr(artifact, "path")


def test_writer_package_export_works(tmp_path) -> None:
    from el_psy_quant.paper import write_paper_trading_artifact_file  # noqa: PLC0415

    destination = tmp_path / "paper-artifact.json"

    assert write_paper_trading_artifact_file(make_artifact(), destination) == Path(
        destination
    )
