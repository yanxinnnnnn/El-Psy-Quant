import type { NextConfig } from "next";

import { resolveApiOrigin } from "./src/config/api-origin";

const apiOrigin = resolveApiOrigin(process.env.EL_PSY_QUANT_API_ORIGIN);

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: `${apiOrigin}/:path*`,
      },
    ];
  },
};

export default nextConfig;
