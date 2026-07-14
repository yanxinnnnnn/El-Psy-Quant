import type { ReactNode } from "react";

import { workspaceDestinations } from "@/navigation";

export function WorkspaceShell({ children }: { children: ReactNode }) {
  return (
    <div className="workspace">
      <header className="workspace-header">
        <a className="skip-link" href="#workspace-main">
          Skip to workspace content
        </a>
        <div className="brand-lockup">
          <span className="brand-mark" aria-hidden="true">
            EP
          </span>
          <div>
            <p className="brand-name">El-Psy-Quant</p>
            <p className="brand-context">Founder paper workspace · Local only</p>
          </div>
        </div>
        <div className="environment-pill" aria-label="Workspace environment: paper trading">
          <span aria-hidden="true" />
          Paper environment
        </div>
      </header>

      <div className="workspace-body">
        <aside className="workspace-sidebar">
          <nav aria-label="Founder workspace">
            <p className="navigation-label">Workspace</p>
            <ul className="navigation-list">
              {workspaceDestinations.map((destination) => (
                <li key={destination.label}>
                  {destination.available && destination.href ? (
                    <a className="navigation-item navigation-item--active" href={destination.href}>
                      <span>{destination.label}</span>
                      <span className="navigation-state">Current</span>
                    </a>
                  ) : (
                    <span className="navigation-item navigation-item--future" aria-disabled="true">
                      <span>{destination.label}</span>
                      <span className="navigation-state">{destination.sprint}</span>
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </nav>
          <div className="sidebar-note">
            <p>Milestone 28</p>
            <span>Workspace foundation</span>
          </div>
        </aside>

        <main id="workspace-main" className="workspace-main" tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
}
