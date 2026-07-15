import { EvidenceManifestListView } from "@/components/evidence-manifest-list-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function EvidenceManifestsPage() {
  return (
    <WorkspaceShell>
      <EvidenceManifestListView />
    </WorkspaceShell>
  );
}
