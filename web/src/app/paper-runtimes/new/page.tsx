import { PaperRuntimeCreateView } from "@/components/paper-runtime-create-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function NewPaperRuntimePage() {
  return <WorkspaceShell><PaperRuntimeCreateView /></WorkspaceShell>;
}
