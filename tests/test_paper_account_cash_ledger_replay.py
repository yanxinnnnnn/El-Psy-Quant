import copy
import json
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import pytest

from el_psy_quant.paper_account import (
    PAPER_ACCOUNT_GENESIS_CHAIN_DIGEST,
    ApprovedPortfolioReviewReference,
    ClosePaperAccountCommand,
    FreezePaperAccountCommand,
    LinkApprovedPortfolioReviewCommand,
    PaperAccountCashState,
    PaperAccountCloseEligibility,
    PaperAccountEvent,
    PaperAccountEventBundle,
    PaperAccountIdentity,
    PaperCashLedgerEntry,
    PaperMoney,
    PostPaperCashMovementCommand,
    ReactivatePaperAccountCommand,
    apply_approved_portfolio_review_link,
    apply_paper_account_lifecycle_command,
    apply_paper_cash_movement,
    create_approved_portfolio_review_reference,
    create_paper_account_command,
    create_paper_account_event_bundle,
    replay_paper_account_cash_ledger,
)
from el_psy_quant.portfolio_review import (
    create_portfolio_review_analysis_artifact,
    create_portfolio_review_baseline_scenario,
    create_portfolio_review_component,
    create_portfolio_review_decision_artifact,
    create_portfolio_review_evidence_reference,
    create_portfolio_review_proposed_scenario,
    create_portfolio_review_scenario_pair,
    create_portfolio_review_source,
)

CREATED = datetime(2026, 7, 23, 10, tzinfo=timezone.utc)


def _identity(
    *,
    account_id: str = "account-001",
    created_by: str = "founder",
) -> PaperAccountIdentity:
    return PaperAccountIdentity(
        account_id=account_id,
        display_name="Founder Account",
        base_currency="USD",
        created_by=created_by,
        created_timestamp=CREATED,
    )


def _approved_reference(
    *,
    decision_id: str = "decision-001",
    rationale: str = "Founder governance decision",
) -> ApprovedPortfolioReviewReference:
    components = tuple(
        create_portfolio_review_component(
            component_id=f"component-{index}",
            strategy_id=f"strategy-{index}",
            evidence_references=(
                create_portfolio_review_evidence_reference(
                    reference_type="research_run",
                    reference_id=f"run-{index}",
                ),
            ),
            symbols=(f"SYN-{index}",),
        )
        for index in (1, 2)
    )
    source = create_portfolio_review_source(
        source_id="source-001",
        components=components,
        aligned_returns=pd.DataFrame(
            {
                "component-1": (0.01, -0.02, 0.03),
                "component-2": (0.02, 0.01, -0.01),
            },
            index=pd.date_range("2026-07-01", periods=3, freq="D"),
        ),
        evaluation_frequency="daily",
        periods_per_year=252.0,
        created_by="source-actor",
        created_timestamp="2026-07-19T12:00:00Z",
    )
    baseline = create_portfolio_review_baseline_scenario(
        scenario_id="baseline-001",
        source=source,
        weights={"component-1": 1.0, "component-2": 0.0},
        rationale="Explicit baseline",
    )
    proposed = create_portfolio_review_proposed_scenario(
        scenario_id="proposed-001",
        source=source,
        weights={"component-1": 0.6, "component-2": 0.4},
        proposed_component_id="component-2",
        rationale="Explicit proposal",
    )
    analysis = create_portfolio_review_analysis_artifact(
        review_id="review-001",
        source=source,
        scenario_pair=create_portfolio_review_scenario_pair(
            source=source,
            baseline=baseline,
            proposed=proposed,
        ),
        created_by="analysis-actor",
        created_timestamp="2026-07-20T12:00:00Z",
    )
    decision = create_portfolio_review_decision_artifact(
        decision_id=decision_id,
        analysis=analysis,
        outcome="approved",
        rationale=rationale,
        reviewed_by="founder",
        reviewed_timestamp="2026-07-21T12:00:00Z",
        notes=("Not account authority",),
        warnings=("No execution authority",),
    )
    return create_approved_portfolio_review_reference(decision)


def _creation(
    *,
    initial_cash: str = "100",
    actor: str = "founder",
    identity: PaperAccountIdentity | None = None,
) -> PaperAccountEventBundle:
    command = create_paper_account_command(
        account_identity=identity or _identity(),
        initial_cash=PaperMoney.parse(initial_cash),
        command_idempotency_key="create-key",
        actor=actor,
    )
    return create_paper_account_event_bundle(
        command,
        event_id="event-001",
        cash_entry_id="cash-001",
        recorded_timestamp_utc=CREATED,
    )


