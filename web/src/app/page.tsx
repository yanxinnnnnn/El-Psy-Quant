import Link from "next/link";

import { HealthPanel } from "@/components/health-panel";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function OverviewPage() {
  return (
    <WorkspaceShell>
      <div className="overview">
        <section className="overview-hero" aria-labelledby="overview-title">
          <p className="eyebrow">Overview · Sprint 155</p>
          <h1 id="overview-title">A calm control surface for reviewable paper workflows.</h1>
          <p className="overview-hero__summary">
            The workspace now adds deliberate durable paper-job submission, status,
            attempt audit, and manual controls to backend-owned strategy, research,
            governance, and report inspection.
          </p>
          <div className="overview-actions">
            <Link className="primary-link" href="/strategies">Browse strategies</Link>
            <Link className="text-link" href="/research-runs">Inspect research runs</Link>
            <Link className="text-link" href="/evidence-manifests">Inspect governance evidence</Link>
            <Link className="text-link" href="/paper-jobs">Operate paper jobs</Link>
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
              <div><dt>Execution</dt><dd>Explicit paper commands only</dd></div>
              <div><dt>Connection</dt><dd>Same-origin API gateway</dd></div>
            </dl>
          </section>
        </div>

        <section className="coming-next" aria-labelledby="coming-next-title">
          <div>
            <p className="eyebrow">Next planned workspace</p>
            <h2 id="coming-next-title">Equity, positions, orders, and fills</h2>
          </div>
          <p>
            Sprint 156 will add authoritative result inspection. Sprint 155 shows only
            backend result availability and never opens result contents or polls job status.
          </p>
          <span className="sprint-chip">S156</span>
        </section>
      </div>
    </WorkspaceShell>
  );
}
