import { StrategyListView } from "@/components/strategy-list-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function StrategiesPage() {
  return (
    <WorkspaceShell>
      <StrategyListView />
    </WorkspaceShell>
  );
}
