export const SUPPORTED_LOCALES = ["en", "zh-CN"] as const;

export type Locale = (typeof SUPPORTED_LOCALES)[number];

export const DEFAULT_LOCALE: Locale = "en";
export const FALLBACK_LOCALE: Locale = "en";
export const LOCALE_COOKIE_NAME = "el_psy_quant_locale";
export const LOCALE_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 365;
export const MAX_LOCALE_VALUE_LENGTH = 16;

export function parseLocale(value: unknown): Locale | null {
  if (typeof value !== "string" || value.length > MAX_LOCALE_VALUE_LENGTH) {
    return null;
  }
  return SUPPORTED_LOCALES.find((locale) => locale === value) ?? null;
}
