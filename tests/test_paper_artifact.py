"""Tests for standalone in-memory paper trading artifacts."""

import copy
from dataclasses import FrozenInstanceError
import json

import pytest

from el_psy_quant.paper import (
    PAPER_TRADING_ARTIFACT_SCHEMA_VERSION,
    PaperTradingArtifact,
    create_paper_account_state,
    create_paper_fill,
    create_paper_order_ledger,
    create_paper_order_record,
    create_paper_trading_artifact,
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


def make_summary(
    *,
    starting_account_state=None,
    ending_account_state=None,
    orders=None,
    fills=None,
):
    return create_paper_trading_session_summary(
        starting_account_state=starting_account_state or make_starting_state(),
        ending_account_state=ending_account_state or make_ending_state(),
        orders=orders if orders is not None else make_orders(),
        fills=fills if fills is not None else make_fills(),
    )


def make_artifact(
    *,
    created_timestamp="2026-01-04T12:00:00Z",
    starting_account_state=None,
    ending_account_state=None,
    orders=None,
    fills=None,
    session_summary=None,
):
    starting = starting_account_state or make_starting_state()
    ending = ending_account_state or make_ending_state()
    normalized_orders = orders if orders is not None else make_orders()
    normalized_fills = fills if fills is not None else make_fills()
    summary = session_summary or make_summary(
        starting_account_state=starting,
        ending_account_state=ending,
        orders=normalized_orders,
        fills=normalized_fills,
    )

    return create_paper_trading_artifact(
        created_timestamp=created_timestamp,
        starting_account_state=starting,
        ending_account_state=ending,
        orders=normalized_orders,
        fills=normalized_fills,
        session_summary=summary,
    )


def test_valid_paper_trading_artifact_creation() -> None:
    artifact = make_artifact()

    assert isinstance(artifact, PaperTradingArtifact)


def test_artifact_schema_version_field() -> None:
    payload = make_artifact().to_dict()

    assert payload["schema_version"] == PAPER_TRADING_ARTIFACT_SCHEMA_VERSION
    assert payload["schema_version"] == 1


def test_artifact_created_timestamp_is_explicit_and_serialized() -> None:
    payload = make_artifact(created_timestamp="2026-01-04 12:00:00").to_dict()

    assert payload["created_timestamp"] == "2026-01-04T12:00:00"


@pytest.mark.parametrize("created_timestamp", ["not-a-date", None])
def test_invalid_created_timestamp_raises(created_timestamp) -> None:
    with pytest.raises(ValueError, match="created_timestamp"):
        make_artifact(created_timestamp=created_timestamp)


def test_starting_account_state_export_included() -> None:
    starting = make_starting_state()
    payload = make_artifact(starting_account_state=starting).to_dict()

    assert payload["starting_account_state"] == starting.to_dict()


def test_ending_account_state_export_included() -> None:
    ending = make_ending_state()
    payload = make_artifact(ending_account_state=ending).to_dict()

    assert payload["ending_account_state"] == ending.to_dict()


def test_order_exports_included() -> None:
    orders = make_orders()
    payload = make_artifact(orders=orders).to_dict()

    assert payload["orders"] == [order.to_dict() for order in orders]


def test_order_ledger_exports_included() -> None:
    ledger = create_paper_order_ledger(make_orders())
    payload = make_artifact(orders=ledger).to_dict()

    assert payload["orders"] == [order.to_dict() for order in ledger.orders]


def test_fill_exports_included() -> None:
    fills = make_fills()
    payload = make_artifact(fills=fills).to_dict()

    assert payload["fills"] == [fill.to_dict() for fill in fills]


def test_session_summary_export_included() -> None:
    summary = make_summary()
    payload = make_artifact(session_summary=summary).to_dict()

    assert payload["session_summary"] == summary.to_dict()


def test_artifact_deterministic_export() -> None:
    first = make_artifact().to_dict()
    second = make_artifact().to_dict()

    assert first == second


def test_artifact_export_is_json_compatible() -> None:
    payload = make_artifact().to_dict()

    json.dumps(payload, allow_nan=False)


def test_invalid_starting_account_state_raises() -> None:
    with pytest.raises(ValueError, match="starting_account_state"):
        make_artifact(starting_account_state=object())


def test_invalid_ending_account_state_raises() -> None:
    with pytest.raises(ValueError, match="ending_account_state"):
        make_artifact(ending_account_state=object())


@pytest.mark.parametrize("orders", [object(), "orders", make_orders()[0]])
def test_invalid_order_or_ledger_input_raises(orders) -> None:
    with pytest.raises(ValueError, match="orders"):
        make_artifact(orders=orders)


def test_invalid_order_item_raises() -> None:
    with pytest.raises(ValueError, match="orders"):
        make_artifact(orders=[make_orders()[0], object()])


@pytest.mark.parametrize("fills", [object(), "fills", make_fills()[0]])
def test_invalid_fill_input_raises(fills) -> None:
    with pytest.raises(ValueError, match="fills"):
        make_artifact(fills=fills)


def test_invalid_fill_item_raises() -> None:
    with pytest.raises(ValueError, match="fills"):
        make_artifact(fills=[make_fills()[0], object()])


def test_invalid_session_summary_input_raises() -> None:
    with pytest.raises(ValueError, match="session_summary"):
        make_artifact(session_summary=object())


def test_artifact_does_not_mutate_account_states() -> None:
    starting = make_starting_state()
    ending = make_ending_state()
    starting_before = starting.to_dict()
    ending_before = ending.to_dict()

    make_artifact(
        starting_account_state=starting,
        ending_account_state=ending,
    ).to_dict()

    assert starting.to_dict() == starting_before
    assert ending.to_dict() == ending_before


def test_artifact_does_not_mutate_orders_or_ledger() -> None:
    orders = make_orders()
    ledger = create_paper_order_ledger(orders)
    order_exports_before = [order.to_dict() for order in orders]
    ledger_export_before = copy.deepcopy(ledger.to_dict())

    make_artifact(orders=orders).to_dict()
    make_artifact(orders=ledger).to_dict()

    assert [order.to_dict() for order in orders] == order_exports_before
    assert ledger.to_dict() == ledger_export_before


def test_artifact_does_not_mutate_fills() -> None:
    fills = make_fills()
    fill_exports_before = [fill.to_dict() for fill in fills]

    make_artifact(fills=fills).to_dict()

    assert [fill.to_dict() for fill in fills] == fill_exports_before


def test_artifact_does_not_mutate_session_summary() -> None:
    summary = make_summary()
    summary_before = summary.to_dict()

    make_artifact(session_summary=summary).to_dict()

    assert summary.to_dict() == summary_before


def test_artifact_does_not_apply_fills_internally() -> None:
    starting = make_starting_state()
    ending = create_paper_account_state(
        starting_cash=1_000.0,
        current_cash=999.0,
        positions={"MSFT": 1.0},
        timestamp="2026-01-03",
    )
    fills = [
        create_paper_fill(
            timestamp="2026-01-02",
            symbol="AAPL",
            side="buy",
            quantity=2.0,
            price=100.0,
            order_id="order-1",
        ),
    ]
    summary = make_summary(
        starting_account_state=starting,
        ending_account_state=ending,
        fills=fills,
    )

    payload = make_artifact(
        starting_account_state=starting,
        ending_account_state=ending,
        fills=fills,
        session_summary=summary,
    ).to_dict()

    assert payload["ending_account_state"]["current_cash"] == 999.0
    assert payload["session_summary"]["cash_change"] == -1.0
    assert payload["ending_account_state"]["positions"] == [
        {"symbol": "MSFT", "quantity": 1.0},
    ]


def test_artifact_has_no_file_writing_or_persistence_behavior() -> None:
    artifact = make_artifact()

    assert not hasattr(artifact, "write")
    assert not hasattr(artifact, "save")
    assert not hasattr(artifact, "path")


def test_artifact_is_immutable() -> None:
    artifact = make_artifact()

    with pytest.raises(FrozenInstanceError):
        artifact.fills = ()


def test_package_exports_work() -> None:
    from el_psy_quant.paper import (  # noqa: PLC0415
        PAPER_TRADING_ARTIFACT_SCHEMA_VERSION,
        PaperTradingArtifact,
        create_paper_trading_artifact,
    )

    artifact = create_paper_trading_artifact(
        created_timestamp="2026-01-04",
        starting_account_state=make_starting_state(),
        ending_account_state=make_ending_state(),
        orders=make_orders(),
        fills=make_fills(),
        session_summary=make_summary(),
    )

    assert PAPER_TRADING_ARTIFACT_SCHEMA_VERSION == 1
    assert isinstance(artifact, PaperTradingArtifact)
