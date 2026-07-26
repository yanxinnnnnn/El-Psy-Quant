import { describe, expect, it, vi } from "vitest";

import {
  changePaperAccountLifecycle,
  createPaperAccount,
  createPaperAccountSnapshot,
  fetchPaperAccountDetail,
  fetchPaperAccountLedger,
  fetchPaperAccounts,
  linkPaperAccountEvidence,
  postPaperAccountCashMovement,
  postPaperAccountPositionAdjustment,
  reconcilePaperAccount,
} from "@/lib/api-client";
import {
  paperAccountCommand,
  paperAccountDetail,
  paperAccountLedger,
  paperAccountList,
  paperAccountReconciliation,
  paperAccountSnapshot,
} from "@/test/paper-account-fixtures";

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": "paper-client-request",
    },
  });
}

describe("Paper Account generated-contract client", () => {
  it("uses the exact ten versioned routes, encoded identities, queries, headers, and bodies", async () => {
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response(paperAccountList))
      .mockResolvedValueOnce(response(paperAccountDetail))
      .mockResolvedValueOnce(response(paperAccountLedger))
      .mockResolvedValueOnce(response(paperAccountCommand, 201))
      .mockResolvedValueOnce(response(paperAccountCommand, 201))
      .mockResolvedValueOnce(response(paperAccountCommand, 200))
      .mockResolvedValueOnce(response(paperAccountCommand, 201))
      .mockResolvedValueOnce(response(paperAccountCommand, 201))
      .mockResolvedValueOnce(response(paperAccountSnapshot, 201))
      .mockResolvedValueOnce(response(paperAccountReconciliation, 200));
    const accountId = "paper account / % ?";

    await fetchPaperAccounts({
      lifecycleStatus: "active",
      limit: 25,
      cursor: "opaque cursor",
    }, fetcher);
    await fetchPaperAccountDetail(accountId, fetcher);
    await fetchPaperAccountLedger(
      accountId,
      { afterSequenceNumber: 7, limit: 100 },
      fetcher,
    );
    await createPaperAccount({
      display_name: "Founder Account",
      base_currency: "USD",
      initial_cash: "1000.25",
      actor: "founder",
    }, "Create:186", fetcher);
    await postPaperAccountCashMovement(accountId, {
      expected_account_version: 2,
      actor: "founder",
      reason: "Exact movement",
      movement_type: "deposit",
      requested_amount: "2.5",
      effective_timestamp_utc: null,
    }, "Cash:186", fetcher);
    await postPaperAccountPositionAdjustment(accountId, {
      expected_account_version: 2,
      actor: "founder",
      reason: "Exact position correction",
      symbol: "AAPL",
      adjustment_category: "manual_correction",
      signed_quantity_delta: "-1.25",
      signed_cost_basis_delta: "-100.5",
      effective_timestamp_utc: "2026-07-26T12:00:00Z",
    }, "Position:186", fetcher);
    await linkPaperAccountEvidence(accountId, {
      expected_account_version: 2,
      actor: "founder",
      reason: "Governance provenance",
      review_id: "review-186",
    }, "Evidence:186", fetcher);
    await changePaperAccountLifecycle(accountId, {
      expected_account_version: 2,
      actor: "founder",
      reason: "Explicit freeze",
      action: "freeze",
    }, "Lifecycle:186", fetcher);
    const evidenceRequest = {
      expected_account_version: 2,
      expected_head_event_id: "event-cash-186",
      expected_head_chain_digest: "b".repeat(64),
      actor: "founder",
      reason: "Derived evidence",
    };
    await createPaperAccountSnapshot(
      accountId,
      evidenceRequest,
      "Snapshot:186",
      fetcher,
    );
    await reconcilePaperAccount(
      accountId,
      evidenceRequest,
      "Reconciliation:186",
      fetcher,
    );

    expect(fetcher.mock.calls.map(([url]) => url)).toEqual([
      "/api/backend/api/v1/paper-accounts?lifecycle_status=active&limit=25&cursor=opaque+cursor",
      "/api/backend/api/v1/paper-accounts/paper%20account%20%2F%20%25%20%3F",
      "/api/backend/api/v1/paper-accounts/paper%20account%20%2F%20%25%20%3F/ledger?after_sequence_number=7&limit=100",
      "/api/backend/api/v1/paper-accounts",
      "/api/backend/api/v1/paper-accounts/paper%20account%20%2F%20%25%20%3F/cash-movements",
      "/api/backend/api/v1/paper-accounts/paper%20account%20%2F%20%25%20%3F/position-adjustments",
      "/api/backend/api/v1/paper-accounts/paper%20account%20%2F%20%25%20%3F/evidence-links",
      "/api/backend/api/v1/paper-accounts/paper%20account%20%2F%20%25%20%3F/lifecycle",
      "/api/backend/api/v1/paper-accounts/paper%20account%20%2F%20%25%20%3F/snapshots",
      "/api/backend/api/v1/paper-accounts/paper%20account%20%2F%20%25%20%3F/reconciliations",
    ]);
    expect(fetcher.mock.calls[3][1]?.headers).toMatchObject({
      "Idempotency-Key": "Create:186",
    });
    expect(JSON.parse(String(fetcher.mock.calls[5][1]?.body))).toEqual({
      expected_account_version: 2,
      actor: "founder",
      reason: "Exact position correction",
      symbol: "AAPL",
      adjustment_category: "manual_correction",
      signed_quantity_delta: "-1.25",
      signed_cost_basis_delta: "-100.5",
      effective_timestamp_utc: "2026-07-26T12:00:00Z",
    });
    expect(JSON.parse(String(fetcher.mock.calls[8][1]?.body))).toEqual(
      evidenceRequest,
    );
  });

  it("fails closed when nested financial authority and durable anchors disagree", async () => {
    const malformed = structuredClone(paperAccountDetail);
    malformed.projection.cash_balance = "999999";
    malformed.projection.source_event_id = "different-event";
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response(malformed));

    await expect(fetchPaperAccountDetail("paper-account-186", fetcher))
      .rejects.toMatchObject({
        code: "api_response_invalid",
        requestId: "paper-client-request",
      });
  });

  it("requires explicit bounded pagination and idempotency inputs", async () => {
    expect(() => fetchPaperAccounts({
      lifecycleStatus: null,
      limit: 201,
    })).toThrow(TypeError);
    expect(() => fetchPaperAccountLedger(
      "paper-account-186",
      { afterSequenceNumber: -1 },
    )).toThrow(TypeError);
    expect(() => createPaperAccount({
      display_name: "Founder Account",
      base_currency: "USD",
      initial_cash: "1000",
      actor: "founder",
    }, " ")).toThrow(TypeError);
  });
});
