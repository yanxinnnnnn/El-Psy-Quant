"""Internal SQLAlchemy model for paper-job execution attempts."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from el_psy_quant.persistence.base import ProductPersistenceBase


class PaperJobAttemptRow(ProductPersistenceBase):
    """Internal persisted representation of one execution attempt."""

    __tablename__ = "paper_job_attempts"
    __table_args__ = (
        PrimaryKeyConstraint("attempt_id", name="pk_paper_job_attempts"),
        UniqueConstraint(
            "job_id",
            "attempt_number",
            name="uq_paper_job_attempts_job_number",
        ),
        CheckConstraint(
            "record_schema_version = 1",
            name="ck_paper_job_attempts_record_schema_version",
        ),
        CheckConstraint(
            "attempt_number >= 1",
            name="ck_paper_job_attempts_number",
        ),
        CheckConstraint(
            "status IN ('running', 'succeeded', 'failed', 'interrupted')",
            name="ck_paper_job_attempts_status",
        ),
        CheckConstraint(
            "error_code IS NULL OR error_code IN ("
            "'workflow_validation_failed', 'output_conflict', "
            "'filesystem_io_failed', 'interrupted_without_output', "
            "'partial_output_detected', 'invalid_output_detected')",
            name="ck_paper_job_attempts_error_code",
        ),
        CheckConstraint(
            "(status = 'running' AND completed_timestamp IS NULL "
            "AND error_code IS NULL) OR "
            "(status = 'succeeded' AND completed_timestamp IS NOT NULL "
            "AND error_code IS NULL) OR "
            "(status IN ('failed', 'interrupted') "
            "AND completed_timestamp IS NOT NULL AND error_code IS NOT NULL)",
            name="ck_paper_job_attempts_state_fields",
        ),
        CheckConstraint(
            "completed_timestamp IS NULL OR completed_timestamp >= started_timestamp",
            name="ck_paper_job_attempts_timestamp_order",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(nullable=False)
    attempt_id: Mapped[str] = mapped_column(String(36), nullable=False)
    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("paper_jobs.job_id", ondelete="RESTRICT"),
        nullable=False,
    )
    attempt_number: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    started_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
