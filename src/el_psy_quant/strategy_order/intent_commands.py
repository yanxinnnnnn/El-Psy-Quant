"""Pure account-bound command for deterministic Order Intent derivation."""

from __future__ import annotations

from dataclasses import dataclass

from el_psy_quant.paper_account import (
    MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
    PaperAccountLedgerState,
)
from el_psy_quant.strategy_order._canonical import (
    canonical_digest,
    normalize_bounded_string,
    reject_public_construction,
    validate_digest,
)
from el_psy_quant.strategy_order.account_references import (
    OrderIntentAccountReference,
    _clone_order_intent_account_reference,
    create_order_intent_account_reference,
    validate_order_intent_account_reference,
)
from el_psy_quant.strategy_order.signals import (
    StrategySignal,
    StrategySignalReference,
    create_strategy_signal_reference,
    validate_strategy_signal_reference,
)

DERIVE_ORDER_INTENT_COMMAND_SCHEMA_VERSION = 1
ORDER_INTENT_POLICY_VERSION = "target_position_quantity_delta_v1"


def _clone_signal_reference(
    value: StrategySignalReference,
) -> StrategySignalReference:
    validate_strategy_signal_reference(value)
    result = object.__new__(StrategySignalReference)
    object.__setattr__(result, "schema_version", value.schema_version)
    object.__setattr__(result, "signal_id", value.signal_id)
    object.__setattr__(result, "signal_digest", value.signal_digest)
    return result


def _payload_without_digest(
    *,
    schema_version: int,
    signal_reference: StrategySignalReference,
    account_reference: OrderIntentAccountReference,
    intent_policy_version: str,
    command_idempotency_key: str,
    actor: str,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "signal_reference": signal_reference.to_dict(),
        "account_reference": account_reference.to_dict(),
        "intent_policy_version": intent_policy_version,
        "command_idempotency_key": command_idempotency_key,
        "actor": actor,
    }


def _derive_order_intent_command_digest(
    *,
    schema_version: int,
    signal_reference: StrategySignalReference,
    account_reference: OrderIntentAccountReference,
    intent_policy_version: str,
    command_idempotency_key: str,
    actor: str,
) -> str:
    return canonical_digest(
        _payload_without_digest(
            schema_version=schema_version,
            signal_reference=signal_reference,
            account_reference=account_reference,
            intent_policy_version=intent_policy_version,
            command_idempotency_key=command_idempotency_key,
            actor=actor,
        )
    )


@dataclass(frozen=True, init=False)
class DeriveOrderIntentCommand:
    """Immutable side-effect-free input for exact signal-to-delta conversion."""

    schema_version: int
    signal_reference: StrategySignalReference
    account_reference: OrderIntentAccountReference
    intent_policy_version: str
    command_idempotency_key: str
    actor: str
    command_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return the complete strict-JSON command contract."""
        return {
            **_payload_without_digest(
                schema_version=self.schema_version,
                signal_reference=self.signal_reference,
                account_reference=self.account_reference,
                intent_policy_version=self.intent_policy_version,
                command_idempotency_key=self.command_idempotency_key,
                actor=self.actor,
            ),
            "command_digest": self.command_digest,
        }


def _build_command(
    *,
    schema_version: int,
    signal_reference: StrategySignalReference,
    account_reference: OrderIntentAccountReference,
    intent_policy_version: str,
    command_idempotency_key: str,
    actor: str,
) -> DeriveOrderIntentCommand:
    signal_snapshot = _clone_signal_reference(signal_reference)
    account_snapshot = _clone_order_intent_account_reference(account_reference)
    result = object.__new__(DeriveOrderIntentCommand)
    for field_name, value in (
        ("schema_version", schema_version),
        ("signal_reference", signal_snapshot),
        ("account_reference", account_snapshot),
        ("intent_policy_version", intent_policy_version),
        ("command_idempotency_key", command_idempotency_key),
        ("actor", actor),
        (
            "command_digest",
            _derive_order_intent_command_digest(
                schema_version=schema_version,
                signal_reference=signal_snapshot,
                account_reference=account_snapshot,
                intent_policy_version=intent_policy_version,
                command_idempotency_key=command_idempotency_key,
                actor=actor,
            ),
        ),
    ):
        object.__setattr__(result, field_name, value)
    return result


def create_derive_order_intent_command(
    *,
    signal: StrategySignal,
    account_state: PaperAccountLedgerState,
    command_idempotency_key: str,
    actor: str,
    intent_policy_version: str = ORDER_INTENT_POLICY_VERSION,
    schema_version: int = DERIVE_ORDER_INTENT_COMMAND_SCHEMA_VERSION,
) -> DeriveOrderIntentCommand:
    """Create one exact command without deriving side or quantity."""
    if (
        type(schema_version) is not int
        or schema_version != DERIVE_ORDER_INTENT_COMMAND_SCHEMA_VERSION
    ):
        raise ValueError(
            f"unsupported derive-intent schema_version: {schema_version}"
        )
    if intent_policy_version != ORDER_INTENT_POLICY_VERSION:
        raise ValueError(
            f"unsupported intent_policy_version: {intent_policy_version}"
        )
    key = normalize_bounded_string(
        command_idempotency_key,
        field_name="command_idempotency_key",
        maximum_length=MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
    )
    normalized_actor = normalize_bounded_string(
        actor,
        field_name="actor",
        maximum_length=MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    )
    signal_reference = create_strategy_signal_reference(signal)
    account_reference = create_order_intent_account_reference(
        signal=signal,
        account_state=account_state,
    )
    return _build_command(
        schema_version=schema_version,
        signal_reference=signal_reference,
        account_reference=account_reference,
        intent_policy_version=intent_policy_version,
        command_idempotency_key=key,
        actor=normalized_actor,
    )


def validate_derive_order_intent_command(
    value: object,
) -> DeriveOrderIntentCommand:
    """Recompute and verify one complete intent-derivation command."""
    if type(value) is not DeriveOrderIntentCommand:
        raise ValueError("command must be a DeriveOrderIntentCommand")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version
            != DERIVE_ORDER_INTENT_COMMAND_SCHEMA_VERSION
        ):
            raise ValueError("unsupported derive-intent schema_version")
        validate_strategy_signal_reference(value.signal_reference)
        validate_order_intent_account_reference(value.account_reference)
        if value.intent_policy_version != ORDER_INTENT_POLICY_VERSION:
            raise ValueError("unsupported intent policy")
        key = normalize_bounded_string(
            value.command_idempotency_key,
            field_name="command_idempotency_key",
            maximum_length=MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
        )
        actor = normalize_bounded_string(
            value.actor,
            field_name="actor",
            maximum_length=MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
        )
        if key != value.command_idempotency_key or actor != value.actor:
            raise ValueError("command strings must already be normalized")
        rebuilt = _build_command(
            schema_version=value.schema_version,
            signal_reference=value.signal_reference,
            account_reference=value.account_reference,
            intent_policy_version=value.intent_policy_version,
            command_idempotency_key=key,
            actor=actor,
        )
        validate_digest(value.command_digest, field_name="command_digest")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("derive order intent command is invalid") from exc
    if rebuilt != value or rebuilt.to_dict() != value.to_dict():
        raise ValueError("derive order intent command is invalid")
    return value
