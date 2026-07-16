"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { usePathname } from "next/navigation";

const sections = [
  { labelKey: "strategies", href: "/strategies" },
  { labelKey: "researchRuns", href: "/research-runs" },
] as const;

export function SectionNavigation() {
  const pathname = usePathname();
  const t = useTranslations("navigation");

  return (
    <nav className="section-navigation" aria-label={t("strategySectionAria")}>
      {sections.map((section) => {
        const active = pathname === section.href || pathname.startsWith(`${section.href}/`);
        return (
          <Link
            key={section.href}
            href={section.href}
            className={active ? "section-navigation__active" : undefined}
            aria-current={active ? "page" : undefined}
          >
            {t(section.labelKey)}
          </Link>
        );
      })}
    </nav>
  );
}
