"""Tests for immutable local paper run requests."""

import copy
from dataclasses import FrozenInstanceError
import json

import pytest

from el_psy_quant.paper import (
    PAPER_RUN_REQUEST_SCHEMA_VERSION,
    PaperRunRequest,
    create_paper_account_state,
    create_paper_fill,
    create_paper_order_ledger,
    create_paper_order_record,
    create_paper_run_request,
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


def make_request(
    *,
    run_id: str = " run-1 ",
    created_timestamp: object = "2026-01-04T12:00:00Z",
    starting_account_state=None,
    ending_account_state=None,
    orders=None,
    fills=None,
) -> PaperRunRequest:
    return create_paper_run_request(
        run_id=run_id,
        created_timestamp=created_timestamp,
        starting_account_state=starting_account_state or make_starting_state(),
        ending_account_state=ending_account_state or make_ending_state(),
        orders=orders if orders is not None else make_orders(),
        fills=fills if fills is not None else make_fills(),
    )


def test_valid_paper_run_request_creation() -> None:
    request = make_request()

    assert isinstance(request, PaperRunRequest)
    assert request.run_id == "run-1"
    assert request.created_timestamp.isoformat() == "2026-01-04T12:00:00+00:00"


def test_paper_run_request_schema_version_exists() -> None:
    assert PAPER_RUN_REQUEST_SCHEMA_VERSION == 1
    json.dumps({"schema_version": PAPER_RUN_REQUEST_SCHEMA_VERSION}, allow_nan=False)


def test_request_export_is_deterministic_and_json_compatible() -> None:
    request = make_request()

    payload = request.to_dict()

    assert payload == request.to_dict()
    assert payload == {
        "schema_version": PAPER_RUN_REQUEST_SCHEMA_VERSION,
        "run_id": "run-1",
        "created_timestamp": "2026-01-04T12:00:00+00:00",
        "starting_account_state": make_starting_state().to_dict(),
        "ending_account_state": make_ending_state().to_dict(),
        "orders": [order.to_dict() for order in make_orders()],
        "fills": [fill.to_dict() for fill in make_fills()],
    }
    json.dumps(payload, allow_nan=False)


def test_request_accepts_order_ledger_and_preserves_order() -> None:
    orders = make_orders()
    ledger = create_paper_order_ledger(orders)

    request = make_request(orders=ledger)

    assert request.orders == tuple(orders)
    assert request.to_dict()["orders"] == [order.to_dict() for order in orders]


def test_request_accepts_empty_orders_and_fills() -> None:
    request = make_request(orders=[], fills=[])

    assert request.orders == ()
    assert request.fills == ()
    assert request.to_dict()["orders"] == []
    assert request.to_dict()["fills"] == []


@pytest.mark.parametrize("run_id", ["", "   ", 123])
def test_invalid_run_id_raises_value_error(run_id: object) -> None:
    with pytest.raises(ValueError, match="run_id"):
        make_request(run_id=run_id)  # type: ignore[arg-type]


@pytest.mark.parametrize("created_timestamp", [None, "not-a-date"])
def test_invalid_created_timestamp_raises_value_error(
    created_timestamp: object,
) -> None:
    with pytest.raises(ValueError, match="created_timestamp"):
        make_request(created_timestamp=created_timestamp)


@pytest.mark.parametrize(
    ("field_name", "starting_account_state", "ending_account_state"),
    [
        ("starting_account_state", object(), None),
        ("ending_account_state", None, object()),
    ],
)
def test_invalid_account_state_raises_value_error(
    field_name: str,
    starting_account_state: object | None,
    ending_account_state: object | None,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        make_request(
            starting_account_state=(
                starting_account_state
                if starting_account_state is not None
                else make_starting_state()
            ),
            ending_account_state=(
                ending_account_state
                if ending_account_state is not None
                else make_ending_state()
            ),
        )


@pytest.mark.parametrize("orders", [make_orders()[0], "bad", object()])
def test_invalid_orders_input_type_raises_value_error(orders: object) -> None:
    with pytest.raises(ValueError, match="orders"):
        make_request(orders=orders)  # type: ignore[arg-type]


def test_invalid_order_item_raises_value_error() -> None:
    with pytest.raises(ValueError, match="PaperOrderRecord"):
        make_request(orders=[make_orders()[0], object()])  # type: ignore[list-item]


def test_duplicate_order_ids_raise_value_error() -> None:
    duplicate_orders = [
        make_orders()[0],
        create_paper_order_record(
            order_id="order-1",
            timestamp="2026-01-03",
            symbol="MSFT",
            side="sell",
            quantity=1.0,
            status="filled",
        ),
    ]

    with pytest.raises(ValueError, match="duplicate order_id: order-1"):
        make_request(orders=duplicate_orders)


@pytest.mark.parametrize("fills", [make_fills()[0], "bad", object()])
def test_invalid_fills_input_type_raises_value_error(fills: object) -> None:
    with pytest.raises(ValueError, match="fills"):
        make_request(fills=fills)  # type: ignore[arg-type]


def test_invalid_fill_item_raises_value_error() -> None:
    with pytest.raises(ValueError, match="PaperFill"):
        make_request(fills=[make_fills()[0], object()])  # type: ignore[list-item]


def test_request_is_immutable() -> None:
    request = make_request()

    with pytest.raises(FrozenInstanceError):
        request.run_id = "other"  # type: ignore[misc]


def test_request_does_not_mutate_caller_inputs() -> None:
    starting = make_starting_state()
    ending = make_ending_state()
    orders = make_orders()
    fills = make_fills()
    original_orders = list(orders)
    original_fills = list(fills)
    starting_payload = copy.deepcopy(starting.to_dict())
    ending_payload = copy.deepcopy(ending.to_dict())

    request = make_request(
        starting_account_state=starting,
        ending_account_state=ending,
        orders=orders,
        fills=fills,
    )
    request.to_dict()

    assert orders == original_orders
    assert fills == original_fills
    assert starting.to_dict() == starting_payload
    assert ending.to_dict() == ending_payload


def test_request_does_not_add_workflow_or_file_behaviors(tmp_path) -> None:
    request = make_request()

    assert not hasattr(request, "run")
    assert not hasattr(request, "execute")
    assert not hasattr(request, "to_artifact")
    assert not hasattr(request, "write")
    assert not hasattr(request, "save")
    assert not hasattr(request, "path")
    assert list(tmp_path.iterdir()) == []


def test_package_exports_work() -> None:
    import el_psy_quant.paper as paper  # noqa: PLC0415

    request = paper.create_paper_run_request(
        run_id="run-1",
        created_timestamp="2026-01-04T12:00:00Z",
        starting_account_state=make_starting_state(),
        ending_account_state=make_ending_state(),
        orders=make_orders(),
        fills=make_fills(),
    )

    assert paper.PAPER_RUN_REQUEST_SCHEMA_VERSION == PAPER_RUN_REQUEST_SCHEMA_VERSION
    assert paper.PaperRunRequest is PaperRunRequest
    assert paper.create_paper_run_request is create_paper_run_request
    assert isinstance(request, PaperRunRequest)
