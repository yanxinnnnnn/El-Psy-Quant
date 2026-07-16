import { describe, expect, it } from "vitest";

import nextConfig from "./next.config";
import { resolveApiOrigin } from "./src/config/api-origin";

describe("Next.js API rewrite", () => {
  it("proxies only the versioned FastAPI boundary", async () => {
    expect(nextConfig.output).toBe("standalone");
    expect(nextConfig.rewrites).toBeTypeOf("function");
    if (nextConfig.rewrites === undefined) {
      throw new Error("expected the versioned API rewrite");
    }

    const rewrites = await nextConfig.rewrites();
    const apiOrigin = resolveApiOrigin(process.env.EL_PSY_QUANT_API_ORIGIN);

    expect(rewrites).toEqual([
      {
        source: "/api/backend/api/v1/:path*",
        destination: `${apiOrigin}/api/v1/:path*`,
      },
    ]);
    expect(rewrites).not.toContainEqual(
      expect.objectContaining({ source: "/api/backend/:path*" }),
    );
  });
});
