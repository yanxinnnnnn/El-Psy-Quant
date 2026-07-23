"""Fail-closed deterministic replay of the cash-only Paper Account ledger."""

from __future__ import annotations

import hashlib
from datetime import timedelta
from typing import Iterable

from el_psy_quant.paper_account._shared import (
    canonical_digest,
    money_from_decimal,
    normalize_bounded_string,
    normalize_utc_datetime,
    validate_digest,
)
from el_psy_quant.paper_account.cash_commands import (
    PostPaperCashMovementCommand,
)
from el_psy_quant.paper_account.cash_ledger import (
    PAPER_CASH_LEDGER_ENTRY_SCHEMA_VERSION,
    PaperCashLedgerEntry,
)
from el_psy_quant.paper_account.cash_state import (
    PaperAccountCashState,
    PaperAccountEventBundle,
    _create_state,
    _signed_cash_movement,
    _validate_state,
)
from el_psy_quant.paper_account.commands import (
    MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
    MAX_PAPER_ACCOUNT_COMMAND_REASON_LENGTH,
    ClosePaperAccountCommand,
    CreatePaperAccountCommand,
    FreezePaperAccountCommand,
    LinkApprovedPortfolioReviewCommand,
    ReactivatePaperAccountCommand,
)
from el_psy_quant.paper_account.decimals import PaperMoney
from el_psy_quant.paper_account.events import (
    PAPER_ACCOUNT_GENESIS_CHAIN_DIGEST,
    SUPPORTED_PAPER_ACCOUNT_EVENT_TYPES,
    PaperAccountEvent,
    _AccountCreatedDetails,
    _CashMovementPostedDetails,
    _LifecycleChangedDetails,
    _PortfolioReviewEvidenceLinkedDetails,
    _event_digest_payload,
)
from el_psy_quant.paper_account.identity import (
    MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    MAX_PAPER_ACCOUNT_ID_LENGTH,
    PaperAccountIdentity,
)
from el_psy_quant.paper_account.references import (
    APPROVED_PORTFOLIO_REVIEW_REFERENCE_SCHEMA_VERSION,
    ApprovedPortfolioReviewReference,
)


def _validate_money(value: object, field_name: str) -> PaperMoney:
    if type(value) is not PaperMoney:
        raise ValueError(f"{field_name} must be PaperMoney")
    try:
        rebuilt = PaperMoney.parse(value.canonical)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{field_name} is not canonical PaperMoney") from exc
    if rebuilt != value or rebuilt.decimal_value != value.decimal_value:
        raise ValueError(f"{field_name} is not canonical PaperMoney")
    return value


def _require_normalized_timestamp(value: object, field_name: str) -> None:
    normalized = normalize_utc_datetime(value, field_name=field_name)
    if value.utcoffset() != timedelta(0) or value.isoformat() != (
        normalized.isoformat()
    ):
        raise ValueError(f"{field_name} must be normalized to UTC")


def _validate_reference(reference: object) -> ApprovedPortfolioReviewReference:
    if type(reference) is not ApprovedPortfolioReviewReference:
        raise ValueError("event evidence reference type is invalid")
    payload = reference.to_dict()
    expected_keys = {
        "schema_version",
        "review_id",
        "source_id",
        "source_digest",
        "analysis_digest",
        "decision_id",
        "decision_digest",
        "outcome",
    }
    if set(payload) != expected_keys:
        raise ValueError("event evidence reference payload is invalid")
    if (
        payload["schema_version"]
        != APPROVED_PORTFOLIO_REVIEW_REFERENCE_SCHEMA_VERSION
        or payload["outcome"] != "approved"
    ):
        raise ValueError("event evidence reference meaning is invalid")
    for field_name in ("review_id", "source_id", "decision_id"):
        value = payload[field_name]
        if (
            not isinstance(value, str)
            or not value
            or value != value.strip()
            or len(value) > 512
        ):
            raise ValueError(
                f"event evidence reference {field_name} is invalid"
            )
    for field_name in (
        "source_digest",
        "analysis_digest",
        "decision_digest",
    ):
        validate_digest(payload[field_name], field_name)
    return reference


