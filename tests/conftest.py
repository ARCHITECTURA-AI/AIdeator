"""Test configuration — adds project root to sys.path.

This is needed because the project uses top-level packages
(engine, api, db, etc.) that aren't installed as packages
but are importable from the project root.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

from aideator.llm.registry import PROVIDER_REGISTRY
from tests.v2.mocks import MockLLMProvider

# Ensure project root is on sys.path for module imports
_ROOT = str(Path(__file__).resolve().parents[1])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

os.environ["IDEATOR_TEST_BYPASS"] = "true"
os.environ["APP_DB_URL"] = "sqlite:///./test_aideator_global.db"

import pytest  # noqa: E402

from db.base import reset_db_connection  # noqa: E402


@pytest.fixture(autouse=True)
def db_init(monkeypatch):
    """Ensure database is initialized for every test with a unique file in temp dir."""
    import tempfile
    import uuid
    
    # Use system temp dir to avoid OneDrive locks and slowness
    temp_dir = tempfile.gettempdir()
    test_db_file = os.path.join(temp_dir, f"test_aideator_{uuid.uuid4().hex}.db")
    test_db_url = f"sqlite:///{test_db_file}"
    
    # Use monkeypatch to isolate the environment change to this test
    monkeypatch.setenv("APP_DB_URL", test_db_url)
    
    reset_db_connection()
    
    yield
    
    # Cleanup: Close connections and remove the test file
    from db.base import db_session, engine
    db_session.remove()
    engine.dispose()
    
    if os.path.exists(test_db_file):
        try:
            os.remove(test_db_file)
        except Exception:
            pass

@pytest.fixture(autouse=True)
def mock_llm_provider_setup():
    """Register MockLLMProvider in the registry and force its use globally."""
    # Register the provider if not already there
    if "mock" not in PROVIDER_REGISTRY:
        PROVIDER_REGISTRY["mock"] = MockLLMProvider
    
    # Force settings to use mock provider
    from api.config import settings
    old_provider = settings.llm_provider
    object.__setattr__(settings, 'llm_provider', "mock")
    
    # Mock the default response for the global provider instance
    god_response = json.dumps({
        "classifications": [{"id": 0, "type": "PAIN_COMPLAINT", "confidence": 0.9}],
        "demand": {
            "strengths": ["Strong demand"],
            "weaknesses": [],
            "synthesis_preamble": "Test"
        },
        "competition": {
            "strengths": [],
            "weaknesses": ["No competition"],
            "synthesis_preamble": "Test"
        },
        "viability": {
            "strengths": ["Technically feasible"],
            "weaknesses": [],
            "synthesis_preamble": "Test"
        },
        "market_sizing": {"tam": "1B", "sam": "100M", "som": "10M"},
        "cards": [
            {
                "type": "demand", "score": 80, "summary": "S",
                "detailed_context": "D", "citation_urls": []
            },
            {
                "type": "competition", "score": 70, "summary": "S",
                "detailed_context": "D", "citation_urls": []
            },
            {
                "type": "market", "score": 90, "summary": "S",
                "detailed_context": "D", "citation_urls": []
            },
            {
                "type": "viability", "score": 85, "summary": "S",
                "detailed_context": "D", "citation_urls": []
            },
            {
                "type": "next_steps", "score": 60, "summary": "S",
                "detailed_context": "D", "citation_urls": []
            }
        ],
        "script": [
            {"question": "What is your biggest pain?", "rationale": "Identify core problem"}
        ],
        "outreach_templates": {"email": "Hi, I'm building..."},
        "response_tracker": ["Name", "Pain Point", "Interest Level"],
        "hypothesis": "Users will pay $10/mo for this.",
        "landing_page_copy": {
            "headline": "Stop wasting time",
            "subheadline": "The best tool for...",
            "pain_points": "It's too slow.",
            "solution": "We are fast.",
            "cta": "Sign up"
        },
        "success_metric": "10% conversion rate",
        "tool_stack": ["Webflow", "Stripe"]
    })
    
    # Patch MockLLMProvider.generate directly
    with patch.object(MockLLMProvider, "generate", wraps=MockLLMProvider.generate) as mock_gen:
        from aideator.llm.providers import LLMResponse
        async def side_effect(*args, **kwargs):
            return LLMResponse(
                content=god_response,
                model="mock",
                provider="mock",
                latency_ms=10.0
            )
        mock_gen.side_effect = side_effect
        yield
    
    # Restore settings
    object.__setattr__(settings, 'llm_provider', old_provider)
