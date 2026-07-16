"""Export the canonical FastAPI OpenAPI contract for the local Web workspace."""

from __future__ import annotations

import argparse
import importlib
import json
import os
from collections.abc import Sequence
from pathlib import Path
from unittest.mock import patch

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OPENAPI_SNAPSHOT_PATH = REPOSITORY_ROOT / "web" / "src" / "generated" / "openapi.json"
SERVER_LOCAL_ENVIRONMENT_NAMES = (
    "EL_PSY_QUANT_RESEARCH_ARTIFACT_ROOT",
    "EL_PSY_QUANT_EVIDENCE_ARTIFACT_ROOT",
    "EL_PSY_QUANT_PRODUCT_DATABASE_PATH",
    "EL_PSY_QUANT_PAPER_ARTIFACT_ROOT",
    "EL_PSY_QUANT_WORKSPACE_MODE",
    "EL_PSY_QUANT_DEMO_WORKSPACE_ROOT",
)


def build_canonical_openapi() -> str:
    """Build stable OpenAPI JSON without consulting local product resources."""
    neutral_environment = {name: "" for name in SERVER_LOCAL_ENVIRONMENT_NAMES}
    with patch.dict(os.environ, neutral_environment):
        app_module = importlib.import_module("el_psy_quant.api.app")
        application = app_module.create_app(
            research_artifact_root="",
            evidence_artifact_root="",
            product_database_path="",
            paper_artifact_root="",
            workspace_mode="standard",
            demo_workspace_root="",
        )
        document = application.openapi()
    return json.dumps(
        document,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def write_or_check_snapshot(*, check: bool) -> bool:
    """Write the snapshot, or report whether the checked-in copy is current."""
    canonical = build_canonical_openapi()
    if check:
        try:
            current = OPENAPI_SNAPSHOT_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            print(
                f"error: missing generated OpenAPI snapshot: {OPENAPI_SNAPSHOT_PATH}"
            )
            return False
        if current != canonical:
            print(
                "error: generated OpenAPI snapshot is stale; "
                "run `npm --prefix web run contracts:generate`"
            )
            return False
        return True

    OPENAPI_SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OPENAPI_SNAPSHOT_PATH.write_text(canonical, encoding="utf-8", newline="\n")
    return True


def main(argv: Sequence[str] | None = None) -> int:
    """Run the deterministic export or freshness check."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing when the checked-in snapshot is stale",
    )
    arguments = parser.parse_args(argv)
    return 0 if write_or_check_snapshot(check=arguments.check) else 1


if __name__ == "__main__":
    raise SystemExit(main())
