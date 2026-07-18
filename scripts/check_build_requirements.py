"""Verify the committed exact build export against ``uv.lock``."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILD_REQUIREMENTS_PATH = PROJECT_ROOT / "requirements-build.txt"
EXPORT_COMMAND = (
    "uv",
    "export",
    "--locked",
    "--only-group",
    "build",
    "--no-emit-project",
    "--no-hashes",
    "--no-annotate",
    "--no-header",
)


def main() -> int:
    """Return non-zero when the committed build export is stale."""
    try:
        completed = subprocess.run(
            EXPORT_COMMAND,
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        committed = BUILD_REQUIREMENTS_PATH.read_text(encoding="utf-8")
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"build requirements check failed: {error}", file=sys.stderr)
        return 1
    if committed != completed.stdout:
        print(
            "requirements-build.txt is stale; regenerate it with:\n"
            f"  {' '.join(EXPORT_COMMAND)} --output-file requirements-build.txt",
            file=sys.stderr,
        )
        return 1
    print("requirements-build.txt matches uv.lock")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
