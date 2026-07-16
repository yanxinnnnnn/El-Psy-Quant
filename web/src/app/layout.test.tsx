// @vitest-environment node

import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import type { Locale } from "@/i18n/config";
import { loadMessages } from "@/i18n/messages";

const requestLocale = vi.hoisted(() => ({ value: "en" as Locale }));

vi.mock("next-intl/server", () => ({
  getLocale: async () => requestLocale.value,
  getMessages: async () => loadMessages(requestLocale.value),
  getTranslations: async () => {
    const metadata = loadMessages(requestLocale.value).common.metadata;
    return (key: keyof typeof metadata) => metadata[key];
  },
}));

import RootLayout, { generateMetadata } from "./layout";

describe("localized root layout", () => {
  it.each([
    ["en", "El-Psy-Quant · Founder Workspace", "Local Founder paper-trading review workspace"],
    ["zh-CN", "El-Psy-Quant · 创始人工作台", "本地创始人模拟交易审查工作台"],
  ] as const)("emits exact %s html language and metadata", async (locale, title, description) => {
    requestLocale.value = locale;
    const markup = renderToStaticMarkup(await RootLayout({ children: <main>content</main> }));
    expect(markup).toContain(`<html lang="${locale}">`);
    await expect(generateMetadata()).resolves.toEqual({ title, description });
  });
});
