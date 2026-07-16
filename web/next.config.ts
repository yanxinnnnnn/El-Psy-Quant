import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

import { resolveApiOrigin } from "./src/config/api-origin";

const apiOrigin = resolveApiOrigin(
  process.env.EL_PSY_QUANT_API_ORIGIN,
  process.env.EL_PSY_QUANT_ALLOW_COMPOSE_API_ORIGIN === "1",
);

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/backend/api/v1/:path*",
        destination: `${apiOrigin}/api/v1/:path*`,
      },
    ];
  },
};

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

export default withNextIntl(nextConfig);