def _validate_event_header(
    event: PaperAccountEvent,
    *,
    sequence_number: int,
    account_id: str | None,
    previous_chain_digest: str,
) -> None:
    if type(event) is not PaperAccountEvent:
        raise ValueError("history contains an invalid event")
    normalize_bounded_string(
        event.event_id,
        field_name="event_id",
        maximum_length=512,
    )
    normalized_account = normalize_bounded_string(
        event.account_id,
        field_name="account_id",
        maximum_length=MAX_PAPER_ACCOUNT_ID_LENGTH,
    )
    if normalized_account != event.account_id:
        raise ValueError("event account_id is not normalized")
    if account_id is not None and event.account_id != account_id:
        raise ValueError("event account_id does not match account history")
    if event.event_type not in SUPPORTED_PAPER_ACCOUNT_EVENT_TYPES:
        raise ValueError("history contains an unsupported event type")
    if type(event.sequence_number) is not int or event.sequence_number <= 0:
        raise ValueError(
            "event sequence_number must be an exact positive integer"
        )
    if type(event.account_version) is not int or event.account_version <= 0:
        raise ValueError(
            "event account_version must be an exact positive integer"
        )
    if (
        event.sequence_number != sequence_number
        or event.account_version != sequence_number
    ):
        raise ValueError("event sequence and version must be contiguous")
    expected_version = None if sequence_number == 1 else sequence_number - 1
    if sequence_number == 1:
        if event.expected_account_version is not None:
            raise ValueError(
                "creation expected_account_version must be None"
            )
    elif (
        type(event.expected_account_version) is not int
        or event.expected_account_version <= 0
    ):
        raise ValueError(
            "event expected_account_version must be an exact positive integer"
        )
    if event.expected_account_version != expected_version:
        raise ValueError("event expected version does not match prior version")
    if event.previous_chain_digest != previous_chain_digest:
        raise ValueError("event previous chain digest does not match")
    validate_digest(event.command_digest, "command_digest")
    validate_digest(event.previous_chain_digest, "previous_chain_digest")
    validate_digest(event.event_digest, "event_digest")
    validate_digest(event.chain_digest, "chain_digest")
    for value, field_name, maximum_length in (
        (
            event.command_idempotency_key,
            "command_idempotency_key",
            MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
        ),
        (event.actor, "actor", MAX_PAPER_ACCOUNT_ACTOR_LENGTH),
    ):
        if normalize_bounded_string(
            value,
            field_name=field_name,
            maximum_length=maximum_length,
        ) != value:
            raise ValueError(f"event {field_name} is not normalized")
    if event.reason is not None and (
        normalize_bounded_string(
            event.reason,
            field_name="reason",
            maximum_length=MAX_PAPER_ACCOUNT_COMMAND_REASON_LENGTH,
        )
        != event.reason
    ):
        raise ValueError("event reason is not normalized")
    _require_normalized_timestamp(
        event.recorded_timestamp_utc,
        "recorded_timestamp_utc",
    )
    if event.effective_timestamp_utc is not None:
        _require_normalized_timestamp(
            event.effective_timestamp_utc,
            "effective_timestamp_utc",
        )


