import type { PaperJobResultResponse } from "@/lib/api-client";

export const paperJobResultFixture: PaperJobResultResponse = {
  job_id: "11111111-1111-4111-8111-111111111111",
  run_id: "run-156",
  result_reference: {
    record_schema_version: 1,
    root_type: "paper",
    artifact_schema_version: 1,
    result_summary_schema_version: 1,
    created_timestamp: "2026-07-15T12:05:00Z",
  },
  artifact: {
    schema_version: 1,
    created_timestamp: "2026-07-15T12:04:00Z",
    starting_account_state: {
      timestamp: "2026-07-15T10:00:00Z",
      starting_cash: 1000,
      current_cash: 970,
      positions: [
        { symbol: "DUP", quantity: 1 },
        { symbol: "DUP", quantity: 1 },
      ],
    },
    ending_account_state: {
      timestamp: "2026-07-15T12:00:00Z",
      starting_cash: 1000,
      current_cash: 880,
      positions: [
        { symbol: "DUP", quantity: 2 },
        { symbol: "DUP", quantity: 2 },
      ],
    },
    orders: [
      { order_id: "order-duplicate", timestamp: "2026-07-15T10:30:00Z", symbol: "DUP", side: "buy", quantity: 3, status: "filled" },
      { order_id: "order-duplicate", timestamp: "2026-07-15T10:30:00Z", symbol: "DUP", side: "buy", quantity: 3, status: "filled" },
    ],
    fills: [
      { timestamp: "2026-07-15T10:31:00Z", symbol: "DUP", side: "buy", quantity: 3, price: 40, order_id: null },
      { timestamp: "2026-07-15T10:31:00Z", symbol: "DUP", side: "buy", quantity: 3, price: 40, order_id: null },
    ],
    session_summary: {
      session_start_timestamp: "2026-07-15T10:00:00Z",
      session_end_timestamp: "2026-07-15T12:00:00Z",
      starting_cash: 970,
      ending_cash: 880,
      cash_change: -91,
      starting_positions: [
        { symbol: "DUP", quantity: 1 },
        { symbol: "DUP", quantity: 1 },
      ],
      ending_positions: [
        { symbol: "DUP", quantity: 2 },
        { symbol: "DUP", quantity: 2 },
      ],
      position_changes: [
        { symbol: "DUP", starting_quantity: 1, ending_quantity: 2, quantity_change: 91 },
        { symbol: "DUP", starting_quantity: 1, ending_quantity: 2, quantity_change: 91 },
      ],
      order_count: 41,
      fill_count: 42,
    },
  },
  result_summary: {
    schema_version: 1,
    run_id: "run-156",
    request_schema_version: 1,
    request_created_timestamp: "2026-07-15T09:59:00Z",
    artifact_schema_version: 1,
    artifact_created_timestamp: "2026-07-15T12:04:00Z",
    audit: {
      schema_version: 1,
      created_timestamp: "2026-07-15T12:04:30Z",
      session_start_timestamp: "2026-07-15T10:00:00Z",
      session_end_timestamp: "2026-07-15T12:00:00Z",
      starting_cash: 970,
      ending_cash: 880,
      cash_change: -92,
      order_count: 51,
      fill_count: 52,
      starting_position_count: 53,
      ending_position_count: 54,
      position_change_count: 55,
    },
  },
};
