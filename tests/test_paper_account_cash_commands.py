import hashlib
import json
from datetime import datetime, timedelta, timezone

import pytest

from el_psy_quant.paper_account import (
    PAPER_ACCOUNT_COMMAND_SCHEMA_VERSION,
    SUPPORTED_POST_PAPER_CASH_MOVEMENT_TYPES,
    PaperMoney,
    PostPaperCashMovementCommand,
    create_post_paper_cash_movement_command,
)


def _expected_digest(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@pytest.mark.parametrize(
    ("movement_type", "amount"),
    (
        ("deposit", "100"),
        ("withdrawal", "10.5"),
        ("manual_adjustment", "-0.25"),
        ("fee", "1"),
        ("commission", "2"),
        ("tax", "3"),
    ),
)
def test_cash_command_supports_exact_closed_movement_vocabulary(
    movement_type: str,
    amount: str,
) -> None:
    command = create_post_paper_cash_movement_command(
        account_id=" account-001 ",
        expected_account_version=2,
        command_idempotency_key=" cash-key ",
        actor=" founder ",
        reason=" explicit cash fact ",
        movement_type=movement_type,  # type: ignore[arg-type]
        requested_amount=PaperMoney.parse(amount),
    )

    assert SUPPORTED_POST_PAPER_CASH_MOVEMENT_TYPES == (
        "deposit",
        "withdrawal",
        "manual_adjustment",
        "fee",
        "commission",
        "tax",
    )
    payload = {
        "schema_version": PAPER_ACCOUNT_COMMAND_SCHEMA_VERSION,
        "command_type": "post_paper_cash_movement",
        "account_id": "account-001",
        "expected_account_version": 2,
        "command_idempotency_key": "cash-key",
        "actor": "founder",
        "reason": "explicit cash fact",
        "movement_type": movement_type,
        "requested_amount": amount,
        "effective_timestamp_utc": None,
    }
    assert command.to_dict() == {
        **payload,
        "command_digest": _expected_digest(payload),
    }
    assert json.loads(json.dumps(command.to_dict(), allow_nan=False)) == (
        command.to_dict()
    )


def test_cash_command_normalizes_effective_timestamp_to_utc() -> None:
    effective = datetime(
        2026,
        7,
        23,
        20,
        15,
        tzinfo=timezone(timedelta(hours=8)),
    )
    command = PostPaperCashMovementCommand(
        account_id="account-001",
        expected_account_version=3,
        command_idempotency_key="cash-key",
        actor="founder",
        reason="Founder-provided fact",
        movement_type="deposit",
        requested_amount=PaperMoney.parse("10"),
        effective_timestamp_utc=effective,
    )

    assert command.effective_timestamp_utc == datetime(
        2026,
        7,
        23,
        12,
        15,
        tzinfo=timezone.utc,
    )
    assert command.to_dict()["effective_timestamp_utc"] == (
        "2026-07-23T12:15:00+00:00"
    )


def test_cash_command_digest_is_stable_and_sensitive() -> None:
    values = {
        "account_id": "account-001",
        "expected_account_version": 3,
        "command_idempotency_key": "cash-key",
        "actor": "founder",
        "reason": "Explicit cash fact",
        "movement_type": "deposit",
        "requested_amount": PaperMoney.parse("10"),
        "effective_timestamp_utc": datetime(
            2026,
            7,
            23,
            tzinfo=timezone.utc,
        ),
    }
    first = PostPaperCashMovementCommand(**values)
    second = PostPaperCashMovementCommand(**values)
    variants = (
        PostPaperCashMovementCommand(**{**values, "account_id": "account-002"}),
        PostPaperCashMovementCommand(
            **{**values, "expected_account_version": 4}
        ),
        PostPaperCashMovementCommand(
            **{**values, "command_idempotency_key": "other-key"}
        ),
        PostPaperCashMovementCommand(**{**values, "actor": "other"}),
        PostPaperCashMovementCommand(**{**values, "reason": "Other reason"}),
        PostPaperCashMovementCommand(
            **{**values, "movement_type": "withdrawal"}
        ),
        PostPaperCashMovementCommand(
            **{**values, "requested_amount": PaperMoney.parse("11")}
        ),
        PostPaperCashMovementCommand(
            **{
                **values,
                "effective_timestamp_utc": datetime(
                    2026,
                    7,
                    24,
                    tzinfo=timezone.utc,
                ),
            }
        ),
    )

    assert first == second
    assert all(
        variant.command_digest != first.command_digest for variant in variants
    )
    assert len({variant.command_digest for variant in variants}) == len(variants)


@pytest.mark.parametrize(
    ("movement_type", "amount"),
    (
        ("deposit", "0"),
        ("deposit", "-1"),
        ("withdrawal", "0"),
        ("withdrawal", "-1"),
        ("fee", "0"),
        ("commission", "-1"),
        ("tax", "0"),
        ("manual_adjustment", "0"),
    ),
)
def test_cash_command_enforces_exact_requested_amount_semantics(
    movement_type: str,
    amount: str,
) -> None:
    with pytest.raises(ValueError, match="requested_amount"):
        PostPaperCashMovementCommand(
            account_id="account-001",
            expected_account_version=1,
            command_idempotency_key="key",
            actor="founder",
            reason="reason",
            movement_type=movement_type,  # type: ignore[arg-type]
            requested_amount=PaperMoney.parse(amount),
        )


@pytest.mark.parametrize("movement_type", ("initial_cash", "interest", "dividend"))
def test_cash_command_rejects_initial_cash_and_unsupported_movements(
    movement_type: str,
) -> None:
    with pytest.raises(ValueError, match="movement_type"):
        PostPaperCashMovementCommand(
            account_id="account-001",
            expected_account_version=1,
            command_idempotency_key="key",
            actor="founder",
            reason="reason",
            movement_type=movement_type,  # type: ignore[arg-type]
            requested_amount=PaperMoney.parse("1"),
        )


@pytest.mark.parametrize("reason", ("", " ", None))
def test_cash_command_requires_reason(reason: object) -> None:
    with pytest.raises(ValueError, match="reason"):
        PostPaperCashMovementCommand(
            account_id="account-001",
            expected_account_version=1,
            command_idempotency_key="key",
            actor="founder",
            reason=reason,  # type: ignore[arg-type]
            movement_type="deposit",
            requested_amount=PaperMoney.parse("1"),
        )


def test_cash_command_rejects_naive_effective_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        PostPaperCashMovementCommand(
            account_id="account-001",
            expected_account_version=1,
            command_idempotency_key="key",
            actor="founder",
            reason="reason",
            movement_type="deposit",
            requested_amount=PaperMoney.parse("1"),
            effective_timestamp_utc=datetime(2026, 7, 23),
        )
