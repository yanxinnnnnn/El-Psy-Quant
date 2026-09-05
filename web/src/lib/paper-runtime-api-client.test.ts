import { readFileSync } from "node:fs";

import { describe, expect, it, vi } from "vitest";

import {
  ApiClientError,
  createPaperRuntime,
  fetchPaperRuntimeAudit,
  fetchPaperRuntimeCheckpoints,
  fetchPaperRuntimeDetail,
  fetchPaperRuntimeHealth,
  fetchPaperRuntimeReconciliation,
  fetchPaperRuntimes,
  fetchPaperRuntimeWork,
  recoverPaperRuntime,
  resumePaperRuntime,
  startPaperRuntime,
  stopPaperRuntime,
} from "@/lib/api-client";
import {
  isPaperRuntimeHealthResponse,
  isPaperRuntimeListResponse,
  isPaperRuntimeResponse,
} from "@/lib/paper-runtime-validators";
import {
  paperRuntime,
  paperRuntimeAudit,
  paperRuntimeCheckpoints,
  paperRuntimeCommand,
  paperRuntimeHealth,
  paperRuntimeReconciliation,
  paperRuntimeWork,
  runtimeRaw,
} from "@/test/paper-runtime-fixtures";

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", "X-Request-ID": runtimeRaw.requestId } });
}

const createRequest = {
  execution_order_id: paperRuntime.execution_order_id,
  execution_order_digest: paperRuntime.execution_order_digest,
  logical_actor: "founder-paper-runtime",
  runtime_policy_id: "durable-runtime-v1",
  runtime_policy_version: 1,
  actor: "founder",
} as const;
const controlRequest = { runtime_binding_digest: runtimeRaw.runtimeDigest, expected_runtime_version: 0, actor: "founder" } as const;

