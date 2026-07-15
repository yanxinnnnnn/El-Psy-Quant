import { PaperJobSubmissionView } from "@/components/paper-job-submission-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function NewPaperJobPage() {
  return (
    <WorkspaceShell>
      <PaperJobSubmissionView />
    </WorkspaceShell>
  );
}
