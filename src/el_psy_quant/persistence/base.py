"""Declarative metadata boundary for product persistence models."""

from sqlalchemy.orm import DeclarativeBase


class ProductPersistenceBase(DeclarativeBase):
    """Metadata registry reserved for product persistence models."""
