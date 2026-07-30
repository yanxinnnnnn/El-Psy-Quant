"""Pure command contract for future deterministic signal evaluation."""

from __future__ import annotations

from dataclasses import dataclass

from el_psy_quant.paper_account import (
    MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
)
from el_psy_quant.strategy_order._canonical import (
    canonical_digest,
    normalize_bounded_string,
    reject_public_construction,
)
from el_psy_quant.strategy_order.market_references import (
    StrategySignalMarketReference,
    _clone_strategy_signal_market_reference,
    validate_strategy_signal_market_reference,
)
from el_psy_quant.strategy_order.runtime import (
    StrategyRuntimeReference,
    _clone_strategy_runtime_reference,
    validate_strategy_runtime_reference,
)

EVALUATE_STRATEGY_SIGNAL_COMMAND_SCHEMA_VERSION = 1


@dataclass(frozen=True, init=False)
class EvaluateStrategySignalCommand:
    """Immutable side-effect-free input for the future S199 evaluator."""

    schema_version: int
    strategy_runtime_reference: StrategyRuntimeReference
    market_reference: StrategySignalMarketReference
    command_idempotency_key: str
    actor: str
    command_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return the complete deterministic JSON-compatible command."""
        return {
            "schema_version": self.schema_version,
            "strategy_runtime_reference": (
                self.strategy_runtime_reference.to_dict()
            ),
            "market_reference": self.market_reference.to_dict(),
            "command_idempotency_key": self.command_idempotency_key,
            "actor": self.actor,
            "command_digest": self.command_digest,
        }


def _command_payload_without_digest(
    *,
    schema_version: int,
    strategy_runtime_reference: StrategyRuntimeReference,
    market_reference: StrategySignalMarketReference,
    command_idempotency_key: str,
    actor: str,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "strategy_runtime_reference": strategy_runtime_reference.to_dict(),
        "market_reference": market_reference.to_dict(),
        "command_idempotency_key": command_idempotency_key,
        "actor": actor,
    }


def create_evaluate_strategy_signal_command(
    *,
    strategy_runtime_reference: StrategyRuntimeReference,
    market_reference: StrategySignalMarketReference,
    command_idempotency_key: str,
    actor: str,
    schema_version: int = EVALUATE_STRATEGY_SIGNAL_COMMAND_SCHEMA_VERSION,
) -> EvaluateStrategySignalCommand:
    """Create a pure command without running a strategy or creating a signal."""
    if (
        type(schema_version) is not int
        or schema_version != EVALUATE_STRATEGY_SIGNAL_COMMAND_SCHEMA_VERSION
    ):
        raise ValueError(
            f"unsupported evaluate-signal schema_version: {schema_version}"
        )
    runtime_snapshot = _clone_strategy_runtime_reference(
        strategy_runtime_reference
    )
    market_snapshot = _clone_strategy_signal_market_reference(
        market_reference
    )
    normalized_key = normalize_bounded_string(
        command_idempotency_key,
        field_name="command_idempotency_key",
        maximum_length=MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
    )
    normalized_actor = normalize_bounded_string(
        actor,
        field_name="actor",
        maximum_length=MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    )
    payload = _command_payload_without_digest(
        schema_version=schema_version,
        strategy_runtime_reference=runtime_snapshot,
        market_reference=market_snapshot,
        command_idempotency_key=normalized_key,
        actor=normalized_actor,
    )
    result = object.__new__(EvaluateStrategySignalCommand)
    object.__setattr__(result, "schema_version", schema_version)
    object.__setattr__(
        result,
        "strategy_runtime_reference",
        runtime_snapshot,
    )
    object.__setattr__(result, "market_reference", market_snapshot)
    object.__setattr__(
        result,
        "command_idempotency_key",
        normalized_key,
    )
    object.__setattr__(result, "actor", normalized_actor)
    object.__setattr__(result, "command_digest", canonical_digest(payload))
    return result


def validate_evaluate_strategy_signal_command(
    value: object,
) -> EvaluateStrategySignalCommand:
    """Recompute and verify one complete signal-evaluation command."""
    if type(value) is not EvaluateStrategySignalCommand:
        raise ValueError(
            "command must be an EvaluateStrategySignalCommand"
        )
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version
            != EVALUATE_STRATEGY_SIGNAL_COMMAND_SCHEMA_VERSION
        ):
            raise ValueError("unsupported evaluate-signal schema_version")
        validate_strategy_runtime_reference(
            value.strategy_runtime_reference
        )
        validate_strategy_signal_market_reference(value.market_reference)
        rebuilt = create_evaluate_strategy_signal_command(
            strategy_runtime_reference=value.strategy_runtime_reference,
            market_reference=value.market_reference,
            command_idempotency_key=value.command_idempotency_key,
            actor=value.actor,
            schema_version=value.schema_version,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(
            "evaluate strategy signal command is invalid"
        ) from exc
    if rebuilt != value or rebuilt.to_dict() != value.to_dict():
        raise ValueError("evaluate strategy signal command is invalid")
    return value
