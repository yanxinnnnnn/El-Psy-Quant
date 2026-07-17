import { FounderDashboard } from "@/components/founder-dashboard";
import { WorkspaceShell } from "@/components/workspace-shell";

export default async function OverviewPage() {
  return (
    <WorkspaceShell>
      <FounderDashboard />
    </WorkspaceShell>
  );
}
