"""Transactional application service for durable Paper Accounts."""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from el_psy_quant.application.portfolio_reviews import (
    get_portfolio_review_detail,
)
from el_psy_quant.paper_account import (
    ApprovedPortfolioReviewReference,
    ClosePaperAccountCommand,
    FreezePaperAccountCommand,
    PaperAccountCloseEligibility,
    PaperAccountLedgerEventBundle,
    PaperAccountLedgerState,
    PaperAccountProjection,
    PaperAccountReconciliation,
    PaperAccountSnapshot,
    PaperMoney,
    PaperQuantity,
    PostPaperCashMovementCommand,
    PostPaperCashMovementType,
    PostPaperPositionAdjustmentCommand,
    ReactivatePaperAccountCommand,
    apply_approved_portfolio_review_link,
    apply_paper_account_lifecycle_command,
    apply_paper_cash_movement,
    apply_paper_position_adjustment,
    create_approved_portfolio_review_reference,
    create_close_paper_account_command,
    create_freeze_paper_account_command,
    create_link_approved_portfolio_review_command,
    create_paper_account_command,
    create_paper_account_event_bundle,
    create_paper_account_identity,
    create_paper_account_snapshot,
    create_paper_account_snapshot_command,
    create_post_paper_cash_movement_command,
    create_post_paper_position_adjustment_command,
    create_reactivate_paper_account_command,
    create_reconcile_paper_account_projection_command,
    rebuild_paper_account_projection,
    reconcile_paper_account_projection,
    replay_paper_account_ledger,
    verify_paper_account_projection,
)
from el_psy_quant.paper_account._shared import canonical_digest
from el_psy_quant.paper_account.ledger_state import (
    _create_ledger_bundle,
    _create_ledger_state,
)
from el_psy_quant.persistence.paper_account_repository import (
    SqlAlchemyPaperAccountRepository,
)
from el_psy_quant.persistence.paper_accounts import (
    PaperAccountApprovedEvidenceError,
    PaperAccountClosedError,
    PaperAccountCommandResult,
    PaperAccountConcurrencyConflictError,
    PaperAccountCreationKeyRecord,
    PaperAccountIdempotencyConflictError,
    PaperAccountLedgerPage,
    PaperAccountListPage,
    PaperAccountNotFoundError,
    PaperAccountOperationConflictError,
    PaperAccountPersistenceCorruptionError,
    PaperAccountProjectionReconciliationRequiredError,
    PaperAccountReconciliationResult,
    PaperAccountRecord,
    PaperAccountSnapshotResult,
    PaperAccountStorageBusyError,
    PaperAccountFrozenError,
    PaperAccountVersionConflictError,
    _exact_string,
    _exact_utc,
)

PaperAccountIdFactory = Callable[[str], str]
PaperAccountClock = Callable[[], datetime]
ApprovedPortfolioReviewVerifier = Callable[
    [str], ApprovedPortfolioReviewReference
]


@dataclass(frozen=True)
class PaperAccountDetail:
    """One account record paired with its verified current projection."""

    account: PaperAccountRecord
    projection: PaperAccountProjection


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


def _default_id_factory(kind: str) -> str:
    return f"{kind}_{uuid.uuid4().hex}"


def _is_busy(exc: OperationalError) -> bool:
    original = exc.orig
    if isinstance(original, sqlite3.OperationalError):
        message = str(original).lower()
        return "locked" in message or "busy" in message
    return False


def _ledger_bundle_from_cash(
    bundle,
    *,
    positions,
) -> PaperAccountLedgerEventBundle:
    cash_state = bundle.resulting_state
    state = _create_ledger_state(
        account_identity=cash_state.account_identity,
        lifecycle_status=cash_state.lifecycle_status,
        cash_balance=cash_state.cash_balance,
        positions=positions,
        approved_portfolio_reviews=cash_state.approved_portfolio_reviews,
        head_version=cash_state.head_version,
        head_event_id=cash_state.head_event_id,
        head_chain_digest=cash_state.head_chain_digest,
    )
    return _create_ledger_bundle(
        event=bundle.event,
        cash_entries=bundle.cash_entries,
        position_entries=(),
        resulting_state=state,
    )


