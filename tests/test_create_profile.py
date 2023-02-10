from fastapi.testclient import TestClient

from main import app
from .mock import mock_login

client = TestClient(app)

profile = {
    "active": False,
    "coords": {'latitude': 54.6541971, 'longitude': -5.6730648},
    "displayName": "testuser1",
    "id": "FlGdc4N4CyMAyKDfNJEHrcGGGRa2",
    "itemName": "test1 item",
    "location": "New Testopolis",
    "photoUrls": '[{"uri":"e58470d6-10ce-48da-a681-92a4f32979fc.jpg"}]',
    "radius": 30,
    "timestamp": "2023-02-09T20:42:52.686000+00:00",
    "isNewUser": False
}

res = {
    u'message': "Successfully created/updated profile",
    u'isNewUser': False,
}


def test_update_existing_profile():
    token = mock_login("testuser1@test.io", "test123")
    response = client.post(
        "/createProfile",
        headers={"Authorization": "Bearer " + token},
        json=profile)
    assert response.status_code == 204
    assert response.json() == res


def test_create_new_profile():
    token = mock_login("testuser1@test.io", "test123")
    profile["isNewUser"] = True
    res[u'isNewUser'] = True
    response = client.post(
        "/createProfile",
        headers={"Authorization": "Bearer " + token},
        json=profile)
    assert response.status_code == 204
    assert response.json() == res


def test_create_profile_unsuccessful():
    response = client.post(
        "/createProfile", headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
