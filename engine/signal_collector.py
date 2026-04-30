"""Signal payload builders for mode-dependent collection.

Integrates with the search provider registry to dispatch queries
to the configured search provider based on the run mode.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aideator.search.providers import SearchResult

from aideator.llm.registry import get_provider
from aideator.search.providers import SearchResult, SignalType

LOGGER = logging.getLogger("engine.signal_collector")

COMPLAINT_TEMPLATES = {
    "reddit_pain": 'site:reddit.com "{topic}" (sucks | hate | problem | annoying | difficult)',
    "review_mining": '"{topic}" (1 star | 2 stars | "bad review" | "honest review" | complaint)',
    "troubleshooting": '"{topic}" "how do I" "doesn\'t work" "error" "issue"',
    "competitor_pain": '"{topic}" alternatives "switching from" "better than"',
}


def build_hybrid_query(text: str) -> str:
    """Build a privacy-safe hybrid query (truncated to 10 words)."""
    words = [word for word in text.split() if word.strip()]
    return " ".join(words[:10])


def build_external_payload(*, mode: str, title: str, description: str) -> dict[str, str]:
    """Build the search query payload for the given mode."""
    if mode == "hybrid":
        return {"query": build_hybrid_query(f"{title} {description}")}
    if mode == "cloud-enabled":
        return {"query": f"{title} {description}"}
    return {"query": ""}


def build_complaint_queries(title: str, description: str) -> list[str]:
    """Generate a set of targeted complaint mining queries."""
    # Use the title and first 3 words of description as the core topic
    core_words = [word for word in description.split() if word.strip()]
    topic = f"{title} {' '.join(core_words[:3])}"
    
    return [
        template.format(topic=topic)
        for template in COMPLAINT_TEMPLATES.values()
    ]


async def collect_search_signals(
    *,
    mode: str,
    title: str,
    description: str,
    limit: int = 5,
    deep_search: bool = False,
) -> list[SearchResult]:
    """Collect search signals from the configured provider.

    This is the main integration point between the orchestrator
    and the search provider registry.

    Args:
        mode: Run mode. 'local-only' skips search entirely.
        title: Idea title for query construction.
        description: Idea description for query construction.
        limit: Maximum number of search results.

    Returns:
        List of SearchResult objects (empty for local-only mode).

    Raises:
        No exceptions — failures are logged and return empty list.
    """
    if mode == "local-only":
        LOGGER.debug("Skipping search signals for local-only mode")
        return []

    payload = build_external_payload(mode=mode, title=title, description=description)
    query = payload.get("query", "")
    if not query:
        return []

    try:
        from aideator.search.registry import get_search_provider
        from api.config import settings

        provider = get_search_provider(settings)

        LOGGER.info(
            "Collecting search signals",
            extra={
                "event": "search_signals_start",
                "extra_fields": {
                    "provider": provider.name,
                    "mode": mode,
                    "query_len": len(query),
                },
            },
        )

        # Check if provider supports web search
        caps = provider.capabilities()
        if "web_search" not in caps:
            LOGGER.debug("Provider %s does not support web_search, skipping", provider.name)
            return []

        results = await provider.search(query, limit=limit, mode="general")

        # --- COMPLAINT MINING (Deep Search) ---
        if deep_search and mode != "local-only":
            LOGGER.info("Starting deep complaint mining passes")
            mining_queries = build_complaint_queries(title, description)
            
            # Run mining queries in parallel
            tasks = [
                provider.search(q, limit=3, mode="general") 
                for q in mining_queries
            ]
            mining_results_batches = await asyncio.gather(*tasks, return_exceptions=True)
            
            seen_urls = {r.url for r in results}
            for batch in mining_results_batches:
                if isinstance(batch, list):
                    for res in batch:
                        if res.url not in seen_urls:
                            results.append(res)
                            seen_urls.add(res.url)
            
            # Sort results? Maybe keep general results first, then mining results.
            # For now, we just append and let the classifier handle them.
            results = results[:limit * 2] # Allow a bit more for deep search

        # --- CIRCUIT BREAKER / FAILOVER LOGIC ---
        if not results and provider.name != "duckduckgo" and provider.name != "builtin":
            LOGGER.info(
                "Primary search provider returned no results, attempting failover",
                extra={
                    "event": "search_failover",
                    "extra_fields": {
                        "from_provider": provider.name,
                        "to_provider": "duckduckgo",
                    },
                },
            )
            try:
                # Fallback to duckduckgo
                fallback_settings = {"search_provider": "duckduckgo"}
                fallback_provider = get_search_provider(fallback_settings)
                results = await fallback_provider.search(query, limit=limit, mode="general")

                LOGGER.info(
                    "Search failover successful",
                    extra={
                        "event": "search_signals_done",
                        "extra_fields": {
                            "provider": "duckduckgo",
                            "results_count": len(results),
                            "is_fallback": True,
                        },
                    },
                )
            except Exception as e:
                LOGGER.warning(f"Search failover to DuckDuckGo failed: {e}")
        else:
            LOGGER.info(
                "Search signals collected",
                extra={
                    "event": "search_signals_done",
                    "extra_fields": {
                        "provider": provider.name,
                        "results_count": len(results),
                    },
                },
            )

        return results

    except Exception:
        LOGGER.warning(
            "Search signal collection failed",
            extra={"event": "search_signals_error"},
            exc_info=True,
        )
        return []


def collect_search_signals_sync(
    *,
    mode: str,
    title: str,
    description: str,
    limit: int = 5,
    deep_search: bool = False,
) -> list[SearchResult]:
    """Synchronous wrapper for collect_search_signals.

    Used by the orchestrator which currently runs synchronously.
    Creates or reuses an event loop for the async search call.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Already in an async context — can't use asyncio.run
        # Fall back to empty results to avoid deadlock
        LOGGER.debug("Already in async context, skipping sync search wrapper")
        return []

    return asyncio.run(
        collect_search_signals(
            mode=mode,
            title=title,
            description=description,
            limit=limit,
            deep_search=deep_search,
        )
    )


