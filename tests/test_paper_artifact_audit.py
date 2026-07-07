"""Tests for compact paper trading artifact audit summaries."""

import json

import pytest

from el_psy_quant.paper import (
    PaperTradingArtifact,
    PaperTradingArtifactAuditSummary,
    create_paper_account_state,
    create_paper_fill,
    create_paper_order_record,
    create_paper_trading_artifact,
    create_paper_trading_artifact_audit_summary,
    create_paper_trading_artifact_file_payload,
    create_paper_trading_session_summary,
    read_paper_trading_artifact_file,
    write_paper_trading_artifact_file,
)


def make_starting_state():
    return create_paper_account_state(
        starting_cash=1_000.0,
        current_cash=1_000.0,
        positions={"MSFT": 1.0},
        timestamp="2026-01-01",
    )


def make_ending_state():
    return create_paper_account_state(
        starting_cash=1_000.0,
        current_cash=875.0,
        positions={"MSFT": 0.5, "AAPL": 2.0},
        timestamp="2026-01-03",
    )


def make_orders():
    return [
        create_paper_order_record(
            order_id="order-1",
            timestamp="2026-01-02",
            symbol="aapl",
            side="buy",
            quantity=2.0,
            status="filled",
        ),
        create_paper_order_record(
            order_id="order-2",
            timestamp="2026-01-03",
            symbol=" msft ",
            side="sell",
            quantity=0.5,
            status="filled",
        ),
    ]


def make_fills():
    return [
        create_paper_fill(
            timestamp="2026-01-02",
            symbol="AAPL",
            side="buy",
            quantity=2.0,
            price=100.0,
            order_id="order-1",
        ),
        create_paper_fill(
            timestamp="2026-01-03",
            symbol="MSFT",
            side="sell",
            quantity=0.5,
            price=150.0,
            order_id="order-2",
        ),
    ]


def make_artifact():
    starting = make_starting_state()
    ending = make_ending_state()
    orders = make_orders()
    fills = make_fills()
    summary = create_paper_trading_session_summary(
        starting_account_state=starting,
        ending_account_state=ending,
        orders=orders,
        fills=fills,
    )

    return create_paper_trading_artifact(
        created_timestamp="2026-01-04T12:00:00",
        starting_account_state=starting,
        ending_account_state=ending,
        orders=orders,
        fills=fills,
        session_summary=summary,
    )


def make_payload() -> dict[str, object]:
    return create_paper_trading_artifact_file_payload(make_artifact())


def test_audit_summary_can_be_created_from_read_file_payload(tmp_path) -> None:
    destination = tmp_path / "paper-artifact.json"
    write_paper_trading_artifact_file(make_artifact(), destination)
    payload = read_paper_trading_artifact_file(destination)

    summary = create_paper_trading_artifact_audit_summary(payload)

    assert isinstance(summary, PaperTradingArtifactAuditSummary)
    assert summary.to_dict()["schema_version"] == 1


def test_audit_summary_to_dict_is_deterministic_and_json_compatible() -> None:
    payload = make_payload()

    first = create_paper_trading_artifact_audit_summary(payload).to_dict()
    second = create_paper_trading_artifact_audit_summary(payload).to_dict()

    assert first == second
    json.dumps(first, allow_nan=False)


def test_audit_summary_contains_artifact_identity_fields() -> None:
    payload = make_payload()
    summary = create_paper_trading_artifact_audit_summary(payload).to_dict()

    assert summary["schema_version"] == payload["schema_version"]
    assert summary["created_timestamp"] == payload["created_timestamp"]


def test_audit_summary_contains_key_session_facts() -> None:
    payload = make_payload()
    session_summary = payload["session_summary"]
    summary = create_paper_trading_artifact_audit_summary(payload).to_dict()

    assert summary["session_start_timestamp"] == (
        session_summary["session_start_timestamp"]
    )
    assert summary["session_end_timestamp"] == (
        session_summary["session_end_timestamp"]
    )
    assert summary["starting_cash"] == session_summary["starting_cash"]
    assert summary["ending_cash"] == session_summary["ending_cash"]
    assert summary["cash_change"] == session_summary["cash_change"]
    assert summary["order_count"] == session_summary["order_count"]
    assert summary["fill_count"] == session_summary["fill_count"]


def test_audit_summary_counts_positions_orders_and_fills() -> None:
    summary = create_paper_trading_artifact_audit_summary(make_payload()).to_dict()

    assert summary["order_count"] == 2
    assert summary["fill_count"] == 2
    assert summary["starting_position_count"] == 1
    assert summary["ending_position_count"] == 2
    assert summary["position_change_count"] == 2


def test_invalid_top_level_payload_raises() -> None:
    with pytest.raises(ValueError, match="dict"):
        create_paper_trading_artifact_audit_summary(object())


def test_missing_session_summary_field_raises() -> None:
    payload = make_payload()
    del payload["session_summary"]["cash_change"]

    with pytest.raises(ValueError, match="session_summary missing fields: cash_change"):
        create_paper_trading_artifact_audit_summary(payload)


def test_non_dict_session_summary_raises() -> None:
    payload = make_payload()
    payload["session_summary"] = []

    with pytest.raises(ValueError, match="session_summary must be a dict"):
        create_paper_trading_artifact_audit_summary(payload)


@pytest.mark.parametrize(
    "field_name",
    ["starting_positions", "ending_positions", "position_changes"],
)
def test_malformed_position_lists_raise(field_name) -> None:
    payload = make_payload()
    payload["session_summary"][field_name] = "not a list"

    with pytest.raises(ValueError, match=f"session_summary {field_name}"):
        create_paper_trading_artifact_audit_summary(payload)


def test_audit_summary_creation_does_not_mutate_input_payload() -> None:
    payload = make_payload()
    original = json.loads(json.dumps(payload))

    create_paper_trading_artifact_audit_summary(payload)

    assert payload == original


def test_audit_summary_does_not_reconstruct_paper_trading_artifact() -> None:
    summary = create_paper_trading_artifact_audit_summary(make_payload())

    assert isinstance(summary, PaperTradingArtifactAuditSummary)
    assert not isinstance(summary, PaperTradingArtifact)


def test_no_dashboard_report_or_cli_behavior_is_added() -> None:
    import el_psy_quant.paper as paper  # noqa: PLC0415

    assert not hasattr(paper, "render_paper_trading_artifact_report")
    assert not hasattr(paper, "create_paper_trading_artifact_dashboard")
    assert not hasattr(paper, "run_paper_trading_artifact_cli")


def test_audit_summary_does_not_add_artifact_methods() -> None:
    artifact = make_artifact()

    assert not hasattr(artifact, "audit")
    assert not hasattr(artifact, "report")
    assert not hasattr(artifact, "read")
    assert not hasattr(artifact, "load")
    assert not hasattr(artifact, "write")
    assert not hasattr(artifact, "save")
    assert not hasattr(artifact, "path")


def test_audit_summary_package_exports_work() -> None:
    from el_psy_quant.paper import (  # noqa: PLC0415
        PaperTradingArtifactAuditSummary,
        create_paper_trading_artifact_audit_summary,
    )

    summary = create_paper_trading_artifact_audit_summary(make_payload())

    assert isinstance(summary, PaperTradingArtifactAuditSummary)
