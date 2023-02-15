from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

item = "test1 item"


def test_delete_match_successful(jwt_token):
    response = client.post(
        "/deactivateMatches",
        headers={"Authorization": "Bearer " + jwt_token},
        json=item)
    assert response.status_code == 200
    assert response.json() == "Successfully deactivated matches"


def test_delete_match_unsuccessful():
    response = client.post(
        "/deactivateMatches", headers={"Authorization": "Bearer fail"},
        json=item)
    assert response.status_code == 400
