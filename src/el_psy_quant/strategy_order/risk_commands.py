"""Pure command contract for deterministic pre-trade risk evaluation."""

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
    validate_digest,
)
from el_psy_quant.strategy_order.order_intents import (
    OrderIntent,
    OrderIntentReference,
    create_order_intent_reference,
    validate_order_intent_reference,
)
from el_psy_quant.strategy_order.risk_policies import (
    PreTradeRiskPolicyReference,
    _clone_pre_trade_risk_policy_reference,
    validate_pre_trade_risk_policy_reference,
)

EVALUATE_PRE_TRADE_RISK_COMMAND_SCHEMA_VERSION = 1


def _clone_order_intent_reference(
    value: OrderIntentReference,
) -> OrderIntentReference:
    validate_order_intent_reference(value)
    result = object.__new__(OrderIntentReference)
    object.__setattr__(result, "schema_version", value.schema_version)
    object.__setattr__(result, "intent_id", value.intent_id)
    object.__setattr__(result, "intent_digest", value.intent_digest)
    return result


def _evaluate_pre_trade_risk_command_payload(
    *,
    schema_version: int,
    intent_reference: OrderIntentReference,
    risk_policy_reference: PreTradeRiskPolicyReference,
    command_idempotency_key: str,
    actor: str,
) -> dict[str, object]:
    """Return the one canonical origin-command payload."""
    return {
        "schema_version": schema_version,
        "intent_reference": intent_reference.to_dict(),
        "risk_policy_reference": risk_policy_reference.to_dict(),
        "command_idempotency_key": command_idempotency_key,
        "actor": actor,
    }


def _evaluate_pre_trade_risk_command_digest(
    *,
    schema_version: int,
    intent_reference: OrderIntentReference,
    risk_policy_reference: PreTradeRiskPolicyReference,
    command_idempotency_key: str,
    actor: str,
) -> str:
    """Digest one exact command for creation and later provenance checks."""
    return canonical_digest(
        _evaluate_pre_trade_risk_command_payload(
            schema_version=schema_version,
            intent_reference=intent_reference,
            risk_policy_reference=risk_policy_reference,
            command_idempotency_key=command_idempotency_key,
            actor=actor,
        )
    )


@dataclass(frozen=True, init=False)
class EvaluatePreTradeRiskCommand:
    """One immutable side-effect-free risk-evaluation command."""

    schema_version: int
    intent_reference: OrderIntentReference
    risk_policy_reference: PreTradeRiskPolicyReference
    command_idempotency_key: str
    actor: str
    command_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return the complete strict-JSON command contract."""
        return {
            **_evaluate_pre_trade_risk_command_payload(
                schema_version=self.schema_version,
                intent_reference=self.intent_reference,
                risk_policy_reference=self.risk_policy_reference,
                command_idempotency_key=self.command_idempotency_key,
                actor=self.actor,
            ),
            "command_digest": self.command_digest,
        }


def _build_command(
    *,
    schema_version: int,
    intent_reference: OrderIntentReference,
    risk_policy_reference: PreTradeRiskPolicyReference,
    command_idempotency_key: str,
    actor: str,
) -> EvaluatePreTradeRiskCommand:
    intent_snapshot = _clone_order_intent_reference(intent_reference)
    policy_snapshot = _clone_pre_trade_risk_policy_reference(
        risk_policy_reference
    )
    result = object.__new__(EvaluatePreTradeRiskCommand)
    for field_name, value in (
        ("schema_version", schema_version),
        ("intent_reference", intent_snapshot),
        ("risk_policy_reference", policy_snapshot),
        ("command_idempotency_key", command_idempotency_key),
        ("actor", actor),
        (
            "command_digest",
            _evaluate_pre_trade_risk_command_digest(
                schema_version=schema_version,
                intent_reference=intent_snapshot,
                risk_policy_reference=policy_snapshot,
                command_idempotency_key=command_idempotency_key,
                actor=actor,
            ),
        ),
    ):
        object.__setattr__(result, field_name, value)
    return result


def create_evaluate_pre_trade_risk_command(
    *,
    intent: OrderIntent,
    risk_policy_reference: PreTradeRiskPolicyReference,
    command_idempotency_key: str,
    actor: str,
    schema_version: int = EVALUATE_PRE_TRADE_RISK_COMMAND_SCHEMA_VERSION,
) -> EvaluatePreTradeRiskCommand:
    """Create a command from one complete intent and explicit policy only."""
    if (
        type(schema_version) is not int
        or schema_version != EVALUATE_PRE_TRADE_RISK_COMMAND_SCHEMA_VERSION
    ):
        raise ValueError(
            f"unsupported risk command schema_version: {schema_version}"
        )
    intent_reference = create_order_intent_reference(intent)
    valid_policy = validate_pre_trade_risk_policy_reference(
        risk_policy_reference
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
    return _build_command(
        schema_version=schema_version,
        intent_reference=intent_reference,
        risk_policy_reference=valid_policy,
        command_idempotency_key=key,
        actor=normalized_actor,
    )


def validate_evaluate_pre_trade_risk_command(
    value: object,
) -> EvaluatePreTradeRiskCommand:
    """Recompute and verify one complete risk-evaluation command."""
    if type(value) is not EvaluatePreTradeRiskCommand:
        raise ValueError("command must be an EvaluatePreTradeRiskCommand")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version
            != EVALUATE_PRE_TRADE_RISK_COMMAND_SCHEMA_VERSION
        ):
            raise ValueError("unsupported risk command schema_version")
        validate_order_intent_reference(value.intent_reference)
        validate_pre_trade_risk_policy_reference(
            value.risk_policy_reference
        )
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
        validate_digest(value.command_digest, field_name="command_digest")
        rebuilt = _build_command(
            schema_version=value.schema_version,
            intent_reference=value.intent_reference,
            risk_policy_reference=value.risk_policy_reference,
            command_idempotency_key=key,
            actor=actor,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("evaluate pre-trade risk command is invalid") from exc
    if rebuilt != value or rebuilt.to_dict() != value.to_dict():
        raise ValueError("evaluate pre-trade risk command is invalid")
    return value
