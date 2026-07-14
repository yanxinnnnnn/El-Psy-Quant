"""Internal SQLAlchemy model for paper-job submission keys."""

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


class PaperJobSubmissionKeyRow(ProductPersistenceBase):
    """Internal persisted representation of one idempotency mapping."""

    __tablename__ = "paper_job_submission_keys"
    __table_args__ = (
        PrimaryKeyConstraint(
            "idempotency_key",
            name="pk_paper_job_submission_keys",
        ),
        UniqueConstraint("job_id", name="uq_paper_job_submission_keys_job_id"),
        CheckConstraint(
            "record_schema_version = 1",
            name="ck_paper_job_submission_keys_record_schema_version",
        ),
        CheckConstraint(
            "request_schema_version = 1",
            name="ck_paper_job_submission_keys_request_schema_version",
        ),
        CheckConstraint(
            "length(idempotency_key) BETWEEN 1 AND 128 "
            "AND idempotency_key NOT GLOB '*[^A-Za-z0-9._:-]*'",
            name="ck_paper_job_submission_keys_key",
        ),
        CheckConstraint(
            "length(request_digest) = 64 "
            "AND request_digest NOT GLOB '*[^0-9a-f]*'",
            name="ck_paper_job_submission_keys_digest",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("paper_jobs.job_id", ondelete="RESTRICT"),
        nullable=False,
    )
    request_schema_version: Mapped[int] = mapped_column(nullable=False)
    request_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    created_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
