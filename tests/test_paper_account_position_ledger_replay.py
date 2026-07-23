import copy
import hashlib
import json
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal, Inexact, localcontext

import pytest

from el_psy_quant.paper_account import (
    ApprovedPortfolioReviewReference,
    ClosePaperAccountCommand,
    FreezePaperAccountCommand,
    LinkApprovedPortfolioReviewCommand,
    PaperAccountCloseEligibility,
    PaperAccountEvent,
    PaperAccountIdentity,
    PaperAccountLedgerEventBundle,
    PaperAccountLedgerState,
    PaperAccountPosition,
    PaperMoney,
    PaperPositionLedgerEntry,
    PaperQuantity,
    PostPaperCashMovementCommand,
    PostPaperPositionAdjustmentCommand,
    ReactivatePaperAccountCommand,
    apply_approved_portfolio_review_link,
    apply_paper_account_lifecycle_command,
    apply_paper_cash_movement,
    apply_paper_position_adjustment,
    create_paper_account_command,
    create_paper_account_event_bundle,
    create_post_paper_position_adjustment_command,
    replay_paper_account_ledger,
)
from el_psy_quant.paper_account.ledger_state import (
    _create_position,
    _derive_average_unit_cost,
    _validate_position,
)

CREATED = datetime(2026, 7, 23, 10, tzinfo=timezone.utc)


def _identity() -> PaperAccountIdentity:
    return PaperAccountIdentity(
        account_id="account-001",
        display_name="Founder Account",
        base_currency="USD",
        created_by="founder",
        created_timestamp=CREATED,
    )


def _creation(initial_cash: str = "100"):
    command = create_paper_account_command(
        account_identity=_identity(),
        initial_cash=PaperMoney.parse(initial_cash),
        command_idempotency_key="create-key",
        actor="founder",
    )
    return create_paper_account_event_bundle(
        command,
        event_id="event-001",
        cash_entry_id="cash-001",
        recorded_timestamp_utc=CREATED,
    )


def _position_command(
    state: PaperAccountLedgerState,
    *,
    symbol: str = "AAPL",
    quantity: str = "2",
    cost: str = "5",
    category: str = "manual_correction",
    version: int | None = None,
) -> PostPaperPositionAdjustmentCommand:
    expected = state.head_version if version is None else version
    return PostPaperPositionAdjustmentCommand(
        account_id=state.account_identity.account_id,
        expected_account_version=expected,
        command_idempotency_key=f"position-key-{expected}",
        actor="founder",
        reason="Explicit position ledger fact",
        symbol=symbol,
        adjustment_category=category,  # type: ignore[arg-type]
        signed_quantity_delta=PaperQuantity.parse(quantity),
        signed_cost_basis_delta=PaperMoney.parse(cost),
        effective_timestamp_utc=datetime(
            2020,
            1,
            1,
            tzinfo=timezone(timedelta(hours=8)),
        ),
    )


def _apply_position(
    state: PaperAccountLedgerState,
    *,
    symbol: str = "AAPL",
    quantity: str = "2",
    cost: str = "5",
    category: str = "manual_correction",
) -> PaperAccountLedgerEventBundle:
    version = state.head_version + 1
    return apply_paper_position_adjustment(
        state,
        _position_command(
            state,
            symbol=symbol,
            quantity=quantity,
            cost=cost,
            category=category,
        ),
        event_id=f"event-{version:03d}",
        position_entry_id=f"position-{version:03d}",
        recorded_timestamp_utc=datetime(
            2026,
            7,
            23,
            10,
            version,
            tzinfo=timezone.utc,
        ),
    )


def _approved_reference() -> ApprovedPortfolioReviewReference:
    reference = object.__new__(ApprovedPortfolioReviewReference)
    object.__setattr__(reference, "review_id", "review-001")
    object.__setattr__(reference, "source_id", "source-001")
    object.__setattr__(reference, "source_digest", "1" * 64)
    object.__setattr__(reference, "analysis_digest", "2" * 64)
    object.__setattr__(reference, "decision_id", "decision-001")
    object.__setattr__(reference, "decision_digest", "3" * 64)
    object.__setattr__(reference, "outcome", "approved")
    return reference


