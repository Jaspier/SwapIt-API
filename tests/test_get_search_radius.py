from fastapi.testclient import TestClient

from main import app
from .mock import mock_login

client = TestClient(app)


def test_get_search_radius_successful():
    token = mock_login("testuser@test.io", "test123")
    response = client.get(
        "/getSearchRadius", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 200
    assert response.json() == 30


def test_get_search_radius_unsuccessful():
    response = client.get(
        "/getSearchRadius", headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
