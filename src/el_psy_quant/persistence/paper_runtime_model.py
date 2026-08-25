"""Internal SQLAlchemy rows for the M35 durable runtime foundation."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from el_psy_quant.persistence.base import ProductPersistenceBase

_DIGEST = "length({0}) = 64 AND {0} NOT GLOB '*[^0-9a-f]*'"


class PaperRuntimeRow(ProductPersistenceBase):
    __tablename__ = "paper_runtimes"
    __table_args__ = (
        PrimaryKeyConstraint("runtime_id", name="pk_paper_runtimes"),
        UniqueConstraint("runtime_binding_digest", name="uq_paper_runtimes_binding"),
        UniqueConstraint("execution_order_id", name="uq_paper_runtimes_order"),
        ForeignKeyConstraint(
            ("execution_order_id",),
            ("paper_execution_orders.execution_order_id",),
            name="fk_paper_runtimes_order",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("account_id",),
            ("paper_accounts.account_id",),
            name="fk_paper_runtimes_account",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("replay_id",),
            ("market_data_replays.replay_id",),
            name="fk_paper_runtimes_replay",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("trading_session_id",),
            ("trading_sessions.session_id",),
            name="fk_paper_runtimes_session",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "record_schema_version = 1 AND runtime_schema_version = 1",
            name="ck_paper_runtimes_versions",
        ),
        CheckConstraint(
            _DIGEST.format("runtime_binding_digest"),
            name="ck_paper_runtimes_binding_digest",
        ),
        CheckConstraint(
            _DIGEST.format("execution_order_digest"),
            name="ck_paper_runtimes_order_digest",
        ),
        CheckConstraint(
            "runtime_policy_version >= 0 AND fencing_token >= 0 AND row_version >= 0",
            name="ck_paper_runtimes_nonnegative",
        ),
        CheckConstraint(
            "desired_state IN ('running','stopped')", name="ck_paper_runtimes_desired"
        ),
        CheckConstraint(
            "observed_state IN ('ready','running','stopped','completed','blocked')",
            name="ck_paper_runtimes_observed",
        ),
        CheckConstraint(
            "(owner_id IS NULL AND claimed_at IS NULL AND heartbeat_at IS NULL AND lease_expires_at IS NULL) OR (owner_id IS NOT NULL AND claimed_at IS NOT NULL AND heartbeat_at IS NOT NULL AND lease_expires_at IS NOT NULL)",
            name="ck_paper_runtimes_owner_group",
        ),
        CheckConstraint(
            "(observed_state = 'blocked' AND block_reason_code IS NOT NULL AND length(block_reason_code) > 0) OR (observed_state <> 'blocked' AND block_reason_code IS NULL)",
            name="ck_paper_runtimes_block_reason",
        ),
        Index(
            "ix_paper_runtimes_binding", "account_id", "replay_id", "trading_session_id"
        ),
        Index(
            "ix_paper_runtimes_state", "desired_state", "observed_state", "updated_at"
        ),
    )
    record_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    runtime_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    runtime_id: Mapped[str] = mapped_column(String(96), nullable=False)
    runtime_binding_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text(), nullable=False)
    execution_order_id: Mapped[str] = mapped_column(String(96), nullable=False)
    execution_order_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    account_id: Mapped[str] = mapped_column(String(512), nullable=False)
    replay_id: Mapped[str] = mapped_column(String(512), nullable=False)
    trading_session_id: Mapped[str] = mapped_column(String(512), nullable=False)
    logical_actor: Mapped[str] = mapped_column(String(256), nullable=False)
    runtime_policy_id: Mapped[str] = mapped_column(String(128), nullable=False)
    runtime_policy_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    desired_state: Mapped[str] = mapped_column(String(16), nullable=False)
    observed_state: Mapped[str] = mapped_column(String(16), nullable=False)
    owner_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    fencing_token: Mapped[int] = mapped_column(Integer(), nullable=False)
    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    row_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    block_reason_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class PaperRuntimeWorkRow(ProductPersistenceBase):
    __tablename__ = "paper_runtime_work"
    __table_args__ = (
        PrimaryKeyConstraint("work_id", name="pk_paper_runtime_work"),
        UniqueConstraint("work_digest", name="uq_paper_runtime_work_digest"),
        UniqueConstraint(
            "m34_step_idempotency_key", name="uq_paper_runtime_work_step_key"
        ),
        UniqueConstraint(
            "runtime_id",
            "expected_execution_version",
            name="uq_paper_runtime_work_version",
        ),
        ForeignKeyConstraint(
            ("runtime_id",),
            ("paper_runtimes.runtime_id",),
            name="fk_paper_runtime_work_runtime",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("execution_order_id",),
            ("paper_execution_orders.execution_order_id",),
            name="fk_paper_runtime_work_order",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "record_schema_version = 1 AND work_schema_version = 1",
            name="ck_paper_runtime_work_versions",
        ),
        CheckConstraint(
            _DIGEST.format("work_digest"), name="ck_paper_runtime_work_digest"
        ),
        CheckConstraint(
            _DIGEST.format("execution_order_digest"),
            name="ck_paper_runtime_work_order_digest",
        ),
        CheckConstraint(
            "expected_execution_version >= 0",
            name="ck_paper_runtime_work_execution_version",
        ),
        Index(
            "ix_paper_runtime_work_runtime", "runtime_id", "expected_execution_version"
        ),
    )
    record_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    work_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    work_id: Mapped[str] = mapped_column(String(96), nullable=False)
    work_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text(), nullable=False)
    runtime_id: Mapped[str] = mapped_column(String(96), nullable=False)
    execution_order_id: Mapped[str] = mapped_column(String(96), nullable=False)
    execution_order_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    expected_execution_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    m34_step_idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    m34_step_actor: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class PaperRuntimeCheckpointRow(ProductPersistenceBase):
    __tablename__ = "paper_runtime_checkpoints"
    __table_args__ = (
        PrimaryKeyConstraint("checkpoint_id", name="pk_paper_runtime_checkpoints"),
        UniqueConstraint(
            "checkpoint_digest", name="uq_paper_runtime_checkpoints_digest"
        ),
        UniqueConstraint("work_id", name="uq_paper_runtime_checkpoints_work"),
        UniqueConstraint(
            "runtime_id",
            "observed_execution_version",
            name="uq_paper_runtime_checkpoints_version",
        ),
        ForeignKeyConstraint(
            ("runtime_id",),
            ("paper_runtimes.runtime_id",),
            name="fk_paper_runtime_checkpoints_runtime",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("work_id",),
            ("paper_runtime_work.work_id",),
            name="fk_paper_runtime_checkpoints_work",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("execution_order_id",),
            ("paper_execution_orders.execution_order_id",),
            name="fk_paper_runtime_checkpoints_order",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("attempt_id",),
            ("paper_execution_attempts.attempt_id",),
            name="fk_paper_runtime_checkpoints_attempt",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("fill_id",),
            ("paper_execution_fills.fill_id",),
            name="fk_paper_runtime_checkpoints_fill",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("settlement_link_id",),
            ("paper_execution_settlement_links.settlement_link_id",),
            name="fk_paper_runtime_checkpoints_link",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("account_event_id",),
            ("paper_account_events.event_id",),
            name="fk_paper_runtime_checkpoints_account_event",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("replay_id",),
            ("market_data_replays.replay_id",),
            name="fk_paper_runtime_checkpoints_replay",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "record_schema_version = 1 AND checkpoint_schema_version = 1",
            name="ck_paper_runtime_checkpoints_versions",
        ),
        CheckConstraint(
            _DIGEST.format("checkpoint_digest"),
            name="ck_paper_runtime_checkpoints_digest",
        ),
        CheckConstraint(
            _DIGEST.format("execution_order_digest"),
            name="ck_paper_runtime_checkpoints_order_digest",
        ),
        CheckConstraint(
            _DIGEST.format("attempt_digest"),
            name="ck_paper_runtime_checkpoints_attempt_digest",
        ),
        CheckConstraint(
            _DIGEST.format("event_stream_digest"),
            name="ck_paper_runtime_checkpoints_stream_digest",
        ),
        CheckConstraint(
            "observed_execution_version >= 1 AND post_cursor_position >= 0",
            name="ck_paper_runtime_checkpoints_nonnegative",
        ),
        CheckConstraint(
            "(fill_id IS NULL AND fill_digest IS NULL AND settlement_link_id IS NULL AND settlement_link_evidence_digest IS NULL AND account_event_id IS NULL) OR (fill_id IS NOT NULL AND fill_digest IS NOT NULL AND settlement_link_id IS NOT NULL AND settlement_link_evidence_digest IS NOT NULL AND account_event_id IS NOT NULL)",
            name="ck_paper_runtime_checkpoints_optional_group",
        ),
        CheckConstraint(
            "fill_digest IS NULL OR (" + _DIGEST.format("fill_digest") + ")",
            name="ck_paper_runtime_checkpoints_fill_digest",
        ),
        CheckConstraint(
            "settlement_link_evidence_digest IS NULL OR ("
            + _DIGEST.format("settlement_link_evidence_digest")
            + ")",
            name="ck_paper_runtime_checkpoints_link_digest",
        ),
        Index(
            "ix_paper_runtime_checkpoints_runtime",
            "runtime_id",
            "observed_execution_version",
        ),
    )
    record_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    checkpoint_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    checkpoint_id: Mapped[str] = mapped_column(String(96), nullable=False)
    checkpoint_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text(), nullable=False)
    runtime_id: Mapped[str] = mapped_column(String(96), nullable=False)
    work_id: Mapped[str] = mapped_column(String(96), nullable=False)
    execution_order_id: Mapped[str] = mapped_column(String(96), nullable=False)
    execution_order_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    observed_execution_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    attempt_id: Mapped[str] = mapped_column(String(96), nullable=False)
    attempt_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    fill_id: Mapped[str | None] = mapped_column(String(96), nullable=True)
    fill_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    settlement_link_id: Mapped[str | None] = mapped_column(String(96), nullable=True)
    settlement_link_evidence_digest: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    account_event_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    replay_id: Mapped[str] = mapped_column(String(512), nullable=False)
    event_stream_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    post_cursor_position: Mapped[int] = mapped_column(Integer(), nullable=False)
    post_cursor_last_event_id: Mapped[str | None] = mapped_column(
        String(512), nullable=True
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class PaperRuntimeEventRow(ProductPersistenceBase):
    __tablename__ = "paper_runtime_events"
    __table_args__ = (
        PrimaryKeyConstraint("event_id", name="pk_paper_runtime_events"),
        UniqueConstraint("event_digest", name="uq_paper_runtime_events_digest"),
        UniqueConstraint(
            "runtime_id", "event_sequence", name="uq_paper_runtime_events_sequence"
        ),
        ForeignKeyConstraint(
            ("runtime_id",),
            ("paper_runtimes.runtime_id",),
            name="fk_paper_runtime_events_runtime",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "record_schema_version = 1 AND event_schema_version = 1",
            name="ck_paper_runtime_events_versions",
        ),
        CheckConstraint(
            _DIGEST.format("event_digest"), name="ck_paper_runtime_events_digest"
        ),
        CheckConstraint(
            "event_sequence >= 0 AND resulting_runtime_version >= 0",
            name="ck_paper_runtime_events_nonnegative",
        ),
        CheckConstraint(
            "event_type IN ('runtime_created','start_requested','stop_requested','resume_requested','recover_requested','claim_acquired','claim_released','claim_taken_over','work_created','work_observed','runtime_completed','runtime_blocked')",
            name="ck_paper_runtime_events_type",
        ),
        Index("ix_paper_runtime_events_runtime", "runtime_id", "event_sequence"),
    )
    record_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    event_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    event_id: Mapped[str] = mapped_column(String(96), nullable=False)
    event_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    runtime_id: Mapped[str] = mapped_column(String(96), nullable=False)
    event_sequence: Mapped[int] = mapped_column(Integer(), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    resulting_runtime_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text(), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class PaperRuntimeCommandReceiptRow(ProductPersistenceBase):
    __tablename__ = "paper_runtime_command_receipts"
    __table_args__ = (
        PrimaryKeyConstraint(
            "namespace",
            "command_idempotency_key",
            name="pk_paper_runtime_command_receipts",
        ),
        UniqueConstraint(
            "namespace",
            "command_digest",
            name="uq_paper_runtime_command_receipts_digest",
        ),
        ForeignKeyConstraint(
            ("runtime_id",),
            ("paper_runtimes.runtime_id",),
            name="fk_paper_runtime_receipts_runtime",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("result_event_id",),
            ("paper_runtime_events.event_id",),
            name="fk_paper_runtime_receipts_event",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "record_schema_version = 1 AND receipt_schema_version = 1",
            name="ck_paper_runtime_receipts_versions",
        ),
        CheckConstraint(
            "namespace IN ('create_paper_runtime','start_paper_runtime','stop_paper_runtime','resume_paper_runtime','recover_paper_runtime')",
            name="ck_paper_runtime_receipts_namespace",
        ),
        CheckConstraint(
            _DIGEST.format("command_digest"),
            name="ck_paper_runtime_receipts_command_digest",
        ),
        CheckConstraint(
            _DIGEST.format("result_event_digest"),
            name="ck_paper_runtime_receipts_event_digest",
        ),
        CheckConstraint(
            "resulting_runtime_version >= 0",
            name="ck_paper_runtime_receipts_version_nonnegative",
        ),
        Index("ix_paper_runtime_receipts_result", "runtime_id", "result_event_id"),
    )
    record_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    receipt_schema_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    namespace: Mapped[str] = mapped_column(String(64), nullable=False)
    command_idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    command_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    command_actor: Mapped[str] = mapped_column(String(256), nullable=False)
    runtime_id: Mapped[str] = mapped_column(String(96), nullable=False)
    result_event_id: Mapped[str] = mapped_column(String(96), nullable=False)
    result_event_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    resulting_runtime_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


__all__ = [
    "PaperRuntimeCheckpointRow",
    "PaperRuntimeCommandReceiptRow",
    "PaperRuntimeEventRow",
    "PaperRuntimeRow",
    "PaperRuntimeWorkRow",
]
