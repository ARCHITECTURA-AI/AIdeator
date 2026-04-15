"""Smoke tests for end-to-end application health."""

from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


class TestAppHealth:
    """Smoke tests for the running application."""

    def test_healthz_returns_200(self) -> None:
        response = client.get("/healthz")
        assert response.status_code == 200

    def test_root_redirects_to_dashboard(self) -> None:
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert "/app/dashboard" in response.headers.get("location", "")

    def test_dashboard_loads(self) -> None:
        response = client.get("/app/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_ideas_page_loads(self) -> None:
        response = client.get("/app/ideas")
        assert response.status_code == 200

    def test_new_idea_page_loads(self) -> None:
        response = client.get("/app/ideas/new")
        assert response.status_code == 200

    def test_runs_page_loads(self) -> None:
        response = client.get("/app/runs")
        assert response.status_code == 200

    def test_reports_page_loads(self) -> None:
        response = client.get("/app/reports")
        assert response.status_code == 200

    def test_settings_page_loads(self) -> None:
        response = client.get("/app/settings")
        assert response.status_code == 200

    def test_diagnostics_page_loads(self) -> None:
        response = client.get("/app/diagnostics")
        assert response.status_code == 200


class TestCreateIdeaFlow:
    """Smoke test for the idea → run → report flow."""

    def test_create_idea_via_form(self) -> None:
        response = client.post(
            "/app/ideas/new",
            data={
                "title": "Smoke Test Idea",
                "description": "A description for smoke testing",
                "target_user": "smoke testers",
                "context": "testing",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/app/ideas/" in response.headers.get("location", "")

    def test_create_and_run(self) -> None:
        """Full lifecycle: create idea → start run → check report."""
        # Create idea
        resp = client.post(
            "/app/ideas/new",
            data={
                "title": "Full Flow Smoke Test",
                "description": "Testing the complete lifecycle",
                "target_user": "QA engineers",
                "context": "e2e testing",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303
        idea_url = resp.headers["location"]
        idea_id = idea_url.split("/")[-1]

        # Start run
        run_resp = client.post(
            "/app/runs/create",
            data={
                "idea_id": idea_id,
                "mode": "local-only",
                "tier": "low",
            },
            follow_redirects=False,
        )
        assert run_resp.status_code == 303
        run_url = run_resp.headers["location"]
        run_id = run_url.split("/")[-1]

        # Check run status via poll
        poll_resp = client.get(f"/api/runs/{run_id}/poll")
        assert poll_resp.status_code == 200
        poll_data = poll_resp.json()
        assert poll_data["status"] == "succeeded"
        assert poll_data["is_terminal"] is True

        # Check report HTML
        report_resp = client.get(f"/app/runs/{run_id}/report")
        assert report_resp.status_code == 200
        assert "score-card" in report_resp.text
