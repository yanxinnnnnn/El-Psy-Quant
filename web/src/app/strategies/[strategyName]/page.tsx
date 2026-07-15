import { StrategyDetailView } from "@/components/strategy-detail-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default async function StrategyDetailPage({
  params,
}: {
  params: Promise<{ strategyName: string }>;
}) {
  const { strategyName } = await params;
  return (
    <WorkspaceShell>
      <StrategyDetailView strategyName={strategyName} />
    </WorkspaceShell>
  );
}
