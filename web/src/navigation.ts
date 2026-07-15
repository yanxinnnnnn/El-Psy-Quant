export type WorkspaceDestination = Readonly<{
  label: string;
  sprint: `S${number}`;
  href?: string;
  available: boolean;
}>;

export const workspaceDestinations: readonly WorkspaceDestination[] = [
  { label: "Overview", sprint: "S152", href: "/", available: true },
  {
    label: "Strategies and Research",
    sprint: "S153",
    href: "/strategies",
    available: true,
  },
  {
    label: "Governance and Reports",
    sprint: "S154",
    href: "/evidence-manifests",
    available: true,
  },
  {
    label: "Paper Runs",
    sprint: "S155",
    href: "/paper-jobs",
    available: true,
  },
  {
    label: "Portfolio Records",
    sprint: "S156",
    href: "/portfolio-records",
    available: true,
  },
  {
    label: "Comparisons",
    sprint: "S157",
    href: "/comparisons",
    available: true,
  },
  { label: "Lifecycle Review", sprint: "S158", available: false },
] as const;

export function isDestinationActive(
  destination: WorkspaceDestination,
  pathname: string,
): boolean {
  if (!destination.available || destination.href === undefined) {
    return false;
  }
  if (destination.href === "/") {
    return pathname === "/";
  }
  if (destination.href === "/strategies") {
    return (
      pathname === "/strategies" ||
      pathname.startsWith("/strategies/") ||
      pathname === "/research-runs" ||
      pathname.startsWith("/research-runs/")
    );
  }
  if (destination.href === "/paper-jobs") {
    return pathname === "/paper-jobs" || pathname.startsWith("/paper-jobs/");
  }
  if (destination.href === "/portfolio-records") {
    return (
      pathname === "/portfolio-records" ||
      pathname.startsWith("/portfolio-records/")
    );
  }
  if (destination.href === "/comparisons") {
    return pathname === "/comparisons";
  }
  return pathname === destination.href || pathname.startsWith(`${destination.href}/`);
}
