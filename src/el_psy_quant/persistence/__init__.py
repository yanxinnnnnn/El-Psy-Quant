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
from el_psy_quant.persistence.market_time_repository import (
    MarketTimeRepository,
    SqlAlchemyMarketTimeRepository,
)
from el_psy_quant.persistence.market_time_replays import (
    MARKET_TIME_PERSISTENCE_RECORD_SCHEMA_VERSION,
    MarketDataReplayRecord,
    create_market_data_replay_record,
)
from el_psy_quant.persistence.paper_job_repository import (
    PaperJobRepository,
    SqlAlchemyPaperJobRepository,
)
from el_psy_quant.persistence.paper_job_result_reference_repository import (
    PaperJobResultReferenceRepository,
    SqlAlchemyPaperJobResultReferenceRepository,
)
from el_psy_quant.persistence.paper_job_result_references import (
    PaperJobResultReference,
    create_paper_job_result_reference,
)
from el_psy_quant.persistence.paper_job_attempt_repository import (
    PaperJobAttemptRepository,
    SqlAlchemyPaperJobAttemptRepository,
)
from el_psy_quant.persistence.paper_job_attempts import (
    PaperJobAttemptRecord,
    PaperJobAttemptStatus,
    PaperJobErrorCode,
    complete_paper_job_attempt,
    create_running_paper_job_attempt,
)
from el_psy_quant.persistence.paper_job_submission_key_repository import (
    PaperJobSubmissionKeyRepository,
    SqlAlchemyPaperJobSubmissionKeyRepository,
)
from el_psy_quant.persistence.paper_job_submission_keys import (
    PaperJobSubmissionKeyRecord,
    create_paper_job_submission_key_record,
    validate_paper_job_idempotency_key,
)
from el_psy_quant.persistence.paper_account_repository import (
    PaperAccountRepository,
    SqlAlchemyPaperAccountRepository,
)
from el_psy_quant.persistence.paper_accounts import (
    PAPER_ACCOUNT_PERSISTENCE_RECORD_SCHEMA_VERSION,
    PAPER_ACCOUNT_RECORD_SCHEMA_VERSION,
    PaperAccountApprovedEvidenceError,
    PaperAccountCommandResult,
    PaperAccountConcurrencyConflictError,
    PaperAccountCreationKeyRecord,
    PaperAccountIdempotencyConflictError,
    PaperAccountNotFoundError,
    PaperAccountOperationConflictError,
    PaperAccountPersistenceCorruptionError,
    PaperAccountProjectionReconciliationRequiredError,
    PaperAccountReconciliationResult,
    PaperAccountRecord,
    PaperAccountSnapshotResult,
    PaperAccountStorageBusyError,
    PaperAccountVersionConflictError,
)
from el_psy_quant.persistence.paper_jobs import (
    PaperJobRecord,
    PaperJobStatus,
    PreparedPaperRunRequest,
    create_queued_paper_job_record,
    digest_prepared_paper_run_request,
    deserialize_paper_run_request,
    prepare_paper_run_request_for_persistence,
    serialize_paper_run_request,
    transition_paper_job_record,
)
from el_psy_quant.persistence.portfolio_review_repository import (
    PortfolioReviewRepository,
    SqlAlchemyPortfolioReviewRepository,
)
from el_psy_quant.persistence.portfolio_reviews import (
    PORTFOLIO_REVIEW_LIST_LIMIT_MAXIMUM,
    PORTFOLIO_REVIEW_RECORD_SCHEMA_VERSION,
    PortfolioReviewRecord,
    PortfolioReviewStatus,
    create_awaiting_portfolio_review_record,
    digest_portfolio_review_command,
    validate_portfolio_review_idempotency_key,
)
from el_psy_quant.persistence.session import create_product_session_factory

__all__ = [
    "ArtifactIndexEntry",
    "ArtifactIndexRepository",
    "MARKET_TIME_PERSISTENCE_RECORD_SCHEMA_VERSION",
    "MarketDataReplayRecord",
    "MarketTimeRepository",
    "PAPER_ACCOUNT_PERSISTENCE_RECORD_SCHEMA_VERSION",
    "PAPER_ACCOUNT_RECORD_SCHEMA_VERSION",
    "PaperAccountApprovedEvidenceError",
    "PaperAccountCommandResult",
    "PaperAccountConcurrencyConflictError",
    "PaperAccountCreationKeyRecord",
    "PaperAccountIdempotencyConflictError",
    "PaperAccountNotFoundError",
    "PaperAccountOperationConflictError",
    "PaperAccountPersistenceCorruptionError",
    "PaperAccountProjectionReconciliationRequiredError",
    "PaperAccountReconciliationResult",
    "PaperAccountRecord",
    "PaperAccountRepository",
    "PaperAccountSnapshotResult",
    "PaperAccountStorageBusyError",
    "PaperAccountVersionConflictError",
    "PaperJobRecord",
    "PaperJobAttemptRecord",
    "PaperJobAttemptRepository",
    "PaperJobAttemptStatus",
    "PaperJobErrorCode",
    "PaperJobRepository",
    "PaperJobResultReference",
    "PaperJobResultReferenceRepository",
    "PaperJobStatus",
    "PaperJobSubmissionKeyRecord",
    "PaperJobSubmissionKeyRepository",
    "PreparedPaperRunRequest",
    "PortfolioReviewRecord",
    "PortfolioReviewRepository",
    "PortfolioReviewStatus",
    "PORTFOLIO_REVIEW_LIST_LIMIT_MAXIMUM",
    "PORTFOLIO_REVIEW_RECORD_SCHEMA_VERSION",
    "ProductDatabaseConfig",
    "ProductPersistenceBase",
    "SqlAlchemyArtifactIndexRepository",
    "SqlAlchemyMarketTimeRepository",
    "SqlAlchemyPaperAccountRepository",
    "SqlAlchemyPaperJobAttemptRepository",
    "SqlAlchemyPaperJobRepository",
    "SqlAlchemyPaperJobResultReferenceRepository",
    "SqlAlchemyPaperJobSubmissionKeyRepository",
    "SqlAlchemyPortfolioReviewRepository",
    "complete_paper_job_attempt",
    "create_artifact_index_entry",
    "create_market_data_replay_record",
    "create_product_database_engine",
    "create_product_session_factory",
    "create_awaiting_portfolio_review_record",
    "create_queued_paper_job_record",
    "create_paper_job_submission_key_record",
    "create_paper_job_result_reference",
    "create_running_paper_job_attempt",
    "deserialize_paper_run_request",
    "digest_portfolio_review_command",
    "digest_prepared_paper_run_request",
    "prepare_paper_run_request_for_persistence",
    "resolve_product_database_config",
    "serialize_paper_run_request",
    "transition_paper_job_record",
    "validate_paper_job_idempotency_key",
    "validate_portfolio_review_idempotency_key",
]
