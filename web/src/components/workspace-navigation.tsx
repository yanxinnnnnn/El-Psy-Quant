"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { usePathname } from "next/navigation";

import { isDestinationActive, workspaceDestinations } from "@/navigation";

export function WorkspaceNavigation() {
  const pathname = usePathname();
  const t = useTranslations("navigation");
  const common = useTranslations("common.states");

  return (
    <nav aria-label={t("ariaLabel")}>
      <p className="navigation-label">{t("workspace")}</p>
      <ul className="navigation-list">
        {workspaceDestinations.map((destination) => {
          const active = isDestinationActive(destination, pathname);
          return (
            <li key={destination.labelKey}>
              {destination.available && destination.href ? (
                <Link
                  className={`navigation-item ${
                    active ? "navigation-item--active" : "navigation-item--available"
                  }`}
                  href={destination.href}
                  aria-current={active ? "page" : undefined}
                >
                  <span>{t(destination.labelKey)}</span>
                  <span className="navigation-state">{active ? common("current") : common("open")}</span>
                </Link>
              ) : (
                <span className="navigation-item navigation-item--future" aria-disabled="true">
                  <span>{t(destination.labelKey)}</span>
                  <span className="navigation-state">{destination.sprint}</span>
                </span>
              )}
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
