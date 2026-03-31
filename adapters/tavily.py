"""Tavily adapter contract helpers."""

from __future__ import annotations

from typing import Any


def parse_tavily_response(payload: dict[str, Any]) -> list[dict[str, str]]:
    rows = payload.get("results", [])
    parsed: list[dict[str, str]] = []
    for row in rows:
        parsed.append(
            {
                "title": str(row.get("title", "")),
                "url": str(row.get("url", "")),
                "snippet": str(row.get("content", "")),
            }
        )
    return parsed
