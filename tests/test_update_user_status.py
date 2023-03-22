from fastapi.testclient import TestClient

from main import app, db, version
from firebase_admin import firestore

from .conftest import mock_login

client = TestClient(app)

status = "online"


def test_update_user_status_successful(jwt_token):
    response = client.post(
        f"/{version}/update_user_status",
        headers={"Authorization": "Bearer " + jwt_token},
        json=status)
    assert response.status_code == 200
    assert response.json() == "Successfully updated status"


def test_update_user_status_not_exists():
    token = mock_login("unknown@test.io", "unknown")
    response = client.post(
        f"/{version}/update_user_status",
        headers={"Authorization": "Bearer " + token},
        json=status)
    assert response.status_code == 400
    assert response.json() == "Failed to update status: user does not exist"


def test_confirm_swap_unsuccessful():
    response = client.post(
        f"/{version}/update_user_status", headers={"Authorization": "Bearer fail"},
        json=status)
    assert response.status_code == 400
    # Delete status field if exists after running tests
    db.collection("users").document("FlGdc4N4CyMAyKDfNJEHrcGGGRa2").update({
        u'status': firestore.DELETE_FIELD
    })
