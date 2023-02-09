from fastapi.testclient import TestClient

from main import app
from .mock import mock_login

client = TestClient(app)

locationData = {
    "location": "New Testopolis",
    "coords": {
        "latitude": 54.6541971,
        "longitude": -5.6730648
    }
}


def test_update_location_successful():
    token = mock_login("testuser1@test.io", "test123")
    response = client.post(
        "/updateLocation",
        headers={"Authorization": "Bearer " + token},
        json=locationData)
    assert response.status_code == 200
    assert response.json() == "Successfully updated location"


def test_update_location_unsuccessful():
    response = client.post(
        "/updateLocation", headers={"Authorization": "Bearer fail"})
    assert response.status_code == 400
