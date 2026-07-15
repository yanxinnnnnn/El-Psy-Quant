import { PortfolioRecordDetailView } from "@/components/portfolio-record-detail-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default async function PortfolioRecordDetailPage({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = await params;
  return (
    <WorkspaceShell>
      <PortfolioRecordDetailView jobId={jobId} />
    </WorkspaceShell>
  );
}
