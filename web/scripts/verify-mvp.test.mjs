import { describe, expect, it, vi } from "vitest";

import {
  FORBIDDEN_MUTATION_FRAGMENTS,
  TOP_LEVEL_ROUTES,
  buildRequestOptions,
  expectStatus,
  runVerification,
  validateOrigin,
} from "./verify-mvp.mjs";

const environment = {
  EL_PSY_QUANT_FOUNDER_USERNAME: "founder",
  EL_PSY_QUANT_FOUNDER_PASSWORD: "super-secret",
  EL_PSY_QUANT_MVP_ORIGIN: "http://127.0.0.1:3000",
  EL_PSY_QUANT_WORKSPACE_MODE: "standard",
};

function response(body, status = 200, headers = {}) {
  return new Response(
    typeof body === "string" ? body : JSON.stringify(body),
    {
      status,
      headers: {
        "content-type": typeof body === "string"
          ? "text/html; charset=utf-8"
          : "application/json",
        "x-request-id": "request-167",
        ...headers,
      },
    },
  );
}

function standardFetchRecorder(demoDescriptor = null) {
  const calls = [];
  const proxyChallenge = new Response("Founder authentication required", {
    status: 401,
    headers: {
      "cache-control": "no-store",
      "content-type": "text/plain; charset=utf-8",
      "www-authenticate": 'Basic realm="el-psy-quant", charset="UTF-8"',
    },
  });
  const fetcher = vi.fn(async (input, options) => {
    const url = new URL(input);
    calls.push({ path: `${url.pathname}${url.search}`, options });
    if (url.pathname === "/api/backend/api/v1/health") {
      if (options.headers.Authorization === undefined) {
        return proxyChallenge;
      }
      return response({
        status: "ok",
        service: "el-psy-quant",
        api_version: "v1",
      });
    }
    if (url.pathname === "/api/locale") {
      const locale = JSON.parse(options.body).locale;
      return response(
        { locale },
        200,
        { "set-cookie": `el_psy_quant_locale=${locale}; Path=/; HttpOnly; SameSite=lax` },
      );
    }
    if (
      TOP_LEVEL_ROUTES.includes(url.pathname) ||
      url.pathname === "/strategies/moving_average_crossover"
    ) {
      const chinese = options.headers.Cookie ===
        "el_psy_quant_locale=zh-CN";
      const locale = chinese ? "zh-CN" : "en";
      const copy = chinese ? "El-Psy-Quant · 创始人工作台" : "Founder Workspace";
      return response(`<html lang="${locale}"><body>${copy}</body></html>`);
    }
    if (url.pathname === "/api/backend/api/v1/strategies") {
      return response({ strategies: [] });
    }
    if (url.pathname === "/api/backend/api/v1/research-runs") {
      return response({ runs: [] });
    }
    if (url.pathname === "/api/backend/api/v1/evidence-manifests") {
      return response({ manifests: [] });
    }
    if (
      url.pathname === "/api/backend/api/v1/paper-jobs" &&
      url.search === "?limit=20"
    ) {
      return response([]);
    }
    if (
      url.pathname === "/api/backend/api/v1/portfolio-reviews" &&
      url.search === "?limit=50"
    ) {
      return response([]);
    }
    if (
      url.pathname === "/api/backend/api/v1/paper-accounts" &&
      url.search === "?limit=50"
    ) {
      return response({ schema_version: 1, items: [], next_cursor: null });
    }
    if (url.pathname === "/api/backend/api/v1/demo-workspace") {
      if (demoDescriptor !== null) {
        return response(demoDescriptor);
      }
      return response(
        { error: { code: "demo_workspace_not_configured" } },
        404,
      );
    }
    if (demoDescriptor !== null) {
      if (
        url.pathname.startsWith("/api/backend/api/v1/strategies/") ||
        url.pathname.startsWith("/api/backend/api/v1/research-runs/") ||
        url.pathname.startsWith("/api/backend/api/v1/evidence-manifests/")
      ) {
        return response({ exact: true });
      }
      if (url.pathname.startsWith("/api/backend/api/v1/paper-jobs/") &&
        url.pathname.endsWith("/result")) {
        return response({ exact: true });
      }
      if (url.pathname.startsWith("/api/backend/api/v1/paper-jobs/")) {
        return response({ status: "succeeded", result_available: true });
      }
      if (url.pathname === "/api/backend/api/v1/portfolio-reviews/demo-review") {
        return response({
          record: { review_id: "demo-review", status: "awaiting_decision" },
          source: { source_id: "demo-source" },
          analysis: { proposed_component_id: "demo-component-b" },
          decision: null,
        });
      }
      if (
        url.pathname ===
        "/api/backend/api/v1/paper-accounts/demo-paper-account/ledger"
      ) {
        return response({
          schema_version: 1,
          events: demoDescriptor.paper_account.event_types.map(
            (event_type) => ({
              account_id: "demo-paper-account",
              event_type,
            }),
          ),
          next_after_sequence_number: null,
        });
      }
      if (
        url.pathname ===
        "/api/backend/api/v1/paper-accounts/demo-paper-account"
      ) {
        return response({
          schema_version: 1,
          account: {
            account_id: "demo-paper-account",
            head_version: 5,
            projection_status: "current",
          },
          projection: {
            source_account_version: 5,
            account_identity: { account_id: "demo-paper-account" },
          },
        });
      }
    }
    if (
      url.pathname === "/api/backend/api/v1/paper-jobs" &&
      url.search === "?limit=0"
    ) {
      return response(
        { error: { code: "request_validation_error" } },
        422,
      );
    }
    throw new Error(`unexpected test request ${url.pathname}${url.search}`);
  });
  return { calls, fetcher, proxyChallenge };
}

