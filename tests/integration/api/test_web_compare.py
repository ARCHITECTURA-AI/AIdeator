from unittest import mock
from uuid import uuid4

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)

@mock.patch("api.web.get_idea")
@mock.patch("api.web.list_runs_for_idea")
@mock.patch("api.web.get_report")
def test_compare_page_success(mock_get_report, mock_list_runs, mock_get_idea):
    # Setup
    id1 = uuid4()
    id2 = uuid4()
    
    def get_idea_side_effect(uid):
        if uid in [id1, id2]:
            return mock.Mock(idea_id=uid, title=f"Idea {uid}")
        return None

    mock_get_idea.side_effect = get_idea_side_effect
    
    mock_run = mock.Mock(run_id=uuid4(), status="succeeded", updated_at=mock.Mock())
    mock_list_runs.return_value = [mock_run]
    
    mock_report = mock.Mock(cards=[])
    mock_get_report.return_value = mock_report

    # Test
    response = client.get(f"/app/compare?ids={id1},{id2}")

    # Verify
    assert response.status_code == 200
    assert f"Idea {id1}" in response.text
    assert f"Idea {id2}" in response.text
    assert "VALIDATION SUMMARY" not in response.text # Just checking layout consistency

def test_compare_page_empty():
    response = client.get("/app/compare?ids=")
    assert response.status_code == 200
    assert "Idea Comparison" in response.text
