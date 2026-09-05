import { PaperRuntimeDetailView } from "@/components/paper-runtime-detail-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default async function PaperRuntimeDetailPage({ params }: { params: Promise<{ runtimeId: string }> }) {
  const { runtimeId } = await params;
  return <WorkspaceShell><PaperRuntimeDetailView runtimeId={runtimeId} /></WorkspaceShell>;
}
