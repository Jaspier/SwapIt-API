from fastapi.testclient import TestClient

from main import app, db
from firebase_admin import firestore

client = TestClient(app)

device_token = {
    "token": "MyDeviceToken"
}

# Delete deviceToken field if exists before running tests
db.collection("users").document("FlGdc4N4CyMAyKDfNJEHrcGGGRa2").update({
    "deviceToken": firestore.DELETE_FIELD,
})


def test_store_device_token_successful(jwt_token):
    response = client.post(
        "/storeDeviceToken",
        headers={"Authorization": "Bearer " + jwt_token},
        json=device_token)
    assert response.status_code == 200
    assert response.json() == "Successfully stored device token"


def test_store_device_token_already_exists(jwt_token):
    response = client.post(
        "/storeDeviceToken",
        headers={"Authorization": "Bearer " + jwt_token},
        json=device_token)
    assert response.status_code == 200
    assert response.json() == "Device token already saved."


def test_confirm_swap_unsuccessful():
    response = client.post(
        "/storeDeviceToken", headers={"Authorization": "Bearer fail"},
        json=device_token)
    assert response.status_code == 400
