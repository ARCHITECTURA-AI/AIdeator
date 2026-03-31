"""Ideas API endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from db.ideas import save_idea
from models.idea import Idea

router = APIRouter(tags=["ideas"])


class CreateIdeaRequest(BaseModel):
    title: str
    description: str
    target_user: str
    context: str


class CreateIdeaResponse(BaseModel):
    idea_id: str


def create_idea(payload: CreateIdeaRequest) -> CreateIdeaResponse:
    idea = Idea(
        title=payload.title,
        description=payload.description,
        target_user=payload.target_user,
        context=payload.context,
    )
    save_idea(idea)
    return CreateIdeaResponse(idea_id=str(idea.idea_id))


@router.post("/ideas", status_code=201, response_model=CreateIdeaResponse)
def post_ideas(payload: CreateIdeaRequest) -> CreateIdeaResponse:
    return create_idea(payload)
