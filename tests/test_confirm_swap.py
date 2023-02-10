from fastapi.testclient import TestClient

from main import app
from .mock import mock_login

client = TestClient(app)

usersMatched = ["pRZu4xbq35Q1vzQBwlPrcGZztqw2", "FlGdc4N4CyMAyKDfNJEHrcGGGRa2"]
usersMatched_not_exists = [
    "pRZu4xbq35Q1vzQBwlPrcGZztqw2", "SomeRandomeSwipedUniqueIdent"]


def test_confirm_swap_successful():
    token = mock_login("testuser1@test.io", "test123")
    response = client.post(
        "/confirmSwap",
        headers={"Authorization": "Bearer " + token},
        json=usersMatched)
    assert response.status_code == 200
    assert response.json() == "Successfully confirmed swap"


def test_confirm_swap_match_not_exists():
    token = mock_login("testuser1@test.io", "test123")
    response = client.post(
        "/confirmSwap",
        headers={"Authorization": "Bearer " + token},
        json=usersMatched_not_exists)
    assert response.status_code == 404
    assert response.json() == "Match does not exist!"


def test_delete_match_unsuccessful():
    response = client.post(
        "/confirmSwap", headers={"Authorization": "Bearer fail"},
        json=usersMatched)
    assert response.status_code == 400
