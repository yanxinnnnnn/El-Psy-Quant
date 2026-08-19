"""Atomic synchronous application orchestration for durable M34 execution."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Callable, Iterator

from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from el_psy_quant.market_time import MarketDataReplayEngine, ReplayCursor
from el_psy_quant.paper_account import (
    PaperAccountLedgerState,
    rebuild_paper_account_projection,
    replay_paper_account_ledger,
    verify_paper_account_projection,
)
from el_psy_quant.paper_execution import (
    CreatePaperExecutionOrderCommand,
    PaperExecutionAttempt,
    PaperExecutionFill,
    PaperExecutionOrder,
    PaperExecutionPolicyReference,
    StepPaperExecutionOrderCommand,
    create_paper_execution_order,
    create_paper_execution_order_command,
    create_paper_execution_order_reference,
    create_paper_execution_risk_handoff_reference,
    create_step_paper_execution_order_command,
    settle_paper_execution_fill,
    step_paper_execution_order,
    validate_create_paper_execution_order_command,
    validate_step_paper_execution_order_command,
)
from el_psy_quant.persistence.market_time_repository import (
    SqlAlchemyMarketTimeRepository,
)
from el_psy_quant.persistence.paper_account_repository import (
    SqlAlchemyPaperAccountRepository,
)
from el_psy_quant.persistence.paper_accounts import (
    PaperAccountPersistenceCorruptionError,
    PaperAccountRecord,
)
from el_psy_quant.persistence.paper_execution_records import (
    COMMAND_NAMESPACE_CREATE_ORDER,
    COMMAND_NAMESPACE_STEP_ORDER,
    RESULT_KIND_ORDER,
    RESULT_KIND_STEP,
    PaperExecutionCommandReceipt,
    PaperExecutionConcurrencyConflictError,
    PaperExecutionCorruptAuthorityError,
    PaperExecutionHistory,
    PaperExecutionIdempotencyConflictError,
    PaperExecutionNotFoundError,
    PaperExecutionOperationConflictError,
    PaperExecutionPage,
    PaperExecutionReconciliationRequiredError,
    PaperExecutionStaleAuthorityError,
    PaperExecutionStepCommit,
    PaperExecutionStorageBusyError,
    PaperExecutionStorageFailureError,
    PaperExecutionStoredResult,
)
from el_psy_quant.persistence.paper_execution_repository import (
    SqlAlchemyPaperExecutionRepository,
)
from el_psy_quant.persistence.strategy_order_records import (
    StrategyOrderCorruptAuthorityError,
)
from el_psy_quant.persistence.strategy_order_repository import (
    SqlAlchemyOrderIntentRepository,
    SqlAlchemyPreTradeRiskDecisionRepository,
)
from el_psy_quant.strategy_order import create_order_intent_reference

PaperExecutionClock = Callable[[], datetime]


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


def _busy(exc: OperationalError) -> bool:
    return isinstance(exc.orig, sqlite3.OperationalError) and any(
        marker in str(exc.orig).lower() for marker in ("locked", "busy")
    )


def _utc(value: object) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise PaperExecutionCorruptAuthorityError()
    normalized = value.astimezone(timezone.utc)
    if normalized != value:
        raise PaperExecutionCorruptAuthorityError()
    return normalized


class PaperExecutionApplicationService:
    """Own one SQLite transaction while M31–M34 domains own all truth."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        clock: PaperExecutionClock = _default_clock,
    ) -> None:
        if not isinstance(session_factory, sessionmaker):
            raise TypeError("session_factory must be a SQLAlchemy sessionmaker")
        if not callable(clock):
            raise TypeError("clock must be callable")
        self._session_factory = session_factory
        self._clock = clock

    def _now(self) -> datetime:
        return _utc(self._clock())

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
                raise PaperExecutionStorageBusyError() from exc
            raise PaperExecutionStorageFailureError() from exc
        except IntegrityError as exc:
            session.rollback()
            raise PaperExecutionConcurrencyConflictError() from exc
        except SQLAlchemyError as exc:
            session.rollback()
            raise PaperExecutionStorageFailureError() from exc
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
                raise PaperExecutionStorageBusyError() from exc
            raise PaperExecutionStorageFailureError() from exc
        except SQLAlchemyError as exc:
            raise PaperExecutionStorageFailureError() from exc
        finally:
            session.close()

    @staticmethod
    def _account(
        session: Session, *, account_id: str
    ) -> tuple[
        PaperAccountRecord,
        tuple,
        PaperAccountLedgerState,
    ]:
        repository = SqlAlchemyPaperAccountRepository(session=session)
        try:
            account = repository.get_account(account_id=account_id)
            if account is None:
                raise PaperExecutionNotFoundError()
            history = repository.get_history(account=account)
            state = replay_paper_account_ledger(history)
            projection = repository.get_projection(account=account)
            if (
                account.projection_status != "current"
                or projection is None
                or projection.source_account_version != account.head_version
                or projection.source_event_id != account.head_event_id
                or projection.source_chain_digest != account.head_chain_digest
                or verify_paper_account_projection(history, projection).status
                != "current"
            ):
                raise PaperExecutionReconciliationRequiredError()
            return account, history, state
        except (
            PaperExecutionNotFoundError,
            PaperExecutionReconciliationRequiredError,
        ):
            raise
        except (PaperAccountPersistenceCorruptionError, ValueError) as exc:
            raise PaperExecutionCorruptAuthorityError() from exc

    @staticmethod
    def _market(session: Session, *, order_or_intent):
        reference = (
            order_or_intent.market_handoff_reference
            if isinstance(order_or_intent, PaperExecutionOrder)
            else order_or_intent.market_reference
        )
        repository = SqlAlchemyMarketTimeRepository(session=session)
        try:
            calendar = repository.get_calendar(calendar_id=reference.calendar_id)
            trading_session = repository.get_session(
                session_id=reference.trading_session_id
            )
            replay = repository.get_replay(replay_id=reference.replay_id)
            if calendar is None or trading_session is None or replay is None:
                raise PaperExecutionNotFoundError()
            engine = MarketDataReplayEngine(
                replay_id=replay.session.replay_id,
                events=replay.events,
                cursor=replay.session.cursor,
            )
            return calendar, trading_session, engine
        except PaperExecutionNotFoundError:
            raise
        except ValueError as exc:
            raise PaperExecutionCorruptAuthorityError() from exc

    @staticmethod
    def _upstream(session: Session, command: CreatePaperExecutionOrderCommand):
        try:
            intent = SqlAlchemyOrderIntentRepository(session=session).get(
                intent_id=command.order_intent_reference.intent_id
            )
            decision = SqlAlchemyPreTradeRiskDecisionRepository(session=session).get(
                decision_id=command.risk_handoff_reference.risk_decision_id
            )
        except StrategyOrderCorruptAuthorityError as exc:
            raise PaperExecutionCorruptAuthorityError() from exc
        if intent is None or decision is None:
            raise PaperExecutionNotFoundError()
        if (
            intent.intent_digest != command.order_intent_reference.intent_digest
            or decision.decision_digest
            != command.risk_handoff_reference.risk_decision_digest
            or decision.input_snapshot.snapshot_id
            != command.risk_handoff_reference.risk_snapshot_id
            or decision.input_snapshot.snapshot_digest
            != command.risk_handoff_reference.risk_snapshot_digest
            or decision.outcome != "allow"
        ):
            raise PaperExecutionStaleAuthorityError()
        return intent, decision

    def _receipt_for_order(
        self,
        command: CreatePaperExecutionOrderCommand,
        order: PaperExecutionOrder,
    ) -> PaperExecutionCommandReceipt:
        return PaperExecutionCommandReceipt(
            namespace=COMMAND_NAMESPACE_CREATE_ORDER,
            command_idempotency_key=command.command_idempotency_key,
            command_digest=command.command_digest,
            command_actor=command.actor,
            result_kind=RESULT_KIND_ORDER,
            execution_order_id=order.execution_order_id,
            execution_order_digest=order.execution_order_digest,
            attempt_id=None,
            attempt_digest=None,
            fill_id=None,
            fill_digest=None,
            settlement_link_id=None,
            settlement_link_evidence_digest=None,
            account_event_id=None,
            created_at=self._now(),
        )

    def _receipt_for_step(
        self,
        command: StepPaperExecutionOrderCommand,
        order: PaperExecutionOrder,
        commit: PaperExecutionStepCommit,
    ) -> PaperExecutionCommandReceipt:
        attempt = commit.step_result.attempt
        fill = commit.step_result.fill
        link = commit.settlement_link
        return PaperExecutionCommandReceipt(
            namespace=COMMAND_NAMESPACE_STEP_ORDER,
            command_idempotency_key=command.command_idempotency_key,
            command_digest=command.command_digest,
            command_actor=command.actor,
            result_kind=RESULT_KIND_STEP,
            execution_order_id=order.execution_order_id,
            execution_order_digest=order.execution_order_digest,
            attempt_id=attempt.attempt_id,
            attempt_digest=attempt.attempt_digest,
            fill_id=None if fill is None else fill.fill_id,
            fill_digest=None if fill is None else fill.fill_digest,
            settlement_link_id=None if link is None else link.settlement_link_id,
            settlement_link_evidence_digest=(
                None if link is None else link.settlement_link_evidence_digest
            ),
            account_event_id=commit.account_event_id,
            created_at=self._now(),
        )

    @staticmethod
    def _same_key(
        repository: SqlAlchemyPaperExecutionRepository,
        *,
        namespace: str,
        command_key: str,
        command_digest: str,
    ):
        receipt = repository.get_receipt(
            namespace=namespace, command_idempotency_key=command_key
        )
        if receipt is None:
            return None
        if receipt.command_digest != command_digest:
            raise PaperExecutionIdempotencyConflictError()
        return repository.resolve_receipt(receipt=receipt)

    def _create_order_in_session(
        self,
        session: Session,
        command: CreatePaperExecutionOrderCommand,
    ) -> PaperExecutionStoredResult[PaperExecutionOrder]:
        """Share the exact S211 create sequence inside one caller transaction."""
        try:
            valid_command = validate_create_paper_execution_order_command(command)
        except (TypeError, ValueError) as exc:
            raise PaperExecutionCorruptAuthorityError() from exc
        repository = SqlAlchemyPaperExecutionRepository(session=session)
        replay = self._same_key(
            repository,
            namespace=COMMAND_NAMESPACE_CREATE_ORDER,
            command_key=valid_command.command_idempotency_key,
            command_digest=valid_command.command_digest,
        )
        if replay is not None:
            if type(replay) is not PaperExecutionOrder:
                raise PaperExecutionCorruptAuthorityError()
            return PaperExecutionStoredResult(result=replay, replayed=True)

        converged = repository.find_create_convergence(command=valid_command)
        if converged is not None:
            converged = repository.load_historical_history(
                execution_order_id=converged.execution_order_id
            ).order
            repository.append_receipt(
                receipt=self._receipt_for_order(valid_command, converged)
            )
            return PaperExecutionStoredResult(result=converged, replayed=True)

        intent, decision = self._upstream(session, valid_command)
        account, _history, account_state = self._account(
            session, account_id=intent.account_reference.account_id
        )
        calendar, trading_session, replay_engine = self._market(
            session, order_or_intent=intent
        )
        try:
            order = create_paper_execution_order(
                valid_command,
                intent=intent,
                decision=decision,
                account_state=account_state,
                calendar=calendar,
                session=trading_session,
                replay_engine=replay_engine,
                created_at=self._now(),
            )
        except ValueError as exc:
            raise PaperExecutionStaleAuthorityError() from exc

        for existing in repository.list_orders(
            account_id=order.account_id,
            replay_id=order.market_handoff_reference.replay_id,
            trading_session_id=order.market_handoff_reference.trading_session_id,
        ):
            if not repository.load_historical_history(
                execution_order_id=existing.execution_order_id
            ).state.terminal:
                raise PaperExecutionOperationConflictError()
        repository.append_order(order=order)
        repository.append_receipt(receipt=self._receipt_for_order(valid_command, order))
        return PaperExecutionStoredResult(result=order, replayed=False)

    def create_order(
        self, command: CreatePaperExecutionOrderCommand
    ) -> PaperExecutionStoredResult[PaperExecutionOrder]:
        with self._write() as session:
            return self._create_order_in_session(session, command)

    def create_order_from_references(
        self,
        *,
        intent_id: str,
        intent_digest: str,
        decision_id: str,
        decision_digest: str,
        execution_policy_reference: PaperExecutionPolicyReference,
        command_idempotency_key: str,
        actor: str,
    ) -> PaperExecutionStoredResult[PaperExecutionHistory]:
        """Compose trusted M33 references and create within one S211 transaction."""
        with self._write() as session:
            try:
                intent = SqlAlchemyOrderIntentRepository(session=session).get(
                    intent_id=intent_id
                )
                decision = SqlAlchemyPreTradeRiskDecisionRepository(
                    session=session
                ).get(decision_id=decision_id)
            except (StrategyOrderCorruptAuthorityError, TypeError, ValueError) as exc:
                raise PaperExecutionCorruptAuthorityError() from exc
            if intent is None or decision is None:
                raise PaperExecutionNotFoundError()
            if (
                intent.intent_digest != intent_digest
                or decision.decision_digest != decision_digest
            ):
                raise PaperExecutionStaleAuthorityError()
            try:
                command = create_paper_execution_order_command(
                    order_intent_reference=create_order_intent_reference(intent),
                    risk_handoff_reference=(
                        create_paper_execution_risk_handoff_reference(
                            decision=decision, intent=intent
                        )
                    ),
                    execution_policy_reference=execution_policy_reference,
                    command_idempotency_key=command_idempotency_key,
                    actor=actor,
                )
            except (TypeError, ValueError) as exc:
                raise PaperExecutionStaleAuthorityError() from exc
            stored = self._create_order_in_session(session, command)
            history = SqlAlchemyPaperExecutionRepository(
                session=session
            ).load_historical_history(
                execution_order_id=stored.result.execution_order_id
            )
            return PaperExecutionStoredResult(
                result=history,
                replayed=stored.replayed,
            )

    def create_paper_execution_order(
        self, command: CreatePaperExecutionOrderCommand
    ) -> PaperExecutionStoredResult[PaperExecutionOrder]:
        return self.create_order(command)

    def step_order(
        self, command: StepPaperExecutionOrderCommand
    ) -> PaperExecutionStoredResult[PaperExecutionStepCommit]:
        try:
            valid_command = validate_step_paper_execution_order_command(command)
        except (TypeError, ValueError) as exc:
            raise PaperExecutionCorruptAuthorityError() from exc
        with self._write() as session:
            repository = SqlAlchemyPaperExecutionRepository(session=session)
            replay = self._same_key(
                repository,
                namespace=COMMAND_NAMESPACE_STEP_ORDER,
                command_key=valid_command.command_idempotency_key,
                command_digest=valid_command.command_digest,
            )
            if replay is not None:
                if type(replay) is not PaperExecutionStepCommit:
                    raise PaperExecutionCorruptAuthorityError()
                return PaperExecutionStoredResult(result=replay, replayed=True)

            order = repository.get_order(
                execution_order_id=valid_command.execution_order_reference.execution_order_id
            )
            if order is None:
                raise PaperExecutionNotFoundError()
            if (
                order.execution_order_digest
                != valid_command.execution_order_reference.execution_order_digest
            ):
                raise PaperExecutionStaleAuthorityError()

            history = repository.load_historical_history(
                execution_order_id=order.execution_order_id
            )
            converged_attempt = next(
                (
                    attempt
                    for attempt in history.attempts
                    if attempt.execution_version_before
                    == valid_command.expected_execution_version
                ),
                None,
            )
            if converged_attempt is not None:
                commit = repository._step_commit(order=order, attempt=converged_attempt)
                repository.append_receipt(
                    receipt=self._receipt_for_step(valid_command, order, commit)
                )
                return PaperExecutionStoredResult(result=commit, replayed=True)

            if (
                history.state.execution_version
                != valid_command.expected_execution_version
            ):
                raise PaperExecutionStaleAuthorityError()
            if history.state.terminal:
                raise PaperExecutionOperationConflictError()

            account, account_history, account_state = self._account(
                session, account_id=order.account_id
            )
            expected_version = (
                order.account_handoff_reference.account_head_version
                if not history.settlement_links
                else history.settlement_links[-1].account_version
            )
            expected_event = (
                order.account_handoff_reference.account_head_event_id
                if not history.settlement_links
                else history.settlement_links[-1].account_event_id
            )
            expected_chain = (
                order.account_handoff_reference.account_head_chain_digest
                if not history.settlement_links
                else history.settlement_links[-1].account_chain_digest
            )
            if (
                account.head_version != expected_version
                or account.head_event_id != expected_event
                or account.head_chain_digest != expected_chain
            ):
                raise PaperExecutionStaleAuthorityError()
            calendar, trading_session, replay_engine = self._market(
                session, order_or_intent=order
            )
            pre_cursor = replay_engine.cursor
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
            if pre_cursor != expected_cursor:
                raise PaperExecutionStaleAuthorityError()
            try:
                step_result = step_paper_execution_order(
                    valid_command,
                    order=order,
                    account_state=account_state,
                    calendar=calendar,
                    session=trading_session,
                    replay_engine=replay_engine,
                    created_at=self._now(),
                    current_state=history.state,
                    attempts=history.attempts,
                    fills=history.fills,
                )
            except ValueError as exc:
                raise PaperExecutionStaleAuthorityError() from exc

            settlement = None
            if step_result.fill is not None:
                settlement = settle_paper_execution_fill(
                    order=order,
                    attempt=step_result.attempt,
                    fill=step_result.fill,
                    account_state=account_state,
                    recorded_timestamp_utc=self._now(),
                )

            repository.append_attempt(attempt=step_result.attempt)
            if step_result.fill is not None:
                repository.append_fill(fill=step_result.fill)

            if settlement is not None:
                bundle = settlement.ledger_bundle
                next_history = (*account_history, bundle)
                projection = rebuild_paper_account_projection(next_history)
                next_account = PaperAccountRecord(
                    record_schema_version=1,
                    account_identity=account.account_identity,
                    lifecycle_status=bundle.resulting_state.lifecycle_status,
                    head_version=bundle.resulting_state.head_version,
                    head_event_id=bundle.resulting_state.head_event_id,
                    head_chain_digest=bundle.resulting_state.head_chain_digest,
                    projection_status="current",
                    updated_timestamp=bundle.event.recorded_timestamp_utc,
                    closed_timestamp=account.closed_timestamp,
                )
                if not SqlAlchemyPaperAccountRepository(
                    session=session
                ).append_mutation(
                    prior_account=account,
                    next_account=next_account,
                    bundle=bundle,
                    projection=projection,
                    updated_timestamp=bundle.event.recorded_timestamp_utc,
                ):
                    raise PaperExecutionConcurrencyConflictError()
                repository.append_settlement_link(link=settlement.settlement_link)

            post_cursor = replay_engine.cursor
            if post_cursor != pre_cursor:
                if not SqlAlchemyMarketTimeRepository(
                    session=session
                ).replace_replay_checkpoint(
                    expected_cursor=pre_cursor,
                    session=replay_engine.session,
                ):
                    raise PaperExecutionConcurrencyConflictError()

            commit = PaperExecutionStepCommit(
                step_result=step_result,
                settlement_link=(
                    None if settlement is None else settlement.settlement_link
                ),
                account_event_id=(
                    None
                    if settlement is None
                    else settlement.ledger_bundle.event.event_id
                ),
            )
            repository.append_receipt(
                receipt=self._receipt_for_step(valid_command, order, commit)
            )
            return PaperExecutionStoredResult(result=commit, replayed=False)

    def step_paper_execution_order(
        self, command: StepPaperExecutionOrderCommand
    ) -> PaperExecutionStoredResult[PaperExecutionStepCommit]:
        return self.step_order(command)

    def step_order_from_reference(
        self,
        *,
        execution_order_id: str,
        execution_order_digest: str,
        expected_execution_version: int,
        command_idempotency_key: str,
        actor: str,
    ) -> PaperExecutionStoredResult[PaperExecutionStepCommit]:
        """Compose the exact domain command; S211 still owns the atomic step."""
        history = self.get_history(execution_order_id=execution_order_id)
        if history.order.execution_order_digest != execution_order_digest:
            raise PaperExecutionStaleAuthorityError()
        try:
            command = create_step_paper_execution_order_command(
                execution_order_reference=create_paper_execution_order_reference(
                    history.order
                ),
                expected_execution_version=expected_execution_version,
                command_idempotency_key=command_idempotency_key,
                actor=actor,
            )
        except (TypeError, ValueError) as exc:
            raise PaperExecutionStaleAuthorityError() from exc
        return self.step_order(command)

    def get_history(self, *, execution_order_id: str) -> PaperExecutionHistory:
        """Return strictly reconstructed historical authority without live freshness."""
        with self._read() as session:
            repository = SqlAlchemyPaperExecutionRepository(session=session)
            if repository.get_order(execution_order_id=execution_order_id) is None:
                raise PaperExecutionNotFoundError()
            return repository.load_historical_history(
                execution_order_id=execution_order_id
            )

    def list_order_histories(
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
    ) -> PaperExecutionPage[PaperExecutionHistory]:
        with self._read() as session:
            repository = SqlAlchemyPaperExecutionRepository(session=session)
            try:
                page = repository.list_orders_page(
                    limit=limit,
                    cursor_created_at=cursor_created_at,
                    cursor_execution_order_id=cursor_execution_order_id,
                    account_id=account_id,
                    replay_id=replay_id,
                    trading_session_id=trading_session_id,
                    instrument_id=instrument_id,
                    side=side,
                )
            except (TypeError, ValueError) as exc:
                raise PaperExecutionCorruptAuthorityError() from exc
            return PaperExecutionPage(
                items=tuple(
                    repository.load_historical_history(
                        execution_order_id=order.execution_order_id
                    )
                    for order in page.items
                ),
                has_more=page.has_more,
            )

    def get_attempt(self, *, attempt_id: str) -> PaperExecutionAttempt:
        with self._read() as session:
            repository = SqlAlchemyPaperExecutionRepository(session=session)
            attempt = repository.get_attempt(attempt_id=attempt_id)
            if attempt is None:
                raise PaperExecutionNotFoundError()
            history = repository.load_historical_history(
                execution_order_id=(
                    attempt.execution_order_reference.execution_order_id
                )
            )
            if attempt not in history.attempts:
                raise PaperExecutionCorruptAuthorityError()
            return attempt

    def list_attempts(
        self,
        *,
        execution_order_id: str,
        limit: int,
        cursor_execution_version_before: int | None = None,
        cursor_attempt_id: str | None = None,
        version_anchor: int | None = None,
    ) -> PaperExecutionPage[PaperExecutionAttempt]:
        if type(limit) is not int or not 1 <= limit <= 200:
            raise PaperExecutionCorruptAuthorityError()
        if (cursor_execution_version_before is None) is not (
            cursor_attempt_id is None
        ):
            raise PaperExecutionCorruptAuthorityError()
        with self._read() as session:
            repository = SqlAlchemyPaperExecutionRepository(session=session)
            if repository.get_order(execution_order_id=execution_order_id) is None:
                raise PaperExecutionNotFoundError()
            history = repository.load_historical_history(
                execution_order_id=execution_order_id
            )
            anchor = (
                history.state.execution_version
                if version_anchor is None
                else version_anchor
            )
            if type(anchor) is not int or not 0 <= anchor <= history.state.execution_version:
                raise PaperExecutionCorruptAuthorityError()
            candidates = tuple(
                attempt
                for attempt in history.attempts
                if attempt.execution_version_before < anchor
            )
            if cursor_execution_version_before is not None:
                cursor_key = (
                    cursor_execution_version_before,
                    cursor_attempt_id,
                )
                candidates = tuple(
                    attempt
                    for attempt in candidates
                    if (
                        attempt.execution_version_before,
                        attempt.attempt_id,
                    )
                    > cursor_key
                )
            return PaperExecutionPage(
                items=candidates[:limit],
                has_more=len(candidates) > limit,
                version_anchor=anchor,
            )

    def get_fill(self, *, fill_id: str) -> PaperExecutionFill:
        with self._read() as session:
            repository = SqlAlchemyPaperExecutionRepository(session=session)
            fill = repository.get_fill(fill_id=fill_id)
            if fill is None:
                raise PaperExecutionNotFoundError()
            history = repository.load_historical_history(
                execution_order_id=fill.execution_order_reference.execution_order_id
            )
            if fill not in history.fills:
                raise PaperExecutionCorruptAuthorityError()
            return fill

    def list_fills(
        self,
        *,
        limit: int,
        cursor_created_at: datetime | None = None,
        cursor_fill_id: str | None = None,
        execution_order_id: str | None = None,
    ) -> PaperExecutionPage[PaperExecutionFill]:
        with self._read() as session:
            repository = SqlAlchemyPaperExecutionRepository(session=session)
            try:
                page = repository.list_fills_page(
                    limit=limit,
                    cursor_created_at=cursor_created_at,
                    cursor_fill_id=cursor_fill_id,
                    execution_order_id=execution_order_id,
                )
            except (TypeError, ValueError) as exc:
                raise PaperExecutionCorruptAuthorityError() from exc
            histories: dict[str, PaperExecutionHistory] = {}
            for fill in page.items:
                order_id = fill.execution_order_reference.execution_order_id
                history = histories.setdefault(
                    order_id,
                    repository.load_historical_history(
                        execution_order_id=order_id
                    ),
                )
                if fill not in history.fills:
                    raise PaperExecutionCorruptAuthorityError()
            return page

    def reconcile_order(self, *, execution_order_id: str) -> PaperExecutionHistory:
        with self._read() as session:
            repository = SqlAlchemyPaperExecutionRepository(session=session)
            if repository.get_order(execution_order_id=execution_order_id) is None:
                raise PaperExecutionNotFoundError()
            return repository.load_history(execution_order_id=execution_order_id)


__all__ = ["PaperExecutionApplicationService"]