describe("non-mutating bilingual MVP verifier", () => {
  it("constructs bounded GET and locale-only POST requests", () => {
    expect(buildRequestOptions()).toMatchObject({
      method: "GET",
      redirect: "manual",
      cache: "no-store",
    });
    expect(buildRequestOptions({ body: { locale: "zh-CN" } })).toMatchObject({
      method: "POST",
      body: '{"locale":"zh-CN"}',
    });
  });

  it("covers both locale cookies, empty Standard reads, and no product mutation", async () => {
    const { calls, fetcher, proxyChallenge } = standardFetchRecorder();

    await expect(runVerification({ environment, fetchImpl: fetcher })).resolves.toBe(
      "standard",
    );

    expect(proxyChallenge.headers.get("x-request-id")).toBeNull();
    const posts = calls.filter(({ options }) => options.method === "POST");
    expect(posts.map(({ path }) => path)).toEqual(["/api/locale", "/api/locale"]);
    expect(posts.map(({ options }) => JSON.parse(options.body).locale)).toEqual([
      "zh-CN",
      "en",
    ]);
    expect(calls.some(({ options }) =>
      options.headers.Cookie === "el_psy_quant_locale=zh-CN"
    )).toBe(true);
    expect(calls.some(({ options }) =>
      options.headers.Cookie === "el_psy_quant_locale=en"
    )).toBe(true);
    expect(
      posts.some(({ path }) =>
        FORBIDDEN_MUTATION_FRAGMENTS.some((fragment) => path.includes(fragment))
      ),
    ).toBe(false);
  });

  it("keeps credentials and response bodies out of failure output", async () => {
    const secretBody = "super-secret private payload";
    const failure = response(secretBody, 500);

    await expect(
      expectStatus(failure, 200, "Bounded route check"),
    ).rejects.toThrow("Bounded route check returned HTTP 500; expected 200");
    await expect(
      expectStatus(failure, 200, "Bounded route check"),
    ).rejects.not.toThrow(secretBody);
  });

  it("verifies Demo descriptor v3, seeded review, and Paper Account without product mutation", async () => {
    const descriptor = {
      schema_version: 3,
      dataset_id: "demo-dataset",
      dataset_version: 3,
      canonical_strategy_name: "moving_average_crossover",
      research_run: { experiment_slug: "demo-experiment", run_id: "demo-run" },
      evidence_manifests: [{
        manifest_type: "report_artifact_manifest",
        artifact_key: "demo-report",
      }],
      paper_jobs: [
        { job_id: "demo-job-a", run_id: "demo-paper-a" },
        { job_id: "demo-job-b", run_id: "demo-paper-b" },
      ],
      comparison_candidate_job_ids: ["demo-job-a", "demo-job-b"],
      portfolio_review_example: {
        create_idempotency_key: "demo-create-key",
        request: {
          review_id: "demo-review",
          source: { source_id: "demo-source" },
          proposed_scenario: { proposed_component_id: "demo-component-b" },
        },
      },
      paper_account: {
        account_id: "demo-paper-account",
        head_version: 5,
        event_types: [
          "account_created",
          "cash_movement_posted",
          "position_adjustment_posted",
          "account_frozen",
          "account_reactivated",
        ],
        snapshot_id: "demo-snapshot",
        reconciliation_id: "demo-reconciliation",
      },
    };
    const { calls, fetcher } = standardFetchRecorder(descriptor);

    await expect(runVerification({
      environment: { ...environment, EL_PSY_QUANT_WORKSPACE_MODE: "demo" },
      fetchImpl: fetcher,
    })).resolves.toBe("demo");

    expect(calls.some(({ path }) =>
      path === "/api/backend/api/v1/portfolio-reviews/demo-review"
    )).toBe(true);
    expect(calls.some(({ path }) =>
      path === "/api/backend/api/v1/paper-accounts/demo-paper-account"
    )).toBe(true);
    expect(calls.some(({ path }) =>
      path ===
      "/api/backend/api/v1/paper-accounts/demo-paper-account/ledger?after_sequence_number=0&limit=200"
    )).toBe(true);
    expect(calls.filter(({ options }) => options.method === "POST").map(({ path }) =>
      path
    )).toEqual(["/api/locale", "/api/locale"]);
  });

  it("rejects non-loopback origins and unknown modes before product reads", async () => {
    expect(() => validateOrigin("https://example.com")).toThrow("loopback");
    const { fetcher } = standardFetchRecorder();
    await expect(
      runVerification({
        environment: {
          ...environment,
          EL_PSY_QUANT_WORKSPACE_MODE: "unknown",
        },
        fetchImpl: fetcher,
      }),
    ).rejects.toThrow("must be standard or demo");
  });
});
