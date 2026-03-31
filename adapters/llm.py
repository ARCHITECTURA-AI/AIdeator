"""LiteLLM response helpers constrained to stable fields."""

from __future__ import annotations

from typing import Any


def extract_text(response: dict[str, Any]) -> str:
    return str(response["choices"][0]["message"]["content"])
