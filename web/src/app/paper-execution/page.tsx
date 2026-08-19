import { PaperExecutionWorkspace } from "@/components/paper-execution-workspace";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function PaperExecutionPage() {
  return (
    <WorkspaceShell>
      <PaperExecutionWorkspace />
    </WorkspaceShell>
  );
}
