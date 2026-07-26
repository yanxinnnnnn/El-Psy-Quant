import { PaperAccountListView } from "@/components/paper-account-list-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function PaperAccountsPage() {
  return (
    <WorkspaceShell>
      <PaperAccountListView />
    </WorkspaceShell>
  );
}
