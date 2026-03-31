"""Signal payload builders for mode-dependent collection."""

from __future__ import annotations


def build_hybrid_query(text: str) -> str:
    words = [word for word in text.split() if word.strip()]
    return " ".join(words[:10])


def build_external_payload(*, mode: str, title: str, description: str) -> dict[str, str]:
    if mode == "hybrid":
        return {"query": build_hybrid_query(f"{title} {description}")}
    if mode == "cloud-enabled":
        return {"query": f"{title} {description}"}
    return {"query": ""}
