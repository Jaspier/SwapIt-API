from fastapi.testclient import TestClient

from main import app, version
from .conftest import mock_login

client = TestClient(app)


def test_get_search_radius_successful():
    token = mock_login("testuser@test.io", "test123")
    response = client.get(
        f"/{version}/get_search_radius", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 200
    assert response.json() == 30


def test_get_search_radius_unsuccessful():
    response = client.get(
        f"/{version}/get_search_radius", headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
