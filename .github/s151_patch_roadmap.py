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
    "docs/roadmap.md",
    """| M27 — Persistence and Paper Job Control Foundation | S145-151 | In Progress | Add product persistence and controllable local jobs. | Product metadata and paper jobs are durable, inspectable, idempotent, recoverable, and manually controlled. |
| M28 — Founder Paper Trading Web Workspace | S152-159 | Planned | Deliver the first usable Founder Web MVP. | The Founder can inspect strategies and operate paper workflows locally through the Web/API boundary. |""",
    """| M27 — Persistence and Paper Job Control Foundation | S145-151 | Complete | Add product persistence and controllable local jobs. | Product metadata and paper jobs are durable, inspectable, idempotent, recoverable, and manually controlled. |
| M28 — Founder Paper Trading Web Workspace | S152-159 | In Progress | Deliver the first usable Founder Web MVP. | The Founder can inspect strategies and operate paper workflows locally through the Web/API boundary. |""",
)
replace_exact("docs/roadmap.md", "| S151 | Milestone 27 Closeout. **Next.** |", "| S151 | Milestone 27 Closeout. **Complete.** |")
replace_exact("docs/roadmap.md", "| S152 | Next.js Workspace Shell and API Client Foundation |", "| S152 | Next.js Workspace Shell and API Client Foundation. **Next.** |")
replace_exact("docs/roadmap.md", "## Milestone 27 Progress", "## Completed Milestone 27 — Persistence and Paper Job Control Foundation")
replace_exact(
    "docs/roadmap.md",
    """Submission does not execute automatically. Compact result references do not
copy result payloads into SQLite, and the existing synchronous
`POST /api/v1/paper-runs` remains unchanged and database-free. Sprint 150 adds
no Web UI, authentication, broker, QMT, live, or capital behavior.

## Current Next Step

```text
Sprint 151 — Milestone 27 Closeout
```

Sprint 151 is the documentation and verification closeout for Milestone 27.
This Sprint 150 implementation does not begin that work.""",
    """Submission does not execute automatically. Compact result references do not
copy result payloads into SQLite, and the existing synchronous
`POST /api/v1/paper-runs` remains unchanged and database-free. Sprint 150 adds
no Web UI, authentication, broker, QMT, live, or capital behavior.

Sprint 151 verified the complete M27 migration, transaction, recovery,
idempotency, result-reference, artifact-authority, and browser-boundary contracts
and closed the milestone without changing runtime code, schemas, dependencies,
or test behavior.

See:

```text
docs/milestones/milestone-027-persistence-and-paper-job-control-foundation.md
docs/sprints/sprint-151-milestone-27-closeout.md
```

## Current Next Step

```text
Sprint 152 — Next.js Workspace Shell and API Client Foundation
```

Sprint 152 begins Milestone 28 with only the smallest local workspace shell,
navigation, configuration, and typed API-client foundation. It must consume the
versioned API and must not duplicate backend domain behavior or access SQLite or
artifact directories directly.""",
)
