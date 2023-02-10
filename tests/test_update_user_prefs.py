from fastapi.testclient import TestClient

from main import app
from .mock import mock_login

client = TestClient(app)

userPrefs = {
    "displayName": "test",
    "radius": 32,
    "photoURL": "https://preview.redd.it/1eboxhg5jij51.jpg?auto=webp&s=907a4ff5366b6e50eaf2f9aa2b97f5a47e02c192"
}


def test_update_user_prefs_successful():
    token = mock_login("testuser1@test.io", "test123")
    response = client.post(
        "/updateUserPrefs",
        headers={"Authorization": "Bearer " + token},
        json=userPrefs)
    print(response.json())
    assert response.status_code == 204
    assert response.json() == "Successfully updated user preferences"


def test_update_user_prefs_unsuccessful():
    response = client.post(
        "/updateUserPrefs", headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
