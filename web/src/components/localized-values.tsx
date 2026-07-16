"use client";

import { useLocale, useTranslations } from "next-intl";

import { parseLocale } from "@/i18n/config";
import { formatDateTime, formatNumber, formatPercentage } from "@/lib/formatters";

export function LocalizedNumber({ value, percentage = false }: { value: number | null; percentage?: boolean }) {
  const locale = parseLocale(useLocale()) ?? "en";
  const t = useTranslations("common");
  if (value === null) {
    return <>{t("states.notAvailable")}</>;
  }
  return (
    <span className="localized-value">
      <span>{percentage ? formatPercentage(value, locale) : formatNumber(value, locale)}</span>
      <span className="raw-value">{t("rawValue", { value: String(value) })}</span>
    </span>
  );
}

export function LocalizedTimestamp({ value }: { value: string }) {
  const locale = parseLocale(useLocale()) ?? "en";
  const t = useTranslations("common");
  const formatted = formatDateTime(value, locale);
  return (
    <span className="localized-value">
      <span>{formatted}</span>
      <span className="raw-value"><span className="visually-hidden">{t("rawUtc", { value: "" })}</span><code>{value}</code></span>
    </span>
  );
}
