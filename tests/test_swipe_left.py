from fastapi.testclient import TestClient

from main import app
from .mock import mock_login

client = TestClient(app)

user_passed = {
    "active": False,
    "coords": {
        "latitude": 54.591379,
        "longitude": -5.69317
    },
    "displayName": "passed@user.io",
    "id": "SomeRandomUniqueIdentifierID",
    "itemName": "unwanted item",
    "location": "Dumpster",
    "photoUrls": "[{\"uri\":\"41277b14-8b4d-430d-9cd3-6469822091c3.jpg\"},{\"uri\":\"0520ec79-70fa-4f0c-bd09-5740ab20aae4.jpg\"}]",
    "radius": 27,
    "timestamp": "2023-02-09T20:42:52.686000+00:00"
}


def test_swipe_left_successful():
    token = mock_login("testuser1@test.io", "test123")
    response = client.post(
        "/swipeLeft",
        headers={"Authorization": "Bearer " + token},
        json=user_passed)
    assert response.status_code == 200
    assert response.json() == "Successfully added Pass"


def test_update_location_unsuccessful():
    response = client.post(
        "/swipeLeft",
        headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