describe("Paper Runtime API client", () => {
  it("calls all twelve generated S223 operations with exact paths, filters, bodies, and keys", async () => {
    const fetchMock = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response(paperRuntimeCommand, 201))
      .mockResolvedValueOnce(response({ schema_version: 1, items: [paperRuntime], next_cursor: runtimeRaw.cursor }))
      .mockResolvedValueOnce(response(paperRuntime))
      .mockResolvedValueOnce(response(paperRuntimeCommand, 201))
      .mockResolvedValueOnce(response(paperRuntimeCommand, 201))
      .mockResolvedValueOnce(response(paperRuntimeCommand, 201))
      .mockResolvedValueOnce(response(paperRuntimeCommand, 201))
      .mockResolvedValueOnce(response(paperRuntimeHealth))
      .mockResolvedValueOnce(response(paperRuntimeReconciliation))
      .mockResolvedValueOnce(response(paperRuntimeAudit))
      .mockResolvedValueOnce(response(paperRuntimeWork))
      .mockResolvedValueOnce(response(paperRuntimeCheckpoints));

    await createPaperRuntime(createRequest, "create-exact-key", fetchMock);
    await fetchPaperRuntimes({ account_id: "account A", replay_id: "replay/1", trading_session_id: "session:1", desired_state: "stopped", observed_state: "ready", limit: 25, cursor: runtimeRaw.cursor }, fetchMock);
    await fetchPaperRuntimeDetail(runtimeRaw.runtimeId, fetchMock);
    await startPaperRuntime(runtimeRaw.runtimeId, controlRequest, "start-key", fetchMock);
    await stopPaperRuntime(runtimeRaw.runtimeId, controlRequest, "stop-key", fetchMock);
    await resumePaperRuntime(runtimeRaw.runtimeId, controlRequest, "resume-key", fetchMock);
    await recoverPaperRuntime(runtimeRaw.runtimeId, controlRequest, "recover-key", fetchMock);
    await fetchPaperRuntimeHealth(runtimeRaw.runtimeId, fetchMock);
    await fetchPaperRuntimeReconciliation(runtimeRaw.runtimeId, fetchMock);
    await fetchPaperRuntimeAudit(runtimeRaw.runtimeId, { limit: 25, cursor: runtimeRaw.cursor }, fetchMock);
    await fetchPaperRuntimeWork(runtimeRaw.runtimeId, { limit: 25, cursor: runtimeRaw.cursor }, fetchMock);
    await fetchPaperRuntimeCheckpoints(runtimeRaw.runtimeId, { limit: 25, cursor: runtimeRaw.cursor }, fetchMock);

    expect(fetchMock).toHaveBeenCalledTimes(12);
    expect(fetchMock.mock.calls.map(([url]) => new URL(String(url), "http://local").pathname)).toEqual([
      "/api/backend/api/v1/paper-runtimes",
      "/api/backend/api/v1/paper-runtimes",
      `/api/backend/api/v1/paper-runtimes/${runtimeRaw.runtimeId}`,
      `/api/backend/api/v1/paper-runtimes/${runtimeRaw.runtimeId}/start`,
      `/api/backend/api/v1/paper-runtimes/${runtimeRaw.runtimeId}/stop`,
      `/api/backend/api/v1/paper-runtimes/${runtimeRaw.runtimeId}/resume`,
      `/api/backend/api/v1/paper-runtimes/${runtimeRaw.runtimeId}/recover`,
      `/api/backend/api/v1/paper-runtimes/${runtimeRaw.runtimeId}/health`,
      `/api/backend/api/v1/paper-runtimes/${runtimeRaw.runtimeId}/reconciliation`,
      `/api/backend/api/v1/paper-runtimes/${runtimeRaw.runtimeId}/audit`,
      `/api/backend/api/v1/paper-runtimes/${runtimeRaw.runtimeId}/work`,
      `/api/backend/api/v1/paper-runtimes/${runtimeRaw.runtimeId}/checkpoints`,
    ]);
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual(createRequest);
    expect(fetchMock.mock.calls[0][1]?.headers).toMatchObject({ "Idempotency-Key": "create-exact-key" });
    for (const [index, key] of [[3, "start-key"], [4, "stop-key"], [5, "resume-key"], [6, "recover-key"]] as const) {
      expect(JSON.parse(String(fetchMock.mock.calls[index][1]?.body))).toEqual(controlRequest);
      expect(fetchMock.mock.calls[index][1]?.headers).toMatchObject({ "Idempotency-Key": key });
    }
    const listUrl = new URL(String(fetchMock.mock.calls[1][0]), "http://local");
    expect(Object.fromEntries(listUrl.searchParams)).toEqual({ account_id: "account A", replay_id: "replay/1", trading_session_id: "session:1", desired_state: "stopped", observed_state: "ready", limit: "25", cursor: runtimeRaw.cursor });
    for (const index of [9, 10, 11]) expect(new URL(String(fetchMock.mock.calls[index][0]), "http://local").searchParams.get("cursor")).toBe(runtimeRaw.cursor);
  });

  it("fails closed for malformed IDs, digests, states, timestamps, and list payloads", () => {
    expect(isPaperRuntimeResponse({ ...paperRuntime, runtime_id: "runtime-1" })).toBe(false);
    expect(isPaperRuntimeResponse({ ...paperRuntime, runtime_binding_digest: "bad" })).toBe(false);
    expect(isPaperRuntimeResponse({ ...paperRuntime, observed_state: "executing" })).toBe(false);
    expect(isPaperRuntimeResponse({ ...paperRuntime, updated_at: "not-a-time" })).toBe(false);
    expect(isPaperRuntimeHealthResponse({ ...paperRuntimeHealth, lease_status: "unknown" })).toBe(false);
    expect(isPaperRuntimeListResponse({ schema_version: 1, items: [paperRuntime], next_cursor: 12 })).toBe(false);
  });

  it("preserves sanitized public API errors", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(response({ error: { code: "paper_runtime_version_conflict", message: "Reload before another request." }, request_id: "body-id" }, 409));
    await expect(startPaperRuntime(runtimeRaw.runtimeId, controlRequest, "same-key", fetchMock)).rejects.toMatchObject({
      status: 409, code: "paper_runtime_version_conflict", publicMessage: "Reload before another request.", requestId: runtimeRaw.requestId,
    } satisfies Partial<ApiClientError>);
  });

  it("derives transport contracts from generated paths without competing DTOs", () => {
    const client = readFileSync("src/lib/api-client.ts", "utf8");
    const validators = readFileSync("src/lib/paper-runtime-validators.ts", "utf8");
    expect(client).toContain("type PaperRuntimeCreateRequest = PostRequestBody");
    expect(client).toContain("type PaperRuntimeResponse = SuccessResponse");
    expect(client).toContain("type PaperRuntimeCommandResponse = PostSuccessResponse");
    expect(validators).toContain("import type {");
    expect(validators).not.toMatch(/interface PaperRuntime|type PaperRuntimeResponse\s*=/);
  });
});
