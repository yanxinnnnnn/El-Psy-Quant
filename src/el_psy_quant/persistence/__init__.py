"""Explicit local product persistence foundations."""

from el_psy_quant.persistence.artifact_index import (
    ArtifactIndexEntry,
    create_artifact_index_entry,
)
from el_psy_quant.persistence.artifact_index_repository import (
    ArtifactIndexRepository,
    SqlAlchemyArtifactIndexRepository,
)
from el_psy_quant.persistence.base import ProductPersistenceBase
from el_psy_quant.persistence.config import (
    ProductDatabaseConfig,
    resolve_product_database_config,
)
from el_psy_quant.persistence.engine import create_product_database_engine
from el_psy_quant.persistence.session import create_product_session_factory

__all__ = [
    "ArtifactIndexEntry",
    "ArtifactIndexRepository",
    "ProductDatabaseConfig",
    "ProductPersistenceBase",
    "SqlAlchemyArtifactIndexRepository",
    "create_artifact_index_entry",
    "create_product_database_engine",
    "create_product_session_factory",
    "resolve_product_database_config",
]
