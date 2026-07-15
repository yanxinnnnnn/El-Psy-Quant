import { ComparisonWorkspace } from "@/components/comparison-workspace";
import { WorkspaceShell } from "@/components/workspace-shell";

type ComparisonsPageProps = Readonly<{
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}>;

export default async function ComparisonsPage({ searchParams }: ComparisonsPageProps) {
  const rawJobIds = (await searchParams).job_id;
  const jobIds =
    rawJobIds === undefined
      ? []
      : Array.isArray(rawJobIds)
        ? rawJobIds
        : [rawJobIds];
  return (
    <WorkspaceShell>
      <ComparisonWorkspace jobIds={jobIds} />
    </WorkspaceShell>
  );
}
