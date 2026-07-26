import { PaperAccountCreateView } from "@/components/paper-account-create-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function NewPaperAccountPage() {
  return (
    <WorkspaceShell>
      <PaperAccountCreateView />
    </WorkspaceShell>
  );
}
