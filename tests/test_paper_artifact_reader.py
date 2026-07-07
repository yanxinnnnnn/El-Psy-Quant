"""Tests for local paper trading artifact reader and validation."""

import json

import pytest

from el_psy_quant.paper import (
    PAPER_TRADING_ARTIFACT_FILE_ENCODING,
    PAPER_TRADING_ARTIFACT_FILE_TOP_LEVEL_KEYS,
    PaperTradingArtifact,
    create_paper_account_state,
    create_paper_fill,
    create_paper_order_record,
    create_paper_trading_artifact,
    create_paper_trading_artifact_file_payload,
    create_paper_trading_session_summary,
    read_paper_trading_artifact_file,
    validate_paper_trading_artifact_file_payload,
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


def test_reader_reads_file_written_by_writer(tmp_path) -> None:
    artifact = make_artifact()
    destination = tmp_path / "paper-artifact.json"
    write_paper_trading_artifact_file(artifact, destination)

    payload = read_paper_trading_artifact_file(destination)

    assert payload == create_paper_trading_artifact_file_payload(artifact)


def test_reader_returns_payload_matching_file_contract(tmp_path) -> None:
    expected = make_payload()
    destination = tmp_path / "paper-artifact.json"
    destination.write_text(
        json.dumps(expected),
        encoding=PAPER_TRADING_ARTIFACT_FILE_ENCODING,
    )

    assert read_paper_trading_artifact_file(destination) == expected


def test_reader_uses_utf8_encoding(tmp_path) -> None:
    payload = make_payload()
    payload["created_timestamp"] = "2026-01-04T12:00:00-\u6d4b\u8bd5"
    destination = tmp_path / "paper-artifact.json"
    destination.write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding=PAPER_TRADING_ARTIFACT_FILE_ENCODING,
    )

    assert read_paper_trading_artifact_file(destination) == payload


@pytest.mark.parametrize("source_path", [object(), ""])
def test_invalid_path_input_raises(source_path) -> None:
    with pytest.raises(ValueError, match="source_path"):
        read_paper_trading_artifact_file(source_path)


def test_missing_file_raises(tmp_path) -> None:
    with pytest.raises(ValueError, match="does not exist"):
        read_paper_trading_artifact_file(tmp_path / "missing.json")


def test_directory_input_raises(tmp_path) -> None:
    with pytest.raises(ValueError, match="file path"):
        read_paper_trading_artifact_file(tmp_path)


def test_invalid_json_raises(tmp_path) -> None:
    source = tmp_path / "paper-artifact.json"
    source.write_text("{not json", encoding=PAPER_TRADING_ARTIFACT_FILE_ENCODING)

    with pytest.raises(ValueError, match="valid JSON"):
        read_paper_trading_artifact_file(source)


def test_non_dict_json_raises(tmp_path) -> None:
    source = tmp_path / "paper-artifact.json"
    source.write_text("[1, 2, 3]", encoding=PAPER_TRADING_ARTIFACT_FILE_ENCODING)

    with pytest.raises(ValueError, match="dict"):
        read_paper_trading_artifact_file(source)


def test_missing_schema_version_raises() -> None:
    payload = make_payload()
    del payload["schema_version"]

    with pytest.raises(ValueError, match="missing keys: schema_version"):
        validate_paper_trading_artifact_file_payload(payload)


def test_unsupported_schema_version_raises() -> None:
    payload = make_payload()
    payload["schema_version"] = 999

    with pytest.raises(ValueError, match="schema_version"):
        validate_paper_trading_artifact_file_payload(payload)


def test_missing_top_level_key_raises() -> None:
    payload = make_payload()
    del payload["fills"]

    with pytest.raises(ValueError, match="missing keys: fills"):
        validate_paper_trading_artifact_file_payload(payload)


def test_unexpected_extra_top_level_key_raises() -> None:
    payload = make_payload()
    payload["extra"] = "not part of contract"

    with pytest.raises(ValueError, match="unexpected keys: extra"):
        validate_paper_trading_artifact_file_payload(payload)


def test_validator_does_not_mutate_input_payload() -> None:
    payload = make_payload()
    original = dict(payload)

    validated = validate_paper_trading_artifact_file_payload(payload)

    assert payload == original
    assert validated == payload
    assert validated is not payload


def test_validator_returns_payload_in_contract_key_order() -> None:
    payload = make_payload()
    reversed_payload = {
        key: payload[key]
        for key in reversed(PAPER_TRADING_ARTIFACT_FILE_TOP_LEVEL_KEYS)
    }

    validated = validate_paper_trading_artifact_file_payload(reversed_payload)

    assert tuple(validated) == PAPER_TRADING_ARTIFACT_FILE_TOP_LEVEL_KEYS


def test_reader_does_not_add_audit_summary_behavior() -> None:
    import el_psy_quant.paper as paper  # noqa: PLC0415

    assert not hasattr(paper, "summarize_paper_trading_artifact_file")
    assert not hasattr(paper, "audit_paper_trading_artifact_file")


def test_reader_does_not_reconstruct_paper_trading_artifact(tmp_path) -> None:
    destination = tmp_path / "paper-artifact.json"
    write_paper_trading_artifact_file(make_artifact(), destination)

    payload = read_paper_trading_artifact_file(destination)

    assert isinstance(payload, dict)
    assert not isinstance(payload, PaperTradingArtifact)


def test_reader_does_not_add_artifact_methods() -> None:
    artifact = make_artifact()

    assert not hasattr(artifact, "read")
    assert not hasattr(artifact, "load")
    assert not hasattr(artifact, "write")
    assert not hasattr(artifact, "save")
    assert not hasattr(artifact, "path")


def test_reader_package_exports_work(tmp_path) -> None:
    from el_psy_quant.paper import (  # noqa: PLC0415
        read_paper_trading_artifact_file,
        validate_paper_trading_artifact_file_payload,
    )

    destination = tmp_path / "paper-artifact.json"
    write_paper_trading_artifact_file(make_artifact(), destination)

    payload = read_paper_trading_artifact_file(destination)

    assert validate_paper_trading_artifact_file_payload(payload) == payload
