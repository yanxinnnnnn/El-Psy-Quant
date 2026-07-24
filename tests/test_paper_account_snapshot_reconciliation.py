import copy
import json
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal, localcontext

import pytest

from el_psy_quant.paper_account import (
    ApprovedPortfolioReviewReference,
    ClosePaperAccountCommand,
    CreatePaperAccountSnapshotCommand,
    FreezePaperAccountCommand,
    LinkApprovedPortfolioReviewCommand,
    PaperAccountCloseEligibility,
    PaperAccountIdentity,
    PaperAccountPositionProjection,
    PaperAccountProjection,
    PaperAccountReconciliation,
    PaperAccountSnapshot,
    PaperMoney,
    PaperQuantity,
    PostPaperCashMovementCommand,
    ReconcilePaperAccountProjectionCommand,
    apply_approved_portfolio_review_link,
    apply_paper_account_lifecycle_command,
    apply_paper_cash_movement,
    apply_paper_position_adjustment,
    create_paper_account_command,
    create_paper_account_event_bundle,
    create_paper_account_snapshot,
    create_paper_account_snapshot_command,
    create_post_paper_position_adjustment_command,
    create_reconcile_paper_account_projection_command,
    rebuild_paper_account_projection,
    reconcile_paper_account_projection,
    replay_paper_account_ledger,
    verify_paper_account_projection,
)
from el_psy_quant.paper_account._shared import canonical_digest
from el_psy_quant.paper_account.projection import (
    _projection_payload_without_digest,
)
from el_psy_quant.paper_account.reconciliation import (
    _reconciliation_payload_without_digest,
)
from el_psy_quant.paper_account.snapshot import (
    _snapshot_payload_without_digest,
)

CREATED = datetime(2026, 7, 24, 8, tzinfo=timezone.utc)


def _identity(account_id: str = "account-183") -> PaperAccountIdentity:
    return PaperAccountIdentity(
        account_id=account_id,
        display_name="Sprint 183 Account",
        base_currency="USD",
        created_by="founder",
        created_timestamp=CREATED,
    )


def _creation(initial_cash: str = "100", account_id: str = "account-183"):
    return create_paper_account_event_bundle(
        create_paper_account_command(
            account_identity=_identity(account_id),
            initial_cash=PaperMoney.parse(initial_cash),
            command_idempotency_key=f"create-{account_id}",
            actor="founder",
        ),
        event_id=f"event-{account_id}-001",
        cash_entry_id=f"cash-{account_id}-001",
        recorded_timestamp_utc=CREATED,
    )


def _approved_reference() -> ApprovedPortfolioReviewReference:
    reference = object.__new__(ApprovedPortfolioReviewReference)
    object.__setattr__(reference, "review_id", "review-183")
    object.__setattr__(reference, "source_id", "source-183")
    object.__setattr__(reference, "source_digest", "1" * 64)
    object.__setattr__(reference, "analysis_digest", "2" * 64)
    object.__setattr__(reference, "decision_id", "decision-183")
    object.__setattr__(reference, "decision_digest", "3" * 64)
    object.__setattr__(reference, "outcome", "approved")
    return reference


def _active_mixed_history():
    history = [_creation()]
    state = replay_paper_account_ledger(history)
    deposit = apply_paper_cash_movement(
        state.to_cash_state(),
        PostPaperCashMovementCommand(
            account_id="account-183",
            expected_account_version=1,
            command_idempotency_key="deposit-183",
            actor="founder",
            reason="Explicit funding fact",
            movement_type="deposit",
            requested_amount=PaperMoney.parse("25.5"),
        ),
        event_id="event-183-002",
        cash_entry_id="cash-183-002",
        recorded_timestamp_utc=CREATED + timedelta(minutes=2),
    )
    history.append(deposit)
    state = replay_paper_account_ledger(history)
    link = apply_approved_portfolio_review_link(
        state.to_cash_state(),
        LinkApprovedPortfolioReviewCommand(
            account_id="account-183",
            expected_account_version=2,
            command_idempotency_key="link-183",
            actor="founder",
            reason="Governance provenance only",
            approved_portfolio_review=_approved_reference(),
        ),
        event_id="event-183-003",
        recorded_timestamp_utc=CREATED + timedelta(minutes=3),
    )
    history.append(link)
    state = replay_paper_account_ledger(history)
    for version, symbol, quantity, cost in (
        (4, "MSFT", "2", "20"),
        (5, "AAPL", "3", "10"),
    ):
        bundle = apply_paper_position_adjustment(
            state,
            create_post_paper_position_adjustment_command(
                account_id="account-183",
                expected_account_version=state.head_version,
                command_idempotency_key=f"position-{version}",
                actor="founder",
                reason="Explicit position fact",
                symbol=symbol,
                adjustment_category="opening_balance",
                signed_quantity_delta=PaperQuantity.parse(quantity),
                signed_cost_basis_delta=PaperMoney.parse(cost),
            ),
            event_id=f"event-183-{version:03d}",
            position_entry_id=f"position-183-{version:03d}",
            recorded_timestamp_utc=CREATED + timedelta(minutes=version),
        )
        history.append(bundle)
        state = bundle.resulting_state
    return tuple(history)


