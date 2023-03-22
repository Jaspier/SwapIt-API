from fastapi.testclient import TestClient
from main import app, db, version
from firebase_admin import firestore

client = TestClient(app)


def test_reset_profile_successful(jwt_token):
    response = client.get(
        f"/{version}/reset_profile", headers={"Authorization": "Bearer " + jwt_token})
    assert response.status_code == 200
    assert response.json() == "Successfully reset profile"

    # repopulate profile
    db.collection("users").document("FlGdc4N4CyMAyKDfNJEHrcGGGRa2").update({
        "itemName": "test1 item",
        "location": "New Testopolis",
        "photoUrls": '[{"uri":"e58470d6-10ce-48da-a681-92a4f32979fc.jpg"}]',
        "timestamp": firestore.SERVER_TIMESTAMP,
        "active": False
    })


def test_reset_profile_unsuccessful():
    response = client.get(
        f"/{version}/reset_profile", headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
