import type { ReactNode } from "react";

import { WorkspaceNavigation } from "@/components/workspace-navigation";

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
          <WorkspaceNavigation />
          <div className="sidebar-note">
            <p>Milestone 28</p>
            <span>Research and governance inspection</span>
          </div>
        </aside>

        <main id="workspace-main" className="workspace-main" tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
}
