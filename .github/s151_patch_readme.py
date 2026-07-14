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
    "README.md",
    """Milestones 1–26 are complete. **Milestone 27 — Persistence and Paper Job
Control Foundation** is in progress.

The latest completed sprint is **Sprint 150 — Durable Job API and Result
Reference Integration**.

Milestone 26 established a thin local application and versioned API boundary over selected existing capabilities:""",
    """Milestones 1–27 are complete. **Milestone 28 — Founder Paper Trading Web
Workspace** is in progress.

The latest completed sprint is **Sprint 151 — Milestone 27 Closeout**.

Milestone 27 established durable local product persistence and manually controlled
paper-job operations beneath the existing versioned application API:""",
)
replace_exact(
    "README.md",
    """Milestone 27 is in progress. Sprint 150 added the versioned durable paper-job
API, one selected-job post-response execution hook, compact result references,
and safe authoritative result reads while keeping output files authoritative.

Sprints 138 through 150 are complete. The next sprint is:

```text
Sprint 151 — Milestone 27 Closeout
```""",
    """Milestone 27 is complete. It delivered explicit SQLite and Alembic ownership,
a compact rebuildable artifact index, durable paper-job requests and operational
state, replay-safe submission, attempt audit, manual recovery and retry, compact
result references, and a versioned durable-job API while keeping completed files
authoritative.

Milestone 28 now begins the first Founder-facing local Web workspace. Sprints 138
through 151 are complete. The next sprint is:

```text
Sprint 152 — Next.js Workspace Shell and API Client Foundation
```""",
)
replace_exact(
    "README.md",
    """M27 — Persistence and Paper Job Control Foundation          S145-S151 In Progress
M28 — Founder Paper Trading Web Workspace                   S152-S159 Planned""",
    """M27 — Persistence and Paper Job Control Foundation          S145-S151 Complete
M28 — Founder Paper Trading Web Workspace                   S152-S159 In Progress""",
)
replace_exact(
    "README.md",
    """### Milestone 26 — Paper Trading Application Service Foundation

The local API exposes selected existing reads and commands without changing domain or artifact ownership. It remains stateless for product operations: no database, durable job control, Web UI, broker, QMT, live, or capital behavior was introduced.

## Module Overview""",
    """### Milestone 26 — Paper Trading Application Service Foundation

The local API exposes selected existing reads and commands without changing domain or artifact ownership. It remains stateless for product operations: no database, durable job control, Web UI, broker, QMT, live, or capital behavior was introduced.

### Milestone 27 — Persistence and Paper Job Control Foundation

The local product now has explicit SQLite migrations, compact artifact indexes,
durable paper-job requests and attempts, replay-safe submission, selected-job
execution, manual recovery and retry, compact result references, and durable-job
API control. Completed files remain authoritative, lifecycle governance remains
separate from operational job state, and no Web UI, persistent worker, broker,
QMT, live, or capital behavior was introduced.

## Module Overview""",
)
