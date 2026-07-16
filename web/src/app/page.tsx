import Link from "next/link";

import { HealthPanel } from "@/components/health-panel";
import { FounderFirstRunPanel } from "@/components/founder-first-run-panel";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function OverviewPage() {
  return (
    <WorkspaceShell>
      <div className="overview">
        <section className="overview-hero" aria-labelledby="overview-title">
          <p className="eyebrow">Overview · Local Web MVP</p>
          <h1 id="overview-title">A calm control surface for reviewable paper workflows.</h1>
          <p className="overview-hero__summary">
            One authenticated local workspace now connects the existing backend-owned
            research, governance, paper, portfolio, comparison, and lifecycle workflows.
          </p>
          <div className="overview-actions">
            <Link className="primary-link" href="/strategies">Browse strategies</Link>
            <Link className="text-link" href="/research-runs">Inspect research runs</Link>
            <Link className="text-link" href="/evidence-manifests">Inspect governance evidence</Link>
            <Link className="text-link" href="/paper-jobs">Operate paper jobs</Link>
            <Link className="text-link" href="/portfolio-records">Inspect portfolio records</Link>
            <Link className="text-link" href="/comparisons">Compare paper results</Link>
            <Link className="text-link" href="/lifecycle-review">Review lifecycle evidence</Link>
          </div>
        </section>

        <FounderFirstRunPanel />

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

        <section className="coming-next" aria-labelledby="workspace-startup-title">
          <div>
            <p className="eyebrow">Explicit first-run choice</p>
            <h2 id="workspace-startup-title">Standard or isolated Demo Workspace</h2>
          </div>
          <p>
            Operators choose clean real-user storage or a separately named disposable
            Demo volume. This page never seeds or initializes either workspace.
          </p>
          <span className="sprint-chip">Local MVP</span>
        </section>
      </div>
    </WorkspaceShell>
  );
}
