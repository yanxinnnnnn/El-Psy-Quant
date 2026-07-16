import { describe, expect, it } from "vitest";

import {
  DEFAULT_LOCALE,
  FALLBACK_LOCALE,
  LOCALE_COOKIE_NAME,
  SUPPORTED_LOCALES,
  parseLocale,
} from "@/i18n/config";
import { localeFromAcceptLanguage, resolveLocale } from "@/i18n/locale";

describe("locale policy", () => {
  it("exposes the exact approved locale allowlist and English fallback", () => {
    expect(SUPPORTED_LOCALES).toEqual(["en", "zh-CN"]);
    expect(DEFAULT_LOCALE).toBe("en");
    expect(FALLBACK_LOCALE).toBe("en");
    expect(LOCALE_COOKIE_NAME).toBe("el_psy_quant_locale");
    expect(parseLocale("en")).toBe("en");
    expect(parseLocale("zh-CN")).toBe("zh-CN");
    expect(parseLocale("zh-cn")).toBeNull();
    expect(parseLocale("fr")).toBeNull();
    expect(parseLocale("x".repeat(17))).toBeNull();
  });

  it("resolves a valid cookie before Accept-Language", () => {
    expect(resolveLocale("en", "zh-CN,zh;q=0.9")).toBe("en");
    expect(resolveLocale("zh-CN", "en-US,en;q=0.9")).toBe("zh-CN");
  });

  it("uses deterministic bounded Accept-Language matching and English fallback", () => {
    expect(localeFromAcceptLanguage("en-US;q=0.4, zh-Hans-CN;q=0.9")).toBe("zh-CN");
    expect(localeFromAcceptLanguage("zh-SG, en;q=0.5")).toBe("zh-CN");
    expect(localeFromAcceptLanguage("zh-TW, en-GB;q=0.8")).toBe("en");
    expect(localeFromAcceptLanguage("zh-CN;q=0, en;q=0.7")).toBe("en");
    expect(localeFromAcceptLanguage("fr-FR")).toBeNull();
    expect(localeFromAcceptLanguage("x".repeat(4097))).toBeNull();
    expect(resolveLocale("unsupported", "fr-FR")).toBe("en");
  });
});
