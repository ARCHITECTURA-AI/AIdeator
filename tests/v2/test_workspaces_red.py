from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_workspace_sharing_red():
    # 1. Register User A and User B
    client.post(
        "/api/auth/register",
        json={"email": "usera@ex.com", "password": "password", "full_name": "User A"},
    )
    client.post(
        "/api/auth/register",
        json={"email": "userb@ex.com", "password": "password", "full_name": "User B"},
    )

    # Login User A
    login_a = client.post(
        "/api/auth/login", data={"username": "usera@ex.com", "password": "password"}
    )
    token_a = login_a.json()["access_token"]

    # 2. User A creates a Workspace
    ws_res = client.post(
        "/api/workspaces",
        json={"name": "Team Alpha"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["workspace_id"]

    # 3. User A creates an Idea in that Workspace
    idea_res = client.post(
        "/ideas",
        json={
            "title": "Shared Idea",
            "description": "Shared",
            "target_user": "everyone",
            "context": "shared",
            "workspace_id": ws_id,
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert idea_res.status_code == 201

    # 4. User B (not in WS) should NOT see the idea
    login_b = client.post(
        "/api/auth/login", data={"username": "userb@ex.com", "password": "password"}
    )
    token_b = login_b.json()["access_token"]

    ideas_b = client.get("/ideas", headers={"Authorization": f"Bearer {token_b}"})
    assert "Shared Idea" not in str(ideas_b.json())

    # 5. User A invites User B to Workspace
    invite_res = client.post(
        f"/api/workspaces/{ws_id}/members",
        json={"email": "userb@ex.com", "role": "editor"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert invite_res.status_code == 201

    # 6. User B should NOW see the idea
    ideas_b_now = client.get("/ideas", headers={"Authorization": f"Bearer {token_b}"})
    assert "Shared Idea" in str(ideas_b_now.json())