class PaperAccountApplicationService:
    """Own transactions while delegating financial truth to pure domain code."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        clock: PaperAccountClock = _default_clock,
        id_factory: PaperAccountIdFactory = _default_id_factory,
        portfolio_review_artifact_root: str | Path | None = None,
        portfolio_review_session_factory: sessionmaker[Session] | None = None,
        approved_review_verifier: ApprovedPortfolioReviewVerifier | None = None,
    ) -> None:
        if not isinstance(session_factory, sessionmaker):
            raise TypeError("session_factory must be a SQLAlchemy sessionmaker")
        if not callable(clock) or not callable(id_factory):
            raise TypeError("clock and id_factory must be callable")
        if approved_review_verifier is not None and not callable(
            approved_review_verifier
        ):
            raise TypeError("approved_review_verifier must be callable")
        self._session_factory = session_factory
        self._clock = clock
        self._id_factory = id_factory
        self._portfolio_review_artifact_root = portfolio_review_artifact_root
        self._portfolio_review_session_factory = (
            portfolio_review_session_factory or session_factory
        )
        self._approved_review_verifier = approved_review_verifier

    def _now(self) -> datetime:
        return _exact_utc(self._clock(), "server clock")

    def _new_id(self, kind: str) -> str:
        return _exact_string(self._id_factory(kind), f"{kind}_id", 512)

    @contextmanager
    def _write_session(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            session.connection().exec_driver_sql("BEGIN IMMEDIATE")
            session.connection().exec_driver_sql(
                "PRAGMA defer_foreign_keys=ON"
            )
            yield session
            session.commit()
        except OperationalError as exc:
            session.rollback()
            if _is_busy(exc):
                raise PaperAccountStorageBusyError() from exc
            raise PaperAccountPersistenceCorruptionError() from exc
        except IntegrityError as exc:
            session.rollback()
            raise PaperAccountConcurrencyConflictError() from exc
        except SQLAlchemyError as exc:
            session.rollback()
            raise PaperAccountPersistenceCorruptionError() from exc
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def _read_session(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
        except OperationalError as exc:
            if _is_busy(exc):
                raise PaperAccountStorageBusyError() from exc
            raise PaperAccountPersistenceCorruptionError() from exc
        except SQLAlchemyError as exc:
            raise PaperAccountPersistenceCorruptionError() from exc
        finally:
            session.close()

    def _creation_intent(
        self,
        *,
        display_name: str,
        base_currency: str,
        initial_cash: PaperMoney,
        creation_idempotency_key: str,
        actor: str,
    ) -> tuple[str, str, str, str]:
        if type(initial_cash) is not PaperMoney:
            raise ValueError("initial_cash must be PaperMoney")
        if initial_cash.decimal_value < 0:
            raise ValueError("initial_cash must be non-negative")
        key = _exact_string(
            creation_idempotency_key,
            "creation_idempotency_key",
            128,
        )
        probe = create_paper_account_identity(
            account_id="creation-intent-validation",
            display_name=display_name,
            base_currency=base_currency,
            created_by=actor,
            created_timestamp=datetime(2000, 1, 1, tzinfo=timezone.utc),
        )
        digest = canonical_digest(
            {
                "schema_version": 1,
                "command_type": "create_paper_account_intent",
                "display_name": probe.display_name,
                "base_currency": probe.base_currency,
                "initial_cash": initial_cash.canonical,
                "creation_idempotency_key": key,
                "actor": probe.created_by,
            }
        )
        return probe.display_name, probe.base_currency, probe.created_by, digest

    def _require_account(
        self,
        repository: SqlAlchemyPaperAccountRepository,
        account_id: str,
    ) -> PaperAccountRecord:
        account = repository.get_account(account_id=account_id)
        if account is None:
            raise PaperAccountNotFoundError()
        return account

    def _verified_current(
        self,
        repository: SqlAlchemyPaperAccountRepository,
        account: PaperAccountRecord,
    ) -> tuple[
        tuple[PaperAccountLedgerEventBundle, ...],
        PaperAccountLedgerState,
        PaperAccountProjection,
    ]:
        history = repository.get_history(account=account)
        state = replay_paper_account_ledger(history)
        if account.projection_status != "current":
            raise PaperAccountProjectionReconciliationRequiredError()
        projection = repository.get_projection(account=account)
        if projection is None:
            raise PaperAccountProjectionReconciliationRequiredError()
        if (
            projection.source_account_version != account.head_version
            or projection.source_event_id != account.head_event_id
            or projection.source_chain_digest != account.head_chain_digest
        ):
            raise PaperAccountProjectionReconciliationRequiredError()
        verification = verify_paper_account_projection(history, projection)
        if verification.status != "current":
            raise PaperAccountProjectionReconciliationRequiredError()
        return history, state, projection

    def _command_replay(
        self,
        *,
        repository: SqlAlchemyPaperAccountRepository,
        account_id: str,
        command_key: str,
        command_digest: str,
    ) -> PaperAccountCommandResult | None:
        existing = repository.get_event_by_command_key(
            account_id=account_id,
            command_idempotency_key=command_key,
        )
        if existing is None:
            return None
        if existing.command_digest != command_digest:
            raise PaperAccountIdempotencyConflictError()
        account = self._require_account(repository, account_id)
        history = repository.get_history(account=account)
        event_index = next(
            (
                index
                for index, bundle in enumerate(history)
                if bundle.event.event_id == existing.event_id
            ),
            -1,
        )
        if event_index < 0:
            raise PaperAccountPersistenceCorruptionError()
        accepted_history = history[: event_index + 1]
        state = replay_paper_account_ledger(accepted_history)
        projection = rebuild_paper_account_projection(accepted_history)
        event = accepted_history[-1].event
        accepted_account = PaperAccountRecord(
            record_schema_version=1,
            account_identity=state.account_identity,
            lifecycle_status=state.lifecycle_status,
            head_version=state.head_version,
            head_event_id=state.head_event_id,
            head_chain_digest=state.head_chain_digest,
            projection_status="current",
            updated_timestamp=event.recorded_timestamp_utc,
            closed_timestamp=(
                event.recorded_timestamp_utc
                if state.lifecycle_status == "closed"
                else None
            ),
        )
        return PaperAccountCommandResult(
            account=accepted_account,
            event=event,
            projection=projection,
            history=accepted_history,
            replayed=True,
        )

    def create_account(
        self,
        *,
        display_name: str,
        base_currency: str,
        initial_cash: PaperMoney,
        creation_idempotency_key: str,
        actor: str,
    ) -> PaperAccountCommandResult:
        """Create one account atomically or replay its global creation key."""
        normalized_name, currency, normalized_actor, request_digest = (
            self._creation_intent(
                display_name=display_name,
                base_currency=base_currency,
                initial_cash=initial_cash,
                creation_idempotency_key=creation_idempotency_key,
                actor=actor,
            )
        )
        with self._write_session() as session:
            repository = SqlAlchemyPaperAccountRepository(session=session)
            existing = repository.get_creation_key(
                creation_idempotency_key=creation_idempotency_key
            )
            if existing is not None:
                if existing.creation_request_digest != request_digest:
                    raise PaperAccountIdempotencyConflictError()
                account = self._require_account(
                    repository, existing.account_id
                )
                complete_history = repository.get_history(account=account)
                history = complete_history[:1]
                event = history[0].event
                if event.event_id != existing.creation_event_id:
                    raise PaperAccountPersistenceCorruptionError()
                state = replay_paper_account_ledger(history)
                projection = rebuild_paper_account_projection(history)
                accepted_account = PaperAccountRecord(
                    record_schema_version=1,
                    account_identity=state.account_identity,
                    lifecycle_status=state.lifecycle_status,
                    head_version=state.head_version,
                    head_event_id=state.head_event_id,
                    head_chain_digest=state.head_chain_digest,
                    projection_status="current",
                    updated_timestamp=event.recorded_timestamp_utc,
                    closed_timestamp=None,
                )
                return PaperAccountCommandResult(
                    account=accepted_account,
                    event=event,
                    projection=projection,
                    history=history,
                    replayed=True,
                )

            account_id = self._new_id("paper_account")
            event_id = self._new_id("paper_account_event")
            cash_entry_id = self._new_id("paper_cash_entry")
            recorded = self._now()
            identity = create_paper_account_identity(
                account_id=account_id,
                display_name=normalized_name,
                base_currency=currency,
                created_by=normalized_actor,
                created_timestamp=recorded,
            )
            command = create_paper_account_command(
                account_identity=identity,
                initial_cash=initial_cash,
                command_idempotency_key=creation_idempotency_key,
                actor=normalized_actor,
            )
            raw_bundle = create_paper_account_event_bundle(
                command,
                event_id=event_id,
                cash_entry_id=cash_entry_id,
                recorded_timestamp_utc=recorded,
            )
            bundle = _ledger_bundle_from_cash(raw_bundle, positions=())
            history = (bundle,)
            projection = rebuild_paper_account_projection(history)
            account = PaperAccountRecord(
                record_schema_version=1,
                account_identity=identity,
                lifecycle_status="active",
                head_version=1,
                head_event_id=event_id,
                head_chain_digest=bundle.event.chain_digest,
                projection_status="current",
                updated_timestamp=recorded,
                closed_timestamp=None,
            )
            creation_key = PaperAccountCreationKeyRecord(
                record_schema_version=1,
                creation_idempotency_key=creation_idempotency_key,
                creation_request_digest=request_digest,
                account_id=account_id,
                creation_event_id=event_id,
                created_timestamp=recorded,
            )
            repository.add_created_account(
                account=account,
                creation_key=creation_key,
                bundle=bundle,
                projection=projection,
                updated_timestamp=recorded,
            )
            return PaperAccountCommandResult(
                account=account,
                event=bundle.event,
                projection=projection,
                history=history,
                replayed=False,
            )

    def get_account(self, *, account_id: str) -> PaperAccountRecord:
        with self._read_session() as session:
            repository = SqlAlchemyPaperAccountRepository(session=session)
            account = self._require_account(repository, account_id)
            repository.get_history(account=account)
            return account

    def list_accounts(
        self, *, lifecycle_status: str | None = None
    ) -> tuple[PaperAccountRecord, ...]:
        with self._read_session() as session:
            return SqlAlchemyPaperAccountRepository(
                session=session
            ).list_accounts(lifecycle_status=lifecycle_status)

    def list_account_page(
        self,
        *,
        lifecycle_status: str | None,
        limit: int,
        cursor_created_timestamp: datetime | None = None,
        cursor_account_id: str | None = None,
    ) -> PaperAccountListPage:
        """Return one repository-bounded deterministic account page."""
        with self._read_session() as session:
            return SqlAlchemyPaperAccountRepository(
                session=session
            ).list_account_page(
                lifecycle_status=lifecycle_status,
                limit=limit,
                cursor_created_timestamp=cursor_created_timestamp,
                cursor_account_id=cursor_account_id,
            )

    def get_account_detail(self, *, account_id: str) -> PaperAccountDetail:
        """Return compact account identity plus one verified current cache."""
        with self._read_session() as session:
            repository = SqlAlchemyPaperAccountRepository(session=session)
            account = self._require_account(repository, account_id)
            _, _, projection = self._verified_current(repository, account)
            return PaperAccountDetail(account=account, projection=projection)

    def get_account_history(
        self, *, account_id: str
    ) -> tuple[PaperAccountLedgerEventBundle, ...]:
        with self._read_session() as session:
            repository = SqlAlchemyPaperAccountRepository(session=session)
            account = self._require_account(repository, account_id)
            return repository.get_history(account=account)

    def get_account_history_page(
        self,
        *,
        account_id: str,
        after_sequence_number: int,
        limit: int,
    ) -> PaperAccountLedgerPage:
        """Return one bounded validated immutable-ledger page."""
        with self._read_session() as session:
            repository = SqlAlchemyPaperAccountRepository(session=session)
            account = self._require_account(repository, account_id)
            return repository.get_history_page(
                account=account,
                after_sequence_number=after_sequence_number,
                limit=limit,
            )

    def get_current_projection(
        self, *, account_id: str
    ) -> PaperAccountProjection:
        with self._read_session() as session:
            repository = SqlAlchemyPaperAccountRepository(session=session)
            account = self._require_account(repository, account_id)
            _, _, projection = self._verified_current(repository, account)
            return projection

    def _mutate(
        self,
        *,
        command,
        apply: Callable[
            [PaperAccountLedgerState, str, datetime],
            PaperAccountLedgerEventBundle,
        ],
    ) -> PaperAccountCommandResult:
        with self._write_session() as session:
            repository = SqlAlchemyPaperAccountRepository(session=session)
            replay = self._command_replay(
                repository=repository,
                account_id=command.account_id,
                command_key=command.command_idempotency_key,
                command_digest=command.command_digest,
            )
            if replay is not None:
                return replay
            account = self._require_account(repository, command.account_id)
            history, state, _ = self._verified_current(
                repository, account
            )
            if command.expected_account_version != account.head_version:
                raise PaperAccountVersionConflictError()
            if state.lifecycle_status == "closed":
                raise PaperAccountClosedError()
            if state.lifecycle_status == "frozen" and type(command) in (
                PostPaperCashMovementCommand,
                PostPaperPositionAdjustmentCommand,
                FreezePaperAccountCommand,
            ):
                raise PaperAccountFrozenError()
            recorded = self._now()
            bundle = apply(
                state,
                self._new_id("paper_account_event"),
                recorded,
            )
            next_history = (*history, bundle)
            projection = rebuild_paper_account_projection(next_history)
            next_account = PaperAccountRecord(
                record_schema_version=1,
                account_identity=account.account_identity,
                lifecycle_status=bundle.resulting_state.lifecycle_status,
                head_version=bundle.resulting_state.head_version,
                head_event_id=bundle.resulting_state.head_event_id,
                head_chain_digest=bundle.resulting_state.head_chain_digest,
                projection_status="current",
                updated_timestamp=recorded,
                closed_timestamp=(
                    recorded
                    if bundle.resulting_state.lifecycle_status == "closed"
                    else None
                ),
            )
            if not repository.append_mutation(
                prior_account=account,
                next_account=next_account,
                bundle=bundle,
                projection=projection,
                updated_timestamp=recorded,
            ):
                raise PaperAccountConcurrencyConflictError()
            return PaperAccountCommandResult(
                account=next_account,
                event=bundle.event,
                projection=projection,
                history=next_history,
                replayed=False,
            )

    def post_cash_movement(
        self,
        *,
        account_id: str,
        expected_account_version: int,
        command_idempotency_key: str,
        actor: str,
        reason: str,
        movement_type: PostPaperCashMovementType,
        requested_amount: PaperMoney,
        effective_timestamp_utc: datetime | None = None,
    ) -> PaperAccountCommandResult:
        command = create_post_paper_cash_movement_command(
            account_id=account_id,
            expected_account_version=expected_account_version,
            command_idempotency_key=command_idempotency_key,
            actor=actor,
            reason=reason,
            movement_type=movement_type,
            requested_amount=requested_amount,
            effective_timestamp_utc=effective_timestamp_utc,
        )

        def apply(
            state: PaperAccountLedgerState,
            event_id: str,
            recorded: datetime,
        ) -> PaperAccountLedgerEventBundle:
            raw = apply_paper_cash_movement(
                state.to_cash_state(),
                command,
                event_id=event_id,
                cash_entry_id=self._new_id("paper_cash_entry"),
                recorded_timestamp_utc=recorded,
            )
            return _ledger_bundle_from_cash(raw, positions=state.positions)

        return self._mutate(command=command, apply=apply)

    def post_position_adjustment(
        self,
        *,
        account_id: str,
        expected_account_version: int,
        command_idempotency_key: str,
        actor: str,
        reason: str,
        symbol: str,
        adjustment_category: str,
        signed_quantity_delta: PaperQuantity,
        signed_cost_basis_delta: PaperMoney,
        effective_timestamp_utc: datetime | None = None,
    ) -> PaperAccountCommandResult:
        command = create_post_paper_position_adjustment_command(
            account_id=account_id,
            expected_account_version=expected_account_version,
            command_idempotency_key=command_idempotency_key,
            actor=actor,
            reason=reason,
            symbol=symbol,
            adjustment_category=adjustment_category,  # type: ignore[arg-type]
            signed_quantity_delta=signed_quantity_delta,
            signed_cost_basis_delta=signed_cost_basis_delta,
            effective_timestamp_utc=effective_timestamp_utc,
        )
        return self._mutate(
            command=command,
            apply=lambda state, event_id, recorded: (
                apply_paper_position_adjustment(
                    state,
                    command,
                    event_id=event_id,
                    position_entry_id=self._new_id("paper_position_entry"),
                    recorded_timestamp_utc=recorded,
                )
            ),
        )

    def _lifecycle_mutation(
        self,
        command: (
            FreezePaperAccountCommand
            | ReactivatePaperAccountCommand
            | ClosePaperAccountCommand
        ),
    ) -> PaperAccountCommandResult:
        def apply(
            state: PaperAccountLedgerState,
            event_id: str,
            recorded: datetime,
        ) -> PaperAccountLedgerEventBundle:
            eligibility = (
                PaperAccountCloseEligibility(
                    cash_is_zero=state.cash_balance.decimal_value == 0,
                    position_quantities_are_zero=not state.positions,
                    aggregate_cost_bases_are_zero=not state.positions,
                )
                if type(command) is ClosePaperAccountCommand
                else None
            )
            raw = apply_paper_account_lifecycle_command(
                state.to_cash_state(),
                command,
                event_id=event_id,
                recorded_timestamp_utc=recorded,
                close_eligibility=eligibility,
            )
            return _ledger_bundle_from_cash(raw, positions=state.positions)

        return self._mutate(command=command, apply=apply)

    def freeze_account(
        self,
        *,
        account_id: str,
        expected_account_version: int,
        command_idempotency_key: str,
        actor: str,
        reason: str,
    ) -> PaperAccountCommandResult:
        return self._lifecycle_mutation(
            create_freeze_paper_account_command(
                account_id=account_id,
                expected_account_version=expected_account_version,
                command_idempotency_key=command_idempotency_key,
                actor=actor,
                reason=reason,
            )
        )

    def reactivate_account(
        self,
        *,
        account_id: str,
        expected_account_version: int,
        command_idempotency_key: str,
        actor: str,
        reason: str,
    ) -> PaperAccountCommandResult:
        return self._lifecycle_mutation(
            create_reactivate_paper_account_command(
                account_id=account_id,
                expected_account_version=expected_account_version,
                command_idempotency_key=command_idempotency_key,
                actor=actor,
                reason=reason,
            )
        )

    def close_account(
        self,
        *,
        account_id: str,
        expected_account_version: int,
        command_idempotency_key: str,
        actor: str,
        reason: str,
    ) -> PaperAccountCommandResult:
        return self._lifecycle_mutation(
            create_close_paper_account_command(
                account_id=account_id,
                expected_account_version=expected_account_version,
                command_idempotency_key=command_idempotency_key,
                actor=actor,
                reason=reason,
            )
        )

    def _approved_reference(
        self, review_id: str
    ) -> ApprovedPortfolioReviewReference:
        try:
            if self._approved_review_verifier is not None:
                result = self._approved_review_verifier(review_id)
            else:
                if self._portfolio_review_artifact_root is None:
                    raise PaperAccountApprovedEvidenceError()
                detail = get_portfolio_review_detail(
                    session_factory=self._portfolio_review_session_factory,
                    artifact_root=self._portfolio_review_artifact_root,
                    review_id=review_id,
                )
                if (
                    detail.record.status != "approved"
                    or detail.decision is None
                    or detail.decision.outcome != "approved"
                ):
                    raise PaperAccountApprovedEvidenceError()
                result = create_approved_portfolio_review_reference(
                    detail.decision
                )
            if type(result) is not ApprovedPortfolioReviewReference:
                raise PaperAccountApprovedEvidenceError()
            return result
        except PaperAccountApprovedEvidenceError:
            raise
        except Exception as exc:
            raise PaperAccountApprovedEvidenceError() from exc

    def link_approved_portfolio_review(
        self,
        *,
        account_id: str,
        expected_account_version: int,
        command_idempotency_key: str,
        actor: str,
        reason: str,
        review_id: str,
    ) -> PaperAccountCommandResult:
        """Reopen approved M30 authority before creating a governance-only link."""
        with self._write_session() as session:
            repository = SqlAlchemyPaperAccountRepository(session=session)
            existing = repository.get_event_by_command_key(
                account_id=account_id,
                command_idempotency_key=command_idempotency_key,
            )
            if existing is not None:
                account = self._require_account(repository, account_id)
                history = repository.get_history(account=account)
                event = next(
                    (
                        bundle.event
                        for bundle in history
                        if bundle.event.event_id == existing.event_id
                    ),
                    None,
                )
                reference = getattr(
                    getattr(event, "details", None),
                    "approved_portfolio_review",
                    None,
                )
                if (
                    event is None
                    or type(reference) is not ApprovedPortfolioReviewReference
                    or reference.review_id != review_id
                ):
                    raise PaperAccountIdempotencyConflictError()
                replay_command = create_link_approved_portfolio_review_command(
                    account_id=account_id,
                    expected_account_version=expected_account_version,
                    command_idempotency_key=command_idempotency_key,
                    actor=actor,
                    reason=reason,
                    approved_portfolio_review=reference,
                )
                if replay_command.command_digest != existing.command_digest:
                    raise PaperAccountIdempotencyConflictError()
                replay = self._command_replay(
                    repository=repository,
                    account_id=account_id,
                    command_key=command_idempotency_key,
                    command_digest=replay_command.command_digest,
                )
                if replay is None:
                    raise PaperAccountPersistenceCorruptionError()
                return replay

            account = self._require_account(repository, account_id)
            history, state, _ = self._verified_current(
                repository, account
            )
            if expected_account_version != account.head_version:
                raise PaperAccountVersionConflictError()
            if state.lifecycle_status == "closed":
                raise PaperAccountClosedError()
            if state.lifecycle_status == "frozen":
                raise PaperAccountFrozenError()
            reference = self._approved_reference(review_id)
            command = create_link_approved_portfolio_review_command(
                account_id=account_id,
                expected_account_version=expected_account_version,
                command_idempotency_key=command_idempotency_key,
                actor=actor,
                reason=reason,
                approved_portfolio_review=reference,
            )
            recorded = self._now()
            raw = apply_approved_portfolio_review_link(
                state.to_cash_state(),
                command,
                event_id=self._new_id("paper_account_event"),
                recorded_timestamp_utc=recorded,
            )
            bundle = _ledger_bundle_from_cash(raw, positions=state.positions)
            next_history = (*history, bundle)
            projection = rebuild_paper_account_projection(next_history)
            next_account = PaperAccountRecord(
                record_schema_version=1,
                account_identity=account.account_identity,
                lifecycle_status=state.lifecycle_status,
                head_version=bundle.event.account_version,
                head_event_id=bundle.event.event_id,
                head_chain_digest=bundle.event.chain_digest,
                projection_status="current",
                updated_timestamp=recorded,
                closed_timestamp=None,
            )
            if not repository.append_mutation(
                prior_account=account,
                next_account=next_account,
                bundle=bundle,
                projection=projection,
                updated_timestamp=recorded,
            ):
                raise PaperAccountConcurrencyConflictError()
            return PaperAccountCommandResult(
                account=next_account,
                event=bundle.event,
                projection=projection,
                history=next_history,
                replayed=False,
            )

    def rebuild_projection(
        self,
        *,
        account_id: str,
        expected_account_version: int,
        expected_head_event_id: str,
        expected_head_chain_digest: str,
    ) -> PaperAccountProjection:
        with self._write_session() as session:
            repository = SqlAlchemyPaperAccountRepository(session=session)
            account = self._require_account(repository, account_id)
            history = repository.get_history(account=account)
            if (
                expected_account_version != account.head_version
                or expected_head_event_id != account.head_event_id
                or expected_head_chain_digest != account.head_chain_digest
            ):
                raise PaperAccountVersionConflictError()
            projection = rebuild_paper_account_projection(history)
            recorded = self._now()
            repository.replace_projection(
                projection=projection,
                updated_timestamp=recorded,
            )
            if not repository.update_projection_status(
                account=account,
                projection_status="current",
                updated_timestamp=recorded,
            ):
                raise PaperAccountConcurrencyConflictError()
            return projection

    def create_snapshot(
        self,
        *,
        account_id: str,
        expected_account_version: int,
        expected_head_event_id: str,
        expected_head_chain_digest: str,
        operation_idempotency_key: str,
        actor: str,
        reason: str,
    ) -> PaperAccountSnapshotResult:
        command = create_paper_account_snapshot_command(
            account_id=account_id,
            expected_account_version=expected_account_version,
            expected_head_event_id=expected_head_event_id,
            expected_head_chain_digest=expected_head_chain_digest,
            operation_idempotency_key=operation_idempotency_key,
            actor=actor,
            reason=reason,
        )
        with self._write_session() as session:
            repository = SqlAlchemyPaperAccountRepository(session=session)
            existing = repository.get_snapshot_by_operation_key(
                account_id=account_id,
                operation_idempotency_key=operation_idempotency_key,
            )
            if existing is not None:
                if existing.operation_command_digest != command.command_digest:
                    raise PaperAccountOperationConflictError()
                return PaperAccountSnapshotResult(
                    snapshot=existing,
                    replayed=True,
                )
            account = self._require_account(repository, account_id)
            history = repository.get_history(account=account)
            snapshot = create_paper_account_snapshot(
                history,
                command,
                snapshot_id=self._new_id("paper_account_snapshot"),
                recorded_timestamp_utc=self._now(),
            )
            repository.add_snapshot(snapshot=snapshot)
            return PaperAccountSnapshotResult(
                snapshot=snapshot,
                replayed=False,
            )

    def reconcile_projection(
        self,
        *,
        account_id: str,
        expected_account_version: int,
        expected_head_event_id: str,
        expected_head_chain_digest: str,
        operation_idempotency_key: str,
        actor: str,
        reason: str,
    ) -> PaperAccountReconciliationResult:
        command = create_reconcile_paper_account_projection_command(
            account_id=account_id,
            expected_account_version=expected_account_version,
            expected_head_event_id=expected_head_event_id,
            expected_head_chain_digest=expected_head_chain_digest,
            operation_idempotency_key=operation_idempotency_key,
            actor=actor,
            reason=reason,
        )
        with self._write_session() as session:
            repository = SqlAlchemyPaperAccountRepository(session=session)
            existing = repository.get_reconciliation_by_operation_key(
                account_id=account_id,
                operation_idempotency_key=operation_idempotency_key,
            )
            if existing is not None:
                if existing.operation_command_digest != command.command_digest:
                    raise PaperAccountOperationConflictError()
                return PaperAccountReconciliationResult(
                    reconciliation=existing,
                    replayed=True,
                )
            account = self._require_account(repository, account_id)
            history = repository.get_history(account=account)
            candidate = repository.get_projection(account=account)
            if candidate is None:
                raise PaperAccountProjectionReconciliationRequiredError()
            recorded = self._now()
            reconciliation = reconcile_paper_account_projection(
                history,
                candidate,
                command,
                reconciliation_id=self._new_id(
                    "paper_account_reconciliation"
                ),
                recorded_timestamp_utc=recorded,
            )
            repository.add_reconciliation(
                reconciliation=reconciliation
            )
            if not repository.update_projection_status(
                account=account,
                projection_status=(
                    "current"
                    if reconciliation.outcome == "matched"
                    else "reconciliation_required"
                ),
                updated_timestamp=recorded,
            ):
                raise PaperAccountConcurrencyConflictError()
            return PaperAccountReconciliationResult(
                reconciliation=reconciliation,
                replayed=False,
            )

    def get_snapshot(self, *, snapshot_id: str) -> PaperAccountSnapshot:
        with self._read_session() as session:
            snapshot = SqlAlchemyPaperAccountRepository(
                session=session
            ).get_snapshot(snapshot_id=snapshot_id)
            if snapshot is None:
                raise PaperAccountOperationConflictError()
            return snapshot

    def get_reconciliation(
        self, *, reconciliation_id: str
    ) -> PaperAccountReconciliation:
        with self._read_session() as session:
            reconciliation = SqlAlchemyPaperAccountRepository(
                session=session
            ).get_reconciliation(reconciliation_id=reconciliation_id)
            if reconciliation is None:
                raise PaperAccountOperationConflictError()
            return reconciliation


__all__ = [
    "ApprovedPortfolioReviewVerifier",
    "PaperAccountApplicationService",
    "PaperAccountClock",
    "PaperAccountDetail",
    "PaperAccountIdFactory",
]
