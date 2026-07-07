"""Tests for the paper trading artifact file contract."""

import json

import pytest

from el_psy_quant.paper import (
    PAPER_TRADING_ARTIFACT_FILE_ENCODING,
    PAPER_TRADING_ARTIFACT_FILE_NAME,
    PAPER_TRADING_ARTIFACT_FILE_TOP_LEVEL_KEYS,
    PAPER_TRADING_ARTIFACT_SCHEMA_VERSION,
    create_paper_account_state,
    create_paper_fill,
    create_paper_order_record,
    create_paper_trading_artifact,
    create_paper_trading_artifact_file_payload,
    create_paper_trading_session_summary,
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


def test_file_contract_constants_are_exported() -> None:
    assert PAPER_TRADING_ARTIFACT_FILE_NAME == "paper_trading_artifact.json"
    assert PAPER_TRADING_ARTIFACT_FILE_ENCODING == "utf-8"
    assert PAPER_TRADING_ARTIFACT_FILE_TOP_LEVEL_KEYS == (
        "schema_version",
        "created_timestamp",
        "starting_account_state",
        "ending_account_state",
        "orders",
        "fills",
        "session_summary",
    )


def test_file_contract_keys_match_artifact_payload_keys() -> None:
    payload = create_paper_trading_artifact_file_payload(make_artifact())

    assert tuple(payload) == PAPER_TRADING_ARTIFACT_FILE_TOP_LEVEL_KEYS
    assert payload["schema_version"] == PAPER_TRADING_ARTIFACT_SCHEMA_VERSION


def test_file_payload_matches_artifact_to_dict() -> None:
    artifact = make_artifact()

    assert create_paper_trading_artifact_file_payload(artifact) == artifact.to_dict()


def test_file_payload_is_json_compatible() -> None:
    payload = create_paper_trading_artifact_file_payload(make_artifact())

    json.dumps(payload, allow_nan=False)


def test_invalid_file_payload_input_raises() -> None:
    with pytest.raises(ValueError, match="PaperTradingArtifact"):
        create_paper_trading_artifact_file_payload(object())


def test_file_payload_does_not_mutate_artifact_or_nested_inputs() -> None:
    artifact = make_artifact()
    artifact_before = artifact.to_dict()
    starting_before = artifact.starting_account_state.to_dict()
    ending_before = artifact.ending_account_state.to_dict()
    orders_before = [order.to_dict() for order in artifact.orders]
    fills_before = [fill.to_dict() for fill in artifact.fills]
    summary_before = artifact.session_summary.to_dict()

    create_paper_trading_artifact_file_payload(artifact)

    assert artifact.to_dict() == artifact_before
    assert artifact.starting_account_state.to_dict() == starting_before
    assert artifact.ending_account_state.to_dict() == ending_before
    assert [order.to_dict() for order in artifact.orders] == orders_before
    assert [fill.to_dict() for fill in artifact.fills] == fills_before
    assert artifact.session_summary.to_dict() == summary_before


def test_file_payload_does_not_write_or_touch_files(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert list(tmp_path.iterdir()) == []
    create_paper_trading_artifact_file_payload(make_artifact())
    assert list(tmp_path.iterdir()) == []


def test_file_contract_package_exports_work() -> None:
    from el_psy_quant.paper import (  # noqa: PLC0415
        PAPER_TRADING_ARTIFACT_FILE_ENCODING,
        PAPER_TRADING_ARTIFACT_FILE_NAME,
        PAPER_TRADING_ARTIFACT_FILE_TOP_LEVEL_KEYS,
        create_paper_trading_artifact_file_payload,
    )

    payload = create_paper_trading_artifact_file_payload(make_artifact())

    assert PAPER_TRADING_ARTIFACT_FILE_NAME == "paper_trading_artifact.json"
    assert PAPER_TRADING_ARTIFACT_FILE_ENCODING == "utf-8"
    assert tuple(payload) == PAPER_TRADING_ARTIFACT_FILE_TOP_LEVEL_KEYS