def _cash_bundle(
    state: PaperAccountLedgerState,
    *,
    movement_type: str,
    amount: str,
):
    version = state.head_version + 1
    return apply_paper_cash_movement(
        state.to_cash_state(),
        PostPaperCashMovementCommand(
            account_id="account-001",
            expected_account_version=state.head_version,
            command_idempotency_key=f"cash-key-{version}",
            actor="founder",
            reason=f"Explicit {movement_type}",
            movement_type=movement_type,  # type: ignore[arg-type]
            requested_amount=PaperMoney.parse(amount),
        ),
        event_id=f"event-{version:03d}",
        cash_entry_id=f"cash-{version:03d}",
        recorded_timestamp_utc=datetime(
            2026,
            7,
            23,
            10,
            version,
            tzinfo=timezone.utc,
        ),
    )


def _mixed_history():
    history = [_creation("100")]
    state = replay_paper_account_ledger(history)

    deposit = _cash_bundle(state, movement_type="deposit", amount="25")
    history.append(deposit)
    state = replay_paper_account_ledger(history)

    link = apply_approved_portfolio_review_link(
        state.to_cash_state(),
        LinkApprovedPortfolioReviewCommand(
            account_id="account-001",
            expected_account_version=state.head_version,
            command_idempotency_key="link-key",
            actor="founder",
            reason="Governance provenance only",
            approved_portfolio_review=_approved_reference(),
        ),
        event_id="event-003",
        recorded_timestamp_utc=datetime(
            2026, 7, 23, 10, 3, tzinfo=timezone.utc
        ),
    )
    history.append(link)
    state = replay_paper_account_ledger(history)

    for symbol, quantity, cost, category in (
        ("symbol_b", "4", "20", "opening_balance"),
        ("SYMBOL_A", "3", "10", "opening_balance"),
        ("symbol_a", "2", "5", "manual_correction"),
    ):
        position = _apply_position(
            state,
            symbol=symbol,
            quantity=quantity,
            cost=cost,
            category=category,
        )
        history.append(position)
        state = position.resulting_state

    fee = _cash_bundle(state, movement_type="fee", amount="5")
    history.append(fee)
    state = replay_paper_account_ledger(history)

    frozen = apply_paper_account_lifecycle_command(
        state.to_cash_state(),
        FreezePaperAccountCommand(
            account_id="account-001",
            expected_account_version=state.head_version,
            command_idempotency_key="freeze-key",
            actor="founder",
            reason="Founder pause",
        ),
        event_id="event-008",
        recorded_timestamp_utc=datetime(
            2026, 7, 23, 10, 8, tzinfo=timezone.utc
        ),
    )
    history.append(frozen)
    state = replay_paper_account_ledger(history)

    active = apply_paper_account_lifecycle_command(
        state.to_cash_state(),
        ReactivatePaperAccountCommand(
            account_id="account-001",
            expected_account_version=state.head_version,
            command_idempotency_key="reactivate-key",
            actor="founder",
            reason="Founder resumes",
        ),
        event_id="event-009",
        recorded_timestamp_utc=datetime(
            2026, 7, 23, 10, 9, tzinfo=timezone.utc
        ),
    )
    history.append(active)
    state = replay_paper_account_ledger(history)

    for symbol, quantity, cost in (
        ("SYMBOL_A", "-5", "-15"),
        ("SYMBOL_B", "-4", "-20"),
    ):
        position = _apply_position(
            state,
            symbol=symbol,
            quantity=quantity,
            cost=cost,
        )
        history.append(position)
        state = position.resulting_state

    withdrawal = _cash_bundle(
        state,
        movement_type="withdrawal",
        amount="120",
    )
    history.append(withdrawal)
    state = replay_paper_account_ledger(history)

    closed = apply_paper_account_lifecycle_command(
        state.to_cash_state(),
        ClosePaperAccountCommand(
            account_id="account-001",
            expected_account_version=state.head_version,
            command_idempotency_key="close-key",
            actor="founder",
            reason="Founder closes empty account",
        ),
        event_id="event-013",
        recorded_timestamp_utc=datetime(
            2026, 7, 23, 10, 13, tzinfo=timezone.utc
        ),
        close_eligibility=PaperAccountCloseEligibility(True, True, True),
    )
    history.append(closed)
    return tuple(history)


