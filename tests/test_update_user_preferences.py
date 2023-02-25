from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

userPrefs = {
    "displayName": "testuser1",
    "radius": 30,
}


def test_update_user_preferences_successful(jwt_token):
    response = client.post(
        "/updateUserPreferences",
        headers={"Authorization": "Bearer " + jwt_token},
        json=userPrefs)
    assert response.status_code == 204
    assert response.json() == "Successfully updated user preferences"


def test_update_user_preferences_unsuccessful():
    response = client.post(
        "/updateUserPreferences", headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
