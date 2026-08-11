export type WorkspaceDestination = Readonly<{
  labelKey:
    | "overview"
    | "strategiesResearch"
    | "governanceReports"
    | "paperJobs"
    | "portfolioRecords"
    | "comparisons"
    | "portfolioReviews"
    | "paperAccounts"
    | "marketTime"
    | "strategyToRisk"
    | "lifecycleReview";
  sprint: `S${number}`;
  href?: string;
  available: boolean;
}>;

export const workspaceDestinations: readonly WorkspaceDestination[] = [
  { labelKey: "overview", sprint: "S152", href: "/", available: true },
  {
    labelKey: "strategiesResearch",
    sprint: "S153",
    href: "/strategies",
    available: true,
  },
  {
    labelKey: "governanceReports",
    sprint: "S154",
    href: "/evidence-manifests",
    available: true,
  },
  {
    labelKey: "paperJobs",
    sprint: "S155",
    href: "/paper-jobs",
    available: true,
  },
  {
    labelKey: "portfolioRecords",
    sprint: "S156",
    href: "/portfolio-records",
    available: true,
  },
  {
    labelKey: "comparisons",
    sprint: "S157",
    href: "/comparisons",
    available: true,
  },
  {
    labelKey: "portfolioReviews",
    sprint: "S175",
    href: "/portfolio-reviews",
    available: true,
  },
  {
    labelKey: "paperAccounts",
    sprint: "S186",
    href: "/paper-accounts",
    available: true,
  },
  {
    labelKey: "marketTime",
    sprint: "S194",
    href: "/market-time",
    available: true,
  },
  {
    labelKey: "strategyToRisk",
    sprint: "S204",
    href: "/strategy-to-risk",
    available: true,
  },
  {
    labelKey: "lifecycleReview",
    sprint: "S158",
    href: "/lifecycle-review",
    available: true,
  },
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
  if (destination.href === "/portfolio-reviews") {
    return (
      pathname === "/portfolio-reviews" ||
      pathname.startsWith("/portfolio-reviews/")
    );
  }
  if (destination.href === "/paper-accounts") {
    return (
      pathname === "/paper-accounts" ||
      pathname.startsWith("/paper-accounts/")
    );
  }
  if (destination.href === "/market-time") {
    return (
      pathname === "/market-time" ||
      pathname.startsWith("/market-time/")
    );
  }
  if (destination.href === "/strategy-to-risk") {
    return pathname === "/strategy-to-risk";
  }
  if (destination.href === "/lifecycle-review") {
    return pathname === "/lifecycle-review";
  }
  return pathname === destination.href || pathname.startsWith(`${destination.href}/`);
}
