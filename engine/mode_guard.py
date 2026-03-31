"""Mode guard and privacy-boundary decisions."""

from __future__ import annotations

from urllib.parse import urlparse

INTERNAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
EXTERNAL_BLOCK_REASON = "local_only_external_block"


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def block_external(url: str) -> bool:
    return _host(url) not in INTERNAL_HOSTS


def enforce_hybrid_keywords(payload: str) -> bool:
    words = [word for word in payload.split() if word.strip()]
    return 0 < len(words) <= 10


def check(mode: str, *, target_url: str, payload: str | None = None) -> bool:
    if mode == "local-only":
        return not block_external(target_url)
    if mode == "hybrid":
        if payload is None:
            return False
        return enforce_hybrid_keywords(payload)
    return True


class ModeGuard:
    def check(self, mode: str, *, target_url: str, payload: str | None = None) -> bool:
        return check(mode, target_url=target_url, payload=payload)
