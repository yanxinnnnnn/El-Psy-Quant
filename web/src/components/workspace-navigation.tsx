"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { isDestinationActive, workspaceDestinations } from "@/navigation";

export function WorkspaceNavigation() {
  const pathname = usePathname();

  return (
    <nav aria-label="Founder workspace">
      <p className="navigation-label">Workspace</p>
      <ul className="navigation-list">
        {workspaceDestinations.map((destination) => {
          const active = isDestinationActive(destination, pathname);
          return (
            <li key={destination.label}>
              {destination.available && destination.href ? (
                <Link
                  className={`navigation-item ${
                    active ? "navigation-item--active" : "navigation-item--available"
                  }`}
                  href={destination.href}
                  aria-current={active ? "page" : undefined}
                >
                  <span>{destination.label}</span>
                  <span className="navigation-state">{active ? "Current" : "Open"}</span>
                </Link>
              ) : (
                <span className="navigation-item navigation-item--future" aria-disabled="true">
                  <span>{destination.label}</span>
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
