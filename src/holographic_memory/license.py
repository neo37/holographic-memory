"""License gate.

`MEMORY_MODE=LOCAL` (default) is free and open — the gate is a no-op. Any other
mode (CLOUD / PRO) requires a valid `MEMORY_LICENSE_KEY`, validated against
Lemon Squeezy and cached locally for 24h to avoid per-request latency.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

_VALIDATE_URL = "https://api.lemonsqueezy.com/v1/licenses/validate"
_CACHE_TTL = 24 * 60 * 60


def _cache_path() -> Path:
    base = Path(os.getenv("MEMORY_STORE_PATH", "~/.holographic-memory")).expanduser()
    base.mkdir(parents=True, exist_ok=True)
    return base / "license.cache.json"


def _cached_ok(key: str) -> bool:
    p = _cache_path()
    if not p.exists():
        return False
    try:
        c = json.loads(p.read_text("utf-8"))
    except Exception:
        return False
    return c.get("key") == key and c.get("valid") and (time.time() - c.get("ts", 0)) < _CACHE_TTL


def _remote_ok(key: str) -> bool:
    body = json.dumps({"license_key": key}).encode()
    req = urllib.request.Request(
        _VALIDATE_URL, data=body, headers={"Accept": "application/json", "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
        valid = bool(data.get("valid"))
    except Exception:
        return False
    if valid:
        _cache_path().write_text(json.dumps({"key": key, "valid": True, "ts": time.time()}), "utf-8")
    return valid


def ensure_licensed() -> None:
    mode = os.getenv("MEMORY_MODE", "LOCAL").upper()
    if mode == "LOCAL":
        return
    key = os.getenv("MEMORY_LICENSE_KEY", "").strip()
    if key and (_cached_ok(key) or _remote_ok(key)):
        return
    print(
        "Error: invalid or missing MEMORY_LICENSE_KEY for mode "
        f"'{mode}'. Get a key at https://holo.ai3d.art (or set MEMORY_MODE=LOCAL for free local use).",
        file=sys.stderr,
    )
    sys.exit(1)
