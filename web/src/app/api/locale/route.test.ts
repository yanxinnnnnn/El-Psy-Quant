import { describe, expect, it } from "vitest";

import { LOCALE_COOKIE_MAX_AGE_SECONDS } from "@/i18n/config";
import { POST } from "./route";

function request(body: string) {
  return new Request("http://localhost/api/locale", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body,
  });
}

describe("POST /api/locale", () => {
  it.each(["en", "zh-CN"])("stores the exact supported %s preference", async (locale) => {
    const response = await POST(request(JSON.stringify({ locale })));
    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ locale });
    const cookie = response.headers.get("set-cookie") ?? "";
    expect(cookie).toContain(`el_psy_quant_locale=${locale}`);
    expect(cookie).toContain(`Max-Age=${LOCALE_COOKIE_MAX_AGE_SECONDS}`);
    expect(cookie).toContain("Path=/");
    expect(cookie).toContain("HttpOnly");
    expect(cookie).toContain("SameSite=lax");
    expect(cookie).not.toContain("Secure");
  });

  it.each([
    "{}",
    JSON.stringify({ locale: "zh-cn" }),
    JSON.stringify({ locale: "fr" }),
    JSON.stringify({ locale: 1 }),
    "{",
  ])("rejects malformed or unsupported input without setting a cookie", async (body) => {
    const response = await POST(request(body));
    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ error: "invalid_locale_preference" });
    expect(response.headers.get("set-cookie")).toBeNull();
  });
});
