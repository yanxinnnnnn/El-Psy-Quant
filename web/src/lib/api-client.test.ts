import { describe, expect, it, vi } from "vitest";

import { ApiClientError, fetchHealth } from "./api-client";

function response(
  body: unknown,
  { status = 200, requestId = "request-123" }: { status?: number; requestId?: string } = {},
): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": requestId,
    },
  });
}

describe("fetchHealth", () => {
  it("returns typed health data and the server request ID", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response({ status: "ok", service: "el-psy-quant", api_version: "v1" }),
    );

    await expect(fetchHealth(fetcher)).resolves.toEqual({
      data: { status: "ok", service: "el-psy-quant", api_version: "v1" },
      requestId: "request-123",
    });
    expect(fetcher).toHaveBeenCalledWith("/api/backend/api/v1/health", {
      method: "GET",
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
  });

  it("translates the stable backend envelope without leaking extra fields", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response(
        {
          error: { code: "service_unavailable", message: "Service unavailable" },
          request_id: "body-request-id",
          private_detail: "C:\\private\\database.sqlite3",
        },
        { status: 503, requestId: "header-request-id" },
      ),
    );

    await expect(fetchHealth(fetcher)).rejects.toMatchObject({
      status: 503,
      code: "service_unavailable",
      publicMessage: "Service unavailable",
      requestId: "header-request-id",
    });
  });

  it.each([
    [new Response("not-json", { status: 200 }), "api_response_invalid"],
    [response({ status: "almost" }), "api_response_invalid"],
    [new Response("private raw failure", { status: 502 }), "api_request_failed"],
  ])("sanitizes malformed response %#", async (malformed, code) => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(malformed);

    try {
      await fetchHealth(fetcher);
      throw new Error("expected fetchHealth to reject");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiClientError);
      expect(error).toMatchObject({ code });
      expect(String(error)).not.toContain("private raw failure");
    }
  });

  it("sanitizes network failures", async () => {
    const fetcher = vi.fn<typeof fetch>().mockRejectedValue(
      new Error("connect ECONNREFUSED with private details"),
    );

    await expect(fetchHealth(fetcher)).rejects.toMatchObject({
      status: 0,
      code: "api_unavailable",
      publicMessage: "The local API is unavailable.",
      requestId: null,
    });
  });
});
