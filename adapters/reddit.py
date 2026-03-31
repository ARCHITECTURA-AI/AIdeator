"""Reddit adapter contract helpers."""

from __future__ import annotations

from typing import Any


def parse_reddit_response(payload: dict[str, Any]) -> list[dict[str, str]]:
    children = payload.get("data", {}).get("children", [])
    parsed: list[dict[str, str]] = []
    for item in children:
        data = item.get("data", {})
        parsed.append(
            {
                "title": str(data.get("title", "")),
                "url": str(data.get("url", "")),
                "snippet": str(data.get("selftext", "")),
            }
        )
    return parsed
