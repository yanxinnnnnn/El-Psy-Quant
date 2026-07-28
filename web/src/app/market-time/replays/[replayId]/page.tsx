import { MarketDataReplayDetailView } from "@/components/market-data-replay-detail-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default async function MarketDataReplayDetailPage({
  params,
}: {
  params: Promise<{ replayId: string }>;
}) {
  const { replayId } = await params;
  return (
    <WorkspaceShell>
      <MarketDataReplayDetailView replayId={replayId} />
    </WorkspaceShell>
  );
}
