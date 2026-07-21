import { PortfolioReviewListView } from "@/components/portfolio-review-list-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function PortfolioReviewsPage() {
  return (
    <WorkspaceShell>
      <PortfolioReviewListView />
    </WorkspaceShell>
  );
}