def _validate_entry(
    entry: PaperCashLedgerEntry,
    *,
    event: PaperAccountEvent,
    base_currency: str,
) -> None:
    if type(entry) is not PaperCashLedgerEntry:
        raise ValueError("history contains an invalid cash entry")
    if entry.account_id != event.account_id or entry.event_id != event.event_id:
        raise ValueError("cash entry identity does not match its event")
    if type(entry.entry_index) is not int or entry.entry_index != 0:
        raise ValueError("cash entry_index must be the exact integer zero")
    if entry.currency != base_currency:
        raise ValueError("cash entry currency does not match account currency")
    normalize_bounded_string(
        entry.cash_entry_id,
        field_name="cash_entry_id",
        maximum_length=512,
    )
    _validate_money(entry.signed_amount, "signed_amount")
    validate_digest(entry.entry_digest, "entry_digest")
    expected_payload = {
        "schema_version": PAPER_CASH_LEDGER_ENTRY_SCHEMA_VERSION,
        "cash_entry_id": entry.cash_entry_id,
        "account_id": entry.account_id,
        "event_id": entry.event_id,
        "entry_index": entry.entry_index,
        "movement_type": entry.movement_type,
        "currency": entry.currency,
        "signed_amount": entry.signed_amount.to_json_value(),
    }
    if canonical_digest(expected_payload) != entry.entry_digest:
        raise ValueError("cash entry digest does not match its payload")


def _verify_creation_command(event: PaperAccountEvent) -> _AccountCreatedDetails:
    if type(event.details) is not _AccountCreatedDetails:
        raise ValueError("account_created event details are invalid")
    if event.reason is not None or event.effective_timestamp_utc is not None:
        raise ValueError("account_created event contains invalid metadata")
    identity = event.details.account_identity
    if type(identity) is not PaperAccountIdentity:
        raise ValueError("account_created identity is invalid")
    try:
        rebuilt_identity = PaperAccountIdentity(
            account_id=identity.account_id,
            display_name=identity.display_name,
            base_currency=identity.base_currency,
            created_by=identity.created_by,
            created_timestamp=identity.created_timestamp,
        )
    except ValueError as exc:
        raise ValueError("account_created identity is invalid") from exc
    if rebuilt_identity != identity or identity.account_id != event.account_id:
        raise ValueError("account_created identity does not match event")
    if event.actor != identity.created_by:
        raise ValueError("creation actor does not match identity")
    if event.recorded_timestamp_utc != identity.created_timestamp:
        raise ValueError("creation timestamp does not match identity")
    initial_cash = _validate_money(event.details.initial_cash, "initial_cash")
    command = CreatePaperAccountCommand(
        account_identity=identity,
        initial_cash=initial_cash,
        command_idempotency_key=event.command_idempotency_key,
        actor=event.actor,
    )
    if command.command_digest != event.command_digest:
        raise ValueError("creation command digest does not match event meaning")
    return event.details


def _verify_cash_command(
    event: PaperAccountEvent,
) -> tuple[_CashMovementPostedDetails, PostPaperCashMovementCommand]:
    if type(event.details) is not _CashMovementPostedDetails:
        raise ValueError("cash_movement_posted event details are invalid")
    if event.reason is None or event.expected_account_version is None:
        raise ValueError("cash movement event metadata is incomplete")
    requested = _validate_money(
        event.details.requested_amount,
        "requested_amount",
    )
    try:
        command = PostPaperCashMovementCommand(
            account_id=event.account_id,
            expected_account_version=event.expected_account_version,
            command_idempotency_key=event.command_idempotency_key,
            actor=event.actor,
            reason=event.reason,
            movement_type=event.details.movement_type,
            requested_amount=requested,
            effective_timestamp_utc=event.effective_timestamp_utc,
        )
    except ValueError as exc:
        raise ValueError("cash movement event meaning is invalid") from exc
    if command.command_digest != event.command_digest:
        raise ValueError("cash command digest does not match event meaning")
    return event.details, command


