import { describe, expect, it } from "vitest";

import {
  authorizationMatchesFounder,
  founderAuthorizationValue,
  resolveFounderAuthConfig,
} from "./founder-auth";

describe("resolveFounderAuthConfig", () => {
  it("keeps authentication disabled when both settings are absent", () => {
    expect(resolveFounderAuthConfig(undefined, undefined)).toBeNull();
  });

  it("returns one exact paired credential", () => {
    expect(resolveFounderAuthConfig("founder", "local-secret")).toEqual({
      username: "founder",
      password: "local-secret",
    });
  });

  it.each([
    ["founder", undefined],
    [undefined, "local-secret"],
    ["", "local-secret"],
    ["founder", ""],
    ["founder:name", "local-secret"],
    ["founder name", "local-secret"],
    ["founder", "local secret"],
    ["f".repeat(129), "local-secret"],
  ])("rejects incomplete or unsafe values", (username, password) => {
    expect(() => resolveFounderAuthConfig(username, password)).toThrow();
  });
});

describe("authorizationMatchesFounder", () => {
  const config = { username: "founder", password: "local-secret" };

  it("accepts only the exact Basic authorization value", () => {
    expect(founderAuthorizationValue(config)).toBe(
      `Basic ${btoa("founder:local-secret")}`,
    );
    expect(
      authorizationMatchesFounder(founderAuthorizationValue(config), config),
    ).toBe(true);
  });

  it.each([
    null,
    "",
    "Bearer local-secret",
    `Basic ${btoa("founder:wrong-secret")}`,
    `Basic ${btoa("wrong-founder:local-secret")}`,
    `Basic ${btoa("founder:local-secret")}x`,
  ])("rejects non-matching authorization %s", (authorization) => {
    expect(authorizationMatchesFounder(authorization, config)).toBe(false);
  });
});
