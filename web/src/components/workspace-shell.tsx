"use client";

import { createContext, type ReactNode, useCallback, useContext } from "react";
import { useTranslations } from "next-intl";

import { LanguageSwitcher } from "@/components/language-switcher";
import { WorkspaceNavigation } from "@/components/workspace-navigation";
import {
  fetchDemoWorkspace,
  type DemoWorkspaceDescriptorResponse,
} from "@/lib/api-client";
import {
  useApiResource,
  type ApiResourceState,
} from "@/lib/use-api-resource";

type WorkspaceEnvironment = {
  state: ApiResourceState<DemoWorkspaceDescriptorResponse>;
  retry: () => number;
};

const WorkspaceEnvironmentContext = createContext<WorkspaceEnvironment | null>(
  null,
);

export function useWorkspaceEnvironment(): WorkspaceEnvironment {
  const environment = useContext(WorkspaceEnvironmentContext);
  if (environment === null) {
    throw new Error(
      "useWorkspaceEnvironment must be used inside WorkspaceShell.",
    );
  }
  return environment;
}

export function WorkspaceShell({ children }: { children: ReactNode }) {
  const request = useCallback(() => fetchDemoWorkspace(), []);
  const { state, retry } = useApiResource(request);
  const demoDescriptor = state.status === "success" ? state.data : null;
  const t = useTranslations("navigation");

  return (
    <WorkspaceEnvironmentContext.Provider value={{ state, retry }}>
      <div className="workspace">
        <header className="workspace-header">
          <a className="skip-link" href="#workspace-main">
            {t("skip")}
          </a>
          <div className="workspace-header__identity">
            <div className="brand-lockup">
              <span className="brand-mark" aria-hidden="true">
                EP
              </span>
              <div>
                <p className="brand-name">El-Psy-Quant</p>
                <p className="brand-context">{t("brandContext")}</p>
              </div>
            </div>
          </div>
          <div className="workspace-header__tools">
            {demoDescriptor ? (
              <div
                className="demo-identity"
                role="status"
                aria-label={t("demoAria")}
              >
                <strong>{t("demo")}</strong>
                <span>{t("demoWarning")}</span>
              </div>
            ) : state.status === "loading" ? (
              <div className="environment-pill" role="status">
                <span aria-hidden="true" />
                {t("discovering")}
              </div>
            ) : state.status === "error" && state.code !== "demo_workspace_not_configured" ? (
              <div className="environment-pill environment-pill--warning" role="alert">
                <span aria-hidden="true" />
                {t("identityUnavailable")}
              </div>
            ) : (
              <div className="environment-pill" role="status" aria-label={t("paperEnvironmentAria")}>
                <span aria-hidden="true" />
                {t("paperEnvironment")}
              </div>
            )}
            <LanguageSwitcher />
          </div>
        </header>

        <div className="workspace-body">
          <aside className="workspace-sidebar">
            <WorkspaceNavigation />
            <div className="sidebar-note">
              <p>{t("sidebarMilestone")}</p>
              <span>{t("sidebarNote")}</span>
            </div>
          </aside>

          <main id="workspace-main" className="workspace-main" tabIndex={-1}>
            {children}
          </main>
        </div>
      </div>
    </WorkspaceEnvironmentContext.Provider>
  );
}
