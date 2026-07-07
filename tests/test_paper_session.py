"""Tests for local paper trading session summaries."""

import copy
from dataclasses import FrozenInstanceError
import json

import pytest

from el_psy_quant.paper import (
    PaperTradingSessionSummary,
    create_paper_account_state,
    create_paper_fill,
    create_paper_order_ledger,
    create_paper_order_record,
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


def test_valid_session_summary_creation() -> None:
    summary = make_summary()

    assert isinstance(summary, PaperTradingSessionSummary)
    assert summary.to_dict() == {
        "session_start_timestamp": "2026-01-01T00:00:00",
        "session_end_timestamp": "2026-01-03T00:00:00",
        "starting_cash": 1_000.0,
        "ending_cash": 875.0,
        "cash_change": -125.0,
        "starting_positions": [
            {"symbol": "MSFT", "quantity": 1.0},
        ],
        "ending_positions": [
            {"symbol": "AAPL", "quantity": 2.0},
            {"symbol": "MSFT", "quantity": 0.5},
        ],
        "position_changes": [
            {
                "symbol": "AAPL",
                "starting_quantity": 0.0,
                "ending_quantity": 2.0,
                "quantity_change": 2.0,
            },
            {
                "symbol": "MSFT",
                "starting_quantity": 1.0,
                "ending_quantity": 0.5,
                "quantity_change": -0.5,
            },
        ],
        "order_count": 2,
        "fill_count": 2,
    }


def test_session_summary_accepts_order_ledger() -> None:
    ledger = create_paper_order_ledger(make_orders())
    summary = make_summary(orders=ledger)

    assert summary.to_dict()["order_count"] == 2


def test_session_summary_cash_fields() -> None:
    payload = make_summary().to_dict()

    assert payload["starting_cash"] == 1_000.0
    assert payload["ending_cash"] == 875.0
    assert payload["cash_change"] == -125.0


def test_session_summary_position_fields() -> None:
    payload = make_summary().to_dict()

    assert payload["starting_positions"] == [
        {"symbol": "MSFT", "quantity": 1.0},
    ]
    assert payload["ending_positions"] == [
        {"symbol": "AAPL", "quantity": 2.0},
        {"symbol": "MSFT", "quantity": 0.5},
    ]
    assert payload["position_changes"] == [
        {
            "symbol": "AAPL",
            "starting_quantity": 0.0,
            "ending_quantity": 2.0,
            "quantity_change": 2.0,
        },
        {
            "symbol": "MSFT",
            "starting_quantity": 1.0,
            "ending_quantity": 0.5,
            "quantity_change": -0.5,
        },
    ]


def test_session_summary_order_count() -> None:
    assert make_summary().to_dict()["order_count"] == 2


def test_session_summary_fill_count() -> None:
    assert make_summary().to_dict()["fill_count"] == 2


def test_session_summary_deterministic_export() -> None:
    first = make_summary().to_dict()
    second = make_summary().to_dict()

    assert first == second


def test_session_summary_export_is_json_compatible() -> None:
    payload = make_summary().to_dict()

    json.dumps(payload, allow_nan=False)


def test_invalid_starting_account_state_raises() -> None:
    with pytest.raises(ValueError, match="starting_account_state"):
        make_summary(starting_account_state=object())


def test_invalid_ending_account_state_raises() -> None:
    with pytest.raises(ValueError, match="ending_account_state"):
        make_summary(ending_account_state=object())


@pytest.mark.parametrize("orders", [object(), "orders", make_orders()[0]])
def test_invalid_order_or_ledger_input_raises(orders) -> None:
    with pytest.raises(ValueError, match="orders"):
        make_summary(orders=orders)


def test_invalid_order_item_raises() -> None:
    with pytest.raises(ValueError, match="orders"):
        make_summary(orders=[make_orders()[0], object()])


@pytest.mark.parametrize("fills", [object(), "fills", make_fills()[0]])
def test_invalid_fill_input_raises(fills) -> None:
    with pytest.raises(ValueError, match="fills"):
        make_summary(fills=fills)


def test_invalid_fill_item_raises() -> None:
    with pytest.raises(ValueError, match="fills"):
        make_summary(fills=[make_fills()[0], object()])


def test_session_summary_does_not_mutate_account_states() -> None:
    starting = make_starting_state()
    ending = make_ending_state()
    starting_before = starting.to_dict()
    ending_before = ending.to_dict()

    make_summary(
        starting_account_state=starting,
        ending_account_state=ending,
    ).to_dict()

    assert starting.to_dict() == starting_before
    assert ending.to_dict() == ending_before


def test_session_summary_does_not_mutate_orders_or_ledger() -> None:
    orders = make_orders()
    ledger = create_paper_order_ledger(orders)
    order_exports_before = [order.to_dict() for order in orders]
    ledger_export_before = copy.deepcopy(ledger.to_dict())

    make_summary(orders=orders).to_dict()
    make_summary(orders=ledger).to_dict()

    assert [order.to_dict() for order in orders] == order_exports_before
    assert ledger.to_dict() == ledger_export_before


def test_session_summary_does_not_mutate_fills() -> None:
    fills = make_fills()
    fill_exports_before = [fill.to_dict() for fill in fills]

    make_summary(fills=fills).to_dict()

    assert [fill.to_dict() for fill in fills] == fill_exports_before


def test_session_summary_does_not_apply_fills_internally() -> None:
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

    payload = make_summary(
        starting_account_state=starting,
        ending_account_state=ending,
        fills=fills,
    ).to_dict()

    assert payload["ending_cash"] == 999.0
    assert payload["cash_change"] == -1.0
    assert payload["ending_positions"] == [
        {"symbol": "MSFT", "quantity": 1.0},
    ]


def test_session_summary_is_immutable() -> None:
    summary = make_summary()

    with pytest.raises(FrozenInstanceError):
        summary.fills = ()


def test_package_exports_work() -> None:
    from el_psy_quant.paper import (  # noqa: PLC0415
        PaperTradingSessionSummary,
        create_paper_trading_session_summary,
    )

    summary = create_paper_trading_session_summary(
        starting_account_state=make_starting_state(),
        ending_account_state=make_ending_state(),
        orders=make_orders(),
        fills=make_fills(),
    )

    assert isinstance(summary, PaperTradingSessionSummary)
