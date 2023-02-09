from fastapi.testclient import TestClient

from main import app
from .mock import mock_login

client = TestClient(app)

profile = {
    "active": True,
    "coords": {'latitude': 54.7173, 'longitude': -6.2055},
    "displayName": "Allen",
    "id": "LrvfEDpPQbbcH63KfEwW9xcuAi22",
    "itemName": "Variegated Monstera",
    "location": "Antrim",
    "photoUrls": '[{"uri":"e58470d6-10ce-48da-a681-92a4f32979fc.jpg"}]',
    "radius": 50,
    "timestamp": "2023-02-09T15:41:37.565000+00:00"
}


def test_my_profile_successful():
    token = mock_login("admin@test.io", "test123")
    response = client.get(
        "/myprofile", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 200
    assert response.json() == profile


def test_my_profile_unsuccessful():
    response = client.get(
        "/myprofile", headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
