"""Transactional application orchestration for durable M33 authority."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, cast

from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from el_psy_quant.market_time import MarketDataReplayEngine
from el_psy_quant.paper_account import (
    MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
    PaperAccountLedgerState,
    replay_paper_account_ledger,
    verify_paper_account_projection,
)
from el_psy_quant.persistence import (
    PaperAccountPersistenceCorruptionError,
    SqlAlchemyMarketTimeRepository,
    SqlAlchemyPaperAccountRepository,
)
from el_psy_quant.persistence.strategy_order_mapping import result_identity
from el_psy_quant.persistence.strategy_order_records import (
    COMMAND_NAMESPACE_DERIVE_INTENT,
    COMMAND_NAMESPACE_EVALUATE_RISK,
    COMMAND_NAMESPACE_EVALUATE_SIGNAL,
    RESULT_KIND_NO_ACTION,
    StrategyOrderCommandReceipt,
    StrategyOrderCorruptAuthorityError,
    StrategyOrderIdempotencyConflictError,
    StrategyOrderNotFoundError,
    StrategyOrderReconciliationRequiredError,
    StrategyOrderStaleAuthorityError,
    StrategyOrderStorageBusyError,
    StrategyOrderStorageFailureError,
    StrategyOrderStoredResult,
    canonical_json,
)
from el_psy_quant.persistence.strategy_order_repository import (
    SqlAlchemyOrderIntentRepository,
    SqlAlchemyPreTradeRiskDecisionRepository,
    SqlAlchemyStrategyOrderCommandReceiptRepository,
    SqlAlchemyStrategySignalRepository,
)
from el_psy_quant.strategy_order import (
    ORDER_INTENT_POLICY_VERSION,
    OrderIntent,
    OrderIntentNoAction,
    PreTradeRiskDecision,
    PreTradeRiskPolicyReference,
    StrategyRuntimeReference,
    StrategySignal,
    create_derive_order_intent_command,
    create_evaluate_pre_trade_risk_command,
    create_evaluate_strategy_signal_command,
    create_order_intent_account_reference,
    create_strategy_signal_market_reference,
    derive_order_intent,
    evaluate_pre_trade_risk,
    evaluate_strategy_signal,
    validate_pre_trade_risk_policy_reference,
    validate_strategy_runtime_reference,
)
from el_psy_quant.strategy_order._canonical import normalize_bounded_string


def _busy(exc: OperationalError) -> bool:
    original = exc.orig
    return isinstance(original, sqlite3.OperationalError) and any(
        marker in str(original).lower() for marker in ("locked", "busy")
    )


def _utc(value: object, field: str) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise StrategyOrderCorruptAuthorityError()
    normalized = value.astimezone(timezone.utc)
    if normalized != value:
        raise StrategyOrderCorruptAuthorityError()
    return normalized


def _positive_int(value: object, field: str) -> int:
    if type(value) is not int or value < 1:
        raise StrategyOrderCorruptAuthorityError()
    return value


def _normalize_command_strings(
    command_idempotency_key: object,
    actor: object,
) -> tuple[str, str]:
    try:
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
    except (TypeError, ValueError) as exc:
        raise StrategyOrderCorruptAuthorityError() from exc
    return key, normalized_actor


class StrategyOrderApplicationService:
    """Own one-winner transactions while pure M31–M33 domains own truth."""

    def __init__(self, *, session_factory: sessionmaker[Session]) -> None:
        if not isinstance(session_factory, sessionmaker):
            raise TypeError("session_factory must be a SQLAlchemy sessionmaker")
        self._session_factory = session_factory

    @contextmanager
    def _write(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            session.connection().exec_driver_sql("BEGIN IMMEDIATE")
            session.connection().exec_driver_sql("PRAGMA defer_foreign_keys=ON")
            yield session
            session.commit()
        except OperationalError as exc:
            session.rollback()
            if _busy(exc):
                raise StrategyOrderStorageBusyError() from exc
            raise StrategyOrderStorageFailureError() from exc
        except IntegrityError as exc:
            session.rollback()
            raise StrategyOrderStorageFailureError() from exc
        except SQLAlchemyError as exc:
            session.rollback()
            raise StrategyOrderStorageFailureError() from exc
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def _read(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
        except OperationalError as exc:
            if _busy(exc):
                raise StrategyOrderStorageBusyError() from exc
            raise StrategyOrderStorageFailureError() from exc
        except SQLAlchemyError as exc:
            raise StrategyOrderStorageFailureError() from exc
        finally:
            session.close()

    @staticmethod
    def _account_state(
        session: Session,
        *,
        account_id: str,
    ) -> PaperAccountLedgerState:
        repository = SqlAlchemyPaperAccountRepository(session=session)
        try:
            account = repository.get_account(account_id=account_id)
            if account is None:
                raise StrategyOrderNotFoundError()
            history = repository.get_history(account=account)
            state = replay_paper_account_ledger(history)
            if account.projection_status != "current":
                raise StrategyOrderReconciliationRequiredError()
            projection = repository.get_projection(account=account)
            if (
                projection is None
                or projection.source_account_version != account.head_version
                or projection.source_event_id != account.head_event_id
                or projection.source_chain_digest != account.head_chain_digest
                or verify_paper_account_projection(history, projection).status
                != "current"
            ):
                raise StrategyOrderReconciliationRequiredError()
            return state
        except (
            StrategyOrderNotFoundError,
            StrategyOrderReconciliationRequiredError,
        ):
            raise
        except PaperAccountPersistenceCorruptionError as exc:
            raise StrategyOrderCorruptAuthorityError() from exc
        except ValueError as exc:
            raise StrategyOrderCorruptAuthorityError() from exc

    @staticmethod
    def _market(
        session: Session,
        *,
        calendar_id: str,
        calendar_version: int,
        trading_session_id: str,
        replay_id: str,
        event_stream_digest: str,
        cursor_position: int,
        current_event_id: str,
        instrument_id: str,
        current_event_time: datetime | None,
    ):
        repository = SqlAlchemyMarketTimeRepository(session=session)
        try:
            calendar = repository.get_calendar(calendar_id=calendar_id)
            trading_session = repository.get_session(
                session_id=trading_session_id
            )
            replay = repository.get_replay(replay_id=replay_id)
            if calendar is None or trading_session is None or replay is None:
                raise StrategyOrderNotFoundError()
            engine = MarketDataReplayEngine(
                replay_id=replay.session.replay_id,
                events=replay.events,
                cursor=replay.session.cursor,
            )
            cursor = engine.cursor
            if (
                calendar.calendar_version != calendar_version
                or trading_session.calendar_id != calendar.id
                or cursor.event_stream_digest != event_stream_digest
                or cursor.position != cursor_position
                or cursor.position < 1
                or cursor.last_event_id != current_event_id
            ):
                raise StrategyOrderStaleAuthorityError()
            event = engine.events[cursor.position - 1]
            if (
                event.event_id != current_event_id
                or event.instrument_id != instrument_id
                or (
                    current_event_time is not None
                    and event.event_time != _utc(
                        current_event_time, "current_event_time"
                    )
                )
            ):
                raise StrategyOrderStaleAuthorityError()
            return calendar, trading_session, engine, event
        except (
            StrategyOrderNotFoundError,
            StrategyOrderStaleAuthorityError,
        ):
            raise
        except ValueError as exc:
            raise StrategyOrderCorruptAuthorityError() from exc

    @staticmethod
    def _account_matches(
        state: PaperAccountLedgerState,
        *,
        expected_version: int,
        expected_event_id: str,
        expected_chain_digest: str,
    ) -> None:
        if (
            state.head_version != _positive_int(
                expected_version, "expected_account_head_version"
            )
            or state.head_event_id != expected_event_id
            or state.head_chain_digest != expected_chain_digest
        ):
            raise StrategyOrderStaleAuthorityError()

    @staticmethod
    def _receipt(
        *,
        namespace,
        command_key: str,
        command_digest: str,
        actor: str,
        result,
    ) -> StrategyOrderCommandReceipt:
        kind, identity, digest = result_identity(result)
        return StrategyOrderCommandReceipt(
            namespace=namespace,
            command_idempotency_key=command_key,
            command_digest=command_digest,
            command_actor=actor,
            result_kind=kind,
            result_id=identity,
            result_digest=digest,
            result_payload_json=(
                canonical_json(result.to_dict())
                if kind == RESULT_KIND_NO_ACTION
                else None
            ),
            created_at=result.created_at,
        )

    @staticmethod
    def _existing(
        session: Session,
        *,
        namespace,
        command_key: str,
    ):
        receipts = SqlAlchemyStrategyOrderCommandReceiptRepository(
            session=session
        )
        receipt = receipts.get(
            namespace=namespace,
            command_idempotency_key=command_key,
        )
        if receipt is None:
            return None
        return receipt, receipts.resolve(receipt=receipt)

    def evaluate_and_store_strategy_signal(
        self,
        *,
        strategy_runtime_reference: StrategyRuntimeReference,
        calendar_id: str,
        expected_calendar_version: int,
        trading_session_id: str,
        replay_id: str,
        expected_event_stream_digest: str,
        expected_cursor_position: int,
        expected_signal_event_id: str,
        instrument_id: str,
        command_idempotency_key: str,
        actor: str,
        created_at: datetime,
        expected_signal_time: datetime | None = None,
    ) -> StrategyOrderStoredResult[StrategySignal]:
        """Evaluate only current M32 authority and store one immutable Signal."""
        key, normalized_actor = _normalize_command_strings(
            command_idempotency_key, actor
        )
        try:
            runtime = validate_strategy_runtime_reference(
                strategy_runtime_reference
            )
        except (TypeError, ValueError) as exc:
            raise StrategyOrderCorruptAuthorityError() from exc
        audit_time = _utc(created_at, "created_at")
        with self._write() as session:
            existing = self._existing(
                session,
                namespace=COMMAND_NAMESPACE_EVALUATE_SIGNAL,
                command_key=key,
            )
            if existing is not None:
                receipt, result = existing
                if (
                    type(result) is not StrategySignal
                    or receipt.command_actor != normalized_actor
                    or result.strategy_runtime_reference != runtime
                    or result.market_reference.calendar_id != calendar_id
                    or result.market_reference.calendar_version
                    != expected_calendar_version
                    or result.market_reference.trading_session_id
                    != trading_session_id
                    or result.market_reference.replay_id != replay_id
                    or result.market_reference.event_stream_digest
                    != expected_event_stream_digest
                    or result.market_reference.cursor_position
                    != expected_cursor_position
                    or result.market_reference.signal_event_id
                    != expected_signal_event_id
                    or result.market_reference.instrument_id != instrument_id
                    or (
                        expected_signal_time is not None
                        and result.market_reference.signal_time
                        != _utc(expected_signal_time, "expected_signal_time")
                    )
                ):
                    raise StrategyOrderIdempotencyConflictError()
                return StrategyOrderStoredResult(result=result, replayed=True)

            calendar, trading_session, engine, event = self._market(
                session,
                calendar_id=calendar_id,
                calendar_version=expected_calendar_version,
                trading_session_id=trading_session_id,
                replay_id=replay_id,
                event_stream_digest=expected_event_stream_digest,
                cursor_position=expected_cursor_position,
                current_event_id=expected_signal_event_id,
                instrument_id=instrument_id,
                current_event_time=expected_signal_time,
            )
            try:
                market = create_strategy_signal_market_reference(
                    calendar=calendar,
                    session=trading_session,
                    replay_session=engine.session,
                    current_event=event,
                )
                command = create_evaluate_strategy_signal_command(
                    strategy_runtime_reference=runtime,
                    market_reference=market,
                    command_idempotency_key=key,
                    actor=normalized_actor,
                )
                result = evaluate_strategy_signal(
                    command,
                    calendar=calendar,
                    session=trading_session,
                    replay_engine=engine,
                    created_at=audit_time,
                )
            except (TypeError, ValueError) as exc:
                raise StrategyOrderCorruptAuthorityError() from exc
            stored = SqlAlchemyStrategySignalRepository(
                session=session
            ).add(signal=result)
            receipt = self._receipt(
                namespace=COMMAND_NAMESPACE_EVALUATE_SIGNAL,
                command_key=command.command_idempotency_key,
                command_digest=command.command_digest,
                actor=command.actor,
                result=stored,
            )
            SqlAlchemyStrategyOrderCommandReceiptRepository(
                session=session
            ).add(receipt=receipt)
            return StrategyOrderStoredResult(result=stored, replayed=False)

    def derive_and_store_order_intent(
        self,
        *,
        signal_id: str,
        account_id: str,
        expected_account_head_version: int,
        expected_account_head_event_id: str,
        expected_account_head_chain_digest: str,
        command_idempotency_key: str,
        actor: str,
        created_at: datetime,
        intent_policy_version: str = ORDER_INTENT_POLICY_VERSION,
    ) -> StrategyOrderStoredResult[OrderIntent | OrderIntentNoAction]:
        """Derive from one persisted Signal and one verified M31 state."""
        key, normalized_actor = _normalize_command_strings(
            command_idempotency_key, actor
        )
        audit_time = _utc(created_at, "created_at")
        with self._write() as session:
            existing = self._existing(
                session,
                namespace=COMMAND_NAMESPACE_DERIVE_INTENT,
                command_key=key,
            )
            if existing is not None:
                receipt, result = existing
                if (
                    type(result) not in (OrderIntent, OrderIntentNoAction)
                    or receipt.command_actor != normalized_actor
                    or result.signal_reference.signal_id != signal_id
                    or result.account_reference.account_id != account_id
                    or result.account_reference.account_head_version
                    != expected_account_head_version
                    or result.account_reference.account_head_event_id
                    != expected_account_head_event_id
                    or result.account_reference.account_head_chain_digest
                    != expected_account_head_chain_digest
                    or result.intent_policy_version != intent_policy_version
                ):
                    raise StrategyOrderIdempotencyConflictError()
                return StrategyOrderStoredResult(result=result, replayed=True)

            signal = SqlAlchemyStrategySignalRepository(
                session=session
            ).get(signal_id=signal_id)
            if signal is None:
                raise StrategyOrderNotFoundError()
            state = self._account_state(session, account_id=account_id)
            self._account_matches(
                state,
                expected_version=expected_account_head_version,
                expected_event_id=expected_account_head_event_id,
                expected_chain_digest=expected_account_head_chain_digest,
            )
            try:
                command = create_derive_order_intent_command(
                    signal=signal,
                    account_state=state,
                    command_idempotency_key=key,
                    actor=normalized_actor,
                    intent_policy_version=intent_policy_version,
                )
                result = derive_order_intent(
                    command,
                    signal=signal,
                    account_state=state,
                    created_at=audit_time,
                )
            except (TypeError, ValueError) as exc:
                raise StrategyOrderCorruptAuthorityError() from exc
            stored = (
                result
                if type(result) is OrderIntentNoAction
                else SqlAlchemyOrderIntentRepository(session=session).add(
                    intent=cast(OrderIntent, result)
                )
            )
            receipt = self._receipt(
                namespace=COMMAND_NAMESPACE_DERIVE_INTENT,
                command_key=command.command_idempotency_key,
                command_digest=command.command_digest,
                actor=command.actor,
                result=stored,
            )
            SqlAlchemyStrategyOrderCommandReceiptRepository(
                session=session
            ).add(receipt=receipt)
            return StrategyOrderStoredResult(result=stored, replayed=False)

    def evaluate_and_store_pre_trade_risk(
        self,
        *,
        intent_id: str,
        risk_policy_reference: PreTradeRiskPolicyReference,
        expected_account_head_version: int,
        expected_account_head_event_id: str,
        expected_account_head_chain_digest: str,
        expected_calendar_id: str,
        expected_calendar_version: int,
        expected_trading_session_id: str,
        expected_replay_id: str,
        expected_event_stream_digest: str,
        expected_cursor_position: int,
        expected_current_event_id: str,
        expected_instrument_id: str,
        command_idempotency_key: str,
        actor: str,
        created_at: datetime,
        expected_current_event_time: datetime | None = None,
    ) -> StrategyOrderStoredResult[PreTradeRiskDecision]:
        """Evaluate risk from persisted Intent and freshly verified M31/M32."""
        key, normalized_actor = _normalize_command_strings(
            command_idempotency_key, actor
        )
        try:
            policy = validate_pre_trade_risk_policy_reference(
                risk_policy_reference
            )
        except (TypeError, ValueError) as exc:
            raise StrategyOrderCorruptAuthorityError() from exc
        audit_time = _utc(created_at, "created_at")
        with self._write() as session:
            existing = self._existing(
                session,
                namespace=COMMAND_NAMESPACE_EVALUATE_RISK,
                command_key=key,
            )
            if existing is not None:
                receipt, result = existing
                if type(result) is not PreTradeRiskDecision:
                    raise StrategyOrderCorruptAuthorityError()
                snapshot = result.input_snapshot
                if (
                    receipt.command_actor != normalized_actor
                    or snapshot.intent_reference.intent_id != intent_id
                    or snapshot.risk_policy_reference != policy
                    or snapshot.account_reference.account_head_version
                    != expected_account_head_version
                    or snapshot.account_reference.account_head_event_id
                    != expected_account_head_event_id
                    or snapshot.account_reference.account_head_chain_digest
                    != expected_account_head_chain_digest
                    or snapshot.market_reference.calendar_id
                    != expected_calendar_id
                    or snapshot.market_reference.calendar_version
                    != expected_calendar_version
                    or snapshot.market_reference.trading_session_id
                    != expected_trading_session_id
                    or snapshot.market_reference.replay_id
                    != expected_replay_id
                    or snapshot.market_reference.event_stream_digest
                    != expected_event_stream_digest
                    or snapshot.market_reference.cursor_position
                    != expected_cursor_position
                    or snapshot.market_reference.signal_event_id
                    != expected_current_event_id
                    or snapshot.market_reference.instrument_id
                    != expected_instrument_id
                    or (
                        expected_current_event_time is not None
                        and snapshot.market_reference.signal_time
                        != _utc(
                            expected_current_event_time,
                            "expected_current_event_time",
                        )
                    )
                ):
                    raise StrategyOrderIdempotencyConflictError()
                return StrategyOrderStoredResult(result=result, replayed=True)

            intent = SqlAlchemyOrderIntentRepository(
                session=session
            ).get(intent_id=intent_id)
            if intent is None:
                raise StrategyOrderNotFoundError()
            signal = SqlAlchemyStrategySignalRepository(
                session=session
            ).get(signal_id=intent.signal_reference.signal_id)
            if signal is None:
                raise StrategyOrderCorruptAuthorityError()
            state = self._account_state(
                session,
                account_id=intent.account_reference.account_id,
            )
            self._account_matches(
                state,
                expected_version=expected_account_head_version,
                expected_event_id=expected_account_head_event_id,
                expected_chain_digest=expected_account_head_chain_digest,
            )
            try:
                current_account_reference = (
                    create_order_intent_account_reference(
                        signal=signal,
                        account_state=state,
                    )
                )
            except (TypeError, ValueError) as exc:
                raise StrategyOrderCorruptAuthorityError() from exc
            if current_account_reference != intent.account_reference:
                raise StrategyOrderStaleAuthorityError()
            calendar, trading_session, engine, event = self._market(
                session,
                calendar_id=expected_calendar_id,
                calendar_version=expected_calendar_version,
                trading_session_id=expected_trading_session_id,
                replay_id=expected_replay_id,
                event_stream_digest=expected_event_stream_digest,
                cursor_position=expected_cursor_position,
                current_event_id=expected_current_event_id,
                instrument_id=expected_instrument_id,
                current_event_time=expected_current_event_time,
            )
            try:
                current_market_reference = (
                    create_strategy_signal_market_reference(
                        calendar=calendar,
                        session=trading_session,
                        replay_session=engine.session,
                        current_event=event,
                    )
                )
            except (TypeError, ValueError) as exc:
                raise StrategyOrderCorruptAuthorityError() from exc
            if current_market_reference != intent.market_reference:
                raise StrategyOrderStaleAuthorityError()
            try:
                command = create_evaluate_pre_trade_risk_command(
                    intent=intent,
                    risk_policy_reference=policy,
                    command_idempotency_key=key,
                    actor=normalized_actor,
                )
                result = evaluate_pre_trade_risk(
                    command,
                    intent=intent,
                    account_state=state,
                    calendar=calendar,
                    session=trading_session,
                    replay_engine=engine,
                    created_at=audit_time,
                )
            except (TypeError, ValueError) as exc:
                raise StrategyOrderCorruptAuthorityError() from exc
            stored = SqlAlchemyPreTradeRiskDecisionRepository(
                session=session
            ).add(decision=result)
            receipt = self._receipt(
                namespace=COMMAND_NAMESPACE_EVALUATE_RISK,
                command_key=command.command_idempotency_key,
                command_digest=command.command_digest,
                actor=command.actor,
                result=stored,
            )
            SqlAlchemyStrategyOrderCommandReceiptRepository(
                session=session
            ).add(receipt=receipt)
            return StrategyOrderStoredResult(result=stored, replayed=False)

    def get_strategy_signal(self, *, signal_id: str) -> StrategySignal:
        with self._read() as session:
            try:
                result = SqlAlchemyStrategySignalRepository(
                    session=session
                ).get(signal_id=signal_id)
            except (TypeError, ValueError) as exc:
                raise StrategyOrderCorruptAuthorityError() from exc
            if result is None:
                raise StrategyOrderNotFoundError()
            return result

    def get_order_intent(self, *, intent_id: str) -> OrderIntent:
        with self._read() as session:
            try:
                result = SqlAlchemyOrderIntentRepository(
                    session=session
                ).get(intent_id=intent_id)
            except (TypeError, ValueError) as exc:
                raise StrategyOrderCorruptAuthorityError() from exc
            if result is None:
                raise StrategyOrderNotFoundError()
            return result

    def get_pre_trade_risk_decision(
        self, *, decision_id: str
    ) -> PreTradeRiskDecision:
        with self._read() as session:
            try:
                result = SqlAlchemyPreTradeRiskDecisionRepository(
                    session=session
                ).get(decision_id=decision_id)
            except (TypeError, ValueError) as exc:
                raise StrategyOrderCorruptAuthorityError() from exc
            if result is None:
                raise StrategyOrderNotFoundError()
            return result


__all__ = [
    "StrategyOrderApplicationService",
    "StrategyOrderCorruptAuthorityError",
    "StrategyOrderIdempotencyConflictError",
    "StrategyOrderNotFoundError",
    "StrategyOrderReconciliationRequiredError",
    "StrategyOrderStaleAuthorityError",
    "StrategyOrderStorageBusyError",
    "StrategyOrderStorageFailureError",
    "StrategyOrderStoredResult",
]
