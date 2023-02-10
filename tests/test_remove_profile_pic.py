from fastapi.testclient import TestClient

from main import app
from .mock import mock_login

client = TestClient(app)


def test_remove_profile_pic_successful():
    token = mock_login("testuser1@test.io", "test123")
    response = client.get(
        "/removeProfilePic", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 204
    assert response.json() == "Successfully removed profile picture"


def test_remove_profile_pic_unsuccessful():
    response = client.get(
        "/removeProfilePic", headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
