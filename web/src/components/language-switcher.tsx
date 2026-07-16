"use client";

import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import { parseLocale, type Locale } from "@/i18n/config";

const LANGUAGE_OPTIONS: readonly Readonly<{ locale: Locale; label: string }>[] = [
  { locale: "en", label: "English" },
  { locale: "zh-CN", label: "简体中文" },
];

export function LanguageSwitcher() {
  const activeLocale = parseLocale(useLocale()) ?? "en";
  const router = useRouter();
  const t = useTranslations("common.languageSwitcher");
  const pendingRef = useRef(false);
  const [pendingLocale, setPendingLocale] = useState<Locale | null>(null);
  const [failed, setFailed] = useState(false);

  async function selectLocale(locale: Locale) {
    if (locale === activeLocale || pendingRef.current) {
      return;
    }
    pendingRef.current = true;
    setPendingLocale(locale);
    setFailed(false);
    try {
      const response = await fetch("/api/locale", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ locale }),
      });
      if (!response.ok) {
        throw new Error("Locale preference was rejected");
      }
      router.refresh();
    } catch {
      setFailed(true);
    } finally {
      pendingRef.current = false;
      setPendingLocale(null);
    }
  }

  return (
    <div className="language-switcher" aria-label={t("label")} role="group">
      <span className="language-switcher__label">{t("label")}</span>
      {LANGUAGE_OPTIONS.map((option) => {
        const selected = option.locale === activeLocale;
        return (
          <button
            className={selected ? "language-switcher__option language-switcher__option--active" : "language-switcher__option"}
            type="button"
            key={option.locale}
            aria-pressed={selected}
            aria-label={t("select", { language: option.label })}
            disabled={pendingLocale !== null}
            onClick={() => void selectLocale(option.locale)}
          >
            {option.label}
          </button>
        );
      })}
      <span className="visually-hidden" aria-live="polite">
        {pendingLocale ? t("updating") : failed ? t("failed") : ""}
      </span>
    </div>
  );
}
