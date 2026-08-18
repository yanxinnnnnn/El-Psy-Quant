"""Pure command identities for M34 order creation and future stepping."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from el_psy_quant.paper_account import (
    MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
)
from el_psy_quant.paper_execution._canonical import (
    canonical_digest,
    normalize_bounded_string,
    reject_public_construction,
    validate_digest,
)
from el_psy_quant.paper_execution.policies import (
    PaperExecutionPolicyReference,
    _clone_policy_reference,
    validate_paper_execution_policy_reference,
)
from el_psy_quant.paper_execution.upstream_references import (
    PaperExecutionRiskHandoffReference,
    _clone_intent_reference,
    _clone_risk_handoff,
    validate_paper_execution_risk_handoff_reference,
)
from el_psy_quant.strategy_order import (
    OrderIntentReference,
    validate_order_intent_reference,
)

if TYPE_CHECKING:
    from el_psy_quant.paper_execution.orders import PaperExecutionOrderReference

CREATE_PAPER_EXECUTION_ORDER_COMMAND_SCHEMA_VERSION = 1
STEP_PAPER_EXECUTION_ORDER_COMMAND_SCHEMA_VERSION = 1


def _create_payload(
    *,
    schema_version: int,
    order_intent_reference: OrderIntentReference,
    risk_handoff_reference: PaperExecutionRiskHandoffReference,
    execution_policy_reference: PaperExecutionPolicyReference,
    command_idempotency_key: str,
    actor: str,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "order_intent_reference": order_intent_reference.to_dict(),
        "risk_handoff_reference": risk_handoff_reference.to_dict(),
        "execution_policy_reference": execution_policy_reference.to_dict(),
        "command_idempotency_key": command_idempotency_key,
        "actor": actor,
    }


@dataclass(frozen=True, init=False)
class CreatePaperExecutionOrderCommand:
    """One immutable side-effect-free execution-order creation command."""

    schema_version: int
    order_intent_reference: OrderIntentReference
    risk_handoff_reference: PaperExecutionRiskHandoffReference
    execution_policy_reference: PaperExecutionPolicyReference
    command_idempotency_key: str
    actor: str
    command_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            **_create_payload(
                schema_version=self.schema_version,
                order_intent_reference=self.order_intent_reference,
                risk_handoff_reference=self.risk_handoff_reference,
                execution_policy_reference=self.execution_policy_reference,
                command_idempotency_key=self.command_idempotency_key,
                actor=self.actor,
            ),
            "command_digest": self.command_digest,
        }


def _build_create_command(
    *,
    order_intent_reference: OrderIntentReference,
    risk_handoff_reference: PaperExecutionRiskHandoffReference,
    execution_policy_reference: PaperExecutionPolicyReference,
    command_idempotency_key: str,
    actor: str,
) -> CreatePaperExecutionOrderCommand:
    intent = _clone_intent_reference(order_intent_reference)
    risk = _clone_risk_handoff(risk_handoff_reference)
    policy = _clone_policy_reference(execution_policy_reference)
    payload = _create_payload(
        schema_version=CREATE_PAPER_EXECUTION_ORDER_COMMAND_SCHEMA_VERSION,
        order_intent_reference=intent,
        risk_handoff_reference=risk,
        execution_policy_reference=policy,
        command_idempotency_key=command_idempotency_key,
        actor=actor,
    )
    result = object.__new__(CreatePaperExecutionOrderCommand)
    for field_name, value in (
        (
            "schema_version",
            CREATE_PAPER_EXECUTION_ORDER_COMMAND_SCHEMA_VERSION,
        ),
        ("order_intent_reference", intent),
        ("risk_handoff_reference", risk),
        ("execution_policy_reference", policy),
        ("command_idempotency_key", command_idempotency_key),
        ("actor", actor),
        ("command_digest", canonical_digest(payload)),
    ):
        object.__setattr__(result, field_name, value)
    return result


def create_paper_execution_order_command(
    *,
    order_intent_reference: OrderIntentReference,
    risk_handoff_reference: PaperExecutionRiskHandoffReference,
    execution_policy_reference: PaperExecutionPolicyReference,
    command_idempotency_key: str,
    actor: str,
    schema_version: int = CREATE_PAPER_EXECUTION_ORDER_COMMAND_SCHEMA_VERSION,
) -> CreatePaperExecutionOrderCommand:
    """Create one command from trusted compact handoff references."""
    if (
        type(schema_version) is not int
        or schema_version != CREATE_PAPER_EXECUTION_ORDER_COMMAND_SCHEMA_VERSION
    ):
        raise ValueError("unsupported create execution command schema_version")
    intent = validate_order_intent_reference(order_intent_reference)
    risk = validate_paper_execution_risk_handoff_reference(risk_handoff_reference)
    policy = validate_paper_execution_policy_reference(execution_policy_reference)
    if risk.order_intent_reference != intent:
        raise ValueError("risk handoff must reference the exact command intent")
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
    return _build_create_command(
        order_intent_reference=intent,
        risk_handoff_reference=risk,
        execution_policy_reference=policy,
        command_idempotency_key=key,
        actor=normalized_actor,
    )


def validate_create_paper_execution_order_command(
    value: object,
) -> CreatePaperExecutionOrderCommand:
    if type(value) is not CreatePaperExecutionOrderCommand:
        raise ValueError("command must be CreatePaperExecutionOrderCommand")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version
            != CREATE_PAPER_EXECUTION_ORDER_COMMAND_SCHEMA_VERSION
        ):
            raise ValueError("unsupported create command schema_version")
        validate_order_intent_reference(value.order_intent_reference)
        validate_paper_execution_risk_handoff_reference(value.risk_handoff_reference)
        validate_paper_execution_policy_reference(value.execution_policy_reference)
        if (
            value.risk_handoff_reference.order_intent_reference
            != value.order_intent_reference
        ):
            raise ValueError("risk handoff does not match command intent")
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
        rebuilt = _build_create_command(
            order_intent_reference=value.order_intent_reference,
            risk_handoff_reference=value.risk_handoff_reference,
            execution_policy_reference=value.execution_policy_reference,
            command_idempotency_key=key,
            actor=actor,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("create paper execution order command is invalid") from exc
    if rebuilt != value or rebuilt.to_dict() != value.to_dict():
        raise ValueError("create paper execution order command is invalid")
    return value


def _step_payload(
    *,
    schema_version: int,
    execution_order_reference: PaperExecutionOrderReference,
    expected_execution_version: int,
    command_idempotency_key: str,
    actor: str,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "execution_order_reference": execution_order_reference.to_dict(),
        "expected_execution_version": expected_execution_version,
        "command_idempotency_key": command_idempotency_key,
        "actor": actor,
    }


@dataclass(frozen=True, init=False)
class StepPaperExecutionOrderCommand:
    """Identity-only command for the future S209 one-event step operation."""

    schema_version: int
    execution_order_reference: PaperExecutionOrderReference
    expected_execution_version: int
    command_idempotency_key: str
    actor: str
    command_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            **_step_payload(
                schema_version=self.schema_version,
                execution_order_reference=self.execution_order_reference,
                expected_execution_version=self.expected_execution_version,
                command_idempotency_key=self.command_idempotency_key,
                actor=self.actor,
            ),
            "command_digest": self.command_digest,
        }


def _validate_and_clone_order_reference(
    value: object,
) -> PaperExecutionOrderReference:
    from el_psy_quant.paper_execution.orders import (
        _clone_order_reference,
        validate_paper_execution_order_reference,
    )

    validate_paper_execution_order_reference(value)
    return _clone_order_reference(value)


def _build_step_command(
    *,
    execution_order_reference: PaperExecutionOrderReference,
    expected_execution_version: int,
    command_idempotency_key: str,
    actor: str,
) -> StepPaperExecutionOrderCommand:
    reference = _validate_and_clone_order_reference(execution_order_reference)
    payload = _step_payload(
        schema_version=STEP_PAPER_EXECUTION_ORDER_COMMAND_SCHEMA_VERSION,
        execution_order_reference=reference,
        expected_execution_version=expected_execution_version,
        command_idempotency_key=command_idempotency_key,
        actor=actor,
    )
    result = object.__new__(StepPaperExecutionOrderCommand)
    for field_name, value in (
        (
            "schema_version",
            STEP_PAPER_EXECUTION_ORDER_COMMAND_SCHEMA_VERSION,
        ),
        ("execution_order_reference", reference),
        ("expected_execution_version", expected_execution_version),
        ("command_idempotency_key", command_idempotency_key),
        ("actor", actor),
        ("command_digest", canonical_digest(payload)),
    ):
        object.__setattr__(result, field_name, value)
    return result


def create_step_paper_execution_order_command(
    *,
    execution_order_reference: PaperExecutionOrderReference,
    expected_execution_version: int,
    command_idempotency_key: str,
    actor: str,
    schema_version: int = STEP_PAPER_EXECUTION_ORDER_COMMAND_SCHEMA_VERSION,
) -> StepPaperExecutionOrderCommand:
    """Create the future step command without inspecting M31 or M32."""
    if (
        type(schema_version) is not int
        or schema_version != STEP_PAPER_EXECUTION_ORDER_COMMAND_SCHEMA_VERSION
    ):
        raise ValueError("unsupported step execution command schema_version")
    if type(expected_execution_version) is not int or expected_execution_version < 0:
        raise ValueError("expected_execution_version must be non-negative")
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
    return _build_step_command(
        execution_order_reference=execution_order_reference,
        expected_execution_version=expected_execution_version,
        command_idempotency_key=key,
        actor=normalized_actor,
    )


def validate_step_paper_execution_order_command(
    value: object,
) -> StepPaperExecutionOrderCommand:
    if type(value) is not StepPaperExecutionOrderCommand:
        raise ValueError("command must be StepPaperExecutionOrderCommand")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != STEP_PAPER_EXECUTION_ORDER_COMMAND_SCHEMA_VERSION
        ):
            raise ValueError("unsupported step command schema_version")
        _validate_and_clone_order_reference(value.execution_order_reference)
        if (
            type(value.expected_execution_version) is not int
            or value.expected_execution_version < 0
        ):
            raise ValueError("expected_execution_version must be non-negative")
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
        rebuilt = _build_step_command(
            execution_order_reference=value.execution_order_reference,
            expected_execution_version=value.expected_execution_version,
            command_idempotency_key=key,
            actor=actor,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("step paper execution order command is invalid") from exc
    if rebuilt != value or rebuilt.to_dict() != value.to_dict():
        raise ValueError("step paper execution order command is invalid")
    return value