def _cash(
    state: PaperAccountCashState,
    movement_type: str,
    amount: str,
    version: int,
) -> PaperAccountEventBundle:
    command = PostPaperCashMovementCommand(
        account_id=state.account_identity.account_id,
        expected_account_version=state.head_version,
        command_idempotency_key=f"cash-key-{version}",
        actor="founder",
        reason=f"Explicit {movement_type}",
        movement_type=movement_type,  # type: ignore[arg-type]
        requested_amount=PaperMoney.parse(amount),
        effective_timestamp_utc=datetime(
            2020,
            1,
            version,
            tzinfo=timezone.utc,
        ),
    )
    return apply_paper_cash_movement(
        state,
        command,
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


def _mixed_history() -> tuple[PaperAccountEventBundle, ...]:
    bundles = [_creation()]
    deposit = _cash(bundles[-1].resulting_state, "deposit", "20", 2)
    bundles.append(deposit)
    fee = _cash(bundles[-1].resulting_state, "fee", "5", 3)
    bundles.append(fee)
    reference = _approved_reference()
    link = apply_approved_portfolio_review_link(
        bundles[-1].resulting_state,
        LinkApprovedPortfolioReviewCommand(
            account_id="account-001",
            expected_account_version=3,
            command_idempotency_key="link-key",
            actor="founder",
            reason="Governance provenance only",
            approved_portfolio_review=reference,
        ),
        event_id="event-004",
        recorded_timestamp_utc=datetime(
            2026,
            7,
            23,
            10,
            4,
            tzinfo=timezone.utc,
        ),
    )
    bundles.append(link)
    frozen = apply_paper_account_lifecycle_command(
        bundles[-1].resulting_state,
        FreezePaperAccountCommand(
            account_id="account-001",
            expected_account_version=4,
            command_idempotency_key="freeze-key",
            actor="founder",
            reason="Founder pause",
        ),
        event_id="event-005",
        recorded_timestamp_utc=datetime(
            2026,
            7,
            23,
            10,
            5,
            tzinfo=timezone.utc,
        ),
    )
    bundles.append(frozen)
    active = apply_paper_account_lifecycle_command(
        bundles[-1].resulting_state,
        ReactivatePaperAccountCommand(
            account_id="account-001",
            expected_account_version=5,
            command_idempotency_key="reactivate-key",
            actor="founder",
            reason="Founder resumes",
        ),
        event_id="event-006",
        recorded_timestamp_utc=datetime(
            2026,
            7,
            23,
            10,
            6,
            tzinfo=timezone.utc,
        ),
    )
    bundles.append(active)
    withdrawal = _cash(
        bundles[-1].resulting_state,
        "withdrawal",
        "115",
        7,
    )
    bundles.append(withdrawal)
    closed = apply_paper_account_lifecycle_command(
        bundles[-1].resulting_state,
        ClosePaperAccountCommand(
            account_id="account-001",
            expected_account_version=7,
            command_idempotency_key="close-key",
            actor="founder",
            reason="Founder closes empty account",
        ),
        event_id="event-008",
        recorded_timestamp_utc=datetime(
            2026,
            7,
            23,
            10,
            8,
            tzinfo=timezone.utc,
        ),
        close_eligibility=PaperAccountCloseEligibility(True, True, True),
    )
    bundles.append(closed)
    return tuple(bundles)


@pytest.mark.parametrize("initial_cash", ("0", "100.125"))
def test_creation_builds_exact_genesis_event_entry_and_cash_state(
    initial_cash: str,
) -> None:
    bundle = _creation(initial_cash=initial_cash)

    assert bundle.event.sequence_number == 1
    assert bundle.event.account_version == 1
    assert bundle.event.expected_account_version is None
    assert bundle.event.event_type == "account_created"
    assert bundle.event.previous_chain_digest == (
        PAPER_ACCOUNT_GENESIS_CHAIN_DIGEST
    )
    assert len(bundle.cash_entries) == 1
    assert bundle.cash_entry is bundle.cash_entries[0]
    assert bundle.cash_entry.movement_type == "initial_cash"
    assert bundle.cash_entry.entry_index == 0
    assert bundle.cash_entry.signed_amount == PaperMoney.parse(initial_cash)
    assert bundle.resulting_state.lifecycle_status == "active"
    assert bundle.resulting_state.cash_balance == PaperMoney.parse(initial_cash)
    assert bundle.resulting_state.available_cash == PaperMoney.parse(initial_cash)
    assert bundle.resulting_state.approved_portfolio_reviews == ()
    assert {
        "positions",
        "allocation",
        "cost_basis",
        "orders",
        "fills",
    }.isdisjoint(bundle.to_dict()["resulting_state"])
    assert json.loads(json.dumps(bundle.to_dict(), allow_nan=False)) == (
        bundle.to_dict()
    )


def test_creation_enforces_actor_timestamp_and_command_digest() -> None:
    with pytest.raises(ValueError, match="actor must match"):
        _creation(actor="other")

    command = create_paper_account_command(
        account_identity=_identity(),
        initial_cash=PaperMoney.parse("0"),
        command_idempotency_key="create-key",
        actor="founder",
    )
    with pytest.raises(ValueError, match="timestamp must match"):
        create_paper_account_event_bundle(
            command,
            event_id="event-001",
            cash_entry_id="cash-001",
            recorded_timestamp_utc=datetime(
                2026,
                7,
                23,
                11,
                tzinfo=timezone.utc,
            ),
        )
    object.__setattr__(command, "command_digest", "0" * 64)
    with pytest.raises(ValueError, match="command digest"):
        create_paper_account_event_bundle(
            command,
            event_id="event-001",
            cash_entry_id="cash-001",
            recorded_timestamp_utc=CREATED,
        )


@pytest.mark.parametrize(
    ("movement_type", "amount", "expected"),
    (
        ("deposit", "10", "110"),
        ("withdrawal", "10", "90"),
        ("manual_adjustment", "1.25", "101.25"),
        ("manual_adjustment", "-1.25", "98.75"),
        ("fee", "1", "99"),
        ("commission", "2", "98"),
        ("tax", "3", "97"),
    ),
)
def test_cash_application_posts_exact_signed_amount_and_balance(
    movement_type: str,
    amount: str,
    expected: str,
) -> None:
    created = _creation()
    bundle = _cash(created.resulting_state, movement_type, amount, 2)

    expected_signed = amount
    if movement_type in {"withdrawal", "fee", "commission", "tax"}:
        expected_signed = f"-{amount}"
    assert bundle.event.sequence_number == 2
    assert bundle.event.account_version == 2
    assert bundle.event.expected_account_version == 1
    assert bundle.event.previous_chain_digest == created.event.chain_digest
    assert bundle.cash_entry is not None
    assert bundle.cash_entry.signed_amount == PaperMoney.parse(expected_signed)
    assert bundle.resulting_state.cash_balance == PaperMoney.parse(expected)
    assert bundle.resulting_state.available_cash == PaperMoney.parse(expected)


def test_cash_application_rejects_negative_frozen_closed_and_conflicts() -> None:
    created = _creation(initial_cash="10")
    with pytest.raises(ValueError, match="negative"):
        _cash(created.resulting_state, "withdrawal", "10.01", 2)

    wrong_account = PostPaperCashMovementCommand(
        account_id="other-account",
        expected_account_version=1,
        command_idempotency_key="key",
        actor="founder",
        reason="reason",
        movement_type="deposit",
        requested_amount=PaperMoney.parse("1"),
    )
    with pytest.raises(ValueError, match="account_id"):
        apply_paper_cash_movement(
            created.resulting_state,
            wrong_account,
            event_id="event-002",
            cash_entry_id="cash-002",
            recorded_timestamp_utc=CREATED,
        )
    stale = PostPaperCashMovementCommand(
        account_id="account-001",
        expected_account_version=2,
        command_idempotency_key="key",
        actor="founder",
        reason="reason",
        movement_type="deposit",
        requested_amount=PaperMoney.parse("1"),
    )
    with pytest.raises(ValueError, match="expected_account_version"):
        apply_paper_cash_movement(
            created.resulting_state,
            stale,
            event_id="event-002",
            cash_entry_id="cash-002",
            recorded_timestamp_utc=CREATED,
        )

    frozen = apply_paper_account_lifecycle_command(
        created.resulting_state,
        FreezePaperAccountCommand(
            account_id="account-001",
            expected_account_version=1,
            command_idempotency_key="freeze",
            actor="founder",
            reason="pause",
        ),
        event_id="event-002",
        recorded_timestamp_utc=CREATED,
    )
    with pytest.raises(ValueError, match="active"):
        _cash(frozen.resulting_state, "deposit", "1", 3)


def test_lifecycle_and_evidence_events_have_no_cash_authority() -> None:
    created = _creation(initial_cash="0")
    reference = _approved_reference()
    linked = apply_approved_portfolio_review_link(
        created.resulting_state,
        LinkApprovedPortfolioReviewCommand(
            account_id="account-001",
            expected_account_version=1,
            command_idempotency_key="link",
            actor="founder",
            reason="Approved governance provenance",
            approved_portfolio_review=reference,
        ),
        event_id="event-002",
        recorded_timestamp_utc=CREATED,
    )
    assert linked.cash_entries == ()
    assert linked.resulting_state.cash_balance == PaperMoney.parse("0")
    assert linked.resulting_state.approved_portfolio_reviews == (reference,)

    frozen = apply_paper_account_lifecycle_command(
        linked.resulting_state,
        FreezePaperAccountCommand(
            account_id="account-001",
            expected_account_version=2,
            command_idempotency_key="freeze",
            actor="founder",
            reason="pause",
        ),
        event_id="event-003",
        recorded_timestamp_utc=CREATED,
    )
    assert frozen.cash_entries == ()
    assert frozen.resulting_state.lifecycle_status == "frozen"

    reactivated = apply_paper_account_lifecycle_command(
        frozen.resulting_state,
        ReactivatePaperAccountCommand(
            account_id="account-001",
            expected_account_version=3,
            command_idempotency_key="reactivate",
            actor="founder",
            reason="resume",
        ),
        event_id="event-004",
        recorded_timestamp_utc=CREATED,
    )
    assert reactivated.resulting_state.lifecycle_status == "active"
    closed = apply_paper_account_lifecycle_command(
        reactivated.resulting_state,
        ClosePaperAccountCommand(
            account_id="account-001",
            expected_account_version=4,
            command_idempotency_key="close",
            actor="founder",
            reason="close empty account",
        ),
        event_id="event-005",
        recorded_timestamp_utc=CREATED,
        close_eligibility=PaperAccountCloseEligibility(True, True, True),
    )
    assert closed.resulting_state.lifecycle_status == "closed"
    with pytest.raises(ValueError):
        apply_paper_account_lifecycle_command(
            closed.resulting_state,
            ReactivatePaperAccountCommand(
                account_id="account-001",
                expected_account_version=5,
                command_idempotency_key="reopen",
                actor="founder",
                reason="not allowed",
            ),
            event_id="event-006",
            recorded_timestamp_utc=CREATED,
        )


def test_evidence_link_rejects_duplicate_conflicting_and_inactive_links() -> None:
    created = _creation()
    reference = _approved_reference()
    linked = apply_approved_portfolio_review_link(
        created.resulting_state,
        LinkApprovedPortfolioReviewCommand(
            account_id="account-001",
            expected_account_version=1,
            command_idempotency_key="link",
            actor="founder",
            reason="provenance",
            approved_portfolio_review=reference,
        ),
        event_id="event-002",
        recorded_timestamp_utc=CREATED,
    )
    for duplicate in (
        reference,
        _approved_reference(rationale="Conflicting decision payload"),
    ):
        with pytest.raises(ValueError, match="already linked"):
            apply_approved_portfolio_review_link(
                linked.resulting_state,
                LinkApprovedPortfolioReviewCommand(
                    account_id="account-001",
                    expected_account_version=2,
                    command_idempotency_key="second-link",
                    actor="founder",
                    reason="duplicate",
                    approved_portfolio_review=duplicate,
                ),
                event_id="event-003",
                recorded_timestamp_utc=CREATED,
            )

    frozen = apply_paper_account_lifecycle_command(
        created.resulting_state,
        FreezePaperAccountCommand(
            account_id="account-001",
            expected_account_version=1,
            command_idempotency_key="freeze",
            actor="founder",
            reason="pause",
        ),
        event_id="event-002",
        recorded_timestamp_utc=CREATED,
    )
    with pytest.raises(ValueError, match="active"):
        apply_approved_portfolio_review_link(
            frozen.resulting_state,
            LinkApprovedPortfolioReviewCommand(
                account_id="account-001",
                expected_account_version=2,
                command_idempotency_key="link",
                actor="founder",
                reason="provenance",
                approved_portfolio_review=reference,
            ),
            event_id="event-003",
            recorded_timestamp_utc=CREATED,
        )


def test_close_requires_zero_cash_and_all_explicit_eligibility_facts() -> None:
    created = _creation()
    command = ClosePaperAccountCommand(
        account_id="account-001",
        expected_account_version=1,
        command_idempotency_key="close",
        actor="founder",
        reason="close",
    )
    with pytest.raises(ValueError, match="cash"):
        apply_paper_account_lifecycle_command(
            created.resulting_state,
            command,
            event_id="event-002",
            recorded_timestamp_utc=CREATED,
            close_eligibility=PaperAccountCloseEligibility(True, True, True),
        )

    empty = _creation(initial_cash="0")
    with pytest.raises(ValueError, match="closing requires"):
        apply_paper_account_lifecycle_command(
            empty.resulting_state,
            command,
            event_id="event-002",
            recorded_timestamp_utc=CREATED,
            close_eligibility=PaperAccountCloseEligibility(True, False, True),
        )


def test_mixed_history_replays_exactly_and_repeatedly() -> None:
    history = _mixed_history()
    first = replay_paper_account_cash_ledger(history)
    second = replay_paper_account_cash_ledger(history)

    assert first == second == history[-1].resulting_state
    assert first.lifecycle_status == "closed"
    assert first.cash_balance == PaperMoney.parse("0")
    assert first.available_cash == PaperMoney.parse("0")
    assert first.head_version == 8
    assert len(first.approved_portfolio_reviews) == 1
    assert json.loads(json.dumps(first.to_dict(), allow_nan=False)) == (
        first.to_dict()
    )


@pytest.mark.parametrize(
    ("bundle_index", "target", "field_name", "replacement"),
    (
        (1, "event", "sequence_number", 99),
        (1, "event", "account_version", 99),
        (1, "event", "account_id", "other-account"),
        (1, "event", "command_digest", "0" * 64),
        (1, "event", "event_digest", "0" * 64),
        (1, "event", "previous_chain_digest", "0" * 64),
        (1, "event", "chain_digest", "0" * 64),
        (1, "entry", "event_id", "other-event"),
        (1, "entry", "entry_index", 1),
        (1, "entry", "entry_digest", "0" * 64),
        (1, "entry", "signed_amount", PaperMoney.parse("-20")),
    ),
)
def test_replay_rejects_event_entry_digest_identity_and_value_tampering(
    bundle_index: int,
    target: str,
    field_name: str,
    replacement: Any,
) -> None:
    history = copy.deepcopy(_mixed_history())
    bundle = history[bundle_index]
    tamper_target = bundle.event if target == "event" else bundle.cash_entry
    assert tamper_target is not None
    object.__setattr__(tamper_target, field_name, replacement)

    with pytest.raises(ValueError):
        replay_paper_account_cash_ledger(history)


def test_replay_rejects_cardinality_order_creation_state_and_closed_violations() -> None:
    history = copy.deepcopy(_mixed_history())
    object.__setattr__(history[1], "cash_entries", ())
    with pytest.raises(ValueError, match="one cash entry"):
        replay_paper_account_cash_ledger(history)

    history = _mixed_history()
    with pytest.raises(ValueError):
        replay_paper_account_cash_ledger((history[1], history[0]))
    with pytest.raises(ValueError):
        replay_paper_account_cash_ledger((history[0], history[0]))
    with pytest.raises(ValueError, match="empty"):
        replay_paper_account_cash_ledger(())

    tampered_state_history = copy.deepcopy(_mixed_history())
    object.__setattr__(
        tampered_state_history[1].resulting_state,
        "cash_balance",
        PaperMoney.parse("999"),
    )
    with pytest.raises(ValueError, match="resulting state"):
        replay_paper_account_cash_ledger(tampered_state_history)

    empty = _creation(initial_cash="0")
    closed = apply_paper_account_lifecycle_command(
        empty.resulting_state,
        ClosePaperAccountCommand(
            account_id="account-001",
            expected_account_version=1,
            command_idempotency_key="close",
            actor="founder",
            reason="close",
        ),
        event_id="event-002",
        recorded_timestamp_utc=CREATED,
        close_eligibility=PaperAccountCloseEligibility(True, True, True),
    )
    frozen_from_old_head = apply_paper_account_lifecycle_command(
        empty.resulting_state,
        FreezePaperAccountCommand(
            account_id="account-001",
            expected_account_version=1,
            command_idempotency_key="freeze",
            actor="founder",
            reason="pause",
        ),
        event_id="event-003",
        recorded_timestamp_utc=CREATED,
    )
    with pytest.raises(ValueError):
        replay_paper_account_cash_ledger(
            (empty, closed, frozen_from_old_head)
        )


def test_public_authority_records_are_immutable_and_not_directly_constructible() -> None:
    bundle = _creation()
    with pytest.raises(FrozenInstanceError):
        bundle.event.event_id = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        PaperAccountEvent()  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        PaperCashLedgerEntry()  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        PaperAccountCashState()  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        PaperAccountEventBundle()  # type: ignore[call-arg]
