import Link from "next/link";
import { getTranslations } from "next-intl/server";

import { HealthPanel } from "@/components/health-panel";
import { FounderFirstRunPanel } from "@/components/founder-first-run-panel";
import { WorkspaceShell } from "@/components/workspace-shell";

export default async function OverviewPage() {
  const t = await getTranslations("overview");
  return (
    <WorkspaceShell>
      <div className="overview">
        <section className="overview-hero" aria-labelledby="overview-title">
          <p className="eyebrow">{t("hero.eyebrow")}</p>
          <h1 id="overview-title">{t("hero.title")}</h1>
          <p className="overview-hero__summary">
            {t("hero.summary")}
          </p>
          <div className="overview-actions">
            <Link className="primary-link" href="/strategies">{t("hero.strategies")}</Link>
            <Link className="text-link" href="/research-runs">{t("hero.research")}</Link>
            <Link className="text-link" href="/evidence-manifests">{t("hero.evidence")}</Link>
            <Link className="text-link" href="/paper-jobs">{t("hero.paperJobs")}</Link>
            <Link className="text-link" href="/portfolio-records">{t("hero.portfolio")}</Link>
            <Link className="text-link" href="/comparisons">{t("hero.comparisons")}</Link>
            <Link className="text-link" href="/lifecycle-review">{t("hero.lifecycle")}</Link>
          </div>
        </section>

        <FounderFirstRunPanel />

        <div className="overview-grid">
          <HealthPanel />
          <section className="boundary-card" aria-labelledby="workspace-boundary-title">
            <p className="eyebrow">{t("boundary.eyebrow")}</p>
            <h2 id="workspace-boundary-title">{t("boundary.title")}</h2>
            <p>{t("boundary.description")}</p>
            <dl className="boundary-list">
              <div><dt>{t("boundary.modeLabel")}</dt><dd>{t("boundary.mode")}</dd></div>
              <div><dt>{t("boundary.executionLabel")}</dt><dd>{t("boundary.execution")}</dd></div>
              <div><dt>{t("boundary.connectionLabel")}</dt><dd>{t("boundary.connection")}</dd></div>
            </dl>
          </section>
        </div>

        <section className="coming-next" aria-labelledby="workspace-startup-title">
          <div>
            <p className="eyebrow">{t("startup.eyebrow")}</p>
            <h2 id="workspace-startup-title">{t("startup.title")}</h2>
          </div>
          <p>
            {t("startup.description")}
          </p>
          <span className="sprint-chip">{t("startup.chip")}</span>
        </section>
      </div>
    </WorkspaceShell>
  );
}