@pytest.mark.parametrize(
    "category",
    ("opening_balance", "manual_correction", "corporate_action", "other"),
)
def test_position_command_normalizes_symbol_and_covers_all_categories(
    category: str,
) -> None:
    command = create_post_paper_position_adjustment_command(
        account_id=" account-001 ",
        expected_account_version=2,
        command_idempotency_key=" position-key ",
        actor=" founder ",
        reason=" explicit fact ",
        symbol=" aapl ",
        adjustment_category=category,  # type: ignore[arg-type]
        signed_quantity_delta=PaperQuantity.parse("-1.25"),
        signed_cost_basis_delta=PaperMoney.parse("2.5"),
        effective_timestamp_utc=datetime(
            2026,
            7,
            23,
            18,
            tzinfo=timezone(timedelta(hours=8)),
        ),
    )

    assert command.symbol == "AAPL"
    assert command.adjustment_category == category
    assert command.signed_quantity_delta == PaperQuantity.parse("-1.25")
    assert command.signed_cost_basis_delta == PaperMoney.parse("2.5")
    assert command.effective_timestamp_utc == CREATED
    assert command.to_dict()["symbol"] == "AAPL"
    assert json.loads(json.dumps(command.to_dict())) == command.to_dict()

    changed = PostPaperPositionAdjustmentCommand(
        account_id="account-001",
        expected_account_version=2,
        command_idempotency_key="position-key",
        actor="founder",
        reason="explicit fact",
        symbol="MSFT",
        adjustment_category=category,  # type: ignore[arg-type]
        signed_quantity_delta=PaperQuantity.parse("-1.25"),
        signed_cost_basis_delta=PaperMoney.parse("2.5"),
        effective_timestamp_utc=CREATED,
    )
    assert changed.command_digest != command.command_digest


@pytest.mark.parametrize("version", (True, 1.0, 0, -1))
def test_position_command_rejects_invalid_exact_version(version: object) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        PostPaperPositionAdjustmentCommand(
            account_id="account-001",
            expected_account_version=version,  # type: ignore[arg-type]
            command_idempotency_key="key",
            actor="founder",
            reason="reason",
            symbol="AAPL",
            adjustment_category="other",
            signed_quantity_delta=PaperQuantity.parse("1"),
            signed_cost_basis_delta=PaperMoney.parse("0"),
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"reason": " "}, "reason"),
        ({"symbol": " "}, "symbol"),
        ({"adjustment_category": "trade"}, "adjustment_category"),
        (
            {
                "signed_quantity_delta": PaperQuantity.parse("0"),
                "signed_cost_basis_delta": PaperMoney.parse("0"),
            },
            "non-zero",
        ),
        ({"signed_quantity_delta": PaperMoney.parse("1")}, "PaperQuantity"),
        ({"signed_cost_basis_delta": PaperQuantity.parse("1")}, "PaperMoney"),
    ),
)
def test_position_command_rejects_invalid_fields(
    overrides: dict[str, object],
    message: str,
) -> None:
    values: dict[str, object] = {
        "account_id": "account-001",
        "expected_account_version": 1,
        "command_idempotency_key": "key",
        "actor": "founder",
        "reason": "reason",
        "symbol": "AAPL",
        "adjustment_category": "other",
        "signed_quantity_delta": PaperQuantity.parse("1"),
        "signed_cost_basis_delta": PaperMoney.parse("0"),
    }
    values.update(overrides)
    with pytest.raises(ValueError, match=message):
        PostPaperPositionAdjustmentCommand(**values)  # type: ignore[arg-type]


