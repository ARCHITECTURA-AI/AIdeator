from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import get_current_user
from db.workspaces import add_member, create_workspace, get_user_workspaces

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


class WorkspaceCreate(BaseModel):
    name: str


class MemberInvite(BaseModel):
    email: str
    role: str = "viewer"


@router.post("", status_code=201)
def post_create_workspace(payload: WorkspaceCreate, current_user: Any = Depends(get_current_user)):
    ws_id = create_workspace(payload.name, current_user.user_id)
    return {"workspace_id": ws_id}


@router.get("")
def list_workspaces(current_user: Any = Depends(get_current_user)):
    return get_user_workspaces(current_user.user_id)


@router.post("/{workspace_id}/members", status_code=201)
def invite_member(
    workspace_id: str, payload: MemberInvite, current_user: Any = Depends(get_current_user)
):
    # Simple check: only admins can invite (for now, just check if member)
    from db.workspaces import is_member

    role = is_member(workspace_id, str(current_user.user_id))
    if not role or role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can invite members")

    success = add_member(workspace_id, payload.email, payload.role)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "member added"}
