import { PortfolioReviewDetailView } from "@/components/portfolio-review-detail-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default async function PortfolioReviewDetailPage({
  params,
}: {
  params: Promise<{ reviewId: string }>;
}) {
  const { reviewId } = await params;
  return (
    <WorkspaceShell>
      <PortfolioReviewDetailView reviewId={reviewId} />
    </WorkspaceShell>
  );
}
