import type { components } from "@/generated/api-types";

type Schemas = components["schemas"];
type Summary = Schemas["PaperAccountSummaryResponse"];
type Projection = Schemas["PaperAccountProjectionResponse"];
type LedgerEvent = Schemas["PaperAccountLedgerEventResponse"];
type ListResponse = Schemas["PaperAccountListResponse"];
type DetailResponse = Schemas["PaperAccountDetailResponse"];
type LedgerResponse = Schemas["PaperAccountLedgerResponse"];
type CommandResponse = Schemas["PaperAccountCommandResponse"];
type SnapshotCommandResponse =
  Schemas["PaperAccountSnapshotCommandResponse"];
type ReconciliationCommandResponse =
  Schemas["PaperAccountReconciliationCommandResponse"];

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function string(value: unknown): value is string {
  return typeof value === "string";
}

function nullableString(value: unknown): value is string | null {
  return value === null || string(value);
}

function integer(value: unknown): value is number {
  return Number.isInteger(value);
}

function positiveInteger(value: unknown): value is number {
  return integer(value) && (value as number) > 0;
}

function nonNegativeInteger(value: unknown): value is number {
  return integer(value) && (value as number) >= 0;
}

function boolean(value: unknown): value is boolean {
  return typeof value === "boolean";
}

function one(value: unknown): value is 1 {
  return value === 1;
}

function arrayOf(
  value: unknown,
  validator: (item: unknown) => boolean,
): value is unknown[] {
  return Array.isArray(value) && value.every(validator);
}

export function isPaperAccountLifecycleStatus(
  value: unknown,
): value is Summary["lifecycle_status"] {
  return value === "active" || value === "frozen" || value === "closed";
}

function projectionStatus(
  value: unknown,
): value is Summary["projection_status"] {
  return value === "current" || value === "reconciliation_required";
}

function identity(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.account_id) &&
    string(value.display_name) &&
    string(value.base_currency) &&
    string(value.created_by) &&
    string(value.created_timestamp)
  );
}

export function isPaperAccountSummary(value: unknown): value is Summary {
  return (
    object(value) &&
    one(value.record_schema_version) &&
    string(value.account_id) &&
    string(value.display_name) &&
    string(value.base_currency) &&
    isPaperAccountLifecycleStatus(value.lifecycle_status) &&
    positiveInteger(value.head_version) &&
    string(value.head_event_id) &&
    string(value.head_chain_digest) &&
    projectionStatus(value.projection_status) &&
    string(value.created_by) &&
    string(value.created_timestamp) &&
    string(value.updated_timestamp) &&
    nullableString(value.closed_timestamp)
  );
}

function approvedPortfolioReview(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.review_id) &&
    string(value.source_id) &&
    string(value.source_digest) &&
    string(value.analysis_digest) &&
    string(value.decision_id) &&
    string(value.decision_digest) &&
    value.outcome === "approved"
  );
}

function positionProjection(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.symbol) &&
    string(value.quantity) &&
    string(value.aggregate_cost_basis) &&
    nullableString(value.average_unit_cost) &&
    boolean(value.average_unit_cost_is_rounded)
  );
}

function projection(value: unknown): value is Projection {
  return (
    object(value) &&
    one(value.schema_version) &&
    identity(value.account_identity) &&
    isPaperAccountLifecycleStatus(value.lifecycle_status) &&
    string(value.cash_balance) &&
    string(value.available_cash) &&
    arrayOf(value.positions, positionProjection) &&
    arrayOf(value.approved_portfolio_reviews, approvedPortfolioReview) &&
    positiveInteger(value.source_account_version) &&
    string(value.source_event_id) &&
    string(value.source_chain_digest) &&
    string(value.projection_digest)
  );
}

function summaryProjectionBinding(
  summary: Summary,
  value: Projection,
): boolean {
  return (
    value.account_identity.account_id === summary.account_id &&
    value.account_identity.display_name === summary.display_name &&
    value.account_identity.base_currency === summary.base_currency &&
    value.account_identity.created_by === summary.created_by &&
    value.account_identity.created_timestamp === summary.created_timestamp &&
    value.lifecycle_status === summary.lifecycle_status &&
    value.source_account_version === summary.head_version &&
    value.source_event_id === summary.head_event_id &&
    value.source_chain_digest === summary.head_chain_digest
  );
}

