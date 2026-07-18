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

function standardFetchRecorder() {
  const calls = [];
  const fetcher = vi.fn(async (input, options) => {
    const url = new URL(input);
    calls.push({ path: `${url.pathname}${url.search}`, options });
    if (url.pathname === "/api/backend/api/v1/health") {
      if (options.headers.Authorization === undefined) {
        return response(
          { error: { code: "authentication_required" } },
          401,
          { "www-authenticate": 'Basic realm="el-psy-quant"' },
        );
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
    if (url.pathname === "/api/backend/api/v1/demo-workspace") {
      return response(
        { error: { code: "demo_workspace_not_configured" } },
        404,
      );
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
  return { calls, fetcher };
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
    const { calls, fetcher } = standardFetchRecorder();

    await expect(runVerification({ environment, fetchImpl: fetcher })).resolves.toBe(
      "standard",
    );

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
    for (const { path, options } of calls) {
      if (options.method !== "GET") {
        continue;
      }
      expect(
        FORBIDDEN_MUTATION_FRAGMENTS.some((fragment) =>
          path.includes(fragment) && !path.includes("?limit=")
        ),
      ).toBe(false);
    }
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
