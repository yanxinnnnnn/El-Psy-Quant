import Link from "next/link";

import { HealthPanel } from "@/components/health-panel";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function OverviewPage() {
  return (
    <WorkspaceShell>
      <div className="overview">
        <section className="overview-hero" aria-labelledby="overview-title">
          <p className="eyebrow">Overview · Sprint 153</p>
          <h1 id="overview-title">A calm control surface for reviewable paper workflows.</h1>
          <p className="overview-hero__summary">
            The workspace now supports backend-owned strategy definitions and saved research
            result inspection while keeping execution, artifacts, and calculations outside the
            browser.
          </p>
          <div className="overview-actions">
            <Link className="primary-link" href="/strategies">
              Browse strategies
            </Link>
            <Link className="text-link" href="/research-runs">
              Inspect research runs
            </Link>
          </div>
        </section>

        <div className="overview-grid">
          <HealthPanel />
          <section className="boundary-card" aria-labelledby="workspace-boundary-title">
            <p className="eyebrow">Workspace boundary</p>
            <h2 id="workspace-boundary-title">Review first. Operate deliberately.</h2>
            <p>
              The browser uses the versioned FastAPI contract through a fixed same-origin
              gateway. Completed artifacts and backend domain services remain authoritative.
            </p>
            <dl className="boundary-list">
              <div><dt>Mode</dt><dd>Founder-only · Local</dd></div>
              <div><dt>Execution</dt><dd>Paper trading only</dd></div>
              <div><dt>Connection</dt><dd>Same-origin API gateway</dd></div>
            </dl>
          </section>
        </div>

        <section className="coming-next" aria-labelledby="coming-next-title">
          <div>
            <p className="eyebrow">Next planned workspace</p>
            <h2 id="coming-next-title">Governance and reports</h2>
          </div>
          <p>
            Sprint 154 will add bounded governance evidence and report-artifact views. Those
            future routes and controls are not introduced in this sprint.
          </p>
          <span className="sprint-chip">S154</span>
        </section>
      </div>
    </WorkspaceShell>
  );
}
