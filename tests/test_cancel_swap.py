from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

usersMatched = ["pRZu4xbq35Q1vzQBwlPrcGZztqw2", "FlGdc4N4CyMAyKDfNJEHrcGGGRa2"]
usersMatched_not_exists = [
    "pRZu4xbq35Q1vzQBwlPrcGZztqw2", "SomeRandomeSwipedUniqueIdent"]


def test_cancel_swap_successful(jwt_token):
    response = client.post(
        "/cancelSwap",
        headers={"Authorization": "Bearer " + jwt_token},
        json=usersMatched)
    assert response.status_code == 200
    assert response.json() == "Successfully canceled swap"


def test_cancel_swap_match_not_exists(jwt_token):
    response = client.post(
        "/cancelSwap",
        headers={"Authorization": "Bearer " + jwt_token},
        json=usersMatched_not_exists)
    assert response.status_code == 404
    assert response.json() == "Match does not exist!"


def test_cancel_swap_unsuccessful():
    response = client.post(
        "/cancelSwap", headers={"Authorization": "Bearer fail"},
        json=usersMatched)
    assert response.status_code == 400