def _lifecycle_histories():
    active = (_creation("0", "account-life"),)
    state = replay_paper_account_ledger(active)
    frozen_bundle = apply_paper_account_lifecycle_command(
        state.to_cash_state(),
        FreezePaperAccountCommand(
            account_id="account-life",
            expected_account_version=1,
            command_idempotency_key="freeze-life",
            actor="founder",
            reason="Explicit pause",
        ),
        event_id="event-life-002",
        recorded_timestamp_utc=CREATED + timedelta(minutes=2),
    )
    frozen = (*active, frozen_bundle)
    state = replay_paper_account_ledger(frozen)
    closed_bundle = apply_paper_account_lifecycle_command(
        state.to_cash_state(),
        ClosePaperAccountCommand(
            account_id="account-life",
            expected_account_version=2,
            command_idempotency_key="close-life",
            actor="founder",
            reason="Close empty account",
        ),
        event_id="event-life-003",
        recorded_timestamp_utc=CREATED + timedelta(minutes=3),
        close_eligibility=PaperAccountCloseEligibility(True, True, True),
    )
    return active, frozen, (*frozen, closed_bundle)


def _snapshot_command(history):
    projection = rebuild_paper_account_projection(history)
    return create_paper_account_snapshot_command(
        account_id=projection.account_id,
        expected_account_version=projection.source_account_version,
        expected_head_event_id=projection.source_event_id,
        expected_head_chain_digest=projection.source_chain_digest,
        operation_idempotency_key="snapshot-operation-183",
        actor="founder",
        reason="Capture exact derived evidence",
    )


def _reconciliation_command(history):
    projection = rebuild_paper_account_projection(history)
    return create_reconcile_paper_account_projection_command(
        account_id=projection.account_id,
        expected_account_version=projection.source_account_version,
        expected_head_event_id=projection.source_event_id,
        expected_head_chain_digest=projection.source_chain_digest,
        operation_idempotency_key="reconciliation-operation-183",
        actor="founder",
        reason="Compare candidate without repair",
    )


def _refresh_projection_digest(projection: PaperAccountProjection) -> None:
    object.__setattr__(
        projection,
        "projection_digest",
        canonical_digest(_projection_payload_without_digest(projection)),
    )


def test_evidence_operation_commands_are_canonical_sensitive_and_pure() -> None:
    history = _active_mixed_history()
    projection = rebuild_paper_account_projection(history)
    snapshot = create_paper_account_snapshot_command(
        account_id=" account-183 ",
        expected_account_version=projection.source_account_version,
        expected_head_event_id=f" {projection.source_event_id} ",
        expected_head_chain_digest=projection.source_chain_digest,
        operation_idempotency_key=" snapshot-key ",
        actor=" founder ",
        reason=" exact evidence ",
    )
    reconciliation = create_reconcile_paper_account_projection_command(
        account_id="account-183",
        expected_account_version=projection.source_account_version,
        expected_head_event_id=projection.source_event_id,
        expected_head_chain_digest=projection.source_chain_digest,
        operation_idempotency_key="snapshot-key",
        actor="founder",
        reason="exact evidence",
    )

    assert snapshot.account_id == "account-183"
    assert snapshot.to_dict()["reason"] == "exact evidence"
    assert snapshot.command_digest != reconciliation.command_digest
    assert snapshot == _snapshot_command(history).__class__(
        account_id="account-183",
        expected_account_version=projection.source_account_version,
        expected_head_event_id=projection.source_event_id,
        expected_head_chain_digest=projection.source_chain_digest,
        operation_idempotency_key="snapshot-key",
        actor="founder",
        reason="exact evidence",
    )
    assert tuple(history) == history


