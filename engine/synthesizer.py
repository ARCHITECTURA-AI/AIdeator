"""Cards synthesizer and validator."""

from __future__ import annotations


REQUIRED_CARD_TYPES = {"demand", "competition", "risk", "next_steps"}
REQUIRES_CITATIONS = {"demand", "competition", "risk"}


def validate_cards(cards: list[dict[str, object]]) -> None:
    present = {str(card.get("type")) for card in cards}
    missing = REQUIRED_CARD_TYPES - present
    if missing:
        raise ValueError(f"Missing card types: {sorted(missing)}")

    for card in cards:
        card_type = str(card.get("type"))
        citations = card.get("citation_urls", [])
        if card_type in REQUIRES_CITATIONS and (not isinstance(citations, list) or len(citations) == 0):
            raise ValueError(f"Missing citations for card type: {card_type}")


def synthesize_default_cards() -> list[dict[str, object]]:
    cards: list[dict[str, object]] = [
        {
            "type": "demand",
            "score": 0.62,
            "summary": "Early demand is plausible but needs focused validation.",
            "citation_urls": ["https://example.com/demand"],
        },
        {
            "type": "competition",
            "score": 0.54,
            "summary": "Market has competitors with room for differentiated execution.",
            "citation_urls": ["https://example.com/competition"],
        },
        {
            "type": "risk",
            "score": 0.48,
            "summary": "Execution risk is moderate due to acquisition and retention uncertainty.",
            "citation_urls": ["https://example.com/risk"],
        },
        {
            "type": "next_steps",
            "score": 0.66,
            "summary": "Run user interviews and ship a constrained pilot in two weeks.",
            "citation_urls": [],
        },
    ]
    validate_cards(cards)
    return cards
