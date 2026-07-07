import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.execution import (
    ExecutionAssumptions,
    default_execution_assumptions,
    validate_execution_assumptions,
)


def test_valid_assumptions_can_be_created() -> None:
    assumptions = ExecutionAssumptions(
        timing="same_bar",
        price_field="close",
        missing_price_policy="raise",
    )

    assert assumptions.timing == "same_bar"
    assert assumptions.price_field == "close"
    assert assumptions.missing_price_policy == "raise"


def test_padded_or_mixed_case_fields_are_normalized() -> None:
    assumptions = validate_execution_assumptions(
        timing=" Next_Bar ",
        price_field=" OPEN ",
        missing_price_policy=" Raise ",
    )

    assert assumptions == ExecutionAssumptions(
        timing="next_bar",
        price_field="open",
        missing_price_policy="raise",
    )


def test_unsupported_timing_raises_value_error() -> None:
    with pytest.raises(ValueError, match="timing"):
        ExecutionAssumptions(
            timing="intrabar",
            price_field="open",
            missing_price_policy="raise",
        )


def test_unsupported_price_field_raises_value_error() -> None:
    with pytest.raises(ValueError, match="price_field"):
        ExecutionAssumptions(
            timing="next_bar",
            price_field="vwap",
            missing_price_policy="raise",
        )


def test_unsupported_missing_price_policy_raises_value_error() -> None:
    with pytest.raises(ValueError, match="missing_price_policy"):
        ExecutionAssumptions(
            timing="next_bar",
            price_field="open",
            missing_price_policy="skip",
        )


def test_dictionary_output_is_json_compatible() -> None:
    assumptions = ExecutionAssumptions(
        timing="next_bar",
        price_field="open",
        missing_price_policy="raise",
    )

    payload = assumptions.to_dict()

    assert payload == {
        "timing": "next_bar",
        "price_field": "open",
        "missing_price_policy": "raise",
    }
    json.dumps(payload, allow_nan=False)


def test_default_assumptions_are_conservative() -> None:
    assumptions = default_execution_assumptions()

    assert assumptions == ExecutionAssumptions(
        timing="next_bar",
        price_field="open",
        missing_price_policy="raise",
    )


def test_execution_assumptions_are_immutable() -> None:
    assumptions = default_execution_assumptions()

    with pytest.raises(FrozenInstanceError):
        assumptions.timing = "same_bar"  # type: ignore[misc]


def test_package_exports_work() -> None:
    import el_psy_quant.execution as execution

    assert execution.ExecutionAssumptions is ExecutionAssumptions
    assert execution.default_execution_assumptions is default_execution_assumptions
    assert execution.validate_execution_assumptions is validate_execution_assumptions
