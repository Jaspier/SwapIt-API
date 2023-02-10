from fastapi.testclient import TestClient

from main import app
from .mock import mock_login

client = TestClient(app)

message = {
    u'matchId': "pRZu4xbq35Q1vzQBwlPrcGZztqw2FlGdc4N4CyMAyKDfNJEHrcGGGRa2",
    u'message': "Test Message",
}


def test_update_existing_profile():
    token = mock_login("testuser1@test.io", "test123")
    response = client.post(
        "/sendMessage",
        headers={"Authorization": "Bearer " + token},
        json=message)
    assert response.status_code == 200
    assert response.json() == "Successfully sent message"


def test_create_profile_unsuccessful():
    response = client.post(
        "/sendMessage", headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
