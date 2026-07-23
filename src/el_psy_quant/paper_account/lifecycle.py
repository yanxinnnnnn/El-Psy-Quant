"""Closed Paper Account lifecycle vocabulary and pure transition checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PAPER_ACCOUNT_CLOSE_ELIGIBILITY_SCHEMA_VERSION = 1

SUPPORTED_PAPER_ACCOUNT_LIFECYCLE_STATUSES = (
    "active",
    "frozen",
    "closed",
)
INITIAL_PAPER_ACCOUNT_LIFECYCLE_STATUS = "active"

PaperAccountLifecycleStatus = Literal["active", "frozen", "closed"]

_ALLOWED_TRANSITIONS = frozenset(
    {
        ("active", "frozen"),
        ("frozen", "active"),
        ("active", "closed"),
        ("frozen", "closed"),
    }
)


def _normalize_status(value: str, field_name: str) -> PaperAccountLifecycleStatus:
    if not isinstance(value, str) or value not in (
        SUPPORTED_PAPER_ACCOUNT_LIFECYCLE_STATUSES
    ):
        supported = ", ".join(SUPPORTED_PAPER_ACCOUNT_LIFECYCLE_STATUSES)
        raise ValueError(f"{field_name} must be one of: {supported}")
    return value  # type: ignore[return-value]


def _validate_boolean(value: bool, field_name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a boolean")
    return value


@dataclass(frozen=True)
class PaperAccountCloseEligibility:
    """Explicit ledger-derived facts supplied to the pure close validator."""

    cash_is_zero: bool
    position_quantities_are_zero: bool
    aggregate_cost_bases_are_zero: bool

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "cash_is_zero",
            _validate_boolean(self.cash_is_zero, "cash_is_zero"),
        )
        object.__setattr__(
            self,
            "position_quantities_are_zero",
            _validate_boolean(
                self.position_quantities_are_zero,
                "position_quantities_are_zero",
            ),
        )
        object.__setattr__(
            self,
            "aggregate_cost_bases_are_zero",
            _validate_boolean(
                self.aggregate_cost_bases_are_zero,
                "aggregate_cost_bases_are_zero",
            ),
        )

    @property
    def is_eligible(self) -> bool:
        """Return whether all three explicit close preconditions hold."""
        return (
            self.cash_is_zero
            and self.position_quantities_are_zero
            and self.aggregate_cost_bases_are_zero
        )

    def to_dict(self) -> dict[str, object]:
        """Return the deterministic JSON-compatible close facts."""
        return {
            "schema_version": PAPER_ACCOUNT_CLOSE_ELIGIBILITY_SCHEMA_VERSION,
            "cash_is_zero": self.cash_is_zero,
            "position_quantities_are_zero": (
                self.position_quantities_are_zero
            ),
            "aggregate_cost_bases_are_zero": (
                self.aggregate_cost_bases_are_zero
            ),
        }


def validate_paper_account_lifecycle_transition(
    current_status: str,
    target_status: str,
    *,
    close_eligibility: PaperAccountCloseEligibility | None = None,
) -> None:
    """Validate one supported transition without mutating account state."""
    current = _normalize_status(current_status, "current_status")
    target = _normalize_status(target_status, "target_status")
    if current == target:
        raise ValueError("same-state lifecycle transitions are not allowed")
    if (current, target) not in _ALLOWED_TRANSITIONS:
        raise ValueError(f"unsupported lifecycle transition: {current} -> {target}")

    if target == "closed":
        if type(close_eligibility) is not PaperAccountCloseEligibility:
            raise ValueError(
                "closing requires explicit PaperAccountCloseEligibility"
            )
        if not close_eligibility.is_eligible:
            raise ValueError(
                "closing requires zero cash, position quantities, and "
                "aggregate cost bases"
            )
    elif close_eligibility is not None:
        raise ValueError("close_eligibility is valid only when closing")
