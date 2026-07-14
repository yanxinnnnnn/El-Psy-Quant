import type { NextConfig } from "next";

import { resolveApiOrigin } from "./src/config/api-origin";

const apiOrigin = resolveApiOrigin(process.env.EL_PSY_QUANT_API_ORIGIN);

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/backend/api/v1/:path*",
        destination: `${apiOrigin}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
