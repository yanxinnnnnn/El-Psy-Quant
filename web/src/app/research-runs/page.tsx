import { ResearchRunListView } from "@/components/research-run-list-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function ResearchRunsPage() {
  return (
    <WorkspaceShell>
      <ResearchRunListView />
    </WorkspaceShell>
  );
}
