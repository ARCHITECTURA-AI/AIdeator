from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import get_current_user
from db.templates import (
    create_template,
    get_template_details,
    list_public_templates,
    upvote_template,
)

router = APIRouter(prefix="/api/templates", tags=["templates"])


class TemplateCreate(BaseModel):
    title: str
    description: str
    category: str
    prefilled_data: dict[str, Any]


@router.post("", status_code=201)
def post_template(payload: TemplateCreate, current_user: Any = Depends(get_current_user)):
    t_id = create_template(
        payload.title,
        payload.description,
        payload.category,
        payload.prefilled_data,
        current_user.user_id,
    )
    return {"template_id": t_id}


@router.get("")
def get_templates():
    return list_public_templates()


@router.get("/{template_id}")
def get_template(template_id: str):
    t = get_template_details(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return t


@router.post("/{template_id}/upvote")
def post_upvote(template_id: str, current_user: Any = Depends(get_current_user)):
    upvotes = upvote_template(template_id, current_user.user_id)
    return {"upvotes": upvotes}
