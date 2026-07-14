from __future__ import annotations

from pathlib import Path


def replace_exact(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one replacement target, found {count}")
    file_path.write_text(text.replace(old, new), encoding="utf-8")


replace_exact(
    "docs/strategy/future-platform-roadmap.md",
    """Status: Milestones 25 and 26 complete; Milestone 27 is in progress through
Sprint 150.""",
    """Status: Milestones 25 through 27 complete; Milestone 28 is in progress after
the Sprint 151 closeout.""",
)
replace_exact("docs/strategy/future-platform-roadmap.md", "M27 may define durable local states equivalent to:", "M27 defines the durable local states:")
replace_exact(
    "docs/strategy/future-platform-roadmap.md",
    "Long-running paper execution should move behind durable local job control in M27 rather than blocking Web requests indefinitely.",
    "Milestone 27 moved selected paper execution behind durable local job control without introducing a persistent worker or distributed queue.",
)
replace_exact("docs/strategy/future-platform-roadmap.md", "M27 should establish:", "M27 established:")
replace_exact(
    "docs/strategy/future-platform-roadmap.md",
    """### Milestone 27 — Persistence and Paper Job Control Foundation

Status: In Progress.""",
    """### Milestone 27 — Persistence and Paper Job Control Foundation

Status: Complete.""",
)
replace_exact("docs/strategy/future-platform-roadmap.md", "S151 — Milestone 27 Closeout — Next", "S151 — Milestone 27 Closeout — Complete")
replace_exact(
    "docs/strategy/future-platform-roadmap.md",
    """### Milestone 28 — Founder Paper Trading Web Workspace

Status: Planned.""",
    """### Milestone 28 — Founder Paper Trading Web Workspace

Status: In Progress.""",
)
replace_exact("docs/strategy/future-platform-roadmap.md", "S152 — Next.js Workspace Shell and API Client Foundation", "S152 — Next.js Workspace Shell and API Client Foundation — Next")
replace_exact(
    "docs/strategy/future-platform-roadmap.md",
    """The versioned durable-job API now supports submission, bounded status and
attempt inspection, explicit one-job run, queued cancellation, failed retry,
interrupted recovery, and path-free result reads. Submission does not execute.
`/run` schedules one selected post-response task; it is not a worker, scanner,
poller, scheduler, or distributed queue. Result references contain no completed
payload, and the existing synchronous `/api/v1/paper-runs` command remains
unchanged. Sprint 150 added no Web UI, authentication, broker, QMT, live, or
capital behavior.

## Current Next Step

```text
Sprint 151 — Milestone 27 Closeout
```

Sprint 151 should close Milestone 27 through verification and documentation.
Sprint 150 does not begin that closeout.""",
    """The versioned durable-job API now supports submission, bounded status and
attempt inspection, explicit one-job run, queued cancellation, failed retry,
interrupted recovery, and path-free result reads. Submission does not execute.
`/run` schedules one selected post-response task; it is not a worker, scanner,
poller, scheduler, or distributed queue. Result references contain no completed
payload, and the existing synchronous `/api/v1/paper-runs` command remains
unchanged. Sprint 150 added no Web UI, authentication, broker, QMT, live, or
capital behavior.

Sprint 151 verified the complete M27 migration chain, authority boundaries,
transaction semantics, recovery and idempotency behavior, result-reference
integration, API surface, and preserved non-goals. It changed documentation only
and closed Milestone 27.

See:

```text
docs/milestones/milestone-027-persistence-and-paper-job-control-foundation.md
docs/sprints/sprint-151-milestone-27-closeout.md
```

## Current Next Step

```text
Sprint 152 — Next.js Workspace Shell and API Client Foundation
```

Sprint 152 begins the smallest local Next.js workspace shell and typed API-client
foundation. The browser must consume the versioned API and must not directly
access SQLite, artifact directories, Python modules, QMT, MiniQMT, or a broker.""",
)
