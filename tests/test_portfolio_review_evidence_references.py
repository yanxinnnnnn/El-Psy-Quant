import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.portfolio_review import (
    SUPPORTED_PORTFOLIO_REVIEW_EVIDENCE_REFERENCE_TYPES,
    create_portfolio_review_component,
    create_portfolio_review_evidence_reference,
)


@pytest.mark.parametrize(
    "reference_type",
    SUPPORTED_PORTFOLIO_REVIEW_EVIDENCE_REFERENCE_TYPES,
)
def test_every_supported_portfolio_review_evidence_type_is_accepted(
    reference_type: str,
) -> None:
    reference = create_portfolio_review_evidence_reference(
        reference_type=f" {reference_type} ",
        reference_id=" evidence-1 ",
    )

    assert reference.reference_type == reference_type
    assert reference.reference_id == "evidence-1"


def test_reference_normalization_is_immutable_and_json_compatible() -> None:
    reference = create_portfolio_review_evidence_reference(
        reference_type=" research_run ",
        reference_id=" run-1 ",
        label=" ",
        description=" Research evidence ",
    )

    assert reference.label is None
    assert reference.description == "Research evidence"
    assert json.loads(json.dumps(reference.to_dict(), allow_nan=False)) == (
        reference.to_dict()
    )
    with pytest.raises(FrozenInstanceError):
        reference.reference_id = "other"  # type: ignore[misc]


def test_unsupported_evidence_type_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported reference_type"):
        create_portfolio_review_evidence_reference(
            reference_type="account_position",
            reference_id="position-1",
        )


def test_component_requires_evidence_and_research_origin() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        create_portfolio_review_component(
            component_id="component-a",
            strategy_id="strategy-a",
            evidence_references=(),
        )

    governance_only = create_portfolio_review_evidence_reference(
        reference_type="promotion_record",
        reference_id="promotion-1",
    )
    with pytest.raises(ValueError, match="research-origin"):
        create_portfolio_review_component(
            component_id="component-a",
            strategy_id="strategy-a",
            evidence_references=(governance_only,),
        )


def test_component_rejects_duplicate_evidence_identity() -> None:
    reference = create_portfolio_review_evidence_reference(
        reference_type="research_run",
        reference_id="run-1",
    )

    with pytest.raises(ValueError, match="duplicate evidence reference"):
        create_portfolio_review_component(
            component_id="component-a",
            strategy_id="strategy-a",
            evidence_references=(reference, reference),
        )


def test_component_normalizes_symbols_and_preserves_missing_symbol_evidence() -> None:
    evidence = create_portfolio_review_evidence_reference(
        reference_type="configured_run",
        reference_id="run-1",
    )
    symbols = [" aapl ", "msft"]

    component = create_portfolio_review_component(
        component_id=" component-a ",
        strategy_id=" strategy-a ",
        evidence_references=[evidence],
        symbols=symbols,
        label=" ",
        description=" Candidate ",
    )
    missing_symbols = create_portfolio_review_component(
        component_id="component-b",
        strategy_id="strategy-b",
        evidence_references=(evidence,),
    )

    assert component.component_id == "component-a"
    assert component.strategy_id == "strategy-a"
    assert component.symbols == ("AAPL", "MSFT")
    assert component.label is None
    assert component.description == "Candidate"
    assert symbols == [" aapl ", "msft"]
    assert missing_symbols.symbols is None
    assert missing_symbols.to_dict()["symbols"] is None
    assert json.loads(json.dumps(component.to_dict(), allow_nan=False)) == (
        component.to_dict()
    )
    with pytest.raises(FrozenInstanceError):
        component.strategy_id = "other"  # type: ignore[misc]


def test_component_reuses_strict_symbol_universe_rules() -> None:
    evidence = create_portfolio_review_evidence_reference(
        reference_type="backtest_artifact",
        reference_id="artifact-1",
    )

    with pytest.raises(ValueError, match="duplicate symbol"):
        create_portfolio_review_component(
            component_id="component-a",
            strategy_id="strategy-a",
            evidence_references=(evidence,),
            symbols=("AAPL", " aapl "),
        )
    with pytest.raises(ValueError, match="single symbol"):
        create_portfolio_review_component(
            component_id="component-a",
            strategy_id="strategy-a",
            evidence_references=(evidence,),
            symbols="AAPL",  # type: ignore[arg-type]
        )
