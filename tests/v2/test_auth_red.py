from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_user_registration_and_login():
    """TC-I-400: User can register and obtain a token."""
    # 1. Register
    reg_response = client.post(
        "/api/auth/register", json={"email": "test@example.com", "password": "securepassword123"}
    )
    assert reg_response.status_code == 201

    # 2. Login
    login_response = client.post(
        "/api/auth/login", data={"username": "test@example.com", "password": "securepassword123"}
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials():
    """TC-I-400: Invalid credentials rejected."""
    # Register first
    client.post(
        "/api/auth/register", json={"email": "test@example.com", "password": "securepassword123"}
    )

    # Login with wrong password
    login_response = client.post(
        "/api/auth/login", data={"username": "test@example.com", "password": "wrongpassword"}
    )
    assert login_response.status_code == 401


def test_authenticated_route_access():
    """TC-I-400: Protected routes require valid token."""
    # Try to list ideas without token
    response = client.get("/ideas")
    assert response.status_code == 401

    # Register and login
    client.post("/api/auth/register", json={"email": "u1@ex.com", "password": "p1"})
    login = client.post("/api/auth/login", data={"username": "u1@ex.com", "password": "p1"})
    token = login.json()["access_token"]

    # Try with token
    response = client.get("/ideas", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
