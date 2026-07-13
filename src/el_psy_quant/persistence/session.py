"""Caller-owned SQLAlchemy session factory construction."""

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker


def create_product_session_factory(
    *,
    engine: Engine,
) -> sessionmaker[Session]:
    """Create a session factory with explicit caller-owned transactions."""
    if not isinstance(engine, Engine):
        raise TypeError("engine must be a SQLAlchemy Engine")
    return sessionmaker(bind=engine, class_=Session)