def test_position_application_builds_exact_entry_event_and_full_state() -> None:
    created = _creation()
    state = replay_paper_account_ledger((created,))
    bundle = _apply_position(
        state,
        symbol=" aapl ",
        quantity="3",
        cost="10",
        category="opening_balance",
    )

    assert bundle.event.event_type == "position_adjustment_posted"
    assert bundle.event.sequence_number == 2
    assert bundle.event.previous_chain_digest == state.head_chain_digest
    assert bundle.cash_entries == ()
    assert len(bundle.position_entries) == 1
    assert bundle.position_entry is bundle.position_entries[0]
    assert bundle.position_entry.entry_index == 0
    assert bundle.position_entry.symbol == "AAPL"
    assert bundle.position_entry.signed_quantity_delta == PaperQuantity.parse(
        "3"
    )
    assert bundle.position_entry.signed_cost_basis_delta == PaperMoney.parse(
        "10"
    )
    assert bundle.resulting_state.cash_balance == PaperMoney.parse("100")
    assert bundle.resulting_state.available_cash == PaperMoney.parse("100")
    assert len(bundle.resulting_state.positions) == 1
    position = bundle.resulting_state.positions[0]
    assert position.quantity == PaperQuantity.parse("3")
    assert position.aggregate_cost_basis == PaperMoney.parse("10")
    assert position.average_unit_cost == "3.33333333"
    assert position.average_unit_cost_is_rounded is True
    assert {
        "market_value",
        "equity",
        "pnl",
        "leverage",
        "exposure",
        "buying_power",
        "returns",
        "scenario_weights",
        "orders",
        "fills",
    }.isdisjoint(bundle.resulting_state.to_dict())
    assert json.loads(json.dumps(bundle.to_dict())) == bundle.to_dict()

    with pytest.raises(FrozenInstanceError):
        bundle.event.event_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        bundle.position_entry.symbol = "MSFT"  # type: ignore[misc]
    with pytest.raises(TypeError, match="trusted event factories"):
        PaperPositionLedgerEntry()  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="derived by domain functions"):
        PaperAccountPosition()  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="derived by domain functions"):
        PaperAccountLedgerState()  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="derived by domain functions"):
        PaperAccountLedgerEventBundle()  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="trusted command factories"):
        PaperAccountEvent()  # type: ignore[call-arg]


@pytest.mark.parametrize(
    ("quantity", "cost", "average", "rounded"),
    (
        ("2", "5", "2.5", False),
        ("3", "1", "0.33333333", True),
        ("2", "2.46913569", "1.23456784", True),
        ("4", "10", "2.5", False),
        ("2", "0", "0", False),
    ),
)
def test_average_unit_cost_is_deterministic_display_only(
    quantity: str,
    cost: str,
    average: str,
    rounded: bool,
) -> None:
    state = replay_paper_account_ledger((_creation(),))
    bundle = _apply_position(state, quantity=quantity, cost=cost)
    position = bundle.resulting_state.positions[0]

    assert position.average_unit_cost == average
    assert position.average_unit_cost_is_rounded is rounded
    assert replay_paper_account_ledger(
        (_creation(), bundle)
    ).positions[0].quantity == PaperQuantity.parse(quantity)
    assert replay_paper_account_ledger(
        (_creation(), bundle)
    ).positions[0].aggregate_cost_basis == PaperMoney.parse(cost)


def test_average_unit_cost_is_null_at_zero_and_ignores_ambient_context() -> None:
    assert _derive_average_unit_cost(
        quantity=PaperQuantity.parse("0"),
        aggregate_cost_basis=PaperMoney.parse("0"),
    ) == (None, False)

    with localcontext() as context:
        context.prec = 2
        context.traps[Inexact] = True
        state = replay_paper_account_ledger((_creation(),))
        bundle = _apply_position(state, quantity="3", cost="1")
    position = bundle.resulting_state.positions[0]
    assert position.average_unit_cost == "0.33333333"
    assert position.average_unit_cost_is_rounded is True


def test_quantity_only_cost_only_reductions_and_symbol_ordering() -> None:
    history = [_creation()]
    state = replay_paper_account_ledger(history)
    for symbol, quantity, cost in (
        ("MSFT", "2", "10"),
        ("AAPL", "3", "9"),
        ("AAPL", "-1", "0"),
        ("MSFT", "0", "2"),
    ):
        bundle = _apply_position(
            state,
            symbol=symbol,
            quantity=quantity,
            cost=cost,
        )
        history.append(bundle)
        state = bundle.resulting_state

    assert [position.symbol for position in state.positions] == ["AAPL", "MSFT"]
    assert state.positions[0].quantity == PaperQuantity.parse("2")
    assert state.positions[0].aggregate_cost_basis == PaperMoney.parse("9")
    assert state.positions[1].quantity == PaperQuantity.parse("2")
    assert state.positions[1].aggregate_cost_basis == PaperMoney.parse("12")
    assert state.cash_balance == PaperMoney.parse("100")
    assert replay_paper_account_ledger(history) == state


