import { PaperAccountDetailView } from "@/components/paper-account-detail-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default async function PaperAccountDetailPage({
  params,
}: {
  params: Promise<{ accountId: string }>;
}) {
  const { accountId } = await params;
  return (
    <WorkspaceShell>
      <PaperAccountDetailView accountId={accountId} />
    </WorkspaceShell>
  );
}
