import pytest

from engine.synthesizer import REQUIRED_CARD_TYPES


@pytest.mark.asyncio
async def test_market_sizing_card_exists():
    """
    Test that the synthesizer now produces a 'market' card with TAM/SAM/SOM logic.
    """
    # We'll mock the LLM provider to return 5 cards including 'market'
    # For now, we just check if 'market' is in REQUIRED_CARD_TYPES
    assert "market" in REQUIRED_CARD_TYPES


def test_default_cards_contain_market():
    from engine.synthesizer import synthesize_default_cards

    cards = synthesize_default_cards()
    card_types = [c.type for c in cards]
    assert "market" in card_types
