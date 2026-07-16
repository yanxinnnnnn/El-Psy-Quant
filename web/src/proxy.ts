import { NextResponse, type NextRequest } from "next/server";

import {
  authorizationMatchesFounder,
  FOUNDER_AUTH_REALM,
  resolveFounderAuthConfig,
} from "@/config/founder-auth";

export function proxy(request: NextRequest) {
  const config = resolveFounderAuthConfig(
    process.env.EL_PSY_QUANT_FOUNDER_USERNAME,
    process.env.EL_PSY_QUANT_FOUNDER_PASSWORD,
  );
  if (
    config === null ||
    authorizationMatchesFounder(request.headers.get("Authorization"), config)
  ) {
    return NextResponse.next();
  }

  return new NextResponse("Founder authentication required", {
    status: 401,
    headers: {
      "Cache-Control": "no-store",
      "Content-Type": "text/plain; charset=utf-8",
      "WWW-Authenticate": `Basic realm="${FOUNDER_AUTH_REALM}", charset="UTF-8"`,
    },
  });
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