@pytest.mark.parametrize("version", (True, 1.0, "1", 0, -1))
@pytest.mark.parametrize(
    "command_type",
    (CreatePaperAccountSnapshotCommand, ReconcilePaperAccountProjectionCommand),
)
def test_evidence_commands_reject_version_aliases_and_invalid_anchors(
    version: object,
    command_type,
) -> None:
    with pytest.raises(ValueError, match="exact positive integer"):
        command_type(
            account_id="account-183",
            expected_account_version=version,
            expected_head_event_id="event-183",
            expected_head_chain_digest="a" * 64,
            operation_idempotency_key="operation-key",
            actor="founder",
            reason="explicit reason",
        )
    with pytest.raises(ValueError):
        command_type(
            account_id="account-183",
            expected_account_version=1,
            expected_head_event_id=" ",
            expected_head_chain_digest="A" * 64,
            operation_idempotency_key=" ",
            actor=" ",
            reason=" ",
        )


def test_projection_rebuild_is_deterministic_complete_and_prefix_aware() -> None:
    history = _active_mixed_history()
    before = [bundle.to_dict() for bundle in history]
    first = rebuild_paper_account_projection(history)
    with localcontext() as context:
        context.prec = 5
        second = rebuild_paper_account_projection(iter(history))
    prefix = rebuild_paper_account_projection(history[:3])

    assert first == second
    assert first.projection_digest == second.projection_digest
    assert first.cash_balance.canonical == "125.5"
    assert first.available_cash == first.cash_balance
    assert [item.symbol for item in first.positions] == ["AAPL", "MSFT"]
    assert first.positions[0].quantity.canonical == "3"
    assert first.positions[0].aggregate_cost_basis.canonical == "10"
    assert first.positions[0].average_unit_cost == "3.33333333"
    assert first.positions[0].average_unit_cost_is_rounded is True
    assert [item.decision_id for item in first.approved_portfolio_reviews] == [
        "decision-183"
    ]
    assert first.source_account_version == 5
    assert prefix.source_account_version == 3
    assert prefix.positions == ()
    exported = first.to_dict()
    json.dumps(exported, allow_nan=False)
    assert not {
        "timestamp",
        "path",
        "market_value",
        "equity",
        "pnl",
        "orders",
        "fills",
    }.intersection(exported)
    assert [bundle.to_dict() for bundle in history] == before


@pytest.mark.parametrize("index", (0, 1, 2))
def test_projection_rebuild_supports_creation_frozen_and_closed(index: int) -> None:
    histories = _lifecycle_histories()
    expected = ("active", "frozen", "closed")
    projection = rebuild_paper_account_projection(histories[index])
    assert projection.lifecycle_status == expected[index]
    assert projection.source_account_version == index + 1


def test_projection_verification_is_current_or_ordered_reconciliation_only() -> None:
    history = _active_mixed_history()
    current = rebuild_paper_account_projection(history)
    stale = rebuild_paper_account_projection(history[:1])
    current_result = verify_paper_account_projection(history, current)
    stale_before = stale.to_dict()
    stale_result = verify_paper_account_projection(history, stale)

    assert current_result.status == "current"
    assert current_result.mismatch_codes == ()
    assert stale_result.status == "reconciliation_required"
    assert stale_result.mismatch_codes == (
        "source_account_version_mismatch",
        "source_event_id_mismatch",
        "source_chain_digest_mismatch",
        "cash_balance_mismatch",
        "available_cash_mismatch",
        "positions_mismatch",
        "evidence_references_mismatch",
    )
    assert stale.to_dict() == stale_before


@pytest.mark.parametrize(
    ("field_name", "replacement", "expected_code"),
    (
        ("source_account_version", 99, "source_account_version_mismatch"),
        ("source_event_id", "other-event", "source_event_id_mismatch"),
        ("source_chain_digest", "4" * 64, "source_chain_digest_mismatch"),
        ("lifecycle_status", "frozen", "lifecycle_status_mismatch"),
        ("positions", (), "positions_mismatch"),
        (
            "approved_portfolio_reviews",
            (),
            "evidence_references_mismatch",
        ),
    ),
)
def test_projection_verification_reports_each_independent_mismatch_code(
    field_name: str,
    replacement: object,
    expected_code: str,
) -> None:
    history = _active_mixed_history()
    candidate = copy.deepcopy(rebuild_paper_account_projection(history))
    object.__setattr__(candidate, field_name, replacement)
    _refresh_projection_digest(candidate)
    result = verify_paper_account_projection(history, candidate)
    assert result.mismatch_codes == (expected_code,)


