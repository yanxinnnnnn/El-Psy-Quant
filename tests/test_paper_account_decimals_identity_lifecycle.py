import json
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from el_psy_quant.paper_account import (
    MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    MAX_PAPER_ACCOUNT_DISPLAY_NAME_LENGTH,
    MAX_PAPER_ACCOUNT_ID_LENGTH,
    PAPER_ACCOUNT_CLOSE_ELIGIBILITY_SCHEMA_VERSION,
    PAPER_ACCOUNT_IDENTITY_SCHEMA_VERSION,
    PAPER_ACCOUNT_REFERENCE_SCHEMA_VERSION,
    PAPER_MONEY_SCHEMA_VERSION,
    PAPER_QUANTITY_SCHEMA_VERSION,
    SUPPORTED_PAPER_ACCOUNT_LIFECYCLE_STATUSES,
    PaperAccountCloseEligibility,
    PaperAccountIdentity,
    PaperAccountReference,
    PaperMoney,
    PaperQuantity,
    create_paper_account_identity,
    create_paper_account_reference,
    validate_paper_account_lifecycle_transition,
)


@pytest.mark.parametrize(
    "value",
    ("0", "12", "-12", "0.5", "-0.5", "12.345", "-999.12345678"),
)
def test_money_accepts_only_canonical_exact_values(value: str) -> None:
    money = PaperMoney.parse(value)

    assert money.decimal_value == Decimal(value)
    assert money.canonical == value
    assert money.to_json_value() == value
    assert money.to_dict() == {
        "schema_version": PAPER_MONEY_SCHEMA_VERSION,
        "value": value,
    }
    assert str(money) == value
    assert json.loads(json.dumps(money.to_dict(), allow_nan=False)) == (
        money.to_dict()
    )


def test_decimal_scale_and_magnitude_boundaries_are_exact() -> None:
    money = PaperMoney.parse("999999999999999999.12345678")
    quantity = PaperQuantity.parse("-999999999999999999.123456789012")

    assert money.decimal_value == Decimal("999999999999999999.12345678")
    assert quantity.decimal_value == Decimal(
        "-999999999999999999.123456789012"
    )
    assert quantity.to_dict() == {
        "schema_version": PAPER_QUANTITY_SCHEMA_VERSION,
        "value": "-999999999999999999.123456789012",
    }


@pytest.mark.parametrize(
    "invalid",
    (
        "+1",
        "01",
        "00.1",
        ".5",
        "1.",
        "1.0",
        "1.2300",
        "-0",
        "-0.0",
        "1e3",
        "1E3",
        "NaN",
        "Infinity",
        "1,000",
        " 1",
        "1 ",
        "0.123456789",
        "1000000000000000000",
    ),
)
def test_money_rejects_noncanonical_or_out_of_bounds_values(
    invalid: str,
) -> None:
    with pytest.raises(ValueError):
        PaperMoney.parse(invalid)


@pytest.mark.parametrize(
    "invalid",
    ("0.1234567890123", "1000000000000000000"),
)
def test_quantity_rejects_out_of_bounds_values(invalid: str) -> None:
    with pytest.raises(ValueError):
        PaperQuantity.parse(invalid)


@pytest.mark.parametrize("invalid", (1.0, True, Decimal("1"), None))
def test_decimal_public_parsing_rejects_non_string_values(invalid: object) -> None:
    with pytest.raises(ValueError, match="canonical decimal string"):
        PaperMoney.parse(invalid)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="canonical decimal string"):
        PaperQuantity.parse(invalid)  # type: ignore[arg-type]


def test_decimal_values_are_immutable_hashable_and_equality_stable() -> None:
    first = PaperMoney.parse("12.5")
    second = PaperMoney.parse("12.5")

    assert first == second
    assert hash(first) == hash(second)
    assert {first, second} == {first}
    with pytest.raises(FrozenInstanceError):
        first._canonical = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        PaperMoney("12.5")  # type: ignore[call-arg]


def test_account_identity_normalizes_bounded_labels_currency_and_utc() -> None:
    identity = create_paper_account_identity(
        account_id="  account-001  ",
        display_name="  Founder Paper Account  ",
        base_currency=" cny ",
        created_by="  founder  ",
        created_timestamp=datetime(
            2026,
            7,
            22,
            20,
            30,
            tzinfo=timezone(timedelta(hours=8)),
        ),
    )

    assert identity == PaperAccountIdentity(
        account_id="account-001",
        display_name="Founder Paper Account",
        base_currency="CNY",
        created_by="founder",
        created_timestamp=datetime(2026, 7, 22, 12, 30, tzinfo=timezone.utc),
    )
    assert identity.to_dict() == {
        "schema_version": PAPER_ACCOUNT_IDENTITY_SCHEMA_VERSION,
        "account_id": "account-001",
        "display_name": "Founder Paper Account",
        "base_currency": "CNY",
        "created_by": "founder",
        "created_timestamp": "2026-07-22T12:30:00+00:00",
    }
    assert set(identity.to_dict()).isdisjoint(
        {"cash", "balance", "positions", "orders", "fills"}
    )


