from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_template_marketplace_flow_red():
    # 1. Register and Login
    client.post(
        "/api/auth/register",
        json={"email": "tester@ex.com", "password": "password", "full_name": "Tester"},
    )
    login = client.post(
        "/api/auth/login", data={"username": "tester@ex.com", "password": "password"}
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Submit a Template
    template_data = {
        "title": "SaaS Starter",
        "description": "Perfect for new SaaS ideas",
        "category": "SaaS",
        "prefilled_data": {"target_user": "Small Business", "context": "Subscription management"},
    }
    res = client.post("/api/templates", json=template_data, headers=headers)
    assert res.status_code == 201
    template_id = res.json()["template_id"]

    # 3. List Templates (Public)
    res = client.get("/api/templates")
    assert res.status_code == 200
    templates = res.json()
    assert any(t["title"] == "SaaS Starter" for t in templates)

    # 4. Upvote Template
    res = client.post(f"/api/templates/{template_id}/upvote", headers=headers)
    assert res.status_code == 200
    assert res.json()["upvotes"] == 1

    # 5. Get Template Details
    res = client.get(f"/api/templates/{template_id}")
    assert res.status_code == 200
    assert res.json()["title"] == "SaaS Starter"
    assert res.json()["upvotes"] == 1
