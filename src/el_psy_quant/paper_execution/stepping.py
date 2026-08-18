"""Pure one-event M34 stepping and immutable history reconstruction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from el_psy_quant.market_time import (
    MarketDataReplayEngine,
    ReplayCursor,
    TradingCalendar,
    TradingSession,
    validate_trading_session_for_calendar,
)
from el_psy_quant.paper_account import (
    PaperAccountLedgerState,
    PaperMoney,
    PaperQuantity,
    validate_paper_account_ledger_state,
)
from el_psy_quant.paper_execution._arithmetic import canonical_decimal
from el_psy_quant.paper_execution._canonical import (
    normalize_utc_datetime,
    reject_public_construction,
)
from el_psy_quant.paper_execution.attempts import (
    PAPER_EXECUTION_ATTEMPT_RESULT_BOUNDARY_REJECTED,
    PAPER_EXECUTION_ATTEMPT_RESULT_FILL,
    PAPER_EXECUTION_ATTEMPT_RESULT_NO_FILL,
    PAPER_EXECUTION_ATTEMPT_RESULT_RISK_REJECTED,
    PAPER_EXECUTION_NO_FILL_REASON_EVENT_TYPE_NOT_TRADE,
    PAPER_EXECUTION_NO_FILL_REASON_INSTRUMENT_MISMATCH,
    PAPER_EXECUTION_NO_FILL_REASON_TRADE_PRICE_INVALID,
    PAPER_EXECUTION_TERMINAL_REASON_EXECUTION_RISK_REJECTED,
    PAPER_EXECUTION_TERMINAL_REASON_REPLAY_EXHAUSTED,
    PAPER_EXECUTION_TERMINAL_REASON_SESSION_EXHAUSTED,
    PaperExecutionAttempt,
    _create_paper_execution_attempt,
    validate_paper_execution_attempt,
)
from el_psy_quant.paper_execution.commands import (
    StepPaperExecutionOrderCommand,
    validate_step_paper_execution_order_command,
)
from el_psy_quant.paper_execution.costs import (
    create_paper_execution_cost_evidence,
)
from el_psy_quant.paper_execution.execution_risk import (
    create_paper_execution_risk_revalidation,
)
from el_psy_quant.paper_execution.fills import (
    PaperExecutionFill,
    _create_paper_execution_fill,
    validate_paper_execution_fill,
)
from el_psy_quant.paper_execution.lifecycle import (
    PAPER_EXECUTION_ORDER_STATUS_FILLED,
    PaperExecutionOrderState,
    _clone_order_state,
    _derive_paper_execution_order_state,
    create_initial_paper_execution_order_state,
    validate_paper_execution_order_state,
)
from el_psy_quant.paper_execution.market_events import (
    create_paper_execution_event_reference,
)
from el_psy_quant.paper_execution.orders import (
    PaperExecutionOrder,
    create_paper_execution_order_reference,
    validate_paper_execution_order,
)
from el_psy_quant.paper_execution.pricing import (
    create_paper_execution_price_evidence,
    extract_supported_trade_price,
)
from el_psy_quant.paper_execution.upstream_references import (
    _validate_exact_market_authority,
)

PAPER_EXECUTION_STEP_RESULT_SCHEMA_VERSION = 1


@dataclass(frozen=True, init=False)
class PaperExecutionStepResult:
    """One in-memory Attempt, optional unsettled Fill, and derived next state."""

    schema_version: int
    attempt: PaperExecutionAttempt
    fill: PaperExecutionFill | None
    order_state: PaperExecutionOrderState

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "attempt": self.attempt.to_dict(),
            "fill": None if self.fill is None else self.fill.to_dict(),
            "order_state": self.order_state.to_dict(),
        }


def _step_result(
    *,
    attempt: PaperExecutionAttempt,
    fill: PaperExecutionFill | None,
    order_state: PaperExecutionOrderState,
) -> PaperExecutionStepResult:
    valid_attempt = validate_paper_execution_attempt(attempt)
    valid_fill = None if fill is None else validate_paper_execution_fill(fill)
    state = _clone_order_state(order_state)
    result = object.__new__(PaperExecutionStepResult)
    object.__setattr__(
        result,
        "schema_version",
        PAPER_EXECUTION_STEP_RESULT_SCHEMA_VERSION,
    )
    object.__setattr__(result, "attempt", valid_attempt)
    object.__setattr__(result, "fill", valid_fill)
    object.__setattr__(result, "order_state", state)
    return result


def validate_paper_execution_step_result(
    value: object,
) -> PaperExecutionStepResult:
    if type(value) is not PaperExecutionStepResult:
        raise ValueError("step result must be PaperExecutionStepResult")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != PAPER_EXECUTION_STEP_RESULT_SCHEMA_VERSION
        ):
            raise ValueError("unsupported step result schema_version")
        attempt = validate_paper_execution_attempt(value.attempt)
        fill = (
            None
            if value.fill is None
            else validate_paper_execution_fill(value.fill)
        )
        state = validate_paper_execution_order_state(value.order_state)
        if not (
            state.execution_version == attempt.execution_version_after
            and state.execution_order_reference
            == attempt.execution_order_reference
        ):
            raise ValueError("step result version is inconsistent")
        if (attempt.attempt_result == PAPER_EXECUTION_ATTEMPT_RESULT_FILL) != (
            fill is not None
        ):
            raise ValueError("step result Fill is inconsistent")
        if fill is not None and not (
            fill.execution_order_reference == attempt.execution_order_reference
            and fill.attempt_reference.attempt_id == attempt.attempt_id
            and fill.attempt_reference.attempt_digest == attempt.attempt_digest
        ):
            raise ValueError("step result Fill does not match Attempt")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper execution step result is invalid") from exc
    return value


def _history_values(
    *,
    order: PaperExecutionOrder,
    attempts: tuple[PaperExecutionAttempt, ...],
    fills: tuple[PaperExecutionFill, ...],
) -> tuple[PaperExecutionOrderState, PaperMoney]:
    valid_order = validate_paper_execution_order(order)
    if type(attempts) is not tuple or type(fills) is not tuple:
        raise ValueError("execution history must use immutable tuples")
    order_reference = create_paper_execution_order_reference(valid_order)
    fill_by_attempt: dict[str, PaperExecutionFill] = {}
    for fill in fills:
        valid_fill = validate_paper_execution_fill(fill)
        if valid_fill.execution_order_reference != order_reference:
            raise ValueError("execution Fill references the wrong order")
        attempt_id = valid_fill.attempt_reference.attempt_id
        if attempt_id in fill_by_attempt:
            raise ValueError("one Attempt cannot have duplicate Fills")
        fill_by_attempt[attempt_id] = valid_fill
    state = create_initial_paper_execution_order_state(valid_order)
    cumulative_gross = PaperMoney.parse("0")
    previous_cursor: ReplayCursor | None = None
    consumed_fill_events: set[tuple[str, int]] = set()
    for index, attempt in enumerate(attempts):
        valid_attempt = validate_paper_execution_attempt(attempt)
        if state.terminal:
            raise ValueError("no Attempt may follow terminal execution state")
        if not (
            valid_attempt.execution_order_reference == order_reference
            and valid_attempt.execution_version_before == index
            and valid_attempt.execution_version_after == index + 1
            and valid_attempt.prior_order_state == state
        ):
            raise ValueError("execution Attempt history is not contiguous")
        if previous_cursor is None:
            handoff = valid_order.market_handoff_reference
            pre = valid_attempt.pre_step_cursor
            if not (
                pre.replay_id == handoff.replay_id
                and pre.event_stream_digest == handoff.event_stream_digest
                and pre.position == handoff.cursor_position
                and pre.last_event_id == handoff.last_event_id
                and pre.current_event_time == handoff.current_event_time
            ):
                raise ValueError("first Attempt does not continue the handoff cursor")
        elif valid_attempt.pre_step_cursor != previous_cursor:
            raise ValueError("execution Attempt cursor history is not contiguous")
        previous_cursor = valid_attempt.post_step_cursor
        fill = fill_by_attempt.pop(valid_attempt.attempt_id, None)
        has_fill = valid_attempt.attempt_result == PAPER_EXECUTION_ATTEMPT_RESULT_FILL
        if has_fill != (fill is not None):
            raise ValueError("Fill/Attempt relationship is incomplete")
        cumulative_decimal = state.cumulative_filled_quantity.decimal_value
        if fill is not None:
            if not (
                fill.attempt_reference.attempt_id == valid_attempt.attempt_id
                and fill.attempt_reference.attempt_digest
                == valid_attempt.attempt_digest
                and fill.execution_event_reference
                == valid_attempt.consumed_event_reference
                and fill.side == valid_order.side
            ):
                raise ValueError("Fill does not match its Attempt")
            event_key = (
                fill.execution_event_reference.replay_id,
                fill.execution_event_reference.consumed_event_position,
            )
            if event_key in consumed_fill_events:
                raise ValueError("one order/event pair cannot create duplicate Fill")
            consumed_fill_events.add(event_key)
            cumulative_decimal += fill.fill_quantity.decimal_value
            cumulative_gross = PaperMoney.parse(
                canonical_decimal(
                    cumulative_gross.decimal_value
                    + fill.cost_evidence.gross_notional.decimal_value
                )
            )
        if cumulative_decimal > valid_order.requested_quantity.decimal_value:
            raise ValueError("execution history overfills the order")
        fully_filled = (
            cumulative_decimal == valid_order.requested_quantity.decimal_value
        )
        terminal_rejected = valid_attempt.terminal_reason_code is not None
        if fully_filled:
            if valid_attempt.terminal_reason_code is not None:
                raise ValueError("fully filled Attempt cannot be rejected")
            terminal_rejected = False
        elif valid_attempt.post_step_cursor.status == "completed" and (
            valid_attempt.attempt_result == PAPER_EXECUTION_ATTEMPT_RESULT_FILL
        ):
            if (
                valid_attempt.terminal_reason_code
                != PAPER_EXECUTION_TERMINAL_REASON_REPLAY_EXHAUSTED
            ):
                raise ValueError("partial final Fill must reject the remainder")
        state = _derive_paper_execution_order_state(
            valid_order,
            execution_version=index + 1,
            cumulative_filled_quantity=PaperQuantity.parse(
                canonical_decimal(cumulative_decimal)
            ),
            terminal_rejected=terminal_rejected,
        )
    if fill_by_attempt:
        raise ValueError("execution history contains orphan Fill evidence")
    return state, cumulative_gross


def reconstruct_paper_execution_order_state(
    order: PaperExecutionOrder,
    *,
    attempts: tuple[PaperExecutionAttempt, ...] = (),
    fills: tuple[PaperExecutionFill, ...] = (),
) -> PaperExecutionOrderState:
    """Strictly reconstruct derived lifecycle from immutable Attempt/Fill history."""
    state, _ = _history_values(order=order, attempts=attempts, fills=fills)
    return state


def _verify_execution_context(
    *,
    order: PaperExecutionOrder,
    state: PaperExecutionOrderState,
    attempts: tuple[PaperExecutionAttempt, ...],
    account_state: PaperAccountLedgerState,
    calendar: TradingCalendar,
    session: TradingSession,
    replay_engine: MarketDataReplayEngine,
) -> None:
    account = validate_paper_account_ledger_state(account_state)
    if account.lifecycle_status != "active":
        raise ValueError("paper execution account must remain active")
    if not (
        account.account_identity.account_id == order.account_id
        and account.account_identity.base_currency
        == order.account_handoff_reference.base_currency
    ):
        raise ValueError("paper execution account authority is incompatible")
    valid_calendar, valid_session, valid_engine = _validate_exact_market_authority(
        calendar=calendar,
        session=session,
        replay_engine=replay_engine,
    )
    validate_trading_session_for_calendar(
        calendar=valid_calendar,
        session=valid_session,
    )
    handoff = order.market_handoff_reference
    if not (
        valid_calendar.id == handoff.calendar_id
        and valid_calendar.calendar_version == handoff.calendar_version
        and valid_session.id == handoff.trading_session_id
        and valid_session.trading_date == handoff.trading_date
        and valid_session.open_time == handoff.session_open_time
        and valid_session.close_time == handoff.session_close_time
        and valid_session.session_type == handoff.session_type
        and valid_engine.cursor.replay_id == handoff.replay_id
        and valid_engine.cursor.event_stream_digest == handoff.event_stream_digest
    ):
        raise ValueError("paper execution market authority is incompatible")
    cursor = valid_engine.cursor
    if cursor.status in {"ready", "paused"}:
        raise ValueError("paper execution replay must be running or exhausted")
    if attempts:
        expected = attempts[-1].post_step_cursor
        if cursor != expected:
            raise ValueError("paper execution replay cursor is stale")
    elif not (
        cursor.position == handoff.cursor_position
        and cursor.last_event_id == handoff.last_event_id
        and cursor.current_event_time == handoff.current_event_time
    ):
        raise ValueError("paper execution replay cursor is stale")
    if state.terminal:
        raise ValueError("terminal paper execution order cannot be stepped")


def _next_state(
    order: PaperExecutionOrder,
    *,
    current_state: PaperExecutionOrderState,
    fill_quantity: PaperQuantity | None,
    terminal_rejected: bool,
) -> PaperExecutionOrderState:
    cumulative = current_state.cumulative_filled_quantity.decimal_value
    if fill_quantity is not None:
        cumulative += fill_quantity.decimal_value
    return _derive_paper_execution_order_state(
        order,
        execution_version=current_state.execution_version + 1,
        cumulative_filled_quantity=PaperQuantity.parse(canonical_decimal(cumulative)),
        terminal_rejected=terminal_rejected,
    )


def step_paper_execution_order(
    command: StepPaperExecutionOrderCommand,
    *,
    order: PaperExecutionOrder,
    account_state: PaperAccountLedgerState,
    calendar: TradingCalendar,
    session: TradingSession,
    replay_engine: MarketDataReplayEngine,
    created_at: datetime,
    current_state: PaperExecutionOrderState | None = None,
    attempts: tuple[PaperExecutionAttempt, ...] = (),
    fills: tuple[PaperExecutionFill, ...] = (),
) -> PaperExecutionStepResult:
    """Evaluate exactly one boundary or consume exactly one canonical M32 event."""
    valid_command = validate_step_paper_execution_order_command(command)
    valid_order = validate_paper_execution_order(order)
    order_reference = create_paper_execution_order_reference(valid_order)
    if valid_command.execution_order_reference != order_reference:
        raise ValueError("step command references the wrong execution order")
    reconstructed, cumulative_gross = _history_values(
        order=valid_order,
        attempts=attempts,
        fills=fills,
    )
    if current_state is not None:
        provided = validate_paper_execution_order_state(current_state)
        if provided != reconstructed:
            raise ValueError("current execution state does not match history")
    if valid_command.expected_execution_version != reconstructed.execution_version:
        raise ValueError("step command expected_execution_version is stale")
    audit_time = normalize_utc_datetime(created_at, field_name="created_at")
    _verify_execution_context(
        order=valid_order,
        state=reconstructed,
        attempts=attempts,
        account_state=account_state,
        calendar=calendar,
        session=session,
        replay_engine=replay_engine,
    )
    pre_cursor = replay_engine.cursor
    if pre_cursor.position >= len(replay_engine.events):
        attempt = _create_paper_execution_attempt(
            execution_order_reference=order_reference,
            prior_order_state=reconstructed,
            pre_step_cursor=pre_cursor,
            post_step_cursor=pre_cursor,
            consumed_event_reference=None,
            attempt_result=PAPER_EXECUTION_ATTEMPT_RESULT_BOUNDARY_REJECTED,
            no_fill_reason_code=None,
            terminal_reason_code=PAPER_EXECUTION_TERMINAL_REASON_REPLAY_EXHAUSTED,
            risk_revalidation=None,
            created_at=audit_time,
        )
        return _step_result(
            attempt=attempt,
            fill=None,
            order_state=_next_state(
                valid_order,
                current_state=reconstructed,
                fill_quantity=None,
                terminal_rejected=True,
            ),
        )
    next_event = replay_engine.events[pre_cursor.position]
    if not (session.open_time <= next_event.event_time < session.close_time):
        attempt = _create_paper_execution_attempt(
            execution_order_reference=order_reference,
            prior_order_state=reconstructed,
            pre_step_cursor=pre_cursor,
            post_step_cursor=pre_cursor,
            consumed_event_reference=None,
            attempt_result=PAPER_EXECUTION_ATTEMPT_RESULT_BOUNDARY_REJECTED,
            no_fill_reason_code=None,
            terminal_reason_code=PAPER_EXECUTION_TERMINAL_REASON_SESSION_EXHAUSTED,
            risk_revalidation=None,
            created_at=audit_time,
        )
        return _step_result(
            attempt=attempt,
            fill=None,
            order_state=_next_state(
                valid_order,
                current_state=reconstructed,
                fill_quantity=None,
                terminal_rejected=True,
            ),
        )
    expected_post = ReplayCursor(
        replay_id=pre_cursor.replay_id,
        event_stream_digest=pre_cursor.event_stream_digest,
        position=pre_cursor.position + 1,
        last_event_id=next_event.event_id,
        current_event_time=next_event.event_time,
        status=(
            "completed"
            if pre_cursor.position + 1 == len(replay_engine.events)
            else "running"
        ),
    )
    event_reference = create_paper_execution_event_reference(
        event=next_event,
        pre_step_cursor=pre_cursor,
        post_step_cursor=expected_post,
    )
    no_fill_reason: str | None = None
    if next_event.instrument_id != valid_order.instrument_id:
        no_fill_reason = PAPER_EXECUTION_NO_FILL_REASON_INSTRUMENT_MISMATCH
    elif next_event.event_type != "trade":
        no_fill_reason = PAPER_EXECUTION_NO_FILL_REASON_EVENT_TYPE_NOT_TRADE
    elif extract_supported_trade_price(next_event) is None:
        no_fill_reason = PAPER_EXECUTION_NO_FILL_REASON_TRADE_PRICE_INVALID
    fill: PaperExecutionFill | None = None
    if no_fill_reason is not None:
        terminal = (
            PAPER_EXECUTION_TERMINAL_REASON_REPLAY_EXHAUSTED
            if expected_post.status == "completed"
            else None
        )
        attempt = _create_paper_execution_attempt(
            execution_order_reference=order_reference,
            prior_order_state=reconstructed,
            pre_step_cursor=pre_cursor,
            post_step_cursor=expected_post,
            consumed_event_reference=event_reference,
            attempt_result=PAPER_EXECUTION_ATTEMPT_RESULT_NO_FILL,
            no_fill_reason_code=no_fill_reason,
            terminal_reason_code=terminal,
            risk_revalidation=None,
            created_at=audit_time,
        )
        next_state = _next_state(
            valid_order,
            current_state=reconstructed,
            fill_quantity=None,
            terminal_rejected=terminal is not None,
        )
    else:
        cap = valid_order.execution_policy_reference.max_fill_quantity_per_trade_event
        fill_decimal = reconstructed.remaining_quantity.decimal_value
        if cap is not None:
            fill_decimal = min(fill_decimal, cap.decimal_value)
        fill_quantity = PaperQuantity.parse(canonical_decimal(fill_decimal))
        price = create_paper_execution_price_evidence(
            event=next_event,
            execution_event_reference=event_reference,
            side=valid_order.side,
            execution_policy_reference=valid_order.execution_policy_reference,
        )
        costs = create_paper_execution_cost_evidence(
            execution_price_evidence=price,
            fill_quantity=fill_quantity,
            execution_policy_reference=valid_order.execution_policy_reference,
        )
        risk = create_paper_execution_risk_revalidation(
            order=valid_order,
            current_state=reconstructed,
            account_state=account_state,
            execution_price_evidence=price,
            cost_evidence=costs,
            candidate_fill_quantity=fill_quantity,
            cumulative_filled_gross_notional=cumulative_gross,
        )
        if risk.outcome == "reject":
            attempt = _create_paper_execution_attempt(
                execution_order_reference=order_reference,
                prior_order_state=reconstructed,
                pre_step_cursor=pre_cursor,
                post_step_cursor=expected_post,
                consumed_event_reference=event_reference,
                attempt_result=PAPER_EXECUTION_ATTEMPT_RESULT_RISK_REJECTED,
                no_fill_reason_code=None,
                terminal_reason_code=(
                    PAPER_EXECUTION_TERMINAL_REASON_EXECUTION_RISK_REJECTED
                ),
                risk_revalidation=risk,
                created_at=audit_time,
            )
            next_state = _next_state(
                valid_order,
                current_state=reconstructed,
                fill_quantity=None,
                terminal_rejected=True,
            )
        else:
            fully_filled = (
                fill_quantity.decimal_value
                == reconstructed.remaining_quantity.decimal_value
            )
            terminal = (
                PAPER_EXECUTION_TERMINAL_REASON_REPLAY_EXHAUSTED
                if expected_post.status == "completed" and not fully_filled
                else None
            )
            attempt = _create_paper_execution_attempt(
                execution_order_reference=order_reference,
                prior_order_state=reconstructed,
                pre_step_cursor=pre_cursor,
                post_step_cursor=expected_post,
                consumed_event_reference=event_reference,
                attempt_result=PAPER_EXECUTION_ATTEMPT_RESULT_FILL,
                no_fill_reason_code=None,
                terminal_reason_code=terminal,
                risk_revalidation=risk,
                created_at=audit_time,
            )
            fill = _create_paper_execution_fill(
                attempt=attempt,
                fill_quantity=fill_quantity,
                created_at=audit_time,
            )
            next_state = _next_state(
                valid_order,
                current_state=reconstructed,
                fill_quantity=fill_quantity,
                terminal_rejected=terminal is not None,
            )
    consumed = replay_engine.next_event()
    if consumed != next_event or replay_engine.cursor != expected_post:
        raise ValueError("M32 next_event result did not match execution preflight")
    result = _step_result(attempt=attempt, fill=fill, order_state=next_state)
    if result.order_state.status == PAPER_EXECUTION_ORDER_STATUS_FILLED and (
        result.attempt.terminal_reason_code is not None
    ):
        raise ValueError("filled result cannot carry a terminal rejection")
    return result
