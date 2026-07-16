"""Authenticated health probe used by the local Docker Compose backend."""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request

EXPECTED_HEALTH = {
    "status": "ok",
    "service": "el-psy-quant",
    "api_version": "v1",
}


def main() -> int:
    """Return success only for the exact authenticated API health contract."""
    username = os.getenv("EL_PSY_QUANT_FOUNDER_USERNAME")
    password = os.getenv("EL_PSY_QUANT_FOUNDER_PASSWORD")
    if not username or not password:
        return 1
    encoded = base64.b64encode(f"{username}:{password}".encode("ascii")).decode(
        "ascii"
    )
    request = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/health",
        headers={"Authorization": f"Basic {encoded}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            payload = json.load(response)
            return 0 if response.status == 200 and payload == EXPECTED_HEALTH else 1
    except (OSError, UnicodeError, ValueError, urllib.error.URLError):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