async def classify_signals(signals: list[SearchResult]) -> list[SearchResult]:
    """Classify a batch of signals using an LLM.

    Args:
        signals: List of raw search results.

    Returns:
        List of classified SearchResult objects.
    """
    if not signals:
        return []

    try:
        from api.config import settings
        provider = get_provider(settings)

        # Prepare batch prompt
        signals_payload = [
            {"id": i, "title": s.title, "snippet": s.snippet}
            for i, s in enumerate(signals)
        ]

        prompt = f"""You are a Signal Classification Engine.
Your task is to categorize the following evidence signals for a business validation run.

CATEGORIES:
- PAIN_COMPLAINT: Direct evidence of a problem, frustration, or "this sucks" rant.
- FEATURE_REQUEST: "I wish X existed" or "How do I do Y?" questions.
- COMPETITOR_WEAKNESS: Negative reviews or complaints about existing solutions.
- MARKET_DATA: Quantitative facts, growth stats, or industry reports.
- ANECDOTAL_POSITIVE: Generic positive mentions or vague support.
- SEO_FILLER: Sponsored content, affiliate links, or generic blog fluff.

SIGNALS:
{json.dumps(signals_payload, indent=2)}

Return a JSON object with a 'classifications' list.
Each item MUST have 'id', 'type' (one of the CATEGORIES above), and 'confidence' (0.0 to 1.0).

Example:
{{
  "classifications": [
    {{ "id": 0, "type": "PAIN_COMPLAINT", "confidence": 0.95 }}
  ]
}}
"""
        messages = [{"role": "user", "content": prompt}]
        response = await provider.generate(messages, temperature=0.1)
        
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        data = json.loads(content)
        classifications = {c["id"]: c for c in data.get("classifications", [])}

        results = []
        for i, s in enumerate(signals):
            c = classifications.get(i, {})
            # Map string type back to Enum
            raw_type = c.get("type", "UNSPECIFIED").upper()
            try:
                sig_type = SignalType[raw_type]
            except KeyError:
                sig_type = SignalType.ANECDOTAL_POSITIVE

            results.append(SearchResult(
                title=s.title,
                url=s.url,
                snippet=s.snippet,
                source=s.source,
                score=s.score,
                signal_type=sig_type,
                confidence=c.get("confidence", 0.5)
            ))
        
        return results

    except Exception as e:
        LOGGER.warning(f"Signal classification failed, falling back to defaults: {e}")
        return [
            SearchResult(
                title=s.title,
                url=s.url,
                snippet=s.snippet,
                source=s.source,
                score=s.score,
                signal_type=SignalType.ANECDOTAL_POSITIVE,
                confidence=0.5
            ) for s in signals
        ]
