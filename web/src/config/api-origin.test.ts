import { describe, expect, it } from "vitest";

import { DEFAULT_API_ORIGIN, resolveApiOrigin } from "./api-origin";

describe("resolveApiOrigin", () => {
  it("uses the documented default when configuration is absent", () => {
    expect(resolveApiOrigin(undefined)).toBe(DEFAULT_API_ORIGIN);
  });

  it.each([
    ["http://127.0.0.1:8000", "http://127.0.0.1:8000"],
    ["https://localhost:8443", "https://localhost:8443"],
    ["http://[::1]:8000", "http://[::1]:8000"],
    ["http://localhost/", "http://localhost"],
  ])("accepts approved loopback origin %s", (value, expected) => {
    expect(resolveApiOrigin(value)).toBe(expected);
  });

  it.each([
    "",
    " http://127.0.0.1:8000",
    "not-a-url",
    "ftp://127.0.0.1:8000",
    "http://192.168.1.10:8000",
    "http://example.com:8000",
    "http://api.localhost:8000",
    "http://user:secret@localhost:8000",
    "http://localhost:8000/api",
    "http://localhost:8000?target=remote",
    "http://localhost:8000#fragment",
  ])("rejects unsafe or malformed destination %s", (value) => {
    expect(() => resolveApiOrigin(value)).toThrow();
  });
});
