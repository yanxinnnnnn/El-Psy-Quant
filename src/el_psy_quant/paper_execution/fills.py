"""Immutable unsettled M34 Paper execution Fill authority."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from el_psy_quant.paper_account import PaperQuantity
from el_psy_quant.paper_execution._arithmetic import exact_quantity
from el_psy_quant.paper_execution._canonical import (
    canonical_digest,
    normalize_utc_datetime,
    reject_public_construction,
    validate_digest,
)
from el_psy_quant.paper_execution.attempts import (
    PAPER_EXECUTION_ATTEMPT_RESULT_FILL,
    PaperExecutionAttempt,
    PaperExecutionAttemptReference,
    _clone_attempt_reference,
    create_paper_execution_attempt_reference,
    validate_paper_execution_attempt,
    validate_paper_execution_attempt_reference,
)
from el_psy_quant.paper_execution.costs import (
    PaperExecutionCostEvidence,
    _clone_cost_evidence,
    validate_paper_execution_cost_evidence,
)
from el_psy_quant.paper_execution.market_events import (
    PaperExecutionEventReference,
    _clone_event_reference,
    validate_paper_execution_event_reference,
)
from el_psy_quant.paper_execution.orders import (
    PaperExecutionOrderReference,
    _clone_order_reference,
    validate_paper_execution_order_reference,
)
from el_psy_quant.paper_execution.pricing import (
    PaperExecutionPriceEvidence,
    _clone_price_evidence,
    validate_paper_execution_price_evidence,
)

PAPER_EXECUTION_FILL_SCHEMA_VERSION = 1
PAPER_EXECUTION_FILL_REFERENCE_SCHEMA_VERSION = 1


def _payload(
    *,
    schema_version: int,
    execution_order_reference: PaperExecutionOrderReference,
    attempt_reference: PaperExecutionAttemptReference,
    execution_event_reference: PaperExecutionEventReference,
    side: str,
    fill_quantity: PaperQuantity,
    execution_price_evidence: PaperExecutionPriceEvidence,
    cost_evidence: PaperExecutionCostEvidence,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "execution_order_reference": execution_order_reference.to_dict(),
        "attempt_reference": attempt_reference.to_dict(),
        "execution_event_reference": execution_event_reference.to_dict(),
        "side": side,
        "fill_quantity": fill_quantity.to_json_value(),
        "execution_price_evidence": execution_price_evidence.to_dict(),
        "cost_evidence": cost_evidence.to_dict(),
    }


@dataclass(frozen=True, init=False)
class PaperExecutionFill:
    """One deterministic execution Fill; M31 settlement is not implied."""

    schema_version: int
    fill_id: str
    fill_digest: str
    execution_order_reference: PaperExecutionOrderReference
    attempt_reference: PaperExecutionAttemptReference
    execution_event_reference: PaperExecutionEventReference
    side: str
    fill_quantity: PaperQuantity
    execution_price_evidence: PaperExecutionPriceEvidence
    cost_evidence: PaperExecutionCostEvidence
    created_at: datetime

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            **_payload(
                schema_version=self.schema_version,
                execution_order_reference=self.execution_order_reference,
                attempt_reference=self.attempt_reference,
                execution_event_reference=self.execution_event_reference,
                side=self.side,
                fill_quantity=self.fill_quantity,
                execution_price_evidence=self.execution_price_evidence,
                cost_evidence=self.cost_evidence,
            ),
            "fill_id": self.fill_id,
            "fill_digest": self.fill_digest,
            "created_at": self.created_at.isoformat(),
        }


def _build_fill(
    *,
    execution_order_reference: PaperExecutionOrderReference,
    attempt_reference: PaperExecutionAttemptReference,
    execution_event_reference: PaperExecutionEventReference,
    side: str,
    fill_quantity: PaperQuantity,
    execution_price_evidence: PaperExecutionPriceEvidence,
    cost_evidence: PaperExecutionCostEvidence,
    created_at: datetime,
) -> PaperExecutionFill:
    order_ref = _clone_order_reference(execution_order_reference)
    attempt_ref = _clone_attempt_reference(attempt_reference)
    event_ref = _clone_event_reference(execution_event_reference)
    quantity = PaperQuantity.parse(fill_quantity.canonical)
    price = _clone_price_evidence(execution_price_evidence)
    costs = _clone_cost_evidence(cost_evidence)
    payload = _payload(
        schema_version=PAPER_EXECUTION_FILL_SCHEMA_VERSION,
        execution_order_reference=order_ref,
        attempt_reference=attempt_ref,
        execution_event_reference=event_ref,
        side=side,
        fill_quantity=quantity,
        execution_price_evidence=price,
        cost_evidence=costs,
    )
    digest = canonical_digest(payload)
    result = object.__new__(PaperExecutionFill)
    values = {
        "schema_version": PAPER_EXECUTION_FILL_SCHEMA_VERSION,
        "fill_id": f"pef_{digest}",
        "fill_digest": digest,
        "execution_order_reference": order_ref,
        "attempt_reference": attempt_ref,
        "execution_event_reference": event_ref,
        "side": side,
        "fill_quantity": quantity,
        "execution_price_evidence": price,
        "cost_evidence": costs,
        "created_at": created_at,
    }
    for field_name, value in values.items():
        object.__setattr__(result, field_name, value)
    return result


def _create_paper_execution_fill(
    *,
    attempt: PaperExecutionAttempt,
    fill_quantity: PaperQuantity,
    created_at: datetime,
) -> PaperExecutionFill:
    valid_attempt = validate_paper_execution_attempt(attempt)
    quantity = exact_quantity(
        fill_quantity,
        field_name="fill_quantity",
        strictly_positive=True,
    )
    if (
        valid_attempt.attempt_result != PAPER_EXECUTION_ATTEMPT_RESULT_FILL
        or valid_attempt.consumed_event_reference is None
        or valid_attempt.risk_revalidation is None
        or valid_attempt.risk_revalidation.outcome != "allow"
    ):
        raise ValueError("Fill requires one compatible allowed Fill Attempt")
    risk = valid_attempt.risk_revalidation
    if quantity != risk.candidate_fill_quantity:
        raise ValueError("Fill quantity must equal the derived risk candidate")
    audit_time = normalize_utc_datetime(created_at, field_name="created_at")
    result = _build_fill(
        execution_order_reference=valid_attempt.execution_order_reference,
        attempt_reference=create_paper_execution_attempt_reference(valid_attempt),
        execution_event_reference=valid_attempt.consumed_event_reference,
        side=risk.execution_price_evidence.side,
        fill_quantity=quantity,
        execution_price_evidence=risk.execution_price_evidence,
        cost_evidence=risk.cost_evidence,
        created_at=audit_time,
    )
    return validate_paper_execution_fill(result)


def validate_paper_execution_fill(value: object) -> PaperExecutionFill:
    if type(value) is not PaperExecutionFill:
        raise ValueError("fill must be PaperExecutionFill")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != PAPER_EXECUTION_FILL_SCHEMA_VERSION
            or value.side not in {"buy", "sell"}
        ):
            raise ValueError("fill metadata is invalid")
        validate_paper_execution_order_reference(value.execution_order_reference)
        validate_paper_execution_attempt_reference(value.attempt_reference)
        event = validate_paper_execution_event_reference(
            value.execution_event_reference
        )
        quantity = exact_quantity(
            value.fill_quantity,
            field_name="fill_quantity",
            strictly_positive=True,
        )
        price = validate_paper_execution_price_evidence(
            value.execution_price_evidence
        )
        costs = validate_paper_execution_cost_evidence(value.cost_evidence)
        if not (
            price.execution_event_reference == event
            and price.side == value.side
            and costs.execution_price_evidence == price
            and costs.fill_quantity == quantity
        ):
            raise ValueError("Fill evidence anchors are incompatible")
        audit_time = normalize_utc_datetime(value.created_at, field_name="created_at")
        if audit_time != value.created_at:
            raise ValueError("Fill created_at must be normalized")
        validate_digest(value.fill_digest, field_name="fill_digest")
        if value.fill_id != f"pef_{value.fill_digest}":
            raise ValueError("Fill ID does not match digest")
        expected = _build_fill(
            execution_order_reference=value.execution_order_reference,
            attempt_reference=value.attempt_reference,
            execution_event_reference=event,
            side=value.side,
            fill_quantity=quantity,
            execution_price_evidence=price,
            cost_evidence=costs,
            created_at=value.created_at,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper execution Fill is invalid") from exc
    if expected != value or expected.to_dict() != value.to_dict():
        raise ValueError("paper execution Fill is invalid")
    return value


@dataclass(frozen=True, init=False)
class PaperExecutionFillReference:
    schema_version: int
    fill_id: str
    fill_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "fill_id": self.fill_id,
            "fill_digest": self.fill_digest,
        }


def create_paper_execution_fill_reference(
    fill: PaperExecutionFill,
) -> PaperExecutionFillReference:
    valid = validate_paper_execution_fill(fill)
    result = object.__new__(PaperExecutionFillReference)
    object.__setattr__(
        result,
        "schema_version",
        PAPER_EXECUTION_FILL_REFERENCE_SCHEMA_VERSION,
    )
    object.__setattr__(result, "fill_id", valid.fill_id)
    object.__setattr__(result, "fill_digest", valid.fill_digest)
    return result


def validate_paper_execution_fill_reference(
    value: object,
) -> PaperExecutionFillReference:
    if type(value) is not PaperExecutionFillReference:
        raise ValueError("fill reference must be PaperExecutionFillReference")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != PAPER_EXECUTION_FILL_REFERENCE_SCHEMA_VERSION
        ):
            raise ValueError("unsupported Fill reference schema_version")
        validate_digest(value.fill_digest, field_name="fill_digest")
        if value.fill_id != f"pef_{value.fill_digest}":
            raise ValueError("Fill reference ID does not match digest")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper execution Fill reference is invalid") from exc
    return value
