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
from el_psy_quant.persistence.paper_job_repository import (
    PaperJobRepository,
    SqlAlchemyPaperJobRepository,
)
from el_psy_quant.persistence.paper_jobs import (
    PaperJobRecord,
    PaperJobStatus,
    PreparedPaperRunRequest,
    create_queued_paper_job_record,
    deserialize_paper_run_request,
    prepare_paper_run_request_for_persistence,
    serialize_paper_run_request,
    transition_paper_job_record,
)
from el_psy_quant.persistence.session import create_product_session_factory

__all__ = [
    "ArtifactIndexEntry",
    "ArtifactIndexRepository",
    "PaperJobRecord",
    "PaperJobRepository",
    "PaperJobStatus",
    "PreparedPaperRunRequest",
    "ProductDatabaseConfig",
    "ProductPersistenceBase",
    "SqlAlchemyArtifactIndexRepository",
    "SqlAlchemyPaperJobRepository",
    "create_artifact_index_entry",
    "create_product_database_engine",
    "create_product_session_factory",
    "create_queued_paper_job_record",
    "deserialize_paper_run_request",
    "prepare_paper_run_request_for_persistence",
    "resolve_product_database_config",
    "serialize_paper_run_request",
    "transition_paper_job_record",
]
