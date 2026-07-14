import { HealthPanel } from "@/components/health-panel";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function OverviewPage() {
  return (
    <WorkspaceShell>
      <div className="overview">
        <section className="overview-hero" aria-labelledby="overview-title">
          <p className="eyebrow">Overview · Sprint 152</p>
          <h1 id="overview-title">A calm control surface for reviewable paper workflows.</h1>
          <p className="overview-hero__summary">
            This first workspace boundary proves local browser-to-API connectivity. Strategy,
            governance, paper-run, portfolio, comparison, and lifecycle workspaces arrive in
            their planned sprints.
          </p>
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
              <div>
                <dt>Mode</dt>
                <dd>Founder-only · Local</dd>
              </div>
              <div>
                <dt>Execution</dt>
                <dd>Paper trading only</dd>
              </div>
              <div>
                <dt>Connection</dt>
                <dd>Same-origin API gateway</dd>
              </div>
            </dl>
          </section>
        </div>

        <section className="coming-next" aria-labelledby="coming-next-title">
          <div>
            <p className="eyebrow">Next planned workspace</p>
            <h2 id="coming-next-title">Strategies and research</h2>
          </div>
          <p>
            Sprint 153 will add the first business views. No placeholder data or unavailable
            product actions are presented here.
          </p>
          <span className="sprint-chip">S153</span>
        </section>
      </div>
    </WorkspaceShell>
  );
}
