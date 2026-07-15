import { NextRequest } from "next/server";
import { afterEach, describe, expect, it } from "vitest";

import { founderAuthorizationValue } from "@/config/founder-auth";
import { proxy } from "./proxy";

const originalUsername = process.env.EL_PSY_QUANT_FOUNDER_USERNAME;
const originalPassword = process.env.EL_PSY_QUANT_FOUNDER_PASSWORD;

afterEach(() => {
  if (originalUsername === undefined) {
    delete process.env.EL_PSY_QUANT_FOUNDER_USERNAME;
  } else {
    process.env.EL_PSY_QUANT_FOUNDER_USERNAME = originalUsername;
  }
  if (originalPassword === undefined) {
    delete process.env.EL_PSY_QUANT_FOUNDER_PASSWORD;
  } else {
    process.env.EL_PSY_QUANT_FOUNDER_PASSWORD = originalPassword;
  }
});

describe("Founder workspace proxy", () => {
  it("passes through the existing loopback developer workflow when auth is unset", () => {
    delete process.env.EL_PSY_QUANT_FOUNDER_USERNAME;
    delete process.env.EL_PSY_QUANT_FOUNDER_PASSWORD;

    const response = proxy(new NextRequest("http://127.0.0.1:3000/strategies"));

    expect(response.status).toBe(200);
  });

  it("challenges unauthenticated workspace and gateway requests", () => {
    process.env.EL_PSY_QUANT_FOUNDER_USERNAME = "founder";
    process.env.EL_PSY_QUANT_FOUNDER_PASSWORD = "local-secret";

    for (const path of ["/", "/api/backend/api/v1/health"]) {
      const response = proxy(new NextRequest(`http://127.0.0.1:3000${path}`));

      expect(response.status).toBe(401);
      expect(response.headers.get("www-authenticate")).toBe(
        'Basic realm="El-Psy-Quant Founder", charset="UTF-8"',
      );
      expect(response.headers.get("cache-control")).toBe("no-store");
    }
  });

  it("passes exact credentials to the existing workspace and rewrite", () => {
    process.env.EL_PSY_QUANT_FOUNDER_USERNAME = "founder";
    process.env.EL_PSY_QUANT_FOUNDER_PASSWORD = "local-secret";
    const authorization = founderAuthorizationValue({
      username: "founder",
      password: "local-secret",
    });

    const response = proxy(
      new NextRequest("http://127.0.0.1:3000/api/backend/api/v1/health", {
        headers: { Authorization: authorization },
      }),
    );

    expect(response.status).toBe(200);
  });

  it("fails closed when only one credential setting is present", () => {
    process.env.EL_PSY_QUANT_FOUNDER_USERNAME = "founder";
    delete process.env.EL_PSY_QUANT_FOUNDER_PASSWORD;

    expect(() =>
      proxy(new NextRequest("http://127.0.0.1:3000/")),
    ).toThrow(/must be configured together/);
  });
});
