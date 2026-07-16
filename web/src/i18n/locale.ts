import { cookies, headers } from "next/headers";

import {
  DEFAULT_LOCALE,
  LOCALE_COOKIE_NAME,
  parseLocale,
  type Locale,
} from "@/i18n/config";

type LanguagePreference = Readonly<{
  locale: Locale;
  quality: number;
  index: number;
}>;

function localeFromLanguageTag(tag: string): Locale | null {
  const normalized = tag.trim().toLowerCase();
  if (normalized === "en" || normalized.startsWith("en-")) {
    return "en";
  }
  if (
    normalized === "zh" ||
    normalized === "zh-cn" ||
    normalized === "zh-hans" ||
    normalized.startsWith("zh-hans-") ||
    normalized === "zh-sg"
  ) {
    return "zh-CN";
  }
  return null;
}

export function localeFromAcceptLanguage(value: string | null | undefined): Locale | null {
  if (!value || value.length > 4096) {
    return null;
  }
  const preferences: LanguagePreference[] = [];
  value.split(",").forEach((entry, index) => {
    const [tag = "", ...parameters] = entry.trim().split(";");
    const locale = localeFromLanguageTag(tag);
    if (locale === null) {
      return;
    }
    let quality = 1;
    for (const parameter of parameters) {
      const match = /^q=(0(?:\.\d{0,3})?|1(?:\.0{0,3})?)$/i.exec(parameter.trim());
      if (match) {
        quality = Number(match[1]);
      }
    }
    if (quality > 0) {
      preferences.push({ locale, quality, index });
    }
  });
  preferences.sort((left, right) => right.quality - left.quality || left.index - right.index);
  return preferences[0]?.locale ?? null;
}

export function resolveLocale(
  cookieValue: unknown,
  acceptLanguage: string | null | undefined,
): Locale {
  return parseLocale(cookieValue) ?? localeFromAcceptLanguage(acceptLanguage) ?? DEFAULT_LOCALE;
}

export async function resolveRequestLocale(): Promise<Locale> {
  const [cookieStore, headerStore] = await Promise.all([cookies(), headers()]);
  return resolveLocale(
    cookieStore.get(LOCALE_COOKIE_NAME)?.value,
    headerStore.get("accept-language"),
  );
}
