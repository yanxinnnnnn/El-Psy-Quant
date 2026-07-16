import { NextResponse } from "next/server";

import {
  LOCALE_COOKIE_MAX_AGE_SECONDS,
  LOCALE_COOKIE_NAME,
  parseLocale,
} from "@/i18n/config";

export async function POST(request: Request) {
  let value: unknown;
  try {
    const body = await request.json() as { locale?: unknown };
    value = body.locale;
  } catch {
    return NextResponse.json({ error: "invalid_locale_preference" }, { status: 400 });
  }
  const locale = parseLocale(value);
  if (locale === null) {
    return NextResponse.json({ error: "invalid_locale_preference" }, { status: 400 });
  }
  const response = NextResponse.json({ locale });
  response.cookies.set({
    name: LOCALE_COOKIE_NAME,
    value: locale,
    path: "/",
    sameSite: "lax",
    httpOnly: true,
    maxAge: LOCALE_COOKIE_MAX_AGE_SECONDS,
  });
  return response;
}
