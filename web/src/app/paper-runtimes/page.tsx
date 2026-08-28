import { PaperRuntimeListView } from "@/components/paper-runtime-list-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function PaperRuntimesPage() {
  return <WorkspaceShell><PaperRuntimeListView /></WorkspaceShell>;
}