def test_account_reference_contains_identity_only() -> None:
    identity = create_paper_account_identity(
        account_id="account-001",
        display_name="Founder Paper Account",
        base_currency="USD",
        created_by="founder",
        created_timestamp=datetime(2026, 7, 22, tzinfo=timezone.utc),
    )

    expected = {
        "schema_version": PAPER_ACCOUNT_REFERENCE_SCHEMA_VERSION,
        "account_id": "account-001",
    }
    assert create_paper_account_reference(identity).to_dict() == expected
    assert create_paper_account_reference(" account-001 ").to_dict() == expected
    assert PaperAccountReference("account-001").to_dict() == expected


@pytest.mark.parametrize(
    ("field_name", "invalid"),
    (
        ("account_id", ""),
        ("account_id", "x" * (MAX_PAPER_ACCOUNT_ID_LENGTH + 1)),
        ("display_name", " "),
        (
            "display_name",
            "x" * (MAX_PAPER_ACCOUNT_DISPLAY_NAME_LENGTH + 1),
        ),
        ("created_by", ""),
        ("created_by", "x" * (MAX_PAPER_ACCOUNT_ACTOR_LENGTH + 1)),
    ),
)
def test_account_identity_rejects_empty_or_overlong_fields(
    field_name: str,
    invalid: str,
) -> None:
    values = {
        "account_id": "account-001",
        "display_name": "Founder Account",
        "base_currency": "USD",
        "created_by": "founder",
        "created_timestamp": datetime(2026, 7, 22, tzinfo=timezone.utc),
    }
    values[field_name] = invalid

    with pytest.raises(ValueError, match=field_name):
        PaperAccountIdentity(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("currency", ("US", "USDT", "U1D", "美元", ""))
def test_account_identity_rejects_invalid_currency(currency: str) -> None:
    with pytest.raises(ValueError, match="base_currency"):
        PaperAccountIdentity(
            account_id="account-001",
            display_name="Founder Account",
            base_currency=currency,
            created_by="founder",
            created_timestamp=datetime(2026, 7, 22, tzinfo=timezone.utc),
        )


@pytest.mark.parametrize(
    "timestamp",
    (datetime(2026, 7, 22), "2026-07-22T00:00:00Z", None),
)
def test_account_identity_rejects_naive_or_invalid_timestamp(
    timestamp: object,
) -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        PaperAccountIdentity(
            account_id="account-001",
            display_name="Founder Account",
            base_currency="USD",
            created_by="founder",
            created_timestamp=timestamp,  # type: ignore[arg-type]
        )


def test_lifecycle_vocabulary_and_all_allowed_transitions_are_closed() -> None:
    assert SUPPORTED_PAPER_ACCOUNT_LIFECYCLE_STATUSES == (
        "active",
        "frozen",
        "closed",
    )
    validate_paper_account_lifecycle_transition("active", "frozen")
    validate_paper_account_lifecycle_transition("frozen", "active")

    eligible = PaperAccountCloseEligibility(True, True, True)
    validate_paper_account_lifecycle_transition(
        "active",
        "closed",
        close_eligibility=eligible,
    )
    validate_paper_account_lifecycle_transition(
        "frozen",
        "closed",
        close_eligibility=eligible,
    )
    assert eligible.to_dict() == {
        "schema_version": PAPER_ACCOUNT_CLOSE_ELIGIBILITY_SCHEMA_VERSION,
        "cash_is_zero": True,
        "position_quantities_are_zero": True,
        "aggregate_cost_bases_are_zero": True,
    }


@pytest.mark.parametrize(
    ("current", "target"),
    (
        ("active", "active"),
        ("frozen", "frozen"),
        ("closed", "closed"),
        ("closed", "active"),
        ("closed", "frozen"),
        ("active", "pending"),
        ("pending", "active"),
    ),
)
def test_lifecycle_rejects_same_state_terminal_and_unsupported_transitions(
    current: str,
    target: str,
) -> None:
    with pytest.raises(ValueError):
        validate_paper_account_lifecycle_transition(current, target)


@pytest.mark.parametrize(
    "eligibility",
    (
        None,
        PaperAccountCloseEligibility(False, True, True),
        PaperAccountCloseEligibility(True, False, True),
        PaperAccountCloseEligibility(True, True, False),
    ),
)
def test_close_requires_all_explicit_zero_eligibility_facts(
    eligibility: PaperAccountCloseEligibility | None,
) -> None:
    with pytest.raises(ValueError, match="closing requires"):
        validate_paper_account_lifecycle_transition(
            "active",
            "closed",
            close_eligibility=eligibility,
        )


def test_close_eligibility_rejects_non_boolean_assertions() -> None:
    with pytest.raises(ValueError, match="boolean"):
        PaperAccountCloseEligibility(1, True, True)  # type: ignore[arg-type]
