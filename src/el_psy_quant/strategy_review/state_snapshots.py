"""Strategy lifecycle state snapshot contract."""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

STRATEGY_LIFECYCLE_STATE_SNAPSHOT_SCHEMA_VERSION = 1

SUPPORTED_STRATEGY_LIFECYCLE_STATES = (
    "research_review",
    "paper_review",
    "watchlist",
    "on_hold",
    "rejected",
)


def _normalize_required_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _normalize_optional_string(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string when provided")
    normalized = value.strip()
    return normalized or None


def _normalize_optional_timestamp(
    declared_timestamp: object | None,
) -> pd.Timestamp | None:
    if declared_timestamp is None:
        return None
    try:
        normalized = pd.Timestamp(declared_timestamp)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "declared_timestamp must be convertible to a pandas Timestamp"
        ) from exc

    if pd.isna(normalized):
        raise ValueError("declared_timestamp must be valid")
    return normalized


def _normalize_lifecycle_state(lifecycle_state: str) -> str:
    normalized = _normalize_required_string(lifecycle_state, "lifecycle_state")
    if normalized not in SUPPORTED_STRATEGY_LIFECYCLE_STATES:
        supported = ", ".join(SUPPORTED_STRATEGY_LIFECYCLE_STATES)
        raise ValueError(
            f"unsupported lifecycle_state: {lifecycle_state}; supported: {supported}"
        )
    return normalized


def _normalize_string_sequence(
    values: Sequence[str],
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{field_name} must be a sequence of non-empty strings")

    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{field_name} must contain only non-empty strings"
            )
        normalized.append(value.strip())

    return tuple(normalized)


@dataclass(frozen=True)
class StrategyLifecycleStateSnapshot:
    """Immutable caller-supplied declaration of one lifecycle state."""

    snapshot_id: str
    strategy_id: str
    lifecycle_state: str
    rationale: str
    declared_by: str | None = None
    declared_timestamp: object | None = None
    notes: Sequence[str] = ()
    warnings: Sequence[str] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "snapshot_id",
            _normalize_required_string(self.snapshot_id, "snapshot_id"),
        )
        object.__setattr__(
            self,
            "strategy_id",
            _normalize_required_string(self.strategy_id, "strategy_id"),
        )
        object.__setattr__(
            self,
            "lifecycle_state",
            _normalize_lifecycle_state(self.lifecycle_state),
        )
        object.__setattr__(
            self,
            "rationale",
            _normalize_required_string(self.rationale, "rationale"),
        )
        object.__setattr__(
            self,
            "declared_by",
            _normalize_optional_string(self.declared_by, "declared_by"),
        )
        object.__setattr__(
            self,
            "declared_timestamp",
            _normalize_optional_timestamp(self.declared_timestamp),
        )
        object.__setattr__(
            self,
            "notes",
            _normalize_string_sequence(self.notes, "notes"),
        )
        object.__setattr__(
            self,
            "warnings",
            _normalize_string_sequence(self.warnings, "warnings"),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible lifecycle state snapshot."""
        return {
            "schema_version": STRATEGY_LIFECYCLE_STATE_SNAPSHOT_SCHEMA_VERSION,
            "snapshot_id": self.snapshot_id,
            "strategy_id": self.strategy_id,
            "lifecycle_state": self.lifecycle_state,
            "rationale": self.rationale,
            "declared_by": self.declared_by,
            "declared_timestamp": (
                None
                if self.declared_timestamp is None
                else self.declared_timestamp.isoformat()
            ),
            "notes": list(self.notes),
            "warnings": list(self.warnings),
        }


def create_strategy_lifecycle_state_snapshot(
    *,
    snapshot_id: str,
    strategy_id: str,
    lifecycle_state: str,
    rationale: str,
    declared_by: str | None = None,
    declared_timestamp: object | None = None,
    notes: Sequence[str] = (),
    warnings: Sequence[str] = (),
) -> StrategyLifecycleStateSnapshot:
    """Create and validate one lifecycle state declaration."""
    return StrategyLifecycleStateSnapshot(
        snapshot_id=snapshot_id,
        strategy_id=strategy_id,
        lifecycle_state=lifecycle_state,
        rationale=rationale,
        declared_by=declared_by,
        declared_timestamp=declared_timestamp,
        notes=notes,
        warnings=warnings,
    )
