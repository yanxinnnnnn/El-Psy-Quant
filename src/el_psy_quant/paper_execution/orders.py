"""Immutable deterministic M34 Paper execution-order authority."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from el_psy_quant.market_time import (
    MarketDataReplayEngine,
    TradingCalendar,
    TradingSession,
)
from el_psy_quant.paper_account import PaperAccountLedgerState, PaperQuantity
from el_psy_quant.paper_execution._canonical import (
    canonical_digest,
    normalize_utc_datetime,
    reject_public_construction,
    validate_digest,
)
from el_psy_quant.paper_execution.commands import (
    CreatePaperExecutionOrderCommand,
    _build_create_command,
    validate_create_paper_execution_order_command,
)
from el_psy_quant.paper_execution.policies import (
    PaperExecutionPolicyReference,
    _clone_policy_reference,
    validate_paper_execution_policy_reference,
)
from el_psy_quant.paper_execution.upstream_references import (
    PaperExecutionAccountHandoffReference,
    PaperExecutionMarketHandoffReference,
    PaperExecutionRiskHandoffReference,
    _clone_account_handoff,
    _clone_intent_reference,
    _clone_market_handoff,
    _clone_risk_handoff,
    create_paper_execution_account_handoff_reference,
    create_paper_execution_market_handoff_reference,
    create_paper_execution_risk_handoff_reference,
    validate_paper_execution_account_handoff_reference,
    validate_paper_execution_market_handoff_reference,
    validate_paper_execution_risk_handoff_reference,
)
from el_psy_quant.strategy_order import (
    OrderIntent,
    OrderIntentReference,
    PreTradeRiskDecision,
    create_order_intent_reference,
    validate_order_intent,
    validate_order_intent_reference,
)

PAPER_EXECUTION_ORDER_SCHEMA_VERSION = 1
PAPER_EXECUTION_ORDER_REFERENCE_SCHEMA_VERSION = 1


def _exact_positive_quantity(value: object) -> PaperQuantity:
    if type(value) is not PaperQuantity:
        raise ValueError("requested_quantity must be PaperQuantity")
    try:
        rebuilt = PaperQuantity.parse(value.canonical)
    except (AttributeError, ValueError) as exc:
        raise ValueError("requested_quantity is invalid") from exc
    if (
        rebuilt != value
        or rebuilt.decimal_value.as_tuple() != value.decimal_value.as_tuple()
        or rebuilt.decimal_value <= 0
    ):
        raise ValueError("requested_quantity must be strictly positive")
    return rebuilt


def _business_payload(
    *,
    order_intent_reference: OrderIntentReference,
    risk_handoff_reference: PaperExecutionRiskHandoffReference,
    account_handoff_reference: PaperExecutionAccountHandoffReference,
    market_handoff_reference: PaperExecutionMarketHandoffReference,
    execution_policy_reference: PaperExecutionPolicyReference,
    account_id: str,
    instrument_id: str,
    side: str,
    requested_quantity: PaperQuantity,
) -> dict[str, object]:
    return {
        "order_intent_reference": order_intent_reference.to_dict(),
        "risk_handoff_reference": risk_handoff_reference.to_dict(),
        "account_handoff_reference": account_handoff_reference.to_dict(),
        "market_handoff_reference": market_handoff_reference.to_dict(),
        "execution_policy_reference": execution_policy_reference.to_dict(),
        "account_id": account_id,
        "instrument_id": instrument_id,
        "side": side,
        "requested_quantity": requested_quantity.to_json_value(),
    }


@dataclass(frozen=True, init=False)
class PaperExecutionOrder:
    """One immutable M34 execution authority over exact upstream handoff."""

    schema_version: int
    execution_order_id: str
    execution_order_digest: str
    order_intent_reference: OrderIntentReference
    risk_handoff_reference: PaperExecutionRiskHandoffReference
    account_handoff_reference: PaperExecutionAccountHandoffReference
    market_handoff_reference: PaperExecutionMarketHandoffReference
    execution_policy_reference: PaperExecutionPolicyReference
    account_id: str
    instrument_id: str
    side: str
    requested_quantity: PaperQuantity
    origin_command_idempotency_key: str
    origin_command_digest: str
    origin_actor: str
    created_at: datetime

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "execution_order_id": self.execution_order_id,
            "execution_order_digest": self.execution_order_digest,
            **_business_payload(
                order_intent_reference=self.order_intent_reference,
                risk_handoff_reference=self.risk_handoff_reference,
                account_handoff_reference=self.account_handoff_reference,
                market_handoff_reference=self.market_handoff_reference,
                execution_policy_reference=self.execution_policy_reference,
                account_id=self.account_id,
                instrument_id=self.instrument_id,
                side=self.side,
                requested_quantity=self.requested_quantity,
            ),
            "origin_command_idempotency_key": (self.origin_command_idempotency_key),
            "origin_command_digest": self.origin_command_digest,
            "origin_actor": self.origin_actor,
            "created_at": self.created_at.isoformat(),
        }


def _build_order(
    *,
    order_intent_reference: OrderIntentReference,
    risk_handoff_reference: PaperExecutionRiskHandoffReference,
    account_handoff_reference: PaperExecutionAccountHandoffReference,
    market_handoff_reference: PaperExecutionMarketHandoffReference,
    execution_policy_reference: PaperExecutionPolicyReference,
    account_id: str,
    instrument_id: str,
    side: str,
    requested_quantity: PaperQuantity,
    origin_command_idempotency_key: str,
    origin_command_digest: str,
    origin_actor: str,
    created_at: datetime,
) -> PaperExecutionOrder:
    intent = _clone_intent_reference(order_intent_reference)
    risk = _clone_risk_handoff(risk_handoff_reference)
    account = _clone_account_handoff(account_handoff_reference)
    market = _clone_market_handoff(market_handoff_reference)
    policy = _clone_policy_reference(execution_policy_reference)
    quantity = PaperQuantity.parse(requested_quantity.canonical)
    payload = _business_payload(
        order_intent_reference=intent,
        risk_handoff_reference=risk,
        account_handoff_reference=account,
        market_handoff_reference=market,
        execution_policy_reference=policy,
        account_id=account_id,
        instrument_id=instrument_id,
        side=side,
        requested_quantity=quantity,
    )
    digest = canonical_digest(payload)
    result = object.__new__(PaperExecutionOrder)
    for field_name, value in (
        ("schema_version", PAPER_EXECUTION_ORDER_SCHEMA_VERSION),
        ("execution_order_id", f"peo_{digest}"),
        ("execution_order_digest", digest),
        ("order_intent_reference", intent),
        ("risk_handoff_reference", risk),
        ("account_handoff_reference", account),
        ("market_handoff_reference", market),
        ("execution_policy_reference", policy),
        ("account_id", account_id),
        ("instrument_id", instrument_id),
        ("side", side),
        ("requested_quantity", quantity),
        ("origin_command_idempotency_key", origin_command_idempotency_key),
        ("origin_command_digest", origin_command_digest),
        ("origin_actor", origin_actor),
        ("created_at", created_at),
    ):
        object.__setattr__(result, field_name, value)
    return result


def create_paper_execution_order(
    command: CreatePaperExecutionOrderCommand,
    *,
    intent: OrderIntent,
    decision: PreTradeRiskDecision,
    account_state: PaperAccountLedgerState,
    calendar: TradingCalendar,
    session: TradingSession,
    replay_engine: MarketDataReplayEngine,
    created_at: datetime,
) -> PaperExecutionOrder:
    """Create one order after revalidating the complete M31/M32/M33 handoff."""
    valid_command = validate_create_paper_execution_order_command(command)
    valid_intent = validate_order_intent(intent)
    intent_reference = create_order_intent_reference(valid_intent)
    if valid_command.order_intent_reference != intent_reference:
        raise ValueError("create execution command is stale or mismatched")
    risk_handoff = create_paper_execution_risk_handoff_reference(
        decision=decision,
        intent=valid_intent,
    )
    if risk_handoff != valid_command.risk_handoff_reference:
        raise ValueError("create execution risk handoff is stale or mismatched")
    account_handoff = create_paper_execution_account_handoff_reference(
        intent=valid_intent,
        account_state=account_state,
    )
    market_handoff = create_paper_execution_market_handoff_reference(
        calendar=calendar,
        session=session,
        replay_engine=replay_engine,
        intent=valid_intent,
        decision=decision,
    )
    if not (
        account_handoff.account_id == valid_intent.account_reference.account_id
        and account_handoff.instrument_id == valid_intent.market_reference.instrument_id
        and market_handoff.instrument_id == account_handoff.instrument_id
    ):
        raise ValueError("execution handoff account/instrument anchors mismatch")
    audit_time = normalize_utc_datetime(created_at, field_name="created_at")
    return _build_order(
        order_intent_reference=intent_reference,
        risk_handoff_reference=risk_handoff,
        account_handoff_reference=account_handoff,
        market_handoff_reference=market_handoff,
        execution_policy_reference=valid_command.execution_policy_reference,
        account_id=account_handoff.account_id,
        instrument_id=account_handoff.instrument_id,
        side=valid_intent.side,
        requested_quantity=valid_intent.requested_quantity,
        origin_command_idempotency_key=(valid_command.command_idempotency_key),
        origin_command_digest=valid_command.command_digest,
        origin_actor=valid_command.actor,
        created_at=audit_time,
    )


def validate_paper_execution_order(value: object) -> PaperExecutionOrder:
    """Recompute all self-contained references and deterministic order identity."""
    if type(value) is not PaperExecutionOrder:
        raise ValueError("order must be PaperExecutionOrder")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != PAPER_EXECUTION_ORDER_SCHEMA_VERSION
        ):
            raise ValueError("unsupported paper execution order schema_version")
        validate_order_intent_reference(value.order_intent_reference)
        validate_paper_execution_risk_handoff_reference(value.risk_handoff_reference)
        validate_paper_execution_account_handoff_reference(
            value.account_handoff_reference
        )
        validate_paper_execution_market_handoff_reference(
            value.market_handoff_reference
        )
        validate_paper_execution_policy_reference(value.execution_policy_reference)
        if (
            value.risk_handoff_reference.order_intent_reference
            != value.order_intent_reference
        ):
            raise ValueError("order risk handoff does not match intent")
        if not (
            value.account_id == value.account_handoff_reference.account_id
            and value.instrument_id == value.account_handoff_reference.instrument_id
            and value.instrument_id == value.market_handoff_reference.instrument_id
        ):
            raise ValueError("order account/instrument anchors do not match")
        if value.side not in {"buy", "sell"}:
            raise ValueError("order side must be buy or sell")
        quantity = _exact_positive_quantity(value.requested_quantity)
        audit_time = normalize_utc_datetime(
            value.created_at,
            field_name="created_at",
        )
        if audit_time != value.created_at:
            raise ValueError("created_at must be normalized to UTC")
        origin = _build_create_command(
            order_intent_reference=value.order_intent_reference,
            risk_handoff_reference=value.risk_handoff_reference,
            execution_policy_reference=value.execution_policy_reference,
            command_idempotency_key=value.origin_command_idempotency_key,
            actor=value.origin_actor,
        )
        validate_create_paper_execution_order_command(origin)
        if origin.command_digest != value.origin_command_digest:
            raise ValueError("order origin command digest is invalid")
        validate_digest(
            value.execution_order_digest,
            field_name="execution_order_digest",
        )
        rebuilt = _build_order(
            order_intent_reference=value.order_intent_reference,
            risk_handoff_reference=value.risk_handoff_reference,
            account_handoff_reference=value.account_handoff_reference,
            market_handoff_reference=value.market_handoff_reference,
            execution_policy_reference=value.execution_policy_reference,
            account_id=value.account_id,
            instrument_id=value.instrument_id,
            side=value.side,
            requested_quantity=quantity,
            origin_command_idempotency_key=(value.origin_command_idempotency_key),
            origin_command_digest=value.origin_command_digest,
            origin_actor=value.origin_actor,
            created_at=audit_time,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper execution order is invalid") from exc
    if rebuilt != value or rebuilt.to_dict() != value.to_dict():
        raise ValueError("paper execution order is invalid")
    return value


@dataclass(frozen=True, init=False)
class PaperExecutionOrderReference:
    """Compact immutable pointer to one complete valid execution order."""

    schema_version: int
    execution_order_id: str
    execution_order_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "execution_order_id": self.execution_order_id,
            "execution_order_digest": self.execution_order_digest,
        }


def create_paper_execution_order_reference(
    order: PaperExecutionOrder,
) -> PaperExecutionOrderReference:
    """Create a compact reference from one complete valid order only."""
    valid = validate_paper_execution_order(order)
    result = object.__new__(PaperExecutionOrderReference)
    object.__setattr__(
        result,
        "schema_version",
        PAPER_EXECUTION_ORDER_REFERENCE_SCHEMA_VERSION,
    )
    object.__setattr__(result, "execution_order_id", valid.execution_order_id)
    object.__setattr__(
        result,
        "execution_order_digest",
        valid.execution_order_digest,
    )
    return result


def validate_paper_execution_order_reference(
    value: object,
) -> PaperExecutionOrderReference:
    if type(value) is not PaperExecutionOrderReference:
        raise ValueError("order reference must be PaperExecutionOrderReference")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != PAPER_EXECUTION_ORDER_REFERENCE_SCHEMA_VERSION
        ):
            raise ValueError("unsupported order reference schema_version")
        digest = validate_digest(
            value.execution_order_digest,
            field_name="execution_order_digest",
        )
        if value.execution_order_id != f"peo_{digest}":
            raise ValueError("execution_order_id must match digest")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper execution order reference is invalid") from exc
    return value


def _clone_order_reference(
    value: PaperExecutionOrderReference,
) -> PaperExecutionOrderReference:
    validate_paper_execution_order_reference(value)
    result = object.__new__(PaperExecutionOrderReference)
    object.__setattr__(result, "schema_version", value.schema_version)
    object.__setattr__(result, "execution_order_id", value.execution_order_id)
    object.__setattr__(
        result,
        "execution_order_digest",
        value.execution_order_digest,
    )
    return result
