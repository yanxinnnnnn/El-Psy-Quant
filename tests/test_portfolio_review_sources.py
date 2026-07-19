import json
from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
import pytest

from el_psy_quant.portfolio_review import (
    PortfolioReviewSource,
    create_portfolio_review_component,
    create_portfolio_review_evidence_reference,
    create_portfolio_review_source,
)


def _component(
    component_id: str,
    *,
    strategy_id: str | None = None,
    reference_id: str | None = None,
    symbols: tuple[str, ...] | None = None,
):
    reference = create_portfolio_review_evidence_reference(
        reference_type="research_run",
        reference_id=reference_id or f"run-{component_id}",
    )
    return create_portfolio_review_component(
        component_id=component_id,
        strategy_id=strategy_id or f"strategy-{component_id}",
        evidence_references=(reference,),
        symbols=symbols,
    )


def _returns(component_ids: tuple[str, ...], *, periods: int = 3) -> pd.DataFrame:
    return pd.DataFrame(
        {
            component_id: [0.01 * (row + column) for row in range(periods)]
            for column, component_id in enumerate(component_ids)
        },
        index=pd.date_range("2025-01-01", periods=periods, freq="D"),
    )


def _source(
    *,
    source_id: str = "source-1",
    components=None,
    aligned_returns: pd.DataFrame | None = None,
    evaluation_frequency: str = "daily",
    periods_per_year: int | float | None = 252,
    created_by: str = "founder",
    created_timestamp: object = "2025-01-04T08:00:00+08:00",
    assumptions: tuple[str, ...] = ("Static review inputs",),
    warnings: tuple[str, ...] = ("Historical evidence only",),
    missing_evidence: tuple[str, ...] = ("No account holdings",),
) -> PortfolioReviewSource:
    normalized_components = (
        (_component("component-a"), _component("component-b"))
        if components is None
        else components
    )
    component_ids = tuple(
        component.component_id for component in normalized_components
    )
    return create_portfolio_review_source(
        source_id=source_id,
        components=normalized_components,
        aligned_returns=(
            _returns(component_ids)
            if aligned_returns is None
            else aligned_returns
        ),
        evaluation_frequency=evaluation_frequency,
        periods_per_year=periods_per_year,
        created_by=created_by,
        created_timestamp=created_timestamp,
        assumptions=assumptions,
        warnings=warnings,
        missing_evidence=missing_evidence,
    )


@pytest.mark.parametrize("component_count", [2, 12])
def test_source_accepts_component_boundaries_and_three_observations(
    component_count: int,
) -> None:
    components = tuple(_component(f"component-{index}") for index in range(12))[
        :component_count
    ]
    component_ids = tuple(component.component_id for component in components)

    source = _source(
        components=components,
        aligned_returns=_returns(component_ids, periods=3),
    )

    assert source.component_ids == component_ids
    assert len(source.return_observations) == 3


def test_source_preserves_order_copies_inputs_and_normalizes_audit_values() -> None:
    components = [_component("component-b"), _component("component-a")]
    aligned_returns = _returns(("component-b", "component-a"))
    original_returns = aligned_returns.copy(deep=True)
    assumptions = [" First ", "First"]

    source = create_portfolio_review_source(
        source_id=" source-1 ",
        components=components,
        aligned_returns=aligned_returns,
        evaluation_frequency=" daily ",
        periods_per_year=252,
        created_by=" founder ",
        created_timestamp="2025-01-04T08:00:00+08:00",
        assumptions=assumptions,
    )
    aligned_returns.iloc[0, 0] = 99.0
    components.reverse()
    assumptions.append("Later")

    assert source.source_id == "source-1"
    assert source.component_ids == ("component-b", "component-a")
    assert source.return_observations[0].component_returns == (0.0, 0.01)
    assert source.evaluation_frequency == "daily"
    assert source.periods_per_year == 252.0
    assert source.created_by == "founder"
    assert source.created_timestamp.isoformat() == "2025-01-04T00:00:00+00:00"
    assert source.assumptions == ("First", "First")
    pd.testing.assert_frame_equal(original_returns, _returns(source.component_ids))
    assert aligned_returns.iloc[0, 0] == 99.0


def test_source_accepts_none_periods_and_canonicalizes_negative_zero() -> None:
    frame = _returns(("component-a", "component-b"))
    frame.iloc[0, 0] = -0.0

    source = _source(aligned_returns=frame, periods_per_year=None)

    assert source.periods_per_year is None
    assert source.return_observations[0].component_returns[0] == 0.0
    assert str(source.return_observations[0].component_returns[0]) == "0.0"


def test_source_export_and_digest_are_deterministic_json() -> None:
    first = _source()
    second = _source()

    assert first.source_digest == second.source_digest
    assert len(first.source_digest) == 64
    assert first.source_digest == first.source_digest.lower()
    assert set(first.source_digest) <= set("0123456789abcdef")
    assert json.loads(
        json.dumps(first.to_dict(), allow_nan=False, ensure_ascii=False)
    ) == first.to_dict()
    with pytest.raises(FrozenInstanceError):
        first.source_id = "other"  # type: ignore[misc]