function cashPosting(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.cash_entry_id) &&
    string(value.account_id) &&
    string(value.event_id) &&
    nonNegativeInteger(value.entry_index) &&
    (
      value.movement_type === "initial_cash" ||
      value.movement_type === "deposit" ||
      value.movement_type === "withdrawal" ||
      value.movement_type === "manual_adjustment" ||
      value.movement_type === "fee" ||
      value.movement_type === "commission" ||
      value.movement_type === "tax"
    ) &&
    string(value.currency) &&
    string(value.signed_amount) &&
    string(value.entry_digest)
  );
}

function positionPosting(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.position_entry_id) &&
    string(value.account_id) &&
    string(value.event_id) &&
    nonNegativeInteger(value.entry_index) &&
    string(value.symbol) &&
    string(value.signed_quantity_delta) &&
    string(value.signed_cost_basis_delta) &&
    (
      value.adjustment_category === "opening_balance" ||
      value.adjustment_category === "manual_correction" ||
      value.adjustment_category === "corporate_action" ||
      value.adjustment_category === "other"
    ) &&
    string(value.entry_digest)
  );
}

function eventDetails(value: unknown): boolean {
  if (!object(value) || !string(value.details_type)) {
    return false;
  }
  if (value.details_type === "account_created") {
    return (
      identity(value.account_identity) &&
      string(value.initial_cash) &&
      value.initial_lifecycle_status === "active"
    );
  }
  if (value.details_type === "cash_movement_posted") {
    return (
      (
        value.movement_type === "deposit" ||
        value.movement_type === "withdrawal" ||
        value.movement_type === "manual_adjustment" ||
        value.movement_type === "fee" ||
        value.movement_type === "commission" ||
        value.movement_type === "tax"
      ) &&
      string(value.requested_amount)
    );
  }
  if (value.details_type === "position_adjustment_posted") {
    return (
      string(value.symbol) &&
      (
        value.adjustment_category === "opening_balance" ||
        value.adjustment_category === "manual_correction" ||
        value.adjustment_category === "corporate_action" ||
        value.adjustment_category === "other"
      ) &&
      string(value.signed_quantity_delta) &&
      string(value.signed_cost_basis_delta)
    );
  }
  if (value.details_type === "portfolio_review_evidence_linked") {
    return approvedPortfolioReview(value.approved_portfolio_review);
  }
  if (value.details_type === "lifecycle_changed") {
    return (
      isPaperAccountLifecycleStatus(value.source_status) &&
      isPaperAccountLifecycleStatus(value.target_status)
    );
  }
  return false;
}

function eventType(value: unknown): boolean {
  return (
    value === "account_created" ||
    value === "cash_movement_posted" ||
    value === "position_adjustment_posted" ||
    value === "portfolio_review_evidence_linked" ||
    value === "account_frozen" ||
    value === "account_reactivated" ||
    value === "account_closed"
  );
}

export function isPaperAccountLedgerEvent(
  value: unknown,
): value is LedgerEvent {
  if (
    !object(value) ||
    !one(value.schema_version) ||
    !string(value.event_id) ||
    !string(value.account_id) ||
    !positiveInteger(value.sequence_number) ||
    !positiveInteger(value.account_version) ||
    !eventType(value.event_type) ||
    !string(value.command_digest) ||
    !(
      value.expected_account_version === null ||
      positiveInteger(value.expected_account_version)
    ) ||
    !string(value.actor) ||
    !nullableString(value.reason) ||
    !string(value.recorded_timestamp_utc) ||
    !nullableString(value.effective_timestamp_utc) ||
    !string(value.previous_chain_digest) ||
    !eventDetails(value.details) ||
    !string(value.event_digest) ||
    !string(value.chain_digest) ||
    !arrayOf(value.cash_postings, cashPosting) ||
    !arrayOf(value.position_postings, positionPosting)
  ) {
    return false;
  }
  const event = value as LedgerEvent;
  return (
    event.cash_postings.every(
      (posting) =>
        posting.account_id === event.account_id &&
        posting.event_id === event.event_id,
    ) &&
    event.position_postings.every(
      (posting) =>
        posting.account_id === event.account_id &&
        posting.event_id === event.event_id,
    )
  );
}

export function isPaperAccountListResponse(
  value: unknown,
): value is ListResponse {
  return (
    object(value) &&
    one(value.schema_version) &&
    arrayOf(value.items, isPaperAccountSummary) &&
    nullableString(value.next_cursor)
  );
}