def _verify_evidence_command(
    event: PaperAccountEvent,
) -> ApprovedPortfolioReviewReference:
    if type(event.details) is not _PortfolioReviewEvidenceLinkedDetails:
        raise ValueError("evidence-link event details are invalid")
    if (
        event.reason is None
        or event.expected_account_version is None
        or event.effective_timestamp_utc is not None
    ):
        raise ValueError("evidence-link event metadata is invalid")
    reference = _validate_reference(event.details.approved_portfolio_review)
    command = LinkApprovedPortfolioReviewCommand(
        account_id=event.account_id,
        expected_account_version=event.expected_account_version,
        command_idempotency_key=event.command_idempotency_key,
        actor=event.actor,
        reason=event.reason,
        approved_portfolio_review=reference,
    )
    if command.command_digest != event.command_digest:
        raise ValueError("evidence command digest does not match event meaning")
    return reference


def _verify_lifecycle_command(
    event: PaperAccountEvent,
    current_status: str,
) -> str:
    if type(event.details) is not _LifecycleChangedDetails:
        raise ValueError("lifecycle event details are invalid")
    if (
        event.reason is None
        or event.expected_account_version is None
        or event.effective_timestamp_utc is not None
    ):
        raise ValueError("lifecycle event metadata is invalid")
    if event.details.source_status != current_status:
        raise ValueError("lifecycle source status does not match replay state")
    mapping = {
        "account_frozen": (
            "frozen",
            FreezePaperAccountCommand,
        ),
        "account_reactivated": (
            "active",
            ReactivatePaperAccountCommand,
        ),
        "account_closed": (
            "closed",
            ClosePaperAccountCommand,
        ),
    }
    if event.event_type not in mapping:
        raise ValueError("event type is not a lifecycle event")
    target_status, command_type = mapping[event.event_type]
    if event.details.target_status != target_status:
        raise ValueError("lifecycle target does not match event type")
    allowed = {
        ("active", "frozen"),
        ("frozen", "active"),
        ("active", "closed"),
        ("frozen", "closed"),
    }
    if (current_status, target_status) not in allowed:
        raise ValueError("invalid lifecycle transition in account history")
    command = command_type(
        account_id=event.account_id,
        expected_account_version=event.expected_account_version,
        command_idempotency_key=event.command_idempotency_key,
        actor=event.actor,
        reason=event.reason,
    )
    if command.command_digest != event.command_digest:
        raise ValueError("lifecycle command digest does not match event meaning")
    return target_status


