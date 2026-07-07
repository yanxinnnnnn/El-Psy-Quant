import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.paper import PaperAccountState, create_paper_account_state


def test_valid_paper_account_state_creation() -> None:
    state = create_paper_account_state(
        starting_cash=10_000,
        current_cash=9_500.5,
        positions={" msft ": 2, "AAPL": 1.5},
        timestamp="2026-01-02 09:30:00",
    )

    assert state.starting_cash == 10_000.0
    assert state.current_cash == 9_500.5
    assert state.positions == (("AAPL", 1.5), ("MSFT", 2.0))
    assert state.timestamp.isoformat() == "2026-01-02T09:30:00"


@pytest.mark.parametrize(
    "starting_cash",
    [-1, float("nan"), float("inf"), "1000", True],
)
def test_invalid_starting_cash_raises_value_error(starting_cash: object) -> None:
    with pytest.raises(ValueError, match="starting_cash"):
        create_paper_account_state(
            starting_cash=starting_cash,  # type: ignore[arg-type]
            current_cash=1_000,
            positions={},
            timestamp="2026-01-02",
        )


@pytest.mark.parametrize(
    "current_cash",
    [-1, float("nan"), float("inf"), "1000", False],
)
def test_invalid_current_cash_raises_value_error(current_cash: object) -> None:
    with pytest.raises(ValueError, match="current_cash"):
        create_paper_account_state(
            starting_cash=1_000,
            current_cash=current_cash,  # type: ignore[arg-type]
            positions={},
            timestamp="2026-01-02",
        )


@pytest.mark.parametrize(
    ("positions", "message"),
    [
        ([], "positions must be a mapping"),
        ({" ": 1.0}, "symbol must not be empty"),
        ({"aapl": 1.0, " AAPL ": 2.0}, "duplicate symbol: AAPL"),
        ({"AAPL": "1"}, "AAPL quantity must be finite"),
        ({"AAPL": True}, "AAPL quantity must be finite"),
        ({"AAPL": float("nan")}, "AAPL quantity must be finite"),
        ({"AAPL": float("inf")}, "AAPL quantity must be finite"),
    ],
)
def test_invalid_positions_raise_value_error(
    positions: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        create_paper_account_state(
            starting_cash=1_000,
            current_cash=1_000,
            positions=positions,  # type: ignore[arg-type]
            timestamp="2026-01-02",
        )


@pytest.mark.parametrize("timestamp", [None, "not-a-date"])
def test_invalid_timestamp_raises_value_error(timestamp: object) -> None:
    with pytest.raises(ValueError, match="timestamp"):
        create_paper_account_state(
            starting_cash=1_000,
            current_cash=1_000,
            positions={},
            timestamp=timestamp,
        )


def test_json_compatible_export() -> None:
    state = create_paper_account_state(
        starting_cash=1_000,
        current_cash=750,
        positions={"AAPL": 2},
        timestamp="2026-01-02",
    )

    payload = state.to_dict()

    assert payload == {
        "timestamp": "2026-01-02T00:00:00",
        "starting_cash": 1000.0,
        "current_cash": 750.0,
        "positions": [{"symbol": "AAPL", "quantity": 2.0}],
    }
    json.dumps(payload, allow_nan=False)


def test_deterministic_export_and_stable_position_order() -> None:
    state = create_paper_account_state(
        starting_cash=1_000,
        current_cash=500,
        positions={"msft": 1, "aapl": 2},
        timestamp="2026-01-02",
    )

    assert state.to_dict() == state.to_dict()
    assert state.to_dict()["positions"] == [
        {"symbol": "AAPL", "quantity": 2.0},
        {"symbol": "MSFT", "quantity": 1.0},
    ]


def test_does_not_mutate_caller_provided_positions() -> None:
    positions = {" msft ": 2, "aapl": 1}
    before = positions.copy()

    create_paper_account_state(
        starting_cash=1_000,
        current_cash=500,
        positions=positions,
        timestamp="2026-01-02",
    )

    assert positions == before


def test_explicit_price_equity_snapshot() -> None:
    state = create_paper_account_state(
        starting_cash=1_000,
        current_cash=500,
        positions={"AAPL": 2, "MSFT": -1},
        timestamp="2026-01-02",
    )

    payload = state.to_dict(prices={"msft": 50, "aapl": 100})

    assert payload["equity"] == 650.0


def test_price_snapshot_does_not_mutate_caller_provided_prices() -> None:
    state = create_paper_account_state(
        starting_cash=1_000,
        current_cash=500,
        positions={"AAPL": 2},
        timestamp="2026-01-02",
    )
    prices = {" aapl ": 100}
    before = prices.copy()

    state.to_dict(prices=prices)

    assert prices == before


@pytest.mark.parametrize(
    ("prices", "message"),
    [
        ([], "prices must be a mapping"),
        ({"AAPL": "100"}, "AAPL price must be finite and non-negative"),
        ({"AAPL": True}, "AAPL price must be finite and non-negative"),
        ({"AAPL": -1}, "AAPL price must be finite and non-negative"),
        ({"AAPL": float("nan")}, "AAPL price must be finite and non-negative"),
        ({"AAPL": float("inf")}, "AAPL price must be finite and non-negative"),
        ({"aapl": 100, " AAPL ": 101}, "duplicate price symbol: AAPL"),
        ({"MSFT": 100}, "missing price for symbol: AAPL"),
    ],
)
def test_invalid_prices_raise_value_error(
    prices: object,
    message: str,
) -> None:
    state = create_paper_account_state(
        starting_cash=1_000,
        current_cash=500,
        positions={"AAPL": 2},
        timestamp="2026-01-02",
    )

    with pytest.raises(ValueError, match=message):
        state.to_dict(prices=prices)  # type: ignore[arg-type]


def test_state_is_immutable() -> None:
    state = create_paper_account_state(
        starting_cash=1_000,
        current_cash=500,
        positions={},
        timestamp="2026-01-02",
    )

    with pytest.raises(FrozenInstanceError):
        state.current_cash = 1.0  # type: ignore[misc]


def test_package_exports_work() -> None:
    import el_psy_quant.paper as paper

    assert paper.PaperAccountState is PaperAccountState
    assert paper.create_paper_account_state is create_paper_account_state