@pytest.mark.parametrize(
    ("opening_quantity", "opening_cost", "delta_quantity", "delta_cost", "error"),
    (
        ("2", "10", "-3", "0", "quantity negative"),
        ("2", "10", "0", "-11", "cost basis negative"),
        ("2", "10", "-2", "0", "zero position quantity"),
    ),
)
def test_position_application_rejects_long_only_invariant_violations(
    opening_quantity: str,
    opening_cost: str,
    delta_quantity: str,
    delta_cost: str,
    error: str,
) -> None:
    state = replay_paper_account_ledger((_creation(),))
    opened = _apply_position(
        state,
        quantity=opening_quantity,
        cost=opening_cost,
    )
    with pytest.raises(ValueError, match=error):
        _apply_position(
            opened.resulting_state,
            quantity=delta_quantity,
            cost=delta_cost,
        )


def test_position_application_rejects_frozen_closed_and_conflicting_heads() -> None:
    created = _creation("0")
    state = replay_paper_account_ledger((created,))
    frozen = apply_paper_account_lifecycle_command(
        state.to_cash_state(),
        FreezePaperAccountCommand(
            account_id="account-001",
            expected_account_version=1,
            command_idempotency_key="freeze",
            actor="founder",
            reason="pause",
        ),
        event_id="event-002",
        recorded_timestamp_utc=datetime(
            2026, 7, 23, 10, 2, tzinfo=timezone.utc
        ),
    )
    frozen_state = replay_paper_account_ledger((created, frozen))
    with pytest.raises(ValueError, match="active"):
        _apply_position(frozen_state)

    with pytest.raises(ValueError, match="expected_account_version"):
        apply_paper_position_adjustment(
            state,
            _position_command(state, version=2),
            event_id="event-003",
            position_entry_id="position-003",
            recorded_timestamp_utc=CREATED,
        )

    closed = apply_paper_account_lifecycle_command(
        frozen_state.to_cash_state(),
        ClosePaperAccountCommand(
            account_id="account-001",
            expected_account_version=2,
            command_idempotency_key="close",
            actor="founder",
            reason="close",
        ),
        event_id="event-003",
        recorded_timestamp_utc=datetime(
            2026, 7, 23, 10, 3, tzinfo=timezone.utc
        ),
        close_eligibility=PaperAccountCloseEligibility(True, True, True),
    )
    closed_state = replay_paper_account_ledger((created, frozen, closed))
    with pytest.raises(ValueError, match="active"):
        _apply_position(closed_state)


def test_position_application_rejects_tampered_command_value_contract() -> None:
    state = replay_paper_account_ledger((_creation(),))
    command = _position_command(state)
    object.__setattr__(
        command.signed_quantity_delta,
        "_decimal_value",
        PaperQuantity.parse("3").decimal_value,
    )
    payload = command.to_dict()
    payload.pop("command_digest")
    object.__setattr__(command, "command_digest", _canonical_digest(payload))

    with pytest.raises(ValueError, match="position command values"):
        apply_paper_position_adjustment(
            state,
            command,
            event_id="event-002",
            position_entry_id="position-002",
            recorded_timestamp_utc=CREATED,
        )


@pytest.mark.parametrize(
    ("quantity", "cost", "expected_flag", "alias"),
    (
        ("3", "10", True, 1),
        ("3", "10", True, 1.0),
        ("2", "5", False, 0),
        ("2", "5", False, 0.0),
    ),
)
def test_position_application_rejects_rounding_flag_numeric_aliases(
    quantity: str,
    cost: str,
    expected_flag: bool,
    alias: object,
) -> None:
    state = replay_paper_account_ledger((_creation(),))
    opened = _apply_position(state, quantity=quantity, cost=cost)
    position = opened.resulting_state.positions[0]
    assert position.average_unit_cost_is_rounded is expected_flag
    next_command = _position_command(
        opened.resulting_state,
        quantity="0",
        cost="1",
    )
    command_digest = next_command.command_digest
    posting_digests = _position_authority_digests(opened)

    object.__setattr__(
        position,
        "average_unit_cost_is_rounded",
        alias,
    )

    assert next_command.command_digest == command_digest
    assert _position_authority_digests(opened) == posting_digests
    with pytest.raises(ValueError, match="must be a boolean"):
        apply_paper_position_adjustment(
            opened.resulting_state,
            next_command,
            event_id="event-003",
            position_entry_id="position-003",
            recorded_timestamp_utc=CREATED,
        )
    assert next_command.command_digest == command_digest
    assert _position_authority_digests(opened) == posting_digests


