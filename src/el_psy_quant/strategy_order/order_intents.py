"""Immutable deterministic Order Intent and no-action evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

from el_psy_quant.paper_account import (
    MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
    PaperAccountLedgerState,
    PaperQuantity,
    validate_paper_account_ledger_state,
)
from el_psy_quant.strategy_order._canonical import (
    canonical_digest,
    normalize_bounded_string,
    normalize_utc_datetime,
    reject_public_construction,
    validate_digest,
)
from el_psy_quant.strategy_order.account_references import (
    OrderIntentAccountReference,
    _clone_order_intent_account_reference,
    create_order_intent_account_reference,
    validate_order_intent_account_reference,
)
from el_psy_quant.strategy_order.intent_commands import (
    DERIVE_ORDER_INTENT_COMMAND_SCHEMA_VERSION,
    ORDER_INTENT_POLICY_VERSION,
    DeriveOrderIntentCommand,
    _derive_order_intent_command_digest,
    validate_derive_order_intent_command,
)
from el_psy_quant.strategy_order.market_references import (
    StrategySignalMarketReference,
    _clone_strategy_signal_market_reference,
    validate_strategy_signal_market_reference,
)
from el_psy_quant.strategy_order.runtime import TARGET_POSITION_QUANTITY
from el_psy_quant.strategy_order.signals import (
    StrategySignal,
    StrategySignalReference,
    create_strategy_signal_reference,
    validate_strategy_signal,
    validate_strategy_signal_reference,
)

ORDER_INTENT_SCHEMA_VERSION = 1
ORDER_INTENT_REFERENCE_SCHEMA_VERSION = 1
ORDER_INTENT_NO_ACTION_SCHEMA_VERSION = 1

ORDER_INTENT_SIDE_BUY = "buy"
ORDER_INTENT_SIDE_SELL = "sell"
ORDER_INTENT_NO_ACTION_TARGET_SATISFIED = "target_already_satisfied"

SUPPORTED_ORDER_INTENT_RISK_STATUSES = (
    "proposed",
    "risk_allowed",
    "risk_rejected",
)

OrderIntentSide = Literal["buy", "sell"]
OrderIntentRiskStatus = Literal[
    "proposed",
    "risk_allowed",
    "risk_rejected",
]


def validate_order_intent_risk_status(
    value: object,
) -> OrderIntentRiskStatus:
    """Return one exact closed derived lifecycle value or fail closed."""
    if value not in SUPPORTED_ORDER_INTENT_RISK_STATUSES:
        raise ValueError("unsupported order intent risk status")
    return value  # type: ignore[return-value]


def _clone_signal_reference(
    value: StrategySignalReference,
) -> StrategySignalReference:
    validate_strategy_signal_reference(value)
    result = object.__new__(StrategySignalReference)
    object.__setattr__(result, "schema_version", value.schema_version)
    object.__setattr__(result, "signal_id", value.signal_id)
    object.__setattr__(result, "signal_digest", value.signal_digest)
    return result


def _exact_quantity(value: object, *, field_name: str) -> PaperQuantity:
    if type(value) is not PaperQuantity:
        raise ValueError(f"{field_name} must be PaperQuantity")
    try:
        rebuilt = PaperQuantity.parse(value.canonical)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid PaperQuantity") from exc
    if (
        rebuilt != value
        or rebuilt.decimal_value.as_tuple()
        != value.decimal_value.as_tuple()
    ):
        raise ValueError(f"{field_name} must be a valid PaperQuantity")
    return rebuilt


def _quantity_from_decimal(value: Decimal) -> PaperQuantity:
    canonical = format(value, "f")
    if "." in canonical:
        canonical = canonical.rstrip("0").rstrip(".")
    if canonical in {"", "-0"}:
        canonical = "0"
    return PaperQuantity.parse(canonical)


def _validate_origin(
    *,
    signal_reference: StrategySignalReference,
    account_reference: OrderIntentAccountReference,
    intent_policy_version: str,
    command_idempotency_key: object,
    command_digest: object,
    actor: object,
) -> tuple[str, str, str]:
    key = normalize_bounded_string(
        command_idempotency_key,
        field_name="origin_command_idempotency_key",
        maximum_length=MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
    )
    normalized_actor = normalize_bounded_string(
        actor,
        field_name="origin_actor",
        maximum_length=MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    )
    if key != command_idempotency_key or normalized_actor != actor:
        raise ValueError("origin audit strings must already be normalized")
    digest = validate_digest(
        command_digest,
        field_name="origin_command_digest",
    )
    expected_digest = _derive_order_intent_command_digest(
        schema_version=DERIVE_ORDER_INTENT_COMMAND_SCHEMA_VERSION,
        signal_reference=signal_reference,
        account_reference=account_reference,
        intent_policy_version=intent_policy_version,
        command_idempotency_key=key,
        actor=normalized_actor,
    )
    if digest != expected_digest:
        raise ValueError("origin command digest does not match command content")
    return key, digest, normalized_actor


def _result_identity_payload(
    *,
    schema_version: int,
    signal_reference: StrategySignalReference,
    market_reference: StrategySignalMarketReference,
    account_reference: OrderIntentAccountReference,
    target_semantics: str,
    target_position_quantity: PaperQuantity,
    current_position_quantity: PaperQuantity,
    intent_policy_version: str,
    side: OrderIntentSide | None = None,
    requested_quantity: PaperQuantity | None = None,
    reason_code: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": schema_version,
        "signal_reference": signal_reference.to_dict(),
        "market_reference": market_reference.to_dict(),
        "account_reference": account_reference.to_dict(),
        "target_semantics": target_semantics,
        "target_position_quantity": target_position_quantity.to_json_value(),
        "current_position_quantity": (
            current_position_quantity.to_json_value()
        ),
        "intent_policy_version": intent_policy_version,
    }
    if side is not None:
        payload["side"] = side
    if requested_quantity is not None:
        payload["requested_quantity"] = requested_quantity.to_json_value()
    if reason_code is not None:
        payload["reason_code"] = reason_code
    return payload


@dataclass(frozen=True, init=False)
class OrderIntent:
    """One immutable account-bound risk-pending trade-delta request."""

    schema_version: int
    intent_id: str
    intent_digest: str
    signal_reference: StrategySignalReference
    market_reference: StrategySignalMarketReference
    account_reference: OrderIntentAccountReference
    target_semantics: str
    target_position_quantity: PaperQuantity
    current_position_quantity: PaperQuantity
    side: OrderIntentSide
    requested_quantity: PaperQuantity
    intent_policy_version: str
    origin_command_idempotency_key: str
    origin_command_digest: str
    origin_actor: str
    created_at: datetime

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return the complete strict-JSON risk-pending request."""
        return {
            "schema_version": self.schema_version,
            "intent_id": self.intent_id,
            "intent_digest": self.intent_digest,
            "signal_reference": self.signal_reference.to_dict(),
            "market_reference": self.market_reference.to_dict(),
            "account_reference": self.account_reference.to_dict(),
            "target_semantics": self.target_semantics,
            "target_position_quantity": (
                self.target_position_quantity.to_json_value()
            ),
            "current_position_quantity": (
                self.current_position_quantity.to_json_value()
            ),
            "side": self.side,
            "requested_quantity": self.requested_quantity.to_json_value(),
            "intent_policy_version": self.intent_policy_version,
            "origin_command_idempotency_key": (
                self.origin_command_idempotency_key
            ),
            "origin_command_digest": self.origin_command_digest,
            "origin_actor": self.origin_actor,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True, init=False)
