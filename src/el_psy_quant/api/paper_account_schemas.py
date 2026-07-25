"""Strict public request and response contracts for M31 Paper Accounts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    field_validator,
)

PaperAccountLifecycleStatus = Literal["active", "frozen", "closed"]
PaperAccountProjectionStatus = Literal["current", "reconciliation_required"]
PaperAccountEventType = Literal[
    "account_created",
    "cash_movement_posted",
    "position_adjustment_posted",
    "portfolio_review_evidence_linked",
    "account_frozen",
    "account_reactivated",
    "account_closed",
]
PaperCashMovementRequestType = Literal[
    "deposit",
    "withdrawal",
    "manual_adjustment",
    "fee",
    "commission",
    "tax",
]
PaperCashMovementType = Literal[
    "initial_cash",
    "deposit",
    "withdrawal",
    "manual_adjustment",
    "fee",
    "commission",
    "tax",
]
PaperPositionAdjustmentCategory = Literal[
    "opening_balance",
    "manual_correction",
    "corporate_action",
    "other",
]
PaperAccountLifecycleAction = Literal["freeze", "reactivate", "close"]
PaperAccountReconciliationOutcome = Literal["matched", "mismatched"]
PaperAccountProjectionMismatchCode = Literal[
    "source_account_version_mismatch",
    "source_event_id_mismatch",
    "source_chain_digest_mismatch",
    "identity_mismatch",
    "lifecycle_status_mismatch",
    "cash_balance_mismatch",
    "available_cash_mismatch",
    "positions_mismatch",
    "evidence_references_mismatch",
]
ExactPositiveInt = Annotated[StrictInt, Field(gt=0)]
ExactNonNegativeInt = Annotated[StrictInt, Field(ge=0)]
CanonicalDecimalInput = StrictStr
BoundedAccountIdInput = Annotated[
    StrictStr,
    Field(min_length=1, max_length=512, pattern=r"^\S(?:.*\S)?$"),
]
BoundedActorInput = Annotated[
    StrictStr,
    Field(min_length=1, max_length=512, pattern=r"^\S(?:.*\S)?$"),
]
BoundedReasonInput = Annotated[
    StrictStr,
    Field(min_length=1, max_length=2000, pattern=r"^\S(?:.*\S)?$"),
]
Sha256DigestInput = Annotated[
    StrictStr,
    Field(pattern=r"^[0-9a-f]{64}$"),
]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


def _normalized_utc_input(value: object) -> object:
    if value is None:
        return None
    if type(value) is not str:
        raise ValueError("timestamp must be an ISO-8601 UTC string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        offset = parsed.utcoffset()
    except (OverflowError, ValueError) as exc:
        raise ValueError("timestamp must be an ISO-8601 UTC string") from exc
    if (
        parsed.tzinfo is None
        or offset is None
        or offset.total_seconds() != 0
    ):
        raise ValueError("timestamp must be an ISO-8601 UTC string")
    return parsed.astimezone(timezone.utc)


class PaperAccountCreateRequest(_StrictModel):
    display_name: Annotated[
        StrictStr,
        Field(min_length=1, max_length=200, pattern=r"^\S(?:.*\S)?$"),
    ]
    base_currency: Annotated[
        StrictStr,
        Field(pattern=r"^[A-Za-z]{3}$"),
    ]
    initial_cash: CanonicalDecimalInput
    actor: BoundedActorInput


class PaperAccountCashMovementRequest(_StrictModel):
    expected_account_version: ExactPositiveInt
    actor: BoundedActorInput
    reason: BoundedReasonInput
    movement_type: PaperCashMovementRequestType
    requested_amount: CanonicalDecimalInput
    effective_timestamp_utc: datetime | None = None

    _validate_effective_timestamp = field_validator(
        "effective_timestamp_utc",
        mode="before",
    )(_normalized_utc_input)


class PaperAccountPositionAdjustmentRequest(_StrictModel):
    expected_account_version: ExactPositiveInt
    actor: BoundedActorInput
    reason: BoundedReasonInput
    symbol: Annotated[
        StrictStr,
        Field(min_length=1, max_length=128, pattern=r"^\S(?:.*\S)?$"),
    ]
    adjustment_category: PaperPositionAdjustmentCategory
    signed_quantity_delta: CanonicalDecimalInput
    signed_cost_basis_delta: CanonicalDecimalInput
    effective_timestamp_utc: datetime | None = None

    _validate_effective_timestamp = field_validator(
        "effective_timestamp_utc",
        mode="before",
    )(_normalized_utc_input)


class PaperAccountEvidenceLinkRequest(_StrictModel):
    expected_account_version: ExactPositiveInt
    actor: BoundedActorInput
    reason: BoundedReasonInput
    review_id: BoundedAccountIdInput


class PaperAccountLifecycleRequest(_StrictModel):
    expected_account_version: ExactPositiveInt
    actor: BoundedActorInput
    reason: BoundedReasonInput
    action: PaperAccountLifecycleAction


class PaperAccountEvidenceOperationRequest(_StrictModel):
    expected_account_version: ExactPositiveInt
    expected_head_event_id: BoundedAccountIdInput
    expected_head_chain_digest: Sha256DigestInput
    actor: BoundedActorInput
    reason: BoundedReasonInput


class PaperAccountIdentityResponse(_StrictModel):
    schema_version: Literal[1]
    account_id: str
    display_name: str
    base_currency: str
    created_by: str
    created_timestamp: datetime


class ApprovedPortfolioReviewReferenceResponse(_StrictModel):
    schema_version: Literal[1]
    review_id: str
    source_id: str
    source_digest: str
    analysis_digest: str
    decision_id: str
    decision_digest: str
    outcome: Literal["approved"]


class PaperAccountPositionProjectionResponse(_StrictModel):
    schema_version: Literal[1]
    symbol: str
    quantity: str
    aggregate_cost_basis: str
    average_unit_cost: str | None
    average_unit_cost_is_rounded: bool


class PaperAccountProjectionResponse(_StrictModel):
    schema_version: Literal[1]
    account_identity: PaperAccountIdentityResponse
    lifecycle_status: PaperAccountLifecycleStatus
    cash_balance: str
    available_cash: str
    positions: list[PaperAccountPositionProjectionResponse]
    approved_portfolio_reviews: list[
        ApprovedPortfolioReviewReferenceResponse
    ]
    source_account_version: ExactPositiveInt
    source_event_id: str
    source_chain_digest: str
    projection_digest: str


class PaperAccountSummaryResponse(_StrictModel):
    record_schema_version: Literal[1]
    account_id: str
    display_name: str
    base_currency: str
    lifecycle_status: PaperAccountLifecycleStatus
    head_version: ExactPositiveInt
    head_event_id: str
    head_chain_digest: str
    projection_status: PaperAccountProjectionStatus
    created_by: str
    created_timestamp: datetime
    updated_timestamp: datetime
    closed_timestamp: datetime | None


class PaperAccountCreatedDetailsResponse(_StrictModel):
    details_type: Literal["account_created"]
    account_identity: PaperAccountIdentityResponse
    initial_cash: str
    initial_lifecycle_status: Literal["active"]


class PaperCashMovementPostedDetailsResponse(_StrictModel):
    details_type: Literal["cash_movement_posted"]
    movement_type: PaperCashMovementRequestType
    requested_amount: str


class PaperPositionAdjustmentPostedDetailsResponse(_StrictModel):
    details_type: Literal["position_adjustment_posted"]
    symbol: str
    adjustment_category: PaperPositionAdjustmentCategory
    signed_quantity_delta: str
    signed_cost_basis_delta: str


class PaperPortfolioReviewLinkedDetailsResponse(_StrictModel):
    details_type: Literal["portfolio_review_evidence_linked"]
    approved_portfolio_review: ApprovedPortfolioReviewReferenceResponse


class PaperAccountLifecycleChangedDetailsResponse(_StrictModel):
    details_type: Literal["lifecycle_changed"]
    source_status: PaperAccountLifecycleStatus
    target_status: PaperAccountLifecycleStatus


PaperAccountEventDetailsResponse = Annotated[
    PaperAccountCreatedDetailsResponse
    | PaperCashMovementPostedDetailsResponse
    | PaperPositionAdjustmentPostedDetailsResponse
    | PaperPortfolioReviewLinkedDetailsResponse
    | PaperAccountLifecycleChangedDetailsResponse,
    Field(discriminator="details_type"),
]


class PaperCashPostingResponse(_StrictModel):
    schema_version: Literal[1]
    cash_entry_id: str
    account_id: str
    event_id: str
    entry_index: ExactNonNegativeInt
    movement_type: PaperCashMovementType
    currency: str
    signed_amount: str
    entry_digest: str


class PaperPositionPostingResponse(_StrictModel):
    schema_version: Literal[1]
    position_entry_id: str
    account_id: str
    event_id: str
    entry_index: ExactNonNegativeInt
    symbol: str
    signed_quantity_delta: str
    signed_cost_basis_delta: str
    adjustment_category: PaperPositionAdjustmentCategory
    entry_digest: str


class PaperAccountLedgerEventResponse(_StrictModel):
    schema_version: Literal[1]
    event_id: str
    account_id: str
    sequence_number: ExactPositiveInt
    account_version: ExactPositiveInt
    event_type: PaperAccountEventType
    command_digest: str
    expected_account_version: ExactPositiveInt | None
    actor: str
    reason: str | None
    recorded_timestamp_utc: datetime
    effective_timestamp_utc: datetime | None
    previous_chain_digest: str
    details: PaperAccountEventDetailsResponse
    event_digest: str
    chain_digest: str
    cash_postings: list[PaperCashPostingResponse]
    position_postings: list[PaperPositionPostingResponse]


class PaperAccountListResponse(_StrictModel):
    schema_version: Literal[1]
    items: list[PaperAccountSummaryResponse]
    next_cursor: str | None


class PaperAccountDetailResponse(_StrictModel):
    schema_version: Literal[1]
    account: PaperAccountSummaryResponse
    projection: PaperAccountProjectionResponse


class PaperAccountLedgerResponse(_StrictModel):
    schema_version: Literal[1]
    events: list[PaperAccountLedgerEventResponse]
    next_after_sequence_number: ExactPositiveInt | None


class PaperAccountCommandResponse(_StrictModel):
    schema_version: Literal[1]
    replayed: bool
    request_id: str
    account: PaperAccountSummaryResponse
    event: PaperAccountLedgerEventResponse
    projection: PaperAccountProjectionResponse


class PaperAccountSnapshotResponse(_StrictModel):
    schema_version: Literal[1]
    snapshot_id: str
    account_id: str
    account_version: ExactPositiveInt
    head_event_id: str
    head_chain_digest: str
    operation_command_digest: str
    created_by: str
    recorded_timestamp_utc: datetime
    reason: str
    projection: PaperAccountProjectionResponse
    snapshot_digest: str


class PaperAccountSnapshotCommandResponse(_StrictModel):
    schema_version: Literal[1]
    replayed: bool
    request_id: str
    snapshot: PaperAccountSnapshotResponse


class PaperAccountReconciliationResponse(_StrictModel):
    schema_version: Literal[1]
    reconciliation_id: str
    account_id: str
    operation_command_digest: str
    created_by: str
    recorded_timestamp_utc: datetime
    reason: str
    outcome: PaperAccountReconciliationOutcome
    mismatch_codes: list[PaperAccountProjectionMismatchCode]
    authoritative_account_version: ExactPositiveInt
    authoritative_event_id: str
    authoritative_chain_digest: str
    authoritative_projection_digest: str
    candidate_account_version: ExactPositiveInt
    candidate_event_id: str
    candidate_chain_digest: str
    candidate_projection_digest: str
    reconciliation_digest: str


class PaperAccountReconciliationCommandResponse(_StrictModel):
    schema_version: Literal[1]
    replayed: bool
    request_id: str
    reconciliation: PaperAccountReconciliationResponse


__all__ = [
    "PaperAccountCashMovementRequest",
    "PaperAccountCommandResponse",
    "PaperAccountCreateRequest",
    "PaperAccountDetailResponse",
    "PaperAccountEvidenceLinkRequest",
    "PaperAccountEvidenceOperationRequest",
    "PaperAccountLedgerResponse",
    "PaperAccountLifecycleRequest",
    "PaperAccountListResponse",
    "PaperAccountPositionAdjustmentRequest",
    "PaperAccountReconciliationCommandResponse",
    "PaperAccountSnapshotCommandResponse",
]
