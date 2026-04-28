import logging
from typing import Any

import httpx

from db.base import db_session
from db.schema import WebhookModel

LOGGER = logging.getLogger("services.webhooks")


async def dispatch_webhooks(
    event_type: str, payload: dict[str, Any], workspace_id: str | None = None
):
    """Dispatch event to all registered webhooks."""
    session = db_session()
    try:
        query = session.query(WebhookModel).filter_by(is_active=1)
        if workspace_id:
            query = query.filter_by(workspace_id=workspace_id)

        webhooks = query.all()

        async with httpx.AsyncClient() as client:
            for webhook in webhooks:
                if event_type in webhook.events:
                    try:
                        LOGGER.info(f"Dispatching {event_type} to {webhook.url}")
                        await client.post(
                            webhook.url, json={"event": event_type, "payload": payload}, timeout=5.0
                        )
                    except Exception as e:
                        LOGGER.error(f"Webhook dispatch failed for {webhook.url}: {e}")
    finally:
        db_session.remove()
