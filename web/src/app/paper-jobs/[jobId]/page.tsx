import { PaperJobDetailView } from "@/components/paper-job-detail-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default async function PaperJobDetailPage({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = await params;
  return (
    <WorkspaceShell>
      <PaperJobDetailView jobId={jobId} />
    </WorkspaceShell>
  );
}
