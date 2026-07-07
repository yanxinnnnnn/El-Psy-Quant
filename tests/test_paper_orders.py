import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.paper import (
    PaperOrderLedger,
    PaperOrderRecord,
    create_paper_order_ledger,
    create_paper_order_record,
)


def make_order(
    *,
    order_id: str = "order-1",
    timestamp: object = "2026-01-02 09:30:00",
    symbol: str = " aapl ",
    side: str = " BUY ",
    quantity: float = 10,
    status: str = " Submitted ",
) -> PaperOrderRecord:
    return create_paper_order_record(
        order_id=order_id,
        timestamp=timestamp,
        symbol=symbol,
        side=side,
        quantity=quantity,
        status=status,
    )


def test_valid_paper_order_creation() -> None:
    order = make_order()

    assert order.order_id == "order-1"
    assert order.timestamp.isoformat() == "2026-01-02T09:30:00"
    assert order.symbol == "AAPL"
    assert order.side == "buy"
    assert order.quantity == 10.0
    assert order.status == "submitted"


@pytest.mark.parametrize("order_id", ["", "   ", 123])
def test_invalid_order_id_raises_value_error(order_id: object) -> None:
    with pytest.raises(ValueError, match="order_id"):
        make_order(order_id=order_id)  # type: ignore[arg-type]


@pytest.mark.parametrize("timestamp", [None, "not-a-date"])
def test_invalid_timestamp_raises_value_error(timestamp: object) -> None:
    with pytest.raises(ValueError, match="timestamp"):
        make_order(timestamp=timestamp)


@pytest.mark.parametrize("symbol", ["", "   ", 123])
def test_invalid_symbol_raises_value_error(symbol: object) -> None:
    with pytest.raises(ValueError, match="symbol"):
        make_order(symbol=symbol)  # type: ignore[arg-type]


@pytest.mark.parametrize("side", ["hold", "", 1])
def test_invalid_side_raises_value_error(side: object) -> None:
    with pytest.raises(ValueError, match="side"):
        make_order(side=side)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "quantity",
    [0, -1, float("nan"), float("inf"), "1", True],
)
def test_invalid_quantity_raises_value_error(quantity: object) -> None:
    with pytest.raises(ValueError, match="quantity"):
        make_order(quantity=quantity)  # type: ignore[arg-type]


@pytest.mark.parametrize("status", ["pending", "", 1])
def test_invalid_status_raises_value_error(status: object) -> None:
    with pytest.raises(ValueError, match="status"):
        make_order(status=status)  # type: ignore[arg-type]


def test_paper_order_export_is_json_compatible() -> None:
    order = make_order()

    payload = order.to_dict()

    assert payload == {
        "order_id": "order-1",
        "timestamp": "2026-01-02T09:30:00",
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 10.0,
        "status": "submitted",
    }
    json.dumps(payload, allow_nan=False)


def test_paper_order_record_is_immutable() -> None:
    order = make_order()

    with pytest.raises(FrozenInstanceError):
        order.status = "accepted"  # type: ignore[misc]


def test_valid_ledger_creation_preserves_order() -> None:
    orders = [
        make_order(order_id="order-1", symbol="AAPL"),
        make_order(order_id="order-2", symbol="MSFT", side="sell", status="accepted"),
    ]

    ledger = create_paper_order_ledger(orders)

    assert ledger.orders == tuple(orders)
    assert ledger.to_dict()["orders"] == [order.to_dict() for order in orders]


def test_duplicate_order_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate order_id: order-1"):
        create_paper_order_ledger(
            [
                make_order(order_id="order-1"),
                make_order(order_id="order-1", symbol="MSFT"),
            ]
        )


@pytest.mark.parametrize("orders", [make_order(), "bad", object()])
def test_invalid_ledger_input_type_raises_value_error(orders: object) -> None:
    with pytest.raises(ValueError, match="sequence"):
        create_paper_order_ledger(orders)  # type: ignore[arg-type]


def test_invalid_ledger_item_raises_value_error() -> None:
    with pytest.raises(ValueError, match="PaperOrderRecord"):
        create_paper_order_ledger([make_order(), object()])  # type: ignore[list-item]


def test_deterministic_ledger_export() -> None:
    ledger = create_paper_order_ledger(
        [
            make_order(order_id="order-1", symbol="AAPL"),
            make_order(order_id="order-2", symbol="MSFT", side="sell"),
        ]
    )

    assert ledger.to_dict() == ledger.to_dict()


def test_ledger_export_is_json_compatible() -> None:
    ledger = create_paper_order_ledger([make_order()])

    json.dumps(ledger.to_dict(), allow_nan=False)


def test_no_mutation_of_caller_provided_order_inputs() -> None:
    orders = [make_order(order_id="order-1"), make_order(order_id="order-2")]
    before = list(orders)

    create_paper_order_ledger(orders)

    assert orders == before


def test_paper_order_ledger_is_immutable() -> None:
    ledger = create_paper_order_ledger([make_order()])

    with pytest.raises(FrozenInstanceError):
        ledger.orders = ()  # type: ignore[misc]


def test_package_exports_work() -> None:
    import el_psy_quant.paper as paper

    assert paper.PaperOrderRecord is PaperOrderRecord
    assert paper.PaperOrderLedger is PaperOrderLedger
    assert paper.create_paper_order_record is create_paper_order_record
    assert paper.create_paper_order_ledger is create_paper_order_ledger
