import type { Locale } from "@/i18n/config";

function numberFormatter(locale: Locale) {
  return new Intl.NumberFormat(locale === "zh-CN" ? "zh-CN" : "en-US", {
    maximumFractionDigits: 4,
  });
}

function percentFormatter(locale: Locale) {
  return new Intl.NumberFormat(locale === "zh-CN" ? "zh-CN" : "en-US", {
    style: "percent",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function formatNumber(value: number | null, locale: Locale = "en"): string {
  return value === null ? (locale === "zh-CN" ? "不可用" : "Not available") : numberFormatter(locale).format(value);
}

export function formatPercentage(value: number | null, locale: Locale = "en"): string {
  return value === null ? (locale === "zh-CN" ? "不可用" : "Not available") : percentFormatter(locale).format(value);
}

export function formatDefault(value: number | null, locale: Locale = "en"): string {
  return formatNumber(value, locale);
}

export function formatDateTime(value: string, locale: Locale = "en"): string {
  if (!/(?:Z|[+-]\d{2}:\d{2})$/.test(value)) {
    return value;
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.valueOf())) {
    return value;
  }
  return new Intl.DateTimeFormat(locale === "zh-CN" ? "zh-CN" : "en-US", {
    dateStyle: "medium",
    timeStyle: "medium",
    timeZone: "UTC",
  }).format(parsed);
}
