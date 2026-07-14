"""Internal SQLAlchemy model for compact paper-job result references."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from el_psy_quant.persistence.base import ProductPersistenceBase


class PaperJobResultReferenceRow(ProductPersistenceBase):
    """Internal persisted representation of one result pointer."""

    __tablename__ = "paper_job_result_references"
    __table_args__ = (
        PrimaryKeyConstraint("job_id", name="pk_paper_job_result_references"),
        UniqueConstraint(
            "artifact_relative_path",
            name="uq_paper_job_result_references_artifact_path",
        ),
        UniqueConstraint(
            "result_summary_relative_path",
            name="uq_paper_job_result_references_summary_path",
        ),
        CheckConstraint(
            "record_schema_version = 1",
            name="ck_paper_job_result_references_record_schema_version",
        ),
        CheckConstraint(
            "root_type = 'paper'",
            name="ck_paper_job_result_references_root_type",
        ),
        CheckConstraint(
            "artifact_schema_version = 1",
            name="ck_paper_job_result_references_artifact_schema_version",
        ),
        CheckConstraint(
            "result_summary_schema_version = 1",
            name="ck_paper_job_result_references_summary_schema_version",
        ),
        CheckConstraint(
            "artifact_relative_path NOT LIKE '/%' "
            "AND artifact_relative_path NOT LIKE '%\\\\%' "
            "AND artifact_relative_path NOT LIKE '%/../%'",
            name="ck_paper_job_result_references_artifact_path_shape",
        ),
        CheckConstraint(
            "result_summary_relative_path NOT LIKE '/%' "
            "AND result_summary_relative_path NOT LIKE '%\\\\%' "
            "AND result_summary_relative_path NOT LIKE '%/../%'",
            name="ck_paper_job_result_references_summary_path_shape",
        ),
        ForeignKeyConstraint(
            ["job_id"],
            ["paper_jobs.job_id"],
            name="fk_paper_job_result_references_job_id_paper_jobs",
            ondelete="RESTRICT",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(nullable=False)
    job_id: Mapped[str] = mapped_column(String(36), nullable=False)
    root_type: Mapped[str] = mapped_column(String(16), nullable=False)
    artifact_schema_version: Mapped[int] = mapped_column(nullable=False)
    result_summary_schema_version: Mapped[int] = mapped_column(nullable=False)
    artifact_relative_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    result_summary_relative_path: Mapped[str] = mapped_column(
        String(1024), nullable=False
    )
    created_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
