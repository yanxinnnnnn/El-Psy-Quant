import { describe, expect, it, vi } from "vitest";

import { ApiClientError, fetchPaperJobResult, type PaperJobResultResponse } from "./api-client";
import { paperJobResultFixture } from "@/test/paper-job-result-fixture";

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "X-Request-ID": "request-156" },
  });
}

describe("portfolio record result client", () => {
  it("uses the generated success type and one independently encoded same-origin result path", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response(paperJobResultFixture));
    const result: PaperJobResultResponse = (await fetchPaperJobResult("job / ?", fetcher)).data;
    expect(result.result_reference.root_type).toBe("paper");
    expect(fetcher).toHaveBeenCalledWith(
      "/api/backend/api/v1/paper-jobs/job%20%2F%20%3F/result",
      { method: "GET", cache: "no-store", headers: { Accept: "application/json" } },
    );
  });

  it.each([
    { ...paperJobResultFixture, result_reference: { ...paperJobResultFixture.result_reference, root_type: "filesystem" } },
    { ...paperJobResultFixture, artifact: { ...paperJobResultFixture.artifact, fills: [{ price: "40" }] } },
    { ...paperJobResultFixture, result_summary: { ...paperJobResultFixture.result_summary, audit: { order_count: -1 } } },
  ])("rejects malformed nested transport without exposing it", async (body) => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response(body));
    await expect(fetchPaperJobResult("job", fetcher)).rejects.toMatchObject({
      code: "api_response_invalid",
      publicMessage: "The local API returned an invalid response.",
      requestId: "request-156",
    });
  });

  it("preserves bounded unavailable and invalid errors and sanitizes response extras", async () => {
    for (const code of ["paper_job_result_unavailable", "paper_job_result_invalid"]) {
      const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response({
        error: { code, message: `Safe ${code}` },
        request_id: "body-id",
        private_path: "C:\\private\\paper",
      }, 409));
      try {
        await fetchPaperJobResult("job", fetcher);
        throw new Error("expected rejection");
      } catch (error) {
        expect(error).toBeInstanceOf(ApiClientError);
        expect(error).toMatchObject({ code, requestId: "request-156" });
        expect(String(error)).not.toContain("private");
      }
    }
  });
});
