import { LifecycleReviewWorkspace } from "@/components/lifecycle-review-workspace";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function LifecycleReviewPage() {
  return (
    <WorkspaceShell>
      <LifecycleReviewWorkspace />
    </WorkspaceShell>
  );
}
