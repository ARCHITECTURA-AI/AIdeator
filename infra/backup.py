"""PH-C backup and restore helpers for deterministic snapshots."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

MANIFEST_VERSION = 1


def build_backup_manifest(*, ideas: int, runs: int, signals: int, reports: int) -> dict[str, Any]:
    return {
        "version": MANIFEST_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "ideas": ideas,
            "runs": runs,
            "signals": signals,
            "reports": reports,
        },
    }


def validate_backup_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("version") != MANIFEST_VERSION:
        raise ValueError("Unsupported backup manifest version")
    counts = manifest.get("counts")
    if not isinstance(counts, dict):
        raise ValueError("Backup manifest counts payload is missing")
    for key in ("ideas", "runs", "signals", "reports"):
        value = counts.get(key)
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"Invalid backup count for '{key}'")


def canonicalize_backup_payload(payload: dict[str, Any]) -> str:
    """Produce deterministic payload bytes for parity checks."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
