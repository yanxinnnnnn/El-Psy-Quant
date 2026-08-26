"""M35 persistence errors and bounded record constants."""

PAPER_RUNTIME_PERSISTENCE_RECORD_SCHEMA_VERSION = 1
PAPER_RUNTIME_LIST_LIMIT_MAXIMUM = 200


class PaperRuntimeNotFoundError(Exception):
    """Requested M35 runtime evidence does not exist."""


class PaperRuntimePersistenceCorruptionError(Exception):
    """M35 or cross-authority durable evidence is corrupt or cross-wired."""


class PaperRuntimeConcurrencyConflictError(Exception):
    """An exact runtime compare-and-swap loser made no durable change."""


class PaperRuntimeStorageBusyError(Exception):
    """SQLite could not grant the one-winner runtime transaction."""


class PaperRuntimeStorageFailureError(Exception):
    """Durable runtime storage failed without exposing implementation details."""


__all__ = [
    "PAPER_RUNTIME_LIST_LIMIT_MAXIMUM",
    "PAPER_RUNTIME_PERSISTENCE_RECORD_SCHEMA_VERSION",
    "PaperRuntimeConcurrencyConflictError",
    "PaperRuntimeNotFoundError",
    "PaperRuntimePersistenceCorruptionError",
    "PaperRuntimeStorageBusyError",
    "PaperRuntimeStorageFailureError",
]
