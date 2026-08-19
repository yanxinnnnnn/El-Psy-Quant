import { readFileSync } from "node:fs";

import { describe, expect, it, vi } from "vitest";

import {
  ApiClientError,
  createPaperExecutionOrder,
  fetchPaperExecutionAttemptDetail,
  fetchPaperExecutionAttempts,
  fetchPaperExecutionFillDetail,
  fetchPaperExecutionFills,
  fetchPaperExecutionOrderDetail,
  fetchPaperExecutionOrders,
  fetchPaperExecutionReconciliation,
  stepPaperExecutionOrder,
} from "@/lib/api-client";
import {
  executionAttempt,
  executionFill,
  executionOrderCommand,
  executionOrderView,
  executionRaw,
  executionReconciliation,
  executionStepCommand,
} from "@/test/paper-execution-fixtures";

function response(body: unknown, status = 200, requestId: string = executionRaw.requestId): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", "X-Request-ID": requestId },
  });
}

const createRequest = {
  intent: { intent_id: executionOrderView.order.order_intent_reference.intent_id, intent_digest: executionOrderView.order.order_intent_reference.intent_digest },
  decision: { decision_id: executionOrderView.order.risk_handoff_reference.risk_decision_id, decision_digest: executionOrderView.order.risk_handoff_reference.risk_decision_digest },
  execution_policy: {
    max_fill_quantity_per_trade_event: null,
    slippage_bps: "1.2500",
    commission_bps: "2.5000",
    fee_bps: "0.1250",
    buy_tax_bps: "0.0000",
    sell_tax_bps: "1.7500",
  },
  actor: "founder",
} as const;

