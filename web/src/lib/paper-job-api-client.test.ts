import { describe, expect, it, vi } from "vitest";

import {
  ApiClientError,
  cancelPaperJob,
  fetchPaperJobAttempts,
  fetchPaperJobDetail,
  fetchPaperJobs,
  recoverPaperJob,
  retryPaperJob,
  runPaperJob,
  submitPaperJob,
  type PaperJobRecoveryRequest,
  type PaperJobRunAcceptedResponse,
  type PaperJobSubmissionRequest,
} from "./api-client";

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "X-Request-ID": "request-155" },
  });
}

const job = {
  job_id: "11111111-1111-4111-8111-111111111111",
  run_id: "founder-run",
  status: "queued" as const,
  submitted_timestamp: "2026-07-15T10:00:00Z",
  updated_timestamp: "2026-07-15T10:00:00Z",
  attempt_count: 0,
  latest_attempt: null,
  result_available: false,
  result_url: null,
};

const command: PaperJobSubmissionRequest = {
  run_id: "founder-run",
  created_timestamp: "2026-07-15T10:00:00Z",
  starting_account_state: {
    timestamp: "2026-07-15T10:00:00Z",
    starting_cash: 1000,
    current_cash: 1000,
    positions: {},
  },
  ending_account_state: {
    timestamp: "2026-07-15T11:00:00Z",
    starting_cash: 1000,
    current_cash: 900,
    positions: { AAPL: 1 },
  },
  orders: [],
  fills: [],
};

describe("paper job endpoint clients", () => {
  it("constructs only status and bounded limit list queries", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response([job]));
    await fetchPaperJobs({ status: "failed", limit: 100 }, fetcher);
    expect(fetcher).toHaveBeenCalledWith(
      "/api/backend/api/v1/paper-jobs?status=failed&limit=100",
      { method: "GET", cache: "no-store", headers: { Accept: "application/json" } },
    );
    expect(() => fetchPaperJobs({ status: null, limit: 201 }, fetcher)).toThrow(
      /between 1 and 200/,
    );
  });

  it("encodes each exact job path segment and validates attempts", async () => {
    const detailFetcher = vi.fn<typeof fetch>().mockResolvedValue(response(job));
    const attemptsFetcher = vi.fn<typeof fetch>().mockResolvedValue(response([{
      attempt_id: "22222222-2222-4222-8222-222222222222",
      attempt_number: 1,
      status: "interrupted",
      started_timestamp: "2026-07-15T10:00:00Z",
      completed_timestamp: null,
      error_code: "interrupted_without_output",
    }]));
    await fetchPaperJobDetail("job / ?", detailFetcher);
    await fetchPaperJobAttempts("job / ?", attemptsFetcher);
    expect(detailFetcher.mock.calls[0][0]).toBe(
      "/api/backend/api/v1/paper-jobs/job%20%2F%20%3F",
    );
    expect(attemptsFetcher.mock.calls[0][0]).toBe(
      "/api/backend/api/v1/paper-jobs/job%20%2F%20%3F/attempts",
    );
  });

  it("uses the generated request body and omits or preserves idempotency exactly", async () => {
    const blankFetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response({ submission_outcome: "created", job }),
    );
    const keyedFetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response({ submission_outcome: "replayed", job }),
    );
    expect((await submitPaperJob(command, "", blankFetcher)).data.submission_outcome).toBe("created");
    expect(
      (await submitPaperJob(command, "Founder.Key:155", keyedFetcher)).data
        .submission_outcome,
    ).toBe("replayed");
    expect(blankFetcher.mock.calls[0][1]).toEqual({
      method: "POST",
      cache: "no-store",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify(command),
    });
    expect(keyedFetcher.mock.calls[0][1]).toEqual({
      method: "POST",
      cache: "no-store",
      headers: {
        Accept: "application/json",
        "Idempotency-Key": "Founder.Key:155",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(command),
    });
  });

  it("accepts the generated 202 Run response and sends no JSON body", async () => {
    const runningJob = {
      ...job,
      status: "running" as const,
      attempt_count: 1,
      latest_attempt: {
        attempt_id: "22222222-2222-4222-8222-222222222222",
        attempt_number: 1,
        status: "running" as const,
        started_timestamp: "2026-07-15T10:00:01Z",
        completed_timestamp: null,
        error_code: null,
      },
    };
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response(runningJob, 202));
    const accepted: PaperJobRunAcceptedResponse = (await runPaperJob(job.job_id, fetcher)).data;
    expect(accepted.status).toBe("running");
    expect(accepted.latest_attempt?.attempt_number).toBe(1);
    expect(fetcher).toHaveBeenCalledWith(
      `/api/backend/api/v1/paper-jobs/${job.job_id}/run`,
      { method: "POST", cache: "no-store", headers: { Accept: "application/json" } },
    );
  });

  it("keeps every mutation endpoint specific and sends exact UTC recovery input", async () => {
    const fetcher = vi.fn<typeof fetch>().mockImplementation((input) =>
      Promise.resolve(
        response(
          String(input).endsWith("/recover")
            ? { recovery_outcome: "requeued", job }
            : job,
        ),
      ),
    );
    const recovery: PaperJobRecoveryRequest = { stale_before: "2026-07-15T10:00:00Z" };
    await cancelPaperJob(job.job_id, fetcher);
    await retryPaperJob(job.job_id, fetcher);
    await recoverPaperJob(job.job_id, recovery, fetcher);
    expect(fetcher.mock.calls.map(([url]) => url)).toEqual([
      `/api/backend/api/v1/paper-jobs/${job.job_id}/cancel`,
      `/api/backend/api/v1/paper-jobs/${job.job_id}/retry`,
      `/api/backend/api/v1/paper-jobs/${job.job_id}/recover`,
    ]);
    expect(fetcher.mock.calls[2][1]).toMatchObject({ body: JSON.stringify(recovery) });
  });

  it("rejects unknown submission and recovery outcomes", async () => {
    const submissionFetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response({ submission_outcome: "duplicate", job }),
    );
    const recoveryFetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response({ recovery_outcome: "uncertain", job }),
    );

    await expect(
      submitPaperJob(command, "Founder.Key:155", submissionFetcher),
    ).rejects.toMatchObject({ code: "api_response_invalid" });
    await expect(
      recoverPaperJob(
        job.job_id,
        { stale_before: "2026-07-15T10:00:00Z" },
        recoveryFetcher,
      ),
    ).rejects.toMatchObject({ code: "api_response_invalid" });
  });

  it.each([
    [{ ...job, status: "complete" }, "invalid job status"],
    [{ ...job, attempt_count: "0" }, "invalid attempt count"],
    [[{ attempt_id: "x", attempt_number: 1, status: "invented" }], "invalid attempt"],
  ])("sanitizes malformed paper-job transport: %s", async (body, label) => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response(body));
    const request = Array.isArray(body)
      ? fetchPaperJobAttempts(job.job_id, fetcher)
      : fetchPaperJobDetail(job.job_id, fetcher);
    await expect(request, label).rejects.toMatchObject({
      code: "api_response_invalid",
      requestId: "request-155",
    });
  });

  it("preserves bounded mutation errors without exposing response extras", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response({
      error: { code: "paper_job_state_conflict", message: "Paper job state conflicts" },
      request_id: "body-id",
      private_path: "C:\\private\\paper",
    }, 409));
    try {
      await retryPaperJob(job.job_id, fetcher);
      throw new Error("expected rejection");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiClientError);
      expect(error).toMatchObject({ code: "paper_job_state_conflict", requestId: "request-155" });
      expect(String(error)).not.toContain("private");
    }
  });
});