def test_mixed_cash_position_evidence_lifecycle_history_replays_to_close() -> None:
    history = _mixed_history()
    first = replay_paper_account_ledger(history)
    second = replay_paper_account_ledger(history)

    assert first == second
    assert first.lifecycle_status == "closed"
    assert first.cash_balance == PaperMoney.parse("0")
    assert first.available_cash == PaperMoney.parse("0")
    assert first.positions == ()
    assert len(first.approved_portfolio_reviews) == 1
    assert first.head_version == 13
    assert first.head_event_id == "event-013"
    assert json.loads(json.dumps(first.to_dict())) == first.to_dict()


def test_sprint_181_event_digest_vector_remains_byte_for_byte_stable() -> None:
    bundle = _creation()

    assert bundle.event.event_digest == (
        "bf11c6c659f5a7eec34cb6660e3297702cc0921ccbc4814d029327e3c1432095"
    )
    assert bundle.event.chain_digest == (
        "1a841149f1caa335dbb00b86e19c52ebd3f49d51351c229473bb105aeadcacce"
    )


def _canonical_digest(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _position_authority_digests(
    bundle: PaperAccountLedgerEventBundle,
) -> tuple[str, str, str, str]:
    assert bundle.position_entry is not None
    return (
        bundle.event.command_digest,
        bundle.position_entry.entry_digest,
        bundle.event.event_digest,
        bundle.event.chain_digest,
    )


def _refresh_position_entry_digest(bundle: PaperAccountLedgerEventBundle) -> None:
    assert bundle.position_entry is not None
    object.__setattr__(
        bundle.position_entry,
        "entry_digest",
        _canonical_digest(bundle.position_entry._payload_without_digest()),
    )


def _refresh_position_event_digest(bundle: PaperAccountLedgerEventBundle) -> None:
    payload = {
        "event_header": bundle.event._header_without_result_digests(),
        "event_details": bundle.event.details.to_dict(),
        "cash_entries": [],
        "position_entries": [
            entry.to_dict() for entry in bundle.position_entries
        ],
    }
    event_digest = _canonical_digest(payload)
    object.__setattr__(bundle.event, "event_digest", event_digest)
    object.__setattr__(
        bundle.event,
        "chain_digest",
        hashlib.sha256(
            (
                bundle.event.previous_chain_digest + event_digest
            ).encode("ascii")
        ).hexdigest(),
    )


@pytest.mark.parametrize("tamper", ("index_bool", "index_float", "cardinality"))
def test_full_replay_rejects_position_index_and_cardinality_tampering(
    tamper: str,
) -> None:
    created = _creation()
    state = replay_paper_account_ledger((created,))
    position = _apply_position(state)
    if tamper == "index_bool":
        object.__setattr__(position.position_entry, "entry_index", False)
    elif tamper == "index_float":
        object.__setattr__(position.position_entry, "entry_index", 0.0)
    else:
        object.__setattr__(position, "position_entries", ())
    with pytest.raises(ValueError):
        replay_paper_account_ledger((created, position))


@pytest.mark.parametrize(
    ("quantity", "cost", "expected_flag", "alias"),
    (
        ("3", "10", True, 1),
        ("3", "10", True, 1.0),
        ("2", "5", False, 0),
        ("2", "5", False, 0.0),
    ),
)
def test_full_replay_rejects_rounding_flag_numeric_aliases_in_resulting_state(
    quantity: str,
    cost: str,
    expected_flag: bool,
    alias: object,
) -> None:
    created = _creation()
    state = replay_paper_account_ledger((created,))
    bundle = _apply_position(state, quantity=quantity, cost=cost)
    position = bundle.resulting_state.positions[0]
    assert position.average_unit_cost_is_rounded is expected_flag
    authority_digests = _position_authority_digests(bundle)

    object.__setattr__(
        position,
        "average_unit_cost_is_rounded",
        alias,
    )

    assert _position_authority_digests(bundle) == authority_digests
    with pytest.raises(ValueError, match="must be a boolean"):
        replay_paper_account_ledger((created, bundle))
    assert _position_authority_digests(bundle) == authority_digests


@pytest.mark.parametrize(
    "invalid_average",
    (
        Decimal("2.5"),
        2,
        2.5,
        " 2.5",
        "2.5 ",
        "2.50",
        "2.5e0",
        "2,5",
        "2.4",
        None,
    ),
)
def test_full_replay_rejects_invalid_average_unit_cost_scalars(
    invalid_average: object,
) -> None:
    created = _creation()
    state = replay_paper_account_ledger((created,))
    bundle = _apply_position(state, quantity="2", cost="5")
    authority_digests = _position_authority_digests(bundle)
    object.__setattr__(
        bundle.resulting_state.positions[0],
        "average_unit_cost",
        invalid_average,
    )

    assert _position_authority_digests(bundle) == authority_digests
    with pytest.raises(ValueError, match="average_unit_cost"):
        replay_paper_account_ledger((created, bundle))
    assert _position_authority_digests(bundle) == authority_digests


def test_zero_value_position_helper_requires_exact_display_scalars() -> None:
    zero_position = _create_position(
        symbol="AAPL",
        quantity=PaperQuantity.parse("0"),
        aggregate_cost_basis=PaperMoney.parse("0"),
    )
    assert zero_position.average_unit_cost is None
    assert zero_position.average_unit_cost_is_rounded is False

    object.__setattr__(zero_position, "average_unit_cost", "0")
    with pytest.raises(ValueError, match="must be None"):
        _validate_position(zero_position)

    zero_position = _create_position(
        symbol="AAPL",
        quantity=PaperQuantity.parse("0"),
        aggregate_cost_basis=PaperMoney.parse("0"),
    )
    object.__setattr__(zero_position, "average_unit_cost_is_rounded", 0)
    with pytest.raises(ValueError, match="must be a boolean"):
        _validate_position(zero_position)


def test_full_replay_rejects_recomputed_lower_entry_and_event_tampering() -> None:
    created = _creation()
    state = replay_paper_account_ledger((created,))
    position = copy.deepcopy(_apply_position(state))
    assert position.position_entry is not None
    object.__setattr__(
        position.position_entry,
        "signed_cost_basis_delta",
        PaperMoney.parse("6"),
    )
    _refresh_position_entry_digest(position)
    _refresh_position_event_digest(position)

    with pytest.raises(ValueError, match="meaning does not match"):
        replay_paper_account_ledger((created, position))


def test_full_replay_rejects_position_entry_ids_and_state_tampering() -> None:
    created = _creation()
    state = replay_paper_account_ledger((created,))
    first = _apply_position(state, symbol="AAPL")
    second = _apply_position(first.resulting_state, symbol="MSFT")
    assert first.position_entry is not None
    assert second.position_entry is not None
    object.__setattr__(
        second.position_entry,
        "position_entry_id",
        first.position_entry.position_entry_id,
    )
    _refresh_position_entry_digest(second)
    _refresh_position_event_digest(second)
    with pytest.raises(ValueError, match="IDs must be unique"):
        replay_paper_account_ledger((created, first, second))

    state_tampered = copy.deepcopy(first)
    object.__setattr__(
        state_tampered.resulting_state,
        "cash_balance",
        PaperMoney.parse("99"),
    )
    with pytest.raises(ValueError, match="does not match records"):
        replay_paper_account_ledger((created, state_tampered))


def test_full_replay_refuses_close_while_a_position_remains() -> None:
    created = _creation("0")
    state = replay_paper_account_ledger((created,))
    position = _apply_position(state, quantity="1", cost="1")
    dishonest_close = apply_paper_account_lifecycle_command(
        position.resulting_state.to_cash_state(),
        ClosePaperAccountCommand(
            account_id="account-001",
            expected_account_version=2,
            command_idempotency_key="close-key",
            actor="founder",
            reason="attempt close",
        ),
        event_id="event-003",
        recorded_timestamp_utc=datetime(
            2026, 7, 23, 10, 3, tzinfo=timezone.utc
        ),
        close_eligibility=PaperAccountCloseEligibility(True, True, True),
    )

    with pytest.raises(ValueError, match="no current positions"):
        replay_paper_account_ledger((created, position, dishonest_close))