describe("Paper Execution API client", () => {
  it("calls exactly the nine S212 routes with generated request shapes", async () => {
    const fetchMock = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response(executionOrderCommand, 201))
      .mockResolvedValueOnce(response({ schema_version: 1, items: [executionOrderView], next_cursor: executionRaw.cursor }))
      .mockResolvedValueOnce(response(executionOrderView))
      .mockResolvedValueOnce(response(executionStepCommand, 201))
      .mockResolvedValueOnce(response({ schema_version: 1, items: [executionAttempt], next_cursor: executionRaw.cursor }))
      .mockResolvedValueOnce(response(executionAttempt))
      .mockResolvedValueOnce(response({ schema_version: 1, items: [executionFill], next_cursor: executionRaw.cursor }))
      .mockResolvedValueOnce(response(executionFill))
      .mockResolvedValueOnce(response(executionReconciliation));

    await createPaperExecutionOrder(createRequest, "create-exact-key", fetchMock);
    await fetchPaperExecutionOrders({ limit: 25, cursor: executionRaw.cursor }, fetchMock);
    await fetchPaperExecutionOrderDetail(executionRaw.orderId, fetchMock);
    await stepPaperExecutionOrder(executionRaw.orderId, {
      execution_order_digest: executionRaw.orderDigest,
      expected_execution_version: 0,
      actor: "founder",
    }, "step-exact-key", fetchMock);
    await fetchPaperExecutionAttempts(executionRaw.orderId, { limit: 25, cursor: executionRaw.cursor }, fetchMock);
    await fetchPaperExecutionAttemptDetail(executionRaw.attemptId, fetchMock);
    await fetchPaperExecutionFills({ execution_order_id: executionRaw.orderId, limit: 25, cursor: executionRaw.cursor }, fetchMock);
    await fetchPaperExecutionFillDetail(executionRaw.fillId, fetchMock);
    await fetchPaperExecutionReconciliation(executionRaw.orderId, fetchMock);

    expect(fetchMock).toHaveBeenCalledTimes(9);
    expect(fetchMock.mock.calls.map(([url]) => new URL(String(url), "http://local").pathname)).toEqual([
      "/api/backend/api/v1/paper-execution/orders",
      "/api/backend/api/v1/paper-execution/orders",
      `/api/backend/api/v1/paper-execution/orders/${executionRaw.orderId}`,
      `/api/backend/api/v1/paper-execution/orders/${executionRaw.orderId}/steps`,
      `/api/backend/api/v1/paper-execution/orders/${executionRaw.orderId}/attempts`,
      `/api/backend/api/v1/paper-execution/attempts/${executionRaw.attemptId}`,
      "/api/backend/api/v1/paper-execution/fills",
      `/api/backend/api/v1/paper-execution/fills/${executionRaw.fillId}`,
      `/api/backend/api/v1/paper-execution/orders/${executionRaw.orderId}/reconciliation`,
    ]);
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual(createRequest);
    expect(fetchMock.mock.calls[0][1]?.headers).toMatchObject({ "Idempotency-Key": "create-exact-key" });
    expect(JSON.parse(String(fetchMock.mock.calls[3][1]?.body))).toEqual({
      execution_order_digest: executionRaw.orderDigest,
      expected_execution_version: 0,
      actor: "founder",
    });
    expect(fetchMock.mock.calls[3][1]?.headers).toMatchObject({ "Idempotency-Key": "step-exact-key" });
    expect(new URL(String(fetchMock.mock.calls[1][0]), "http://local").searchParams.get("cursor")).toBe(executionRaw.cursor);
    expect(new URL(String(fetchMock.mock.calls[4][0]), "http://local").searchParams.get("cursor")).toBe(executionRaw.cursor);
    expect(new URL(String(fetchMock.mock.calls[6][0]), "http://local").searchParams.get("cursor")).toBe(executionRaw.cursor);
  });

  it("preserves exact quantity, price, and cost strings without numeric coercion", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(response(executionStepCommand));
    const result = await stepPaperExecutionOrder(executionRaw.orderId, {
      execution_order_digest: executionRaw.orderDigest,
      expected_execution_version: 0,
      actor: "founder",
    }, "exact", fetchMock);
    expect(result.data.result.fill?.fill_quantity).toBe("3.2500");
    expect(result.data.result.fill?.execution_price_evidence.execution_price).toBe("12.34154250");
    expect(result.data.result.fill?.cost_evidence.total_charges).toBe("0.01052861");
    expect(result.data.result.fill?.cost_evidence.tax).toBe("0.00000000");
  });

  it("preserves stable error code, public message, status, and request ID", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(response({
      error: { code: "paper_execution_reconciliation_required", message: "Historical evidence retained." },
      request_id: "request-from-body",
    }, 409, "request-from-header"));
    let caught: unknown;
    try {
      await fetchPaperExecutionReconciliation(executionRaw.orderId, fetchMock);
    } catch (error) {
      caught = error;
    }
    expect(caught).toBeInstanceOf(ApiClientError);
    expect(caught).toMatchObject({
      code: "paper_execution_reconciliation_required",
      publicMessage: "Historical evidence retained.",
      status: 409,
      requestId: "request-from-header",
    });
  });

  it("rejects malformed success JSON instead of casting arbitrary data", async () => {
    const malformed = structuredClone(executionOrderView) as Record<string, unknown>;
    delete (malformed.order as Record<string, unknown>).execution_order_digest;
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(response(malformed));
    await expect(fetchPaperExecutionOrderDetail(executionRaw.orderId, fetchMock)).rejects.toMatchObject({
      code: "api_response_invalid",
    });
  });
});

describe("Sprint 213 browser authority boundary", () => {
  it("derives Paper Execution aliases from generated paths and exposes no competing DTOs", () => {
    const client = readFileSync("src/lib/api-client.ts", "utf8");
    const validators = readFileSync("src/lib/paper-execution-validators.ts", "utf8");
    expect(client).toContain('import type { paths } from "@/generated/api-types"');
    expect(client).toContain("type PaperExecutionOrderCreateRequest = PostRequestBody");
    expect(client).toContain("type PaperExecutionStepCommandResponse = PostSuccessResponse");
    expect(validators).toContain('import type { components } from "@/generated/api-types"');
    expect(validators).not.toMatch(/\bany\b/);
  });

  it("contains no direct Fill creation, settlement mutation, or replay cursor mutation client", () => {
    const client = readFileSync("src/lib/api-client.ts", "utf8");
    expect(client).not.toContain("createPaperExecutionFill");
    expect(client).not.toContain("postPaperExecutionSettlement");
    expect(client).not.toContain("advancePaperExecutionReplay");
  });
});
