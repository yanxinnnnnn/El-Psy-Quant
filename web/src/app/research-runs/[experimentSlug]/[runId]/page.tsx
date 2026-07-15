import { ResearchRunDetailView } from "@/components/research-run-detail-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default async function ResearchRunDetailPage({
  params,
}: {
  params: Promise<{ experimentSlug: string; runId: string }>;
}) {
  const { experimentSlug, runId } = await params;
  return (
    <WorkspaceShell>
      <ResearchRunDetailView experimentSlug={experimentSlug} runId={runId} />
    </WorkspaceShell>
  );
}
