"""Tests for local in-memory paper run execution."""

import copy
import json

import pytest

from el_psy_quant.paper import (
    PaperTradingArtifact,
    create_paper_account_state,
    create_paper_fill,
    create_paper_order_record,
    create_paper_run_request,
    create_paper_trading_artifact,
    create_paper_trading_session_summary,
    run_paper_trading_request,
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
    starting_account_state=None,
    ending_account_state=None,
    orders=None,
    fills=None,
):
    return create_paper_run_request(
        run_id="run-1",
        created_timestamp="2026-01-04T12:00:00Z",
        starting_account_state=starting_account_state or make_starting_state(),
        ending_account_state=ending_account_state or make_ending_state(),
        orders=orders if orders is not None else make_orders(),
        fills=fills if fills is not None else make_fills(),
    )


def test_run_paper_trading_request_returns_artifact() -> None:
    artifact = run_paper_trading_request(make_request())

    assert isinstance(artifact, PaperTradingArtifact)


def test_run_paper_trading_request_matches_existing_helpers() -> None:
    request = make_request()
    expected_summary = create_paper_trading_session_summary(
        starting_account_state=request.starting_account_state,
        ending_account_state=request.ending_account_state,
        orders=request.orders,
        fills=request.fills,
    )
    expected_artifact = create_paper_trading_artifact(
        created_timestamp=request.created_timestamp,
        starting_account_state=request.starting_account_state,
        ending_account_state=request.ending_account_state,
        orders=request.orders,
        fills=request.fills,
        session_summary=expected_summary,
    )

    artifact = run_paper_trading_request(request)

    assert artifact.to_dict() == expected_artifact.to_dict()


def test_run_paper_trading_request_preserves_request_ordering() -> None:
    request = make_request()

    artifact = run_paper_trading_request(request)

    assert artifact.orders == request.orders
    assert artifact.fills == request.fills
    assert artifact.to_dict()["orders"] == [order.to_dict() for order in request.orders]
    assert artifact.to_dict()["fills"] == [fill.to_dict() for fill in request.fills]


def test_run_paper_trading_request_uses_explicit_ending_state_without_fill_application() -> None:
    starting = create_paper_account_state(
        starting_cash=1_000.0,
        current_cash=1_000.0,
        positions={},
        timestamp="2026-01-01",
    )
    explicit_ending = create_paper_account_state(
        starting_cash=1_000.0,
        current_cash=999.0,
        positions={},
        timestamp="2026-01-03",
    )
    request = make_request(
        starting_account_state=starting,
        ending_account_state=explicit_ending,
        orders=[],
        fills=[
            create_paper_fill(
                timestamp="2026-01-02",
                symbol="AAPL",
                side="buy",
                quantity=2.0,
                price=100.0,
            )
        ],
    )

    artifact = run_paper_trading_request(request)

    assert artifact.ending_account_state is explicit_ending
    assert artifact.to_dict()["ending_account_state"] == explicit_ending.to_dict()
    assert artifact.to_dict()["session_summary"]["ending_cash"] == 999.0


def test_run_paper_trading_request_export_is_json_compatible() -> None:
    artifact = run_paper_trading_request(make_request())

    json.dumps(artifact.to_dict(), allow_nan=False)


def test_invalid_request_raises_value_error() -> None:
    with pytest.raises(ValueError, match="PaperRunRequest"):
        run_paper_trading_request(object())  # type: ignore[arg-type]


def test_run_paper_trading_request_does_not_mutate_request_or_inputs() -> None:
    starting = make_starting_state()
    ending = make_ending_state()
    orders = make_orders()
    fills = make_fills()
    request = make_request(
        starting_account_state=starting,
        ending_account_state=ending,
        orders=orders,
        fills=fills,
    )
    request_payload = copy.deepcopy(request.to_dict())
    starting_payload = copy.deepcopy(starting.to_dict())
    ending_payload = copy.deepcopy(ending.to_dict())
    orders_before = list(orders)
    fills_before = list(fills)

    run_paper_trading_request(request)

    assert request.to_dict() == request_payload
    assert starting.to_dict() == starting_payload
    assert ending.to_dict() == ending_payload
    assert orders == orders_before
    assert fills == fills_before


def test_run_execution_module_does_not_add_persistence_or_summary_behavior(tmp_path) -> None:
    artifact = run_paper_trading_request(make_request())

    assert isinstance(artifact, PaperTradingArtifact)
    assert not hasattr(artifact, "write")
    assert not hasattr(artifact, "save")
    assert not hasattr(artifact, "path")
    assert list(tmp_path.iterdir()) == []


def test_package_exports_work() -> None:
    import el_psy_quant.paper as paper  # noqa: PLC0415

    artifact = paper.run_paper_trading_request(make_request())

    assert paper.run_paper_trading_request is run_paper_trading_request
    assert isinstance(artifact, PaperTradingArtifact)
