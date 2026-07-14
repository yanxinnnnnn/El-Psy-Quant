from __future__ import annotations

from pathlib import Path


def replace_exact(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one replacement target, found {count}")
    file_path.write_text(text.replace(old, new), encoding="utf-8")


replace_exact("AGENTS.md", "Milestones 18–26 are complete:", "Milestones 18–27 are complete:")
replace_exact(
    "AGENTS.md",
    """M25 — Paper Trading Productization Planning
M26 — Paper Trading Application Service Foundation
```""",
    """M25 — Paper Trading Productization Planning
M26 — Paper Trading Application Service Foundation
M27 — Persistence and Paper Job Control Foundation
```""",
)
replace_exact(
    "AGENTS.md",
    """Milestone 26 then established a thin local FastAPI application and versioned API boundary over selected existing capabilities. It delivered deterministic strategy reads, bounded artifact inspection, synchronous in-memory paper execution, and stateless lifecycle proposal/review commands while preserving domain and artifact authority.

## Current Focus""",
    """Milestone 26 then established a thin local FastAPI application and versioned API boundary over selected existing capabilities. It delivered deterministic strategy reads, bounded artifact inspection, synchronous in-memory paper execution, and stateless lifecycle proposal/review commands while preserving domain and artifact authority.

Milestone 27 added explicit local SQLite and Alembic ownership, a compact artifact index, durable paper-job requests and operational state, replay-safe submission, attempt audit, manual recovery and retry, compact result references, and durable job API control while preserving completed-file authority.

## Current Focus""",
)
replace_exact(
    "AGENTS.md",
    """The current milestone is:

```text
Milestone 27 — Persistence and Paper Job Control Foundation
```""",
    """The current milestone is:

```text
Milestone 28 — Founder Paper Trading Web Workspace
```""",
)
replace_exact(
    "AGENTS.md",
    """Sprint 149 added migration `0004_paper_job_recovery_audit` with exactly the
`paper_job_submission_keys` and `paper_job_attempts` tables. Explicit caller
keys now provide digest-bound replay-safe submission without claiming
exactly-once execution. New runner claims create compact attempt audit; expected
failures persist only approved sanitized codes. Interrupted-job recovery and
failed-job retry are explicit manual services that never rewrite authoritative
outputs. It added no result reference, API route, worker, polling, automatic
recovery, or Sprint 150 behavior.

The next sprint is:

```text
Sprint 150 — Durable Job API and Result Reference Integration
```

Sprint 150 may add only the durable-job API and result-reference integration
defined by its authoritative issue. It must preserve Sprint 149 replay,
attempt-audit, manual-recovery, file-authority, and transaction boundaries.""",
    """Sprint 149 added migration `0004_paper_job_recovery_audit` with exactly the
`paper_job_submission_keys` and `paper_job_attempts` tables. Explicit caller
keys now provide digest-bound replay-safe submission without claiming
exactly-once execution. New runner claims create compact attempt audit; expected
failures persist only approved sanitized codes. Interrupted-job recovery and
failed-job retry are explicit manual services that never rewrite authoritative
outputs.

Sprint 150 added migration `0005_paper_job_result_references`, one compact
job-owned result-reference registry, fixed server-owned paper output paths,
atomic API-owned job/attempt/reference completion, strict authoritative result
reads, and the durable `/api/v1/paper-jobs` API. Durable routes reject missing,
unavailable, or pre-0005 databases before mutation. Submission remains
non-executing, and `/run` schedules only one selected post-response callback.

Sprint 151 closed Milestone 27 through documentation and verification only. No
runtime, schema, migration, dependency, test, worker, or Web implementation was
added.

The next sprint is:

```text
Sprint 152 — Next.js Workspace Shell and API Client Foundation
```

Sprint 152 may establish only the smallest local Next.js workspace shell,
navigation, configuration, and typed API-client foundation. The browser must use
the API and must not directly access SQLite, artifact files, Python modules,
QMT, MiniQMT, or a broker.""",
)
replace_exact(
    "AGENTS.md",
    """M27 — S145-S151 Persistence and Paper Job Control Foundation — In Progress
M28 — S152-S159 Founder Paper Trading Web Workspace""",
    """M27 — S145-S151 Persistence and Paper Job Control Foundation — Complete
M28 — S152-S159 Founder Paper Trading Web Workspace — In Progress""",
)
replace_exact("AGENTS.md", "M27 may define durable local states equivalent to:", "M27 defines the durable local states:")
replace_exact(
    "AGENTS.md",
    """- M26 completed without product database or background-worker requirements.
- Move long-running paper execution behind durable local job control in M27.""",
    """- M26 completed without product database or background-worker requirements.
- M27 completed durable local paper-job control with selected-job post-response execution.
- M28 UI code must consume the API and must not own backend operational semantics.""",
)
