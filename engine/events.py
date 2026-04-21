"""Event bus for run-time progress updates (SSE support)."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

LOGGER = logging.getLogger("engine.events")

class EventBus:
    def __init__(self) -> None:
        # Map run_id -> List of queues (one per subscriber)
        self._subscribers: dict[UUID, list[asyncio.Queue]] = {}

    async def publish(
        self, run_id: UUID, event_type: str, data: dict[str, Any] | None = None
    ) -> None:
        """Broadcast an event to all subscribers for a specific run."""
        if run_id not in self._subscribers:
            return

        payload = {
            "type": event_type,
            "run_id": str(run_id),
            "data": data or {},
        }
        
        # Broadcast to all active queues for this run
        for queue in self._subscribers[run_id]:
            await queue.put(payload)
            
        LOGGER.debug(f"Published event {event_type} for run {run_id}")

    async def subscribe(self, run_id: UUID) -> AsyncIterator[dict[str, Any]]:
        """Subscribe to events for a specific run."""
        queue = asyncio.Queue()
        if run_id not in self._subscribers:
            self._subscribers[run_id] = []
        
        self._subscribers[run_id].append(queue)
        
        try:
            while True:
                yield await queue.get()
        finally:
            # Cleanup on disconnect
            if run_id in self._subscribers:
                self._subscribers[run_id].remove(queue)
                if not self._subscribers[run_id]:
                    del self._subscribers[run_id]

# Global instance for app-wide use
bus = EventBus()

async def publish_event(run_id: UUID, event_type: str, data: dict[str, Any] | None = None) -> None:
    await bus.publish(run_id, event_type, data)

async def subscribe_run(run_id: UUID) -> AsyncIterator[dict[str, Any]]:
    async for event in bus.subscribe(run_id):
        yield event
