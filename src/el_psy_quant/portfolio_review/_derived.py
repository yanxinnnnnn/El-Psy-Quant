"""Internal construction helpers for derived portfolio-review results."""

from __future__ import annotations

import math

_DERIVED_CONSTRUCTOR_MESSAGE = (
    "portfolio-review interaction and impact values are created by "
    "analyze_portfolio_review_interaction_and_impact"
)


def reject_public_construction(*args: object, **kwargs: object) -> None:
    """Prevent callers from authoring derived financial values directly."""
    del args, kwargs
    raise TypeError(_DERIVED_CONSTRUCTOR_MESSAGE)


def new_derived(result_type: type[object], **values: object) -> object:
    """Construct one validated derived result inside the analysis boundary."""
    result = object.__new__(result_type)
    for field_name, value in values.items():
        object.__setattr__(result, field_name, value)
    return result


def canonical_float(value: float, field_name: str) -> float:
    """Require a finite Python float and canonicalize numerical zero."""
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"derived {field_name} must be finite")
    return 0.0 if normalized == 0.0 else normalized