def replay_paper_account_cash_ledger(
    bundles: Iterable[PaperAccountEventBundle],
) -> PaperAccountCashState:
    """Rebuild exact cash-only state and reject every inconsistent history."""
    history = tuple(bundles)
    if not history:
        raise ValueError("paper account history must not be empty")

    account_identity: PaperAccountIdentity | None = None
    lifecycle_status = "active"
    cash_balance = PaperMoney.parse("0")
    references: tuple[ApprovedPortfolioReviewReference, ...] = ()
    previous_chain_digest = PAPER_ACCOUNT_GENESIS_CHAIN_DIGEST
    seen_event_ids: set[str] = set()
    seen_entry_ids: set[str] = set()
    seen_decision_ids: set[str] = set()
    rebuilt_state: PaperAccountCashState | None = None

    for sequence_number, bundle in enumerate(history, start=1):
        if type(bundle) is not PaperAccountEventBundle:
            raise ValueError("history contains an invalid event bundle")
        event = bundle.event
        _validate_event_header(
            event,
            sequence_number=sequence_number,
            account_id=(
                account_identity.account_id
                if account_identity is not None
                else None
            ),
            previous_chain_digest=previous_chain_digest,
        )
        if event.event_id in seen_event_ids:
            raise ValueError("event IDs must be unique")
        seen_event_ids.add(event.event_id)
        if lifecycle_status == "closed":
            raise ValueError("no event may follow a closed account")

        entries = bundle.cash_entries
        if not isinstance(entries, tuple):
            raise ValueError("cash entries must use immutable tuple ordering")
        if sequence_number == 1:
            if event.event_type != "account_created":
                raise ValueError("the first event must be account_created")
            if len(entries) != 1:
                raise ValueError("account creation requires one cash entry")
            details = _verify_creation_command(event)
            account_identity = details.account_identity
            entry = entries[0]
            _validate_entry(
                entry,
                event=event,
                base_currency=account_identity.base_currency,
            )
            if (
                entry.movement_type != "initial_cash"
                or entry.signed_amount != details.initial_cash
                or entry.signed_amount.decimal_value < 0
            ):
                raise ValueError("initial cash entry meaning is invalid")
            cash_balance = details.initial_cash
        else:
            if event.event_type == "account_created":
                raise ValueError("account_created may appear only once")
            if account_identity is None:
                raise ValueError("account identity was not established")
            if event.event_type == "cash_movement_posted":
                if lifecycle_status != "active":
                    raise ValueError(
                        "cash movements require an active account"
                    )
                if len(entries) != 1:
                    raise ValueError("cash movement requires one cash entry")
                details, command = _verify_cash_command(event)
                entry = entries[0]
                _validate_entry(
                    entry,
                    event=event,
                    base_currency=account_identity.base_currency,
                )
                expected_signed = _signed_cash_movement(command)
                if (
                    entry.movement_type != details.movement_type
                    or entry.signed_amount != expected_signed
                ):
                    raise ValueError("cash entry movement meaning is invalid")
                cash_balance = money_from_decimal(
                    cash_balance.decimal_value
                    + entry.signed_amount.decimal_value
                )
                if cash_balance.decimal_value < 0:
                    raise ValueError(
                        "cash became negative during ledger replay"
                    )
            elif event.event_type == "portfolio_review_evidence_linked":
                if entries:
                    raise ValueError(
                        "evidence-link events cannot contain cash entries"
                    )
                if lifecycle_status != "active":
                    raise ValueError(
                        "evidence links require an active account"
                    )
                reference = _verify_evidence_command(event)
                if reference.decision_id in seen_decision_ids:
                    raise ValueError(
                        "evidence decision IDs must not be duplicated"
                    )
                seen_decision_ids.add(reference.decision_id)
                references = (*references, reference)
            else:
                if entries:
                    raise ValueError(
                        "lifecycle events cannot contain cash entries"
                    )
                target_status = _verify_lifecycle_command(
                    event,
                    lifecycle_status,
                )
                if target_status == "closed" and (
                    cash_balance.decimal_value != 0
                ):
                    raise ValueError(
                        "closed account event requires zero replayed cash"
                    )
                lifecycle_status = target_status

        for entry in entries:
            if entry.cash_entry_id in seen_entry_ids:
                raise ValueError("cash entry IDs must be unique")
            seen_entry_ids.add(entry.cash_entry_id)
        if canonical_digest(_event_digest_payload(event, entries)) != (
            event.event_digest
        ):
            raise ValueError("event digest does not match event and postings")
        expected_chain = hashlib.sha256(
            (previous_chain_digest + event.event_digest).encode("ascii")
        ).hexdigest()
        if expected_chain != event.chain_digest:
            raise ValueError("event chain digest does not match")

        if account_identity is None:
            raise ValueError("account identity was not established")
        rebuilt_state = _create_state(
            account_identity=account_identity,
            lifecycle_status=lifecycle_status,  # type: ignore[arg-type]
            cash_balance=cash_balance,
            approved_portfolio_reviews=references,
            head_version=sequence_number,
            head_event_id=event.event_id,
            head_chain_digest=event.chain_digest,
        )
        try:
            _validate_state(bundle.resulting_state)
        except ValueError as exc:
            raise ValueError(
                f"bundle resulting state is invalid: {exc}"
            ) from exc
        if bundle.resulting_state != rebuilt_state:
            raise ValueError(
                "bundle resulting state does not match immutable records"
            )
        previous_chain_digest = event.chain_digest

    if rebuilt_state is None:
        raise ValueError("paper account history must not be empty")
    return rebuilt_state
