"""In-memory execution realism artifacts for local deterministic backtests."""

from collections.abc import Mapping, Sequence
import json

from el_psy_quant.execution.assumptions import ExecutionAssumptions
from el_psy_quant.execution.fills import AssumedFill
from el_psy_quant.execution.orders import OrderIntent
from el_psy_quant.execution.summary import summarize_assumed_fills

EXECUTION_REALISM_SCHEMA_VERSION = "execution_realism.v1"

EXECUTION_REALISM_SCOPE = {
    "local_only": True,
    "broker_integration": False,
    "paper_trading": False,
    "live_trading": False,
    "market_microstructure": False,
    "partial_fills": False,
    "position_accounting": False,
    "cash_accounting": False,
}


def _validate_sequence(
    value: object,
    *,
    field_name: str,
    single_type: type[object],
) -> Sequence[object]:
    if isinstance(value, single_type):
        raise ValueError(f"{field_name} must be a non-empty sequence")
    if isinstance(value, str):
        raise ValueError(f"{field_name} must be a non-empty sequence")
    if not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a non-empty sequence")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    return value


def _validate_order_intents(
    order_intents: object,
) -> Sequence[OrderIntent]:
    values = _validate_sequence(
        order_intents,
        field_name="order_intents",
        single_type=OrderIntent,
    )
    for item in values:
        if not isinstance(item, OrderIntent):
            raise ValueError("order_intents must contain only OrderIntent objects")
    return values


def _validate_assumed_fills(
    assumed_fills: object,
) -> Sequence[AssumedFill]:
    values = _validate_sequence(
        assumed_fills,
        field_name="assumed_fills",
        single_type=AssumedFill,
    )
    for item in values:
        if not isinstance(item, AssumedFill):
            raise ValueError("assumed_fills must contain only AssumedFill objects")
    return values


def _validate_json_compatible(value: object, *, field_name: str) -> object:
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be JSON-compatible") from exc
    return value


def _resolve_assumptions(
    assumptions: ExecutionAssumptions | None,
    assumed_fills: Sequence[AssumedFill],
    order_intents: Sequence[OrderIntent],
) -> ExecutionAssumptions:
    if assumptions is not None:
        if not isinstance(assumptions, ExecutionAssumptions):
            raise ValueError("assumptions must be an ExecutionAssumptions instance")
        return assumptions
    if assumed_fills:
        return assumed_fills[0].assumptions
    return order_intents[0].assumptions


def build_execution_realism_artifact(
    order_intents: Sequence[OrderIntent],
    assumed_fills: Sequence[AssumedFill],
    assumptions: ExecutionAssumptions | None = None,
    summary: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Build a deterministic in-memory execution realism artifact."""
    validated_order_intents = _validate_order_intents(order_intents)
    validated_assumed_fills = _validate_assumed_fills(assumed_fills)
    resolved_assumptions = _resolve_assumptions(
        assumptions,
        validated_assumed_fills,
        validated_order_intents,
    )

    if summary is None:
        serialized_summary = summarize_assumed_fills(validated_assumed_fills)
    else:
        if not isinstance(summary, Mapping):
            raise ValueError("summary must be a mapping")
        serialized_summary = dict(summary)
        _validate_json_compatible(serialized_summary, field_name="summary")

    artifact = {
        "schema_version": EXECUTION_REALISM_SCHEMA_VERSION,
        "assumptions": resolved_assumptions.to_dict(),
        "order_intents": [intent.to_dict() for intent in validated_order_intents],
        "assumed_fills": [fill.to_dict() for fill in validated_assumed_fills],
        "summary": serialized_summary,
        "scope": dict(EXECUTION_REALISM_SCOPE),
    }
    _validate_json_compatible(artifact, field_name="artifact")
    return artifact
