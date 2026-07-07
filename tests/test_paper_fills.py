import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.paper import (
    PaperFill,
    PaperOrderRecord,
    apply_paper_fills,
    create_paper_account_state,
    create_paper_fill,
    create_paper_order_record,
)


def make_state():
    return create_paper_account_state(
        starting_cash=1_000,
        current_cash=1_000,
        positions={"MSFT": 1},
        timestamp="2026-01-01",
    )


def make_fill(
    *,
    timestamp: object = "2026-01-02",
    symbol: str = " aapl ",
    side: str = " buy ",
    quantity: float = 2,
    price: float = 100,
    order_id: str | None = None,
) -> PaperFill:
    return create_paper_fill(
        timestamp=timestamp,
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
        order_id=order_id,
    )


def test_valid_buy_fill_application_returns_new_state() -> None:
    state = make_state()

    result = apply_paper_fills(state, [make_fill()])

    assert result is not state
    assert result.to_dict() == {
        "timestamp": "2026-01-02T00:00:00",
        "starting_cash": 1000.0,
        "current_cash": 800.0,
        "positions": [
            {"symbol": "AAPL", "quantity": 2.0},
            {"symbol": "MSFT", "quantity": 1.0},
        ],
    }


def test_valid_sell_fill_application_returns_new_state() -> None:
    state = make_state()
    fill = make_fill(symbol="MSFT", side="sell", quantity=0.5, price=40)

    result = apply_paper_fills(state, [fill])

    assert result.current_cash == 1_020.0
    assert result.positions == (("MSFT", 0.5),)
    assert result.timestamp.isoformat() == "2026-01-02T00:00:00"


def test_multiple_fills_apply_in_caller_provided_order() -> None:
    state = make_state()
    fills = [
        make_fill(timestamp="2026-01-02", symbol="AAPL", side="buy", quantity=2, price=100),
        make_fill(timestamp="2026-01-03", symbol="AAPL", side="sell", quantity=1, price=125),
        make_fill(timestamp="2026-01-04", symbol="MSFT", side="sell", quantity=1, price=50),
    ]

    result = apply_paper_fills(state, fills)

    assert result.current_cash == 975.0
    assert result.positions == (("AAPL", 1.0), ("MSFT", 0.0))
    assert result.timestamp.isoformat() == "2026-01-04T00:00:00"


@pytest.mark.parametrize("timestamp", [None, "not-a-date"])
def test_invalid_fill_timestamp_raises_value_error(timestamp: object) -> None:
    with pytest.raises(ValueError, match="timestamp"):
        make_fill(timestamp=timestamp)


@pytest.mark.parametrize("symbol", ["", "   ", 123])
def test_invalid_fill_symbol_raises_value_error(symbol: object) -> None:
    with pytest.raises(ValueError, match="symbol"):
        make_fill(symbol=symbol)  # type: ignore[arg-type]


@pytest.mark.parametrize("side", ["hold", "", 1])
def test_invalid_fill_side_raises_value_error(side: object) -> None:
    with pytest.raises(ValueError, match="side"):
        make_fill(side=side)  # type: ignore[arg-type]


@pytest.mark.parametrize("quantity", [0, -1, float("nan"), float("inf"), "1", True])
def test_invalid_fill_quantity_raises_value_error(quantity: object) -> None:
    with pytest.raises(ValueError, match="quantity"):
        make_fill(quantity=quantity)  # type: ignore[arg-type]


@pytest.mark.parametrize("price", [-1, float("nan"), float("inf"), "1", False])
def test_invalid_fill_price_raises_value_error(price: object) -> None:
    with pytest.raises(ValueError, match="price"):
        make_fill(price=price)  # type: ignore[arg-type]


def test_invalid_order_id_raises_value_error() -> None:
    with pytest.raises(ValueError, match="order_id"):
        make_fill(order_id=" ")


def test_invalid_account_state_raises_value_error() -> None:
    with pytest.raises(ValueError, match="PaperAccountState"):
        apply_paper_fills(object(), [make_fill()])  # type: ignore[arg-type]


@pytest.mark.parametrize("fills", [[], make_fill(), "bad", object()])
def test_invalid_fill_sequence_raises_value_error(fills: object) -> None:
    with pytest.raises(ValueError, match="fills"):
        apply_paper_fills(make_state(), fills)  # type: ignore[arg-type]


def test_invalid_fill_item_raises_value_error() -> None:
    with pytest.raises(ValueError, match="PaperFill"):
        apply_paper_fills(make_state(), [make_fill(), object()])  # type: ignore[list-item]


def test_source_account_state_is_not_mutated() -> None:
    state = make_state()
    before = state.to_dict()

    apply_paper_fills(state, [make_fill()])

    assert state.to_dict() == before


def test_caller_provided_fill_inputs_are_not_mutated() -> None:
    fills = [make_fill(symbol="AAPL"), make_fill(symbol="MSFT", side="sell")]
    before = list(fills)

    apply_paper_fills(make_state(), fills)

    assert fills == before


def test_output_state_export_is_json_compatible() -> None:
    result = apply_paper_fills(make_state(), [make_fill()])

    json.dumps(result.to_dict(), allow_nan=False)


def test_deterministic_output_for_same_inputs() -> None:
    state = make_state()
    fills = [make_fill(), make_fill(symbol="MSFT", side="sell", quantity=1, price=50)]

    assert apply_paper_fills(state, fills).to_dict() == apply_paper_fills(
        state,
        fills,
    ).to_dict()


def test_no_order_status_driven_fill_behavior() -> None:
    state = make_state()
    filled_order = create_paper_order_record(
        order_id="order-1",
        timestamp="2026-01-02",
        symbol="AAPL",
        side="buy",
        quantity=2,
        status="filled",
    )

    with pytest.raises(ValueError, match="PaperFill"):
        apply_paper_fills(
            state,
            [filled_order],  # type: ignore[list-item]
        )

    assert isinstance(filled_order, PaperOrderRecord)
    assert state.to_dict() == make_state().to_dict()


def test_paper_fill_export_is_json_compatible() -> None:
    fill = make_fill(order_id=" order-1 ")

    payload = fill.to_dict()

    assert payload == {
        "timestamp": "2026-01-02T00:00:00",
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 2.0,
        "price": 100.0,
        "order_id": "order-1",
    }
    json.dumps(payload, allow_nan=False)


def test_paper_fill_is_immutable() -> None:
    fill = make_fill()

    with pytest.raises(FrozenInstanceError):
        fill.price = 1.0  # type: ignore[misc]


def test_package_exports_work() -> None:
    import el_psy_quant.paper as paper

    assert paper.PaperFill is PaperFill
    assert paper.create_paper_fill is create_paper_fill
    assert paper.apply_paper_fills is apply_paper_fills
