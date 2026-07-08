"""Tests for promotion source references."""

import json
from dataclasses import FrozenInstanceError

import pytest

from el_psy_quant.promotion import (
    PROMOTION_SOURCE_REFERENCE_SCHEMA_VERSION,
    SUPPORTED_PROMOTION_SOURCE_TYPES,
    PromotionSourceReference,
    create_promotion_source_reference,
)


def test_valid_promotion_source_reference_creation() -> None:
    reference = create_promotion_source_reference(
        source_type="configured_run",
        reference="outputs/ma/run-1",
        run_id="run-1",
        artifact_id="manifest",
        label="Candidate source",
        description="Configured run selected for manual review.",
    )

    assert isinstance(reference, PromotionSourceReference)
    assert reference.source_type == "configured_run"
    assert reference.reference == "outputs/ma/run-1"
    assert reference.run_id == "run-1"
    assert reference.artifact_id == "manifest"
    assert reference.label == "Candidate source"
    assert reference.description == "Configured run selected for manual review."


def test_supported_source_types_are_explicit_and_deterministic() -> None:
    assert SUPPORTED_PROMOTION_SOURCE_TYPES == (
        "research_run",
        "backtest_artifact",
        "execution_artifact",
        "portfolio_artifact",
        "configured_run",
        "paper_artifact",
        "paper_result_summary",
    )


def test_source_type_validation() -> None:
    with pytest.raises(ValueError, match="unsupported source_type"):
        create_promotion_source_reference(
            source_type="unknown",
            reference="outputs/run-1",
        )


@pytest.mark.parametrize("reference", ["", "   "])
def test_blank_required_reference_validation(reference: str) -> None:
    with pytest.raises(ValueError, match="reference"):
        create_promotion_source_reference(
            source_type="research_run",
            reference=reference,
        )


def test_required_fields_strip_whitespace() -> None:
    reference = create_promotion_source_reference(
        source_type=" research_run ",
        reference=" outputs/run-1 ",
    )

    assert reference.source_type == "research_run"
    assert reference.reference == "outputs/run-1"


def test_optional_field_normalization() -> None:
    reference = create_promotion_source_reference(
        source_type="paper_artifact",
        reference="paper/paper_run_artifact.json",
        run_id=" run-1 ",
        artifact_id=" artifact-1 ",
        label="  ",
        description=" Paper artifact evidence. ",
    )

    assert reference.run_id == "run-1"
    assert reference.artifact_id == "artifact-1"
    assert reference.label is None
    assert reference.description == "Paper artifact evidence."


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("run_id", {"run_id": object()}),
        ("artifact_id", {"artifact_id": object()}),
        ("label", {"label": object()}),
        ("description", {"description": object()}),
    ],
)
def test_invalid_optional_field_types_raise_value_error(
    field_name: str,
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match=field_name):
        create_promotion_source_reference(
            source_type="research_run",
            reference="outputs/run-1",
            **kwargs,  # type: ignore[arg-type]
        )


def test_to_dict_is_deterministic_and_json_compatible() -> None:
    reference = create_promotion_source_reference(
        source_type="portfolio_artifact",
        reference="outputs/run-1/portfolio.json",
        run_id="run-1",
        artifact_id="portfolio-summary",
        label="Portfolio evidence",
        description=None,
    )

    expected = {
        "schema_version": PROMOTION_SOURCE_REFERENCE_SCHEMA_VERSION,
        "source_type": "portfolio_artifact",
        "reference": "outputs/run-1/portfolio.json",
        "run_id": "run-1",
        "artifact_id": "portfolio-summary",
        "label": "Portfolio evidence",
        "description": None,
    }
    assert reference.to_dict() == expected
    assert reference.to_dict() == expected
    json.dumps(reference.to_dict(), allow_nan=False)


def test_schema_version_is_json_compatible() -> None:
    assert PROMOTION_SOURCE_REFERENCE_SCHEMA_VERSION == 1
    json.dumps(
        {"schema_version": PROMOTION_SOURCE_REFERENCE_SCHEMA_VERSION},
        allow_nan=False,
    )


def test_promotion_source_reference_is_immutable() -> None:
    reference = create_promotion_source_reference(
        source_type="research_run",
        reference="outputs/run-1",
    )

    with pytest.raises(FrozenInstanceError):
        reference.reference = "other"  # type: ignore[misc]


def test_promotion_package_exports_public_api() -> None:
    from el_psy_quant import promotion

    assert (
        promotion.PROMOTION_SOURCE_REFERENCE_SCHEMA_VERSION
        == PROMOTION_SOURCE_REFERENCE_SCHEMA_VERSION
    )
    assert promotion.SUPPORTED_PROMOTION_SOURCE_TYPES is SUPPORTED_PROMOTION_SOURCE_TYPES
    assert promotion.PromotionSourceReference is PromotionSourceReference
    assert (
        promotion.create_promotion_source_reference
        is create_promotion_source_reference
    )
