import time

import pytest
from fastapi.testclient import TestClient

from api.app import app


def test_end_to_end_flow():
    with TestClient(app) as client:
        # 1. Register and Login
        email = f"user_{int(time.time())}@example.com"
        client.post(
            "/api/auth/register",
            json={"email": email, "password": "password", "full_name": "E2E Tester"},
        )
        login = client.post("/api/auth/login", data={"username": email, "password": "password"})
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create an Idea
        idea_data = {
            "title": "AI Coffee Roaster",
            "description": "An AI-powered coffee roasting machine that optimizes flavor profiles.",
            "target_user": "Coffee enthusiasts",
            "context": "Home roasting",
        }
        res = client.post("/ideas", json=idea_data, headers=headers)
        assert res.status_code == 201
        idea_id = res.json()["idea_id"]

        # 3. Start a Run
        run_payload = {"idea_id": idea_id, "tier": "low", "mode": "local-only"}
        run_res = client.post("/runs", json=run_payload, headers=headers)
        assert run_res.status_code == 202
        run_id = run_res.json()["run_id"]

        # 4. Wait for completion
        max_retries = 30
        finished = False
        for i in range(max_retries):
            status_res = client.get(f"/runs/{run_id}/status", headers=headers)
            assert status_res.status_code == 200
            status = status_res.json()["status"]
            if status == "succeeded":
                finished = True
                break
            elif status == "failed":
                pytest.fail("Run failed")
            time.sleep(1)

        assert finished, "Run did not complete in time"

        # 5. Get Report
        report_res = client.get(f"/runs/{run_id}/report", headers=headers)
        assert report_res.status_code == 200
        report = report_res.json()
        assert "cards" in report
        assert len(report["cards"]) > 0
        print(f"End-to-end success! Report generated with {len(report['cards'])} cards.")


if __name__ == "__main__":
    test_end_to_end_flow()
