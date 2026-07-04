"""Run the same local quality checks as GitHub Actions CI."""

from __future__ import annotations

import shlex
import subprocess
import sys

CHECKS = (
    ("uv", "run", "pytest"),
    ("uv", "run", "ruff", "check", "."),
    ("uv", "run", "python", "-c", "import el_psy_quant"),
    ("uv", "run", "el-psy-quant", "--help"),
)


def main() -> int:
    """Run each quality check in order and stop at the first failure."""
    try:
        for command in CHECKS:
            print(f"$ {shlex.join(command)}", flush=True)
            subprocess.run(command, check=True)
    except subprocess.CalledProcessError as error:
        return error.returncode if error.returncode > 0 else 1
    except FileNotFoundError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
