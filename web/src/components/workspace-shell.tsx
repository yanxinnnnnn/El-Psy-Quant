"use client";

import type { ReactNode } from "react";
import { useCallback } from "react";
import { useTranslations } from "next-intl";

import { LanguageSwitcher } from "@/components/language-switcher";
import { WorkspaceNavigation } from "@/components/workspace-navigation";
import { fetchDemoWorkspace } from "@/lib/api-client";
import { useApiResource } from "@/lib/use-api-resource";

export function WorkspaceShell({ children }: { children: ReactNode }) {
  const request = useCallback(() => fetchDemoWorkspace(), []);
  const { state } = useApiResource(request);
  const demoDescriptor = state.status === "success" ? state.data : null;
  const t = useTranslations("navigation");

  return (
    <div className="workspace">
      <header className="workspace-header">
        <a className="skip-link" href="#workspace-main">
          {t("skip")}
        </a>
        <div className="brand-lockup">
          <span className="brand-mark" aria-hidden="true">
            EP
          </span>
          <div>
            <p className="brand-name">El-Psy-Quant</p>
            <p className="brand-context">{t("brandContext")}</p>
          </div>
        </div>
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
            {t("discovering")}
          </div>
        ) : state.status === "error" && state.code !== "demo_workspace_not_configured" ? (
          <div className="environment-pill environment-pill--warning" role="alert">
            {t("identityUnavailable")}
          </div>
        ) : (
          <div className="environment-pill" aria-label={t("paperEnvironmentAria")}>
            <span aria-hidden="true" />
            {t("paperEnvironment")}
          </div>
        )}
        <LanguageSwitcher />
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
  );
}
