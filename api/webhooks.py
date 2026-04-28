"""Webhook system for post-validation actions."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl

from api.auth import get_current_user
from db.base import db_session
from db.schema import WebhookModel

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])
LOGGER = logging.getLogger("api.webhooks")


class WebhookCreate(BaseModel):
    url: HttpUrl
    events: str = "run.succeeded"
    workspace_id: str | None = None


class WebhookResponse(BaseModel):
    webhook_id: str
    url: str
    events: str
    is_active: bool


@router.post("/", response_model=WebhookResponse, status_code=201)
def create_webhook(payload: WebhookCreate, current_user: Any = Depends(get_current_user)):
    session = db_session()
    try:
        webhook = WebhookModel(
            owner_id=str(current_user.user_id),
            workspace_id=payload.workspace_id,
            url=str(payload.url),
            events=payload.events,
            is_active=1,
        )
        session.add(webhook)
        session.commit()
        session.refresh(webhook)
        return {
            "webhook_id": webhook.webhook_id,
            "url": webhook.url,
            "events": webhook.events,
            "is_active": bool(webhook.is_active),
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_session.remove()


@router.get("/", response_model=list[WebhookResponse])
def list_webhooks(current_user: Any = Depends(get_current_user)):
    session = db_session()
    try:
        webhooks = session.query(WebhookModel).filter_by(owner_id=str(current_user.user_id)).all()
        return [
            {
                "webhook_id": w.webhook_id,
                "url": w.url,
                "events": w.events,
                "is_active": bool(w.is_active),
            }
            for w in webhooks
        ]
    finally:
        db_session.remove()


@router.delete("/{webhook_id}")
def delete_webhook(webhook_id: str, current_user: Any = Depends(get_current_user)):
    session = db_session()
    try:
        webhook = (
            session.query(WebhookModel)
            .filter_by(webhook_id=webhook_id, owner_id=str(current_user.user_id))
            .first()
        )
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        session.delete(webhook)
        session.commit()
        return {"status": "deleted"}
    finally:
        db_session.remove()
