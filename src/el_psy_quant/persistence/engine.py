"""SQLite engine construction for local product persistence."""

from __future__ import annotations

import sqlite3
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import URL

from el_psy_quant.persistence.config import ProductDatabaseConfig


def _enable_sqlite_foreign_keys(
    dbapi_connection: Any,
    _connection_record: Any,
) -> None:
    if not isinstance(dbapi_connection, sqlite3.Connection):
        raise TypeError("product database engine requires SQLite connections")
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


def create_product_database_engine(
    *,
    config: ProductDatabaseConfig,
) -> Engine:
    """Create one lazy SQLite engine for the configured local database file.

    ``check_same_thread=False`` permits future FastAPI composition, but callers must
    still give each concurrent unit of work its own connection and session.
    Constructing the engine does not connect, create the database file, or migrate it.
    """
    if not isinstance(config, ProductDatabaseConfig):
        raise TypeError("config must be a ProductDatabaseConfig")

    engine = create_engine(
        URL.create("sqlite", database=str(config.database_path)),
        connect_args={"check_same_thread": False},
    )
    event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine
