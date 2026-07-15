import { EvidenceManifestDetailView } from "@/components/evidence-manifest-detail-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default async function EvidenceManifestDetailPage({
  params,
}: {
  params: Promise<{ manifestType: string; artifactKey: string }>;
}) {
  const { manifestType, artifactKey } = await params;
  return (
    <WorkspaceShell>
      <EvidenceManifestDetailView
        manifestType={manifestType}
        artifactKey={artifactKey}
      />
    </WorkspaceShell>
  );
}
