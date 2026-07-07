import json

import pandas as pd
import pytest

from el_psy_quant.execution import (
    AssumedFill,
    ExecutionAssumptions,
    OrderIntent,
    build_execution_realism_artifact,
    summarize_assumed_fills,
)


def make_assumptions(
    *,
    timing: str = "next_bar",
    price_field: str = "open",
) -> ExecutionAssumptions:
    return ExecutionAssumptions(
        timing=timing,
        price_field=price_field,
        missing_price_policy="raise",
    )


def make_order_intent(
    *,
    timestamp: str = "2026-01-02",
    symbol: str = "AAPL",
    side: str = "buy",
    quantity: float = 10.0,
    assumptions: ExecutionAssumptions | None = None,
) -> OrderIntent:
    return OrderIntent(
        timestamp=timestamp,
        symbol=symbol,
        side=side,
        quantity=quantity,
        assumptions=assumptions or make_assumptions(),
    )


def make_assumed_fill(
    *,
    intent_timestamp: str = "2026-01-02",
    fill_timestamp: str = "2026-01-03",
    symbol: str = "AAPL",
    side: str = "buy",
    quantity: float = 10.0,
    price: float = 100.0,
    assumptions: ExecutionAssumptions | None = None,
) -> AssumedFill:
    fill_assumptions = assumptions or make_assumptions()
    return AssumedFill(
        intent_timestamp=pd.Timestamp(intent_timestamp),
        fill_timestamp=pd.Timestamp(fill_timestamp),
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
        price_field=fill_assumptions.price_field,
        assumptions=fill_assumptions,
    )


def test_valid_execution_objects_produce_expected_artifact_shape() -> None:
    assumptions = make_assumptions()
    order_intents = [
        make_order_intent(assumptions=assumptions),
        make_order_intent(
            timestamp="2026-01-04",
            symbol="MSFT",
            side="sell",
            quantity=2.0,
            assumptions=assumptions,
        ),
    ]
    assumed_fills = [
        make_assumed_fill(assumptions=assumptions),
        make_assumed_fill(
            intent_timestamp="2026-01-04",
            fill_timestamp="2026-01-05",
            symbol="MSFT",
            side="sell",
            quantity=2.0,
            price=200.0,
            assumptions=assumptions,
        ),
    ]

    artifact = build_execution_realism_artifact(
        order_intents,
        assumed_fills,
        assumptions=assumptions,
    )

    assert artifact["schema_version"] == "execution_realism.v1"
    assert artifact["assumptions"] == assumptions.to_dict()
    assert artifact["order_intents"] == [item.to_dict() for item in order_intents]
    assert artifact["assumed_fills"] == [item.to_dict() for item in assumed_fills]
    assert artifact["summary"] == summarize_assumed_fills(assumed_fills)
    assert artifact["scope"] == {
        "local_only": True,
        "broker_integration": False,
        "paper_trading": False,
        "live_trading": False,
        "market_microstructure": False,
        "partial_fills": False,
        "position_accounting": False,
        "cash_accounting": False,
    }


def test_summary_is_included_when_supplied() -> None:
    summary = {"fill_count": 1, "custom": "kept"}

    artifact = build_execution_realism_artifact(
        [make_order_intent()],
        [make_assumed_fill()],
        summary=summary,
    )

    assert artifact["summary"] == summary


def test_summary_is_generated_when_omitted() -> None:
    fills = [make_assumed_fill()]

    artifact = build_execution_realism_artifact(
        [make_order_intent()],
        fills,
    )

    assert artifact["summary"] == summarize_assumed_fills(fills)


def test_scope_flags_are_present_and_conservative() -> None:
    artifact = build_execution_realism_artifact(
        [make_order_intent()],
        [make_assumed_fill()],
    )

    scope = artifact["scope"]
    assert scope["local_only"] is True
    assert all(
        scope[key] is False
        for key in [
            "broker_integration",
            "paper_trading",
            "live_trading",
            "market_microstructure",
            "partial_fills",
            "position_accounting",
            "cash_accounting",
        ]
    )


def test_output_is_json_compatible() -> None:
    artifact = build_execution_realism_artifact(
        [make_order_intent()],
        [make_assumed_fill()],
    )

    json.dumps(artifact, allow_nan=False)


@pytest.mark.parametrize("order_intents", [[], make_order_intent(), "bad", object()])
def test_invalid_order_intents_input_raises_value_error(
    order_intents: object,
) -> None:
    with pytest.raises(ValueError, match="order_intents"):
        build_execution_realism_artifact(
            order_intents,  # type: ignore[arg-type]
            [make_assumed_fill()],
        )


@pytest.mark.parametrize("assumed_fills", [[], make_assumed_fill(), "bad", object()])
def test_invalid_assumed_fills_input_raises_value_error(
    assumed_fills: object,
) -> None:
    with pytest.raises(ValueError, match="assumed_fills"):
        build_execution_realism_artifact(
            [make_order_intent()],
            assumed_fills,  # type: ignore[arg-type]
        )


def test_invalid_order_intent_item_raises_value_error() -> None:
    with pytest.raises(ValueError, match="OrderIntent"):
        build_execution_realism_artifact(
            [make_order_intent(), object()],  # type: ignore[list-item]
            [make_assumed_fill()],
        )


def test_invalid_assumed_fill_item_raises_value_error() -> None:
    with pytest.raises(ValueError, match="AssumedFill"):
        build_execution_realism_artifact(
            [make_order_intent()],
            [make_assumed_fill(), object()],  # type: ignore[list-item]
        )


@pytest.mark.parametrize(
    "summary",
    [
        [],
        {"bad": object()},
        {"bad": float("nan")},
    ],
)
def test_invalid_supplied_summary_raises_value_error(summary: object) -> None:
    with pytest.raises(ValueError, match="summary"):
        build_execution_realism_artifact(
            [make_order_intent()],
            [make_assumed_fill()],
            summary=summary,  # type: ignore[arg-type]
        )


def test_invalid_assumptions_raise_value_error() -> None:
    with pytest.raises(ValueError, match="assumptions"):
        build_execution_realism_artifact(
            [make_order_intent()],
            [make_assumed_fill()],
            assumptions={"timing": "next_bar"},  # type: ignore[arg-type]
        )


def test_package_exports_work() -> None:
    import el_psy_quant.execution as execution

    assert (
        execution.build_execution_realism_artifact
        is build_execution_realism_artifact
    )


def test_inputs_are_not_mutated() -> None:
    order_intents = [make_order_intent(), make_order_intent(symbol="MSFT")]
    assumed_fills = [make_assumed_fill(), make_assumed_fill(symbol="MSFT")]
    summary = {"fill_count": 2}
    order_intents_before = list(order_intents)
    assumed_fills_before = list(assumed_fills)
    summary_before = dict(summary)

    build_execution_realism_artifact(order_intents, assumed_fills, summary=summary)

    assert order_intents == order_intents_before
    assert assumed_fills == assumed_fills_before
    assert summary == summary_before