@pytest.mark.parametrize(
    "changed_source",
    [
        lambda: _source(source_id="source-2"),
        lambda: _source(
            components=(
                _component("component-a", reference_id="different-run"),
                _component("component-b"),
            )
        ),
        lambda: _source(
            components=(
                _component("component-a", symbols=("AAPL",)),
                _component("component-b"),
            )
        ),
        lambda: _source(
            aligned_returns=pd.DataFrame(
                {
                    "component-a": [0.0, 0.011, 0.02],
                    "component-b": [0.01, 0.02, 0.03],
                },
                index=pd.date_range("2025-01-01", periods=3, freq="D"),
            )
        ),
        lambda: _source(
            aligned_returns=pd.DataFrame(
                {
                    "component-a": [0.0, 0.01, 0.02],
                    "component-b": [0.01, 0.02, 0.03],
                },
                index=pd.date_range("2025-02-01", periods=3, freq="D"),
            )
        ),
        lambda: _source(evaluation_frequency="weekly"),
        lambda: _source(periods_per_year=365),
        lambda: _source(created_by="reviewer"),
        lambda: _source(created_timestamp="2025-01-05T00:00:00Z"),
        lambda: _source(assumptions=("Different",)),
        lambda: _source(warnings=("Different",)),
        lambda: _source(missing_evidence=("Different",)),
    ],
)
def test_each_material_source_field_changes_digest(changed_source) -> None:
    assert changed_source().source_digest != _source().source_digest


@pytest.mark.parametrize("component_count", [1, 13])
def test_source_rejects_out_of_bounds_component_count(component_count: int) -> None:
    components = tuple(
        _component(f"component-{index}") for index in range(component_count)
    )
    with pytest.raises(ValueError, match="between 2 and 12"):
        create_portfolio_review_source(
            source_id="source-1",
            components=components,
            aligned_returns=_returns(
                tuple(component.component_id for component in components)
            ),
            evaluation_frequency="daily",
            created_by="founder",
            created_timestamp="2025-01-01T00:00:00Z",
        )


def test_source_rejects_duplicate_component_id() -> None:
    components = (
        _component("component-a", strategy_id="strategy-a"),
        _component("component-a", strategy_id="strategy-b"),
    )
    with pytest.raises(ValueError, match="duplicate component_id"):
        _source(components=components)


@pytest.mark.parametrize(
    ("aligned_returns", "message"),
    [
        ([1, 2, 3], "pandas DataFrame"),
        (
            pd.DataFrame(
                {"component-a": [0.0, 0.1, 0.2], "component-b": [0.0, 0.1, 0.2]}
            ),
            "DatetimeIndex",
        ),
        (_returns(("component-a", "component-b"), periods=2), "at least three"),
        (
            pd.DataFrame(
                {"component-a": [0.0, 0.1, 0.2], "component-b": [0.0, 0.1, 0.2]},
                index=pd.to_datetime(["2025-01-01", "2025-01-01", "2025-01-02"]),
            ),
            "strictly increasing",
        ),
        (
            pd.DataFrame(
                {"component-a": [0.0, 0.1, 0.2], "component-b": [0.0, 0.1, 0.2]},
                index=pd.to_datetime(["2025-01-02", "2025-01-01", "2025-01-03"]),
            ),
            "strictly increasing",
        ),
        (_returns(("component-b", "component-a")), "exactly match"),
        (_returns(("component-a", "component-b", "extra")), "exactly match"),
        (_returns(("component-a",)), "exactly match"),
    ],
)
def test_source_rejects_invalid_aligned_table_shape(
    aligned_returns,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _source(aligned_returns=aligned_returns)


@pytest.mark.parametrize(
    "invalid_value",
    ["not-numeric", True, np.nan, np.inf, -np.inf],
)
def test_source_rejects_invalid_return_values(invalid_value: object) -> None:
    frame = _returns(("component-a", "component-b"))
    frame = frame.astype(object)
    frame.iloc[1, 0] = invalid_value

    with pytest.raises(ValueError, match="returns|return values"):
        _source(aligned_returns=frame)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("evaluation_frequency", " ", "evaluation_frequency"),
        ("created_by", "", "created_by"),
        ("periods_per_year", True, "periods_per_year"),
        ("periods_per_year", 0, "periods_per_year"),
        ("periods_per_year", -1, "periods_per_year"),
        ("periods_per_year", np.nan, "periods_per_year"),
        ("periods_per_year", np.inf, "periods_per_year"),
        ("created_timestamp", "2025-01-01", "timezone-aware"),
        ("created_timestamp", "not-a-timestamp", "timezone-aware"),
    ],
)
def test_source_rejects_invalid_evaluation_and_audit_values(
    field: str,
    value: object,
    message: str,
) -> None:
    kwargs = {field: value}
    with pytest.raises(ValueError, match=message):
        _source(**kwargs)


def test_source_rejects_blank_optional_prose() -> None:
    with pytest.raises(ValueError, match="assumptions item"):
        _source(assumptions=("valid", " "))