class OrderIntentNoAction:
    """Deterministic evidence that one exact account already meets its target."""

    schema_version: int
    no_action_id: str
    no_action_digest: str
    reason_code: str
    signal_reference: StrategySignalReference
    market_reference: StrategySignalMarketReference
    account_reference: OrderIntentAccountReference
    target_semantics: str
    target_position_quantity: PaperQuantity
    current_position_quantity: PaperQuantity
    intent_policy_version: str
    origin_command_idempotency_key: str
    origin_command_digest: str
    origin_actor: str
    created_at: datetime

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return the complete strict-JSON no-action evidence."""
        return {
            "schema_version": self.schema_version,
            "no_action_id": self.no_action_id,
            "no_action_digest": self.no_action_digest,
            "reason_code": self.reason_code,
            "signal_reference": self.signal_reference.to_dict(),
            "market_reference": self.market_reference.to_dict(),
            "account_reference": self.account_reference.to_dict(),
            "target_semantics": self.target_semantics,
            "target_position_quantity": (
                self.target_position_quantity.to_json_value()
            ),
            "current_position_quantity": (
                self.current_position_quantity.to_json_value()
            ),
            "intent_policy_version": self.intent_policy_version,
            "origin_command_idempotency_key": (
                self.origin_command_idempotency_key
            ),
            "origin_command_digest": self.origin_command_digest,
            "origin_actor": self.origin_actor,
            "created_at": self.created_at.isoformat(),
        }


def _build_intent(
    *,
    signal_reference: StrategySignalReference,
    market_reference: StrategySignalMarketReference,
    account_reference: OrderIntentAccountReference,
    target_semantics: str,
    target_position_quantity: PaperQuantity,
    current_position_quantity: PaperQuantity,
    side: OrderIntentSide,
    requested_quantity: PaperQuantity,
    intent_policy_version: str,
    origin_command_idempotency_key: str,
    origin_command_digest: str,
    origin_actor: str,
    created_at: datetime,
) -> OrderIntent:
    signal_snapshot = _clone_signal_reference(signal_reference)
    market_snapshot = _clone_strategy_signal_market_reference(market_reference)
    account_snapshot = _clone_order_intent_account_reference(account_reference)
    target = PaperQuantity.parse(target_position_quantity.canonical)
    current = PaperQuantity.parse(current_position_quantity.canonical)
    requested = PaperQuantity.parse(requested_quantity.canonical)
    payload = _result_identity_payload(
        schema_version=ORDER_INTENT_SCHEMA_VERSION,
        signal_reference=signal_snapshot,
        market_reference=market_snapshot,
        account_reference=account_snapshot,
        target_semantics=target_semantics,
        target_position_quantity=target,
        current_position_quantity=current,
        side=side,
        requested_quantity=requested,
        intent_policy_version=intent_policy_version,
    )
    digest = canonical_digest(payload)
    result = object.__new__(OrderIntent)
    values: tuple[tuple[str, object], ...] = (
        ("schema_version", ORDER_INTENT_SCHEMA_VERSION),
        ("intent_id", f"oi_{digest}"),
        ("intent_digest", digest),
        ("signal_reference", signal_snapshot),
        ("market_reference", market_snapshot),
        ("account_reference", account_snapshot),
        ("target_semantics", target_semantics),
        ("target_position_quantity", target),
        ("current_position_quantity", current),
        ("side", side),
        ("requested_quantity", requested),
        ("intent_policy_version", intent_policy_version),
        (
            "origin_command_idempotency_key",
            origin_command_idempotency_key,
        ),
        ("origin_command_digest", origin_command_digest),
        ("origin_actor", origin_actor),
        ("created_at", created_at),
    )
    for field_name, value in values:
        object.__setattr__(result, field_name, value)
    return result


def _build_no_action(
    *,
    signal_reference: StrategySignalReference,
    market_reference: StrategySignalMarketReference,
    account_reference: OrderIntentAccountReference,
    target_semantics: str,
    target_position_quantity: PaperQuantity,
    current_position_quantity: PaperQuantity,
    intent_policy_version: str,
    origin_command_idempotency_key: str,
    origin_command_digest: str,
    origin_actor: str,
    created_at: datetime,
) -> OrderIntentNoAction:
    signal_snapshot = _clone_signal_reference(signal_reference)
    market_snapshot = _clone_strategy_signal_market_reference(market_reference)
    account_snapshot = _clone_order_intent_account_reference(account_reference)
    target = PaperQuantity.parse(target_position_quantity.canonical)
    current = PaperQuantity.parse(current_position_quantity.canonical)
    payload = _result_identity_payload(
        schema_version=ORDER_INTENT_NO_ACTION_SCHEMA_VERSION,
        signal_reference=signal_snapshot,
        market_reference=market_snapshot,
        account_reference=account_snapshot,
        target_semantics=target_semantics,
        target_position_quantity=target,
        current_position_quantity=current,
        reason_code=ORDER_INTENT_NO_ACTION_TARGET_SATISFIED,
        intent_policy_version=intent_policy_version,
    )
    digest = canonical_digest(payload)
    result = object.__new__(OrderIntentNoAction)
    values: tuple[tuple[str, object], ...] = (
        ("schema_version", ORDER_INTENT_NO_ACTION_SCHEMA_VERSION),
        ("no_action_id", f"no_action_{digest}"),
        ("no_action_digest", digest),
        ("reason_code", ORDER_INTENT_NO_ACTION_TARGET_SATISFIED),
        ("signal_reference", signal_snapshot),
        ("market_reference", market_snapshot),
        ("account_reference", account_snapshot),
        ("target_semantics", target_semantics),
        ("target_position_quantity", target),
        ("current_position_quantity", current),
        ("intent_policy_version", intent_policy_version),
        (
            "origin_command_idempotency_key",
            origin_command_idempotency_key,
        ),
        ("origin_command_digest", origin_command_digest),
        ("origin_actor", origin_actor),
        ("created_at", created_at),
    )
    for field_name, value in values:
        object.__setattr__(result, field_name, value)
    return result


def derive_order_intent(
    command: DeriveOrderIntentCommand,
    *,
    signal: StrategySignal,
    account_state: PaperAccountLedgerState,
    created_at: datetime,
) -> OrderIntent | OrderIntentNoAction:
    """Derive an exact buy, sell, or no-action result from bound authority."""
    valid_command = validate_derive_order_intent_command(command)
    valid_signal = validate_strategy_signal(signal)
    validate_paper_account_ledger_state(account_state)
    recreated_signal = create_strategy_signal_reference(valid_signal)
    recreated_account = create_order_intent_account_reference(
        signal=valid_signal,
        account_state=account_state,
    )
    if (
        recreated_signal != valid_command.signal_reference
        or recreated_signal.to_dict()
        != valid_command.signal_reference.to_dict()
        or recreated_account != valid_command.account_reference
        or recreated_account.to_dict()
        != valid_command.account_reference.to_dict()
    ):
        raise ValueError("derive order intent command is stale or mismatched")

    target = _exact_quantity(
        valid_signal.target_position_quantity,
        field_name="target_position_quantity",
    )
    current = _exact_quantity(
        recreated_account.current_instrument_quantity,
        field_name="current_position_quantity",
    )
    normalized_created_at = normalize_utc_datetime(
        created_at,
        field_name="created_at",
    )
    common = {
        "signal_reference": recreated_signal,
        "market_reference": valid_signal.market_reference,
        "account_reference": recreated_account,
        "target_semantics": valid_signal.target_semantics,
        "target_position_quantity": target,
        "current_position_quantity": current,
        "intent_policy_version": valid_command.intent_policy_version,
        "origin_command_idempotency_key": (
            valid_command.command_idempotency_key
        ),
        "origin_command_digest": valid_command.command_digest,
        "origin_actor": valid_command.actor,
        "created_at": normalized_created_at,
    }
    if target.decimal_value == current.decimal_value:
        return _build_no_action(**common)
    if target.decimal_value > current.decimal_value:
        side: OrderIntentSide = ORDER_INTENT_SIDE_BUY
        delta = target.decimal_value - current.decimal_value
    else:
        side = ORDER_INTENT_SIDE_SELL
        delta = current.decimal_value - target.decimal_value
    requested = _quantity_from_decimal(delta)
    if requested.decimal_value <= 0:
        raise ValueError("requested quantity must be strictly positive")
    return _build_intent(
        **common,
        side=side,
        requested_quantity=requested,
    )


def validate_order_intent(value: object) -> OrderIntent:
    """Recompute and verify one complete immutable Order Intent."""
    if type(value) is not OrderIntent:
        raise ValueError("intent must be an OrderIntent")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != ORDER_INTENT_SCHEMA_VERSION
        ):
            raise ValueError("unsupported order intent schema_version")
        validate_strategy_signal_reference(value.signal_reference)
        validate_strategy_signal_market_reference(value.market_reference)
        validate_order_intent_account_reference(value.account_reference)
        if (
            value.market_reference.instrument_id
            != value.account_reference.instrument_id
        ):
            raise ValueError("intent instrument anchors do not match")
        if value.target_semantics != TARGET_POSITION_QUANTITY:
            raise ValueError("unsupported target semantics")
        if value.intent_policy_version != ORDER_INTENT_POLICY_VERSION:
            raise ValueError("unsupported intent policy")
        target = _exact_quantity(
            value.target_position_quantity,
            field_name="target_position_quantity",
        )
        current = _exact_quantity(
            value.current_position_quantity,
            field_name="current_position_quantity",
        )
        requested = _exact_quantity(
            value.requested_quantity,
            field_name="requested_quantity",
        )
        if min(target.decimal_value, current.decimal_value) < 0:
            raise ValueError("position quantities must be non-negative")
        if current != value.account_reference.current_instrument_quantity:
            raise ValueError("current quantity does not match account reference")
        expected_side: OrderIntentSide
        expected_delta: Decimal
        if target.decimal_value > current.decimal_value:
            expected_side = ORDER_INTENT_SIDE_BUY
            expected_delta = target.decimal_value - current.decimal_value
        elif target.decimal_value < current.decimal_value:
            expected_side = ORDER_INTENT_SIDE_SELL
            expected_delta = current.decimal_value - target.decimal_value
        else:
            raise ValueError("equal quantities require no-action evidence")
        if value.side != expected_side:
            raise ValueError("intent side does not match exact delta")
        if requested != _quantity_from_decimal(expected_delta):
            raise ValueError("requested quantity does not match exact delta")
        if requested.decimal_value <= 0:
            raise ValueError("requested quantity must be strictly positive")
        key, command_digest, actor = _validate_origin(
            signal_reference=value.signal_reference,
            account_reference=value.account_reference,
            intent_policy_version=value.intent_policy_version,
            command_idempotency_key=value.origin_command_idempotency_key,
            command_digest=value.origin_command_digest,
            actor=value.origin_actor,
        )
        audit_time = normalize_utc_datetime(
            value.created_at,
            field_name="created_at",
        )
        if audit_time != value.created_at:
            raise ValueError("created_at must be normalized to UTC")
        rebuilt = _build_intent(
            signal_reference=value.signal_reference,
            market_reference=value.market_reference,
            account_reference=value.account_reference,
            target_semantics=value.target_semantics,
            target_position_quantity=target,
            current_position_quantity=current,
            side=expected_side,
            requested_quantity=requested,
            intent_policy_version=value.intent_policy_version,
            origin_command_idempotency_key=key,
            origin_command_digest=command_digest,
            origin_actor=actor,
            created_at=audit_time,
        )
        validate_digest(value.intent_digest, field_name="intent_digest")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("order intent is invalid") from exc
    if rebuilt != value or rebuilt.to_dict() != value.to_dict():
        raise ValueError("order intent is invalid")
    return value


def validate_order_intent_no_action(
    value: object,
) -> OrderIntentNoAction:
    """Recompute and verify deterministic target-satisfied evidence."""
    if type(value) is not OrderIntentNoAction:
        raise ValueError("result must be an OrderIntentNoAction")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != ORDER_INTENT_NO_ACTION_SCHEMA_VERSION
        ):
            raise ValueError("unsupported no-action schema_version")
        if value.reason_code != ORDER_INTENT_NO_ACTION_TARGET_SATISFIED:
            raise ValueError("unsupported no-action reason code")
        validate_strategy_signal_reference(value.signal_reference)
        validate_strategy_signal_market_reference(value.market_reference)
        validate_order_intent_account_reference(value.account_reference)
        if (
            value.market_reference.instrument_id
            != value.account_reference.instrument_id
        ):
            raise ValueError("no-action instrument anchors do not match")
        if value.target_semantics != TARGET_POSITION_QUANTITY:
            raise ValueError("unsupported target semantics")
        if value.intent_policy_version != ORDER_INTENT_POLICY_VERSION:
            raise ValueError("unsupported intent policy")
        target = _exact_quantity(
            value.target_position_quantity,
            field_name="target_position_quantity",
        )
        current = _exact_quantity(
            value.current_position_quantity,
            field_name="current_position_quantity",
        )
        if target.decimal_value < 0 or current.decimal_value < 0:
            raise ValueError("position quantities must be non-negative")
        if target != current:
            raise ValueError("no-action quantities must be equal")
        if current != value.account_reference.current_instrument_quantity:
            raise ValueError("current quantity does not match account reference")
        key, command_digest, actor = _validate_origin(
            signal_reference=value.signal_reference,
            account_reference=value.account_reference,
            intent_policy_version=value.intent_policy_version,
            command_idempotency_key=value.origin_command_idempotency_key,
            command_digest=value.origin_command_digest,
            actor=value.origin_actor,
        )
        audit_time = normalize_utc_datetime(
            value.created_at,
            field_name="created_at",
        )
        if audit_time != value.created_at:
            raise ValueError("created_at must be normalized to UTC")
        rebuilt = _build_no_action(
            signal_reference=value.signal_reference,
            market_reference=value.market_reference,
            account_reference=value.account_reference,
            target_semantics=value.target_semantics,
            target_position_quantity=target,
            current_position_quantity=current,
            intent_policy_version=value.intent_policy_version,
            origin_command_idempotency_key=key,
            origin_command_digest=command_digest,
            origin_actor=actor,
            created_at=audit_time,
        )
        validate_digest(
            value.no_action_digest,
            field_name="no_action_digest",
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("order intent no-action result is invalid") from exc
    if rebuilt != value or rebuilt.to_dict() != value.to_dict():
        raise ValueError("order intent no-action result is invalid")
    return value


@dataclass(frozen=True, init=False)
class OrderIntentReference:
    """Compact immutable pointer to one complete valid Order Intent."""

    schema_version: int
    intent_id: str
    intent_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return only the minimum deterministic intent anchor."""
        return {
            "schema_version": self.schema_version,
            "intent_id": self.intent_id,
            "intent_digest": self.intent_digest,
        }


def create_order_intent_reference(
    intent: OrderIntent,
) -> OrderIntentReference:
    """Create a compact reference from one complete valid intent only."""
    validate_order_intent(intent)
    result = object.__new__(OrderIntentReference)
    object.__setattr__(
        result,
        "schema_version",
        ORDER_INTENT_REFERENCE_SCHEMA_VERSION,
    )
    object.__setattr__(result, "intent_id", intent.intent_id)
    object.__setattr__(result, "intent_digest", intent.intent_digest)
    return result


def validate_order_intent_reference(
    value: object,
) -> OrderIntentReference:
    """Validate one compact Order Intent reference."""
    if type(value) is not OrderIntentReference:
        raise ValueError("intent_reference must be an OrderIntentReference")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != ORDER_INTENT_REFERENCE_SCHEMA_VERSION
        ):
            raise ValueError("unsupported intent-reference schema_version")
        digest = validate_digest(
            value.intent_digest,
            field_name="intent_digest",
        )
        if value.intent_id != f"oi_{digest}":
            raise ValueError("intent_id must match intent_digest")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("order intent reference is invalid") from exc
    return value
