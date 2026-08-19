"""Caller-transaction-owned strict repository for durable M34 execution."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from el_psy_quant.market_time import MarketDataReplayEngine, ReplayCursor
from el_psy_quant.paper_execution import (
    CreatePaperExecutionOrderCommand,
    ExecutionSettlementLink,
    PaperExecutionAttempt,
    PaperExecutionFill,
    PaperExecutionOrder,
    PaperExecutionSettlementResult,
    PaperExecutionStepResult,
    create_paper_execution_event_reference,
    create_paper_execution_order,
    create_paper_execution_order_command,
    create_paper_execution_order_reference,
    create_step_paper_execution_order_command,
    reconcile_paper_execution_settlement,
    reconstruct_paper_execution_order_state,
    validate_paper_execution_step_result,
)
from el_psy_quant.persistence.market_time_repository import (
    SqlAlchemyMarketTimeRepository,
)
from el_psy_quant.persistence.paper_account_repository import (
    SqlAlchemyPaperAccountRepository,
)
from el_psy_quant.persistence.paper_accounts import (
    PaperAccountPersistenceCorruptionError,
)
from el_psy_quant.persistence.paper_account_model import PaperAccountEventRow
from el_psy_quant.persistence.paper_execution_mapping import (
    attempt_from_row,
    attempt_row,
    fill_from_row,
    fill_row,
    order_from_row,
    order_row,
    receipt_from_row,
    receipt_row,
    settlement_link_from_row,
    settlement_link_row,
)
from el_psy_quant.persistence.paper_execution_model import (
    PaperExecutionAttemptRow,
    PaperExecutionCommandReceiptRow,
    PaperExecutionFillRow,
    PaperExecutionOrderRow,
    PaperExecutionSettlementLinkRow,
)
from el_psy_quant.persistence.paper_execution_records import (
    RESULT_KIND_ORDER,
    RESULT_KIND_STEP,
    PaperExecutionCommandReceipt,
    PaperExecutionCorruptAuthorityError,
    PaperExecutionHistory,
    PaperExecutionPage,
    PaperExecutionReconciliationRequiredError,
    PaperExecutionStepCommit,
    bounded_string,
)
from el_psy_quant.persistence.strategy_order_records import (
    StrategyOrderCorruptAuthorityError,
)
from el_psy_quant.persistence.strategy_order_repository import (
    SqlAlchemyOrderIntentRepository,
    SqlAlchemyPreTradeRiskDecisionRepository,
)


class PaperExecutionRepository(Protocol):
    def get_order(self, *, execution_order_id: str) -> PaperExecutionOrder | None: ...
    def append_order(self, *, order: PaperExecutionOrder) -> PaperExecutionOrder: ...
    def load_historical_history(
        self, *, execution_order_id: str
    ) -> PaperExecutionHistory: ...
    def load_history(self, *, execution_order_id: str) -> PaperExecutionHistory: ...


class SqlAlchemyPaperExecutionRepository:
    """Strict immutable M34 repository that never commits caller work."""

    def __init__(self, *, session: Session) -> None:
        if not isinstance(session, Session):
            raise TypeError("session must be a SQLAlchemy Session")
        self._session = session

    def get_order(self, *, execution_order_id: str) -> PaperExecutionOrder | None:
        row = self._session.get(
            PaperExecutionOrderRow,
            bounded_string(execution_order_id, "execution_order_id", 96),
        )
        return None if row is None else order_from_row(row)

    def get_order_by_digest(
        self, *, execution_order_digest: str
    ) -> PaperExecutionOrder | None:
        row = self._session.scalar(
            select(PaperExecutionOrderRow).where(
                PaperExecutionOrderRow.execution_order_digest
                == bounded_string(execution_order_digest, "execution_order_digest", 64)
            )
        )
        return None if row is None else order_from_row(row)

    def find_create_convergence(
        self, *, command: CreatePaperExecutionOrderCommand
    ) -> PaperExecutionOrder | None:
        rows = tuple(
            self._session.scalars(
                select(PaperExecutionOrderRow).where(
                    PaperExecutionOrderRow.intent_id
                    == command.order_intent_reference.intent_id,
                    PaperExecutionOrderRow.intent_digest
                    == command.order_intent_reference.intent_digest,
                    PaperExecutionOrderRow.risk_decision_id
                    == command.risk_handoff_reference.risk_decision_id,
                    PaperExecutionOrderRow.risk_decision_digest
                    == command.risk_handoff_reference.risk_decision_digest,
                    PaperExecutionOrderRow.policy_reference_digest
                    == command.execution_policy_reference.reference_digest,
                )
            ).all()
        )
        reconstructed = tuple(order_from_row(row) for row in rows)
        matches = tuple(
            order
            for order in reconstructed
            if (
                order.order_intent_reference == command.order_intent_reference
                and order.risk_handoff_reference == command.risk_handoff_reference
                and order.execution_policy_reference
                == command.execution_policy_reference
            )
        )
        if len(matches) > 1:
            raise PaperExecutionCorruptAuthorityError()
        return None if not matches else matches[0]

    def list_orders(
        self,
        *,
        limit: int = 200,
        account_id: str | None = None,
        replay_id: str | None = None,
        trading_session_id: str | None = None,
    ) -> tuple[PaperExecutionOrder, ...]:
        if type(limit) is not int or not 1 <= limit <= 200:
            raise ValueError("limit must be from 1 to 200")
        statement = select(PaperExecutionOrderRow)
        for column, value, name in (
            (PaperExecutionOrderRow.account_id, account_id, "account_id"),
            (PaperExecutionOrderRow.replay_id, replay_id, "replay_id"),
            (
                PaperExecutionOrderRow.trading_session_id,
                trading_session_id,
                "trading_session_id",
            ),
        ):
            if value is not None:
                statement = statement.where(column == bounded_string(value, name))
        rows = self._session.scalars(
            statement.order_by(
                PaperExecutionOrderRow.created_at.desc(),
                PaperExecutionOrderRow.execution_order_id.asc(),
            ).limit(limit)
        ).all()
        return tuple(order_from_row(row) for row in rows)

    def list_orders_page(
        self,
        *,
        limit: int,
        cursor_created_at: datetime | None = None,
        cursor_execution_order_id: str | None = None,
        account_id: str | None = None,
        replay_id: str | None = None,
        trading_session_id: str | None = None,
        instrument_id: str | None = None,
        side: str | None = None,
    ) -> PaperExecutionPage[PaperExecutionOrder]:
        if type(limit) is not int or not 1 <= limit <= 200:
            raise ValueError("limit must be from 1 to 200")
        if (cursor_created_at is None) is not (
            cursor_execution_order_id is None
        ):
            raise ValueError("order cursor anchor is incomplete")
        statement = select(PaperExecutionOrderRow)
        for column, value, name in (
            (PaperExecutionOrderRow.account_id, account_id, "account_id"),
            (PaperExecutionOrderRow.replay_id, replay_id, "replay_id"),
            (
                PaperExecutionOrderRow.trading_session_id,
                trading_session_id,
                "trading_session_id",
            ),
            (
                PaperExecutionOrderRow.instrument_id,
                instrument_id,
                "instrument_id",
            ),
        ):
            if value is not None:
                statement = statement.where(column == bounded_string(value, name))
        if side is not None:
            if side not in {"buy", "sell"}:
                raise ValueError("unsupported side")
            statement = statement.where(PaperExecutionOrderRow.side == side)
        if cursor_created_at is not None:
            if (
                type(cursor_created_at) is not datetime
                or cursor_created_at.tzinfo is None
                or cursor_created_at.utcoffset() is None
                or cursor_created_at.utcoffset().total_seconds() != 0
            ):
                raise ValueError("order cursor timestamp is invalid")
            identity = bounded_string(
                cursor_execution_order_id, "cursor_execution_order_id", 96
            )
            statement = statement.where(
                or_(
                    PaperExecutionOrderRow.created_at < cursor_created_at,
                    and_(
                        PaperExecutionOrderRow.created_at == cursor_created_at,
                        PaperExecutionOrderRow.execution_order_id > identity,
                    ),
                )
            )
        rows = tuple(
            self._session.scalars(
                statement.order_by(
                    PaperExecutionOrderRow.created_at.desc(),
                    PaperExecutionOrderRow.execution_order_id.asc(),
                ).limit(limit + 1)
            ).all()
        )
        return PaperExecutionPage(
            items=tuple(order_from_row(row) for row in rows[:limit]),
            has_more=len(rows) > limit,
        )

    def append_order(self, *, order: PaperExecutionOrder) -> PaperExecutionOrder:
        candidate = order_row(order)
        by_id = self.get_order(execution_order_id=order.execution_order_id)
        by_digest = self.get_order_by_digest(
            execution_order_digest=order.execution_order_digest
        )
        existing = by_id or by_digest
        if existing is not None:
            if existing != order or existing.to_dict() != order.to_dict():
                raise PaperExecutionCorruptAuthorityError()
            return existing
        self._session.add(candidate)
        self._session.flush()
        return order

    def get_attempt(self, *, attempt_id: str) -> PaperExecutionAttempt | None:
        row = self._session.get(
            PaperExecutionAttemptRow, bounded_string(attempt_id, "attempt_id", 96)
        )
        return None if row is None else attempt_from_row(row)

    def get_attempt_for_version(
        self, *, execution_order_id: str, execution_version_before: int
    ) -> PaperExecutionAttempt | None:
        if type(execution_version_before) is not int or execution_version_before < 0:
            raise ValueError("execution_version_before must be non-negative")
        row = self._session.scalar(
            select(PaperExecutionAttemptRow).where(
                PaperExecutionAttemptRow.execution_order_id
                == bounded_string(execution_order_id, "execution_order_id", 96),
                PaperExecutionAttemptRow.execution_version_before
                == execution_version_before,
            )
        )
        return None if row is None else attempt_from_row(row)

    def list_attempts(
        self, *, execution_order_id: str
    ) -> tuple[PaperExecutionAttempt, ...]:
        rows = self._session.scalars(
            select(PaperExecutionAttemptRow)
            .where(
                PaperExecutionAttemptRow.execution_order_id
                == bounded_string(execution_order_id, "execution_order_id", 96)
            )
            .order_by(PaperExecutionAttemptRow.execution_version_before.asc())
        ).all()
        return tuple(attempt_from_row(row) for row in rows)

    def append_attempt(
        self, *, attempt: PaperExecutionAttempt
    ) -> PaperExecutionAttempt:
        existing = self.get_attempt(attempt_id=attempt.attempt_id)
        by_version = self.get_attempt_for_version(
            execution_order_id=attempt.execution_order_reference.execution_order_id,
            execution_version_before=attempt.execution_version_before,
        )
        current = existing or by_version
        if current is not None:
            if current != attempt or current.to_dict() != attempt.to_dict():
                raise PaperExecutionCorruptAuthorityError()
            return current
        self._session.add(attempt_row(attempt))
        self._session.flush()
        return attempt

    def get_fill(self, *, fill_id: str) -> PaperExecutionFill | None:
        row = self._session.get(
            PaperExecutionFillRow, bounded_string(fill_id, "fill_id", 96)
        )
        return None if row is None else fill_from_row(row)

    def get_fill_for_attempt(self, *, attempt_id: str) -> PaperExecutionFill | None:
        row = self._session.scalar(
            select(PaperExecutionFillRow).where(
                PaperExecutionFillRow.attempt_id
                == bounded_string(attempt_id, "attempt_id", 96)
            )
        )
        return None if row is None else fill_from_row(row)

    def list_fills(self, *, execution_order_id: str) -> tuple[PaperExecutionFill, ...]:
        rows = self._session.scalars(
            select(PaperExecutionFillRow)
            .join(
                PaperExecutionAttemptRow,
                PaperExecutionAttemptRow.attempt_id == PaperExecutionFillRow.attempt_id,
            )
            .where(
                PaperExecutionFillRow.execution_order_id
                == bounded_string(execution_order_id, "execution_order_id", 96)
            )
            .order_by(
                PaperExecutionAttemptRow.execution_version_before.asc(),
                PaperExecutionFillRow.fill_id.asc(),
            )
        ).all()
        return tuple(fill_from_row(row) for row in rows)

    def list_fills_page(
        self,
        *,
        limit: int,
        cursor_created_at: datetime | None = None,
        cursor_fill_id: str | None = None,
        execution_order_id: str | None = None,
    ) -> PaperExecutionPage[PaperExecutionFill]:
        if type(limit) is not int or not 1 <= limit <= 200:
            raise ValueError("limit must be from 1 to 200")
        if (cursor_created_at is None) is not (cursor_fill_id is None):
            raise ValueError("Fill cursor anchor is incomplete")
        statement = select(PaperExecutionFillRow)
        if execution_order_id is not None:
            statement = statement.where(
                PaperExecutionFillRow.execution_order_id
                == bounded_string(execution_order_id, "execution_order_id", 96)
            )
        if cursor_created_at is not None:
            if (
                type(cursor_created_at) is not datetime
                or cursor_created_at.tzinfo is None
                or cursor_created_at.utcoffset() is None
                or cursor_created_at.utcoffset().total_seconds() != 0
            ):
                raise ValueError("Fill cursor timestamp is invalid")
            identity = bounded_string(cursor_fill_id, "cursor_fill_id", 96)
            statement = statement.where(
                or_(
                    PaperExecutionFillRow.created_at < cursor_created_at,
                    and_(
                        PaperExecutionFillRow.created_at == cursor_created_at,
                        PaperExecutionFillRow.fill_id > identity,
                    ),
                )
            )
        rows = tuple(
            self._session.scalars(
                statement.order_by(
                    PaperExecutionFillRow.created_at.desc(),
                    PaperExecutionFillRow.fill_id.asc(),
                ).limit(limit + 1)
            ).all()
        )
        return PaperExecutionPage(
            items=tuple(fill_from_row(row) for row in rows[:limit]),
            has_more=len(rows) > limit,
        )

    def append_fill(self, *, fill: PaperExecutionFill) -> PaperExecutionFill:
        existing = self.get_fill(fill_id=fill.fill_id)
        by_attempt = self.get_fill_for_attempt(
            attempt_id=fill.attempt_reference.attempt_id
        )
        current = existing or by_attempt
        if current is not None:
            if current != fill or current.to_dict() != fill.to_dict():
                raise PaperExecutionCorruptAuthorityError()
            return current
        self._session.add(fill_row(fill))
        self._session.flush()
        return fill

    def get_settlement_link(
        self, *, settlement_link_id: str
    ) -> ExecutionSettlementLink | None:
        row = self._session.get(
            PaperExecutionSettlementLinkRow,
            bounded_string(settlement_link_id, "settlement_link_id", 96),
        )
        return None if row is None else settlement_link_from_row(row)

    def get_settlement_link_for_fill(
        self, *, fill_id: str
    ) -> ExecutionSettlementLink | None:
        row = self._session.scalar(
            select(PaperExecutionSettlementLinkRow).where(
                PaperExecutionSettlementLinkRow.fill_id
                == bounded_string(fill_id, "fill_id", 96)
            )
        )
        return None if row is None else settlement_link_from_row(row)

    def append_settlement_link(
        self, *, link: ExecutionSettlementLink
    ) -> ExecutionSettlementLink:
        existing = self.get_settlement_link(settlement_link_id=link.settlement_link_id)
        by_fill = self.get_settlement_link_for_fill(
            fill_id=link.execution_fill_reference.fill_id
        )
        current = existing or by_fill
        if current is not None:
            if current != link or current.to_dict() != link.to_dict():
                raise PaperExecutionCorruptAuthorityError()
            return current
        event = self._session.get(PaperAccountEventRow, link.account_event_id)
        if event is None:
            raise PaperExecutionCorruptAuthorityError()
        recorded = event.recorded_timestamp
        if recorded.tzinfo is None:
            recorded = recorded.replace(tzinfo=timezone.utc)
        self._session.add(settlement_link_row(link, recorded_at=recorded))
        self._session.flush()
        return link

    def get_receipt(
        self, *, namespace: str, command_idempotency_key: str
    ) -> PaperExecutionCommandReceipt | None:
        row = self._session.get(
            PaperExecutionCommandReceiptRow,
            (
                bounded_string(namespace, "namespace", 64),
                bounded_string(command_idempotency_key, "command key", 128),
            ),
        )
        return None if row is None else receipt_from_row(row)

    def append_receipt(
        self, *, receipt: PaperExecutionCommandReceipt
    ) -> PaperExecutionCommandReceipt:
        self.resolve_receipt(receipt=receipt)
        existing = self.get_receipt(
            namespace=receipt.namespace,
            command_idempotency_key=receipt.command_idempotency_key,
        )
        if existing is not None:
            if existing != receipt:
                raise PaperExecutionCorruptAuthorityError()
            return existing
        self._session.add(receipt_row(receipt))
        self._session.flush()
        return receipt

    def _step_commit(
        self, *, order: PaperExecutionOrder, attempt: PaperExecutionAttempt
    ) -> PaperExecutionStepCommit:
        attempts = self.list_attempts(execution_order_id=order.execution_order_id)
        prefix = tuple(
            item
            for item in attempts
            if item.execution_version_after <= attempt.execution_version_after
        )
        if not prefix or prefix[-1] != attempt:
            raise PaperExecutionCorruptAuthorityError()
        fills = tuple(
            fill
            for fill in self.list_fills(execution_order_id=order.execution_order_id)
            if fill.attempt_reference.attempt_id in {item.attempt_id for item in prefix}
        )
        fill = next(
            (
                item
                for item in fills
                if item.attempt_reference.attempt_id == attempt.attempt_id
            ),
            None,
        )
        state = reconstruct_paper_execution_order_state(
            order, attempts=prefix, fills=fills
        )
        result = object.__new__(PaperExecutionStepResult)
        object.__setattr__(result, "schema_version", 1)
        object.__setattr__(result, "attempt", attempt)
        object.__setattr__(result, "fill", fill)
        object.__setattr__(result, "order_state", state)
        validate_paper_execution_step_result(result)
        link = (
            None
            if fill is None
            else self.get_settlement_link_for_fill(fill_id=fill.fill_id)
        )
        if (fill is None) is not (link is None):
            raise PaperExecutionCorruptAuthorityError()
        return PaperExecutionStepCommit(
            step_result=result,
            settlement_link=link,
            account_event_id=None if link is None else link.account_event_id,
        )

    def resolve_receipt(
        self, *, receipt: PaperExecutionCommandReceipt
    ) -> PaperExecutionOrder | PaperExecutionStepCommit:
        order = self.get_order(execution_order_id=receipt.execution_order_id)
        if (
            order is None
            or order.execution_order_digest != receipt.execution_order_digest
        ):
            raise PaperExecutionCorruptAuthorityError()
        if receipt.result_kind == RESULT_KIND_ORDER:
            expected = create_paper_execution_order_command(
                order_intent_reference=order.order_intent_reference,
                risk_handoff_reference=order.risk_handoff_reference,
                execution_policy_reference=order.execution_policy_reference,
                command_idempotency_key=receipt.command_idempotency_key,
                actor=receipt.command_actor,
            ).command_digest
            history = self.load_historical_history(
                execution_order_id=order.execution_order_id
            )
            result: PaperExecutionOrder | PaperExecutionStepCommit = history.order
        elif receipt.result_kind == RESULT_KIND_STEP and receipt.attempt_id is not None:
            attempt = self.get_attempt(attempt_id=receipt.attempt_id)
            if attempt is None or attempt.attempt_digest != receipt.attempt_digest:
                raise PaperExecutionCorruptAuthorityError()
            expected = create_step_paper_execution_order_command(
                execution_order_reference=create_paper_execution_order_reference(order),
                expected_execution_version=attempt.execution_version_before,
                command_idempotency_key=receipt.command_idempotency_key,
                actor=receipt.command_actor,
            ).command_digest
            result = self._step_commit(order=order, attempt=attempt)
            history = self.load_historical_history(
                execution_order_id=order.execution_order_id
            )
            if attempt not in history.attempts:
                raise PaperExecutionCorruptAuthorityError()
            step = result.step_result
            link = result.settlement_link
            if (step.fill is None and receipt.fill_id is not None) or (
                step.fill is not None
                and (
                    step.fill.fill_id != receipt.fill_id
                    or step.fill.fill_digest != receipt.fill_digest
                    or link is None
                    or link.settlement_link_id != receipt.settlement_link_id
                    or link.settlement_link_evidence_digest
                    != receipt.settlement_link_evidence_digest
                    or link.account_event_id != receipt.account_event_id
                )
            ):
                raise PaperExecutionCorruptAuthorityError()
        else:
            raise PaperExecutionCorruptAuthorityError()
        if expected != receipt.command_digest:
            raise PaperExecutionCorruptAuthorityError()
        return result

    def load_historical_history(
        self, *, execution_order_id: str
    ) -> PaperExecutionHistory:
        """Reconstruct committed authority without requiring live upstream heads."""
        order = self.get_order(execution_order_id=execution_order_id)
        if order is None:
            raise PaperExecutionCorruptAuthorityError()
        attempts = self.list_attempts(execution_order_id=execution_order_id)
        fills = self.list_fills(execution_order_id=execution_order_id)
        try:
            state = reconstruct_paper_execution_order_state(
                order, attempts=attempts, fills=fills
            )
        except ValueError as exc:
            raise PaperExecutionCorruptAuthorityError() from exc

        try:
            intent = SqlAlchemyOrderIntentRepository(session=self._session).get(
                intent_id=order.order_intent_reference.intent_id
            )
            decision = SqlAlchemyPreTradeRiskDecisionRepository(
                session=self._session
            ).get(decision_id=order.risk_handoff_reference.risk_decision_id)
        except StrategyOrderCorruptAuthorityError as exc:
            raise PaperExecutionCorruptAuthorityError() from exc
        if intent is None or decision is None:
            raise PaperExecutionCorruptAuthorityError()

        market = SqlAlchemyMarketTimeRepository(session=self._session)
        try:
            replay = market.get_replay(
                replay_id=order.market_handoff_reference.replay_id
            )
            calendar = market.get_calendar(
                calendar_id=order.market_handoff_reference.calendar_id
            )
            session = market.get_session(
                session_id=order.market_handoff_reference.trading_session_id
            )
        except ValueError as exc:
            raise PaperExecutionCorruptAuthorityError() from exc
        if replay is None or calendar is None or session is None:
            raise PaperExecutionCorruptAuthorityError()
        for attempt in attempts:
            event_ref = attempt.consumed_event_reference
            if event_ref is None:
                continue
            position = event_ref.consumed_event_position
            if position < 1 or position > len(replay.events):
                raise PaperExecutionCorruptAuthorityError()
            event = replay.events[position - 1]
            try:
                expected_event_reference = create_paper_execution_event_reference(
                    event=event,
                    pre_step_cursor=attempt.pre_step_cursor,
                    post_step_cursor=attempt.post_step_cursor,
                )
            except ValueError as exc:
                raise PaperExecutionCorruptAuthorityError() from exc
            if expected_event_reference != event_ref:
                raise PaperExecutionCorruptAuthorityError()

        account_repo = SqlAlchemyPaperAccountRepository(session=self._session)
        try:
            account = account_repo.get_account(account_id=order.account_id)
            if account is None:
                raise PaperExecutionCorruptAuthorityError()
            account_history = account_repo.get_history(account=account)
        except PaperAccountPersistenceCorruptionError as exc:
            raise PaperExecutionCorruptAuthorityError() from exc
        handoff_version = order.account_handoff_reference.account_head_version
        if handoff_version < 1 or handoff_version > len(account_history):
            raise PaperExecutionCorruptAuthorityError()
        handoff_state = account_history[handoff_version - 1].resulting_state

        try:
            handoff = order.market_handoff_reference
            historical_replay = MarketDataReplayEngine(
                replay_id=handoff.replay_id,
                events=replay.events,
                cursor=ReplayCursor(
                    replay_id=handoff.replay_id,
                    event_stream_digest=handoff.event_stream_digest,
                    position=handoff.cursor_position,
                    last_event_id=handoff.last_event_id,
                    current_event_time=handoff.current_event_time,
                    status=handoff.handoff_replay_status,
                ),
            )
            origin_command = create_paper_execution_order_command(
                order_intent_reference=order.order_intent_reference,
                risk_handoff_reference=order.risk_handoff_reference,
                execution_policy_reference=order.execution_policy_reference,
                command_idempotency_key=order.origin_command_idempotency_key,
                actor=order.origin_actor,
            )
            expected_order = create_paper_execution_order(
                origin_command,
                intent=intent,
                decision=decision,
                account_state=handoff_state,
                calendar=calendar,
                session=session,
                replay_engine=historical_replay,
                created_at=order.created_at,
            )
        except ValueError as exc:
            raise PaperExecutionCorruptAuthorityError() from exc
        if expected_order != order or expected_order.to_dict() != order.to_dict():
            raise PaperExecutionCorruptAuthorityError()

        links: list[ExecutionSettlementLink] = []
        previous_version = handoff_version
        fill_by_id = {fill.fill_id: fill for fill in fills}
        attempt_by_id = {attempt.attempt_id: attempt for attempt in attempts}
        for fill in fills:
            link = self.get_settlement_link_for_fill(fill_id=fill.fill_id)
            if link is None:
                raise PaperExecutionCorruptAuthorityError()
            if (
                link.account_version != previous_version + 1
                or link.account_version > len(account_history)
            ):
                raise PaperExecutionCorruptAuthorityError()
            bundle = account_history[link.account_version - 1]
            prior_state = account_history[link.account_version - 2].resulting_state
            result = object.__new__(PaperExecutionSettlementResult)
            object.__setattr__(result, "schema_version", 1)
            object.__setattr__(result, "ledger_bundle", bundle)
            object.__setattr__(result, "settlement_link", link)
            try:
                reconcile_paper_execution_settlement(
                    account_state=prior_state,
                    order=order,
                    attempt=attempt_by_id[fill.attempt_reference.attempt_id],
                    fill=fill,
                    result=result,
                )
            except (KeyError, ValueError) as exc:
                raise PaperExecutionCorruptAuthorityError() from exc
            previous_version = link.account_version
            links.append(link)
        all_link_rows = self._session.scalars(
            select(PaperExecutionSettlementLinkRow).where(
                PaperExecutionSettlementLinkRow.execution_order_id == execution_order_id
            )
        ).all()
        if len(all_link_rows) != len(links) or set(fill_by_id) != {
            link.execution_fill_reference.fill_id for link in links
        }:
            raise PaperExecutionCorruptAuthorityError()

        return PaperExecutionHistory(
            order=order,
            attempts=attempts,
            fills=fills,
            settlement_links=tuple(links),
            state=state,
        )

    def validate_current_working_authority(
        self, *, history: PaperExecutionHistory
    ) -> PaperExecutionHistory:
        """Require live M31/M32 freshness only for a working Order."""
        if type(history) is not PaperExecutionHistory:
            raise TypeError("history must be PaperExecutionHistory")
        if history.state.terminal:
            return history

        order = history.order
        try:
            account = SqlAlchemyPaperAccountRepository(
                session=self._session
            ).get_account(account_id=order.account_id)
            replay = SqlAlchemyMarketTimeRepository(session=self._session).get_replay(
                replay_id=order.market_handoff_reference.replay_id
            )
        except (PaperAccountPersistenceCorruptionError, ValueError) as exc:
            raise PaperExecutionCorruptAuthorityError() from exc
        if account is None or replay is None:
            raise PaperExecutionCorruptAuthorityError()

        links = history.settlement_links
        expected_account_version = (
            order.account_handoff_reference.account_head_version
            if not links
            else links[-1].account_version
        )
        expected_account_event_id = (
            order.account_handoff_reference.account_head_event_id
            if not links
            else links[-1].account_event_id
        )
        expected_account_chain_digest = (
            order.account_handoff_reference.account_head_chain_digest
            if not links
            else links[-1].account_chain_digest
        )
        if (
            account.head_version != expected_account_version
            or account.head_event_id != expected_account_event_id
            or account.head_chain_digest != expected_account_chain_digest
        ):
            raise PaperExecutionReconciliationRequiredError()

        expected_cursor = (
            history.attempts[-1].post_step_cursor
            if history.attempts
            else ReplayCursor(
                replay_id=order.market_handoff_reference.replay_id,
                event_stream_digest=(
                    order.market_handoff_reference.event_stream_digest
                ),
                position=order.market_handoff_reference.cursor_position,
                last_event_id=order.market_handoff_reference.last_event_id,
                current_event_time=(
                    order.market_handoff_reference.current_event_time
                ),
                status=order.market_handoff_reference.handoff_replay_status,
            )
        )
        if replay.session.cursor != expected_cursor:
            raise PaperExecutionReconciliationRequiredError()
        return history

    def load_history(self, *, execution_order_id: str) -> PaperExecutionHistory:
        """Reconstruct authority and require a working Order's live freshness."""
        history = self.load_historical_history(
            execution_order_id=execution_order_id
        )
        return self.validate_current_working_authority(history=history)


__all__ = ["PaperExecutionRepository", "SqlAlchemyPaperExecutionRepository"]
