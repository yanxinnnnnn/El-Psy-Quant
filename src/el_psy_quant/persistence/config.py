"""Explicit local SQLite product database configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PRODUCT_DATABASE_PATH_ENV = "EL_PSY_QUANT_PRODUCT_DATABASE_PATH"


@dataclass(frozen=True)
class ProductDatabaseConfig:
    """Normalized path to the one configured local SQLite database file."""

    database_path: Path


def _validate_database_path_value(value: object) -> str | Path:
    if not isinstance(value, (str, Path)):
        raise ValueError("product database path must be a string or Path")
    text_value = str(value).strip()
    if not text_value:
        raise ValueError("product database path must not be blank")
    if "://" in text_value or text_value.lower().startswith("sqlite:"):
        raise ValueError(
            "product database path must be a local file path, not a database URL"
        )
    if isinstance(value, str):
        return text_value
    return value


def resolve_product_database_config(
    *,
    database_path: str | Path | None = None,
) -> ProductDatabaseConfig:
    """Resolve the explicit local SQLite file path without filesystem writes."""
    configured_value: object = (
        os.getenv(PRODUCT_DATABASE_PATH_ENV)
        if database_path is None
        else database_path
    )
    if configured_value is None:
        raise ValueError(
            f"product database path is required through {PRODUCT_DATABASE_PATH_ENV} "
            "or an explicit database_path"
        )

    normalized_path = Path(_validate_database_path_value(configured_value)).resolve(
        strict=False
    )
    if normalized_path.exists() and normalized_path.is_dir():
        raise ValueError("product database path must identify a file, not a directory")
    return ProductDatabaseConfig(database_path=normalized_path)
