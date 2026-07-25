"""Canonical installed-package authority for product migration resources."""

from __future__ import annotations

from importlib import resources
from pathlib import PurePosixPath

from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory

from el_psy_quant.persistence.schema import CURRENT_PRODUCT_SCHEMA_REVISION

ALEMBIC_SCRIPT_LOCATION = "el_psy_quant.persistence:migrations"
MIGRATION_RESOURCE_PACKAGE = "el_psy_quant.persistence"
MIGRATION_RESOURCE_DIRECTORY = "migrations"
MIGRATION_CHAIN = (
    "0001_product_baseline",
    "0002_artifact_index",
    "0003_paper_jobs",
    "0004_paper_job_recovery_audit",
    "0005_paper_job_result_references",
    "0006_portfolio_reviews",
    CURRENT_PRODUCT_SCHEMA_REVISION,
)
REQUIRED_MIGRATION_RESOURCE_PATHS = (
    "env.py",
    "script.py.mako",
    "versions/0001_product_persistence_baseline.py",
    "versions/0002_artifact_index.py",
    "versions/0003_paper_jobs.py",
    "versions/0004_paper_job_recovery_audit.py",
    "versions/0005_paper_job_result_references.py",
    "versions/0006_portfolio_reviews.py",
    "versions/0007_paper_account_ledger.py",
)
_REQUIRED_VERSION_FILES = tuple(
    PurePosixPath(path).name
    for path in REQUIRED_MIGRATION_RESOURCE_PATHS
    if path.startswith("versions/")
)


class MigrationResourceError(Exception):
    """Raised when the installed migration authority is unavailable or invalid."""


def _resource_child(root: resources.abc.Traversable, path: str):
    child = root
    for part in PurePosixPath(path).parts:
        child = child.joinpath(part)
    return child


def validate_migration_resources(config: AlembicConfig) -> ScriptDirectory:
    """Validate the exact packaged tree, linear chain, and one current head."""
    try:
        if config.get_alembic_option("script_location") != ALEMBIC_SCRIPT_LOCATION:
            raise MigrationResourceError(
                "Alembic script location is not the packaged migration authority"
            )

        root = resources.files(MIGRATION_RESOURCE_PACKAGE).joinpath(
            MIGRATION_RESOURCE_DIRECTORY
        )
        if not root.is_dir():
            raise MigrationResourceError("packaged migration directory is unavailable")
        for path in REQUIRED_MIGRATION_RESOURCE_PATHS:
            if not _resource_child(root, path).is_file():
                raise MigrationResourceError(
                    "packaged migration resources are incomplete"
                )

        versions = root.joinpath("versions")
        packaged_version_files = tuple(
            sorted(
                child.name
                for child in versions.iterdir()
                if child.is_file() and child.name.endswith(".py")
            )
        )
        if packaged_version_files != _REQUIRED_VERSION_FILES:
            raise MigrationResourceError(
                "packaged migration revisions do not match the approved tree"
            )

        scripts = ScriptDirectory.from_config(config)
        if tuple(scripts.get_heads()) != (CURRENT_PRODUCT_SCHEMA_REVISION,):
            raise MigrationResourceError(
                "packaged migration head does not match the product schema"
            )
        installed_chain = tuple(
            revision.revision
            for revision in scripts.walk_revisions(base="base", head="heads")
        )
        if installed_chain != tuple(reversed(MIGRATION_CHAIN)):
            raise MigrationResourceError(
                "packaged migration chain does not match the approved tree"
            )
        return scripts
    except MigrationResourceError:
        raise
    except Exception as exc:
        raise MigrationResourceError(
            "packaged migration resources could not be validated"
        ) from exc


__all__ = [
    "ALEMBIC_SCRIPT_LOCATION",
    "MIGRATION_CHAIN",
    "MIGRATION_RESOURCE_DIRECTORY",
    "MIGRATION_RESOURCE_PACKAGE",
    "MigrationResourceError",
    "REQUIRED_MIGRATION_RESOURCE_PATHS",
    "validate_migration_resources",
]
