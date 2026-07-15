import { PortfolioRecordListView } from "@/components/portfolio-record-list-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function PortfolioRecordsPage() {
  return (
    <WorkspaceShell>
      <PortfolioRecordListView />
    </WorkspaceShell>
  );
}
