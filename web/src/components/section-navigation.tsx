"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const sections = [
  { label: "Strategies", href: "/strategies" },
  { label: "Research runs", href: "/research-runs" },
] as const;

export function SectionNavigation() {
  const pathname = usePathname();

  return (
    <nav className="section-navigation" aria-label="Strategies and research">
      {sections.map((section) => {
        const active = pathname === section.href || pathname.startsWith(`${section.href}/`);
        return (
          <Link
            key={section.href}
            href={section.href}
            className={active ? "section-navigation__active" : undefined}
            aria-current={active ? "page" : undefined}
          >
            {section.label}
          </Link>
        );
      })}
    </nav>
  );
}