export function isPaperAccountDetailResponse(
  value: unknown,
): value is DetailResponse {
  return (
    object(value) &&
    one(value.schema_version) &&
    isPaperAccountSummary(value.account) &&
    projection(value.projection) &&
    summaryProjectionBinding(value.account, value.projection)
  );
}

export function isPaperAccountLedgerResponse(
  value: unknown,
): value is LedgerResponse {
  if (
    !object(value) ||
    !one(value.schema_version) ||
    !arrayOf(value.events, isPaperAccountLedgerEvent) ||
    !(
      value.next_after_sequence_number === null ||
      positiveInteger(value.next_after_sequence_number)
    )
  ) {
    return false;
  }
  const response = value as LedgerResponse;
  return response.events.every(
    (event, index) =>
      index === 0 ||
      event.sequence_number === response.events[index - 1].sequence_number + 1,
  );
}

export function isPaperAccountCommandResponse(
  value: unknown,
): value is CommandResponse {
  if (
    !object(value) ||
    !one(value.schema_version) ||
    !boolean(value.replayed) ||
    !string(value.request_id) ||
    !isPaperAccountSummary(value.account) ||
    !isPaperAccountLedgerEvent(value.event) ||
    !projection(value.projection)
  ) {
    return false;
  }
  return (
    summaryProjectionBinding(value.account, value.projection) &&
    value.event.account_id === value.account.account_id &&
    value.event.event_id === value.account.head_event_id &&
    value.event.account_version === value.account.head_version &&
    value.event.chain_digest === value.account.head_chain_digest
  );
}

function snapshot(value: unknown): boolean {
  if (
    !object(value) ||
    !one(value.schema_version) ||
    !string(value.snapshot_id) ||
    !string(value.account_id) ||
    !positiveInteger(value.account_version) ||
    !string(value.head_event_id) ||
    !string(value.head_chain_digest) ||
    !string(value.operation_command_digest) ||
    !string(value.created_by) ||
    !string(value.recorded_timestamp_utc) ||
    !string(value.reason) ||
    !projection(value.projection) ||
    !string(value.snapshot_digest)
  ) {
    return false;
  }
  return (
    value.projection.account_identity.account_id === value.account_id &&
    value.projection.source_account_version === value.account_version &&
    value.projection.source_event_id === value.head_event_id &&
    value.projection.source_chain_digest === value.head_chain_digest
  );
}

export function isPaperAccountSnapshotCommandResponse(
  value: unknown,
): value is SnapshotCommandResponse {
  return (
    object(value) &&
    one(value.schema_version) &&
    boolean(value.replayed) &&
    string(value.request_id) &&
    snapshot(value.snapshot)
  );
}

function mismatchCode(value: unknown): boolean {
  return (
    value === "source_account_version_mismatch" ||
    value === "source_event_id_mismatch" ||
    value === "source_chain_digest_mismatch" ||
    value === "identity_mismatch" ||
    value === "lifecycle_status_mismatch" ||
    value === "cash_balance_mismatch" ||
    value === "available_cash_mismatch" ||
    value === "positions_mismatch" ||
    value === "evidence_references_mismatch"
  );
}

function reconciliation(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.reconciliation_id) &&
    string(value.account_id) &&
    string(value.operation_command_digest) &&
    string(value.created_by) &&
    string(value.recorded_timestamp_utc) &&
    string(value.reason) &&
    (value.outcome === "matched" || value.outcome === "mismatched") &&
    arrayOf(value.mismatch_codes, mismatchCode) &&
    positiveInteger(value.authoritative_account_version) &&
    string(value.authoritative_event_id) &&
    string(value.authoritative_chain_digest) &&
    string(value.authoritative_projection_digest) &&
    positiveInteger(value.candidate_account_version) &&
    string(value.candidate_event_id) &&
    string(value.candidate_chain_digest) &&
    string(value.candidate_projection_digest) &&
    string(value.reconciliation_digest)
  );
}

export function isPaperAccountReconciliationCommandResponse(
  value: unknown,
): value is ReconciliationCommandResponse {
  return (
    object(value) &&
    one(value.schema_version) &&
    boolean(value.replayed) &&
    string(value.request_id) &&
    reconciliation(value.reconciliation)
  );
}
