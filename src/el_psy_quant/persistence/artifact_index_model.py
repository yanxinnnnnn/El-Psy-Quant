"""Internal SQLAlchemy model for the compact artifact index."""

from sqlalchemy import (
    CheckConstraint,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from el_psy_quant.persistence.base import ProductPersistenceBase


class ArtifactIndexRecord(ProductPersistenceBase):
    """Internal persisted representation of one artifact-index entry."""

    __tablename__ = "artifact_index_entries"
    __table_args__ = (
        PrimaryKeyConstraint(
            "artifact_type",
            "artifact_key",
            name="pk_artifact_index_entries",
        ),
        UniqueConstraint(
            "root_type",
            "relative_path",
            name="uq_artifact_index_root_locator",
        ),
        CheckConstraint(
            "record_schema_version = 1",
            name="ck_artifact_index_schema_version",
        ),
        CheckConstraint(
            "artifact_type IN ('research_run_manifest', "
            "'strategy_decision_manifest', 'report_artifact_manifest', "
            "'strategy_review_workflow_manifest')",
            name="ck_artifact_index_artifact_type",
        ),
        CheckConstraint(
            "root_type IN ('research', 'evidence')",
            name="ck_artifact_index_root_type",
        ),
        CheckConstraint(
            "(artifact_type = 'research_run_manifest' AND root_type = 'research') "
            "OR (artifact_type IN ('strategy_decision_manifest', "
            "'report_artifact_manifest', 'strategy_review_workflow_manifest') "
            "AND root_type = 'evidence')",
            name="ck_artifact_index_type_root_mapping",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_key: Mapped[str] = mapped_column(String(512), nullable=False)
    root_type: Mapped[str] = mapped_column(String(16), nullable=False)
    relative_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    source_id: Mapped[str] = mapped_column(String(512), nullable=False)
