export type WorkspaceDestination = Readonly<{
  label: string;
  sprint: `S${number}`;
  href?: string;
  available: boolean;
}>;

export const workspaceDestinations: readonly WorkspaceDestination[] = [
  { label: "Overview", sprint: "S152", href: "/", available: true },
  { label: "Strategies and Research", sprint: "S153", available: false },
  { label: "Governance and Reports", sprint: "S154", available: false },
  { label: "Paper Runs", sprint: "S155", available: false },
  { label: "Portfolio Records", sprint: "S156", available: false },
  { label: "Comparisons", sprint: "S157", available: false },
  { label: "Lifecycle Review", sprint: "S158", available: false },
] as const;
