from fastapi.testclient import TestClient

from main import app, version

client = TestClient(app)

userPrefs = {
    "displayName": "testuser1",
    "radius": 30,
    "photoKey": ""
}


def test_update_user_preferences_successful(jwt_token):
    response = client.post(
        f"/{version}/update_user_preferences",
        headers={"Authorization": "Bearer " + jwt_token},
        json=userPrefs)
    assert response.status_code == 200
    assert response.json() == "Successfully updated user preferences"


def test_update_user_preferences_unsuccessful():
    response = client.post(
        f"/{version}/update_user_preferences", headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
