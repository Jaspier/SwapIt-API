from fastapi.testclient import TestClient

from main import app
from .mock import mock_login

client = TestClient(app)

profile = {
    "active": True,
    "coords": {'latitude': 54.7173, 'longitude': -6.2055},
    "displayName": "testuser",
    "id": "QQyOyOf4dLdAN8SD4f2t3JM4g0r1",
    "itemName": "test item",
    "location": "Antrim",
    "photoUrls": '[{"uri":"e58470d6-10ce-48da-a681-92a4f32979fc.jpg"}]',
    "radius": 30,
    "timestamp": "2023-02-09T19:59:47.710000+00:00"
}


def test_my_profile_successful():
    token = mock_login("testuser@test.io", "test123")
    response = client.get(
        "/myprofile", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 200
    assert response.json() == profile


def test_my_profile_unsuccessful():
    response = client.get(
        "/myprofile", headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
