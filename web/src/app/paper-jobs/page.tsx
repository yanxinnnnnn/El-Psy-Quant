import { PaperJobListView } from "@/components/paper-job-list-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function PaperJobsPage() {
  return (
    <WorkspaceShell>
      <PaperJobListView />
    </WorkspaceShell>
  );
}