def test_projection_verification_reports_identity_and_both_cash_codes() -> None:
    history = _active_mixed_history()
    identity_candidate = copy.deepcopy(rebuild_paper_account_projection(history))
    object.__setattr__(
        identity_candidate,
        "account_identity",
        PaperAccountIdentity(
            account_id="account-183",
            display_name="Changed label",
            base_currency="USD",
            created_by="founder",
            created_timestamp=CREATED,
        ),
    )
    _refresh_projection_digest(identity_candidate)
    assert verify_paper_account_projection(
        history, identity_candidate
    ).mismatch_codes == ("identity_mismatch",)

    cash_candidate = copy.deepcopy(rebuild_paper_account_projection(history))
    object.__setattr__(cash_candidate, "cash_balance", PaperMoney.parse("999"))
    object.__setattr__(cash_candidate, "available_cash", PaperMoney.parse("999"))
    _refresh_projection_digest(cash_candidate)
    assert verify_paper_account_projection(
        history, cash_candidate
    ).mismatch_codes == (
        "cash_balance_mismatch",
        "available_cash_mismatch",
    )


def test_projection_verification_rejects_cross_account_and_tampering() -> None:
    history = _active_mixed_history()
    other = rebuild_paper_account_projection((_creation("1", "other-account"),))
    with pytest.raises(ValueError, match="different account"):
        verify_paper_account_projection(history, other)

    candidate = copy.deepcopy(rebuild_paper_account_projection(history))
    object.__setattr__(candidate, "source_account_version", True)
    _refresh_projection_digest(candidate)
    with pytest.raises(ValueError, match="exact positive integer"):
        verify_paper_account_projection(history, candidate)

    candidate = copy.deepcopy(rebuild_paper_account_projection(history))
    object.__setattr__(candidate, "positions", list(candidate.positions))
    with pytest.raises(ValueError, match="tuple ordering"):
        verify_paper_account_projection(history, candidate)

    candidate = copy.deepcopy(rebuild_paper_account_projection(history))
    object.__setattr__(candidate.positions[0], "average_unit_cost_is_rounded", 1)
    _refresh_projection_digest(candidate)
    with pytest.raises(ValueError, match="exact boolean"):
        verify_paper_account_projection(history, candidate)

    candidate = copy.deepcopy(rebuild_paper_account_projection(history))
    object.__setattr__(candidate, "projection_digest", "A" * 64)
    with pytest.raises(ValueError, match="lowercase"):
        verify_paper_account_projection(history, candidate)


def test_projection_rejects_unordered_duplicate_and_noncanonical_nested_values() -> None:
    history = _active_mixed_history()
    candidate = copy.deepcopy(rebuild_paper_account_projection(history))
    object.__setattr__(candidate, "positions", tuple(reversed(candidate.positions)))
    _refresh_projection_digest(candidate)
    with pytest.raises(ValueError, match="ordered"):
        verify_paper_account_projection(history, candidate)

    candidate = copy.deepcopy(rebuild_paper_account_projection(history))
    object.__setattr__(
        candidate,
        "positions",
        (candidate.positions[0], candidate.positions[0]),
    )
    _refresh_projection_digest(candidate)
    with pytest.raises(ValueError, match="unique"):
        verify_paper_account_projection(history, candidate)

    candidate = copy.deepcopy(rebuild_paper_account_projection(history))
    money = candidate.positions[0].aggregate_cost_basis
    object.__setattr__(money, "_canonical", "10.0")
    _refresh_projection_digest(candidate)
    with pytest.raises(ValueError, match="canonical"):
        verify_paper_account_projection(history, candidate)

    candidate = copy.deepcopy(rebuild_paper_account_projection(history))
    object.__setattr__(
        candidate,
        "approved_portfolio_reviews",
        (
            candidate.approved_portfolio_reviews[0],
            candidate.approved_portfolio_reviews[0],
        ),
    )
    _refresh_projection_digest(candidate)
    with pytest.raises(ValueError, match="unique"):
        verify_paper_account_projection(history, candidate)


