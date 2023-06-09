from fastapi.testclient import TestClient

from main import app, version
from .conftest import mock_login

client = TestClient(app)

profile = {
    "active": False,
    "coords": {'latitude': 54.6541971, 'longitude': -5.6730648},
    "deviceToken": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]",
    "displayName": "testuser",
    "id": "QQyOyOf4dLdAN8SD4f2t3JM4g0r1",
    "itemName": "test item",
    "lastOnline": "2023-03-20T00:36:20.004000+00:00",
    "location": "Testopolis",
    "photoUrls": '[{"uri":"e58470d6-10ce-48da-a681-92a4f32979fc.jpg"}]',
    "radius": 30,
    "status": "offline",
    "timestamp": "2023-02-09T20:42:52.686000+00:00"
}


def test_my_profile_successful():
    token = mock_login("testuser@test.io", "test123")
    response = client.get(
        f"/{version}/my_profile", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 200
    assert response.json() == profile


def test_my_profile_unsuccessful():
    response = client.get(
        f"/{version}/my_profile", headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
