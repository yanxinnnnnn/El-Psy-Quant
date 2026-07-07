"""Compact audit summaries for saved paper trading artifact payloads."""

from dataclasses import dataclass

from el_psy_quant.paper.reader import validate_paper_trading_artifact_file_payload

_SESSION_SUMMARY_FIELDS = (
    "session_start_timestamp",
    "session_end_timestamp",
    "starting_cash",
    "ending_cash",
    "cash_change",
    "order_count",
    "fill_count",
    "starting_positions",
    "ending_positions",
    "position_changes",
)


def _require_session_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    session_summary = payload["session_summary"]
    if not isinstance(session_summary, dict):
        raise ValueError("session_summary must be a dict")

    missing_fields = [
        field for field in _SESSION_SUMMARY_FIELDS if field not in session_summary
    ]
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise ValueError(f"session_summary missing fields: {missing}")

    return session_summary


def _count_records(value: object, *, field_name: str) -> int:
    if not isinstance(value, list):
        raise ValueError(f"session_summary {field_name} must be a list")
    return len(value)


@dataclass(frozen=True)
class PaperTradingArtifactAuditSummary:
    """Immutable compact audit summary for a saved paper trading artifact."""

    schema_version: int
    created_timestamp: str
    session_start_timestamp: str
    session_end_timestamp: str
    starting_cash: float
    ending_cash: float
    cash_change: float
    order_count: int
    fill_count: int
    starting_position_count: int
    ending_position_count: int
    position_change_count: int

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible audit summary export."""
        return {
            "schema_version": self.schema_version,
            "created_timestamp": self.created_timestamp,
            "session_start_timestamp": self.session_start_timestamp,
            "session_end_timestamp": self.session_end_timestamp,
            "starting_cash": self.starting_cash,
            "ending_cash": self.ending_cash,
            "cash_change": self.cash_change,
            "order_count": self.order_count,
            "fill_count": self.fill_count,
            "starting_position_count": self.starting_position_count,
            "ending_position_count": self.ending_position_count,
            "position_change_count": self.position_change_count,
        }


def create_paper_trading_artifact_audit_summary(
    payload: object,
) -> PaperTradingArtifactAuditSummary:
    """Create a compact audit summary from a validated paper artifact payload."""
    validated_payload = validate_paper_trading_artifact_file_payload(payload)
    session_summary = _require_session_summary(validated_payload)

    return PaperTradingArtifactAuditSummary(
        schema_version=validated_payload["schema_version"],
        created_timestamp=validated_payload["created_timestamp"],
        session_start_timestamp=session_summary["session_start_timestamp"],
        session_end_timestamp=session_summary["session_end_timestamp"],
        starting_cash=session_summary["starting_cash"],
        ending_cash=session_summary["ending_cash"],
        cash_change=session_summary["cash_change"],
        order_count=session_summary["order_count"],
        fill_count=session_summary["fill_count"],
        starting_position_count=_count_records(
            session_summary["starting_positions"],
            field_name="starting_positions",
        ),
        ending_position_count=_count_records(
            session_summary["ending_positions"],
            field_name="ending_positions",
        ),
        position_change_count=_count_records(
            session_summary["position_changes"],
            field_name="position_changes",
        ),
    )
