from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

userPrefs = {
    "displayName": "testuser1",
    "radius": 30,
    "photoURL": "https://preview.redd.it/1eboxhg5jij51.jpg?auto=webp&s=907a4ff5366b6e50eaf2f9aa2b97f5a47e02c192"
}


def test_update_user_prefs_successful(jwt_token):
    response = client.post(
        "/updateUserPrefs",
        headers={"Authorization": "Bearer " + jwt_token},
        json=userPrefs)
    assert response.status_code == 204
    assert response.json() == "Successfully updated user preferences"


def test_update_user_prefs_unsuccessful():
    response = client.post(
        "/updateUserPrefs", headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
