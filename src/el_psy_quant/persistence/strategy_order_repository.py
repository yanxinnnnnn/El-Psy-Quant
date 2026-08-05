"""Immutable bounded repositories for durable M33 authority."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from el_psy_quant.persistence.strategy_order_mapping import (
    decision_from_row,
    decision_row,
    intent_from_row,
    intent_row,
    order_intent_no_action_from_payload,
    receipt_from_row,
    receipt_row,
    result_identity,
    signal_from_row,
    signal_row,
)
from el_psy_quant.persistence.strategy_order_model import (
    OrderIntentRow,
    PreTradeRiskDecisionRow,
    StrategyOrderCommandReceiptRow,
    StrategySignalRow,
)
from el_psy_quant.persistence.strategy_order_records import (
    COMMAND_NAMESPACE_DERIVE_INTENT,
    COMMAND_NAMESPACE_EVALUATE_RISK,
    COMMAND_NAMESPACE_EVALUATE_SIGNAL,
    RESULT_KIND_DECISION,
    RESULT_KIND_INTENT,
    RESULT_KIND_NO_ACTION,
    RESULT_KIND_SIGNAL,
    STRATEGY_ORDER_LIST_LIMIT_MAXIMUM,
    StrategyOrderCommandNamespace,
    StrategyOrderCommandReceipt,
    StrategyOrderCorruptAuthorityError,
    StrategyOrderPage,
    StrategyOrderResult,
    load_canonical_json,
)
from el_psy_quant.strategy_order import (
    OrderIntent,
    OrderIntentNoAction,
    PreTradeRiskDecision,
    StrategySignal,
    create_evaluate_strategy_signal_command,
)
from el_psy_quant.strategy_order.intent_commands import (
    DERIVE_ORDER_INTENT_COMMAND_SCHEMA_VERSION,
    _derive_order_intent_command_digest,
)
from el_psy_quant.strategy_order.risk_commands import (
    EVALUATE_PRE_TRADE_RISK_COMMAND_SCHEMA_VERSION,
    _evaluate_pre_trade_risk_command_digest,
)


def _text(value: object, field: str, maximum: int = 512) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or len(value) > maximum
    ):
        raise ValueError(f"{field} is invalid")
    return value


def _limit(value: object) -> int:
    if (
        type(value) is not int
        or not 1 <= value <= STRATEGY_ORDER_LIST_LIMIT_MAXIMUM
    ):
        raise ValueError("limit must be an integer from 1 to 200")
    return value


def _cursor(
    created_at: datetime | None,
    identity: str | None,
) -> tuple[datetime, str] | None:
    if (created_at is None) is not (identity is None):
        raise ValueError("cursor anchors must be paired")
    if created_at is None:
        return None
    if type(created_at) is not datetime or created_at.tzinfo is None:
        raise ValueError("cursor timestamp is invalid")
    return created_at.astimezone(timezone.utc), _text(identity, "cursor ID")


def _intent_matches_signal(
    intent: OrderIntent | OrderIntentNoAction,
    signal: StrategySignal,
) -> bool:
    return (
        intent.signal_reference.signal_id == signal.signal_id
        and intent.signal_reference.signal_digest == signal.signal_digest
        and intent.market_reference == signal.market_reference
        and intent.target_semantics == signal.target_semantics
        and intent.target_position_quantity
        == signal.target_position_quantity
    )


def _decision_matches_intent(
    decision: PreTradeRiskDecision,
    intent: OrderIntent,
) -> bool:
    snapshot = decision.input_snapshot
    return (
        snapshot.intent_reference.intent_id == intent.intent_id
        and snapshot.intent_reference.intent_digest == intent.intent_digest
        and snapshot.market_reference == intent.market_reference
        and snapshot.account_reference == intent.account_reference
        and snapshot.side == intent.side
        and snapshot.requested_quantity == intent.requested_quantity
    )


class StrategySignalRepository(Protocol):
    def get(self, *, signal_id: str) -> StrategySignal | None: ...
    def get_by_digest(self, *, signal_digest: str) -> StrategySignal | None: ...
    def add(self, *, signal: StrategySignal) -> StrategySignal: ...
    def list_page(
        self,
        *,
        limit: int,
        cursor_created_at: datetime | None = None,
        cursor_signal_id: str | None = None,
        strategy_name: str | None = None,
        instrument_id: str | None = None,
    ) -> StrategyOrderPage[StrategySignal]: ...


class OrderIntentRepository(Protocol):
    def get(self, *, intent_id: str) -> OrderIntent | None: ...
    def get_by_digest(self, *, intent_digest: str) -> OrderIntent | None: ...
    def add(self, *, intent: OrderIntent) -> OrderIntent: ...
    def list_page(
        self,
        *,
        limit: int,
        cursor_created_at: datetime | None = None,
        cursor_intent_id: str | None = None,
        signal_id: str | None = None,
        account_id: str | None = None,
        instrument_id: str | None = None,
        side: str | None = None,
    ) -> StrategyOrderPage[OrderIntent]: ...


class PreTradeRiskDecisionRepository(Protocol):
    def get(self, *, decision_id: str) -> PreTradeRiskDecision | None: ...
    def get_by_digest(
        self, *, decision_digest: str
    ) -> PreTradeRiskDecision | None: ...
    def add(
        self, *, decision: PreTradeRiskDecision
    ) -> PreTradeRiskDecision: ...
    def list_page(
        self,
        *,
        limit: int,
        cursor_created_at: datetime | None = None,
        cursor_decision_id: str | None = None,
        intent_id: str | None = None,
        account_id: str | None = None,
        outcome: str | None = None,
    ) -> StrategyOrderPage[PreTradeRiskDecision]: ...


class StrategyOrderCommandReceiptRepository(Protocol):
    def get(
        self,
        *,
        namespace: StrategyOrderCommandNamespace,
        command_idempotency_key: str,
    ) -> StrategyOrderCommandReceipt | None: ...
    def get_by_digest(
        self,
        *,
        namespace: StrategyOrderCommandNamespace,
        command_digest: str,
    ) -> StrategyOrderCommandReceipt | None: ...
    def add(
        self, *, receipt: StrategyOrderCommandReceipt
    ) -> StrategyOrderCommandReceipt: ...
    def resolve(
        self, *, receipt: StrategyOrderCommandReceipt
    ) -> StrategyOrderResult: ...


class _Repository:
    def __init__(self, *, session: Session) -> None:
        if not isinstance(session, Session):
            raise TypeError("session must be a SQLAlchemy Session")
        self._session = session


class SqlAlchemyStrategySignalRepository(_Repository):
    """Strict signal repository with deterministic bounded reads."""

    def get(self, *, signal_id: str) -> StrategySignal | None:
        row = self._session.get(
            StrategySignalRow, _text(signal_id, "signal_id", 80)
        )
        return None if row is None else signal_from_row(row)

    def get_by_digest(self, *, signal_digest: str) -> StrategySignal | None:
        row = self._session.scalar(
            select(StrategySignalRow).where(
                StrategySignalRow.signal_digest
                == _text(signal_digest, "signal_digest", 64)
            )
        )
        return None if row is None else signal_from_row(row)

    def add(self, *, signal: StrategySignal) -> StrategySignal:
        candidate = signal_row(signal)
        by_id = self.get(signal_id=signal.signal_id)
        by_digest = self.get_by_digest(signal_digest=signal.signal_digest)
        existing = by_id or by_digest
        if existing is not None:
            if (
                existing.signal_id != signal.signal_id
                or existing.signal_digest != signal.signal_digest
            ):
                raise StrategyOrderCorruptAuthorityError()
            return existing
        self._session.add(candidate)
        self._session.flush()
        return signal

    def list_page(
        self,
        *,
        limit: int,
        cursor_created_at: datetime | None = None,
        cursor_signal_id: str | None = None,
        strategy_name: str | None = None,
        instrument_id: str | None = None,
    ) -> StrategyOrderPage[StrategySignal]:
        size = _limit(limit)
        cursor = _cursor(cursor_created_at, cursor_signal_id)
        statement = select(StrategySignalRow)
        if strategy_name is not None:
            statement = statement.where(
                StrategySignalRow.strategy_name
                == _text(strategy_name, "strategy_name", 128)
            )
        if instrument_id is not None:
            statement = statement.where(
                StrategySignalRow.instrument_id
                == _text(instrument_id, "instrument_id")
            )
        if cursor is not None:
            timestamp, identity = cursor
            statement = statement.where(
                or_(
                    StrategySignalRow.created_at < timestamp,
                    and_(
                        StrategySignalRow.created_at == timestamp,
                        StrategySignalRow.signal_id > identity,
                    ),
                )
            )
        rows = tuple(
            self._session.scalars(
                statement.order_by(
                    StrategySignalRow.created_at.desc(),
                    StrategySignalRow.signal_id.asc(),
                ).limit(size + 1)
            ).all()
        )
        return StrategyOrderPage(
            items=tuple(signal_from_row(row) for row in rows[:size]),
            has_more=len(rows) > size,
        )


class SqlAlchemyOrderIntentRepository(_Repository):
    """Strict intent repository validating its persisted Signal relationship."""

    def _restore(self, row: OrderIntentRow) -> OrderIntent:
        intent = intent_from_row(row)
        signal = SqlAlchemyStrategySignalRepository(
            session=self._session
        ).get(signal_id=intent.signal_reference.signal_id)
        if signal is None or not _intent_matches_signal(intent, signal):
            raise StrategyOrderCorruptAuthorityError()
        return intent

    def get(self, *, intent_id: str) -> OrderIntent | None:
        row = self._session.get(
            OrderIntentRow, _text(intent_id, "intent_id", 80)
        )
        return None if row is None else self._restore(row)

    def get_by_digest(self, *, intent_digest: str) -> OrderIntent | None:
        row = self._session.scalar(
            select(OrderIntentRow).where(
                OrderIntentRow.intent_digest
                == _text(intent_digest, "intent_digest", 64)
            )
        )
        return None if row is None else self._restore(row)

    def add(self, *, intent: OrderIntent) -> OrderIntent:
        signal = SqlAlchemyStrategySignalRepository(
            session=self._session
        ).get(signal_id=intent.signal_reference.signal_id)
        if signal is None or not _intent_matches_signal(intent, signal):
            raise StrategyOrderCorruptAuthorityError()
        by_id = self.get(intent_id=intent.intent_id)
        by_digest = self.get_by_digest(intent_digest=intent.intent_digest)
        existing = by_id or by_digest
        if existing is not None:
            if (
                existing.intent_id != intent.intent_id
                or existing.intent_digest != intent.intent_digest
            ):
                raise StrategyOrderCorruptAuthorityError()
            return existing
        self._session.add(intent_row(intent))
        self._session.flush()
        return intent

    def list_page(
        self,
        *,
        limit: int,
        cursor_created_at: datetime | None = None,
        cursor_intent_id: str | None = None,
        signal_id: str | None = None,
        account_id: str | None = None,
        instrument_id: str | None = None,
        side: str | None = None,
    ) -> StrategyOrderPage[OrderIntent]:
        size = _limit(limit)
        cursor = _cursor(cursor_created_at, cursor_intent_id)
        statement = select(OrderIntentRow)
        for column, value, field, maximum in (
            (OrderIntentRow.signal_id, signal_id, "signal_id", 80),
            (OrderIntentRow.account_id, account_id, "account_id", 512),
            (
                OrderIntentRow.instrument_id,
                instrument_id,
                "instrument_id",
                512,
            ),
        ):
            if value is not None:
                statement = statement.where(
                    column == _text(value, field, maximum)
                )
        if side is not None:
            if side not in ("buy", "sell"):
                raise ValueError("unsupported side")
            statement = statement.where(OrderIntentRow.side == side)
        if cursor is not None:
            timestamp, identity = cursor
            statement = statement.where(
                or_(
                    OrderIntentRow.created_at < timestamp,
                    and_(
                        OrderIntentRow.created_at == timestamp,
                        OrderIntentRow.intent_id > identity,
                    ),
                )
            )
        rows = tuple(
            self._session.scalars(
                statement.order_by(
                    OrderIntentRow.created_at.desc(),
                    OrderIntentRow.intent_id.asc(),
                ).limit(size + 1)
            ).all()
        )
        return StrategyOrderPage(
            items=tuple(self._restore(row) for row in rows[:size]),
            has_more=len(rows) > size,
        )


class SqlAlchemyPreTradeRiskDecisionRepository(_Repository):
    """Strict decision repository validating its persisted Intent relationship."""

    def _restore(self, row: PreTradeRiskDecisionRow) -> PreTradeRiskDecision:
        decision = decision_from_row(row)
        intent_ref = decision.input_snapshot.intent_reference
        intent = SqlAlchemyOrderIntentRepository(
            session=self._session
        ).get(intent_id=intent_ref.intent_id)
        if intent is None or not _decision_matches_intent(decision, intent):
            raise StrategyOrderCorruptAuthorityError()
        return decision

    def get(self, *, decision_id: str) -> PreTradeRiskDecision | None:
        row = self._session.get(
            PreTradeRiskDecisionRow,
            _text(decision_id, "decision_id", 96),
        )
        return None if row is None else self._restore(row)

    def get_by_digest(
        self, *, decision_digest: str
    ) -> PreTradeRiskDecision | None:
        row = self._session.scalar(
            select(PreTradeRiskDecisionRow).where(
                PreTradeRiskDecisionRow.decision_digest
                == _text(decision_digest, "decision_digest", 64)
            )
        )
        return None if row is None else self._restore(row)

    def add(
        self, *, decision: PreTradeRiskDecision
    ) -> PreTradeRiskDecision:
        intent_ref = decision.input_snapshot.intent_reference
        intent = SqlAlchemyOrderIntentRepository(
            session=self._session
        ).get(intent_id=intent_ref.intent_id)
        if intent is None or not _decision_matches_intent(decision, intent):
            raise StrategyOrderCorruptAuthorityError()
        by_id = self.get(decision_id=decision.decision_id)
        by_digest = self.get_by_digest(
            decision_digest=decision.decision_digest
        )
        existing = by_id or by_digest
        if existing is not None:
            if (
                existing.decision_id != decision.decision_id
                or existing.decision_digest != decision.decision_digest
            ):
                raise StrategyOrderCorruptAuthorityError()
            return existing
        self._session.add(decision_row(decision))
        self._session.flush()
        return decision

    def list_page(
        self,
        *,
        limit: int,
        cursor_created_at: datetime | None = None,
        cursor_decision_id: str | None = None,
        intent_id: str | None = None,
        account_id: str | None = None,
        outcome: str | None = None,
    ) -> StrategyOrderPage[PreTradeRiskDecision]:
        size = _limit(limit)
        cursor = _cursor(cursor_created_at, cursor_decision_id)
        statement = select(PreTradeRiskDecisionRow)
        if intent_id is not None:
            statement = statement.where(
                PreTradeRiskDecisionRow.intent_id
                == _text(intent_id, "intent_id", 80)
            )
        if account_id is not None:
            statement = statement.where(
                PreTradeRiskDecisionRow.account_id
                == _text(account_id, "account_id")
            )
        if outcome is not None:
            if outcome not in ("allow", "reject"):
                raise ValueError("unsupported outcome")
            statement = statement.where(
                PreTradeRiskDecisionRow.outcome == outcome
            )
        if cursor is not None:
            timestamp, identity = cursor
            statement = statement.where(
                or_(
                    PreTradeRiskDecisionRow.created_at < timestamp,
                    and_(
                        PreTradeRiskDecisionRow.created_at == timestamp,
                        PreTradeRiskDecisionRow.decision_id > identity,
                    ),
                )
            )
        rows = tuple(
            self._session.scalars(
                statement.order_by(
                    PreTradeRiskDecisionRow.created_at.desc(),
                    PreTradeRiskDecisionRow.decision_id.asc(),
                ).limit(size + 1)
            ).all()
        )
        return StrategyOrderPage(
            items=tuple(self._restore(row) for row in rows[:size]),
            has_more=len(rows) > size,
        )


class SqlAlchemyStrategyOrderCommandReceiptRepository(_Repository):
    """Strict scoped durable command-idempotency repository."""

    def get(
        self,
        *,
        namespace: StrategyOrderCommandNamespace,
        command_idempotency_key: str,
    ) -> StrategyOrderCommandReceipt | None:
        row = self._session.get(
            StrategyOrderCommandReceiptRow,
            (
                _text(namespace, "namespace", 64),
                _text(command_idempotency_key, "command key", 128),
            ),
        )
        return None if row is None else receipt_from_row(row)

    def get_by_digest(
        self,
        *,
        namespace: StrategyOrderCommandNamespace,
        command_digest: str,
    ) -> StrategyOrderCommandReceipt | None:
        row = self._session.scalar(
            select(StrategyOrderCommandReceiptRow).where(
                StrategyOrderCommandReceiptRow.namespace
                == _text(namespace, "namespace", 64),
                StrategyOrderCommandReceiptRow.command_digest
                == _text(command_digest, "command digest", 64),
            )
        )
        return None if row is None else receipt_from_row(row)

    def resolve(
        self, *, receipt: StrategyOrderCommandReceipt
    ) -> StrategyOrderResult:
        if type(receipt) is not StrategyOrderCommandReceipt:
            raise ValueError("receipt must be StrategyOrderCommandReceipt")
        result: StrategyOrderResult | None
        if receipt.result_kind == RESULT_KIND_SIGNAL:
            if receipt.namespace != COMMAND_NAMESPACE_EVALUATE_SIGNAL:
                raise StrategyOrderCorruptAuthorityError()
            result = SqlAlchemyStrategySignalRepository(
                session=self._session
            ).get(signal_id=receipt.result_id)
            if result is not None:
                expected = create_evaluate_strategy_signal_command(
                    strategy_runtime_reference=result.strategy_runtime_reference,
                    market_reference=result.market_reference,
                    command_idempotency_key=receipt.command_idempotency_key,
                    actor=receipt.command_actor,
                ).command_digest
            else:
                expected = ""
        elif receipt.result_kind == RESULT_KIND_INTENT:
            if receipt.namespace != COMMAND_NAMESPACE_DERIVE_INTENT:
                raise StrategyOrderCorruptAuthorityError()
            result = SqlAlchemyOrderIntentRepository(
                session=self._session
            ).get(intent_id=receipt.result_id)
            if result is not None:
                expected = _derive_order_intent_command_digest(
                    schema_version=DERIVE_ORDER_INTENT_COMMAND_SCHEMA_VERSION,
                    signal_reference=result.signal_reference,
                    account_reference=result.account_reference,
                    intent_policy_version=result.intent_policy_version,
                    command_idempotency_key=receipt.command_idempotency_key,
                    actor=receipt.command_actor,
                )
            else:
                expected = ""
        elif receipt.result_kind == RESULT_KIND_NO_ACTION:
            if (
                receipt.namespace != COMMAND_NAMESPACE_DERIVE_INTENT
                or receipt.result_payload_json is None
            ):
                raise StrategyOrderCorruptAuthorityError()
            result = order_intent_no_action_from_payload(
                load_canonical_json(receipt.result_payload_json)
            )
            signal = SqlAlchemyStrategySignalRepository(
                session=self._session
            ).get(signal_id=result.signal_reference.signal_id)
            if signal is None or not _intent_matches_signal(result, signal):
                raise StrategyOrderCorruptAuthorityError()
            expected = _derive_order_intent_command_digest(
                schema_version=DERIVE_ORDER_INTENT_COMMAND_SCHEMA_VERSION,
                signal_reference=result.signal_reference,
                account_reference=result.account_reference,
                intent_policy_version=result.intent_policy_version,
                command_idempotency_key=receipt.command_idempotency_key,
                actor=receipt.command_actor,
            )
        elif receipt.result_kind == RESULT_KIND_DECISION:
            if receipt.namespace != COMMAND_NAMESPACE_EVALUATE_RISK:
                raise StrategyOrderCorruptAuthorityError()
            result = SqlAlchemyPreTradeRiskDecisionRepository(
                session=self._session
            ).get(decision_id=receipt.result_id)
            if result is not None:
                snapshot = result.input_snapshot
                expected = _evaluate_pre_trade_risk_command_digest(
                    schema_version=EVALUATE_PRE_TRADE_RISK_COMMAND_SCHEMA_VERSION,
                    intent_reference=snapshot.intent_reference,
                    risk_policy_reference=snapshot.risk_policy_reference,
                    command_idempotency_key=receipt.command_idempotency_key,
                    actor=receipt.command_actor,
                )
            else:
                expected = ""
        else:
            raise StrategyOrderCorruptAuthorityError()
        if result is None:
            raise StrategyOrderCorruptAuthorityError()
        kind, identity, digest = result_identity(result)
        if (
            kind != receipt.result_kind
            or identity != receipt.result_id
            or digest != receipt.result_digest
            or expected != receipt.command_digest
        ):
            raise StrategyOrderCorruptAuthorityError()
        return result

    def add(
        self, *, receipt: StrategyOrderCommandReceipt
    ) -> StrategyOrderCommandReceipt:
        self.resolve(receipt=receipt)
        by_key = self.get(
            namespace=receipt.namespace,
            command_idempotency_key=receipt.command_idempotency_key,
        )
        by_digest = self.get_by_digest(
            namespace=receipt.namespace,
            command_digest=receipt.command_digest,
        )
        existing = by_key or by_digest
        if existing is not None:
            if existing != receipt:
                raise StrategyOrderCorruptAuthorityError()
            return existing
        self._session.add(receipt_row(receipt))
        self._session.flush()
        return receipt


__all__ = [
    "OrderIntentRepository",
    "PreTradeRiskDecisionRepository",
    "SqlAlchemyOrderIntentRepository",
    "SqlAlchemyPreTradeRiskDecisionRepository",
    "SqlAlchemyStrategyOrderCommandReceiptRepository",
    "SqlAlchemyStrategySignalRepository",
    "StrategyOrderCommandReceiptRepository",
    "StrategySignalRepository",
]