@pytest.mark.parametrize("index", (0, 1, 2))
def test_snapshot_creation_supports_all_lifecycle_states_without_mutation(
    index: int,
) -> None:
    history = _lifecycle_histories()[index]
    before = [bundle.to_dict() for bundle in history]
    state_before = replay_paper_account_ledger(history)
    snapshot = create_paper_account_snapshot(
        history,
        _snapshot_command(history),
        snapshot_id=f"snapshot-{index}",
        recorded_timestamp_utc=datetime(
            2026, 7, 24, 16, tzinfo=timezone(timedelta(hours=8))
        ),
    )
    state_after = replay_paper_account_ledger(history)

    assert snapshot.projection.lifecycle_status == ("active", "frozen", "closed")[
        index
    ]
    assert snapshot.recorded_timestamp_utc.isoformat() == "2026-07-24T08:00:00+00:00"
    assert snapshot.account_version == state_before.head_version
    assert state_after == state_before
    assert [bundle.to_dict() for bundle in history] == before
    assert create_paper_account_snapshot(
        history,
        _snapshot_command(history),
        snapshot_id=f"snapshot-{index}",
        recorded_timestamp_utc=datetime(
            2026, 7, 24, 16, tzinfo=timezone(timedelta(hours=8))
        ),
    ) == snapshot


def test_snapshot_rejects_anchor_command_digest_and_nested_tampering() -> None:
    history = _active_mixed_history()
    command = _snapshot_command(history)
    object.__setattr__(command, "expected_account_version", True)
    payload = command.to_dict()
    payload.pop("command_digest")
    object.__setattr__(command, "command_digest", canonical_digest(payload))
    with pytest.raises(ValueError, match="operation command"):
        create_paper_account_snapshot(
            history,
            command,
            snapshot_id="snapshot-tampered-command",
            recorded_timestamp_utc=CREATED,
        )

    command = _snapshot_command(history)
    object.__setattr__(command, "expected_head_event_id", "other-event")
    payload = command.to_dict()
    payload.pop("command_digest")
    object.__setattr__(command, "command_digest", canonical_digest(payload))
    with pytest.raises(ValueError, match="anchors"):
        create_paper_account_snapshot(
            history,
            command,
            snapshot_id="snapshot-bad-anchor",
            recorded_timestamp_utc=CREATED,
        )

    snapshot = create_paper_account_snapshot(
        history,
        _snapshot_command(history),
        snapshot_id="snapshot-valid",
        recorded_timestamp_utc=CREATED,
    )
    object.__setattr__(snapshot, "account_version", True)
    object.__setattr__(
        snapshot,
        "snapshot_digest",
        canonical_digest(_snapshot_payload_without_digest(snapshot)),
    )
    with pytest.raises(ValueError, match="exact positive integer"):
        snapshot.to_dict()

    snapshot = create_paper_account_snapshot(
        history,
        _snapshot_command(history),
        snapshot_id="snapshot-nested-tamper",
        recorded_timestamp_utc=CREATED,
    )
    object.__setattr__(snapshot.projection, "projection_digest", "0" * 64)
    object.__setattr__(
        snapshot,
        "snapshot_digest",
        "1" * 64,
    )
    with pytest.raises(ValueError, match="projection digest"):
        snapshot.to_dict()


def test_reconciliation_records_matched_and_mismatched_without_repair() -> None:
    history = _active_mixed_history()
    current = rebuild_paper_account_projection(history)
    stale = rebuild_paper_account_projection(history[:1])
    stale_before = stale.to_dict()
    command = _reconciliation_command(history)
    matched = reconcile_paper_account_projection(
        history,
        current,
        command,
        reconciliation_id="reconciliation-matched",
        recorded_timestamp_utc=CREATED,
    )
    mismatched = reconcile_paper_account_projection(
        history,
        stale,
        command,
        reconciliation_id="reconciliation-mismatched",
        recorded_timestamp_utc=CREATED,
    )

    assert matched.outcome == "matched"
    assert matched.mismatch_codes == ()
    assert mismatched.outcome == "mismatched"
    assert mismatched.mismatch_codes == (
        "source_account_version_mismatch",
        "source_event_id_mismatch",
        "source_chain_digest_mismatch",
        "cash_balance_mismatch",
        "available_cash_mismatch",
        "positions_mismatch",
        "evidence_references_mismatch",
    )
    assert mismatched.authoritative_projection_digest == current.projection_digest
    assert mismatched.candidate_projection_digest == stale.projection_digest
    assert stale.to_dict() == stale_before


