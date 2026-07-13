"""Internal SQLAlchemy model for durable paper-job operational input."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from el_psy_quant.persistence.base import ProductPersistenceBase


class PaperJobRow(ProductPersistenceBase):
    """Internal persisted representation of one paper job."""

    __tablename__ = "paper_jobs"
    __table_args__ = (
        PrimaryKeyConstraint("job_id", name="pk_paper_jobs"),
        UniqueConstraint("run_id", name="uq_paper_jobs_run_id"),
        CheckConstraint(
            "record_schema_version = 1",
            name="ck_paper_jobs_record_schema_version",
        ),
        CheckConstraint(
            "request_schema_version = 1",
            name="ck_paper_jobs_request_schema_version",
        ),
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'canceled')",
            name="ck_paper_jobs_status",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(nullable=False)
    job_id: Mapped[str] = mapped_column(String(36), nullable=False)
    run_id: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    request_schema_version: Mapped[int] = mapped_column(nullable=False)
    request_payload: Mapped[str] = mapped_column(Text(), nullable=False)
    submitted_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
