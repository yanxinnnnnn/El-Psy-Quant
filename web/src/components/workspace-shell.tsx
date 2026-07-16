"use client";

import type { ReactNode } from "react";
import { useCallback } from "react";

import { WorkspaceNavigation } from "@/components/workspace-navigation";
import { fetchDemoWorkspace } from "@/lib/api-client";
import { useApiResource } from "@/lib/use-api-resource";

export function WorkspaceShell({ children }: { children: ReactNode }) {
  const request = useCallback(() => fetchDemoWorkspace(), []);
  const { state } = useApiResource(request);
  const demoDescriptor = state.status === "success" ? state.data : null;

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
            <p className="brand-context">Founder-only paper workspace · Local</p>
          </div>
        </div>
        {demoDescriptor ? (
          <div
            className="demo-identity"
            role="status"
            aria-label="Demo Workspace: disposable example evidence, not real user data"
          >
            <strong>Demo Workspace</strong>
            <span>{demoDescriptor.warning}</span>
          </div>
        ) : state.status === "loading" ? (
          <div className="environment-pill" role="status">
            Discovering workspace
          </div>
        ) : state.status === "error" && state.code !== "demo_workspace_not_configured" ? (
          <div className="environment-pill environment-pill--warning" role="alert">
            Workspace identity unavailable
          </div>
        ) : (
          <div className="environment-pill" aria-label="Workspace environment: paper trading">
            <span aria-hidden="true" />
            Paper environment
          </div>
        )}
      </header>

      <div className="workspace-body">
        <aside className="workspace-sidebar">
          <WorkspaceNavigation />
          <div className="sidebar-note">
            <p>Milestone 28</p>
            <span>Review and explicit paper operations</span>
          </div>
        </aside>

        <main id="workspace-main" className="workspace-main" tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
}
