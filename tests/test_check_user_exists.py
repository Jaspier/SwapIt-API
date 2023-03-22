from fastapi.testclient import TestClient

from main import app, version
from .conftest import mock_login

client = TestClient(app)


def test_checkUserExists_with_existing_user():
    token = mock_login("testuser@test.io", "test123")
    response = client.get(
        f"/{version}/check_user_exists", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 200
    assert response.json() == "User exists"


def test_checkUserExists_with_non_existing_user():
    token = mock_login("unknown@test.io", "unknown")
    response = client.get(
        f"/{version}/check_user_exists", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 404
    assert response.json() == "User does not exist"


def test_checkUserExists_with_fetch_failure():
    response = client.get(
        f"/{version}/check_user_exists", headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