@pytest.mark.parametrize("index", (0, 1, 2))
def test_reconciliation_supports_active_frozen_and_closed(index: int) -> None:
    history = _lifecycle_histories()[index]
    candidate = rebuild_paper_account_projection(history)
    artifact = reconcile_paper_account_projection(
        history,
        candidate,
        _reconciliation_command(history),
        reconciliation_id=f"reconciliation-{index}",
        recorded_timestamp_utc=CREATED,
    )
    assert artifact.outcome == "matched"


def test_reconciliation_rejects_anchor_and_recomputed_scalar_tampering() -> None:
    history = _active_mixed_history()
    candidate = rebuild_paper_account_projection(history)
    command = _reconciliation_command(history)
    object.__setattr__(command, "expected_head_chain_digest", "9" * 64)
    payload = command.to_dict()
    payload.pop("command_digest")
    object.__setattr__(command, "command_digest", canonical_digest(payload))
    with pytest.raises(ValueError, match="anchors"):
        reconcile_paper_account_projection(
            history,
            candidate,
            command,
            reconciliation_id="reconciliation-bad-anchor",
            recorded_timestamp_utc=CREATED,
        )

    artifact = reconcile_paper_account_projection(
        history,
        candidate,
        _reconciliation_command(history),
        reconciliation_id="reconciliation-valid",
        recorded_timestamp_utc=CREATED,
    )
    object.__setattr__(artifact, "outcome", "mismatched")
    object.__setattr__(
        artifact,
        "reconciliation_digest",
        canonical_digest(_reconciliation_payload_without_digest(artifact)),
    )
    with pytest.raises(ValueError, match="disagree"):
        artifact.to_dict()

    artifact = reconcile_paper_account_projection(
        history,
        candidate,
        _reconciliation_command(history),
        reconciliation_id="reconciliation-anchor-tamper",
        recorded_timestamp_utc=CREATED,
    )
    object.__setattr__(artifact, "candidate_account_version", 1.0)
    object.__setattr__(artifact, "reconciliation_digest", "8" * 64)
    with pytest.raises(ValueError, match="exact positive integer"):
        artifact.to_dict()

    artifact = reconcile_paper_account_projection(
        history,
        candidate,
        _reconciliation_command(history),
        reconciliation_id="reconciliation-event-tamper",
        recorded_timestamp_utc=CREATED,
    )
    object.__setattr__(artifact, "candidate_event_id", " ")
    object.__setattr__(
        artifact,
        "reconciliation_digest",
        canonical_digest(_reconciliation_payload_without_digest(artifact)),
    )
    with pytest.raises(ValueError, match="candidate_event_id"):
        artifact.to_dict()


def test_derived_records_are_frozen_and_not_directly_constructible() -> None:
    for record_type in (
        PaperAccountPositionProjection,
        PaperAccountProjection,
        PaperAccountSnapshot,
        PaperAccountReconciliation,
    ):
        with pytest.raises(TypeError):
            record_type()  # type: ignore[call-arg]

    projection = rebuild_paper_account_projection(_active_mixed_history())
    with pytest.raises(FrozenInstanceError):
        projection.source_account_version = 99  # type: ignore[misc]


def test_sprint_181_and_182_digest_vectors_remain_stable() -> None:
    history = _active_mixed_history()
    before = [
        (
            bundle.event.event_digest,
            bundle.event.chain_digest,
            tuple(entry.entry_digest for entry in bundle.cash_entries),
            tuple(entry.entry_digest for entry in getattr(bundle, "position_entries", ())),
        )
        for bundle in history
    ]
    rebuild_paper_account_projection(history)
    create_paper_account_snapshot(
        history,
        _snapshot_command(history),
        snapshot_id="snapshot-regression",
        recorded_timestamp_utc=CREATED,
    )
    after = [
        (
            bundle.event.event_digest,
            bundle.event.chain_digest,
            tuple(entry.entry_digest for entry in bundle.cash_entries),
            tuple(entry.entry_digest for entry in getattr(bundle, "position_entries", ())),
        )
        for bundle in history
    ]
    assert after == before
    assert Decimal("1.0") == Decimal("1.00")
