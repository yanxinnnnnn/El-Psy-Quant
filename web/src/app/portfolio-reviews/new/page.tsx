import { PortfolioReviewCreateView } from "@/components/portfolio-review-create-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function NewPortfolioReviewPage() {
  return (
    <WorkspaceShell>
      <PortfolioReviewCreateView />
    </WorkspaceShell>
  );
}
