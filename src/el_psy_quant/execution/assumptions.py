"""Execution assumptions for deterministic local backtests."""

from dataclasses import dataclass

SUPPORTED_TIMING = ("same_bar", "next_bar")
SUPPORTED_PRICE_FIELDS = ("open", "high", "low", "close")
SUPPORTED_MISSING_PRICE_POLICIES = ("raise",)


def _normalize_supported_value(
    value: str,
    *,
    field_name: str,
    supported_values: tuple[str, ...],
) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    normalized = value.strip().lower()
    if normalized not in supported_values:
        supported = ", ".join(supported_values)
        raise ValueError(f"{field_name} must be one of: {supported}")
    return normalized


@dataclass(frozen=True)
class ExecutionAssumptions:
    """Explicit local backtest execution assumptions."""

    timing: str
    price_field: str
    missing_price_policy: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "timing",
            _normalize_supported_value(
                self.timing,
                field_name="timing",
                supported_values=SUPPORTED_TIMING,
            ),
        )
        object.__setattr__(
            self,
            "price_field",
            _normalize_supported_value(
                self.price_field,
                field_name="price_field",
                supported_values=SUPPORTED_PRICE_FIELDS,
            ),
        )
        object.__setattr__(
            self,
            "missing_price_policy",
            _normalize_supported_value(
                self.missing_price_policy,
                field_name="missing_price_policy",
                supported_values=SUPPORTED_MISSING_PRICE_POLICIES,
            ),
        )

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-compatible dictionary representation."""
        return {
            "timing": self.timing,
            "price_field": self.price_field,
            "missing_price_policy": self.missing_price_policy,
        }


def validate_execution_assumptions(
    timing: str,
    price_field: str,
    missing_price_policy: str,
) -> ExecutionAssumptions:
    """Validate and normalize execution assumptions."""
    return ExecutionAssumptions(
        timing=timing,
        price_field=price_field,
        missing_price_policy=missing_price_policy,
    )


def default_execution_assumptions() -> ExecutionAssumptions:
    """Return conservative default execution assumptions."""
    return ExecutionAssumptions(
        timing="next_bar",
        price_field="open",
        missing_price_policy="raise",
    )
